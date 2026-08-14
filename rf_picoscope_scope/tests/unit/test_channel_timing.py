"""Cross-channel timing measurements (delay, phase).

The simulator gives each channel a fixed, known phase offset relative to
channel A (B lags by a quarter cycle, C by a half, D by three-quarters — see
picoscope_scope.simulator.SIMULATED_CHANNEL_PHASE_OFFSET_RAD), so these have
known non-zero expected values, not just a same-signal-vs-itself sanity check.
"""

from __future__ import annotations

import pytest

from picoscope_scope.driver import PicoScope
from picoscope_scope.exceptions import PicoScopeValidationError
from picoscope_scope.simulator import SIMULATED_SIGNAL_FREQUENCY_HZ

_PERIOD_S = 1.0 / SIMULATED_SIGNAL_FREQUENCY_HZ


@pytest.fixture
def three_channel_driver():
    d = PicoScope.connect_simulated()
    for channel in ("A", "B", "C"):
        d.set_channel_enabled(channel, True)
        d.set_channel_range(channel, 5.0)
    d.set_timebase(sample_interval_s=5e-6, num_samples=4000)  # ~20 cycles
    d.capture_block()
    yield d
    d.close()


def test_delay_b_relative_to_a_is_a_quarter_period(three_channel_driver):
    delay = three_channel_driver.get_channel_delay("A", "B")
    assert delay == pytest.approx(_PERIOD_S / 4, rel=0.02)


def test_delay_c_relative_to_a_is_a_half_period(three_channel_driver):
    delay = three_channel_driver.get_channel_delay("A", "C")
    assert delay == pytest.approx(_PERIOD_S / 2, rel=0.02)


def test_delay_is_antisymmetric(three_channel_driver):
    forward = three_channel_driver.get_channel_delay("A", "B")
    backward = three_channel_driver.get_channel_delay("B", "A")
    assert backward == pytest.approx(-forward, rel=0.02)


def test_delay_of_a_channel_against_itself_is_zero(three_channel_driver):
    delay = three_channel_driver.get_channel_delay("A", "A")
    assert delay == pytest.approx(0.0, abs=1e-9)


def test_phase_b_relative_to_a_is_90_degrees(three_channel_driver):
    phase = three_channel_driver.get_channel_phase("A", "B")
    assert phase == pytest.approx(90.0, abs=2.0)


def test_phase_c_relative_to_a_is_180_degrees(three_channel_driver):
    phase = three_channel_driver.get_channel_phase("A", "C")
    assert phase == pytest.approx(180.0, abs=2.0)


def test_falling_edge_gives_the_same_delay_as_rising_for_a_pure_sine(three_channel_driver):
    rising_delay = three_channel_driver.get_channel_delay("A", "B", edge="RISING")
    falling_delay = three_channel_driver.get_channel_delay("A", "B", edge="FALLING")
    assert falling_delay == pytest.approx(rising_delay, rel=0.02)


def test_get_channel_delay_rejects_invalid_edge(three_channel_driver):
    with pytest.raises(PicoScopeValidationError):
        three_channel_driver.get_channel_delay("A", "B", edge="sideways")


def test_get_channel_delay_requires_both_channels_captured(three_channel_driver):
    with pytest.raises(PicoScopeValidationError, match="was not enabled/captured"):
        three_channel_driver.get_channel_delay("A", "D")


def test_get_channel_delay_raises_when_too_few_edges():
    d = PicoScope.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_channel_enabled("B", True)
    # A single sample: genuinely zero crossings possible (a tiny multi-sample
    # slice would still cross its own local midpoint at least once, since the
    # histogram high/low is computed from whatever's in the window).
    d.set_timebase(sample_interval_s=5e-6, num_samples=1)
    d.capture_block()
    with pytest.raises(PicoScopeValidationError, match="could not be determined"):
        d.get_channel_delay("A", "B")


def test_get_channel_phase_raises_when_too_few_edges():
    d = PicoScope.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_channel_enabled("B", True)
    d.set_timebase(sample_interval_s=5e-6, num_samples=5)
    d.capture_block()
    with pytest.raises(PicoScopeValidationError, match="could not be determined"):
        d.get_channel_phase("A", "B")


def test_channel_delay_should_be_within_passes_inside_range(three_channel_driver):
    value = three_channel_driver.channel_delay_should_be_within(
        "A", "B", _PERIOD_S / 4 - 1e-5, _PERIOD_S / 4 + 1e-5
    )
    assert value == pytest.approx(_PERIOD_S / 4, rel=0.02)


def test_channel_delay_should_be_within_fails_outside_range(three_channel_driver):
    with pytest.raises(AssertionError):
        three_channel_driver.channel_delay_should_be_within("A", "B", 0.0, 1e-9)


def test_channel_delay_should_be_within_rejects_inverted_range(three_channel_driver):
    with pytest.raises(PicoScopeValidationError):
        three_channel_driver.channel_delay_should_be_within("A", "B", 1.0, 0.0)


def test_channel_phase_should_be_within_passes_inside_range(three_channel_driver):
    value = three_channel_driver.channel_phase_should_be_within("A", "B", 85.0, 95.0)
    assert value == pytest.approx(90.0, abs=2.0)


def test_channel_phase_should_be_within_fails_outside_range(three_channel_driver):
    with pytest.raises(AssertionError):
        three_channel_driver.channel_phase_should_be_within("A", "B", 0.0, 10.0)


def test_delay_scales_with_range_independent_amplitude():
    """A and B on very different ranges (5 V vs 50 mV) must not distort the delay —
    each channel gets its own mid-reference level, not a shared one."""

    d = PicoScope.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_channel_range("A", 5.0)
    d.set_channel_enabled("B", True)
    d.set_channel_range("B", 0.05)
    d.set_timebase(sample_interval_s=5e-6, num_samples=4000)
    d.capture_block()
    delay = d.get_channel_delay("A", "B")
    assert delay == pytest.approx(_PERIOD_S / 4, rel=0.02)
