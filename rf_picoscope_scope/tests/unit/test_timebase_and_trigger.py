"""Timebase (main time) resolution and simple-edge trigger configuration."""

from __future__ import annotations

import pytest

from picoscope_scope.driver import PicoScope
from picoscope_scope.exceptions import PicoScopeValidationError


@pytest.fixture
def driver():
    d = PicoScope.connect_simulated()
    yield d
    d.close()


# ----------------------------------------------------------------------
# Timebase
# ----------------------------------------------------------------------
def test_set_timebase_resolves_a_supported_interval_at_least_as_slow_as_requested(driver):
    settings = driver.set_timebase(sample_interval_s=1e-6, num_samples=1000)
    assert settings.sample_interval_s >= 1e-6
    assert settings.num_samples == 1000
    assert settings.timebase_index >= 0
    assert settings.pre_trigger_ratio == 0.0


def test_set_timebase_picks_the_fastest_index_that_still_satisfies_the_request(driver):
    # Exactly the fastest ("timebase 0") interval the simulator's formula gives: 1 ns.
    settings = driver.set_timebase(sample_interval_s=1e-9, num_samples=10)
    assert settings.timebase_index == 0
    assert settings.sample_interval_s == pytest.approx(1e-9)


def test_get_timebase_settings_returns_last_configured_value(driver):
    driver.set_timebase(sample_interval_s=1e-6, num_samples=500)
    settings = driver.get_timebase_settings()
    assert settings.num_samples == 500


def test_get_timebase_settings_before_configuration_raises(driver):
    with pytest.raises(PicoScopeValidationError, match="has not been configured"):
        driver.get_timebase_settings()


def test_set_timebase_rejects_non_positive_interval(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_timebase(sample_interval_s=0.0, num_samples=100)
    with pytest.raises(PicoScopeValidationError):
        driver.set_timebase(sample_interval_s=-1e-6, num_samples=100)


def test_set_timebase_rejects_non_positive_num_samples(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_timebase(sample_interval_s=1e-6, num_samples=0)


def test_set_timebase_rejects_out_of_range_pre_trigger_ratio(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_timebase(sample_interval_s=1e-6, num_samples=100, pre_trigger_ratio=1.5)
    with pytest.raises(PicoScopeValidationError):
        driver.set_timebase(sample_interval_s=1e-6, num_samples=100, pre_trigger_ratio=-0.1)


def test_set_timebase_rejects_num_samples_exceeding_memory(driver):
    with pytest.raises(PicoScopeValidationError, match="supports at most"):
        driver.set_timebase(sample_interval_s=1e-6, num_samples=10_000_000)


# ----------------------------------------------------------------------
# Trigger
# ----------------------------------------------------------------------
def test_trigger_is_disabled_by_default(driver):
    settings = driver.get_trigger_settings()
    assert settings.enabled is False
    assert settings.channel is None


def test_set_trigger_round_trips(driver):
    driver.set_trigger("A", threshold_v=1.0, direction="rising", delay_samples=5, auto_trigger_ms=100)
    settings = driver.get_trigger_settings()
    assert settings.enabled is True
    assert settings.channel == "A"
    assert settings.threshold_v == 1.0
    assert settings.direction == "RISING"
    assert settings.delay_samples == 5
    assert settings.auto_trigger_ms == 100


def test_set_trigger_pushes_adc_threshold_scaled_by_channel_range(driver):
    driver.set_channel_range("A", 5.0)
    driver.set_trigger("A", threshold_v=2.5)  # half of the 5 V range
    raw = driver.backend.trigger
    assert raw["enabled"] is True
    assert raw["channel"] == "A"
    assert raw["threshold_adc"] == pytest.approx(driver.backend.maximum_adc_value() // 2, abs=2)


def test_set_trigger_clamps_threshold_within_adc_range(driver):
    driver.set_channel_range("A", 1.0)
    driver.set_trigger("A", threshold_v=100.0)  # way outside the 1 V range
    raw = driver.backend.trigger
    assert raw["threshold_adc"] == driver.backend.maximum_adc_value()


def test_disable_trigger_clears_settings(driver):
    driver.set_trigger("A", threshold_v=1.0)
    driver.disable_trigger()
    settings = driver.get_trigger_settings()
    assert settings.enabled is False
    assert driver.backend.trigger["enabled"] is False


def test_set_trigger_rejects_invalid_direction(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_trigger("A", threshold_v=1.0, direction="sideways")


def test_set_trigger_rejects_negative_delay_or_auto_trigger(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_trigger("A", threshold_v=1.0, delay_samples=-1)
    with pytest.raises(PicoScopeValidationError):
        driver.set_trigger("A", threshold_v=1.0, auto_trigger_ms=-1)


def test_set_trigger_rejects_unknown_channel(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_trigger("Z", threshold_v=1.0)
