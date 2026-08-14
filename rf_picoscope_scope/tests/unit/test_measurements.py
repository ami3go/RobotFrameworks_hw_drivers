"""Standard waveform measurements, verified against the simulator's known synthetic sine
(1 kHz, amplitude = 0.5 * channel range, see picoscope_scope.simulator)."""

from __future__ import annotations

import math

import pytest

from picoscope_scope.driver import PicoScope
from picoscope_scope.exceptions import PicoScopeValidationError
from picoscope_scope.measurements import compute_measurements
from picoscope_scope.models import Waveform
from picoscope_scope.simulator import (
    SIMULATED_SIGNAL_AMPLITUDE_FRACTION,
    SIMULATED_SIGNAL_FREQUENCY_HZ,
)

_RANGE_V = 5.0
_PEAK_V = _RANGE_V * SIMULATED_SIGNAL_AMPLITUDE_FRACTION  # single-sided peak amplitude


@pytest.fixture
def many_cycles_driver():
    """~20 complete cycles at 200 kS/s: plenty of edges for every timing measurement."""

    d = PicoScope.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_channel_range("A", _RANGE_V)
    d.set_timebase(sample_interval_s=5e-6, num_samples=4000)
    d.capture_block()
    yield d
    d.close()


def test_peak_to_peak_and_max_min_are_exact(many_cycles_driver):
    m = many_cycles_driver.get_measurements("A")
    assert m.maximum == pytest.approx(_PEAK_V, rel=0.01)
    assert m.minimum == pytest.approx(-_PEAK_V, rel=0.01)
    assert m.peak_to_peak == pytest.approx(2 * _PEAK_V, rel=0.01)


def test_amplitude_is_close_to_peak_to_peak_for_a_sine(many_cycles_driver):
    """A sine has no flat top/bottom, but spends more time near its extremes than near
    zero (derivative -> 0 at the peaks), so the histogram High/Low method still lands
    close to the true peaks — unlike a plain (max-min)/2 'half amplitude' definition."""

    m = many_cycles_driver.get_measurements("A")
    assert m.amplitude == pytest.approx(m.peak_to_peak, rel=0.03)


def test_mean_is_near_zero_for_a_symmetric_sine(many_cycles_driver):
    m = many_cycles_driver.get_measurements("A")
    assert m.mean == pytest.approx(0.0, abs=0.01)


def test_rms_matches_sine_rms_formula(many_cycles_driver):
    m = many_cycles_driver.get_measurements("A")
    expected_rms = _PEAK_V / math.sqrt(2)
    assert m.rms == pytest.approx(expected_rms, rel=0.01)
    assert m.cycle_rms == pytest.approx(expected_rms, rel=0.02)


def test_frequency_and_period(many_cycles_driver):
    m = many_cycles_driver.get_measurements("A")
    assert m.frequency_hz == pytest.approx(SIMULATED_SIGNAL_FREQUENCY_HZ, rel=0.01)
    assert m.period_s == pytest.approx(1.0 / SIMULATED_SIGNAL_FREQUENCY_HZ, rel=0.01)


def test_positive_and_negative_width_are_each_half_the_period(many_cycles_driver):
    m = many_cycles_driver.get_measurements("A")
    half_period = m.period_s / 2
    assert m.positive_width_s == pytest.approx(half_period, rel=0.02)
    assert m.negative_width_s == pytest.approx(half_period, rel=0.02)


def test_duty_cycle_is_50_percent_for_a_symmetric_sine(many_cycles_driver):
    m = many_cycles_driver.get_measurements("A")
    assert m.positive_duty_cycle_pct == pytest.approx(50.0, abs=1.0)


def test_rise_time_equals_fall_time_for_a_symmetric_sine(many_cycles_driver):
    m = many_cycles_driver.get_measurements("A")
    assert m.rise_time_s is not None
    assert m.fall_time_s is not None
    assert m.rise_time_s == pytest.approx(m.fall_time_s, rel=0.02)
    assert 0 < m.rise_time_s < m.period_s / 2


def test_overshoot_is_small_for_a_smooth_sine(many_cycles_driver):
    m = many_cycles_driver.get_measurements("A")
    assert 0 <= m.positive_overshoot_pct < 5.0
    assert 0 <= m.negative_overshoot_pct < 5.0


def test_unit_matches_channel_probe_unit(many_cycles_driver):
    assert many_cycles_driver.get_measurements("A").unit == "V"


def test_current_probe_channel_measurements_are_in_amps():
    d = PicoScope.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_channel_range("A", _RANGE_V)
    d.set_channel_probe("A", "current", scale=10.0)
    d.set_timebase(sample_interval_s=5e-6, num_samples=4000)
    d.capture_block()
    m = d.get_measurements("A")
    assert m.unit == "A"
    assert m.peak_to_peak == pytest.approx(2 * _PEAK_V * 10.0, rel=0.01)


def test_get_measurement_returns_a_single_named_value(many_cycles_driver):
    assert many_cycles_driver.get_measurement("A", "FREQUENCY") == pytest.approx(
        SIMULATED_SIGNAL_FREQUENCY_HZ, rel=0.01
    )
    assert many_cycles_driver.get_measurement("A", "PK2Pk") == pytest.approx(2 * _PEAK_V, rel=0.01)


def test_get_measurement_accepts_enum_name_or_scope_style_abbreviation(many_cycles_driver):
    by_name = many_cycles_driver.get_measurement("A", "PEAK_TO_PEAK")
    by_abbreviation = many_cycles_driver.get_measurement("A", "PK2Pk")
    assert by_name == by_abbreviation


def test_get_measurement_rejects_unknown_type(many_cycles_driver):
    with pytest.raises(PicoScopeValidationError):
        many_cycles_driver.get_measurement("A", "BOGUS")


def test_get_measurement_raises_when_undeterminable_from_a_too_short_capture():
    """Fewer than two edge crossings in the whole capture: frequency/period/edge
    timing measurements can't be computed."""

    d = PicoScope.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_channel_range("A", _RANGE_V)
    # A tiny slice of one cycle: not enough for even one full period.
    d.set_timebase(sample_interval_s=5e-6, num_samples=5)
    d.capture_block()
    with pytest.raises(PicoScopeValidationError, match="could not be determined"):
        d.get_measurement("A", "FREQUENCY")
    # But amplitude/max/min/mean/rms always work, regardless of cycle count.
    assert d.get_measurement("A", "MAXIMUM") is not None


def test_measurement_should_be_within_passes_inside_range(many_cycles_driver):
    value = many_cycles_driver.measurement_should_be_within("A", "FREQUENCY", 900.0, 1100.0)
    assert value == pytest.approx(SIMULATED_SIGNAL_FREQUENCY_HZ, rel=0.01)


def test_measurement_should_be_within_fails_outside_range(many_cycles_driver):
    with pytest.raises(AssertionError):
        many_cycles_driver.measurement_should_be_within("A", "FREQUENCY", 1.0, 2.0)


def test_measurement_should_be_within_rejects_inverted_range(many_cycles_driver):
    with pytest.raises(PicoScopeValidationError):
        many_cycles_driver.measurement_should_be_within("A", "FREQUENCY", 100.0, 1.0)


def test_get_measurements_requires_a_capture():
    d = PicoScope.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_timebase(sample_interval_s=5e-6, num_samples=100)
    with pytest.raises(PicoScopeValidationError, match="no capture available"):
        d.get_measurements("A")


def test_compute_measurements_rejects_an_empty_waveform():
    empty = Waveform(channel="A", time_s=[], values=[], unit="V", sample_interval_s=1e-6)
    with pytest.raises(PicoScopeValidationError, match="no samples"):
        compute_measurements(empty)
