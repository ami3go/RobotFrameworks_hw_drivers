"""Transport abstraction for SCPI communication."""

from __future__ import annotations

import socket
import threading
from typing import Any, Protocol, runtime_checkable

from .exceptions import N6700ConnectionError, N6700TimeoutError, UnsupportedFeatureError


@runtime_checkable
class Transport(Protocol):
    supports_clear: bool

    @property
    def is_open(self) -> bool: ...
    def write(self, command: str) -> None: ...
    def query(self, command: str) -> str: ...
    def read_raw(self) -> bytes: ...
    def write_raw(self, data: bytes) -> None: ...
    def clear(self) -> None: ...
    def close(self) -> None: ...


class PyVisaTransport:
    """PyVISA transport for USBTMC, TCPIP INSTR, and TCPIP SOCKET resources."""

    supports_clear = True

    def __init__(
        self,
        resource: str,
        *,
        timeout_ms: int = 5000,
        read_termination: str = "\n",
        write_termination: str = "\n",
        query_delay: float | None = None,
        chunk_size: int | None = None,
        backend: str | None = None,
    ) -> None:
        try:
            import pyvisa
        except Exception as exc:  # pragma: no cover - depends on optional environment
            raise N6700ConnectionError("pyvisa is required for PyVisaTransport") from exc
        rm = pyvisa.ResourceManager(backend) if backend else pyvisa.ResourceManager()
        self._inst: Any | None = None
        try:
            self._inst = rm.open_resource(resource)
        except Exception as exc:  # pragma: no cover - real hardware dependent
            raise N6700ConnectionError(f"could not open VISA resource {resource!r}") from exc
        inst: Any = self._inst
        inst.timeout = timeout_ms
        inst.read_termination = read_termination
        inst.write_termination = write_termination
        if query_delay is not None:
            inst.query_delay = query_delay
        if chunk_size is not None:
            inst.chunk_size = chunk_size
        self._lock = threading.RLock()
        self.resource = resource

    def _instrument(self) -> Any:
        if self._inst is None:
            raise N6700ConnectionError(f"VISA resource {self.resource!r} is closed")
        return self._inst

    @property
    def is_open(self) -> bool:
        return self._inst is not None

    def write(self, command: str) -> None:
        with self._lock:
            try:
                self._instrument().write(command)
            except Exception as exc:  # pragma: no cover
                raise N6700TimeoutError(str(exc)) from exc

    def query(self, command: str) -> str:
        with self._lock:
            try:
                return str(self._instrument().query(command)).strip()
            except Exception as exc:  # pragma: no cover
                raise N6700TimeoutError(str(exc)) from exc

    def read_raw(self) -> bytes:
        with self._lock:
            return bytes(self._instrument().read_raw())

    def write_raw(self, data: bytes) -> None:
        with self._lock:
            self._instrument().write_raw(data)

    def clear(self) -> None:
        with self._lock:
            self._instrument().clear()

    def close(self) -> None:
        with self._lock:
            if self._inst is not None:
                self._inst.close()
                self._inst = None


class RawSocketTransport:
    """Raw TCP SCPI socket transport.

    Device clear is not faked over raw sockets. `supports_clear` is False.
    """

    supports_clear = False

    def __init__(self, host: str, port: int = 5025, *, timeout_s: float = 5.0) -> None:
        self.host = host
        self.port = port
        self.timeout_s = timeout_s
        self._sock: socket.socket | None = socket.create_connection((host, port), timeout=timeout_s)
        self._sock.settimeout(timeout_s)
        self._lock = threading.RLock()

    def _socket(self) -> socket.socket:
        if self._sock is None:
            raise N6700ConnectionError(f"socket {self.host}:{self.port} is closed")
        return self._sock

    @property
    def is_open(self) -> bool:
        return self._sock is not None

    def write(self, command: str) -> None:
        with self._lock:
            self.write_raw((command.rstrip("\n") + "\n").encode("ascii"))

    def query(self, command: str) -> str:
        with self._lock:
            self.write(command)
            return self.read_raw().decode("ascii", errors="replace").strip()

    def read_raw(self) -> bytes:
        with self._lock:
            chunks: list[bytes] = []
            while True:
                try:
                    data = self._socket().recv(4096)
                except TimeoutError as exc:
                    raise N6700TimeoutError("socket read timed out") from exc
                if not data:
                    break
                chunks.append(data)
                if data.endswith(b"\n"):
                    break
            return b"".join(chunks)

    def write_raw(self, data: bytes) -> None:
        with self._lock:
            try:
                self._socket().sendall(data)
            except TimeoutError as exc:
                raise N6700TimeoutError("socket write timed out") from exc

    def clear(self) -> None:
        raise UnsupportedFeatureError("raw TCP socket transport does not support device clear")

    def close(self) -> None:
        with self._lock:
            if self._sock is not None:
                self._sock.close()
                self._sock = None


class SimulatedTransport:
    """Transport for the built-in simulator."""

    supports_clear = True

    def __init__(self, simulator: object) -> None:
        self.simulator = simulator
        self._lock = threading.RLock()
        self._open = True
        self._raw_response = b""

    @property
    def is_open(self) -> bool:
        return self._open

    def write(self, command: str) -> None:
        with self._lock:
            self.simulator.execute(command)  # type: ignore[attr-defined]

    def query(self, command: str) -> str:
        with self._lock:
            response = self.simulator.execute(command)  # type: ignore[attr-defined]
            if isinstance(response, bytes):
                return response.decode("ascii", errors="replace").strip()
            return str(response).strip()

    def read_raw(self) -> bytes:
        with self._lock:
            return self._raw_response

    def write_raw(self, data: bytes) -> None:
        with self._lock:
            self._raw_response = data

    def clear(self) -> None:
        with self._lock:
            self.simulator.clear()  # type: ignore[attr-defined]

    def close(self) -> None:
        self._open = False
