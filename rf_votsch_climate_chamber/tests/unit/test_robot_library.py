from __future__ import annotations

import pytest
from robot.libdocpkg import LibraryDocumentation

from tests.support.fake_chamber import FakeChamberServer
from votsch_climate_chamber.driver import ClimateChamberError
from votsch_climate_chamber.robot_library import VotschClimateChamberLibrary


def connect_library(server: FakeChamberServer) -> VotschClimateChamberLibrary:
    library = VotschClimateChamberLibrary(progress_log_interval="1 ms")
    library.connect_climate_chamber(
        "127.0.0.1", -40, 180, port=server.port, timeout="500 ms", response_timeout="500 ms"
    )
    return library


def test_constructor_does_not_connect() -> None:
    library = VotschClimateChamberLibrary()
    assert library._driver is None


def test_connection_guard_message() -> None:
    with pytest.raises(ClimateChamberError, match="Connect Climate Chamber"):
        VotschClimateChamberLibrary().get_temperature()


def test_robot_time_and_boolean_conversion() -> None:
    assert VotschClimateChamberLibrary._seconds("500 ms", "time") == 0.5
    assert VotschClimateChamberLibrary._seconds("2h", "time") == 7200
    assert VotschClimateChamberLibrary._boolean("OFF", "value") is False
    assert VotschClimateChamberLibrary._boolean("yes", "value") is True
    with pytest.raises(ValueError):
        VotschClimateChamberLibrary._boolean("maybe", "value")


def test_connect_control_and_disconnect() -> None:
    with FakeChamberServer() as server:
        library = connect_library(server)
        assert "FAKE-2601" in library.get_identification()
        assert library.set_temperature(85) == 85
        library.start_climate_chamber()
        library.chamber_should_be_running()
        final = library.wait_until_stable(85, tolerance=0.1, poll_interval="1 ms", timeout="1 s", stable_samples=2)
        assert final == 85
        assert library.set_dryer("ON") is True
        assert library.set_compressed_air(True) is True
        health = library.get_health()
        assert health["is_running"] is True
        library.stop_and_disconnect_climate_chamber()
        assert library._driver is None


def test_temperature_assertions() -> None:
    with FakeChamberServer() as server:
        library = connect_library(server)
        library.temperature_should_be(25, 0.1)
        library.temperature_should_be_within(24, 26)
        with pytest.raises(AssertionError):
            library.temperature_should_be(30, 0.1)
        library.disconnect_climate_chamber()


def test_temperature_limits_can_move_outside_old_range() -> None:
    with FakeChamberServer() as server:
        library = connect_library(server)
        assert library.set_temperature_limits(200, 300) == {"minimum": 200.0, "maximum": 300.0}
        assert library.set_temperature_limits(-100, -50) == {"minimum": -100.0, "maximum": -50.0}
        library.disconnect_climate_chamber()


def test_only_explicit_keywords_are_exposed() -> None:
    documentation = LibraryDocumentation(
        "votsch_climate_chamber.robot_library.VotschClimateChamberLibrary"
    )
    names = {keyword.name for keyword in documentation.keywords}
    assert "Connect Climate Chamber" in names
    assert "Set Climate Chamber Temperature" in names
    assert "Seconds" not in names
    assert "Require Driver" not in names
    assert all(not name.startswith("_") for name in names)
