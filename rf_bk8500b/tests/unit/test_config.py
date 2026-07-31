import math
import pytest

from bk8500b import ConfigurationError, DriverConfig, RetryPolicy


def test_valid_default_configuration() -> None:
    config = DriverConfig(port="COM1")
    assert config.baud_rate == 9600
    assert config.read_timeout_s == 2.0


@pytest.mark.parametrize("value", [0.0, -1.0, math.inf, math.nan])
def test_timeout_must_be_positive_and_finite(value: float) -> None:
    with pytest.raises(ConfigurationError):
        DriverConfig(port="COM1", read_timeout_s=value)


def test_empty_port_rejected() -> None:
    with pytest.raises(ConfigurationError):
        DriverConfig(port="  ")


def test_blind_write_retries_prohibited() -> None:
    with pytest.raises(ConfigurationError):
        RetryPolicy(max_write_attempts=2)
