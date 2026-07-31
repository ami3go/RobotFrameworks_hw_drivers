"""RFDS-004 transport models used by TCP and simulator backends."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class TransportState(StrEnum):
    CREATED = "CREATED"
    OPENING = "OPENING"
    OPEN = "OPEN"
    FAULTED = "FAULTED"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


class ReplayPolicy(StrEnum):
    NEVER = "NEVER"
    SAFE_QUERY = "SAFE_QUERY"


class FlushDirection(StrEnum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    BOTH = "BOTH"


@dataclass(frozen=True, slots=True)
class ReadRequest:
    terminator: bytes = b"\r"
    max_bytes: int = 4096

    def __post_init__(self) -> None:
        if not self.terminator:
            raise ValueError("ReadRequest.terminator must not be empty")
        if self.max_bytes < len(self.terminator):
            raise ValueError("ReadRequest.max_bytes is smaller than the terminator")


@dataclass(frozen=True, slots=True)
class TransportDescriptor:
    transport_type: str
    resource: str
    normalized_resource: str
    opened_at: str | None
    closed_at: str | None
    backend: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class WriteResult:
    requested_bytes: int
    written_bytes: int
    duration_s: float
    operation_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TransportCapabilities:
    supports_reconnect: bool
    supports_cancel: bool
    supports_flush: bool
    supports_device_clear: bool
    transaction_atomic: bool = True
    byte_oriented: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TransportMetrics:
    opens: int = 0
    closes: int = 0
    reconnects: int = 0
    writes: int = 0
    reads: int = 0
    transactions: int = 0
    bytes_written: int = 0
    bytes_read: int = 0
    failures: int = 0
    timeouts: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)
