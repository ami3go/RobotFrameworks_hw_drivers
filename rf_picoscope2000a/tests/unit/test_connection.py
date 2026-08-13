"""Connection lifecycle, autodetect, and identity."""

from __future__ import annotations

import pytest

from picoscope2000a.driver import PicoScope2000A
from picoscope2000a.exceptions import PicoScope2000AConnectionError
from picoscope2000a.simulator import DEFAULT_SIMULATED_SERIAL, SimulatedBus


def test_connect_and_identity():
    driver = PicoScope2000A.connect_simulated()
    assert driver.connected is True
    assert driver.resource == DEFAULT_SIMULATED_SERIAL

    identity = driver.identify()
    assert identity.manufacturer == "Pico Technology"
    assert identity.model
    assert identity.serial == DEFAULT_SIMULATED_SERIAL

    assert driver.check_communication() is True
    driver.close()
    assert driver.connected is False


def test_operations_require_connection():
    driver = PicoScope2000A.connect_simulated()
    driver.close()
    with pytest.raises(PicoScope2000AConnectionError):
        driver.identify()
    with pytest.raises(PicoScope2000AConnectionError):
        driver.check_communication()


def test_close_is_idempotent():
    driver = PicoScope2000A.connect_simulated()
    driver.close()
    driver.close()  # must not raise
    assert driver.connected is False


def test_autodetect_opens_the_single_available_device():
    bus = SimulatedBus(devices={"SIM/00042": "2208B"})
    driver = PicoScope2000A.connect_simulated(bus=bus)
    assert driver.resource == "SIM/00042"
    assert driver.identify().model == "2208B"


def test_autodetect_raises_when_no_devices_present():
    bus = SimulatedBus(devices={})
    with pytest.raises(PicoScope2000AConnectionError, match="no PicoScope devices"):
        PicoScope2000A.connect_simulated(bus=bus)


def test_autodetect_raises_when_multiple_devices_present():
    bus = SimulatedBus(devices={"SIM/001": "2208B", "SIM/002": "2206B"})
    with pytest.raises(PicoScope2000AConnectionError, match="multiple PicoScope devices"):
        PicoScope2000A.connect_simulated(bus=bus)


def test_explicit_resource_selects_one_of_several_devices():
    bus = SimulatedBus(devices={"SIM/001": "2208B", "SIM/002": "2206B"})
    driver = PicoScope2000A.connect_simulated(resource="SIM/002", bus=bus)
    assert driver.resource == "SIM/002"
    assert driver.identify().model == "2206B"


def test_enumerate_devices_lists_serials_without_opening():
    bus = SimulatedBus(devices={"SIM/001": "2208B", "SIM/002": "2206B"})
    driver = PicoScope2000A.connect_simulated(resource="SIM/001", bus=bus)
    assert driver.enumerate_devices() == ["SIM/001", "SIM/002"]


def test_connect_to_unknown_serial_raises():
    bus = SimulatedBus(devices={"SIM/001": "2208B"})
    with pytest.raises(PicoScope2000AConnectionError, match="no simulated PicoScope"):
        PicoScope2000A.connect_simulated(resource="SIM/999", bus=bus)
