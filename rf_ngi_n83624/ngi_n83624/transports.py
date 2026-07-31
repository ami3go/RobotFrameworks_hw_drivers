"""Transport backends for raw SCPI communication with NGI N83624."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .exceptions import CommunicationError, TimeoutError, ValidationError
from .safety import validate_channel, validate_serial_baudrate

TERMINATOR = b"\n"


@runtime_checkable
class Transport(Protocol):
    """Structural transport protocol used by the driver.

    Third-party transports may be passed to :class:`N83624CellSimulator` without
    inheriting from a base class, as long as they implement this contract.
    """

    def open(self) -> None: ...

    def close(self) -> None: ...

    def write(self, command: str) -> None: ...

    def query(self, command: str) -> str: ...

    def is_open(self) -> bool: ...


@dataclass
class TcpTransport:
    """Raw TCP SCPI transport.

    The vendor manual documents default host ``192.168.0.123`` and TCP port 7000.
    The socket is kept open across commands until ``close()`` is called.
    """

    host: str = "192.168.0.123"
    port: int = 7000
    timeout: float = 3.0
    recv_size: int = 4096

    def __post_init__(self) -> None:
        if self.port <= 0 or self.port > 65535:
            raise ValidationError(f"Invalid TCP port: {self.port}")
        self._sock: socket.socket | None = None

    def open(self) -> None:
        if self._sock is not None:
            return
        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            sock.settimeout(self.timeout)
        except socket.timeout as exc:
            raise TimeoutError(f"TCP connect timeout to {self.host}:{self.port}") from exc
        except OSError as exc:
            raise CommunicationError(f"TCP connect failed to {self.host}:{self.port}: {exc}") from exc
        self._sock = sock

    def close(self) -> None:
        sock, self._sock = self._sock, None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

    def is_open(self) -> bool:
        return self._sock is not None

    def write(self, command: str) -> None:
        sock = self._require_open()
        payload = _encode_command(command)
        try:
            sock.sendall(payload)
        except socket.timeout as exc:
            raise TimeoutError(f"TCP write timeout for command {command!r}") from exc
        except OSError as exc:
            self.close()
            raise CommunicationError(f"TCP write failed for command {command!r}: {exc}") from exc

    def query(self, command: str) -> str:
        sock = self._require_open()
        payload = _encode_command(command)
        try:
            sock.sendall(payload)
            chunks: list[bytes] = []
            while True:
                chunk = sock.recv(self.recv_size)
                if not chunk:
                    break
                chunks.append(chunk)
                if b"\n" in chunk or b"\r" in chunk:
                    break
        except socket.timeout as exc:
            if chunks:
                return b"".join(chunks).decode("ascii", errors="replace").strip()
            raise TimeoutError(f"TCP query timeout for command {command!r}") from exc
        except OSError as exc:
            self.close()
            raise CommunicationError(f"TCP query failed for command {command!r}: {exc}") from exc
        try:
            return b"".join(chunks).decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise CommunicationError(f"TCP query returned non-ASCII bytes for command {command!r}") from exc

    def _require_open(self) -> socket.socket:
        if self._sock is None:
            raise CommunicationError("TCP transport is not open")
        return self._sock


@dataclass
class UdpTransport:
    """UDP SCPI transport.

    UDP is less reliable than TCP. Use it only when the application can tolerate
    packet loss or when higher measurement acquisition speed is needed.

    Port semantics from the vendor manual:
    - 7000: communication-board port; may control all 24 channels.
    - 7001..7024: channel-specific ports for channels 1..24.

    The high-level driver treats channel-specific UDP ports as single-channel
    transports. It refuses access to other channels unless explicitly bypassed with
    raw SCPI methods.
    """

    host: str = "192.168.0.123"
    port: int = 7000
    timeout: float = 3.0
    recv_size: int = 4096
    single_channel: int | None = None

    def __post_init__(self) -> None:
        if not (7000 <= self.port <= 7024):
            raise ValidationError(f"N83624 UDP port must be 7000..7024; got {self.port}")
        expected_channel = self.port - 7000 if self.port > 7000 else None
        if self.single_channel is None:
            self.single_channel = expected_channel
        elif expected_channel is not None and self.single_channel != expected_channel:
            raise ValidationError(
                f"UDP port {self.port} maps to channel {expected_channel}, not {self.single_channel}"
            )
        if self.single_channel is not None:
            validate_channel(self.single_channel)
        self._sock: socket.socket | None = None

    def open(self) -> None:
        if self._sock is not None:
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
        except OSError as exc:
            raise CommunicationError(f"UDP socket creation failed: {exc}") from exc
        self._sock = sock

    def close(self) -> None:
        sock, self._sock = self._sock, None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    def is_open(self) -> bool:
        return self._sock is not None

    def write(self, command: str) -> None:
        sock = self._require_open()
        try:
            sock.sendto(_encode_command(command), (self.host, self.port))
        except socket.timeout as exc:
            raise TimeoutError(f"UDP write timeout for command {command!r}") from exc
        except OSError as exc:
            raise CommunicationError(f"UDP write failed for command {command!r}: {exc}") from exc

    def query(self, command: str) -> str:
        sock = self._require_open()
        try:
            sock.sendto(_encode_command(command), (self.host, self.port))
            data, _addr = sock.recvfrom(self.recv_size)
        except socket.timeout as exc:
            raise TimeoutError(f"UDP query timeout for command {command!r}") from exc
        except OSError as exc:
            raise CommunicationError(f"UDP query failed for command {command!r}: {exc}") from exc
        try:
            return data.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise CommunicationError(f"UDP query returned non-ASCII bytes for command {command!r}") from exc

    def _require_open(self) -> socket.socket:
        if self._sock is None:
            raise CommunicationError("UDP transport is not open")
        return self._sock


@dataclass
class SerialTransport:
    """RS232 SCPI transport using pyserial."""

    port: str
    baudrate: int = 115200
    timeout: float = 3.0

    def __post_init__(self) -> None:
        validate_serial_baudrate(self.baudrate)
        self._serial = None

    def open(self) -> None:
        if self._serial is not None:
            return
        try:
            import serial  # type: ignore[import-not-found]
        except ImportError as exc:
            raise CommunicationError("pyserial is required for SerialTransport") from exc
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
        except serial.SerialException as exc:  # type: ignore[attr-defined]
            raise CommunicationError(f"Serial open failed for {self.port}: {exc}") from exc

    def close(self) -> None:
        ser, self._serial = self._serial, None
        if ser is not None:
            try:
                ser.close()
            except Exception as exc:  # pragma: no cover - pyserial-dependent edge case
                raise CommunicationError(f"Serial close failed: {exc}") from exc

    def is_open(self) -> bool:
        return self._serial is not None and bool(getattr(self._serial, "is_open", False))

    def write(self, command: str) -> None:
        ser = self._require_open()
        try:
            ser.write(_encode_command(command))
            ser.flush()
        except Exception as exc:
            raise CommunicationError(f"Serial write failed for command {command!r}: {exc}") from exc

    def query(self, command: str) -> str:
        ser = self._require_open()
        try:
            ser.write(_encode_command(command))
            ser.flush()
            line = ser.readline()
        except Exception as exc:
            raise CommunicationError(f"Serial query failed for command {command!r}: {exc}") from exc
        if not line:
            raise TimeoutError(f"Serial query timeout for command {command!r}")
        try:
            return line.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise CommunicationError(f"Serial query returned non-ASCII bytes for command {command!r}") from exc

    def _require_open(self):
        if self._serial is None or not self.is_open():
            raise CommunicationError("Serial transport is not open")
        return self._serial


def udp_channel(host: str, channel: int, *, timeout: float = 3.0) -> UdpTransport:
    """Create a UDP transport bound to a channel-specific port.

    ``channel=1`` maps to UDP port 7001, ``channel=24`` maps to 7024.
    The resulting simulator object is intended to access only that channel.
    """
    validate_channel(channel)
    return UdpTransport(host=host, port=7000 + channel, timeout=timeout, single_channel=channel)


def _encode_command(command: str) -> bytes:
    if not isinstance(command, str) or not command.strip():
        raise ValidationError("SCPI command must be a non-empty string")
    command = command.rstrip("\r\n")
    return command.encode("ascii") + TERMINATOR
