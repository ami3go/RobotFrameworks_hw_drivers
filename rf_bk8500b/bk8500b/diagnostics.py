"""Structured audit and metrics interfaces."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable
import uuid

from .enums import CommandOutcome, RiskClass


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    created_utc: datetime
    operation: str
    risk: RiskClass
    outcome: CommandOutcome
    detail: str
    context: dict[str, Any]

    @classmethod
    def create(
        cls,
        operation: str,
        risk: RiskClass,
        outcome: CommandOutcome,
        detail: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> "AuditEvent":
        return cls(
            event_id=str(uuid.uuid4()),
            created_utc=datetime.now(timezone.utc),
            operation=operation,
            risk=risk,
            outcome=outcome,
            detail=detail,
            context=dict(context or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_utc"] = self.created_utc.isoformat()
        data["risk"] = self.risk.value
        data["outcome"] = self.outcome.value
        return data


@runtime_checkable
class AuditSink(Protocol):
    def record(self, event: AuditEvent) -> None: ...


@runtime_checkable
class MetricsSink(Protocol):
    def increment(self, name: str, value: int = 1, **labels: str) -> None: ...
    def observe(self, name: str, value: float, **labels: str) -> None: ...


class NullAuditSink:
    def record(self, event: AuditEvent) -> None:
        return None


class NullMetricsSink:
    def increment(self, name: str, value: int = 1, **labels: str) -> None:
        return None

    def observe(self, name: str, value: float, **labels: str) -> None:
        return None
