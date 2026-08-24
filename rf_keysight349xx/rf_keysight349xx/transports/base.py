"""Byte-oriented RFDS-004-compatible transport boundary."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable


class TransportState(str, Enum):
    CREATED = "created"
    OPENING = "opening"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    FAULTED = "faulted"


class ReplayPolicy(str, Enum):
    NEVER = "never"
    IF_IDEMPOTENT = "if_idempotent"


class FlushDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    BOTH = "both"


class ReadMode(str, Enum):
    UNTIL_TERMINATOR = "until_terminator"
    EXACT_LENGTH = "exact_length"
    UP_TO_LENGTH = "up_to_length"
    AVAILABLE = "available"
    BACKEND_DEFINED_MESSAGE = "backend_defined_message"


@dataclass(frozen=True)
class ReadRequest:
    mode: ReadMode = ReadMode.UNTIL_TERMINATOR
    maximum_length: int = 1024 * 1024
    terminator: bytes = b"\n"
    include_terminator: bool = False
    allow_empty: bool = False

    def __post_init__(self) -> None:
        if self.maximum_length <= 0:
            raise ValueError("maximum_length must be positive")
        if self.mode == ReadMode.UNTIL_TERMINATOR and not self.terminator:
            raise ValueError("terminator is required for UNTIL_TERMINATOR")


@dataclass(frozen=True)
class WriteResult:
    requested_bytes: int
    accepted_bytes: int
    duration_s: float
    complete: bool
    operation_id: str | None = None
    session_id: str | None = None


@dataclass(frozen=True)
class TransportDescriptor:
    kind: str
    endpoint: str
    backend: str
    backend_version: str | None
    session_id: str
    display_name: str


@dataclass(frozen=True)
class TransportCapabilities:
    can_read: bool = True
    can_write: bool = True
    supports_transactions: bool = True
    supports_binary_transfers: bool = False
    supports_resource_discovery: bool = False
    supports_input_flush: bool = True
    supports_output_flush: bool = True
    supports_device_clear: bool = False
    supports_exclusive_locking: bool = True
    supports_transport_tracing: bool = True
    supports_reconnect: bool = True


@dataclass
class TransportMetrics:
    bytes_written: int = 0
    bytes_read: int = 0
    write_count: int = 0
    read_count: int = 0
    transaction_count: int = 0
    error_count: int = 0
    trace_drop_count: int = 0


@dataclass(frozen=True)
class TraceRecord:
    direction: str
    payload: bytes
    operation_id: str | None


@runtime_checkable
class Transport(Protocol):
    @property
    def state(self) -> TransportState: ...
    @property
    def is_open(self) -> bool: ...
    @property
    def descriptor(self) -> TransportDescriptor: ...
    @property
    def capabilities(self) -> TransportCapabilities: ...
    @property
    def metrics(self) -> TransportMetrics: ...
    def open(self) -> TransportDescriptor: ...
    def close(self, *, timeout_s: float | None = None) -> None: ...
    def reconnect(self, *, timeout_s: float | None = None) -> TransportDescriptor: ...
    def cancel(self) -> None: ...
    def write(self, data: bytes, *, timeout_s: float | None = None, operation_id: str | None = None) -> WriteResult: ...
    def read(self, request: ReadRequest, *, timeout_s: float | None = None, operation_id: str | None = None) -> bytes: ...
    def transact(self, outbound: bytes, response: ReadRequest, *, timeout_s: float | None = None, replay_policy: ReplayPolicy = ReplayPolicy.NEVER, operation_id: str | None = None) -> bytes: ...
    def flush(self, direction: FlushDirection) -> None: ...
    def clear(self) -> None: ...
    def add_trace_observer(self, observer) -> None: ...
    def remove_trace_observer(self, observer) -> None: ...
