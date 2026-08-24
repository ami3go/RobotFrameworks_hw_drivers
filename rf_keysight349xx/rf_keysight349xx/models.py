"""Driver-domain data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from time import monotonic
from typing import Any


@dataclass(frozen=True)
class InstrumentIdentity:
    manufacturer: str
    model: str
    serial_number: str
    firmware_version: str
    raw_response: str

    def display(self) -> str:
        return self.raw_response.strip()

    def as_dict(self) -> dict[str, str]:
        return {
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "raw_response": self.raw_response,
        }


@dataclass(frozen=True)
class ModuleInfo:
    slot: int
    manufacturer: str
    model: str
    serial_number: str
    firmware_version: str
    raw_response: str

    @property
    def installed(self) -> bool:
        return self.model != "0"

    def as_dict(self) -> dict[str, Any]:
        return {
            "slot": self.slot,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "installed": self.installed,
            "raw_response": self.raw_response,
        }


@dataclass
class DriverSession:
    alias: str
    resource: str
    transport: Any
    timeout_s: float
    simulated: bool
    transport_kind: str
    connected: bool = False
    communication_ok: bool = False
    state: str = "connecting"
    identity: InstrumentIdentity | None = None
    modules: dict[int, ModuleInfo] = field(default_factory=dict)
    probe_identity_raw: str | None = None
    connected_at_monotonic: float = field(default_factory=monotonic)
    lock: Lock = field(default_factory=Lock, repr=False)

    def state_dict(self) -> dict[str, Any]:
        return {
            "alias": self.alias,
            "resource": self.resource,
            "connected": bool(self.connected),
            "communication_ok": bool(self.communication_ok),
            "transport": self.transport_kind,
            "identity": self.identity.display() if self.identity else None,
            "timeout_s": float(self.timeout_s),
            "state": self.state,
            "simulated": bool(self.simulated),
        }
