"""Per-channel configuration and the current/voltage probe abstraction."""

from __future__ import annotations

import pytest

from picoscope_scope.driver import PicoScope
from picoscope_scope.exceptions import PicoScopeValidationError


@pytest.fixture
def driver():
    d = PicoScope.connect_simulated()
    yield d
    d.close()


def test_channel_a_is_enabled_by_default_others_are_not(driver):
    assert driver.get_channel_enabled("A") is True
    assert driver.get_channel_enabled("B") is False
    assert driver.get_channel_enabled("C") is False
    assert driver.get_channel_enabled("D") is False
    assert driver.get_enabled_channels() == ["A"]


def test_defaults_are_pushed_to_the_backend_at_connect():
    driver = PicoScope.connect_simulated()
    assert "A" in driver.backend.channels
    assert driver.backend.channels["A"]["enabled"] is True
    assert driver.backend.channels["B"]["enabled"] is False


def test_set_channel_enabled_round_trips(driver):
    driver.set_channel_enabled("b", True)
    assert driver.get_channel_enabled("B") is True
    assert driver.backend.channels["B"]["enabled"] is True
    assert driver.get_enabled_channels() == ["A", "B"]


def test_set_channel_range_selects_nearest_supported_range(driver):
    actual = driver.set_channel_range("A", 3.0)
    assert actual == 5.0  # smallest range that still covers 3 V
    assert driver.get_channel_range("A") == 5.0

    actual2 = driver.set_channel_range("A", 0.09)
    assert actual2 == 0.1
    assert driver.get_channel_range("A") == 0.1


def test_set_channel_range_rejects_out_of_range_request(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_channel_range("A", 1000.0)


def test_set_channel_coupling_round_trips(driver):
    driver.set_channel_coupling("A", "ac")
    assert driver.get_channel_coupling("A") == "AC"
    driver.set_channel_coupling("A", "DC")
    assert driver.get_channel_coupling("A") == "DC"


def test_set_channel_coupling_rejects_invalid_value(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_channel_coupling("A", "invalid")


def test_set_channel_offset_round_trips(driver):
    driver.set_channel_offset("A", 0.25)
    assert driver.get_channel_offset("A") == 0.25


def test_channel_validation_rejects_unknown_channel(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.get_channel_enabled("E")
    with pytest.raises(PicoScopeValidationError):
        driver.set_channel_enabled("Z", True)


def test_channel_names_are_case_insensitive(driver):
    driver.set_channel_enabled("b", True)
    assert driver.get_channel_enabled("B") is True


def test_default_probe_is_voltage_with_unity_scale(driver):
    probe = driver.get_channel_probe("A")
    assert probe == {"probe_type": "VOLTAGE", "probe_scale": 1.0}


def test_set_channel_probe_configures_current_clamp(driver):
    driver.set_channel_probe("A", "current", scale=10.0)
    probe = driver.get_channel_probe("A")
    assert probe == {"probe_type": "CURRENT", "probe_scale": 10.0}


def test_set_channel_probe_rejects_invalid_type(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_channel_probe("A", "resistance")


def test_set_channel_probe_rejects_non_positive_scale(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_channel_probe("A", "voltage", scale=0.0)
    with pytest.raises(PicoScopeValidationError):
        driver.set_channel_probe("A", "voltage", scale=-1.0)


def test_get_channel_settings_reflects_all_fields(driver):
    driver.set_channel_enabled("A", True)
    driver.set_channel_range("A", 2.0)
    driver.set_channel_coupling("A", "AC")
    driver.set_channel_offset("A", 0.1)
    driver.set_channel_probe("A", "current", scale=5.0)

    settings = driver.get_channel_settings("A")
    assert settings.channel == "A"
    assert settings.enabled is True
    assert settings.range_v == 2.0
    assert settings.coupling == "AC"
    assert settings.offset_v == 0.1
    assert settings.probe_type == "CURRENT"
    assert settings.probe_scale == 5.0
