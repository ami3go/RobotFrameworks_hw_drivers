"""Timestamp mode (Gate 3 extension — Z0/Z1)."""

from __future__ import annotations

import time

import pytest

from slcan.driver import SlcanAdapter
from slcan.enums import Bitrate, ChannelMode
from slcan.models import CanFrame


@pytest.fixture()
def driver():
    d = SlcanAdapter.connect_simulated()
    d.set_bitrate(Bitrate.BPS_500K)
    d.open_channel(ChannelMode.NORMAL)
    yield d
    d.close()


def test_timestamps_default_disabled(driver):
    assert driver.get_timestamps_enabled() is False


def test_timestamps_enable_round_trip(driver):
    driver.set_timestamps_enabled(True)
    assert driver.get_timestamps_enabled() is True
    driver.set_timestamps_enabled(False)
    assert driver.get_timestamps_enabled() is False


def test_received_frame_has_no_timestamp_when_disabled(driver):
    driver.transport.simulator.inject_frame(CanFrame(arbitration_id=0x1, data=b"", dlc=0))
    frame = driver.receive_frame(timeout_s=1.0)
    assert frame is not None
    assert frame.timestamp_ms is None


def test_received_frame_carries_explicit_timestamp_when_enabled(driver):
    driver.set_timestamps_enabled(True)
    driver.transport.simulator.inject_frame(
        CanFrame(arbitration_id=0x1, data=b"\xaa", dlc=1, timestamp_ms=1234)
    )
    frame = driver.receive_frame(timeout_s=1.0)
    assert frame is not None
    assert frame.timestamp_ms == 1234


def test_received_frame_gets_an_auto_filled_timestamp_when_enabled_and_unset(driver):
    driver.set_timestamps_enabled(True)
    driver.transport.simulator.inject_frame(CanFrame(arbitration_id=0x1, data=b"\xaa", dlc=1))
    frame = driver.receive_frame(timeout_s=1.0)
    assert frame is not None
    assert frame.timestamp_ms is not None
    assert 0 <= frame.timestamp_ms < 60000


def test_timestamp_wraps_at_60000_ms(driver):
    driver.set_timestamps_enabled(True)
    driver.transport.simulator.inject_frame(
        CanFrame(arbitration_id=0x1, data=b"", dlc=0, timestamp_ms=60005)
    )
    frame = driver.receive_frame(timeout_s=1.0)
    assert frame is not None
    assert frame.timestamp_ms == 5


def test_enabling_timestamps_mid_session_only_affects_frames_after(driver):
    driver.transport.simulator.inject_frame(CanFrame(arbitration_id=0x1, data=b"", dlc=0))
    driver.set_timestamps_enabled(True)
    driver.transport.simulator.inject_frame(
        CanFrame(arbitration_id=0x2, data=b"", dlc=0, timestamp_ms=42)
    )
    time.sleep(0.1)

    first = driver.receive_frame(timeout_s=1.0)
    second = driver.receive_frame(timeout_s=1.0)
    assert first is not None and first.timestamp_ms is None
    assert second is not None and second.timestamp_ms == 42
