"""Scan, trigger, acquisition, reading-memory and statistics semantics."""
from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Mapping, Sequence

from ..exceptions import DriverNotSupportedError, DriverProtocolError, DriverValidationError
from ..models import ModuleInfo
from ..protocol.scpi import ScpiProtocol
from ..transports.base import ReplayPolicy
from .measurement import canonical_channel, channel_exists

TRIGGER_SOURCES = {
    "BUS": "BUS",
    "IMM": "IMM",
    "IMMEDIATE": "IMM",
    "EXT": "EXT",
    "EXTERNAL": "EXT",
    "ALAR1": "ALAR1",
    "ALARM1": "ALAR1",
    "ALAR2": "ALAR2",
    "ALARM2": "ALAR2",
    "ALAR3": "ALAR3",
    "ALARM3": "ALAR3",
    "ALAR4": "ALAR4",
    "ALARM4": "ALAR4",
    "TIM": "TIM",
    "TIMER": "TIM",
}


def normalize_channels(channels: object, modules: Mapping[int, ModuleInfo]) -> list[str]:
    if isinstance(channels, str):
        text = channels.strip()
        if text.startswith("(@") and text.endswith(")"):
            text = text[2:-1]
        raw = [item.strip() for item in text.replace(";", ",").split(",") if item.strip()]
    elif isinstance(channels, Sequence):
        raw = [str(item).strip() for item in channels]
    else:
        raw = [str(channels).strip()]
    if not raw:
        raise DriverValidationError("at least one scan channel is required")
    result: list[str] = []
    for item in raw:
        canonical = canonical_channel(item)
        if not channel_exists(modules, canonical):
            raise DriverValidationError(f"channel {canonical} is unavailable for the implemented scan capability")
        if canonical not in result:
            result.append(canonical)
    return sorted(result, key=int)


def parse_definite_block(text: str) -> str:
    value = text.strip()
    if not value.startswith("#") or len(value) < 3:
        raise DriverProtocolError(f"expected SCPI definite-length block, got {text!r}")
    try:
        digits = int(value[1])
    except ValueError as exc:
        raise DriverProtocolError(f"invalid definite-length block header: {text!r}") from exc
    if digits <= 0 or len(value) < 2 + digits:
        raise DriverProtocolError(f"invalid definite-length block header: {text!r}")
    count_text = value[2 : 2 + digits]
    if not count_text.isdigit():
        raise DriverProtocolError(f"invalid definite-length block count: {text!r}")
    count = int(count_text)
    payload = value[2 + digits : 2 + digits + count]
    if len(payload) != count:
        raise DriverProtocolError(f"truncated definite-length block: {text!r}")
    return payload


def parse_scan_list(text: str) -> list[str]:
    payload = parse_definite_block(text).strip()
    if payload == "(@)":
        return []
    if not payload.startswith("(@") or not payload.endswith(")"):
        raise DriverProtocolError(f"invalid scan-list block payload: {payload!r}")
    items = [item.strip() for item in payload[2:-1].split(",") if item.strip()]
    return [canonical_channel(item) for item in items]


def parse_numeric_list(text: str) -> list[float]:
    payload = text.strip()
    if payload.startswith("#"):
        payload = parse_definite_block(payload)
    if not payload:
        return []
    result: list[float] = []
    for item in payload.split(","):
        try:
            value = float(item.strip())
        except ValueError as exc:
            raise DriverProtocolError(f"reading list contains non-numeric value: {item!r}") from exc
        if not math.isfinite(value):
            raise DriverProtocolError(f"reading list contains non-finite value: {item!r}")
        result.append(value)
    return result


def normalize_trigger_source(value: object) -> str:
    token = str(value).strip().upper()
    try:
        return TRIGGER_SOURCES[token]
    except KeyError as exc:
        raise DriverValidationError("trigger source must be BUS, IMM, EXT, ALAR1..ALAR4, or TIM") from exc


def normalize_trigger_count(value: object) -> str:
    token = str(value).strip().upper()
    if token in {"INF", "INFINITY", "INFINITE"}:
        return "INF"
    try:
        count = int(token)
    except ValueError as exc:
        raise DriverValidationError("trigger count must be integer 1..50000 or INF") from exc
    if count < 1 or count > 50000:
        raise DriverValidationError("trigger count must be integer 1..50000 or INF")
    return str(count)


def parse_trigger_count(text: str) -> int | str:
    try:
        value = float(text.strip())
    except ValueError as exc:
        raise DriverProtocolError(f"invalid trigger-count response: {text!r}") from exc
    if value >= 9.0e37:
        return "INF"
    rounded = int(round(value))
    if rounded < 1 or rounded > 50000:
        raise DriverProtocolError(f"trigger-count response out of range: {text!r}")
    return rounded


def normalize_trigger_timer(value: object) -> float:
    try:
        seconds = float(value)
    except (TypeError, ValueError) as exc:
        raise DriverValidationError("trigger timer must be a finite value from 0 to 359999 seconds") from exc
    if not math.isfinite(seconds) or seconds < 0 or seconds > 359999:
        raise DriverValidationError("trigger timer must be a finite value from 0 to 359999 seconds")
    return seconds


class AcquisitionEngine:
    def __init__(self, transport) -> None:
        self.scpi = ScpiProtocol(transport)

    def configure_scan_list(self, channels: object, modules: Mapping[int, ModuleInfo], *, timeout_s: float) -> list[str]:
        normalized = normalize_channels(channels, modules)
        command = f"ROUT:SCAN (@{','.join(normalized)})"
        self.scpi.write(command, timeout_s=timeout_s, operation_id="scan.list.configure")
        return normalized

    def get_scan_list(self, *, timeout_s: float) -> list[str]:
        raw = self.scpi.query("ROUT:SCAN?", timeout_s=timeout_s, operation_id="scan.list.query")
        return parse_scan_list(raw)

    def clear_scan_list(self, *, timeout_s: float) -> None:
        self.scpi.write("ROUT:SCAN (@)", timeout_s=timeout_s, operation_id="scan.list.clear")

    def set_trigger_source(self, source: object, *, timeout_s: float) -> str:
        normalized = normalize_trigger_source(source)
        self.scpi.write(f"TRIG:SOUR {normalized}", timeout_s=timeout_s, operation_id="trigger.source.set")
        return normalized

    def get_trigger_source(self, *, timeout_s: float) -> str:
        raw = self.scpi.query("TRIG:SOUR?", timeout_s=timeout_s, operation_id="trigger.source.get")
        return normalize_trigger_source(raw)

    def set_trigger_count(self, count: object, *, timeout_s: float) -> int | str:
        normalized = normalize_trigger_count(count)
        self.scpi.write(f"TRIG:COUN {normalized}", timeout_s=timeout_s, operation_id="trigger.count.set")
        return "INF" if normalized == "INF" else int(normalized)

    def get_trigger_count(self, *, timeout_s: float) -> int | str:
        raw = self.scpi.query("TRIG:COUN?", timeout_s=timeout_s, operation_id="trigger.count.get")
        return parse_trigger_count(raw)

    def set_trigger_timer(self, seconds: object, *, timeout_s: float) -> float:
        normalized = normalize_trigger_timer(seconds)
        self.scpi.write(f"TRIG:TIM {normalized:.12g}", timeout_s=timeout_s, operation_id="trigger.timer.set")
        return normalized

    def get_trigger_timer(self, *, timeout_s: float) -> float:
        raw = self.scpi.query("TRIG:TIM?", timeout_s=timeout_s, operation_id="trigger.timer.get")
        try:
            value = float(raw)
        except ValueError as exc:
            raise DriverProtocolError(f"invalid trigger-timer response: {raw!r}") from exc
        if not math.isfinite(value) or value < 0 or value > 359999:
            raise DriverProtocolError(f"trigger-timer response out of range: {raw!r}")
        return value

    def initiate(self, *, timeout_s: float) -> None:
        self.scpi.write("INIT", timeout_s=timeout_s, operation_id="scan.initiate")

    def abort(self, *, timeout_s: float) -> None:
        self.scpi.write("ABOR", timeout_s=timeout_s, operation_id="scan.abort")

    def read_scan(self, *, timeout_s: float) -> list[float]:
        raw = self.scpi.query("READ?", timeout_s=timeout_s, operation_id="scan.read", replay_policy=ReplayPolicy.NEVER)
        return parse_numeric_list(raw)

    def fetch(self, *, timeout_s: float) -> list[float]:
        raw = self.scpi.query("FETC?", timeout_s=timeout_s, operation_id="scan.fetch")
        return parse_numeric_list(raw)

    def buffered(self, max_count: object | None, *, timeout_s: float) -> list[float]:
        command = "R?" if max_count is None else f"R? {self._positive_count(max_count, max_value=50000)}"
        raw = self.scpi.query(command, timeout_s=timeout_s, operation_id="memory.read_remove", replay_policy=ReplayPolicy.NEVER)
        return parse_numeric_list(raw)

    def remove(self, count: object, *, timeout_s: float) -> list[float]:
        value = self._positive_count(count, max_value=50000)
        raw = self.scpi.query(f"DATA:REM? {value}", timeout_s=timeout_s, operation_id="memory.remove", replay_policy=ReplayPolicy.NEVER)
        return parse_numeric_list(raw)

    def reading_count(self, *, timeout_s: float) -> int:
        raw = self.scpi.query("DATA:POIN?", timeout_s=timeout_s, operation_id="memory.count")
        try:
            count = int(float(raw))
        except ValueError as exc:
            raise DriverProtocolError(f"invalid reading-count response: {raw!r}") from exc
        if count < 0 or count > 50000:
            raise DriverProtocolError(f"reading-count response out of range: {raw!r}")
        return count

    @staticmethod
    def _positive_count(value: object, *, max_value: int) -> int:
        try:
            result = int(str(value).strip())
        except ValueError as exc:
            raise DriverValidationError(f"count must be an integer from 1 to {max_value}") from exc
        if result < 1 or result > max_value:
            raise DriverValidationError(f"count must be an integer from 1 to {max_value}")
        return result
