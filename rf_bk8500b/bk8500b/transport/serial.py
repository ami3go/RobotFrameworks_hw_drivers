"""pySerial-backed transport.

pySerial is imported lazily so documentation, static inspection, and fake-transport
unit tests can run before the optional runtime dependency is installed.
"""
from __future__ import annotations

import time
from typing import Any

from ..config import DriverConfig
from ..exceptions import (
    ConfigurationError,
    ConnectionLostError,
    PortBusyError,
    ReadTimeoutError,
    ResponseTooLargeError,
    TransportError,
    WriteTimeoutError,
)
from .base import PortInfo


def _import_serial() -> tuple[Any, Any]:
    try:
        import serial  # type: ignore[import-not-found]
        from serial.tools import list_ports  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ConfigurationError(
            "pyserial is required for SerialTransport; install bk8500b[serial]"
        ) from exc
    return serial, list_ports


def list_serial_ports() -> tuple[PortInfo, ...]:
    _serial, list_ports = _import_serial()
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
    def __init__(self, config: DriverConfig) -> None:
        self._config = config
        self._serial: Any | None = None

    @property
    def is_open(self) -> bool:
        return bool(self._serial is not None and self._serial.is_open)

    def open(self) -> None:
        if self.is_open:
            return
        serial, _ = _import_serial()
        try:
            kwargs = dict(
                port=self._config.port,
                baudrate=self._config.baud_rate,
                bytesize=self._config.bytesize,
                parity=self._config.parity,
                stopbits=self._config.stopbits,
                timeout=self._config.read_timeout_s,
                write_timeout=self._config.write_timeout_s,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
            )
            try:
                kwargs["exclusive"] = True
                instance = serial.Serial(**kwargs)
            except (TypeError, ValueError):
                kwargs.pop("exclusive", None)
                instance = serial.Serial(**kwargs)
            instance.dtr = self._config.dtr
            instance.rts = self._config.rts
            self._serial = instance
        except serial.SerialException as exc:
            text = str(exc).lower()
            error_type = PortBusyError if any(x in text for x in ("busy", "access", "permission")) else TransportError
            raise error_type(
                f"Unable to open serial port {self._config.port!r}",
                context={"port": self._config.port},
            ) from exc

    def close(self) -> None:
        instance, self._serial = self._serial, None
        if instance is None:
            return
        try:
            instance.close()
        except Exception as exc:  # close must preserve original type as transport error
            raise TransportError("Failed to close serial transport") from exc

    def _require(self) -> Any:
        if not self.is_open:
            raise ConnectionLostError("Serial transport is not open")
        return self._serial

    def write(self, data: bytes, *, timeout_s: float | None = None) -> int:
        instance = self._require()
        if not isinstance(data, bytes) or not data:
            raise ValueError("write data must be non-empty bytes")
        previous = instance.write_timeout
        if timeout_s is not None:
            instance.write_timeout = timeout_s
        try:
            count = instance.write(data)
            instance.flush()
            if count != len(data):
                raise WriteTimeoutError(
                    "Serial write completed only partially",
                    context={"expected": len(data), "written": count},
                )
            return count
        except WriteTimeoutError:
            raise
        except Exception as exc:
            serial, _ = _import_serial()
            if isinstance(exc, getattr(serial, "SerialTimeoutException", ())):
                raise WriteTimeoutError("Serial write timed out") from exc
            raise ConnectionLostError("Serial write failed") from exc
        finally:
            instance.write_timeout = previous

    def read(self, size: int, *, timeout_s: float | None = None) -> bytes:
        instance = self._require()
        if size < 0:
            raise ValueError("size must be non-negative")
        previous = instance.timeout
        if timeout_s is not None:
            instance.timeout = timeout_s
        try:
            data = instance.read(size)
            if not data and size:
                raise ReadTimeoutError(
                    "Serial read timed out",
                    context={"requested": size},
                )
            return bytes(data)
        except ReadTimeoutError:
            raise
        except Exception as exc:
            raise ConnectionLostError("Serial read failed") from exc
        finally:
            instance.timeout = previous

    def read_until(
        self,
        terminator: bytes,
        *,
        maximum_bytes: int,
        timeout_s: float | None = None,
    ) -> bytes:
        if not terminator:
            raise ValueError("terminator must be non-empty")
        deadline = time.monotonic() + (
            self._config.read_timeout_s if timeout_s is None else timeout_s
        )
        data = bytearray()
        while time.monotonic() < deadline:
            remaining = max(0.001, deadline - time.monotonic())
            try:
                chunk = self.read(1, timeout_s=remaining)
            except ReadTimeoutError:
                break
            data += chunk
            if len(data) > maximum_bytes:
                raise ResponseTooLargeError(
                    "Serial response exceeded configured maximum",
                    context={"maximum_bytes": maximum_bytes},
                )
            if data.endswith(terminator):
                return bytes(data)
        raise ReadTimeoutError(
            "Serial response terminator was not received before deadline",
            context={"received_bytes": len(data)},
        )

    def reset_input_buffer(self) -> None:
        self._require().reset_input_buffer()

    def reset_output_buffer(self) -> None:
        self._require().reset_output_buffer()
