"""Typed result models returned by the PicoScope core driver, shared across every series."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentIdentity:
    """Parsed ``GetUnitInfo`` fields for a connected unit."""

    manufacturer: str
    model: str
    serial: str
    firmware: str
    driver_version: str
    raw: str


@dataclass(frozen=True)
class ChannelSettings:
    """Current per-channel configuration, as cached by the driver.

    No supported series' SDK has a "get channel" query — ``SetChannel`` is
    write-only — so this reflects the last values this driver instance sent,
    seeded with the device's documented power-on defaults at connect time.
    ``probe_type``/``probe_scale`` are a driver-side abstraction with no SDK
    equivalent: ``probe_scale`` is native units per volt at the ADC input, so
    a current-clamp probe (e.g. 100 mV/A) has ``probe_scale=10`` and
    ``probe_type="CURRENT"``, and :meth:`~picoscope_scope.driver.PicoScope.get_waveform`
    reports amps instead of volts for that channel.
    """

    channel: str
    enabled: bool
    range_v: float
    coupling: str
    offset_v: float
    probe_type: str
    probe_scale: float

    def as_dict(self) -> dict[str, object]:
        return {
            "channel": self.channel,
            "enabled": self.enabled,
            "range_v": self.range_v,
            "coupling": self.coupling,
            "offset_v": self.offset_v,
            "probe_type": self.probe_type,
            "probe_scale": self.probe_scale,
        }


@dataclass(frozen=True)
class Measurements:
    """Standard measurements computed from one captured channel's waveform.

    ``frequency_hz``/``period_s``/``rise_time_s``/``fall_time_s``/
    ``positive_width_s``/``negative_width_s``/``positive_duty_cycle_pct`` are
    ``None`` when they can't be determined from this particular capture
    (e.g. fewer than two edge crossings — not enough of the signal was
    captured to measure it). See :mod:`picoscope_scope.measurements` for the
    algorithms. ``unit`` matches the source channel's ``Waveform.unit``
    ("V" or "A") for every voltage-shaped field; the two ``_pct`` fields and
    ``positive_duty_cycle_pct`` are always percentages regardless of unit.
    """

    maximum: float
    minimum: float
    peak_to_peak: float
    high: float
    low: float
    amplitude: float
    mean: float
    rms: float
    cycle_rms: float
    frequency_hz: float | None
    period_s: float | None
    rise_time_s: float | None
    fall_time_s: float | None
    positive_width_s: float | None
    negative_width_s: float | None
    positive_duty_cycle_pct: float | None
    positive_overshoot_pct: float
    negative_overshoot_pct: float
    unit: str

    def as_dict(self) -> dict[str, object]:
        return {
            "maximum": self.maximum,
            "minimum": self.minimum,
            "peak_to_peak": self.peak_to_peak,
            "high": self.high,
            "low": self.low,
            "amplitude": self.amplitude,
            "mean": self.mean,
            "rms": self.rms,
            "cycle_rms": self.cycle_rms,
            "frequency_hz": self.frequency_hz,
            "period_s": self.period_s,
            "rise_time_s": self.rise_time_s,
            "fall_time_s": self.fall_time_s,
            "positive_width_s": self.positive_width_s,
            "negative_width_s": self.negative_width_s,
            "positive_duty_cycle_pct": self.positive_duty_cycle_pct,
            "positive_overshoot_pct": self.positive_overshoot_pct,
            "negative_overshoot_pct": self.negative_overshoot_pct,
            "unit": self.unit,
        }


@dataclass(frozen=True)
class Waveform:
    """A decoded block-capture record for one channel.

    ``time_s`` is trigger-relative (0 at the trigger point, negative before
    it). ``values`` is in ``unit`` — volts for a voltage-probe channel, amps
    for a current-probe one (:class:`ChannelSettings.probe_scale`/
    ``probe_type``). ADC-to-volts conversion does not compensate for
    ``offset_v`` (matching ``picosdk.functions.adc2mV``'s own behavior, which
    is offset-agnostic too) — ``offset_v`` only widens the usable input range,
    it is not subtracted back out here.
    """

    channel: str
    time_s: list[float]
    values: list[float]
    unit: str
    sample_interval_s: float

    def as_dict(self) -> dict[str, object]:
        return {
            "channel": self.channel,
            "time_s": self.time_s,
            "values": self.values,
            "unit": self.unit,
            "sample_interval_s": self.sample_interval_s,
        }


@dataclass(frozen=True)
class TimebaseSettings:
    """Current block-capture timebase, as resolved by ``GetTimebase2``."""

    timebase_index: int
    sample_interval_s: float
    num_samples: int
    pre_trigger_ratio: float

    def as_dict(self) -> dict[str, object]:
        return {
            "timebase_index": self.timebase_index,
            "sample_interval_s": self.sample_interval_s,
            "num_samples": self.num_samples,
            "pre_trigger_ratio": self.pre_trigger_ratio,
        }


@dataclass(frozen=True)
class TriggerSettings:
    """Current simple (edge) trigger configuration, as cached by the driver.

    Like :class:`ChannelSettings`, this is write-only on the SDK side —
    ``SetSimpleTrigger`` has no query counterpart.
    """

    enabled: bool
    channel: str | None
    threshold_v: float
    direction: str | None
    delay_samples: int
    auto_trigger_ms: int

    def as_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "channel": self.channel,
            "threshold_v": self.threshold_v,
            "direction": self.direction,
            "delay_samples": self.delay_samples,
            "auto_trigger_ms": self.auto_trigger_ms,
        }


@dataclass(frozen=True)
class AWGSettings:
    """Current built-in signal generator configuration, as cached by the driver.

    Like :class:`ChannelSettings`/:class:`TriggerSettings`, ``picosdk`` has no
    "get siggen" query — ``SetSigGenBuiltIn`` is write-only.
    """

    enabled: bool
    wave_type: str | None
    frequency_hz: float
    peak_to_peak_v: float
    offset_v: float

    def as_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "wave_type": self.wave_type,
            "frequency_hz": self.frequency_hz,
            "peak_to_peak_v": self.peak_to_peak_v,
            "offset_v": self.offset_v,
        }


@dataclass(frozen=True)
class ConnectionState:
    """RFDS-002 Section 12.1 normalized connection-state dictionary, as a typed object."""

    alias: str
    resource: str | None
    connected: bool
    communication_ok: bool
    transport: str | None
    identity: str | None
    timeout_s: float | None
    state: str

    def as_dict(self) -> dict[str, object]:
        return {
            "alias": self.alias,
            "resource": self.resource,
            "connected": self.connected,
            "communication_ok": self.communication_ok,
            "transport": self.transport,
            "identity": self.identity,
            "timeout_s": self.timeout_s,
            "state": self.state,
        }
