from __future__ import annotations

from dataclasses import dataclass

import pytest

from rf_votsch_climate_chamber.core import ClimateChamberCore
from rf_votsch_climate_chamber.exceptions import (
    DriverSafetyError,
    DriverUnsupportedOperationError,
)
from rf_votsch_climate_chamber.library import VotschClimateChamberLibrary
from rf_votsch_climate_chamber.transports.simulator import SimulatorTransport


@dataclass
class FakeClock:
    now: float = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def _connected_core(*, clock: FakeClock | None = None, **kwargs):
    clock = clock or FakeClock()
    core = ClimateChamberCore(
        SimulatorTransport("regression"),
        sleep=clock.sleep,
        monotonic=clock.monotonic,
        **kwargs,
    )
    core.connect()
    return core, clock


def test_setpoint_verification_polls_until_delayed_readback(monkeypatch) -> None:
    core, _ = _connected_core(
        setpoint_verify_timeout_s=2.0,
        setpoint_verify_poll_interval_s=0.1,
    )
    readings = iter([15.0, 15.0, 25.0])
    monkeypatch.setattr(core, "get_temperature_setpoint_c", lambda: next(readings))

    core.set_temperature_c(25.0)


def test_setpoint_verification_timeout_contains_actionable_evidence(monkeypatch) -> None:
    core, _ = _connected_core(
        setpoint_verify_timeout_s=0.3,
        setpoint_verify_poll_interval_s=0.1,
    )
    monkeypatch.setattr(core, "get_temperature_setpoint_c", lambda: 15.0)

    with pytest.raises(DriverSafetyError) as captured:
        core.set_temperature_c(25.0)

    error = captured.value
    assert error.details["requested_c"] == 25.0
    assert error.details["reported_c"] == 15.0
    assert error.details["verification_attempts"] >= 3
    assert "local-control mode" in (error.recovery_action or "")


def test_auxiliary_outputs_are_disabled_by_default_on_unqualified_hardware_profile() -> None:
    core, _ = _connected_core()

    with pytest.raises(DriverUnsupportedOperationError):
        core.get_dryer()
    with pytest.raises(DriverUnsupportedOperationError):
        core.set_compressed_air(False)


def test_safe_shutdown_skips_unconfigured_auxiliary_outputs_and_stops_chamber() -> None:
    core, _ = _connected_core()
    core.start()

    result = core.safe_shutdown()

    assert result["safe"] is True
    by_action = {item["action"]: item for item in result["actions"]}
    assert by_action["dryer_off"]["status"] == "SKIP"
    assert by_action["compressed_air_off"]["status"] == "SKIP"
    assert by_action["chamber_stop"]["status"] == "PASS"
    assert core.get_running() is False


def test_configured_auxiliary_outputs_remain_supported() -> None:
    core, _ = _connected_core(dryer_output_channel=8, compressed_air_output_channel=7)
    core.set_dryer(True)
    core.set_compressed_air(True)
    assert core.get_dryer() is True
    assert core.get_compressed_air() is True

    result = core.safe_shutdown()
    assert result["safe"] is True
    assert core.get_dryer() is False
    assert core.get_compressed_air() is False


def test_get_configuration_can_be_modified_and_reimported(tmp_path) -> None:
    lib = VotschClimateChamberLibrary(
        default_resource="SIM::configuration-roundtrip",
        managed_configuration_root=str(tmp_path / "profiles"),
    )
    configuration = lib.get_driver_configuration()
    configuration["settings"]["safety"]["safe_shutdown_on_disconnect"] = False

    result = lib.import_driver_configuration(configuration, apply=True)

    assert result["valid"] is True
    assert result["applied"] is True
    assert any("runtime annotations" in item["message"] for item in result["warnings"])
    assert (
        lib.get_driver_configuration()["settings"]["safety"]["safe_shutdown_on_disconnect"]
        is False
    )


def test_disconnect_respects_round_tripped_close_only_policy(tmp_path) -> None:
    lib = VotschClimateChamberLibrary(
        default_resource="SIM::close-only",
        managed_configuration_root=str(tmp_path / "profiles"),
    )
    configuration = lib.get_driver_configuration()
    configuration["settings"]["safety"]["safe_shutdown_on_disconnect"] = False
    result = lib.import_driver_configuration(configuration, apply=True)
    assert result["applied"] is True

    lib.connect()
    handle = lib._registry.get()  # Intentional white-box regression check.
    simulator = handle.core.transport
    lib.start_chamber()
    assert simulator.simulator_state.running is True

    lib.disconnect()

    # Close-only disconnect must not silently change the chamber's functional state.
    assert simulator.simulator_state.running is True
