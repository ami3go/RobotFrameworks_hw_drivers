"""Raw SLCAN escape hatch, behind its own confirmation-text guard."""

from __future__ import annotations

import pytest

from slcan.driver import SlcanAdapter
from slcan.enums import Bitrate
from slcan.exceptions import SlcanDeviceError, SlcanValidationError


@pytest.fixture()
def driver():
    d = SlcanAdapter.connect_simulated()
    yield d
    d.close()


def test_raw_command_rejected_before_enable(driver):
    with pytest.raises(SlcanValidationError, match="disabled"):
        driver.raw_command("V", expects_data=True)


def test_enable_raw_slcan_rejects_wrong_confirmation_text(driver):
    with pytest.raises(SlcanValidationError, match="confirmation"):
        driver.enable_raw_slcan("yes please")


def test_enable_raw_slcan_with_exact_text_unlocks_it(driver):
    driver.enable_raw_slcan("ENABLE RAW SLCAN")
    assert driver.raw_command("V", expects_data=True) == "V1013"


def test_raw_command_can_set_bitrate(driver):
    driver.enable_raw_slcan("ENABLE RAW SLCAN")
    driver.raw_command(f"S{Bitrate.BPS_500K.value}")
    driver.raw_command("O")
    assert driver.channel_open is False  # raw_command bypasses driver-level state tracking


def test_raw_command_surfaces_nack_as_device_error(driver):
    driver.enable_raw_slcan("ENABLE RAW SLCAN")
    with pytest.raises(SlcanDeviceError):
        driver.raw_command("O")  # channel can't open without a bitrate first
