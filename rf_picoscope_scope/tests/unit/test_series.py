"""Multi-series selection: the ``series`` argument on ``connect``/``connect_simulated``,
the per-series default simulated device, and per-series AWG-capable-model gating.
"""

from __future__ import annotations

import pytest

from picoscope_scope.driver import PicoScope
from picoscope_scope.exceptions import PicoScopeDeviceError, PicoScopeValidationError
from picoscope_scope.simulator import SimulatedBus


def test_default_series_is_2000a_and_behavior_is_unchanged():
    """No caller has to know about `series` at all to keep working exactly as before."""

    driver = PicoScope.connect_simulated()
    assert driver.series == "2000A"
    assert driver.resource == "SIM/00001"
    assert driver.identify().model == "2208B"
    driver.close()


def test_series_is_case_insensitive():
    driver = PicoScope.connect_simulated(series="3000a")
    assert driver.series == "3000A"
    driver.close()


def test_3000a_series_has_its_own_default_simulated_device():
    driver = PicoScope.connect_simulated(series="3000A")
    assert driver.resource == "SIM/00001"
    assert driver.identify().model == "3405D MSO"
    driver.close()


def test_unknown_series_raises_before_touching_any_backend():
    with pytest.raises(PicoScopeValidationError, match="series must be one of"):
        PicoScope.connect_simulated(series="9000A")


def test_explicit_bus_overrides_the_per_series_default():
    bus = SimulatedBus(devices={"SIM/custom": "3204D"})
    driver = PicoScope.connect_simulated(series="3000A", bus=bus)
    assert driver.resource == "SIM/custom"
    assert driver.identify().model == "3204D"
    driver.close()


def test_channel_trigger_timebase_capture_logic_is_identical_across_series():
    """The whole point of the refactor: series-agnostic logic needs no per-series
    behavior at all — same channel/trigger/timebase/capture/measurement code path."""

    for series in ("2000A", "3000A"):
        driver = PicoScope.connect_simulated(series=series)
        driver.set_channel_enabled("A", True)
        driver.set_channel_range("A", 5.0)
        driver.set_trigger("A", threshold_v=0.5)
        driver.set_timebase(sample_interval_s=20e-6, num_samples=200)
        summary = driver.capture_block()
        assert summary["channels"] == ["A"]
        waveform = driver.get_waveform("A")
        assert len(waveform.values) == 200
        driver.close()


def test_3000a_awg_capable_models_are_recognized():
    for model in ("3204D", "3404D", "3405D", "3405D MSO"):
        bus = SimulatedBus(devices={"SIM/x": model})
        driver = PicoScope.connect_simulated(series="3000A", bus=bus)
        driver.set_awg_waveform("sine", frequency_hz=1000.0, peak_to_peak_v=1.0)  # must not raise
        driver.close()


def test_3000a_non_d_model_has_no_awg():
    bus = SimulatedBus(devices={"SIM/x": "3204A"})  # plain (non-D) 3000A variant
    driver = PicoScope.connect_simulated(series="3000A", bus=bus)
    with pytest.raises(PicoScopeDeviceError, match="no built-in AWG"):
        driver.set_awg_waveform("sine", frequency_hz=1000.0, peak_to_peak_v=1.0)
    driver.close()


def test_2000a_and_3000a_awg_capable_lists_are_independent():
    """A 2000A-family model string must not accidentally satisfy the 3000A gate
    (and vice versa) just because both lists happen to share no overlap today."""

    bus = SimulatedBus(devices={"SIM/x": "2208B"})  # a 2000A model
    driver = PicoScope.connect_simulated(series="3000A", bus=bus)
    with pytest.raises(PicoScopeDeviceError, match="no built-in AWG"):
        driver.set_awg_waveform("sine", frequency_hz=1000.0, peak_to_peak_v=1.0)
    driver.close()


def test_connect_real_hardware_validates_series_before_importing_picosdk():
    """`connect()` (not `_simulated`) must still validate series first — this proves
    the check happens before any backend/SDK touch, not after a failed import."""

    with pytest.raises(PicoScopeValidationError, match="series must be one of"):
        PicoScope.connect(series="9000A")
