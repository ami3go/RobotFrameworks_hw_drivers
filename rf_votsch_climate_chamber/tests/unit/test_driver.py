from __future__ import annotations

import socket

import pytest

from tests.support.fake_chamber import FakeChamberServer
from votsch_climate_chamber.driver import (
    ClimateChamber,
    ClimateChamberCommunicationError,
    ClimateChamberSafetyError,
    create_command_string,
    translate_command_name_to_command_number,
)


def make_driver(server: FakeChamberServer, **kwargs) -> ClimateChamber:
    return ClimateChamber(
        "127.0.0.1",
        -40,
        180,
        port=server.port,
        timeout=0.5,
        response_timeout=0.5,
        state_settle_delay=0,
        **kwargs,
    )


def test_command_creation_and_translation() -> None:
    assert create_command_string("11004", 1) == b"11004\xb61\xb61\r"
    assert translate_command_name_to_command_number("get control_variable actual_value") == "11004"


def test_deferred_connection_has_no_socket() -> None:
    driver = ClimateChamber("127.0.0.1", -40, 180, connect_on_init=False)
    assert driver.is_connected is False
    driver.disconnect()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"port": 0},
        {"timeout": 0},
        {"response_timeout": -1},
        {"retries": -1},
        {"retry_delay": -0.1},
        {"max_response_bytes": 8},
    ],
)
def test_invalid_transport_configuration_is_rejected(kwargs) -> None:
    with pytest.raises(ValueError):
        ClimateChamber("127.0.0.1", -40, 180, connect_on_init=False, **kwargs)


def test_full_driver_round_trip() -> None:
    with FakeChamberServer() as server:
        driver = make_driver(server)
        assert driver.verify_connection()
        assert driver.serial_number == "FAKE-2601"
        assert driver.test_system_type == "VT4002EMC"
        assert driver.year_manufactured == "2026"
        driver.temperature_set_point = 85
        assert driver.temperature_set_point == 85
        driver.start()
        assert driver.is_running is True
        assert driver.wait_until_temperature(85, wait_period=0.01, timeout=1, stable_samples=2) == 85
        driver.dryer = True
        driver.compressed_air = True
        assert driver.dryer is True
        assert driver.compressed_air is True
        driver.gradient_up = 3
        driver.gradient_down = 2.5
        assert driver.gradient_up == 3
        assert driver.gradient_down == 2.5
        driver.stop()
        assert driver.is_running is False
        driver.disconnect()


def test_safety_limit_rejects_command() -> None:
    with FakeChamberServer() as server:
        driver = make_driver(server)
        with pytest.raises(ClimateChamberSafetyError):
            driver.temperature_set_point = 200


def test_reconnect_after_server_closes_connection_once() -> None:
    with FakeChamberServer() as server:
        driver = make_driver(server, retries=2, retry_delay=0)
        server.state.close_next_request = True
        assert driver.chamber_status == "READY"
        assert driver.communication_stats["reconnect_count"] >= 1


def test_unavailable_server_raises_communication_error() -> None:
    temporary = socket.socket()
    temporary.bind(("127.0.0.1", 0))
    port = temporary.getsockname()[1]
    temporary.close()
    driver = ClimateChamber(
        "127.0.0.1", -40, 180, port=port, timeout=0.05, retries=0, connect_on_init=False
    )
    with pytest.raises(ClimateChamberCommunicationError):
        driver.connect()
