"""Acceptance code/mask filter commands (Gate 3 extension — M/m).

Not confirmed as universally supported/identical across adapters (task doc
§2/§16) — grounded in the widely-mirrored Lawicel description. The
simulator/driver treat these as config-only-while-closed, mirroring the
already-confirmed S<n> bitrate constraint.
"""

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


def test_acceptance_code_default_is_none(driver):
    assert driver.get_acceptance_code() is None


def test_acceptance_mask_default_is_none(driver):
    assert driver.get_acceptance_mask() is None


def test_acceptance_code_round_trip(driver):
    driver.set_acceptance_code(0x123)
    assert driver.get_acceptance_code() == 0x123


def test_acceptance_mask_round_trip(driver):
    driver.set_acceptance_mask(0xFFFFFFFF)
    assert driver.get_acceptance_mask() == 0xFFFFFFFF


def test_acceptance_code_accepts_full_32_bit_range(driver):
    driver.set_acceptance_code(0xFFFFFFFF)
    assert driver.get_acceptance_code() == 0xFFFFFFFF
    driver.set_acceptance_code(0)
    assert driver.get_acceptance_code() == 0


def test_acceptance_code_rejects_out_of_range(driver):
    with pytest.raises(SlcanValidationError):
        driver.set_acceptance_code(-1)
    with pytest.raises(SlcanValidationError):
        driver.set_acceptance_code(0x100000000)


def test_acceptance_mask_rejects_out_of_range(driver):
    with pytest.raises(SlcanValidationError):
        driver.set_acceptance_mask(-1)
    with pytest.raises(SlcanValidationError):
        driver.set_acceptance_mask(0x100000000)


def test_acceptance_code_cannot_change_while_channel_open(driver):
    driver.set_bitrate(Bitrate.BPS_500K)
    driver.open_channel()
    with pytest.raises(SlcanDeviceError):
        driver.set_acceptance_code(0x123)
    driver.close_channel()


def test_acceptance_mask_cannot_change_while_channel_open(driver):
    driver.set_bitrate(Bitrate.BPS_500K)
    driver.open_channel()
    with pytest.raises(SlcanDeviceError):
        driver.set_acceptance_mask(0xFFFFFFFF)
    driver.close_channel()


def test_acceptance_code_and_mask_can_be_set_before_open(driver):
    driver.set_acceptance_code(0x123)
    driver.set_acceptance_mask(0x7FF)
    driver.set_bitrate(Bitrate.BPS_500K)
    driver.open_channel()  # no exception — filters configured while closed
    driver.close_channel()
