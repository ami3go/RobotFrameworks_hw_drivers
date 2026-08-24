"""Strict stateful protocol-boundary simulator for the initial driver slice."""
from __future__ import annotations

import re
import time
import uuid
from collections import deque
from threading import RLock
from typing import Callable

from .base import (
    FlushDirection,
    ReadRequest,
    ReplayPolicy,
    TraceRecord,
    TransportCapabilities,
    TransportDescriptor,
    TransportMetrics,
    TransportState,
    WriteResult,
)


class SimulatorTransport:
    """ASCII SCPI simulator for 34970A/34972A discovery and error handling.

    The simulator is intentionally strict: unsupported queries raise instead of
    returning fabricated success.  Unknown commands are placed in the simulated
    device error queue, matching SCPI-style rejection semantics.
    """

    def __init__(
        self,
        model: str = "34972A",
        modules: dict[int, str] | None = None,
        *,
        strict: bool = True,
    ) -> None:
        model = str(model).strip().upper()
        if model not in {"34970A", "34972A"}:
            raise ValueError("simulator model must be 34970A or 34972A")
        self.model = model
        self._modules = dict(modules or {100: "34901A", 200: "0", 300: "34907A"})
        for slot in (100, 200, 300):
            self._modules.setdefault(slot, "0")
        self.strict = strict
        self._state = TransportState.CREATED
        self._session_id = str(uuid.uuid4())
        self._descriptor = TransportDescriptor(
            kind="simulator",
            endpoint=f"SIM::{model}",
            backend="rf_keysight349xx.simulator",
            backend_version="1",
            session_id=self._session_id,
            display_name=f"SIM::{model}",
        )
        self._capabilities = TransportCapabilities(supports_device_clear=True)
        self._metrics = TransportMetrics()
        self._pending: deque[bytes] = deque()
        self._errors: deque[tuple[int, str]] = deque()
        self._lock = RLock()
        self._trace: list[TraceRecord] = []
        self._observers: list[Callable[[TraceRecord], None]] = []
        self._cancelled = False
        self.response_delay_s = 0.0
        self.fail_next_timeout = False
        self.malformed_next_response: bytes | None = None

    @property
    def state(self):
        return self._state

    @property
    def is_open(self) -> bool:
        return self._state == TransportState.OPEN

    @property
    def descriptor(self):
        return self._descriptor

    @property
    def capabilities(self):
        return self._capabilities

    @property
    def metrics(self):
        return self._metrics

    @property
    def trace_records(self) -> list[TraceRecord]:
        return list(self._trace)

    def _record(self, direction: str, payload: bytes, operation_id: str | None) -> None:
        record = TraceRecord(direction=direction, payload=bytes(payload), operation_id=operation_id)
        self._trace.append(record)
        for observer in tuple(self._observers):
            try:
                observer(record)
            except Exception:
                self._metrics.trace_drop_count += 1

    def open(self):
        if self.is_open:
            return self._descriptor
        self._state = TransportState.OPENING
        self._cancelled = False
        self._state = TransportState.OPEN
        return self._descriptor

    def close(self, *, timeout_s: float | None = None) -> None:
        if self._state == TransportState.CLOSED:
            return
        self._state = TransportState.CLOSING
        self._pending.clear()
        self._state = TransportState.CLOSED

    def reconnect(self, *, timeout_s: float | None = None):
        self.close(timeout_s=timeout_s)
        return self.open()

    def cancel(self) -> None:
        self._cancelled = True

    def _require_open(self) -> None:
        if not self.is_open:
            raise RuntimeError("simulator transport is not open")

    def _identity(self) -> str:
        if self.model == "34970A":
            return "HEWLETT-PACKARD,34970A,0,13-2-2"
        return "Keysight Technologies,34972A,MY12345678,1.01-1.00-01-0002"

    def _module_response(self, slot: int) -> str:
        module = self._modules[slot]
        manufacturer = "HEWLETT-PACKARD" if self.model == "34970A" else "Keysight Technologies"
        fw = "0" if module == "0" else "1.0"
        return f"{manufacturer},{module},0,{fw}"

    def _execute(self, command: str) -> bytes | None:
        normalized = command.strip()
        upper = normalized.upper()
        if upper == "*IDN?":
            return (self._identity() + "\n").encode("ascii")
        if upper in {"SYST:VERS?", "SYSTEM:VERSION?"}:
            return b"1994.0\n"
        match = re.fullmatch(r"SYST(?:EM)?:CTYP(?:E)?\?\s+(100|200|300)", upper)
        if match:
            return (self._module_response(int(match.group(1))) + "\n").encode("ascii")
        if upper in {"SYST:ERR?", "SYSTEM:ERROR?"}:
            if self._errors:
                code, message = self._errors.popleft()
                return f'{code},"{message}"\n'.encode("ascii")
            return b'+0,"No error"\n'
        if upper == "*CLS":
            self._errors.clear()
            return None
        if upper == "*OPC?":
            return b"+1\n"
        if upper.endswith("?"):
            if self.strict:
                raise RuntimeError(f"unsupported simulator query: {normalized}")
            self._errors.append((-113, "Undefined header"))
            return b"\n"
        self._errors.append((-113, "Undefined header"))
        return None

    def write(self, data: bytes, *, timeout_s: float | None = None, operation_id: str | None = None):
        self._require_open()
        started = time.monotonic()
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("transport data must be bytes")
        payload = bytes(data)
        with self._lock:
            self._record("TX", payload, operation_id)
            self._metrics.bytes_written += len(payload)
            self._metrics.write_count += 1
            response = self._execute(payload.decode("ascii", errors="strict").rstrip("\r\n"))
            if response is not None:
                self._pending.append(response)
        return WriteResult(
            requested_bytes=len(payload),
            accepted_bytes=len(payload),
            duration_s=time.monotonic() - started,
            complete=True,
            operation_id=operation_id,
            session_id=self._session_id,
        )

    def read(self, request: ReadRequest, *, timeout_s: float | None = None, operation_id: str | None = None) -> bytes:
        self._require_open()
        if self.fail_next_timeout:
            self.fail_next_timeout = False
            self._metrics.error_count += 1
            raise TimeoutError("simulated read timeout")
        if self.response_delay_s:
            if timeout_s is not None and self.response_delay_s > timeout_s:
                self._metrics.error_count += 1
                raise TimeoutError("simulated read timeout")
            time.sleep(self.response_delay_s)
        with self._lock:
            if self.malformed_next_response is not None:
                payload = self.malformed_next_response
                self.malformed_next_response = None
            elif self._pending:
                payload = self._pending.popleft()
            elif request.allow_empty:
                payload = b""
            else:
                raise TimeoutError("no simulated response available")
            if len(payload) > request.maximum_length:
                raise RuntimeError("simulated response exceeds maximum_length")
            self._record("RX", payload, operation_id)
            self._metrics.bytes_read += len(payload)
            self._metrics.read_count += 1
            if not request.include_terminator and request.terminator and payload.endswith(request.terminator):
                payload = payload[: -len(request.terminator)]
            return payload

    def transact(self, outbound: bytes, response: ReadRequest, *, timeout_s: float | None = None, replay_policy: ReplayPolicy = ReplayPolicy.NEVER, operation_id: str | None = None) -> bytes:
        with self._lock:
            self._metrics.transaction_count += 1
            self.write(outbound, timeout_s=timeout_s, operation_id=operation_id)
            return self.read(response, timeout_s=timeout_s, operation_id=operation_id)

    def flush(self, direction: FlushDirection) -> None:
        if direction in {FlushDirection.INPUT, FlushDirection.BOTH}:
            self._pending.clear()

    def clear(self) -> None:
        self._pending.clear()
        self._errors.clear()

    def add_trace_observer(self, observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_trace_observer(self, observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
