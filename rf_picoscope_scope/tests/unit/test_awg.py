"""Built-in AWG (signal generator) control and per-model capability gating."""

from __future__ import annotations

import pytest

from picoscope_scope.driver import PicoScope
from picoscope_scope.exceptions import PicoScopeDeviceError, PicoScopeValidationError
from picoscope_scope.simulator import SimulatedBus


@pytest.fixture
def driver():
    d = PicoScope.connect_simulated()  # default simulated model is AWG-capable (2208B)
    yield d
    d.close()


def test_awg_is_disabled_by_default(driver):
    settings = driver.get_awg_settings()
    assert settings.enabled is False


def test_set_awg_waveform_round_trips(driver):
    driver.set_awg_waveform("sine", frequency_hz=1000.0, peak_to_peak_v=2.0, offset_v=0.1)
    settings = driver.get_awg_settings()
    assert settings.enabled is True
    assert settings.wave_type == "SINE"
    assert settings.frequency_hz == 1000.0
    assert settings.peak_to_peak_v == 2.0
    assert settings.offset_v == 0.1


def test_set_awg_waveform_pushes_microvolt_units_to_backend(driver):
    driver.set_awg_waveform("square", frequency_hz=500.0, peak_to_peak_v=3.3, offset_v=0.5)
    raw = driver.backend.awg
    assert raw["pk_to_pk_uv"] == 3_300_000
    assert raw["offset_uv"] == 500_000
    assert raw["frequency_hz"] == 500.0


def test_stop_awg_disables(driver):
    driver.set_awg_waveform("sine", frequency_hz=1000.0, peak_to_peak_v=1.0)
    driver.stop_awg()
    settings = driver.get_awg_settings()
    assert settings.enabled is False


def test_set_awg_waveform_rejects_invalid_wave_type(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_awg_waveform("hexagon", frequency_hz=1000.0, peak_to_peak_v=1.0)


def test_set_awg_waveform_rejects_non_positive_frequency(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_awg_waveform("sine", frequency_hz=0.0, peak_to_peak_v=1.0)


def test_set_awg_waveform_rejects_non_positive_amplitude(driver):
    with pytest.raises(PicoScopeValidationError):
        driver.set_awg_waveform("sine", frequency_hz=1000.0, peak_to_peak_v=0.0)


def test_set_awg_waveform_raises_on_a_non_awg_capable_model():
    bus = SimulatedBus(devices={"SIM/2204": "2204"})  # not in the AWG-capable list
    driver = PicoScope.connect_simulated(bus=bus)
    with pytest.raises(PicoScopeDeviceError, match="no built-in AWG"):
        driver.set_awg_waveform("sine", frequency_hz=1000.0, peak_to_peak_v=1.0)


def test_stop_awg_raises_on_a_non_awg_capable_model():
    bus = SimulatedBus(devices={"SIM/2204": "2204"})
    driver = PicoScope.connect_simulated(bus=bus)
    with pytest.raises(PicoScopeDeviceError, match="no built-in AWG"):
        driver.stop_awg()


def test_awg_capable_models_are_recognized():
    for model in ("2205A MSO", "2206B", "2206 MSO", "2207B", "2208B", "2208 MSO", "2405A"):
        bus = SimulatedBus(devices={"SIM/x": model})
        driver = PicoScope.connect_simulated(bus=bus)
        driver.set_awg_waveform("sine", frequency_hz=1000.0, peak_to_peak_v=1.0)  # must not raise
        driver.close()
