"""Enums for the PicoScope 2000A (``picosdk.ps2000a``) argument values.

Numeric values are grounded in the ps2000a Programmer's Guide's C enums
(``PS2000A_COUPLING``, ``PS2000A_RANGE``, ``PS2000A_THRESHOLD_DIRECTION``,
``PS2000A_WAVE_TYPE``) so :mod:`backend` can pass them to ``picosdk.ps2000a``
calls unchanged. :class:`ProbeType` and :class:`Channel` are driver-level
conveniences with no direct SDK equivalent.
"""

from __future__ import annotations

from enum import Enum, IntEnum

from .exceptions import PicoScope2000AValidationError


class Channel(str, Enum):
    """The four analog input channels ps2000a exposes (``PS2000A_CHANNEL_A``..``_D``)."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"


class Coupling(IntEnum):
    """``PS2000A_COUPLING``: ``ps2000aSetChannel``'s ``coupling`` argument."""

    AC = 0
    DC = 1


class Range(IntEnum):
    """``PS2000A_RANGE``: full-scale voltage range codes for ``ps2000aSetChannel``.

    The enum member's *name* carries the human-readable full-scale voltage;
    :meth:`volts` returns it as a float and :meth:`nearest` picks the
    smallest range that still contains a requested full-scale voltage.
    """

    R_10MV = 0
    R_20MV = 1
    R_50MV = 2
    R_100MV = 3
    R_200MV = 4
    R_500MV = 5
    R_1V = 6
    R_2V = 7
    R_5V = 8
    R_10V = 9
    R_20V = 10
    R_50V = 11

    def volts(self) -> float:
        return _RANGE_VOLTS[self]

    @classmethod
    def nearest(cls, full_scale_v: float) -> Range:
        full_scale_v = float(full_scale_v)
        if full_scale_v <= 0:
            raise PicoScope2000AValidationError(
                f"full_scale_v must be positive, got {full_scale_v!r}"
            )
        for member in sorted(cls, key=lambda m: _RANGE_VOLTS[m]):
            if _RANGE_VOLTS[member] >= full_scale_v:
                return member
        largest = max(cls, key=lambda m: _RANGE_VOLTS[m])
        raise PicoScope2000AValidationError(
            f"no ps2000a range covers {full_scale_v:g} V (largest is {_RANGE_VOLTS[largest]:g} V)"
        )


_RANGE_VOLTS: dict[Range, float] = {
    Range.R_10MV: 0.010,
    Range.R_20MV: 0.020,
    Range.R_50MV: 0.050,
    Range.R_100MV: 0.100,
    Range.R_200MV: 0.200,
    Range.R_500MV: 0.500,
    Range.R_1V: 1.0,
    Range.R_2V: 2.0,
    Range.R_5V: 5.0,
    Range.R_10V: 10.0,
    Range.R_20V: 20.0,
    Range.R_50V: 50.0,
}


class TriggerDirection(IntEnum):
    """``PS2000A_THRESHOLD_DIRECTION`` subset used by a simple edge trigger."""

    RISING = 2
    FALLING = 3


class ProbeType(str, Enum):
    """Driver-level probe abstraction: ``picosdk`` itself has no probe concept.

    A :class:`~picoscope2000a.models.ChannelSettings` combines this with a
    ``scale`` (native units per volt at the ADC input) so a current-clamp
    probe's channel reports amps instead of volts from ``Get Waveform``.
    """

    VOLTAGE = "VOLTAGE"
    CURRENT = "CURRENT"


class WaveType(IntEnum):
    """``PS2000A_WAVE_TYPE`` subset ``ps2000aSetSigGenBuiltIn`` accepts."""

    SINE = 0
    SQUARE = 1
    TRIANGLE = 2
    DC_VOLTAGE = 8


class MeasurementType(str, Enum):
    """Standard waveform measurements, computed host-side from a captured waveform.

    ``picosdk.ps2000a`` has no on-device "immediate measurement" call (unlike
    a scope with its own display/firmware, e.g. this repo's ``rf_tbs1000c`` —
    see :mod:`picoscope2000a.measurements` for the algorithms and why). Names
    reuse ``rf_tbs1000c``'s ``MeasurementType`` mixed-case abbreviations
    (a subset of them) for vocabulary consistency across this repo.
    """

    AMPLITUDE = "AMPlitude"
    PEAK_TO_PEAK = "PK2Pk"
    MAXIMUM = "MAXimum"
    MINIMUM = "MINImum"
    HIGH = "HIGH"
    LOW = "LOW"
    MEAN = "MEAN"
    RMS = "RMS"
    CYCLE_RMS = "CRMs"
    FREQUENCY = "FREQuency"
    PERIOD = "PERIod"
    RISE_TIME = "RISe"
    FALL_TIME = "FALL"
    POSITIVE_WIDTH = "PWIdth"
    NEGATIVE_WIDTH = "NWIdth"
    POSITIVE_DUTY = "PDUty"
    POSITIVE_OVERSHOOT = "POVershoot"
    NEGATIVE_OVERSHOOT = "NOVershoot"
