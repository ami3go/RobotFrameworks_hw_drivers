"""Byte-stream transport abstraction for SLCAN, plus concrete backends.

SLCAN is a line-oriented ASCII protocol, not a query/response one — a line
arriving from the adapter can be a command's own acknowledgement *or* an
unrelated, unsolicited CAN-frame notification, so the transport exposes raw
``write(bytes)``/``read_until(...)`` primitives (matching the shape already
used by ``rf_bk8500b``'s serial transport) rather than the SCPI-flavored
``query(command) -> str`` used by this repo's other, synchronous drivers.
The background reader (``reader.py``) is what turns this into a driver-level
API; this module has no knowledge of commands, acks, or frames.
"""

from __future__ import annotations

import queue
import time
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .exceptions import SlcanConfigurationError, SlcanConnectionError, SlcanTimeoutError
from .simulator import SimSlcanAdapter


@dataclass(frozen=True, slots=True)
class PortInfo:
    device: str
    description: str | None = None
    hardware_id: str | None = None
    manufacturer: str | None = None
    serial_number: str | None = None


@runtime_checkable
class Transport(Protocol):
    """Structural interface both :class:`SerialTransport` and
    :class:`SimulatedTransport` satisfy."""

    @property
    def resource(self) -> str: ...

    def open(self) -> None: ...
    def close(self) -> None: ...
    def is_open(self) -> bool: ...
    def write(self, data: bytes) -> None: ...
    def read_until(
        self, terminators: tuple[bytes, ...], *, maximum_bytes: int, timeout_s: float
    ) -> bytes: ...


def _import_serial() -> Any:
    try:
        import serial
    except ImportError as exc:
        raise SlcanConfigurationError(
            "pyserial is required for SerialTransport; install slcan[serial]"
        ) from exc
    return serial


def list_serial_ports() -> tuple[PortInfo, ...]:
    _import_serial()
    from serial.tools import list_ports

    result = []
    for port in list_ports.comports():
        result.append(
            PortInfo(
                device=port.device,
                description=getattr(port, "description", None),
                hardware_id=getattr(port, "hwid", None),
                manufacturer=getattr(port, "manufacturer", None),
                serial_number=getattr(port, "serial_number", None),
            )
        )
    return tuple(result)


class SerialTransport:
    """pySerial-backed transport for a real SLCAN adapter (usually a USB-CDC
    virtual COM port). pySerial is imported lazily so the package imports
    without the optional dependency installed."""

    def __init__(
        self,
        port: str,
        *,
        baud_rate: int = 115200,
        write_timeout_s: float = 2.0,
        dtr: bool = True,
        rts: bool = True,
    ) -> None:
        self._port = port
        self._baud_rate = baud_rate
        self._write_timeout_s = write_timeout_s
        self._dtr = dtr
        self._rts = rts
        self._serial: Any | None = None

    @property
    def resource(self) -> str:
        return self._port

    def is_open(self) -> bool:
        return bool(self._serial is not None and self._serial.is_open)

    def open(self) -> None:
        if self.is_open():
            return
        serial = _import_serial()
        kwargs: dict[str, Any] = {
            "port": self._port,
            "baudrate": self._baud_rate,
            "bytesize": serial.EIGHTBITS,
            "parity": serial.PARITY_NONE,
            "stopbits": serial.STOPBITS_ONE,
            # Short blocking per-byte read timeout: read_until polls read(1) in a
            # loop against its own overall deadline, so this just sets the pacing
            # granularity and keeps that loop from busy-spinning.
            "timeout": 0.05,
            "write_timeout": self._write_timeout_s,
            "xonxoff": False,
            "rtscts": False,
            "dsrdtr": False,
        }
        try:
            try:
                instance = serial.Serial(exclusive=True, **kwargs)
            except (TypeError, ValueError):
                instance = serial.Serial(**kwargs)
            instance.dtr = self._dtr
            instance.rts = self._rts
            instance.reset_input_buffer()
            instance.reset_output_buffer()
            self._serial = instance
        except serial.SerialException as exc:
            raise SlcanConnectionError(f"unable to open serial port {self._port!r}: {exc}") from exc

    def close(self) -> None:
        instance, self._serial = self._serial, None
        if instance is not None:
            instance.close()

    def _require(self) -> Any:
        if not self.is_open():
            raise SlcanConnectionError("serial transport is not open")
        return self._serial

    def write(self, data: bytes) -> None:
        instance = self._require()
        try:
            instance.write(data)
            instance.flush()
        except Exception as exc:  # pyserial exception types vary by platform
            raise SlcanConnectionError(f"serial write failed: {exc}") from exc

    def read_until(
        self, terminators: tuple[bytes, ...], *, maximum_bytes: int, timeout_s: float
    ) -> bytes:
        instance = self._require()
        deadline = time.monotonic() + timeout_s
        data = bytearray()
        while time.monotonic() < deadline:
            chunk = instance.read(1)
            if not chunk:
                continue
            data += chunk
            if len(data) > maximum_bytes:
                raise SlcanConnectionError(
                    f"response exceeded maximum of {maximum_bytes} bytes without a terminator"
                )
            if any(bytes(data).endswith(t) for t in terminators):
                return bytes(data)
        raise SlcanTimeoutError("no terminator received before deadline")

    def reset_input_buffer(self) -> None:
        self._require().reset_input_buffer()

    def reset_output_buffer(self) -> None:
        self._require().reset_output_buffer()


class SimulatedTransport:
    """Wraps a :class:`SimSlcanAdapter`. Uses the same blocking
    ``read_until`` shape as :class:`SerialTransport` — both a synchronous
    command's ack and an asynchronously injected frame arrive through the
    same internal queue, in the order they occur, so the background reader
    (``reader.py``) exercises identical logic against simulated and real
    hardware."""

    def __init__(self, simulator: SimSlcanAdapter | None = None) -> None:
        self.simulator = simulator or SimSlcanAdapter()
        self._open = False

    @property
    def resource(self) -> str:
        return "SIMULATED"

    def is_open(self) -> bool:
        return self._open

    def open(self) -> None:
        self._open = True

    def close(self) -> None:
        self._open = False

    def _require(self) -> None:
        if not self._open:
            raise SlcanConnectionError("simulated transport is not open")

    def write(self, data: bytes) -> None:
        self._require()
        self.simulator.dispatch(data)

    def read_until(
        self, terminators: tuple[bytes, ...], *, maximum_bytes: int, timeout_s: float
    ) -> bytes:
        del maximum_bytes  # the simulator only ever queues whole, well-formed lines
        self._require()
        try:
            return self.simulator.queue.get(timeout=timeout_s)
        except queue.Empty as exc:
            raise SlcanTimeoutError("no terminator received before deadline") from exc

    def reset_input_buffer(self) -> None:
        while not self.simulator.queue.empty():
            self.simulator.queue.get_nowait()

    def reset_output_buffer(self) -> None:
        return None
