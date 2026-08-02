"""Bitrate / open / close channel control."""

from __future__ import annotations

import pytest

from slcan.driver import SlcanAdapter
from slcan.enums import Bitrate, ChannelMode
from slcan.exceptions import SlcanDeviceError


@pytest.fixture()
def driver():
    d = SlcanAdapter.connect_simulated()
    yield d
    d.close()


def test_open_before_bitrate_is_rejected(driver):
    """Conservative, documented judgment call (task §19): the simulator
    fail-closes rather than opening at an undefined bitrate."""

    with pytest.raises(SlcanDeviceError):
        driver.open_channel()
    assert driver.channel_open is False


def test_bitrate_then_open_normal(driver):
    driver.set_bitrate(Bitrate.BPS_500K)
    driver.open_channel(ChannelMode.NORMAL)
    assert driver.channel_open is True


def test_bitrate_then_open_listen_only(driver):
    driver.set_bitrate(Bitrate.BPS_250K)
    driver.open_channel(ChannelMode.LISTEN_ONLY)
    assert driver.channel_open is True


def test_bitrate_cannot_change_while_open(driver):
    driver.set_bitrate(Bitrate.BPS_500K)
    driver.open_channel()
    with pytest.raises(SlcanDeviceError):
        driver.set_bitrate(Bitrate.BPS_250K)


def test_open_twice_is_rejected(driver):
    driver.set_bitrate(Bitrate.BPS_500K)
    driver.open_channel()
    with pytest.raises(SlcanDeviceError):
        driver.open_channel()


def test_close_is_always_possible_even_when_not_open(driver):
    """task §6: closing the channel must always be possible, even mid-fault
    or when the driver's own state already believes it's closed."""

    driver.close_channel()  # no exception
    assert driver.channel_open is False


def test_close_then_reopen_round_trip(driver):
    driver.set_bitrate(Bitrate.BPS_500K)
    driver.open_channel()
    driver.close_channel()
    assert driver.channel_open is False
    driver.open_channel()
    assert driver.channel_open is True
