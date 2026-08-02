"""Typed result models returned by the SLCAN core driver."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanFrame:
    """One CAN frame, transmitted or received.

    ``arbitration_id`` is 0-0x7FF for a standard (11-bit) frame or
    0-0x1FFFFFFF for an extended (29-bit) frame, per ``extended``.
    """

    arbitration_id: int
    data: bytes
    dlc: int
    extended: bool = False
    remote: bool = False
    timestamp_ms: int | None = None


@dataclass(frozen=True)
class AdapterStatus:
    """Parsed ``F`` status-flag response.

    Bit assignments confirmed against the source cited in the task document
    (task §2) — not asserted here independently of that citation.
    """

    rx_queue_full: bool
    tx_queue_full: bool
    error_warning: bool
    data_overrun: bool
    error_passive: bool
    arbitration_lost: bool
    bus_error: bool
    raw_flags: int

    @property
    def has_fault(self) -> bool:
        return self.error_passive or self.arbitration_lost or self.bus_error


@dataclass(frozen=True)
class AdapterIdentity:
    """Combined ``V`` (version) / ``N`` (serial number) response."""

    hardware_version: str
    software_version: str
    serial_number: str
    raw: str


@dataclass(frozen=True)
class ConnectionState:
    """RFDS-002 Section 12.1 normalized connection-state dictionary, as a typed object."""

    alias: str
    resource: str | None
    connected: bool
    communication_ok: bool
    transport: str | None
    identity: str | None
    timeout_s: float | None
    state: str

    def as_dict(self) -> dict[str, object]:
        return {
            "alias": self.alias,
            "resource": self.resource,
            "connected": self.connected,
            "communication_ok": self.communication_ok,
            "transport": self.transport,
            "identity": self.identity,
            "timeout_s": self.timeout_s,
            "state": self.state,
        }
