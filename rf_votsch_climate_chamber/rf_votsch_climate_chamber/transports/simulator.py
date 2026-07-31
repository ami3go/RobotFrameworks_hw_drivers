"""Deterministic in-process Vötsch protocol simulator transport."""

from __future__ import annotations

import datetime as dt
import time
from dataclasses import dataclass

from ..exceptions import DriverReadError, DriverTimeoutError
from .base import BaseTransport
from .models import ReadRequest, TransportCapabilities, TransportDescriptor, TransportState, WriteResult

SEPARATOR = "¶"


def _utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass(slots=True)
class SimulatorState:
    setpoint_c: float = 25.0
    temperature_c: float = 25.0
    running: bool = False
    dryer: bool = False
    compressed_air: bool = False
    gradient_up_c_per_min: float = 2.0
    gradient_down_c_per_min: float = 2.0
    status: str = "READY"
    model: str = "VT4002EMC-SIM"
    serial: str = "SIM-2604"
    manufacturing_year: str = "2026"
    temperature_step_c: float = 20.0
    fault_mode: str | None = None


class SimulatorTransport(BaseTransport):
    transport_type = "simulator"

    def __init__(self, profile: str = "default", *, state: SimulatorState | None = None) -> None:
        super().__init__(f"SIM::{profile}")
        self.profile = profile
        self.simulator_state = state or SimulatorState()
        self._pending_response: bytes | None = None

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
            self.close()
        self._transition(TransportState.OPENING, "open", op)
        now = _utc_now()
        self._descriptor = TransportDescriptor(
            transport_type="simulator",
            resource=self._resource,
            normalized_resource=self._resource,
            opened_at=now,
            closed_at=None,
            backend="in_process",
            metadata={"profile": self.profile},
        )
        self._metrics.opens += 1
        self._cancel_event.clear()
        self._transition(TransportState.OPEN, "open_succeeded", op)
        self._emit("open", op)
        return self._descriptor

    def close(self, *, timeout_s: float | None = None) -> None:
        del timeout_s
        if self.state is TransportState.CREATED:
            self._transition(TransportState.CLOSED, "close", "transport.close")
            return
        if self.state is TransportState.CLOSED:
            return
        if self.state not in {TransportState.OPEN, TransportState.FAULTED}:
            return
        op = self._operation_id("transport.close")
        self._transition(TransportState.CLOSING, "close", op)
        self._pending_response = None
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

    def _write_locked(self, data: bytes, *, timeout_s: float | None, operation_id: str) -> WriteResult:
        del timeout_s
        started = time.monotonic()
        self._metrics.writes += 1
        self._metrics.bytes_written += len(data)
        self._emit("outbound", operation_id, data=data)
        self._pending_response = self._process(data)
        return WriteResult(len(data), len(data), time.monotonic() - started, operation_id)

    def _read_locked(self, request: ReadRequest, *, timeout_s: float | None, operation_id: str) -> bytes:
        timeout = 5.0 if timeout_s is None else float(timeout_s)
        mode = self.simulator_state.fault_mode
        self.simulator_state.fault_mode = None
        if mode == "timeout":
            self._metrics.timeouts += 1
            raise DriverTimeoutError(
                f"simulated timeout after {timeout:.3f} s",
                operation=operation_id,
                details={"timeout_s": timeout},
            )
        if mode == "disconnect":
            self._transition(TransportState.FAULTED, "simulated_disconnect", operation_id)
            raise DriverReadError("simulated peer disconnect", operation=operation_id)
        if mode == "malformed":
            response = b"BROKEN\r"
        elif mode == "incomplete":
            response = b"1\xb6PARTIAL"
        else:
            response = self._pending_response
        self._pending_response = None
        if response is None:
            raise DriverReadError("simulator has no pending response", operation=operation_id)
        if len(response) > request.max_bytes:
            raise DriverReadError("simulator response exceeds maximum", operation=operation_id)
        if not response.endswith(request.terminator):
            raise DriverTimeoutError(
                "simulator produced an incomplete frame",
                operation=operation_id,
                details={"partial_bytes": len(response)},
            )
        self._metrics.reads += 1
        self._metrics.bytes_read += len(response)
        self._emit("inbound", operation_id, data=response)
        return response

    def flush(self, direction) -> None:  # type: ignore[no-untyped-def]
        del direction
        self._pending_response = None

    @staticmethod
    def _response(value: object | None = None) -> bytes:
        text = "1" if value is None else f"1{SEPARATOR}{value}"
        return text.encode("latin-1") + b"\r"

    def _process(self, data: bytes) -> bytes:
        raw = data.rstrip(b"\r")
        fields = raw.decode("latin-1").split(SEPARATOR)
        if len(fields) < 2:
            return b"0\r"
        command, args = fields[0], fields[2:]
        state = self.simulator_state
        if command == "99997":
            item = args[0] if args else "1"
            return self._response(
                {"1": state.model, "2": state.manufacturing_year, "3": state.serial}.get(item, "UNAVAILABLE")
            )
        if command == "10012":
            return self._response(state.status)
        if command == "11001":
            state.setpoint_c = float(args[-1])
            return self._response()
        if command == "11002":
            return self._response(f"{state.setpoint_c:.2f}")
        if command == "11004":
            if state.running:
                delta = state.setpoint_c - state.temperature_c
                step = min(abs(delta), state.temperature_step_c)
                state.temperature_c += step if delta >= 0 else -step
            return self._response(f"{state.temperature_c:.2f}")
        if command == "14001":
            channel = int(args[0])
            value = bool(int(args[1]))
            if channel == 1:
                state.running = value
            elif channel == 7:
                state.compressed_air = value
            elif channel == 8:
                state.dryer = value
            return self._response()
        if command == "14003":
            channel = int(args[0])
            value = {1: state.running, 7: state.compressed_air, 8: state.dryer}.get(channel, False)
            return self._response(1 if value else 0)
        if command == "11066":
            return self._response(f"{state.gradient_up_c_per_min:.2f}")
        if command == "11068":
            state.gradient_up_c_per_min = float(args[-1])
            return self._response()
        if command == "11070":
            return self._response(f"{state.gradient_down_c_per_min:.2f}")
        if command == "11072":
            state.gradient_down_c_per_min = float(args[-1])
            return self._response()
        return b"0\r"
