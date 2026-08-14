"""Robot Framework adapter layer: connection lifecycle, multi-alias sessions,
and an end-to-end keyword-level smoke flow proving the wiring to the core
driver is correct (exercised as plain Python calls — no Robot Framework
install required, matching how the core driver's own decorator machinery
falls back when ``robot`` isn't importable).
"""

from __future__ import annotations

import pytest

from picoscope_scope.exceptions import PicoScopeConnectionError, PicoScopeValidationError
from rf_picoscope_scope.library import PicoScopeLibrary


@pytest.fixture
def lib():
    library = PicoScopeLibrary()
    yield library
    library._end_suite(None, {})


def test_connect_returns_rfds_002_connection_state_shape(lib):
    state = lib.connect(simulated=True)
    assert set(state) == {
        "alias",
        "resource",
        "connected",
        "communication_ok",
        "transport",
        "identity",
        "timeout_s",
        "state",
    }
    assert state["alias"] == "default"
    assert state["connected"] is True
    assert state["communication_ok"] is True
    assert state["state"] == "connected"


def test_connect_is_idempotent_for_the_same_alias_and_resource(lib):
    first = lib.connect(simulated=True, alias="a")
    second = lib.connect(simulated=True, alias="a")
    assert first["resource"] == second["resource"]


def test_disconnect_is_idempotent(lib):
    lib.connect(simulated=True)
    lib.disconnect()
    lib.disconnect()  # must not raise
    assert lib.is_connected() is False


def test_get_connection_state_when_never_connected(lib):
    state = lib.get_connection_state(alias="nope")
    assert state["connected"] is False
    assert state["state"] == "disconnected"


def test_operations_without_connect_raise(lib):
    with pytest.raises(PicoScopeConnectionError):
        lib.get_channel_enabled("A")


def test_multi_alias_sessions_are_independent(lib):
    lib.connect(simulated=True, alias="scope1")
    lib.connect(simulated=True, alias="scope2")
    lib.set_channel_enabled("B", True, alias="scope1")
    assert lib.get_channel_enabled("B", alias="scope1") is True
    assert lib.get_channel_enabled("B", alias="scope2") is False


def test_switch_and_get_active_oscilloscope(lib):
    lib.connect(simulated=True, alias="scope1")
    lib.connect(simulated=True, alias="scope2")
    assert lib.get_active_oscilloscope() == "scope2"
    lib.switch_oscilloscope("scope1")
    assert lib.get_active_oscilloscope() == "scope1"
    assert lib.get_channel_enabled("A") is True  # implicitly targets scope1


def test_list_oscilloscope_connections(lib):
    lib.connect(simulated=True, alias="scope1")
    lib.connect(simulated=True, alias="scope2")
    assert lib.list_oscilloscope_connections() == ["scope1", "scope2"]


def test_find_devices_via_simulated_session(lib):
    lib.connect(simulated=True, alias="scope1")
    assert lib.find_devices(alias="scope1") == ["SIM/00001"]


def test_find_devices_without_a_session_probes_a_fresh_simulator(lib):
    assert lib.find_devices(simulated=True) == ["SIM/00001"]


def test_connect_with_a_specific_series(lib):
    state = lib.connect(simulated=True, series="3000A", alias="scope3000")
    assert state["connected"] is True
    assert "3405D MSO" in state["identity"]
    lib.set_channel_enabled("A", True, alias="scope3000")
    lib.set_awg_waveform("sine", frequency_hz=1000.0, peak_to_peak_v=1.0, alias="scope3000")
    awg = lib.get_awg_settings(alias="scope3000")
    assert awg["enabled"] is True


def test_find_devices_for_a_specific_series(lib):
    assert lib.find_devices(series="3000A", simulated=True) == ["SIM/00001"]


def test_unknown_alias_raises_with_known_aliases_listed(lib):
    lib.connect(simulated=True, alias="scope1")
    with pytest.raises(PicoScopeConnectionError, match="scope1"):
        lib.get_channel_enabled("A", alias="does-not-exist")


def test_end_to_end_capture_csv_awg_preset_flow(lib, tmp_path):
    lib.connect(simulated=True)
    lib.set_channel_enabled("A", True)
    lib.set_channel_range("A", 5.0)
    lib.set_channel_probe("A", "current", scale=10.0)
    lib.set_trigger("A", threshold_v=0.5, direction="RISING")
    lib.set_timebase(sample_interval_s=20e-6, num_samples=200)
    summary = lib.capture_block()
    assert summary["channels"] == ["A"]

    waveform = lib.get_waveform("A")
    assert waveform["unit"] == "A"
    assert len(waveform["values"]) == 200

    all_waveforms = lib.get_all_waveforms()
    assert set(all_waveforms) == {"A"}

    csv_path = tmp_path / "a.csv"
    lib.save_waveform_to_csv(str(csv_path), "A")
    assert csv_path.exists()

    combined_csv_path = tmp_path / "all.csv"
    lib.save_all_waveforms_to_csv(str(combined_csv_path))
    assert combined_csv_path.exists()

    measurements = lib.get_measurements("A")
    assert measurements["unit"] == "A"
    frequency = lib.get_measurement("A", "FREQUENCY")
    lib.measurement_should_be_within("A", "FREQUENCY", frequency - 50, frequency + 50)

    lib.set_awg_waveform("sine", frequency_hz=1000.0, peak_to_peak_v=1.0)
    awg = lib.get_awg_settings()
    assert awg["enabled"] is True

    preset_path = tmp_path / "preset.json"
    lib.save_preset(str(preset_path))
    assert preset_path.exists()

    lib.connect(simulated=True, alias="fresh")
    lib.load_preset(str(preset_path), alias="fresh")
    assert lib.get_channel_settings("A", alias="fresh")["probe_type"] == "CURRENT"


def test_channel_delay_and_phase_keywords(lib):
    lib.connect(simulated=True)
    lib.set_channel_enabled("A", True)
    lib.set_channel_enabled("B", True)
    lib.set_timebase(sample_interval_s=5e-6, num_samples=4000)
    lib.capture_block()

    delay = lib.get_channel_delay("A", "B")
    assert delay > 0  # B lags A in the simulator

    phase = lib.get_channel_phase("A", "B")
    assert phase == pytest.approx(90.0, abs=2.0)

    lib.channel_delay_should_be_within("A", "B", delay - 1e-6, delay + 1e-6)
    lib.channel_phase_should_be_within("A", "B", 85.0, 95.0)


def test_export_diagnostic_bundle_without_any_session(lib):
    bundle = lib.export_diagnostic_bundle()
    assert bundle is not None


def test_get_identity_and_check_communication(lib):
    lib.connect(simulated=True)
    assert lib.check_communication() is True
    identity = lib.get_identity()
    assert "Pico Technology" in identity


def test_validation_error_propagates_through_keywords(lib):
    lib.connect(simulated=True)
    with pytest.raises(PicoScopeValidationError):
        lib.set_channel_coupling("A", "bogus")
