"""Shared protocol command metadata."""
from __future__ import annotations

from dataclasses import dataclass

from ..enums import RiskClass


@dataclass(frozen=True, slots=True)
class CommandPolicy:
    command_id: str
    protocol: str
    risk: RiskClass
    idempotent: bool
    retry_allowed: bool
    verification: str | None
    stability: str
