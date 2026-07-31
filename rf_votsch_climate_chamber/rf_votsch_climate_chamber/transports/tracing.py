"""Protocol-boundary trace records for RFDS-019 correlation."""

from __future__ import annotations

import datetime as dt
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def new_operation_id() -> str:
    return f"op-{uuid.uuid4().hex[:8]}"


@dataclass(frozen=True, slots=True)
class TraceRecord:
    event: str
    operation_id: str
    transport: str
    resource: str
    timestamp: str = field(default_factory=utc_now)
    monotonic_s: float = field(default_factory=time.monotonic)
    data_hex: str | None = None
    data_text: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TraceObserver(Protocol):
    def __call__(self, record: TraceRecord) -> None: ...


class MemoryTraceObserver:
    """Thread-safe enough append-only observer for tests and evidence export."""

    def __init__(self) -> None:
        self.records: list[TraceRecord] = []

    def __call__(self, record: TraceRecord) -> None:
        self.records.append(record)

    def clear(self) -> None:
        self.records.clear()

    def to_list(self) -> list[dict[str, Any]]:
        return [record.to_dict() for record in self.records]
