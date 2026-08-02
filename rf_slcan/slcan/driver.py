"""Typed core driver for SLCAN (serial-line CAN) interface adapters.

Owns SLCAN command construction/parsing and the background reader thread
that makes receiving unsolicited CAN frames possible. The Robot Framework
adapter (``rf_slcan/library.py``) is a thin layer on top of this module and
must not duplicate any of this logic.
"""

from __future__ import annotations

import queue
import threading

from . import codec
from .enums import Bitrate, ChannelMode
from .exceptions import (
    SlcanConnectionError,
    SlcanDeviceError,
    SlcanProtocolError,
    SlcanTimeoutError,
    SlcanValidationError,
)
from .models import AdapterIdentity, AdapterStatus, CanFrame
from .reader import FAULT_SENTINEL, BackgroundReader
from .simulator import SimSlcanAdapter
from .transport import SerialTransport, SimulatedTransport, Transport

_RAW_SLCAN_CONFIRMATION = "ENABLE RAW SLCAN"
_DEFAULT_COMMAND_TIMEOUT_S = 2.0


class SlcanAdapter:
    """A connected session with one SLCAN interface adapter."""

    def __init__(self, transport: Transport, *, timeout_s: float = _DEFAULT_COMMAND_TIMEOUT_S) -> None:
        self.transport = transport
        self.timeout_s = timeout_s
        self._reader = BackgroundReader(transport)
        self._command_lock = threading.Lock()
        self._raw_slcan_enabled = False
        self._identity: AdapterIdentity | None = None
        self._bitrate: Bitrate | None = None
        self._mode: ChannelMode | None = None
        self._channel_open = False

    # ------------------------------------------------------------------
    # Construction / lifecycle
    # ------------------------------------------------------------------
    @classmethod
    def connect_serial(
        cls,
        port: str,
        *,
        baud_rate: int = 115200,
        timeout_s: float = _DEFAULT_COMMAND_TIMEOUT_S,
    ) -> SlcanAdapter:
        transport = SerialTransport(port, baud_rate=baud_rate)
        transport.open()
        adapter = cls(transport, timeout_s=timeout_s)
        adapter._reader.start()
        return adapter

    @classmethod
    def connect_simulated(
        cls, simulator: SimSlcanAdapter | None = None, *, timeout_s: float = _DEFAULT_COMMAND_TIMEOUT_S
    ) -> SlcanAdapter:
        transport = SimulatedTransport(simulator)
        transport.open()
        adapter = cls(transport, timeout_s=timeout_s)
        adapter._reader.start()
        return adapter

    def close(self) -> None:
        # Stop the reader before closing the transport so it never touches
        # a closed transport mid-read.
        self._reader.stop()
        self.transport.close()

    @property
    def connected(self) -> bool:
        return self.transport.is_open() and self._reader.fault is None

    @property
    def resource(self) -> str:
        return self.transport.resource

    @property
    def channel_open(self) -> bool:
        return self._channel_open

    # ------------------------------------------------------------------
    # Low-level I/O with exception translation
    # ------------------------------------------------------------------
    def _require_connected(self) -> None:
        if not self.transport.is_open():
            raise SlcanConnectionError("not connected; call connect_serial/connect_simulated first")
        if self._reader.fault is not None:
            raise SlcanConnectionError(
                f"connection lost: {self._reader.fault}"
            ) from self._reader.fault

    def _send_command(self, command: bytes, *, expects_data: bool, timeout_s: float | None = None) -> bytes:
        """The single choke-point every mutating/query command goes through.

        SLCAN gives no per-command tag on its acks, so commands must be
        serialized one at a time (``_command_lock``) and any stale,
        undelivered result from a previously-timed-out command must be
        drained before sending a new one — otherwise a late-arriving ack for
        command A could be mistaken for command B's ack.
        """

        effective_timeout_s = self.timeout_s if timeout_s is None else timeout_s
        with self._command_lock:
            self._require_connected()
            while not self._reader.ack_queue.empty():
                try:
                    self._reader.ack_queue.get_nowait()
                except queue.Empty:
                    break
            self.transport.write(command)
            try:
                result = self._reader.ack_queue.get(timeout=effective_timeout_s)
            except queue.Empty as exc:
                raise SlcanTimeoutError(
                    f"no response to {command!r} within {effective_timeout_s}s"
                ) from exc

        if result is FAULT_SENTINEL:
            raise SlcanConnectionError(f"connection lost: {self._reader.fault}") from self._reader.fault
        assert isinstance(result, bytes)  # narrows for mypy; FAULT_SENTINEL handled above
        if result == codec.BEL:
            raise SlcanDeviceError(f"adapter rejected command {command!r}")
        if not expects_data and result != b"":
            raise SlcanProtocolError(f"unexpected data for command {command!r}: {result!r}")
        return result

    # ------------------------------------------------------------------
    # Identity / communication (RFDS-002)
    # ------------------------------------------------------------------
    def identify(self, *, refresh: bool = True) -> AdapterIdentity:
        if not refresh and self._identity is not None:
            return self._identity
        version_response = self._send_command(codec.encode_version_query(), expects_data=True)
        serial_response = self._send_command(codec.encode_serial_query(), expects_data=True)
        hardware_version, software_version = codec.parse_version(version_response)
        serial_number = codec.parse_serial_number(serial_response)
        identity = AdapterIdentity(
            hardware_version=hardware_version,
            software_version=software_version,
            serial_number=serial_number,
            raw=f"SLCAN,HW{hardware_version},SW{software_version},{serial_number}",
        )
        self._identity = identity
        return identity

    def check_communication(self) -> bool:
        self.get_version(raw=True)
        return True

    # ------------------------------------------------------------------
    # Channel control
    # ------------------------------------------------------------------
    def set_bitrate(self, bitrate: Bitrate) -> None:
        self._send_command(codec.encode_set_bitrate(bitrate), expects_data=False)
        self._bitrate = bitrate

    def open_channel(self, mode: ChannelMode = ChannelMode.NORMAL) -> None:
        self._send_command(codec.encode_open(mode), expects_data=False)
        self._mode = mode
        self._channel_open = True

    def close_channel(self) -> None:
        # Always attempted, even if the driver already believes the channel
        # is closed — matches task §6: closing must always be possible.
        self._send_command(codec.encode_close(), expects_data=False)
        self._channel_open = False
        self._mode = None

    # ------------------------------------------------------------------
    # Frames
    # ------------------------------------------------------------------
    def send_frame(
        self, arbitration_id: int, data: bytes = b"", *, extended: bool = False, remote: bool = False
    ) -> None:
        if not remote and len(data) > 8:
            raise SlcanValidationError(f"data must be 0-8 bytes, got {len(data)}")
        frame = CanFrame(
            arbitration_id=arbitration_id,
            data=data,
            dlc=len(data) if not remote else 0,
            extended=extended,
            remote=remote,
        )
        command = codec.encode_transmit(frame)  # raises SlcanValidationError on bad id/dlc
        self._send_command(command, expects_data=False)

    def receive_frame(self, timeout_s: float = 1.0) -> CanFrame | None:
        """Blocks up to ``timeout_s`` for the next frame. Returns ``None`` on
        timeout — receiving nothing is a normal outcome, not an error."""

        self._require_connected()
        try:
            return self._reader.rx_queue.get(timeout=timeout_s)
        except queue.Empty:
            return None

    def drain_received_frames(self, max_count: int | None = None) -> list[CanFrame]:
        """Non-blocking: returns whatever is already queued, up to ``max_count``."""

        self._require_connected()
        frames: list[CanFrame] = []
        while max_count is None or len(frames) < max_count:
            try:
                frames.append(self._reader.rx_queue.get_nowait())
            except queue.Empty:
                break
        return frames

    def get_received_frame_count(self) -> int:
        return self._reader.rx_queue.qsize()

    def clear_received_frames(self) -> None:
        self.drain_received_frames()

    def get_receive_overflow_count(self) -> int:
        return self._reader.overflow_count

    # ------------------------------------------------------------------
    # Status / identity queries
    # ------------------------------------------------------------------
    def get_status(self) -> AdapterStatus:
        raw = self._send_command(codec.encode_status_query(), expects_data=True)
        return codec.parse_status_flags(raw)

    def get_version(self, *, raw: bool = False) -> bytes | str:
        response = self._send_command(codec.encode_version_query(), expects_data=True)
        if raw:
            return response
        hardware_version, software_version = codec.parse_version(response)
        return f"HW{hardware_version} SW{software_version}"

    def get_serial_number(self, *, raw: bool = False) -> bytes | str:
        response = self._send_command(codec.encode_serial_query(), expects_data=True)
        return response if raw else codec.parse_serial_number(response)

    # ------------------------------------------------------------------
    # Raw escape hatch
    # ------------------------------------------------------------------
    def enable_raw_slcan(self, confirmation: str) -> None:
        if confirmation != _RAW_SLCAN_CONFIRMATION:
            raise SlcanValidationError(
                f'raw SLCAN requires the exact confirmation text "{_RAW_SLCAN_CONFIRMATION}"'
            )
        self._raw_slcan_enabled = True

    def _require_raw_slcan_enabled(self) -> None:
        if not self._raw_slcan_enabled:
            raise SlcanValidationError(
                "raw SLCAN is disabled; call enable_raw_slcan() with the exact confirmation text first"
            )

    def raw_command(self, command: str, *, expects_data: bool = False) -> str:
        """Bypasses typed validation. Sends ``command`` verbatim (a trailing
        CR is added if missing) and returns the adapter's response body as
        text (empty string for a bare ack)."""

        self._require_raw_slcan_enabled()
        payload = command.encode("ascii")
        if not payload.endswith(codec.CR):
            payload += codec.CR
        response = self._send_command(payload, expects_data=expects_data)
        return response.decode("ascii", errors="replace")
