"""Status, health, diagnostics, and safety result models."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from .enums import OperatingMode, ProtectionFlag, Protocol, SessionState
from .measurements import AppliedSetpoint, InstrumentIdentity, Measurement


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_json_value(v) for v in value]
    return value


@dataclass(frozen=True, slots=True)
class DeviceStatus:
    input_enabled: bool | None
    short_enabled: bool | None
    operating_mode: OperatingMode | None
    status_byte: int | None
    questionable_condition: int | None
    operation_condition: int | None
    protection_flags: ProtectionFlag
    unknown_bits: int
    synchronized: bool


@dataclass(frozen=True, slots=True)
class HealthReport:
    healthy: bool
    session_state: SessionState
    identity: InstrumentIdentity | None
    latency_s: float | None
    consecutive_failures: int
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {k: _json_value(v) for k, v in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class DiagnosticSnapshot:
    created_utc: datetime
    session_state: SessionState
    protocol: Protocol
    connected: bool
    identity: InstrumentIdentity | None
    status: DeviceStatus | None
    last_error: str | None
    counters: dict[str, int | float]
    partial: bool
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {k: _json_value(v) for k, v in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class SafeEnableResult:
    input_enabled: bool
    input_off_after_failure: bool | None
    applied_setpoint: AppliedSetpoint
    status: DeviceStatus
    audit_event_id: str


@dataclass(frozen=True, slots=True)
class MeasurementSnapshot:
    voltage: Measurement
    current: Measurement
    power: Measurement
    resistance: Measurement | None
    status: DeviceStatus | None
