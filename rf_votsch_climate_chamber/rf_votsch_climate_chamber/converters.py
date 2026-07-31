"""Central Robot/Python boundary conversion and validation helpers."""

from __future__ import annotations

import math
import re
from typing import Any

from .exceptions import DriverArgumentTypeError, DriverArgumentValueError, DriverRangeError

_DURATION_PATTERN = re.compile(
    r"^\s*(?P<value>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?P<unit>ms|milliseconds?|s|sec(?:onds?)?|m|min(?:utes?)?|h|hours?)?\s*$",
    re.IGNORECASE,
)
_ALIAS_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")


def to_float(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise DriverArgumentTypeError(f"<{name}> must be numeric, received bool", operation="validate")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DriverArgumentTypeError(
            f"<{name}> must be numeric, received {value!r}", operation="validate"
        ) from exc
    if not math.isfinite(result):
        raise DriverArgumentValueError(f"<{name}> must be finite, received {value!r}", operation="validate")
    return result


def to_positive_seconds(value: Any, name: str, *, allow_none: bool = False) -> float | None:
    if value is None and allow_none:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = float(value)
    else:
        match = _DURATION_PATTERN.match(str(value))
        if not match:
            raise DriverArgumentValueError(
                f"<{name}> must be a duration in seconds or Robot-style time text, received {value!r}",
                operation="validate",
            )
        seconds = float(match.group("value"))
        unit = (match.group("unit") or "s").lower()
        if unit.startswith("ms") or unit.startswith("millisecond"):
            seconds /= 1000.0
        elif unit.startswith("m") and not unit.startswith("ms"):
            seconds *= 60.0
        elif unit.startswith("h"):
            seconds *= 3600.0
    if not math.isfinite(seconds) or seconds <= 0:
        raise DriverRangeError(f"<{name}> must be finite and > 0 s, received {value!r}", operation="validate")
    return seconds


def to_nonnegative_seconds(value: Any, name: str) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = float(value)
    else:
        match = _DURATION_PATTERN.match(str(value))
        if not match:
            raise DriverArgumentValueError(f"<{name}> is not a valid duration", operation="validate")
        seconds = float(match.group("value"))
        unit = (match.group("unit") or "s").lower()
        if unit.startswith("ms") or unit.startswith("millisecond"):
            seconds /= 1000.0
        elif unit.startswith("m") and not unit.startswith("ms"):
            seconds *= 60.0
        elif unit.startswith("h"):
            seconds *= 3600.0
    if not math.isfinite(seconds) or seconds < 0:
        raise DriverRangeError(f"<{name}> must be finite and >= 0 s", operation="validate")
    return seconds


def to_bool(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "on", "1"}:
            return True
        if normalized in {"false", "no", "off", "0", "none", ""}:
            return False
    raise DriverArgumentValueError(f"<{name}> must be a Boolean value, received {value!r}", operation="validate")


def to_int(value: Any, name: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    if isinstance(value, bool):
        raise DriverArgumentTypeError(f"<{name}> must be an integer, received bool", operation="validate")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise DriverArgumentTypeError(f"<{name}> must be an integer, received {value!r}", operation="validate") from exc
    if minimum is not None and result < minimum:
        raise DriverRangeError(f"<{name}> must be >= {minimum}, received {result}", operation="validate")
    if maximum is not None and result > maximum:
        raise DriverRangeError(f"<{name}> must be <= {maximum}, received {result}", operation="validate")
    return result


def normalize_alias(alias: Any | None, *, default: str = "default") -> str:
    value = default if alias is None else str(alias).strip()
    if not _ALIAS_PATTERN.fullmatch(value):
        raise DriverArgumentValueError(
            f"<alias> must match {_ALIAS_PATTERN.pattern!r}, received {value!r}", operation="validate"
        )
    return value.lower()


def sanitize(value: Any) -> Any:
    """Convert arbitrary internal values into Robot/JSON-compatible primitives."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.decode("latin-1", errors="backslashreplace")
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize(item) for item in value]
    if hasattr(value, "to_dict"):
        return sanitize(value.to_dict())
    return str(value)
