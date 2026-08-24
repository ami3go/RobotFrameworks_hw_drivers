"""Public-boundary value conversion and validation helpers."""
from __future__ import annotations

import math

from .exceptions import DriverValidationError


def as_timeout(value: object, *, name: str = "timeout_s") -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DriverValidationError(f"{name} must be a finite positive number") from exc
    if not math.isfinite(result) or result <= 0:
        raise DriverValidationError(f"{name} must be a finite positive number")
    return result


def as_alias(value: object | None, *, default: str | None = None) -> str | None:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        raise DriverValidationError("alias must not be empty")
    return text


def as_resource(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        raise DriverValidationError("resource must not be empty")
    return text


def as_bool(value: object, *, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise DriverValidationError(f"{name} must be Boolean")


def as_slot(value: object) -> int:
    try:
        slot = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise DriverValidationError("slot must be 100, 200, or 300") from exc
    if slot not in (100, 200, 300):
        raise DriverValidationError("slot must be 100, 200, or 300")
    return slot
