from __future__ import annotations

from typing import Any, cast

import pytest

from tests.support.fake_chamber import FakeChamberServer
from votsch_climate_chamber.driver import ClimateChamberError, ClimateChamberSafetyError
from votsch_climate_chamber.robot_library import VotschClimateChamberLibrary


def connect_library(server: FakeChamberServer, **library_options: Any) -> VotschClimateChamberLibrary:
    library = VotschClimateChamberLibrary(**library_options)
    library.connect_climate_chamber(
        "127.0.0.1",
        -40,
        180,
        port=server.port,
        timeout="500 ms",
        response_timeout="500 ms",
        retry_delay=0,
    )
    return library


def test_conversion_validation_and_sanitizing() -> None:
    library = VotschClimateChamberLibrary()
    assert library.get_library_version() == "v26.02"
    assert library._boolean(1, "x") is True
    assert library._boolean(0, "x") is False
    assert library._boolean("NONE", "x") is False
    assert library._float("3.5", "x") == 3.5
    assert library._integer("3", "x", minimum=1) == 3
    assert library._sanitize({"raw": b"1\xb6READY\r", "items": (b"a", 2)}) == {
        "raw": "1¶READY\r",
        "items": ["a", 2],
    }

    with pytest.raises(ValueError):
        library._seconds("not a time", "x")
    with pytest.raises(ValueError):
        library._seconds(float("inf"), "x")
    with pytest.raises(ValueError):
        library._seconds(0, "x", positive=True)
    with pytest.raises(ValueError):
        library._seconds(-1, "x")
    with pytest.raises(TypeError):
        library._float(True, "x")
    with pytest.raises(TypeError):
        library._float("abc", "x")
    with pytest.raises(ValueError):
        library._float(float("nan"), "x")
    with pytest.raises(TypeError):
        library._integer("abc", "x")
    with pytest.raises(ValueError):
        library._integer(0, "x", minimum=1)


def test_all_identification_status_and_limit_keywords() -> None:
    with FakeChamberServer() as server:
        library = connect_library(server)
        assert library.get_serial_number() == "FAKE-2601"
        assert library.get_model() == "VT4002EMC"
        assert library.get_manufacturing_year() == "2026"
        assert library.get_status() == "READY"
        assert library.get_temperature() == 25
        assert library.get_setpoint() == 25
        assert library.get_temperature_limits() == {"minimum": -40.0, "maximum": 180.0}
        stats = library.get_connection_statistics()
        assert isinstance(stats["last_raw_response"], str)
        library.climate_chamber_should_be_connected()
        library.disconnect_climate_chamber()
        library.disconnect_climate_chamber()
        with pytest.raises(ClimateChamberError, match="already disconnected"):
            library.disconnect_climate_chamber(strict=True)


def test_duplicate_and_replace_existing_connection() -> None:
    with FakeChamberServer() as server:
        library = connect_library(server)
        with pytest.raises(ClimateChamberError, match="already exists"):
            library.connect_climate_chamber("127.0.0.1", -40, 180, port=server.port)
        identification = library.connect_climate_chamber(
            "127.0.0.1",
            -40,
            180,
            port=server.port,
            timeout=0.5,
            retry_delay=0,
            replace_existing=True,
        )
        assert "FAKE-2601" in identification
        library.disconnect_climate_chamber()


def test_stop_on_close_and_explicit_reconnect() -> None:
    with FakeChamberServer() as server:
        library = connect_library(server, stop_on_close="ON")
        library.start_climate_chamber()
        library.chamber_should_be_running()
        assert library.reconnect_climate_chamber() is True
        library.disconnect_climate_chamber()
        assert server.state.running is False


def test_full_temperature_sequence_dwell_gradients_and_outputs() -> None:
    with FakeChamberServer() as server:
        library = connect_library(server, progress_log_interval="1 ms")
        final = library.set_temperature_and_wait(
            65,
            dwell="2 ms",
            tolerance=0.1,
            poll_interval="1 ms",
            timeout="1 s",
            stable_samples=2,
            start_chamber="YES",
        )
        assert final == 65
        assert library.wait_for_dwell("2 ms", poll_interval="1 ms") == 65
        assert library.set_heating_gradient(3.0) == 3.0
        assert library.get_heating_gradient() == 3.0
        assert library.set_cooling_gradient(2.5) == 2.5
        assert library.get_cooling_gradient() == 2.5
        assert library.set_dryer(True) is True
        assert library.get_dryer() is True
        assert library.set_compressed_air("ON") is True
        assert library.get_compressed_air() is True
        library.setpoint_should_be(65)
        library.temperature_should_be_within(64, 66)
        library.stop_climate_chamber()
        library.chamber_should_be_stopped()
        with pytest.raises(AssertionError, match="should be running"):
            library.chamber_should_be_running()
        library.disconnect_climate_chamber()


def test_wait_can_use_current_setpoint_and_not_start() -> None:
    with FakeChamberServer() as server:
        server.state.temperature = 25
        library = connect_library(server)
        assert library.wait_until_stable(
            target=None,
            tolerance=0.1,
            poll_interval="1 ms",
            timeout="100 ms",
            stable_samples=1,
            start_chamber=False,
        ) == 25
        library.disconnect_climate_chamber()


def test_assertion_and_limit_failure_messages() -> None:
    with FakeChamberServer() as server:
        library = connect_library(server)
        with pytest.raises(ClimateChamberSafetyError):
            library.set_temperature_limits(10, 10)
        with pytest.raises(ValueError):
            library.temperature_should_be(25, tolerance=-1)
        with pytest.raises(ValueError):
            library.temperature_should_be_within(30, 20)
        with pytest.raises(AssertionError, match="outside"):
            library.temperature_should_be_within(30, 40)
        with pytest.raises(ValueError):
            library.setpoint_should_be(25, tolerance=-1)
        with pytest.raises(AssertionError, match="setpoint mismatch"):
            library.setpoint_should_be(30, tolerance=0.1)
        library.disconnect_climate_chamber()


class _BrokenTeardownDriver:
    def stop(self) -> None:
        raise RuntimeError("stop boom")

    def disconnect(self) -> None:
        raise RuntimeError("disconnect boom")


def test_stop_and_disconnect_reports_both_failures() -> None:
    library = VotschClimateChamberLibrary()
    library._driver = cast(Any, _BrokenTeardownDriver())
    with pytest.raises(ClimateChamberError) as exc:
        library.stop_and_disconnect_climate_chamber()
    text = str(exc.value)
    assert "stop boom" in text
    assert "disconnect boom" in text
    assert library._driver is None


def test_stop_and_disconnect_is_idempotent() -> None:
    VotschClimateChamberLibrary().stop_and_disconnect_climate_chamber()
