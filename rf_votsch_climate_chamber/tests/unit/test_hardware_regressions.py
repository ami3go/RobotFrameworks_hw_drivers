from __future__ import annotations

from dataclasses import dataclass

import pytest

from rf_votsch_climate_chamber.core import ClimateChamberCore
from rf_votsch_climate_chamber.exceptions import (
    DriverLimitViolationError,
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


def test_digital_output_verification_polls_until_delayed_readback(monkeypatch) -> None:
    """Same delayed-readback tolerance the setpoint path has: the SimServ ack for
    14001 can arrive before the 14003 readback register reflects it."""
    core, _ = _connected_core(
        dryer_output_channel=2,
        state_change_timeout_s=2.0,
        setpoint_verify_poll_interval_s=0.1,
    )
    readings = iter([False, False, True])
    monkeypatch.setattr(core, "_get_digital_output", lambda channel, operation: next(readings))

    core.set_dryer(True)


def test_digital_output_verification_timeout_contains_actionable_evidence(monkeypatch) -> None:
    core, _ = _connected_core(
        dryer_output_channel=2,
        state_change_timeout_s=0.3,
        setpoint_verify_poll_interval_s=0.1,
    )
    monkeypatch.setattr(core, "_get_digital_output", lambda channel, operation: False)

    with pytest.raises(DriverSafetyError) as captured:
        core.set_dryer(True)

    error = captured.value
    assert error.details["channel"] == 2
    assert error.details["requested"] is True
    assert error.details["reported"] is False
    assert error.details["verification_attempts"] >= 3
    assert "physical mapping" in (error.recovery_action or "")


@pytest.mark.parametrize("channel", [2, 3, 5, 7, 8, 12])
def test_simulator_models_whichever_auxiliary_channel_was_configured(channel: int) -> None:
    """The simulator used to hardcode channels 7/8: a write to any other channel
    was acknowledged but discarded, and the readback then reported 0 forever, so
    a SIM:: round trip failed for wiring the docs explicitly allow."""
    core, _ = _connected_core(dryer_output_channel=channel)

    core.set_dryer(True)
    assert core.get_dryer() is True
    core.set_dryer(False)
    assert core.get_dryer() is False


def test_fan_is_unsupported_until_its_channel_mapping_is_qualified() -> None:
    core, _ = _connected_core()

    with pytest.raises(DriverUnsupportedOperationError):
        core.get_fan()
    with pytest.raises(DriverUnsupportedOperationError):
        core.set_fan(True)


def test_fan_round_trips_on_its_configured_channel() -> None:
    core, _ = _connected_core(fan_output_channel=6)

    core.set_fan(True)
    assert core.get_fan() is True
    core.set_fan(False)
    assert core.get_fan() is False


def test_fan_is_independent_of_the_other_auxiliary_outputs() -> None:
    core, _ = _connected_core(
        fan_output_channel=6, dryer_output_channel=8, compressed_air_output_channel=7
    )

    core.set_fan(True)

    assert core.get_fan() is True
    assert core.get_dryer() is False
    assert core.get_compressed_air() is False


def test_safe_shutdown_switches_off_a_configured_fan() -> None:
    core, _ = _connected_core(fan_output_channel=6)
    core.start()
    core.set_fan(True)

    result = core.safe_shutdown()

    assert result["safe"] is True
    by_action = {item["action"]: item for item in result["actions"]}
    assert by_action["fan_off"]["status"] == "PASS"
    assert core.get_fan() is False


def test_safe_shutdown_skips_an_unconfigured_fan() -> None:
    core, _ = _connected_core()

    result = core.safe_shutdown()

    by_action = {item["action"]: item for item in result["actions"]}
    assert by_action["fan_off"]["status"] == "SKIP"


@pytest.mark.parametrize(
    "channels",
    [
        {"dryer_output_channel": 2, "compressed_air_output_channel": 2},
        {"dryer_output_channel": 2, "fan_output_channel": 2},
        {"compressed_air_output_channel": 3, "fan_output_channel": 3},
    ],
)
def test_mapping_two_auxiliary_outputs_to_one_channel_is_rejected(channels) -> None:
    """One physical output cannot drive two loads; the features would alias."""
    with pytest.raises(DriverLimitViolationError) as captured:
        _connected_core(**channels)

    error = captured.value
    assert sorted(error.details["conflicting_settings"]) == sorted(channels)
    assert "different channels" in str(error)


def test_simulator_keeps_auxiliary_output_channels_independent() -> None:
    core, _ = _connected_core(dryer_output_channel=2, compressed_air_output_channel=3)

    core.set_dryer(True)

    assert core.get_dryer() is True
    assert core.get_compressed_air() is False


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
