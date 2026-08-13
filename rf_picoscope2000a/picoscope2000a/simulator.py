"""In-process simulated backend: no ``picosdk``, no hardware, no native driver required.

:class:`SimulatedBus` models "what's physically plugged in" (serial -> model
string) independently of any one :class:`SimulatedBackend` instance's
open/close state, so tests can exercise autodetect's zero/one/many-device
cases by constructing a bus with a chosen set of devices before connecting.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .exceptions import PicoScope2000AConnectionError

DEFAULT_SIMULATED_SERIAL = "SIM/00001"
DEFAULT_SIMULATED_MODEL = "2208B"

# ps2000a 8-bit resolution ADC full-scale count and timebase formula. Both are
# the commonly published approximations for this device family (mirrored in
# Pico's own example comments) — used here only because there's no real
# ps2000a device in this simulator to ask; :class:`~picoscope2000a.backend.RealPs2000aBackend`
# never uses either constant, it always asks the real device via
# ``ps2000aMaximumValue``/``ps2000aGetTimebase2`` instead.
_SIMULATED_MAX_ADC = 32512
_SIMULATED_MEMORY_SAMPLES = 1_000_000

# A deterministic synthetic signal (fraction of full-scale ADC counts) every
# simulated channel "captures", so tests can assert decoded frequency/
# amplitude are correct within tolerance. Each channel gets a fixed, known
# phase offset relative to channel A (B lags by a quarter cycle, C by a half,
# D by three-quarters) so cross-channel delay/phase measurements have a
# known non-zero expected value to test against too — a real multi-channel
# capture wouldn't have every channel perfectly in phase either.
SIMULATED_SIGNAL_FREQUENCY_HZ = 1_000.0
SIMULATED_SIGNAL_AMPLITUDE_FRACTION = 0.5
SIMULATED_CHANNEL_PHASE_OFFSET_RAD = {
    "A": 0.0,
    "B": math.pi / 2,
    "C": math.pi,
    "D": 3 * math.pi / 2,
}


def _simulated_timebase_to_interval_s(timebase_index: int) -> float:
    if timebase_index < 3:
        return (2**timebase_index) * 1e-9
    return (timebase_index - 2) * 8e-9


@dataclass
class SimulatedBus:
    """serial -> model string for every simulated device "connected" to the host."""

    devices: dict[str, str] = field(
        default_factory=lambda: {DEFAULT_SIMULATED_SERIAL: DEFAULT_SIMULATED_MODEL}
    )


class SimulatedBackend:
    """Implements :class:`~picoscope2000a.backend.Ps2000aBackend` against a :class:`SimulatedBus`."""

    def __init__(self, bus: SimulatedBus | None = None) -> None:
        self.bus = bus if bus is not None else SimulatedBus()
        self._serial: str | None = None
        self._model: str | None = None
        self.channels: dict[str, dict[str, object]] = {}
        self.trigger: dict[str, object] | None = None
        self.awg: dict[str, object] | None = None

    def enumerate_devices(self) -> list[str]:
        return sorted(self.bus.devices)

    def open(self, serial: str) -> None:
        if serial not in self.bus.devices:
            available = ", ".join(sorted(self.bus.devices)) or "none"
            raise PicoScope2000AConnectionError(
                f"no simulated PicoScope with serial {serial!r}; available: {available}"
            )
        self._serial = serial
        self._model = self.bus.devices[serial]

    def close(self) -> None:
        self._serial = None
        self._model = None

    def is_open(self) -> bool:
        return self._serial is not None

    def _require_open(self) -> None:
        if self._serial is None:
            raise PicoScope2000AConnectionError("backend is not open")

    def get_unit_info(self) -> dict[str, str]:
        self._require_open()
        return {
            "manufacturer": "Pico Technology",
            "model": self._model or "",
            "serial": self._serial or "",
            "firmware": "1.0.0.0",
            "driver_version": "SIMULATED",
        }

    def set_channel(
        self, channel: str, enabled: bool, coupling: int, range_index: int, offset_v: float
    ) -> None:
        self._require_open()
        self.channels[channel] = {
            "enabled": bool(enabled),
            "coupling": int(coupling),
            "range_index": int(range_index),
            "offset_v": float(offset_v),
        }

    def maximum_adc_value(self) -> int:
        self._require_open()
        return _SIMULATED_MAX_ADC

    def get_timebase(self, timebase_index: int, num_samples: int) -> tuple[float, int]:
        self._require_open()
        return _simulated_timebase_to_interval_s(timebase_index), _SIMULATED_MEMORY_SAMPLES

    def set_simple_trigger(
        self,
        enabled: bool,
        channel: str,
        threshold_adc: int,
        direction: int,
        delay_samples: int,
        auto_trigger_ms: int,
    ) -> None:
        self._require_open()
        self.trigger = {
            "enabled": bool(enabled),
            "channel": channel,
            "threshold_adc": int(threshold_adc),
            "direction": int(direction),
            "delay_samples": int(delay_samples),
            "auto_trigger_ms": int(auto_trigger_ms),
        }

    def run_block_capture(
        self,
        pre_samples: int,
        post_samples: int,
        timebase_index: int,
        channels: list[str],
        timeout_s: float,
    ) -> dict[str, list[int]]:
        self._require_open()
        del timeout_s  # the simulator never actually waits
        total_samples = pre_samples + post_samples
        interval_s, _max_samples = self.get_timebase(timebase_index, total_samples)
        amplitude_adc = _SIMULATED_MAX_ADC * SIMULATED_SIGNAL_AMPLITUDE_FRACTION
        angular_freq = 2 * math.pi * SIMULATED_SIGNAL_FREQUENCY_HZ
        result: dict[str, list[int]] = {}
        for channel in channels:
            phase_offset = SIMULATED_CHANNEL_PHASE_OFFSET_RAD.get(channel, 0.0)
            result[channel] = [
                int(
                    round(
                        amplitude_adc
                        * math.sin(angular_freq * (i - pre_samples) * interval_s - phase_offset)
                    )
                )
                for i in range(total_samples)
            ]
        return result

    def set_sig_gen_built_in(
        self, offset_uv: int, pk_to_pk_uv: int, wave_type: int, frequency_hz: float
    ) -> None:
        self._require_open()
        self.awg = {
            "offset_uv": int(offset_uv),
            "pk_to_pk_uv": int(pk_to_pk_uv),
            "wave_type": int(wave_type),
            "frequency_hz": float(frequency_hz),
        }
