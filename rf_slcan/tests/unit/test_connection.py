"""Connection lifecycle and identity."""

from __future__ import annotations

import pytest

from slcan.driver import SlcanAdapter
from slcan.exceptions import SlcanConnectionError


def test_simulator_connect_and_identity():
    driver = SlcanAdapter.connect_simulated()
    assert driver.connected is True

    identity = driver.identify()
    assert identity.hardware_version == "1.0"
    assert identity.software_version == "1.3"
    assert identity.serial_number == "A123"

    assert driver.check_communication() is True
    driver.close()
    assert driver.connected is False


def test_operations_require_connection():
    driver = SlcanAdapter.connect_simulated()
    driver.close()
    with pytest.raises(SlcanConnectionError):
        driver.get_version()


def test_resource_reports_simulated_marker():
    driver = SlcanAdapter.connect_simulated()
    assert driver.resource == "SIMULATED"
    driver.close()


def test_identify_caches_by_default():
    driver = SlcanAdapter.connect_simulated()
    first = driver.identify()
    second = driver.identify(refresh=False)
    assert first is second
    driver.close()


def test_identify_refresh_true_re_queries():
    driver = SlcanAdapter.connect_simulated()
    first = driver.identify()
    second = driver.identify(refresh=True)
    assert first == second
    assert first is not second
    driver.close()
