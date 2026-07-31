from dataclasses import dataclass

import pytest

from rf_eresistor.library import EResistorLibrary, _bool, _robot_value


@dataclass
class Result:
    channel: int
    mask: str


def test_robot_value_converts_dataclass_and_integer_keys():
    assert _robot_value({1: Result(1, "0001")}) == {"1": {"channel": 1, "mask": "0001"}}


@pytest.mark.parametrize("value", [True, "TRUE", "yes", "1", 1])
def test_boolean_true(value):
    assert _bool(value) is True


@pytest.mark.parametrize("value", [False, "FALSE", "no", "0", 0])
def test_boolean_false(value):
    assert _bool(value) is False


def test_invalid_boolean_rejected():
    with pytest.raises(ValueError):
        _bool("perhaps")


def test_operation_requires_connection():
    lib = EResistorLibrary()
    with pytest.raises(RuntimeError, match="not connected"):
        lib.get_identity()


class FakeClient:
    def __init__(self):
        self.closed = False
        self.shutdown_policy = __import__("eresistor_driver.models", fromlist=["ShutdownPolicy"]).ShutdownPolicy.ALL_OFF

    def idn(self):
        return "OpenBench,E-Resistor,SN001,0.4.0"

    def close(self):
        self.closed = True


def test_disconnect_is_idempotent():
    lib = EResistorLibrary()
    fake = FakeClient()
    lib._client = fake
    lib.disconnect()
    assert fake.closed
    assert lib._client is None
    lib.disconnect()

