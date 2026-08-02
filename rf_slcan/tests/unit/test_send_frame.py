"""Sending CAN frames."""

from __future__ import annotations

import pytest

from slcan.driver import SlcanAdapter
from slcan.enums import Bitrate, ChannelMode
from slcan.exceptions import SlcanDeviceError, SlcanValidationError


@pytest.fixture()
def driver():
    d = SlcanAdapter.connect_simulated()
    d.set_bitrate(Bitrate.BPS_500K)
    d.open_channel(ChannelMode.NORMAL)
    yield d
    d.close()


def test_send_standard_data_frame(driver):
    driver.send_frame(0x123, b"\xaa\xbb\xcc")  # no exception


def test_send_extended_data_frame(driver):
    driver.send_frame(0x1ABCDEF, b"\x01\x02", extended=True)


def test_send_remote_frame(driver):
    driver.send_frame(0x321, remote=True)


def test_send_rejects_more_than_8_bytes(driver):
    with pytest.raises(SlcanValidationError):
        driver.send_frame(0x123, b"\x00" * 9)


def test_send_rejects_standard_id_out_of_range(driver):
    with pytest.raises(SlcanValidationError):
        driver.send_frame(0x800, b"\x01")


def test_send_rejects_extended_id_out_of_range(driver):
    with pytest.raises(SlcanValidationError):
        driver.send_frame(0x20000000, b"\x01", extended=True)


def test_send_requires_channel_open():
    driver = SlcanAdapter.connect_simulated()
    driver.set_bitrate(Bitrate.BPS_500K)
    with pytest.raises(SlcanDeviceError):
        driver.send_frame(0x123, b"\x01")
    driver.close()


def test_send_rejected_in_listen_only_mode():
    driver = SlcanAdapter.connect_simulated()
    driver.set_bitrate(Bitrate.BPS_500K)
    driver.open_channel(ChannelMode.LISTEN_ONLY)
    with pytest.raises(SlcanDeviceError):
        driver.send_frame(0x123, b"\x01")
    driver.close()
