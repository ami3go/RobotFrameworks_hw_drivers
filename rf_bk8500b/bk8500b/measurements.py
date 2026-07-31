"""Public immutable measurement and advanced configuration models."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import secrets
import time

from .enums import DynamicMode, OperatingMode, Protocol, TriggerEdge, TriggerSource



@dataclass(frozen=True, slots=True)
class InstrumentIdentity:
    manufacturer: str
    model: str
    serial_number: str
    firmware_revision: str
    raw: str


@dataclass(frozen=True, slots=True)
class InstrumentCapabilities:
    model: str
    firmware_revision: str
    protocol: Protocol
    maximum_voltage_v: float
    maximum_current_a: float
    maximum_power_w: float
    minimum_voltage_v: float | None
    minimum_resistance_ohm: float | None
    maximum_resistance_ohm: float | None
    supported_features: frozenset[str]
    experimental_features: frozenset[str]
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Measurement:
    value: float
    unit: str
    monotonic_timestamp_s: float
    wall_timestamp_utc: datetime
    protocol: Protocol
    valid: bool
    raw: str | bytes | None = None

    @classmethod
    def now(
        cls,
        value: float,
        unit: str,
        protocol: Protocol,
        *,
        raw: str | bytes | None = None,
        valid: bool = True,
    ) -> "Measurement":
        if not math.isfinite(value):
            raise ValueError("Measurement value must be finite")
        return cls(
            value=value,
            unit=unit,
            monotonic_timestamp_s=time.monotonic(),
            wall_timestamp_utc=datetime.now(timezone.utc),
            protocol=protocol,
            valid=valid,
            raw=raw,
        )


@dataclass(frozen=True, slots=True)
class AppliedSetpoint:
    requested: float
    applied: float
    unit: str
    wire_value: int | str
    verified: bool


@dataclass(frozen=True, slots=True)
class SelfTestResult:
    code: int
    passed: bool
    raw: str


@dataclass(frozen=True, slots=True)
class SCPIErrorEntry:
    code: int
    message: str
    raw: str


@dataclass(frozen=True, slots=True)
class SlewRate:
    rise_a_per_us: float
    fall_a_per_us: float


@dataclass(frozen=True, slots=True)
class SafetyToken:
    nonce: str
    purpose: str
    issued_monotonic_s: float
    expires_monotonic_s: float

    @classmethod
    def issue(cls, purpose: str, *, valid_for_s: float = 60.0) -> "SafetyToken":
        now = time.monotonic()
        return cls(secrets.token_urlsafe(24), purpose, now, now + valid_for_s)

    def is_valid_for(self, purpose: str) -> bool:
        return self.purpose == purpose and time.monotonic() <= self.expires_monotonic_s


@dataclass(frozen=True, slots=True)
class SafeEnableConfig:
    mode: OperatingMode
    setpoint: float
    current_limit_a: float | None = None
    voltage_limit_v: float | None = None
    power_limit_w: float | None = None
    resistance_limit_ohm: float | None = None
    remote_sense: bool = False
    verify: bool = True


@dataclass(frozen=True, slots=True)
class TransientConfig:
    high_level: float
    high_dwell_s: float
    low_level: float
    low_dwell_s: float
    slew_a_per_us: float
    mode: DynamicMode = DynamicMode.CONTINUOUS


@dataclass(frozen=True, slots=True)
class LEDConfig:
    voltage_v: float
    current_a: float
    resistance_coefficient: float


@dataclass(frozen=True, slots=True)
class OCPTestConfig:
    start_current_a: float
    end_current_a: float
    steps: int
    dwell_s: float
    trigger_voltage_v: float


@dataclass(frozen=True, slots=True)
class OCPTestResult:
    ocp_current_a: float
    maximum_power_w: float
    voltage_at_maximum_v: float
    current_at_maximum_a: float


@dataclass(frozen=True, slots=True)
class TimingTestConfig:
    load_setting_enabled: bool
    mode: OperatingMode
    value: float
    start_source: TriggerSource
    start_edge: TriggerEdge
    start_level: float
    end_source: TriggerSource
    end_edge: TriggerEdge
    end_level: float


@dataclass(frozen=True, slots=True)
class TimingTestResult:
    duration_s: float


@dataclass(frozen=True, slots=True)
class ListStep:
    current_a: float
    dwell_s: float


@dataclass(frozen=True, slots=True)
class ListConfig:
    steps: tuple[ListStep, ...]
    repeat_count: int = 1


@dataclass(frozen=True, slots=True)
class ListRunResult:
    completed: bool
    maximum_voltage_v: float | None
    minimum_voltage_v: float | None
    maximum_current_a: float | None
    minimum_current_a: float | None
    experimental: bool = True
