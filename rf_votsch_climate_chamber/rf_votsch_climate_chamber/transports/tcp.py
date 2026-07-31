"""Thread-safe TCP transport with finite deadlines and persistent framing buffer."""

from __future__ import annotations

import contextlib
import datetime as dt
import socket
import time
from typing import Callable

from ..exceptions import (
    DriverReadError,
    DriverTimeoutError,
    DriverTransportOpenError,
    DriverWriteError,
)
from .base import BaseTransport
from .models import ReadRequest, TransportCapabilities, TransportDescriptor, TransportState, WriteResult


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class TcpTransport(BaseTransport):
    """RFDS-004-style TCP backend for request/response byte protocols."""

    transport_type = "tcp"

    def __init__(
        self,
        host: str,
        port: int = 2049,
        *,
        timeout_s: float = 5.0,
        keepalive: bool = True,
        socket_factory: Callable[[tuple[str, int], float], socket.socket] | None = None,
    ) -> None:
        super().__init__(f"tcp://{host}:{port}")
        self.host = host
        self.port = int(port)
        self.timeout_s = float(timeout_s)
        self.keepalive = bool(keepalive)
        self._socket_factory = socket_factory or (
            lambda endpoint, timeout: socket.create_connection(endpoint, timeout=timeout)
        )
        self._socket: socket.socket | None = None
        self._receive_buffer = bytearray()

    @property
    def capabilities(self) -> TransportCapabilities:
        return TransportCapabilities(
            supports_reconnect=True,
            supports_cancel=True,
            supports_flush=True,
            supports_device_clear=False,
        )

    def open(self) -> TransportDescriptor:
        if self.is_open:
            return self.descriptor
        op = self._operation_id("transport.open")
        if self.state is TransportState.FAULTED:
            self.close(timeout_s=self.timeout_s)
        self._transition(TransportState.OPENING, "open", op)
        try:
            sock = self._socket_factory((self.host, self.port), self.timeout_s)
            sock.settimeout(self.timeout_s)
            if self.keepalive:
                with contextlib.suppress(OSError):
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self._socket = sock
            self._receive_buffer.clear()
            self._cancel_event.clear()
            self._descriptor = TransportDescriptor(
                transport_type="tcp",
                resource=self._resource,
                normalized_resource=f"tcp://{self.host.lower()}:{self.port}",
                opened_at=_utc_now(),
                closed_at=None,
                backend="socket",
                metadata={"host": self.host, "port": self.port},
            )
            self._metrics.opens += 1
            self._transition(TransportState.OPEN, "open_succeeded", op)
            self._emit("open", op, details={"host": self.host, "port": self.port})
            return self._descriptor
        except Exception as exc:
            self._metrics.failures += 1
            self._socket = None
            self._transition(TransportState.CLOSED, "open_failed", op)
            raise DriverTransportOpenError(
                f"cannot open TCP endpoint {self.host}:{self.port}: {exc}",
                operation="Connect",
                details={"resource": self._resource},
            ) from exc

    def close(self, *, timeout_s: float | None = None) -> None:
        del timeout_s
        if self.state in {TransportState.CREATED, TransportState.CLOSED}:
            if self.state is TransportState.CREATED:
                self._transition(TransportState.CLOSED, "close", "transport.close")
            return
        op = self._operation_id("transport.close")
        if self.state not in {TransportState.OPEN, TransportState.FAULTED}:
            return
        self._transition(TransportState.CLOSING, "close", op)
        sock, self._socket = self._socket, None
        try:
            if sock is not None:
                with contextlib.suppress(OSError):
                    sock.shutdown(socket.SHUT_RDWR)
                with contextlib.suppress(OSError):
                    sock.close()
            self._receive_buffer.clear()
            self._metrics.closes += 1
            if self._descriptor is not None:
                self._descriptor = TransportDescriptor(
                    transport_type=self._descriptor.transport_type,
                    resource=self._descriptor.resource,
                    normalized_resource=self._descriptor.normalized_resource,
                    opened_at=self._descriptor.opened_at,
                    closed_at=_utc_now(),
                    backend=self._descriptor.backend,
                    metadata=dict(self._descriptor.metadata),
                )
            self._transition(TransportState.CLOSED, "close_succeeded", op)
            self._emit("close", op)
        except Exception as exc:
            self._metrics.failures += 1
            self._transition(TransportState.FAULTED, "close_failed", op)
            raise DriverWriteError(f"TCP close failed: {exc}", operation="Disconnect") from exc

    def cancel(self) -> None:
        super().cancel()
        sock = self._socket
        if sock is not None:
            with contextlib.suppress(OSError):
                sock.shutdown(socket.SHUT_RDWR)

    def _write_locked(self, data: bytes, *, timeout_s: float | None, operation_id: str) -> WriteResult:
        sock = self._socket
        if sock is None:
            raise DriverWriteError("TCP socket is closed", operation=operation_id)
        timeout = self.timeout_s if timeout_s is None else float(timeout_s)
        started = time.monotonic()
        try:
            sock.settimeout(timeout)
            sock.sendall(data)
        except socket.timeout as exc:
            self._metrics.timeouts += 1
            self._metrics.failures += 1
            self._transition(TransportState.FAULTED, "write_timeout", operation_id)
            raise DriverTimeoutError(
                f"TCP write did not complete within {timeout:.3f} s",
                operation=operation_id,
                details={"timeout_s": timeout, "resource": self._resource},
            ) from exc
        except OSError as exc:
            self._metrics.failures += 1
            self._transition(TransportState.FAULTED, "write_failed", operation_id)
            raise DriverWriteError(f"TCP write failed: {exc}", operation=operation_id) from exc
        duration = time.monotonic() - started
        self._metrics.writes += 1
        self._metrics.bytes_written += len(data)
        self._emit("outbound", operation_id, data=data, details={"duration_s": duration})
        return WriteResult(len(data), len(data), duration, operation_id)

    def _read_locked(self, request: ReadRequest, *, timeout_s: float | None, operation_id: str) -> bytes:
        sock = self._socket
        if sock is None:
            raise DriverReadError("TCP socket is closed", operation=operation_id)
        timeout = self.timeout_s if timeout_s is None else float(timeout_s)
        deadline = time.monotonic() + timeout
        while True:
            index = self._receive_buffer.find(request.terminator)
            if index >= 0:
                end = index + len(request.terminator)
                frame = bytes(self._receive_buffer[:end])
                del self._receive_buffer[:end]
                self._metrics.reads += 1
                self._metrics.bytes_read += len(frame)
                self._emit("inbound", operation_id, data=frame)
                return frame
            if len(self._receive_buffer) > request.max_bytes:
                self._metrics.failures += 1
                self._transition(TransportState.FAULTED, "read_oversize", operation_id)
                raise DriverReadError(
                    f"response exceeded {request.max_bytes} bytes",
                    operation=operation_id,
                )
            if self._cancel_event.is_set():
                self._metrics.failures += 1
                self._transition(TransportState.FAULTED, "cancelled", operation_id)
                raise DriverReadError("operation was cancelled", operation=operation_id)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._metrics.timeouts += 1
                self._metrics.failures += 1
                self._transition(TransportState.FAULTED, "read_timeout", operation_id)
                raise DriverTimeoutError(
                    f"no complete TCP response within {timeout:.3f} s",
                    operation=operation_id,
                    details={"timeout_s": timeout, "partial_bytes": len(self._receive_buffer)},
                )
            try:
                sock.settimeout(min(remaining, 0.25))
                chunk = sock.recv(512)
            except socket.timeout:
                continue
            except OSError as exc:
                self._metrics.failures += 1
                self._transition(TransportState.FAULTED, "read_failed", operation_id)
                raise DriverReadError(f"TCP read failed: {exc}", operation=operation_id) from exc
            if chunk == b"":
                self._metrics.failures += 1
                self._transition(TransportState.FAULTED, "peer_closed", operation_id)
                raise DriverReadError("TCP peer closed the connection", operation=operation_id)
            self._receive_buffer.extend(chunk)

    def flush(self, direction) -> None:  # type: ignore[no-untyped-def]
        del direction
        self._receive_buffer.clear()
