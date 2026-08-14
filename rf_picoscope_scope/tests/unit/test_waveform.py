"""Block capture and waveform decode, including current-probe unit conversion."""

from __future__ import annotations

import pytest

from picoscope_scope.driver import PicoScope
from picoscope_scope.exceptions import PicoScopeValidationError
from picoscope_scope.simulator import (
    SIMULATED_SIGNAL_AMPLITUDE_FRACTION,
    SIMULATED_SIGNAL_FREQUENCY_HZ,
)

_SAMPLE_INTERVAL_S = 20e-6  # 50 kS/s: >> 2x the 1 kHz simulated signal, well within Nyquist
_NUM_SAMPLES = 1000


@pytest.fixture
def driver():
    d = PicoScope.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_channel_range("A", 5.0)
    d.set_timebase(sample_interval_s=_SAMPLE_INTERVAL_S, num_samples=_NUM_SAMPLES)
    yield d
    d.close()


def _measured_amplitude(values: list[float]) -> float:
    return (max(values) - min(values)) / 2


def _measured_frequency_hz(time_s: list[float], values: list[float]) -> float:
    """Zero-crossing based frequency estimate, good enough for a tolerance check."""

    crossings = []
    for i in range(1, len(values)):
        if values[i - 1] < 0 <= values[i]:
            # linear-interpolate the crossing time for better accuracy than a bare index.
            t0, t1 = time_s[i - 1], time_s[i]
            v0, v1 = values[i - 1], values[i]
            crossings.append(t0 + (0 - v0) * (t1 - t0) / (v1 - v0))
    assert len(crossings) >= 2, "not enough rising zero-crossings to estimate frequency"
    periods = [b - a for a, b in zip(crossings, crossings[1:])]
    return 1.0 / (sum(periods) / len(periods))


def test_capture_block_requires_timebase():
    driver = PicoScope.connect_simulated()
    driver.set_channel_enabled("A", True)
    with pytest.raises(PicoScopeValidationError, match="timebase has not been configured"):
        driver.capture_block()


def test_capture_block_requires_an_enabled_channel():
    driver = PicoScope.connect_simulated()
    driver.set_channel_enabled("A", False)
    driver.set_timebase(sample_interval_s=1e-6, num_samples=100)
    with pytest.raises(PicoScopeValidationError, match="no channels are enabled"):
        driver.capture_block()


def test_get_waveform_requires_a_capture(driver):
    with pytest.raises(PicoScopeValidationError, match="no capture available"):
        driver.get_waveform("A")


def test_capture_block_returns_a_summary(driver):
    summary = driver.capture_block()
    assert summary["channels"] == ["A"]
    assert summary["num_samples"] == _NUM_SAMPLES
    assert summary["sample_interval_s"] == pytest.approx(_SAMPLE_INTERVAL_S)


def test_get_waveform_decodes_correct_shape_and_unit(driver):
    driver.capture_block()
    waveform = driver.get_waveform("A")
    assert waveform.channel == "A"
    assert len(waveform.time_s) == _NUM_SAMPLES
    assert len(waveform.values) == _NUM_SAMPLES
    assert waveform.unit == "V"
    assert waveform.sample_interval_s == pytest.approx(_SAMPLE_INTERVAL_S)


def test_get_waveform_time_is_trigger_relative(driver):
    driver.set_timebase(sample_interval_s=_SAMPLE_INTERVAL_S, num_samples=100, pre_trigger_ratio=0.5)
    driver.capture_block()
    waveform = driver.get_waveform("A")
    assert waveform.time_s[0] == pytest.approx(-50 * _SAMPLE_INTERVAL_S)
    assert waveform.time_s[50] == pytest.approx(0.0, abs=1e-12)


def test_get_waveform_decodes_correct_amplitude_and_frequency(driver):
    driver.capture_block()
    waveform = driver.get_waveform("A")
    expected_amplitude_v = 5.0 * SIMULATED_SIGNAL_AMPLITUDE_FRACTION
    assert _measured_amplitude(waveform.values) == pytest.approx(expected_amplitude_v, rel=0.01)
    assert _measured_frequency_hz(waveform.time_s, waveform.values) == pytest.approx(
        SIMULATED_SIGNAL_FREQUENCY_HZ, rel=0.02
    )


def test_get_waveform_scales_smaller_range_proportionally(driver):
    driver.set_channel_range("A", 1.0)
    driver.capture_block()
    waveform = driver.get_waveform("A")
    expected_amplitude_v = 1.0 * SIMULATED_SIGNAL_AMPLITUDE_FRACTION
    assert _measured_amplitude(waveform.values) == pytest.approx(expected_amplitude_v, rel=0.01)


def test_current_probe_channel_reports_amps(driver):
    driver.set_channel_probe("A", "current", scale=10.0)  # 100 mV/A clamp
    driver.capture_block()
    waveform = driver.get_waveform("A")
    assert waveform.unit == "A"
    expected_amplitude_a = 5.0 * SIMULATED_SIGNAL_AMPLITUDE_FRACTION * 10.0
    assert _measured_amplitude(waveform.values) == pytest.approx(expected_amplitude_a, rel=0.01)


def test_get_waveform_rejects_unenabled_channel(driver):
    driver.capture_block()
    with pytest.raises(PicoScopeValidationError, match="was not enabled/captured"):
        driver.get_waveform("B")


def test_get_all_waveforms_returns_every_captured_channel():
    driver = PicoScope.connect_simulated()
    driver.set_channel_enabled("A", True)
    driver.set_channel_enabled("B", True)
    driver.set_timebase(sample_interval_s=_SAMPLE_INTERVAL_S, num_samples=200)
    driver.capture_block()
    waveforms = driver.get_all_waveforms()
    assert set(waveforms) == {"A", "B"}
    assert waveforms["A"].channel == "A"
    assert waveforms["B"].channel == "B"


def test_get_all_waveforms_requires_a_capture():
    driver = PicoScope.connect_simulated()
    driver.set_timebase(sample_interval_s=_SAMPLE_INTERVAL_S, num_samples=200)
    with pytest.raises(PicoScopeValidationError, match="no capture available"):
        driver.get_all_waveforms()


def test_recapture_replaces_previous_waveform_data(driver):
    driver.capture_block()
    first = driver.get_waveform("A").values[:]
    driver.capture_block()
    second = driver.get_waveform("A").values[:]
    # Same deterministic simulated signal + settings -> same result, but this
    # proves the second capture_block() call didn't just append/leak state.
    assert first == second
    assert len(second) == _NUM_SAMPLES
