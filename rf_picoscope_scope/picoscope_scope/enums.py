"""Enums for PicoScope SDK argument values, shared across every supported series.

Numeric values are grounded in the ps2000a/ps3000a Programmer's Guides' C
enums (``PS2000A_COUPLING``/``PS3000A_COUPLING``, ``..._RANGE``,
``..._THRESHOLD_DIRECTION``, ``..._WAVE_TYPE``) so :mod:`backend` can pass
them to any series' ``picosdk`` calls unchanged — Pico kept these numerically
identical across its "X000A"-generation API family (confirmed against the
real ``picosdk`` source for both series), which is exactly why this module
has no per-series variants. :class:`ProbeType` and :class:`Channel` are
driver-level conveniences with no direct SDK equivalent.
"""

from __future__ import annotations

from enum import Enum, IntEnum

from .exceptions import PicoScopeValidationError


class Channel(str, Enum):
    """The four analog input channels every supported series exposes
    (``PS2000A_CHANNEL_A``/``PS3000A_CHANNEL_A``..``_D``)."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"


class Coupling(IntEnum):
    """``..._COUPLING``: ``SetChannel``'s ``coupling`` argument."""

    AC = 0
    DC = 1


class Range(IntEnum):
    """``..._RANGE``: full-scale voltage range codes for ``SetChannel``.

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
            raise PicoScopeValidationError(
                f"full_scale_v must be positive, got {full_scale_v!r}"
            )
        for member in sorted(cls, key=lambda m: _RANGE_VOLTS[m]):
            if _RANGE_VOLTS[member] >= full_scale_v:
                return member
        largest = max(cls, key=lambda m: _RANGE_VOLTS[m])
        raise PicoScopeValidationError(
            f"no supported range covers {full_scale_v:g} V (largest is {_RANGE_VOLTS[largest]:g} V)"
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
    """``..._THRESHOLD_DIRECTION`` subset used by a simple edge trigger."""

    RISING = 2
    FALLING = 3


class ProbeType(str, Enum):
    """Driver-level probe abstraction: ``picosdk`` itself has no probe concept.

    A :class:`~picoscope_scope.models.ChannelSettings` combines this with a
    ``scale`` (native units per volt at the ADC input) so a current-clamp
    probe's channel reports amps instead of volts from ``Get Waveform``.
    """

    VOLTAGE = "VOLTAGE"
    CURRENT = "CURRENT"


class WaveType(IntEnum):
    """``..._WAVE_TYPE`` subset ``SetSigGenBuiltIn`` accepts.

    Numeric values are Pico's standard convention across the "X000A" API
    family (documented, but not independently verifiable from the
    ``picosdk`` Python source — neither ``ps2000a.py`` nor ``ps3000a.py``
    defines ``WAVE_TYPE`` as a named enum; it's a bare ``int16`` in both,
    with values coming from Pico's C header)."""

    SINE = 0
    SQUARE = 1
    TRIANGLE = 2
    DC_VOLTAGE = 8


class MeasurementType(str, Enum):
    """Standard waveform measurements, computed host-side from a captured waveform.

    No supported series' SDK has an on-device "immediate measurement" call
    (unlike a scope with its own display/firmware, e.g. this repo's
    ``rf_tbs1000c`` — see :mod:`picoscope_scope.measurements` for the
    algorithms and why). Names reuse ``rf_tbs1000c``'s ``MeasurementType``
    mixed-case abbreviations (a subset of them) for vocabulary consistency
    across this repo.
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
