from __future__ import annotations

import math
import pytest

from bk8500b import DriverConfig, Protocol, ReconnectPolicy, RetryPolicy
from bk8500b.exceptions import ConfigurationError


@pytest.mark.parametrize("kwargs", [
    {"max_read_attempts": 0},
    {"max_write_attempts": 2},
    {"initial_backoff_s": -1},
    {"maximum_backoff_s": -1},
    {"initial_backoff_s": 1, "maximum_backoff_s": 0.5},
    {"jitter_fraction": -0.1},
    {"jitter_fraction": 1.1},
    {"jitter_fraction": math.nan},
])
def test_retry_policy_rejects_invalid_values(kwargs):
    with pytest.raises(ConfigurationError):
        RetryPolicy(**kwargs)


@pytest.mark.parametrize("kwargs", [
    {"max_attempts": 0},
    {"total_deadline_s": 0},
    {"total_deadline_s": math.inf},
])
def test_reconnect_policy_rejects_invalid_values(kwargs):
    with pytest.raises(ConfigurationError):
        ReconnectPolicy(**kwargs)


def test_protocol_string_is_coerced():
    assert DriverConfig(port="COM1", protocol="scpi").protocol is Protocol.SCPI


@pytest.mark.parametrize("kwargs", [
    {"port": ""},
    {"protocol": "not-a-protocol"},
    {"address": -1},
    {"address": 32},
    {"baud_rate": 0},
    {"bytesize": 9},
    {"parity": "X"},
    {"stopbits": 3},
    {"connect_timeout_s": 0},
    {"minimum_command_interval_s": -1},
    {"scpi_write_terminator": b""},
    {"scpi_read_terminator": b"12345"},
    {"maximum_scpi_response_bytes": 15},
    {"maximum_error_queue_entries": 0},
    {"maximum_error_queue_entries": 1025},
])
def test_driver_config_rejects_invalid_values(kwargs):
    with pytest.raises(ConfigurationError):
        DriverConfig(**({"port": "COM1"} | kwargs))
