from __future__ import annotations

import logging

import pytest

from tests.support.fake_chamber import FakeChamberServer
from votsch_climate_chamber.driver import (
    ClimateChamber,
    ClimateChamberProtocolError,
    ClimateChamberTimeoutError,
    check_tolerance,
    create_command_string,
    range_check,
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


def test_legacy_helpers_and_invalid_commands(capsys) -> None:
    assert range_check(200, -40, 180, "temperature") == 180
    assert range_check(-50, -40, 180, "temperature") == -40
    assert check_tolerance(10.1, 10, 0.1)
    assert "Wrong temperature" in capsys.readouterr().out
    with pytest.raises(ValueError):
        create_command_string("1234")
    with pytest.raises(ValueError):
        create_command_string("12345", 1, 2, 3, 4, 5)
    with pytest.raises(ValueError):
        create_command_string("12345", "bad\rvalue")
    with pytest.raises(ValueError):
        translate_command_name_to_command_number("GET DOES NOT EXIST")


def test_split_response_and_malformed_response() -> None:
    with FakeChamberServer() as server:
        server.state.split_responses = True
        driver = make_driver(server)
        assert driver.chamber_status == "READY"
        server.state.malformed_next_response = True
        with pytest.raises(ClimateChamberProtocolError):
            _ = driver.chamber_status


def test_context_manager_and_health() -> None:
    with FakeChamberServer() as server:
        with make_driver(server) as driver:
            health = driver.health_check()
            assert health["connected"] is True
            assert health["chamber_status"] == "READY"
        assert driver.is_connected is False


def test_wait_timeout_and_cancel() -> None:
    with FakeChamberServer() as server:
        server.state.temperature = 25
        server.state.temperature_step = 0
        driver = make_driver(server)
        driver.temperature_set_point = 85
        with pytest.raises(ClimateChamberTimeoutError, match="Timeout waiting"):
            driver.wait_until_temperature(85, wait_period=0.001, timeout=0.005)
        with pytest.raises(ClimateChamberTimeoutError, match="cancelled"):
            driver.wait_until_temperature(85, timeout=1, cancel_callback=lambda: True)


def test_dwell_validation_and_cancel() -> None:
    with FakeChamberServer() as server:
        driver = make_driver(server)
        with pytest.raises(ValueError):
            driver.dwell(-1)
        with pytest.raises(ValueError):
            driver.dwell(1, poll_interval=0)
        with pytest.raises(ClimateChamberTimeoutError, match="cancelled"):
            driver.dwell(1, poll_interval=0.01, cancel_callback=lambda: True)


def test_reconnect_disconnect_and_logger_stats() -> None:
    with FakeChamberServer() as server:
        driver = make_driver(server, logger=logging.getLogger("driver-test"))
        driver.reconnect()
        assert driver.communication_stats["reconnect_count"] == 1
        driver.disconnect()
        driver.connect()
        assert driver.verify_connection()

class _BufferedSocket:
    """Small socket double used to verify TCP frame coalescing behavior."""

    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.timeout = 1.0

    def gettimeout(self) -> float:
        return self.timeout

    def settimeout(self, value: float) -> None:
        self.timeout = value

    def recv(self, size: int) -> bytes:
        payload, self.payload = self.payload, b""
        return payload


def test_receive_buffer_preserves_coalesced_next_frame() -> None:
    driver = ClimateChamber("127.0.0.1", -40, 180, connect_on_init=False)
    driver.socket = _BufferedSocket(b"1\xb6FIRST\r1\xb6SECOND\r")  # type: ignore[assignment]
    first = driver._recv_response_locked()
    second = driver._recv_response_locked()
    assert first == b"1\xb6FIRST\r"
    assert second == b"1\xb6SECOND\r"
