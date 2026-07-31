from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from bk8500b import BK8500B
from BK8500BLibrary import BK8500BLibrary, BK8500BRobotError
from tests.fakes import FakeSCPITransport


def make_library() -> BK8500BLibrary:
    library = BK8500BLibrary()

    def factory(config):
        return BK8500B(
            replace(config, minimum_command_interval_s=0),
            transport=FakeSCPITransport(),
        )

    library._device_factory = factory
    return library


def connected_library(**kwargs) -> BK8500BLibrary:
    library = make_library()
    library.connect_to_electronic_load("FAKE", **kwargs)
    return library


def test_connect_identity_sessions_and_disconnect() -> None:
    library = make_library()
    identity = library.connect_to_electronic_load("FAKE", alias="load_a")
    assert identity["model"] == "BK8500B"
    assert identity["alias"] == "load_a"
    assert library.get_active_electronic_load() == "load_a"
    assert library.list_electronic_load_sessions()[0]["connected"] is True
    library.electronic_load_should_be_connected()
    library.disconnect_electronic_load()
    assert library.get_active_electronic_load() is None


def test_duplicate_alias_is_rejected() -> None:
    library = connected_library()
    with pytest.raises(BK8500BRobotError, match="already exists"):
        library.connect_to_electronic_load("FAKE")
    library.disconnect_all_electronic_loads()


def test_multiple_sessions_and_switch() -> None:
    library = make_library()
    library.connect_to_electronic_load("FAKE1", alias="one")
    library.connect_to_electronic_load("FAKE2", alias="two")
    assert library.get_active_electronic_load() == "two"
    assert library.switch_electronic_load("one") == "one"
    assert len(library.list_electronic_load_sessions()) == 2
    library.disconnect_all_electronic_loads()


def test_setpoints_modes_and_safe_enable() -> None:
    library = connected_library(require_enable_token=True)
    assert library.set_electronic_load_mode("CC") == "CURRent"
    result = library.set_current_setpoint(1.0)
    assert result["verified"] is True
    assert result["applied"] == 1.0
    enabled = library.configure_and_enable_load(
        "CC", 1.0, current_limit=1.2, power_limit=20, remote_sense=False
    )
    assert enabled["input_enabled"] is True
    library.electronic_load_input_should_be_on()
    library.disable_electronic_load_input()
    library.electronic_load_input_should_be_off()
    library.disconnect_all_electronic_loads()


def test_measurements_assertions_and_wait() -> None:
    library = connected_library()
    assert library.measure_voltage() == 12.0
    assert library.measure_current() == 1.0
    assert library.measure_power() == 12.0
    library.voltage_should_be_within_range(11.9, 12.1)
    library.current_should_be_within_range(0.9, 1.1)
    library.power_should_be_within_range(11.0, 13.0)
    assert library.wait_until_measurement_is_within_range("voltage", 11, 13) == 12.0
    with pytest.raises(AssertionError, match="outside"):
        library.measurement_should_be_within_range(5, 0, 4)
    with pytest.raises(AssertionError, match="did not enter"):
        library.wait_until_measurement_is_within_range(
            "current", 2, 3, timeout=0.01, interval=0.001
        )
    library.disconnect_all_electronic_loads()


def test_snapshot_status_diagnostics_and_errors() -> None:
    library = connected_library()
    snapshot = library.get_measurement_snapshot()
    assert snapshot["voltage"]["value"] == 12.0
    assert snapshot["status"]["input_enabled"] is False
    health = library.run_electronic_load_health_check()
    assert health["healthy"] is True
    diagnostic = library.get_electronic_load_diagnostic_snapshot()
    assert diagnostic["connected"] is True
    assert library.drain_electronic_load_error_queue() == []
    assert library.run_electronic_load_self_test()["passed"] is True
    library.disconnect_all_electronic_loads()


def test_csv_and_json_export(tmp_path: Path) -> None:
    library = connected_library()
    csv_path = library.log_measurements_to_csv(
        str(tmp_path / "logs" / "measurements.csv"), samples=2, interval=0
    )
    text = Path(csv_path).read_text(encoding="utf-8")
    assert "voltage_v" in text
    assert len(text.strip().splitlines()) == 3
    json_path = library.export_diagnostic_snapshot(str(tmp_path / "diagnostic.json"))
    assert '"connected": true' in Path(json_path).read_text(encoding="utf-8")
    library.disconnect_all_electronic_loads()


def test_transient_peak_state_and_raw_scpi() -> None:
    library = connected_library()
    library.configure_transient_load(1, 0.1, 0.2, 0.2, 2, mode="continuous")
    config = library.get_transient_load_configuration()
    assert config["high_level"] == 1.0
    library.enable_peak_capture()
    peaks = library.read_peak_measurements()
    assert peaks["voltage_maximum_v"] == 12.2
    library.clear_peak_capture()
    library.save_electronic_load_state(1)
    library.recall_electronic_load_state(1)
    assert library.query_raw_scpi("SYSTem:VERSion?") == "1999.0"
    library.write_raw_scpi("*CLS")
    library.disconnect_all_electronic_loads()


def test_short_circuit_requires_policy_and_confirmation() -> None:
    library = connected_library(allow_short=True)
    with pytest.raises(BK8500BRobotError, match="confirmation"):
        library.set_short_circuit_mode(True)
    library.set_short_circuit_mode(True, confirmation="I UNDERSTAND")
    library.set_short_circuit_mode(False)
    library.disconnect_all_electronic_loads()


def test_invalid_mode_and_unknown_alias_are_clear() -> None:
    library = connected_library()
    with pytest.raises(ValueError, match="Unknown operating mode"):
        library.set_electronic_load_mode("banana")
    with pytest.raises(BK8500BRobotError, match="Unknown electronic load alias"):
        library.measure_voltage(alias="missing")
    library.disconnect_all_electronic_loads()


def test_connection_validation_and_default_port() -> None:
    library = make_library()
    with pytest.raises(ValueError, match="port is required"):
        library.connect_to_electronic_load()
    with pytest.raises(ValueError, match="alias must not be empty"):
        library.connect_to_electronic_load("FAKE", alias=" ")
    with pytest.raises(ValueError, match="protocol must be"):
        library.connect_to_electronic_load("FAKE", protocol="unknown")

    library = BK8500BLibrary(default_port="FAKE")

    def factory(config):
        return BK8500B(
            replace(config, minimum_command_interval_s=0),
            transport=FakeSCPITransport(),
        )

    library._device_factory = factory
    assert library.connect_to_electronic_load()["port"] == "FAKE"
    library.disconnect_all_electronic_loads()


def test_reconnect_synchronize_capabilities_and_status() -> None:
    library = connected_library(reconnect=True)
    library.reconnect_electronic_load()
    synced = library.synchronize_electronic_load_state()
    assert synced["synchronized"] is True
    capabilities = library.get_electronic_load_capabilities(refresh=True)
    assert capabilities["maximum_current_a"] > 0
    status = library.get_electronic_load_status()
    assert status["input_enabled"] is False
    assert library.get_electronic_load_mode() == "CURRent"
    library.clear_electronic_load_status()
    assert library.drain_electronic_load_error_queue(maximum=1) == []
    library.disconnect_all_electronic_loads()


def test_all_fixed_mode_configuration_wrappers() -> None:
    library = connected_library()
    assert library.set_voltage_setpoint(10)["applied"] == 10
    assert library.get_voltage_setpoint() == 10
    assert library.set_power_setpoint(20)["applied"] == 20
    assert library.get_power_setpoint() == 20
    assert library.set_resistance_setpoint(100)["applied"] == 100
    assert library.get_resistance_setpoint() == 100

    assert library.set_current_protection(2)["verified"] is True
    assert library.get_current_protection() == 2
    assert library.set_power_protection(30)["verified"] is True
    assert library.get_power_protection() == 30

    library.set_remote_sense(True)
    assert library.get_remote_sense() is True
    assert library.set_current_range(5)["applied"] == 5
    assert library.get_current_range() == 5
    assert library.set_voltage_range(50)["applied"] == 50
    assert library.get_voltage_range() == 50
    library.set_voltage_autorange(False)
    assert library.get_voltage_autorange() is False

    both = library.set_current_slew_rate(2)
    assert both["applied"] == 2
    split = library.set_current_slew_rate(3, 4)
    assert split["rise"]["applied"] == 3
    assert split["fall"]["applied"] == 4
    slew = library.get_current_slew_rate()
    assert slew == {"rise_a_per_us": 3.0, "fall_a_per_us": 4.0}

    thresholds = library.set_load_voltage_thresholds(2, 1)
    assert thresholds["on"]["applied"] == 2
    assert thresholds["off"]["applied"] == 1
    library.clear_electronic_load_protection()
    library.disconnect_all_electronic_loads()


def test_input_assertion_failures_and_enable_keyword() -> None:
    library = connected_library(require_enable_token=True)
    with pytest.raises(AssertionError, match="OFF"):
        library.electronic_load_input_should_be_on()
    library.enable_electronic_load_input()
    with pytest.raises(AssertionError, match="ON"):
        library.electronic_load_input_should_be_off()
    library.disable_electronic_load_input()
    library.disconnect_all_electronic_loads()


def test_measure_resistance_and_validation_errors(tmp_path: Path) -> None:
    library = connected_library()
    assert library.measure_resistance() == 12.0
    with pytest.raises(ValueError, match="minimum"):
        library.measurement_should_be_within_range(1, 2, 1)
    with pytest.raises(ValueError, match="measurement must be"):
        library.wait_until_measurement_is_within_range("temperature", 0, 1)
    with pytest.raises(ValueError, match="timeout and interval"):
        library.wait_until_measurement_is_within_range("voltage", 0, 1, timeout=0)
    with pytest.raises(ValueError, match="samples"):
        library.log_measurements_to_csv(str(tmp_path / "bad.csv"), samples=0)
    with pytest.raises(ValueError, match="interval"):
        library.log_measurements_to_csv(str(tmp_path / "bad.csv"), interval=-1)
    output = library.log_measurements_to_csv(
        str(tmp_path / "resistance.csv"), samples=1, interval=0, include_resistance=True
    )
    assert "resistance_ohm" in Path(output).read_text(encoding="utf-8")
    library.disconnect_all_electronic_loads()


def test_dynamic_trigger_reset_and_control_modes() -> None:
    library = connected_library()
    with pytest.raises(ValueError, match="Dynamic mode"):
        library.configure_transient_load(1, 1, 0, 1, 1, mode="invalid")
    library.configure_transient_load(1, 0.1, 0.2, 0.2, 2, mode="pulse")
    assert library.get_transient_load_configuration()["mode"] == "PULSe"
    library.trigger_electronic_load()
    library.set_electronic_load_remote()
    library.set_electronic_load_remote(local_lockout=True)
    library.set_electronic_load_local()
    library.reset_electronic_load()
    assert library.get_electronic_load_status()["input_enabled"] is False
    library.disconnect_all_electronic_loads()


def test_timeout_arguments_and_driver_error_translation() -> None:
    library = connected_library()
    assert library.run_electronic_load_self_test(timeout=1)["passed"] is True
    with pytest.raises(BK8500BRobotError, match="InstrumentRangeError"):
        library.set_current_setpoint(10_000)
    assert library.query_raw_scpi("SYSTem:VERSion?", timeout=1) == "1999.0"
    library.synchronize_electronic_load_state()
    library.write_raw_scpi("*CLS", timeout=1)
    library.synchronize_electronic_load_state()
    library.disconnect_all_electronic_loads()


def test_cleanup_listener_and_unknown_session_state() -> None:
    library = connected_library()
    library._end_suite(None, None)
    assert library.list_electronic_load_sessions() == []
    with pytest.raises(BK8500BRobotError, match="No active electronic load"):
        library.measure_voltage()


def test_conversion_helpers() -> None:
    from datetime import datetime, timezone
    from enum import Enum, IntFlag

    from BK8500BLibrary.conversion import as_bool, as_float, as_int, to_robot

    assert as_bool("YES") is True
    assert as_bool("disabled") is False
    assert as_bool(1) is True
    with pytest.raises(ValueError, match="boolean"):
        as_bool("perhaps")
    assert as_float("1.25") == 1.25
    with pytest.raises(ValueError, match="numeric"):
        as_float("abc")
    assert as_int("2.0") == 2
    with pytest.raises(ValueError, match="integer"):
        as_int("2.5")

    class SampleEnum(Enum):
        ITEM = "item"

    class SampleFlag(IntFlag):
        A = 1

    converted = to_robot(
        {
            "enum": SampleEnum.ITEM,
            "flag": SampleFlag.A,
            "time": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "bytes": b"\x01\x02",
            "path": Path("demo"),
            "items": (SampleEnum.ITEM,),
        }
    )
    assert converted["enum"] == "item"
    assert converted["flag"] == 1
    assert converted["bytes"] == "0102"
    assert converted["items"] == ["item"]
