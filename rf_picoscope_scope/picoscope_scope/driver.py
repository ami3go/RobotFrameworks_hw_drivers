"""Typed core driver for PicoScope oscilloscopes, across multiple SDK series.

Owns backend selection (via ``series``), autodetect, and identity. The
Robot Framework adapter (``rf_picoscope_scope/library.py``) is a thin layer
on top of this module and must not duplicate any of this logic. Channel/
trigger/timebase/capture/measurement/CSV/image/preset logic below is
series-agnostic by design — only :mod:`backend` knows which concrete SDK
module (``picosdk.ps2000a``, ``picosdk.ps3000a``, ...) it's calling.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from . import plotting
from .backend import PicoScopeBackend, RealPs2000aBackend, RealPs3000aBackend
from .enums import Channel, Coupling, MeasurementType, ProbeType, Range, TriggerDirection, WaveType
from .exceptions import (
    PicoScopeConnectionError,
    PicoScopeDeviceError,
    PicoScopeValidationError,
)
from .measurements import compute_delay, compute_measurements, compute_phase
from .models import (
    AWGSettings,
    ChannelSettings,
    InstrumentIdentity,
    Measurements,
    TimebaseSettings,
    TriggerSettings,
    Waveform,
)
from .simulator import SimulatedBackend, SimulatedBus

_DEFAULT_CHANNEL_RANGE_V = 5.0
_DEFAULT_CHANNEL_COUPLING = Coupling.DC
_DEFAULT_CAPTURE_TIMEOUT_S = 10.0
_VALID_CHANNELS = {member.value for member in Channel}
_VALID_PROBE_TYPES = {member.value for member in ProbeType}
_TIMEBASE_SEARCH_LIMIT = 2_000_000
_DISABLED_TRIGGER = TriggerSettings(
    enabled=False, channel=None, threshold_v=0.0, direction=None, delay_samples=0, auto_trigger_ms=0
)
_DISABLED_AWG = AWGSettings(
    enabled=False, wave_type=None, frequency_hz=0.0, peak_to_peak_v=0.0, offset_v=0.0
)

# One real backend class per supported SDK series. "2000A"/"3000A" match the
# actual picosdk module names (ps2000a, ps3000a) — deliberately not plain
# "2000"/"3000", which would be ambiguous with Pico's older, out-of-scope
# non-A legacy APIs (ps2000/ps3000) for older units like the 2104/2202/3204.
_DEFAULT_SERIES = "2000A"
_REAL_BACKEND_BY_SERIES: dict[str, type[PicoScopeBackend]] = {
    "2000A": RealPs2000aBackend,
    "3000A": RealPs3000aBackend,
}
# Default simulated device per series, used by connect_simulated() when no
# explicit `bus` is passed — "2000A" is unchanged from before this driver
# supported multiple series, so every existing caller's behavior is identical.
_DEFAULT_SIMULATED_DEVICE_BY_SERIES: dict[str, tuple[str, str]] = {
    "2000A": ("SIM/00001", "2208B"),
    "3000A": ("SIM/00001", "3405D MSO"),
}
# Model substrings with a built-in AWG, matched against GetUnitInfo's model
# string (e.g. "2208B", "2206 MSO", "3405D MSO"), per series. Best-effort,
# not exhaustive — see package README for what's confirmed vs. assumed.
_AWG_CAPABLE_MODEL_SUBSTRINGS_BY_SERIES: dict[str, tuple[str, ...]] = {
    "2000A": ("2205A", "2206", "2207", "2208", "2405A"),
    "3000A": ("3204D", "3404D", "3405D"),
}


@dataclass
class _Capture:
    """Raw ADC counts from the last block capture — internal, not part of the public API."""

    raw_counts: dict[str, list[int]]
    pre_samples: int
    sample_interval_s: float


def _validate_series(series: str) -> str:
    normalized = str(series).strip().upper()
    if normalized not in _REAL_BACKEND_BY_SERIES:
        raise PicoScopeValidationError(
            f"series must be one of {sorted(_REAL_BACKEND_BY_SERIES)}, got {series!r}"
        )
    return normalized


def _validate_channel(channel: str) -> str:
    normalized = str(channel).strip().upper()
    if normalized not in _VALID_CHANNELS:
        raise PicoScopeValidationError(
            f"channel must be one of A/B/C/D, got {channel!r}"
        )
    return normalized


def _validate_coupling(coupling: str) -> Coupling:
    try:
        return Coupling[str(coupling).strip().upper()]
    except KeyError:
        raise PicoScopeValidationError(
            f"coupling must be AC or DC, got {coupling!r}"
        ) from None


def _validate_probe_type(probe_type: str) -> str:
    normalized = str(probe_type).strip().upper()
    if normalized not in _VALID_PROBE_TYPES:
        raise PicoScopeValidationError(
            f"probe_type must be one of {sorted(_VALID_PROBE_TYPES)}, got {probe_type!r}"
        )
    return normalized


def _validate_wave_type(wave_type: str) -> WaveType:
    try:
        return WaveType[str(wave_type).strip().upper()]
    except KeyError:
        raise PicoScopeValidationError(
            f"wave_type must be one of {[m.name for m in WaveType]}, got {wave_type!r}"
        ) from None


def _validate_measurement_type(measurement_type: str) -> MeasurementType:
    normalized = str(measurement_type).strip().upper()
    for member in MeasurementType:
        if member.name == normalized or member.value.upper() == normalized:
            return member
    raise PicoScopeValidationError(
        f"measurement_type must be one of {[m.name for m in MeasurementType]}, "
        f"got {measurement_type!r}"
    )


_MEASUREMENT_FIELD = {
    MeasurementType.AMPLITUDE: "amplitude",
    MeasurementType.PEAK_TO_PEAK: "peak_to_peak",
    MeasurementType.MAXIMUM: "maximum",
    MeasurementType.MINIMUM: "minimum",
    MeasurementType.HIGH: "high",
    MeasurementType.LOW: "low",
    MeasurementType.MEAN: "mean",
    MeasurementType.RMS: "rms",
    MeasurementType.CYCLE_RMS: "cycle_rms",
    MeasurementType.FREQUENCY: "frequency_hz",
    MeasurementType.PERIOD: "period_s",
    MeasurementType.RISE_TIME: "rise_time_s",
    MeasurementType.FALL_TIME: "fall_time_s",
    MeasurementType.POSITIVE_WIDTH: "positive_width_s",
    MeasurementType.NEGATIVE_WIDTH: "negative_width_s",
    MeasurementType.POSITIVE_DUTY: "positive_duty_cycle_pct",
    MeasurementType.POSITIVE_OVERSHOOT: "positive_overshoot_pct",
    MeasurementType.NEGATIVE_OVERSHOOT: "negative_overshoot_pct",
}


def _validate_trigger_direction(direction: str) -> TriggerDirection:
    try:
        return TriggerDirection[str(direction).strip().upper()]
    except KeyError:
        raise PicoScopeValidationError(
            f"direction must be RISING or FALLING, got {direction!r}"
        ) from None


def _validate_edge(edge: str) -> bool:
    """Returns ``True`` for a rising edge, ``False`` for falling — used by the
    cross-channel delay/phase measurements, which aren't SDK-facing so don't need
    :class:`TriggerDirection`'s numeric ``PS2000A_THRESHOLD_DIRECTION`` values."""

    normalized = str(edge).strip().upper()
    if normalized == "RISING":
        return True
    if normalized == "FALLING":
        return False
    raise PicoScopeValidationError(f"edge must be RISING or FALLING, got {edge!r}")


def _default_channel_settings(channel: str) -> ChannelSettings:
    return ChannelSettings(
        channel=channel,
        enabled=(channel == Channel.A.value),
        range_v=_DEFAULT_CHANNEL_RANGE_V,
        coupling=_DEFAULT_CHANNEL_COUPLING.name,
        offset_v=0.0,
        probe_type=ProbeType.VOLTAGE.value,
        probe_scale=1.0,
    )


class PicoScope:
    """A connected session with one PicoScope instrument, on any supported series."""

    def __init__(self, backend: PicoScopeBackend, series: str = _DEFAULT_SERIES) -> None:
        self.backend = backend
        self.series = series
        self.resource: str | None = None
        self._identity: InstrumentIdentity | None = None
        self._channels: dict[str, ChannelSettings] = {
            member.value: _default_channel_settings(member.value) for member in Channel
        }
        self._timebase: TimebaseSettings | None = None
        self._trigger: TriggerSettings = _DISABLED_TRIGGER
        self._awg: AWGSettings = _DISABLED_AWG
        self._last_capture: _Capture | None = None

    # ------------------------------------------------------------------
    # Construction / lifecycle
    # ------------------------------------------------------------------
    @classmethod
    def connect(cls, resource: str | None = None, series: str = _DEFAULT_SERIES) -> PicoScope:
        """Open real hardware. ``resource`` is a serial; omit it to autodetect.

        ``series`` selects which SDK/native driver to use (e.g. ``"2000A"``
        for ``picosdk.ps2000a``, ``"3000A"`` for ``picosdk.ps3000a``) — the
        real SDKs are separate native drivers with their own enumerate/open
        calls, so this can't be autodetected the way a serial number can."""

        series = _validate_series(series)
        backend_cls = _REAL_BACKEND_BY_SERIES[series]
        return cls._connect_with_backend(backend_cls(), resource, series)

    @classmethod
    def connect_simulated(
        cls, resource: str | None = None, bus: SimulatedBus | None = None, series: str = _DEFAULT_SERIES
    ) -> PicoScope:
        series = _validate_series(series)
        if bus is None:
            default_serial, default_model = _DEFAULT_SIMULATED_DEVICE_BY_SERIES[series]
            bus = SimulatedBus(devices={default_serial: default_model})
        return cls._connect_with_backend(SimulatedBackend(bus), resource, series)

    @classmethod
    def _connect_with_backend(
        cls, backend: PicoScopeBackend, resource: str | None, series: str = _DEFAULT_SERIES
    ) -> PicoScope:
        driver = cls(backend, series=series)
        driver._open(resource)
        return driver

    @staticmethod
    def enumerate_devices_for_series(series: str = _DEFAULT_SERIES, simulated: bool = False) -> list[str]:
        """Lists connected serials for one series without opening any of them or
        creating a session — used by ``Find Devices`` when no session is open yet."""

        series = _validate_series(series)
        if simulated:
            default_serial, default_model = _DEFAULT_SIMULATED_DEVICE_BY_SERIES[series]
            bus = SimulatedBus(devices={default_serial: default_model})
            return SimulatedBackend(bus).enumerate_devices()
        return _REAL_BACKEND_BY_SERIES[series]().enumerate_devices()

    def _open(self, resource: str | None) -> None:
        if resource is None:
            candidates = self.backend.enumerate_devices()
            if not candidates:
                raise PicoScopeConnectionError(
                    "no PicoScope devices found; connect one or pass resource explicitly"
                )
            if len(candidates) > 1:
                raise PicoScopeConnectionError(
                    f"multiple PicoScope devices found ({', '.join(candidates)}); "
                    "pass resource explicitly to select one"
                )
            resource = candidates[0]
        self.backend.open(str(resource))
        self.resource = str(resource)
        # Push our known-good channel defaults immediately: SetChannel is
        # write-only (no "get channel" query exists), so the cached
        # ChannelSettings would otherwise just be an unverified guess about
        # the device's true power-on state.
        for settings in self._channels.values():
            self._push_channel(settings)

    def close(self) -> None:
        if self.backend.is_open():
            self.backend.close()
        self.resource = None
        self._identity = None

    @property
    def connected(self) -> bool:
        return self.backend.is_open()

    def _require_connected(self) -> None:
        if not self.connected:
            raise PicoScopeConnectionError(
                "not connected; call 'connect'/'connect_simulated' first"
            )

    # ------------------------------------------------------------------
    # Autodetect / identity
    # ------------------------------------------------------------------
    def enumerate_devices(self) -> list[str]:
        """List connected device serials without opening any of them."""

        return self.backend.enumerate_devices()

    def identify(self, *, refresh: bool = True) -> InstrumentIdentity:
        self._require_connected()
        if not refresh and self._identity is not None:
            return self._identity
        info = self.backend.get_unit_info()
        raw = f"{info['manufacturer']},{info['model']},{info['serial']},{info['driver_version']}"
        identity = InstrumentIdentity(
            manufacturer=info["manufacturer"],
            model=info["model"],
            serial=info["serial"],
            firmware=info.get("firmware", ""),
            driver_version=info["driver_version"],
            raw=raw,
        )
        self._identity = identity
        return identity

    def check_communication(self) -> bool:
        self._require_connected()
        self.backend.get_unit_info()
        return True

    # ------------------------------------------------------------------
    # Channel configuration
    # ------------------------------------------------------------------
    def _push_channel(self, settings: ChannelSettings) -> None:
        self.backend.set_channel(
            settings.channel,
            settings.enabled,
            int(Coupling[settings.coupling]),
            int(Range.nearest(settings.range_v)),
            settings.offset_v,
        )

    def set_channel_enabled(self, channel: str, enabled: bool) -> None:
        self._require_connected()
        channel = _validate_channel(channel)
        updated = replace(self._channels[channel], enabled=bool(enabled))
        self._push_channel(updated)
        self._channels[channel] = updated

    def get_channel_enabled(self, channel: str) -> bool:
        self._require_connected()
        return self._channels[_validate_channel(channel)].enabled

    def set_channel_range(self, channel: str, range_v: float) -> float:
        """Selects the smallest ps2000a range that still covers ``range_v``; returns it."""

        self._require_connected()
        channel = _validate_channel(channel)
        resolved = Range.nearest(range_v)
        updated = replace(self._channels[channel], range_v=resolved.volts())
        self._push_channel(updated)
        self._channels[channel] = updated
        return updated.range_v

    def get_channel_range(self, channel: str) -> float:
        self._require_connected()
        return self._channels[_validate_channel(channel)].range_v

    def set_channel_coupling(self, channel: str, coupling: str) -> None:
        self._require_connected()
        channel = _validate_channel(channel)
        resolved = _validate_coupling(coupling)
        updated = replace(self._channels[channel], coupling=resolved.name)
        self._push_channel(updated)
        self._channels[channel] = updated

    def get_channel_coupling(self, channel: str) -> str:
        self._require_connected()
        return self._channels[_validate_channel(channel)].coupling

    def set_channel_offset(self, channel: str, offset_v: float) -> None:
        self._require_connected()
        channel = _validate_channel(channel)
        updated = replace(self._channels[channel], offset_v=float(offset_v))
        self._push_channel(updated)
        self._channels[channel] = updated

    def get_channel_offset(self, channel: str) -> float:
        self._require_connected()
        return self._channels[_validate_channel(channel)].offset_v

    def set_channel_probe(self, channel: str, probe_type: str, scale: float = 1.0) -> None:
        """Driver-side only — ``picosdk`` has no probe concept, so no backend I/O here.

        ``scale`` is native units per volt at the ADC input, e.g. a 100 mV/A
        current clamp uses ``scale=10`` with ``probe_type="CURRENT"`` so
        ``get_waveform`` reports amps for this channel.
        """

        self._require_connected()
        channel = _validate_channel(channel)
        resolved_type = _validate_probe_type(probe_type)
        scale = float(scale)
        if scale <= 0:
            raise PicoScopeValidationError(f"scale must be positive, got {scale!r}")
        self._channels[channel] = replace(
            self._channels[channel], probe_type=resolved_type, probe_scale=scale
        )

    def get_channel_probe(self, channel: str) -> dict[str, object]:
        self._require_connected()
        settings = self._channels[_validate_channel(channel)]
        return {"probe_type": settings.probe_type, "probe_scale": settings.probe_scale}

    def get_channel_settings(self, channel: str) -> ChannelSettings:
        self._require_connected()
        return self._channels[_validate_channel(channel)]

    def get_enabled_channels(self) -> list[str]:
        self._require_connected()
        return [ch for ch in sorted(self._channels) if self._channels[ch].enabled]

    # ------------------------------------------------------------------
    # Timebase (main time settings)
    # ------------------------------------------------------------------
    def set_timebase(
        self, sample_interval_s: float, num_samples: int, pre_trigger_ratio: float = 0.0
    ) -> TimebaseSettings:
        """Resolves the fastest ps2000a timebase whose achieved interval is at
        least ``sample_interval_s``, by probing ``ps2000aGetTimebase2``
        upward from index 0 — there is no direct "set sample rate" call."""

        self._require_connected()
        sample_interval_s = float(sample_interval_s)
        num_samples = int(num_samples)
        pre_trigger_ratio = float(pre_trigger_ratio)
        if sample_interval_s <= 0:
            raise PicoScopeValidationError(
                f"sample_interval_s must be positive, got {sample_interval_s!r}"
            )
        if num_samples <= 0:
            raise PicoScopeValidationError(
                f"num_samples must be positive, got {num_samples!r}"
            )
        if not 0.0 <= pre_trigger_ratio <= 1.0:
            raise PicoScopeValidationError(
                f"pre_trigger_ratio must be between 0 and 1, got {pre_trigger_ratio!r}"
            )

        achieved_interval_s = None
        max_samples = None
        timebase_index = None
        for candidate in range(_TIMEBASE_SEARCH_LIMIT):
            achieved_interval_s, max_samples = self.backend.get_timebase(candidate, num_samples)
            if achieved_interval_s >= sample_interval_s:
                timebase_index = candidate
                break
        if timebase_index is None:
            raise PicoScopeValidationError(
                f"could not find a ps2000a timebase achieving at least "
                f"{sample_interval_s:g} s/sample within {_TIMEBASE_SEARCH_LIMIT} indices"
            )
        if max_samples < num_samples:
            raise PicoScopeValidationError(
                f"timebase {timebase_index} supports at most {max_samples} samples, "
                f"requested {num_samples}"
            )

        self._timebase = TimebaseSettings(
            timebase_index=timebase_index,
            sample_interval_s=achieved_interval_s,
            num_samples=num_samples,
            pre_trigger_ratio=pre_trigger_ratio,
        )
        return self._timebase

    def get_timebase_settings(self) -> TimebaseSettings:
        self._require_connected()
        if self._timebase is None:
            raise PicoScopeValidationError(
                "timebase has not been configured; call 'set_timebase' first"
            )
        return self._timebase

    # ------------------------------------------------------------------
    # Trigger
    # ------------------------------------------------------------------
    def set_trigger(
        self,
        channel: str,
        threshold_v: float,
        direction: str = "RISING",
        delay_samples: int = 0,
        auto_trigger_ms: int = 0,
    ) -> None:
        """``threshold_v`` is always the raw BNC-input voltage, even on a
        current-probe channel — real trigger hardware compares against the
        physical input voltage before any probe scaling is applied, so
        ``probe_scale`` never factors into this threshold."""

        self._require_connected()
        channel = _validate_channel(channel)
        direction_enum = _validate_trigger_direction(direction)
        threshold_v = float(threshold_v)
        delay_samples = int(delay_samples)
        auto_trigger_ms = int(auto_trigger_ms)
        if delay_samples < 0:
            raise PicoScopeValidationError(
                f"delay_samples must not be negative, got {delay_samples!r}"
            )
        if auto_trigger_ms < 0:
            raise PicoScopeValidationError(
                f"auto_trigger_ms must not be negative, got {auto_trigger_ms!r}"
            )

        channel_range_v = self._channels[channel].range_v
        max_adc = self.backend.maximum_adc_value()
        threshold_adc = int(round((threshold_v / channel_range_v) * max_adc))
        threshold_adc = max(-max_adc, min(max_adc, threshold_adc))

        self.backend.set_simple_trigger(
            True, channel, threshold_adc, int(direction_enum), delay_samples, auto_trigger_ms
        )
        self._trigger = TriggerSettings(
            enabled=True,
            channel=channel,
            threshold_v=threshold_v,
            direction=direction_enum.name,
            delay_samples=delay_samples,
            auto_trigger_ms=auto_trigger_ms,
        )

    def disable_trigger(self) -> None:
        self._require_connected()
        self.backend.set_simple_trigger(False, Channel.A.value, 0, int(TriggerDirection.RISING), 0, 0)
        self._trigger = _DISABLED_TRIGGER

    def get_trigger_settings(self) -> TriggerSettings:
        self._require_connected()
        return self._trigger

    # ------------------------------------------------------------------
    # Block capture + waveform retrieval
    # ------------------------------------------------------------------
    def capture_block(self, timeout_s: float | None = None) -> dict[str, object]:
        """Runs one block acquisition and caches the raw per-channel samples.

        ``Get Waveform``/``Get All Waveforms``/CSV/image export all read from
        this cached capture rather than re-triggering hardware — call this
        again for a fresh capture.
        """

        self._require_connected()
        if self._timebase is None:
            raise PicoScopeValidationError(
                "timebase has not been configured; call 'set_timebase' first"
            )
        channels = self.get_enabled_channels()
        if not channels:
            raise PicoScopeValidationError(
                "no channels are enabled; call 'set_channel_enabled' first"
            )
        num_samples = self._timebase.num_samples
        pre_samples = int(round(num_samples * self._timebase.pre_trigger_ratio))
        post_samples = num_samples - pre_samples
        raw_counts = self.backend.run_block_capture(
            pre_samples,
            post_samples,
            self._timebase.timebase_index,
            channels,
            timeout_s if timeout_s is not None else _DEFAULT_CAPTURE_TIMEOUT_S,
        )
        self._last_capture = _Capture(
            raw_counts=raw_counts,
            pre_samples=pre_samples,
            sample_interval_s=self._timebase.sample_interval_s,
        )
        return {
            "channels": sorted(raw_counts),
            "num_samples": num_samples,
            "sample_interval_s": self._timebase.sample_interval_s,
        }

    def _require_capture(self) -> _Capture:
        if self._last_capture is None:
            raise PicoScopeValidationError("no capture available; call 'capture_block' first")
        return self._last_capture

    def _decode_waveform(self, channel: str, capture: _Capture) -> Waveform:
        settings = self._channels[channel]
        max_adc = self.backend.maximum_adc_value()
        raw_counts = capture.raw_counts[channel]
        volts = [(count / max_adc) * settings.range_v for count in raw_counts]
        unit = "A" if settings.probe_type == ProbeType.CURRENT.value else "V"
        values = [v * settings.probe_scale for v in volts]
        time_s = [
            (i - capture.pre_samples) * capture.sample_interval_s for i in range(len(raw_counts))
        ]
        return Waveform(
            channel=channel,
            time_s=time_s,
            values=values,
            unit=unit,
            sample_interval_s=capture.sample_interval_s,
        )

    def get_waveform(self, channel: str) -> Waveform:
        self._require_connected()
        channel = _validate_channel(channel)
        capture = self._require_capture()
        if channel not in capture.raw_counts:
            raise PicoScopeValidationError(
                f"channel {channel!r} was not enabled/captured in the last block capture"
            )
        return self._decode_waveform(channel, capture)

    def get_all_waveforms(self) -> dict[str, Waveform]:
        self._require_connected()
        capture = self._require_capture()
        return {channel: self._decode_waveform(channel, capture) for channel in sorted(capture.raw_counts)}

    # ------------------------------------------------------------------
    # Standard measurements (computed host-side; see measurements.py)
    # ------------------------------------------------------------------
    def get_measurements(self, channel: str) -> Measurements:
        """All standard measurements for one channel's last-captured waveform at once."""

        return compute_measurements(self.get_waveform(channel))

    def get_measurement(self, channel: str, measurement_type: str) -> float:
        measurement_type_enum = _validate_measurement_type(measurement_type)
        measurements = self.get_measurements(channel)
        value = getattr(measurements, _MEASUREMENT_FIELD[measurement_type_enum])
        if value is None:
            raise PicoScopeValidationError(
                f"{measurement_type_enum.name} could not be determined from this capture "
                "(e.g. fewer than two edge crossings — capture more cycles of the signal)"
            )
        return value

    def measurement_should_be_within(
        self, channel: str, measurement_type: str, minimum: float, maximum: float
    ) -> float:
        minimum, maximum = float(minimum), float(maximum)
        if minimum > maximum:
            raise PicoScopeValidationError(
                f"minimum {minimum} must not be greater than maximum {maximum}"
            )
        value = self.get_measurement(channel, measurement_type)
        if not minimum <= value <= maximum:
            raise AssertionError(
                f"{measurement_type} on channel {channel} was {value:g}, expected between "
                f"{minimum:g} and {maximum:g}"
            )
        return value

    # ------------------------------------------------------------------
    # Cross-channel timing measurements
    # ------------------------------------------------------------------
    def get_channel_delay(self, reference_channel: str, target_channel: str, edge: str = "RISING") -> float:
        """Time from ``reference_channel``'s first qualifying edge to the nearest
        corresponding edge on ``target_channel``, in seconds. Positive means
        ``target_channel`` lags ``reference_channel``; negative means it leads."""

        rising = _validate_edge(edge)
        reference_waveform = self.get_waveform(reference_channel)
        target_waveform = self.get_waveform(target_channel)
        delay = compute_delay(reference_waveform, target_waveform, rising=rising)
        if delay is None:
            raise PicoScopeValidationError(
                f"delay between {reference_channel!r} and {target_channel!r} could not be "
                "determined (no qualifying edge on one or both channels in this capture)"
            )
        return delay

    def get_channel_phase(self, reference_channel: str, target_channel: str, edge: str = "RISING") -> float:
        """Phase of ``target_channel`` relative to ``reference_channel``, in degrees,
        using ``reference_channel``'s own measured period as the 360-degree reference."""

        rising = _validate_edge(edge)
        reference_waveform = self.get_waveform(reference_channel)
        target_waveform = self.get_waveform(target_channel)
        phase = compute_phase(reference_waveform, target_waveform, rising=rising)
        if phase is None:
            raise PicoScopeValidationError(
                f"phase between {reference_channel!r} and {target_channel!r} could not be "
                "determined (fewer than two edges on the reference channel, or no "
                "qualifying edge on the target channel, in this capture)"
            )
        return phase

    def channel_delay_should_be_within(
        self,
        reference_channel: str,
        target_channel: str,
        minimum: float,
        maximum: float,
        edge: str = "RISING",
    ) -> float:
        minimum, maximum = float(minimum), float(maximum)
        if minimum > maximum:
            raise PicoScopeValidationError(
                f"minimum {minimum} must not be greater than maximum {maximum}"
            )
        value = self.get_channel_delay(reference_channel, target_channel, edge)
        if not minimum <= value <= maximum:
            raise AssertionError(
                f"delay from {reference_channel} to {target_channel} was {value:g} s, "
                f"expected between {minimum:g} and {maximum:g} s"
            )
        return value

    def channel_phase_should_be_within(
        self,
        reference_channel: str,
        target_channel: str,
        minimum: float,
        maximum: float,
        edge: str = "RISING",
    ) -> float:
        minimum, maximum = float(minimum), float(maximum)
        if minimum > maximum:
            raise PicoScopeValidationError(
                f"minimum {minimum} must not be greater than maximum {maximum}"
            )
        value = self.get_channel_phase(reference_channel, target_channel, edge)
        if not minimum <= value <= maximum:
            raise AssertionError(
                f"phase from {reference_channel} to {target_channel} was {value:g} deg, "
                f"expected between {minimum:g} and {maximum:g} deg"
            )
        return value

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------
    def save_waveform_to_csv(self, path: str | Path, channel: str) -> None:
        """Host-side, from the cached capture — no instrument-side storage exists to use."""

        self._require_connected()
        waveform = self.get_waveform(channel)
        host_path = Path(path)
        host_path.parent.mkdir(parents=True, exist_ok=True)
        column = f"value_{waveform.unit.lower()}"
        with host_path.open("w", encoding="ascii", newline="") as handle:
            handle.write(f"time_s,{column}\n")
            for t, v in zip(waveform.time_s, waveform.values):
                handle.write(f"{t},{v}\n")

    def save_all_waveforms_to_csv(self, path: str | Path) -> None:
        """One shared ``time_s`` column (every channel in a block capture shares one sample
        clock) plus one value column per captured channel, each labelled with its own unit."""

        self._require_connected()
        waveforms = self.get_all_waveforms()
        channels = sorted(waveforms)
        time_s = waveforms[channels[0]].time_s
        host_path = Path(path)
        host_path.parent.mkdir(parents=True, exist_ok=True)
        header = "time_s," + ",".join(f"{ch}_{waveforms[ch].unit.lower()}" for ch in channels)
        with host_path.open("w", encoding="ascii", newline="") as handle:
            handle.write(header + "\n")
            for i, t in enumerate(time_s):
                row = [str(t)] + [str(waveforms[ch].values[i]) for ch in channels]
                handle.write(",".join(row) + "\n")

    # ------------------------------------------------------------------
    # Image export
    # ------------------------------------------------------------------
    def save_channel_image(self, path: str | Path, channel: str, title: str | None = None) -> None:
        """Renders the cached capture's decoded waveform — these units have no display to
        screenshot, so this is a plot of ``Get Waveform``'s data, not an on-device capture."""

        self._require_connected()
        waveform = self.get_waveform(channel)
        plotting.render_channel_image(waveform, Path(path), title)

    def save_all_channels_image(self, path: str | Path, title: str | None = None) -> None:
        self._require_connected()
        waveforms = self.get_all_waveforms()
        plotting.render_all_channels_image(waveforms, Path(path), title)

    # ------------------------------------------------------------------
    # AWG (built-in signal generator)
    # ------------------------------------------------------------------
    def _require_awg_capable(self) -> None:
        model = self.identify(refresh=False).model.upper()
        markers = _AWG_CAPABLE_MODEL_SUBSTRINGS_BY_SERIES[self.series]
        if not any(marker in model for marker in markers):
            raise PicoScopeDeviceError(
                f"connected model {model!r} has no built-in AWG "
                f"(AWG-capable {self.series} models: {'/'.join(markers)})"
            )

    def set_awg_waveform(
        self, wave_type: str, frequency_hz: float, peak_to_peak_v: float, offset_v: float = 0.0
    ) -> None:
        self._require_connected()
        self._require_awg_capable()
        wave_type_enum = _validate_wave_type(wave_type)
        frequency_hz = float(frequency_hz)
        peak_to_peak_v = float(peak_to_peak_v)
        offset_v = float(offset_v)
        if frequency_hz <= 0:
            raise PicoScopeValidationError(
                f"frequency_hz must be positive, got {frequency_hz!r}"
            )
        if peak_to_peak_v <= 0:
            raise PicoScopeValidationError(
                f"peak_to_peak_v must be positive, got {peak_to_peak_v!r}"
            )
        self.backend.set_sig_gen_built_in(
            int(round(offset_v * 1_000_000)),
            int(round(peak_to_peak_v * 1_000_000)),
            int(wave_type_enum),
            frequency_hz,
        )
        self._awg = AWGSettings(
            enabled=True,
            wave_type=wave_type_enum.name,
            frequency_hz=frequency_hz,
            peak_to_peak_v=peak_to_peak_v,
            offset_v=offset_v,
        )

    def stop_awg(self) -> None:
        self._require_connected()
        self._require_awg_capable()
        self.backend.set_sig_gen_built_in(0, 0, int(WaveType.DC_VOLTAGE), 0.0)
        self._awg = _DISABLED_AWG

    def get_awg_settings(self) -> AWGSettings:
        self._require_connected()
        return self._awg

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------
    def save_preset(self, path: str | Path) -> None:
        """A structured JSON snapshot of channel/trigger/timebase/AWG settings — ps2000a
        has no single learn-string call, so this is the driver's own analogue of one."""

        self._require_connected()
        preset = {
            "channels": {ch: self._channels[ch].as_dict() for ch in sorted(self._channels)},
            "trigger": self._trigger.as_dict(),
            "timebase": self._timebase.as_dict() if self._timebase is not None else None,
            "awg": self._awg.as_dict() if self._awg.enabled else None,
        }
        host_path = Path(path)
        host_path.parent.mkdir(parents=True, exist_ok=True)
        host_path.write_text(json.dumps(preset, indent=2), encoding="ascii")

    def load_preset(self, path: str | Path) -> None:
        """Replays a ``Save Preset`` snapshot through the same public setters used to
        create it, so every value round-trips through the same validation/backend push."""

        self._require_connected()
        data = json.loads(Path(path).read_text(encoding="ascii"))

        for channel, settings in data["channels"].items():
            self.set_channel_enabled(channel, settings["enabled"])
            self.set_channel_range(channel, settings["range_v"])
            self.set_channel_coupling(channel, settings["coupling"])
            self.set_channel_offset(channel, settings["offset_v"])
            self.set_channel_probe(channel, settings["probe_type"], scale=settings["probe_scale"])

        trigger = data["trigger"]
        if trigger["enabled"]:
            self.set_trigger(
                trigger["channel"],
                trigger["threshold_v"],
                trigger["direction"],
                trigger["delay_samples"],
                trigger["auto_trigger_ms"],
            )
        else:
            self.disable_trigger()

        if data["timebase"] is not None:
            timebase = data["timebase"]
            self.set_timebase(
                timebase["sample_interval_s"], timebase["num_samples"], timebase["pre_trigger_ratio"]
            )

        if data["awg"] is not None:
            awg = data["awg"]
            self.set_awg_waveform(
                awg["wave_type"], awg["frequency_hz"], awg["peak_to_peak_v"], awg["offset_v"]
            )
        else:
            try:
                self._require_awg_capable()
            except PicoScopeDeviceError:
                pass
            else:
                self.stop_awg()
