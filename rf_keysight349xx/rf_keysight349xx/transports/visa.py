"""Optional PyVISA byte transport.

No VISA resource manager or hardware is touched until ``open()`` is called.
"""
from __future__ import annotations

import time
import uuid
from threading import RLock

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


class VisaTransport:
    def __init__(self, resource: str, *, backend: str | None = None, default_timeout_s: float = 5.0) -> None:
        self.resource = resource
        self.backend = backend
        self.default_timeout_s = float(default_timeout_s)
        self._state = TransportState.CREATED
        self._rm = None
        self._inst = None
        self._lock = RLock()
        self._session_id = str(uuid.uuid4())
        self._descriptor = TransportDescriptor(
            kind="visa", endpoint=resource, backend="pyvisa", backend_version=None,
            session_id=self._session_id, display_name=resource,
        )
        self._caps = TransportCapabilities(supports_device_clear=True, supports_resource_discovery=True)
        self._metrics = TransportMetrics()
        self._trace: list[TraceRecord] = []
        self._observers = []

    @property
    def state(self): return self._state
    @property
    def is_open(self): return self._state == TransportState.OPEN
    @property
    def descriptor(self): return self._descriptor
    @property
    def capabilities(self): return self._caps
    @property
    def metrics(self): return self._metrics
    @property
    def trace_records(self): return list(self._trace)

    def _record(self, direction, payload, operation_id):
        r = TraceRecord(direction, bytes(payload), operation_id)
        self._trace.append(r)
        for observer in tuple(self._observers):
            try: observer(r)
            except Exception: self._metrics.trace_drop_count += 1

    def open(self):
        if self.is_open: return self._descriptor
        self._state = TransportState.OPENING
        try:
            import pyvisa
            self._rm = pyvisa.ResourceManager(self.backend) if self.backend else pyvisa.ResourceManager()
            self._inst = self._rm.open_resource(self.resource)
            self._inst.timeout = int(self.default_timeout_s * 1000)
            try: self._inst.read_termination = "\n"
            except Exception: pass
            try: self._inst.write_termination = None
            except Exception: pass
            try:
                version = getattr(pyvisa, "__version__", None)
                self._descriptor = TransportDescriptor(
                    kind="visa", endpoint=self.resource, backend="pyvisa", backend_version=version,
                    session_id=self._session_id, display_name=self.resource,
                )
            except Exception:
                pass
            self._state = TransportState.OPEN
            return self._descriptor
        except Exception:
            self._state = TransportState.FAULTED
            self._safe_cleanup()
            raise

    def _safe_cleanup(self):
        if self._inst is not None:
            try: self._inst.close()
            except Exception: pass
            self._inst = None
        if self._rm is not None:
            try: self._rm.close()
            except Exception: pass
            self._rm = None

    def close(self, *, timeout_s=None):
        if self._state == TransportState.CLOSED: return
        self._state = TransportState.CLOSING
        self._safe_cleanup()
        self._state = TransportState.CLOSED

    def reconnect(self, *, timeout_s=None):
        self.close(timeout_s=timeout_s)
        return self.open()

    def cancel(self):
        self._state = TransportState.FAULTED

    def _require(self):
        if not self.is_open or self._inst is None:
            raise RuntimeError("VISA transport is not open")

    def _apply_timeout(self, timeout_s):
        if timeout_s is not None and self._inst is not None:
            self._inst.timeout = max(1, int(float(timeout_s) * 1000))

    def write(self, data: bytes, *, timeout_s=None, operation_id=None):
        self._require(); self._apply_timeout(timeout_s)
        started = time.monotonic()
        with self._lock:
            self._record("TX", data, operation_id)
            count = int(self._inst.write_raw(bytes(data)))
        self._metrics.write_count += 1; self._metrics.bytes_written += count
        if count != len(data):
            raise RuntimeError(f"short VISA write: {count}/{len(data)}")
        return WriteResult(len(data), count, time.monotonic()-started, True, operation_id, self._session_id)

    def read(self, request: ReadRequest, *, timeout_s=None, operation_id=None):
        self._require(); self._apply_timeout(timeout_s)
        with self._lock:
            data = bytes(self._inst.read_raw())
        if len(data) > request.maximum_length:
            raise RuntimeError("VISA response exceeds maximum_length")
        self._record("RX", data, operation_id)
        self._metrics.read_count += 1; self._metrics.bytes_read += len(data)
        if not request.include_terminator and request.terminator and data.endswith(request.terminator):
            data = data[:-len(request.terminator)]
        if not data and not request.allow_empty:
            raise RuntimeError("empty VISA response")
        return data

    def transact(self, outbound: bytes, response: ReadRequest, *, timeout_s=None, replay_policy=ReplayPolicy.NEVER, operation_id=None):
        with self._lock:
            self._metrics.transaction_count += 1
            self.write(outbound, timeout_s=timeout_s, operation_id=operation_id)
            return self.read(response, timeout_s=timeout_s, operation_id=operation_id)

    def flush(self, direction: FlushDirection):
        self._require()
        try:
            import pyvisa.constants as c
            mask = 0
            if direction in {FlushDirection.INPUT, FlushDirection.BOTH}: mask |= int(c.BufferOperation.discard_read_buffer)
            if direction in {FlushDirection.OUTPUT, FlushDirection.BOTH}: mask |= int(c.BufferOperation.discard_write_buffer)
            if mask: self._inst.flush(mask)
        except Exception:
            pass

    def clear(self):
        self._require(); self._inst.clear()
    def add_trace_observer(self, observer):
        if observer not in self._observers: self._observers.append(observer)
    def remove_trace_observer(self, observer):
        if observer in self._observers: self._observers.remove(observer)
    def __enter__(self): self.open(); return self
    def __exit__(self, exc_type, exc, tb): self.close(); return False
