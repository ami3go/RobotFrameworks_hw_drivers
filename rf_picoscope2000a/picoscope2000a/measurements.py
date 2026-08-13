"""Standard waveform measurements, computed host-side from a captured :class:`Waveform`.

``picosdk.ps2000a`` has no on-device "immediate measurement" call — unlike a
bench scope with its own display/firmware (e.g. this repo's ``rf_tbs1000c``,
which wraps Tektronix's ``MEASUrement:IMMed:TYPe``), the ps2000a driver only
ever gives you raw ADC block data. Pico's own PicoScope desktop application
computes measurements like these itself, in application code, not the
driver — so this module is this driver's equivalent of that: every value
here is derived from the same decoded ``(time_s, values)`` arrays
``Get Waveform`` already returns.

``High``/``Low`` use the histogram (modal) method most oscilloscope vendors
use for "top"/"base" — the most common sample value in the upper/lower half
of the value range — rather than bare max/min, so ``Amplitude`` means what
it means on a real scope: the settled high/low levels, excluding overshoot
and ringing. ``Frequency``/``Period``/edge-timing measurements use linear-
interpolated threshold crossings at the mid-reference level
``(High + Low) / 2`` (and the 10%/90% levels for rise/fall time), the
standard approach for a digitized (not continuously sampled) waveform.
"""

from __future__ import annotations

from .exceptions import PicoScope2000AValidationError
from .models import Measurements, Waveform

_HISTOGRAM_BINS = 100


def _high_low(values: list[float]) -> tuple[float, float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return hi, lo
    width = (hi - lo) / _HISTOGRAM_BINS
    counts = [0] * _HISTOGRAM_BINS
    for v in values:
        idx = int((v - lo) / width)
        if idx >= _HISTOGRAM_BINS:
            idx = _HISTOGRAM_BINS - 1
        counts[idx] += 1
    half = _HISTOGRAM_BINS // 2
    upper_idx = max(range(half, _HISTOGRAM_BINS), key=lambda i: counts[i])
    lower_idx = max(range(0, half), key=lambda i: counts[i])
    high = lo + (upper_idx + 0.5) * width
    low = lo + (lower_idx + 0.5) * width
    return high, low


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _rms(values: list[float]) -> float:
    return (sum(v * v for v in values) / len(values)) ** 0.5


def _crossings(time_s: list[float], values: list[float], level: float, *, rising: bool) -> list[float]:
    """Linear-interpolated times where the signal crosses ``level``, in one direction."""

    result = []
    for i in range(1, len(values)):
        v0, v1 = values[i - 1], values[i]
        t0, t1 = time_s[i - 1], time_s[i]
        if rising and v0 < level <= v1:
            result.append(t0 + (level - v0) * (t1 - t0) / (v1 - v0))
        elif not rising and v0 > level >= v1:
            result.append(t0 + (level - v0) * (t1 - t0) / (v1 - v0))
    return result


def _rising_mid_crossings(time_s: list[float], values: list[float], mid: float) -> list[float]:
    return _crossings(time_s, values, mid, rising=True)


def _mid_reference(values: list[float]) -> float:
    high, low = _high_low(values)
    return (high + low) / 2.0


def _threshold_crossing_time(
    time_s: list[float], values: list[float], level: float, *, rising: bool, after: float
) -> float | None:
    for i in range(1, len(values)):
        t1 = time_s[i]
        if t1 <= after:
            continue
        v0, v1 = values[i - 1], values[i]
        if rising and v0 < level <= v1:
            t0 = time_s[i - 1]
            return t0 + (level - v0) * (t1 - t0) / (v1 - v0)
        if not rising and v0 > level >= v1:
            t0 = time_s[i - 1]
            return t0 + (level - v0) * (t1 - t0) / (v1 - v0)
    return None


def _frequency_and_period(rising_crossings: list[float]) -> tuple[float | None, float | None]:
    if len(rising_crossings) < 2:
        return None, None
    periods = [b - a for a, b in zip(rising_crossings, rising_crossings[1:])]
    period = sum(periods) / len(periods)
    if period <= 0:
        return None, None
    return 1.0 / period, period


def _rise_time(time_s: list[float], values: list[float], low: float, high: float) -> float | None:
    amplitude = high - low
    if amplitude <= 0:
        return None
    level10 = low + 0.1 * amplitude
    level90 = low + 0.9 * amplitude
    t10 = _threshold_crossing_time(time_s, values, level10, rising=True, after=float("-inf"))
    if t10 is None:
        return None
    t90 = _threshold_crossing_time(time_s, values, level90, rising=True, after=t10)
    if t90 is None:
        return None
    return t90 - t10


def _fall_time(time_s: list[float], values: list[float], low: float, high: float) -> float | None:
    amplitude = high - low
    if amplitude <= 0:
        return None
    level10 = low + 0.1 * amplitude
    level90 = low + 0.9 * amplitude
    t90 = _threshold_crossing_time(time_s, values, level90, rising=False, after=float("-inf"))
    if t90 is None:
        return None
    t10 = _threshold_crossing_time(time_s, values, level10, rising=False, after=t90)
    if t10 is None:
        return None
    return t10 - t90


def _positive_negative_width(
    time_s: list[float], values: list[float], mid: float, rising_crossings: list[float]
) -> tuple[float | None, float | None]:
    if not rising_crossings:
        return None, None
    t_rise0 = rising_crossings[0]
    t_fall = _threshold_crossing_time(time_s, values, mid, rising=False, after=t_rise0)
    if t_fall is None:
        return None, None
    positive_width = t_fall - t_rise0
    if len(rising_crossings) < 2:
        return positive_width, None
    negative_width = rising_crossings[1] - t_fall
    return positive_width, negative_width


def _cycle_rms(time_s: list[float], values: list[float], rising_crossings: list[float]) -> float | None:
    if len(rising_crossings) < 2:
        return None
    t0, t1 = rising_crossings[0], rising_crossings[1]
    selected = [v for t, v in zip(time_s, values) if t0 <= t < t1]
    return _rms(selected) if selected else None


def _overshoot(maximum: float, minimum: float, high: float, low: float) -> tuple[float, float]:
    amplitude = high - low
    if amplitude <= 0:
        return 0.0, 0.0
    positive = max(0.0, (maximum - high) / amplitude * 100.0)
    negative = max(0.0, (low - minimum) / amplitude * 100.0)
    return positive, negative


def compute_measurements(waveform: Waveform) -> Measurements:
    values = waveform.values
    time_s = waveform.time_s
    if not values:
        raise PicoScope2000AValidationError("waveform has no samples to measure")

    maximum = max(values)
    minimum = min(values)
    high, low = _high_low(values)
    mid = (high + low) / 2.0
    rising_crossings = _rising_mid_crossings(time_s, values, mid)

    frequency_hz, period_s = _frequency_and_period(rising_crossings)
    positive_width_s, negative_width_s = _positive_negative_width(time_s, values, mid, rising_crossings)
    positive_overshoot_pct, negative_overshoot_pct = _overshoot(maximum, minimum, high, low)
    cycle_rms = _cycle_rms(time_s, values, rising_crossings)
    rms = _rms(values)

    return Measurements(
        maximum=maximum,
        minimum=minimum,
        peak_to_peak=maximum - minimum,
        high=high,
        low=low,
        amplitude=high - low,
        mean=_mean(values),
        rms=rms,
        cycle_rms=cycle_rms if cycle_rms is not None else rms,
        frequency_hz=frequency_hz,
        period_s=period_s,
        rise_time_s=_rise_time(time_s, values, low, high),
        fall_time_s=_fall_time(time_s, values, low, high),
        positive_width_s=positive_width_s,
        negative_width_s=negative_width_s,
        positive_duty_cycle_pct=(
            positive_width_s / period_s * 100.0 if positive_width_s is not None and period_s else None
        ),
        positive_overshoot_pct=positive_overshoot_pct,
        negative_overshoot_pct=negative_overshoot_pct,
        unit=waveform.unit,
    )


def compute_delay(reference: Waveform, target: Waveform, *, rising: bool = True) -> float | None:
    """Time from ``reference``'s first qualifying edge to the nearest corresponding edge
    on ``target``. Positive means ``target`` lags ``reference``; negative means it leads.
    ``None`` if either waveform has no such edge.

    Each channel gets its own mid-reference level (``(High + Low) / 2``, same as every
    other timing measurement here) rather than assuming both channels share one
    amplitude/offset — a delay measurement between a 5 V logic signal and a 50 mV analog
    one is exactly the kind of case that would otherwise be silently wrong. Both waveforms
    must come from the same ``capture_block()`` call: every enabled channel in one block
    capture shares one sample clock, so their ``time_s`` arrays are already time-aligned.
    """

    reference_mid = _mid_reference(reference.values)
    target_mid = _mid_reference(target.values)
    reference_crossings = _crossings(reference.time_s, reference.values, reference_mid, rising=rising)
    target_crossings = _crossings(target.time_s, target.values, target_mid, rising=rising)
    if not reference_crossings or not target_crossings:
        return None
    reference_t = reference_crossings[0]
    nearest_t = min(target_crossings, key=lambda t: abs(t - reference_t))
    return nearest_t - reference_t


def compute_phase(reference: Waveform, target: Waveform, *, rising: bool = True) -> float | None:
    """Phase of ``target`` relative to ``reference``, in degrees, using ``reference``'s own
    measured period as the 360-degree reference — the standard assumption for a phase
    measurement is that both signals share one fundamental frequency. ``None`` if the delay
    or ``reference``'s period can't be determined (e.g. too few cycles captured)."""

    delay = compute_delay(reference, target, rising=rising)
    if delay is None:
        return None
    reference_mid = _mid_reference(reference.values)
    reference_crossings = _crossings(reference.time_s, reference.values, reference_mid, rising=rising)
    _frequency, period = _frequency_and_period(reference_crossings)
    if not period:
        return None
    return (delay / period) * 360.0
