"""Conversion helpers used by the Robot Framework adapter."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum, IntFlag
from pathlib import Path
from typing import Any

_TRUE = {"1", "true", "yes", "on", "enabled", "enable"}
_FALSE = {"0", "false", "no", "off", "disabled", "disable", "none", ""}


def as_bool(value: Any, *, name: str = "value") -> bool:
    """Convert common Robot Framework scalar values to ``bool``."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    token = str(value).strip().lower()
    if token in _TRUE:
        return True
    if token in _FALSE:
        return False
    raise ValueError(f"{name} must be a boolean value, got {value!r}")


def as_float(value: Any, *, name: str = "value") -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric, got {value!r}") from exc
    return result


def as_int(value: Any, *, name: str = "value") -> int:
    try:
        if isinstance(value, str) and any(char in value.lower() for char in (".", "e")):
            number = float(value)
            if not number.is_integer():
                raise ValueError
            return int(number)
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc


def to_robot(value: Any) -> Any:
    """Convert driver return models to Robot-friendly scalars, lists, and dictionaries."""
    if is_dataclass(value):
        return {key: to_robot(item) for key, item in asdict(value).items()}
    if isinstance(value, IntFlag):
        return int(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): to_robot(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [to_robot(item) for item in value]
    return value
