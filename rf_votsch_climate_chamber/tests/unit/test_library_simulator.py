from __future__ import annotations
import json
from pathlib import Path
import pytest
from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
from rf_votsch_climate_chamber.exceptions import DriverLimitViolationError, DriverStateError

@pytest.fixture
def lib(tmp_path):
    item=VotschClimateChamberLibrary(default_resource="SIM::pytest", managed_configuration_root=str(tmp_path/"profiles"))
    yield item
    try: item.disconnect_all()
    except Exception: pass


def test_constructor_does_not_connect(lib):
    assert lib.is_connected() is False
    assert lib.get_active_connection() is None


def test_universal_lifecycle(lib):
    state=lib.connect()
    assert state["connected"] is True
    assert lib.is_connected() is True
    assert lib.check_communication() is True
    assert "SIM-2604" in lib.get_identity(refresh=True)
    assert lib.get_connection_state()["state"] == "connected"
    assert lib.get_communication_timeout() == 5.0
    assert lib.set_communication_timeout(2.5) == 2.5
    assert lib.get_communication_timeout() == 2.5
    lib.disconnect()
    assert lib.is_connected() is False
    lib.disconnect()


def test_temperature_and_operation(lib):
    lib.connect()
    assert lib.measure_temperature() == 25.0
    lib.set_temperature(35)
    assert lib.get_temperature_setpoint() == 35.0
    lib.start_chamber()
    assert lib.get_chamber_running_state() is True
    result=lib.wait_for_temperature_stability(35, stable_samples=1, poll_interval_s=0.001, settle_timeout_s=1)
    assert result == 35.0
    lib.stop_chamber()
    assert lib.get_chamber_running_state() is False


def test_local_limits_reject_before_transport(lib):
    lib.connect()
    with pytest.raises(DriverLimitViolationError):
        lib.set_temperature(999)
    limits=lib.set_temperature_limits(-20, 100)
    assert limits["min"] == -20
    with pytest.raises(DriverLimitViolationError):
        lib.set_temperature(-21)


def test_gradients_and_outputs(lib):
    lib.connect()
    lib.set_heating_gradient(3.0)
    lib.set_cooling_gradient(2.5)
    assert lib.get_heating_gradient() == 3.0
    assert lib.get_cooling_gradient() == 2.5
    lib.set_dryer(True); assert lib.get_dryer() is True
    lib.set_compressed_air(True); assert lib.get_compressed_air() is True
    result=lib.safe_shutdown()
    assert result["safe"] is True
    assert lib.get_dryer() is False
    assert lib.get_compressed_air() is False


def test_multi_connection(lib):
    lib.connect("SIM::one", alias="one")
    lib.connect("SIM::two", alias="two")
    assert len(lib.list_connections()) == 2
    assert lib.select_connection("one")["alias"] == "one"
    assert lib.get_active_connection() == "one"
    lib.disconnect_all()
    assert lib.list_connections() == []


def test_reconnect_and_diagnostics(lib, tmp_path):
    lib.connect()
    state=lib.reconnect()
    assert state["connected"] is True
    data=lib.get_diagnostics()
    assert data["schema_version"]
    out=lib.export_diagnostics(str(tmp_path/"diag.json"))
    assert Path(out["path"]).exists()
    assert json.loads(Path(out["path"]).read_text())["schema_version"]


def test_assertions(lib):
    lib.connect()
    lib.temperature_should_be(25)
    lib.temperature_should_be_within(20,30)
    lib.temperature_setpoint_should_be(25)
    lib.chamber_should_be_stopped()
    with pytest.raises(AssertionError): lib.chamber_should_be_running()


def test_not_connected_state_error(lib):
    with pytest.raises(DriverStateError):
        lib.measure_temperature()
