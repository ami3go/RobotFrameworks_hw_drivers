"""Measurement semantics for Keysight/Agilent 34970A/34972A.

This module contains no Robot Framework imports.  It validates documented
module/channel combinations, serializes single-channel MEASure? queries, and
parses scalar instrument readings.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from ..exceptions import DriverDeviceError, DriverNotSupportedError, DriverResponseError, DriverValidationError
from ..models import ModuleInfo
from ..protocol.scpi import ScpiProtocol
from ..transports.base import ReplayPolicy


@dataclass(frozen=True)
class MeasurementSpec:
    key: str
    command: str
    unit: str
    quantity: str
    supported_modules: tuple[str, ...]
    numeric_range_min: float | None = None
    numeric_range_max: float | None = None


MEASUREMENT_SPECS: dict[str, MeasurementSpec] = {
    "dc_voltage": MeasurementSpec(
        "dc_voltage", "MEAS:VOLT:DC?", "V", "dc_voltage", ("34901A", "34902A", "34908A"), None, 300.0
    ),
    "ac_voltage": MeasurementSpec(
        "ac_voltage", "MEAS:VOLT:AC?", "V", "ac_voltage", ("34901A", "34902A", "34908A"), None, 300.0
    ),
    "dc_current": MeasurementSpec(
        "dc_current", "MEAS:CURR:DC?", "A", "dc_current", ("34901A",), None, 1.0
    ),
    "ac_current": MeasurementSpec(
        "ac_current", "MEAS:CURR:AC?", "A", "ac_current", ("34901A",), None, 1.0
    ),
    "resistance": MeasurementSpec(
        "resistance", "MEAS:RES?", "ohm", "resistance", ("34901A", "34902A", "34908A"), None, 100_000_000.0
    ),
    "four_wire_resistance": MeasurementSpec(
        "four_wire_resistance", "MEAS:FRES?", "ohm", "resistance", ("34901A", "34902A"), None, 100_000_000.0
    ),
    "frequency": MeasurementSpec(
        "frequency", "MEAS:FREQ?", "Hz", "frequency", ("34901A", "34902A", "34908A"), 3.0, 300_000.0
    ),
    "period": MeasurementSpec(
        "period", "MEAS:PER?", "s", "period", ("34901A", "34902A", "34908A"), 1.0 / 300_000.0, 1.0 / 3.0
    ),
}

_RANGE_TOKENS = {"AUTO", "MIN", "MAX", "DEF"}
_RESOLUTION_TOKENS = {"AUTO", "MIN", "MAX", "DEF"}


def canonical_channel(value: object) -> str:
    """Normalize a well-formed three-digit channel identifier to ``str``."""
    text = str(value).strip()
    if not text.isdigit():
        raise DriverValidationError("channel must be a three-digit numeric identifier such as 101")
    number = int(text)
    slot_digit = number // 100
    index = number % 100
    if slot_digit not in (1, 2, 3) or index < 1 or index > 99:
        raise DriverValidationError("channel must identify slot 100, 200, or 300 and channel 01..99")
    return f"{number:03d}"


def _module_channels(slot: int, model: str) -> list[str]:
    """Return channels usable by the currently implemented measurement group."""
    base = slot
    if model == "34901A":
        indices = range(1, 23)  # 01..20 general measurement; 21..22 current only
    elif model == "34902A":
        indices = range(1, 17)
    elif model == "34908A":
        indices = range(1, 41)
    else:
        indices = ()
    return [str(base + index) for index in indices]


def list_measurement_channels(modules: Mapping[int, ModuleInfo]) -> list[str]:
    channels: list[str] = []
    for slot in (100, 200, 300):
        module = modules.get(slot)
        if module and module.installed:
            channels.extend(_module_channels(slot, module.model))
    return channels


def channel_exists(modules: Mapping[int, ModuleInfo], channel: object) -> bool:
    canonical = canonical_channel(channel)
    return canonical in set(list_measurement_channels(modules))


def _channel_index(channel: str) -> int:
    return int(channel) % 100


def validate_measurement_channel(
    modules: Mapping[int, ModuleInfo], channel: object, measurement_key: str
) -> tuple[str, ModuleInfo]:
    canonical = canonical_channel(channel)
    spec = MEASUREMENT_SPECS[measurement_key]
    slot = (int(canonical) // 100) * 100
    module = modules.get(slot)
    if module is None or not module.installed:
        raise DriverValidationError(f"channel {canonical} refers to empty or undiscovered slot {slot}")
    if module.model not in spec.supported_modules:
        raise DriverNotSupportedError(
            f"{spec.quantity} measurement is not supported on module {module.model} in slot {slot}"
        )
    index = _channel_index(canonical)
    if module.model == "34901A":
        if measurement_key in {"dc_current", "ac_current"}:
            valid = index in (21, 22)
        elif measurement_key == "four_wire_resistance":
            valid = 1 <= index <= 10
        else:
            valid = 1 <= index <= 20
    elif module.model == "34902A":
        if measurement_key == "four_wire_resistance":
            valid = 1 <= index <= 8
        else:
            valid = 1 <= index <= 16
    elif module.model == "34908A":
        valid = measurement_key != "four_wire_resistance" and 1 <= index <= 40
    else:
        valid = False
    if not valid:
        raise DriverValidationError(
            f"channel {canonical} is not valid for {measurement_key.replace('_', ' ')} on {module.model}"
        )
    return canonical, module


def _format_numeric(value: float) -> str:
    return format(value, ".12g")


def normalize_range(value: object | None, spec: MeasurementSpec) -> str | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    if isinstance(value, str):
        token = value.strip().upper()
        if token in _RANGE_TOKENS:
            return token
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DriverValidationError(
            f"range_value must be one of {sorted(_RANGE_TOKENS)} or a finite numeric value"
        ) from exc
    if not math.isfinite(numeric) or numeric <= 0:
        raise DriverValidationError("range_value must be finite and greater than zero")
    if spec.numeric_range_min is not None and numeric < spec.numeric_range_min:
        raise DriverValidationError(
            f"range_value {numeric:g} is below documented minimum {spec.numeric_range_min:g} {spec.unit}"
        )
    if spec.numeric_range_max is not None and numeric > spec.numeric_range_max:
        raise DriverValidationError(
            f"range_value {numeric:g} exceeds documented maximum {spec.numeric_range_max:g} {spec.unit}"
        )
    return _format_numeric(numeric)


def normalize_resolution(value: object | None) -> str | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    if isinstance(value, str):
        token = value.strip().upper()
        if token in _RESOLUTION_TOKENS:
            return token
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DriverValidationError(
            f"resolution must be one of {sorted(_RESOLUTION_TOKENS)} or a finite numeric value"
        ) from exc
    if not math.isfinite(numeric) or numeric <= 0:
        raise DriverValidationError("resolution must be finite and greater than zero")
    return _format_numeric(numeric)


def build_measurement_query(
    measurement_key: str,
    channel: str,
    *,
    range_value: object | None = None,
    resolution: object | None = None,
) -> str:
    spec = MEASUREMENT_SPECS[measurement_key]
    normalized_range = normalize_range(range_value, spec)
    normalized_resolution = normalize_resolution(resolution)
    if normalized_resolution is not None and normalized_range is None:
        raise DriverValidationError("resolution requires an explicit range_value")
    if normalized_resolution is not None and normalized_range in {"AUTO", "DEF"}:
        # The command reference explicitly rejects discrete resolution with autorange.
        if normalized_resolution not in {"AUTO", "DEF"}:
            raise DriverValidationError(
                "a discrete resolution cannot be combined with AUTO/DEF range; omit resolution or use a manual range"
            )
    args = ""
    if normalized_range is not None:
        args = f" {normalized_range}"
        if normalized_resolution is not None:
            args += f",{normalized_resolution}"
        args += ","
    else:
        args = " "
    return f"{spec.command}{args}(@{channel})"


def parse_scalar_measurement(raw: str, *, measurement_key: str, channel: str) -> float:
    text = raw.strip()
    if "," in text:
        raise DriverResponseError(
            f"single-channel {measurement_key} query returned multiple values: {raw!r}"
        )
    try:
        value = float(text)
    except (TypeError, ValueError) as exc:
        raise DriverResponseError(f"measurement response is not numeric: {raw!r}") from exc
    if not math.isfinite(value):
        raise DriverResponseError(f"measurement response is not finite: {raw!r}")
    if abs(value) >= 9.0e37:
        raise DriverDeviceError(
            f"instrument reported overload for {measurement_key.replace('_', ' ')} on channel {channel}",
            details={"raw_response": text, "channel": channel, "measurement": measurement_key},
        )
    return value


class MeasurementEngine:
    """Execute validated single-channel measurement queries."""

    def __init__(self, transport) -> None:
        self.scpi = ScpiProtocol(transport)

    def measure(
        self,
        measurement_key: str,
        modules: Mapping[int, ModuleInfo],
        channel: object,
        *,
        range_value: object | None,
        resolution: object | None,
        timeout_s: float,
    ) -> float:
        canonical, _module = validate_measurement_channel(modules, channel, measurement_key)
        query = build_measurement_query(
            measurement_key, canonical, range_value=range_value, resolution=resolution
        )
        raw = self.scpi.query(
            query,
            timeout_s=timeout_s,
            operation_id=f"measure.{measurement_key}.{canonical}",
            replay_policy=ReplayPolicy.NEVER,
        )
        return parse_scalar_measurement(raw, measurement_key=measurement_key, channel=canonical)
