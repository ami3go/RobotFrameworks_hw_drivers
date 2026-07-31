"""Canonical byte-oriented transport boundary used by the chamber protocol."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from types import TracebackType

from ..exceptions import DriverStateError, DriverUnsupportedOperationError
from .models import (
    FlushDirection,
    ReadRequest,
    ReplayPolicy,
    TransportCapabilities,
    TransportDescriptor,
    TransportMetrics,
    TransportState,
    WriteResult,
)
from .tracing import TraceObserver, TraceRecord, new_operation_id


_ALLOWED_TRANSITIONS: dict[TransportState, set[TransportState]] = {
    TransportState.CREATED: {TransportState.OPENING, TransportState.CLOSED},
    TransportState.OPENING: {TransportState.OPEN, TransportState.CLOSED, TransportState.FAULTED, TransportState.CLOSING},
    TransportState.OPEN: {TransportState.FAULTED, TransportState.CLOSING},
    TransportState.FAULTED: {TransportState.CLOSING},
    TransportState.CLOSING: {TransportState.CLOSED, TransportState.FAULTED},
    TransportState.CLOSED: {TransportState.OPENING},
}


class BaseTransport(ABC):
    """Common state, tracing and transaction locking for transport backends."""

    transport_type = "unknown"

    def __init__(self, resource: str) -> None:
        self._resource = resource
        self._state = TransportState.CREATED
        self._state_lock = threading.Lock()
        self._transaction_lock = threading.RLock()
        self._observers: list[TraceObserver] = []
        self._descriptor: TransportDescriptor | None = None
        self._metrics = TransportMetrics()
        self._cancel_event = threading.Event()

    @property
    def state(self) -> TransportState:
        with self._state_lock:
            return self._state

    @property
    def is_open(self) -> bool:
        return self.state is TransportState.OPEN

    @property
    def descriptor(self) -> TransportDescriptor:
        if self._descriptor is None:
            raise DriverStateError("transport has never been opened", operation="descriptor")
        return self._descriptor

    @property
    @abstractmethod
    def capabilities(self) -> TransportCapabilities: ...

    @property
    def metrics(self) -> TransportMetrics:
        return self._metrics

    def _transition(self, new_state: TransportState, trigger: str, operation_id: str) -> None:
        with self._state_lock:
            previous = self._state
            if new_state not in _ALLOWED_TRANSITIONS.get(previous, set()):
                raise DriverStateError(
                    f"invalid transport transition {previous.value}->{new_state.value}",
                    operation=trigger,
                    details={"previous": previous.value, "new": new_state.value},
                )
            self._state = new_state
        self._emit(
            "state_changed",
            operation_id,
            details={"previous": previous.value, "new": new_state.value, "trigger": trigger},
        )

    def _require_open(self, operation: str) -> None:
        if not self.is_open:
            raise DriverStateError(
                f"transport must be OPEN for {operation}; current state is {self.state.value}",
                operation=operation,
            )

    def _operation_id(self, operation_id: str | None) -> str:
        return operation_id or new_operation_id()

    def add_trace_observer(self, observer: TraceObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_trace_observer(self, observer: TraceObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def _emit(
        self,
        event: str,
        operation_id: str,
        *,
        data: bytes | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        record = TraceRecord(
            event=event,
            operation_id=operation_id,
            transport=self.transport_type,
            resource=self._resource,
            data_hex=None if data is None else data.hex(),
            data_text=None if data is None else data.decode("latin-1", errors="backslashreplace"),
            details=dict(details or {}),
        )
        for observer in tuple(self._observers):
            observer(record)

    @abstractmethod
    def open(self) -> TransportDescriptor: ...

    @abstractmethod
    def close(self, *, timeout_s: float | None = None) -> None: ...

    def reconnect(self, *, timeout_s: float | None = None) -> TransportDescriptor:
        if not self.capabilities.supports_reconnect:
            raise DriverUnsupportedOperationError("transport reconnect is unavailable", operation="reconnect")
        self.close(timeout_s=timeout_s)
        self._metrics.reconnects += 1
        return self.open()

    def cancel(self) -> None:
        self._cancel_event.set()

    def write(self, data: bytes, *, timeout_s: float | None = None, operation_id: str | None = None) -> WriteResult:
        op = self._operation_id(operation_id)
        with self._transaction_lock:
            self._require_open("write")
            return self._write_locked(data, timeout_s=timeout_s, operation_id=op)

    def read(self, request: ReadRequest, *, timeout_s: float | None = None, operation_id: str | None = None) -> bytes:
        op = self._operation_id(operation_id)
        with self._transaction_lock:
            self._require_open("read")
            return self._read_locked(request, timeout_s=timeout_s, operation_id=op)

    def transact(
        self,
        outbound: bytes,
        response: ReadRequest,
        *,
        timeout_s: float | None = None,
        replay_policy: ReplayPolicy = ReplayPolicy.NEVER,
        operation_id: str | None = None,
    ) -> bytes:
        del replay_policy  # retry decisions are owned by the driver operation layer
        op = self._operation_id(operation_id)
        with self._transaction_lock:
            self._require_open("transact")
            self._metrics.transactions += 1
            self._write_locked(outbound, timeout_s=timeout_s, operation_id=op)
            return self._read_locked(response, timeout_s=timeout_s, operation_id=op)

    @abstractmethod
    def _write_locked(self, data: bytes, *, timeout_s: float | None, operation_id: str) -> WriteResult: ...

    @abstractmethod
    def _read_locked(self, request: ReadRequest, *, timeout_s: float | None, operation_id: str) -> bytes: ...

    def flush(self, direction: FlushDirection) -> None:
        del direction
        raise DriverUnsupportedOperationError("transport flush is unavailable", operation="flush")

    def clear(self) -> None:
        raise DriverUnsupportedOperationError("device clear is unavailable", operation="clear")

    def __enter__(self) -> "BaseTransport":
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        del exc_type, exc, tb
        self.close()
