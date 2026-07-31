"""Enumerations, status registers and per-model capability limits."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Final

from .exceptions import BK8500ValidationError


class LoadMode(IntEnum):
    """Regulation mode (command 0x28 / 0x29)."""

    CC = 0
    CV = 1
    CW = 2
    CR = 3


class LoadFunction(IntEnum):
    """Operating function (command 0x5D / 0x5E)."""

    FIXED = 0
    SHORT = 1
    TRANSIENT = 2
    LIST = 3
    BATTERY = 4


class TriggerSource(IntEnum):
    """Trigger source (command 0x58 / 0x59)."""

    IMMEDIATE = 0
    EXTERNAL = 1
    BUS = 2


class TransientOperation(IntEnum):
    """Transient operation type (payload byte 15 of 0x32..0x39)."""

    CONTINUOUS = 0
    PULSE = 1
    TOGGLED = 2


class ListRepeat(IntEnum):
    """List repetition (command 0x3C / 0x3D)."""

    ONCE = 0
    REPEAT = 1


def parse_enum(enum_cls, value, name: str):
    """Coerce a Robot Framework string or an integer into ``enum_cls``."""
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        try:
            return enum_cls(value)
        except ValueError as exc:
            raise BK8500ValidationError(f"{name}: {value} is not a valid {enum_cls.__name__}") from exc
    text = str(value).strip().upper()
    try:
        return enum_cls[text]
    except KeyError:
        valid = ", ".join(m.name for m in enum_cls)
        raise BK8500ValidationError(
            f"{name}: '{value}' is not a valid {enum_cls.__name__}. Valid values: {valid}"
        ) from None


# Operation state register: byte 15 of the 0x5F response.
OPERATION_STATE_BITS: Final[tuple[str, ...]] = (
    "recalculating_demarcation_coefficient",
    "waiting_for_trigger",
    "remote_control_enabled",
    "input_on",
    "local_key_enabled",
    "remote_sense_enabled",
    "load_on_timer_enabled",
    "reserved_bit_7",
)

# Demand state register: bytes 16..17 of the 0x5F response.
DEMAND_STATE_BITS: Final[tuple[str, ...]] = (
    "reverse_voltage",
    "over_voltage",
    "over_current",
    "over_power",
    "over_temperature",
    "remote_sense_terminal_not_connected",
    "constant_current",
    "constant_voltage",
    "constant_power",
    "constant_resistance",
)

# Demand-state bits that represent a protection event rather than a regulation
# state. Any of these set means the load is not measuring a healthy DUT.
PROTECTION_BITS: Final[tuple[str, ...]] = (
    "reverse_voltage",
    "over_voltage",
    "over_current",
    "over_power",
    "over_temperature",
)


def decode_bitfield(value: int, names: tuple[str, ...]) -> dict[str, bool]:
    """Expand an integer register into a ``{flag_name: bool}`` mapping."""
    return {name: bool(value >> index & 1) for index, name in enumerate(names)}


@dataclass(frozen=True)
class ModelLimits:
    """Rated input envelope of one 8500 series model.

    Values are taken from the "Specifications" chapter of the user manual and
    are used for pre-flight validation, never as a substitute for the
    instrument's own protection.
    """

    model: str
    max_voltage_v: float
    max_current_a: float
    max_power_w: float
    min_resistance_ohm: float = 0.1
    max_resistance_ohm: float = 4000.0


MODEL_LIMITS: Final[dict[str, ModelLimits]] = {
    "8500": ModelLimits("8500", 120.0, 30.0, 300.0),
    "8502": ModelLimits("8502", 500.0, 15.0, 300.0),
    "8510": ModelLimits("8510", 120.0, 120.0, 600.0),
    "8512": ModelLimits("8512", 500.0, 30.0, 600.0),
    "8514": ModelLimits("8514", 120.0, 240.0, 1200.0),
    "8518": ModelLimits("8518", 60.0, 240.0, 1200.0),
    "8520": ModelLimits("8520", 120.0, 240.0, 2400.0),
    "8522": ModelLimits("8522", 500.0, 120.0, 2400.0),
    "8524": ModelLimits("8524", 60.0, 240.0, 5000.0),
    "8526": ModelLimits("8526", 500.0, 120.0, 5000.0),
}

#: Conservative envelope used when the model is unknown. Matches the smallest
#: rated model in the series so that validation can never permit more than the
#: real instrument allows.
UNKNOWN_MODEL_LIMITS: Final[ModelLimits] = ModelLimits("UNKNOWN", 60.0, 15.0, 300.0)


def limits_for(model: str | None) -> ModelLimits:
    """Return the capability envelope for ``model``, falling back to UNKNOWN."""
    if not model:
        return UNKNOWN_MODEL_LIMITS
    return MODEL_LIMITS.get(str(model).strip().upper().replace("BK", ""), UNKNOWN_MODEL_LIMITS)


@dataclass(frozen=True)
class InputValues:
    """One reading of the load's input terminals (command 0x5F)."""

    voltage_v: float
    current_a: float
    power_w: float
    operation_state: dict[str, bool] = field(default_factory=dict)
    demand_state: dict[str, bool] = field(default_factory=dict)
    operation_state_raw: int = 0
    demand_state_raw: int = 0

    @property
    def active_protections(self) -> tuple[str, ...]:
        """Names of the protection flags that are currently asserted."""
        return tuple(name for name in PROTECTION_BITS if self.demand_state.get(name))

    @property
    def input_on(self) -> bool:
        return bool(self.operation_state.get("input_on"))

    def as_dict(self) -> dict:
        return {
            "voltage_v": self.voltage_v,
            "current_a": self.current_a,
            "power_w": self.power_w,
            "input_on": self.input_on,
            "active_protections": list(self.active_protections),
            "operation_state": dict(self.operation_state),
            "demand_state": dict(self.demand_state),
        }


@dataclass(frozen=True)
class ProductInfo:
    """Identity of the connected instrument (command 0x6A)."""

    model: str
    serial_number: str
    firmware_version: str
    #: Raw (high, low) firmware bytes. The manual does not say whether the
    #: encoding is hexadecimal or BCD, so the decoded string is a best effort
    #: and these bytes are kept for confirmation against the front panel.
    firmware_raw: tuple[int, int] = (0, 0)

    def as_dict(self) -> dict:
        return {
            "model": self.model,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "firmware_raw": list(self.firmware_raw),
        }


@dataclass(frozen=True)
class TransientSettings:
    """Transient (A/B toggling) parameters for one mode."""

    mode: LoadMode
    level_a: float
    dwell_a_s: float
    level_b: float
    dwell_b_s: float
    operation: TransientOperation

    def as_dict(self) -> dict:
        return {
            "mode": self.mode.name,
            "level_a": self.level_a,
            "dwell_a_s": self.dwell_a_s,
            "level_b": self.level_b,
            "dwell_b_s": self.dwell_b_s,
            "operation": self.operation.name,
        }


@dataclass(frozen=True)
class ListStep:
    """One step of a list sequence."""

    index: int
    level: float
    dwell_s: float

    def as_dict(self) -> dict:
        return {"index": self.index, "level": self.level, "dwell_s": self.dwell_s}
