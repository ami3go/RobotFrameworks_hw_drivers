"""Status / version / serial-number queries."""

from __future__ import annotations

import pytest

from slcan.driver import SlcanAdapter


@pytest.fixture()
def driver():
    d = SlcanAdapter.connect_simulated()
    yield d
    d.close()


def test_get_status_default_is_fault_free(driver):
    status = driver.get_status()
    assert status.has_fault is False
    assert status.raw_flags == 0


def test_get_status_reflects_simulator_flags(driver):
    driver.transport.simulator.status_flags = 0x80  # bus_error bit, per simulator test hook
    status = driver.get_status()
    assert status.bus_error is True
    assert status.has_fault is True


def test_get_version(driver):
    assert driver.get_version() == "HW1.0 SW1.3"


def test_get_serial_number(driver):
    assert driver.get_serial_number() == "A123"


def test_get_version_raw(driver):
    assert driver.get_version(raw=True) == b"V1013"


def test_status_query_does_not_require_channel_open(driver):
    # F/V/N are harmless, read-only queries — no bitrate/open needed first.
    driver.get_status()
    driver.get_version()
    driver.get_serial_number()
