from __future__ import annotations

import pytest

from rf_votsch_climate_chamber.exceptions import (
    DriverArgumentValueError,
    DriverDeviceError,
    DriverProtocolError,
)
from rf_votsch_climate_chamber.protocol.simserv import (
    COMMAND_NUMBERS,
    build_frame,
    build_named_frame,
    parse_response,
)


def test_supported_protocol_registry_contains_only_runtime_operations() -> None:
    assert set(COMMAND_NUMBERS) == {
        "GET CHAMBER INFO",
        "GET CHAMBER STATUS",
        "GET CONTROL_VARIABLE ACTUAL_VALUE",
        "GET CONTROL_VARIABLE SET_POINT",
        "GET DIGITAL_OUT VALUE",
        "GET GRADIENT_DOWN VALUE",
        "GET GRADIENT_UP VALUE",
        "SET CONTROL_VARIABLE SET_POINT",
        "SET DIGITAL_OUT VALUE",
        "SET GRADIENT_DOWN VALUE",
        "SET GRADIENT_UP VALUE",
        "START MANUAL_MODE",
    }


def test_build_frame_exact_bytes() -> None:
    assert build_frame("11001", 1, 25) == b"11001\xb61\xb61\xb625\r"


def test_build_named_frame() -> None:
    assert build_named_frame("GET CHAMBER STATUS") == b"10012\xb61\r"


@pytest.mark.parametrize("bad", ["1", "ABCDE", "123456"])
def test_bad_command_number_rejected(bad: str) -> None:
    with pytest.raises(DriverArgumentValueError):
        build_frame(bad)


def test_parse_success() -> None:
    assert parse_response("x", (), b"1\xb625.00\r") == ["25.00"]


def test_parse_malformed_and_device_error() -> None:
    with pytest.raises(DriverProtocolError):
        parse_response("x", (), b"BROKEN\r")
    with pytest.raises(DriverDeviceError):
        parse_response("x", (), b"0\r")
