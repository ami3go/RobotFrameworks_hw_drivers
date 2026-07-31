"""Shared immutable data models used by the Robot adapter and core service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class SessionState(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    CONFIGURED = "CONFIGURED"
    BUSY = "BUSY"
    WAITING = "WAITING"
    CANCELLING = "CANCELLING"
    RECOVERING = "RECOVERING"
    ERROR = "ERROR"
    CLOSING = "CLOSING"


class IdempotencyClass(StrEnum):
    IDEMPOTENT = "IDEMPOTENT"
    IDEMPOTENT_WITH_TOKEN = "IDEMPOTENT_WITH_TOKEN"
    NON_IDEMPOTENT = "NON_IDEMPOTENT"
    UNKNOWN = "UNKNOWN"


class RiskClass(StrEnum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class DriverMetadata:
    name: str
    package_version: str
    api_version: str
    api_spec: str
    api_spec_version: str
    robot_framework_min_version: str
    python_min_version: str
    library_scope: str
    transport_types: tuple[str, ...]
    capability_ids: tuple[str, ...]
    simulation_supported: bool
    identity_source: str
    release_class: str
    rfds_core_version: str | None = None
    rfds_core_version_status: str = "UNAVAILABLE"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["transport_types"] = list(self.transport_types)
        result["capability_ids"] = list(self.capability_ids)
        return result


@dataclass(frozen=True, slots=True)
class InstrumentIdentity:
    identity: str
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    manufacturing_year: str | None
    raw: str
    source: str = "device_query"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConnectionRequest:
    resource: str
    alias: str = "default"
    timeout_s: float = 5.0
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ConnectionRecord:
    alias: str
    resource: str
    state: SessionState = SessionState.DISCONNECTED
    communication_ok: bool | None = None
    identity: InstrumentIdentity | None = None
    timeout_s: float = 5.0
    connected_at: str | None = None
    last_communication_at: str | None = None
    last_error: dict[str, Any] | None = None
    generation: int = 0

    def to_robot_dict(self) -> dict[str, Any]:
        return {
            "alias": self.alias,
            "resource": self.resource,
            "connected": self.state in {SessionState.CONNECTED, SessionState.CONFIGURED, SessionState.BUSY, SessionState.WAITING},
            "state": self.state.value.lower(),
            "communication_ok": self.communication_ok,
            "identity": None if self.identity is None else self.identity.identity,
            "timeout_s": self.timeout_s,
            "connected_at": self.connected_at,
            "last_communication_at": self.last_communication_at,
            "generation": self.generation,
            "last_error": self.last_error,
        }
