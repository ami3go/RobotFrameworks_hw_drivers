"""Deterministic in-process SLCAN adapter simulator.

Unlike this repo's SCPI-instrument simulators (a single ``dispatch(command)
-> bytes`` call-and-response), this one has no synchronous return path:
:meth:`SimSlcanAdapter.dispatch` pushes whatever the real adapter would have
written back (an ack, a nack, or a query's data response) onto ``self.queue``
instead of returning it, because :class:`slcan.transport.SimulatedTransport`
needs command results and asynchronously injected frames to arrive through
the same ordered channel — exactly how a real serial byte stream carries
both. This makes the simulated transport exercise the same background
reader (``reader.py``) code path as real hardware, not a special-cased
shortcut.

:meth:`inject_frame` is this simulator's test hook for unsolicited incoming
CAN frames — the same role ``force_overload``/``force_calibration_failure``
play in this repo's other simulators for triggering conditions a
synchronous dispatch call can't reach on its own.
"""

from __future__ import annotations

import queue

from . import codec
from .codec import BEL, CR
from .enums import Bitrate, ChannelMode
from .exceptions import SlcanProtocolError
from .models import CanFrame

_VERSION_RESPONSE = b"V1013" + CR  # simulated hardware 1.0, software 1.3
_SERIAL_RESPONSE = b"NA123" + CR


class _Nack(Exception):
    """Internal control-flow signal: reject the in-flight command."""


class SimSlcanAdapter:
    """A small, deterministic stand-in for a real SLCAN adapter."""

    def __init__(self) -> None:
        self.is_open = False
        self.mode: ChannelMode | None = None
        self.bitrate: Bitrate | None = None
        self.status_flags = 0
        self.queue: queue.Queue[bytes] = queue.Queue()

    # -- test hooks --------------------------------------------------------
    def inject_frame(self, frame: CanFrame) -> None:
        """Simulates another node putting a frame on the bus. Bypasses
        ``dispatch`` entirely — this is not something the host commanded."""

        self.queue.put(codec.encode_transmit(frame))

    # -- public dispatch -----------------------------------------------------
    def dispatch(self, raw: bytes) -> None:
        text = raw.decode("ascii", errors="replace")
        command = text.removesuffix("\r")
        try:
            if not command:
                raise _Nack
            head = command[0]
            if head == "S":
                self._cmd_set_bitrate(command)
            elif head in ("O", "L"):
                self._cmd_open(command)
            elif head == "C":
                self._cmd_close(command)
            elif head in ("t", "T", "r", "R"):
                self._cmd_transmit(command)
            elif head == "F":
                self._cmd_status(command)
            elif head == "V":
                self._cmd_version(command)
            elif head == "N":
                self._cmd_serial(command)
            else:
                raise _Nack
        except (_Nack, SlcanProtocolError):
            self.queue.put(BEL)

    # -- command handlers ------------------------------------------------
    def _ack(self) -> None:
        self.queue.put(CR)

    def _cmd_set_bitrate(self, command: str) -> None:
        if self.is_open:
            raise _Nack  # bitrate can't change while the channel is open
        try:
            self.bitrate = Bitrate(int(command[1:]))
        except (ValueError, KeyError) as exc:
            raise _Nack from exc
        self._ack()

    def _cmd_open(self, command: str) -> None:
        """Requires a bitrate to already be set (``S<n>``) — a conservative,
        fail-closed judgment call documented in the task doc, since the
        cited source doesn't spell out behavior for opening at an undefined
        bitrate."""

        if self.is_open:
            raise _Nack
        if self.bitrate is None:
            raise _Nack
        if command not in ("O", "L"):
            raise _Nack
        self.mode = ChannelMode.NORMAL if command == "O" else ChannelMode.LISTEN_ONLY
        self.is_open = True
        self._ack()

    def _cmd_close(self, command: str) -> None:
        if command != "C":
            raise _Nack
        # Closing is always accepted, even mid-fault — matches task §6 safety
        # requirement that the channel must always be closeable.
        self.is_open = False
        self.mode = None
        self._ack()

    def _cmd_transmit(self, command: str) -> None:
        if not self.is_open:
            raise _Nack
        if self.mode is ChannelMode.LISTEN_ONLY:
            raise _Nack
        codec.parse_frame_line(command.encode("ascii"))  # validates shape; raises on garbage
        self._ack()

    def _cmd_status(self, command: str) -> None:
        if command != "F":
            raise _Nack
        self.queue.put(f"F{self.status_flags:02X}".encode("ascii") + CR)

    def _cmd_version(self, command: str) -> None:
        if command != "V":
            raise _Nack
        self.queue.put(_VERSION_RESPONSE)

    def _cmd_serial(self, command: str) -> None:
        if command != "N":
            raise _Nack
        self.queue.put(_SERIAL_RESPONSE)
