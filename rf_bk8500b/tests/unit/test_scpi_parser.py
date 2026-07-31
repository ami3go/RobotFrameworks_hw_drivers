import pytest

from bk8500b import MalformedResponseError, OperatingMode
from bk8500b.protocol.scpi import parse_bool, parse_error, parse_float, parse_identity, parse_int


def test_parse_identity() -> None:
    identity = parse_identity("B&K Precision,BK8510B,1234,1.45")
    assert identity.model == "BK8510B"
    assert identity.serial_number == "1234"


def test_parse_error_with_quoted_comma() -> None:
    error = parse_error('-200,"Execution error, mode"')
    assert error.code == -200
    assert error.message == "Execution error, mode"

@pytest.mark.parametrize("text,expected", [("1", True), ("ON", True), ("0", False), ("OFF", False)])
def test_parse_bool(text: str, expected: bool) -> None:
    assert parse_bool(text) is expected


def test_nonfinite_float_rejected() -> None:
    with pytest.raises(MalformedResponseError):
        parse_float("nan")


def test_integral_nr2_accepted() -> None:
    assert parse_int("1.000") == 1


def test_mode_aliases() -> None:
    assert OperatingMode.from_response("CC") is OperatingMode.CURRENT
    assert OperatingMode.from_response("RES") is OperatingMode.RESISTANCE
