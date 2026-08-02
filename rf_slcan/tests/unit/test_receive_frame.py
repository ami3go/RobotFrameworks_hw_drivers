"""Receiving CAN frames via the background reader thread.

These are the scenarios that justify this driver's whole architecture (see
``slcan/reader.py``): frames arrive asynchronously and must never be
confused with a command's own acknowledgement, must survive arriving while
no keyword is actively running, and a full receive queue must degrade
predictably (drop oldest, count it) rather than silently losing track or
blocking a producer forever.
"""

from __future__ import annotations

import threading
import time

import pytest

from slcan.driver import SlcanAdapter
from slcan.enums import Bitrate, ChannelMode
from slcan.exceptions import SlcanConnectionError
from slcan.models import CanFrame


@pytest.fixture()
def driver():
    d = SlcanAdapter.connect_simulated()
    d.set_bitrate(Bitrate.BPS_500K)
    d.open_channel(ChannelMode.NORMAL)
    yield d
    d.close()


def test_receive_frame_times_out_with_none_when_nothing_arrives(driver):
    assert driver.receive_frame(timeout_s=0.2) is None


def test_frame_injected_while_idle_is_still_captured(driver):
    """No keyword is running between the inject and the receive call — the
    background thread must have captured it anyway."""

    frame = CanFrame(arbitration_id=0x456, data=b"\x01\x02", dlc=2)
    driver.transport.simulator.inject_frame(frame)
    time.sleep(0.05)  # give the background thread a moment to route it
    received = driver.receive_frame(timeout_s=1.0)
    assert received == frame


def test_frame_injected_between_command_write_and_ack_is_not_mistaken_for_the_ack(driver):
    """The core correctness property of the background-reader design: a
    frame arriving mid-command must be routed to rx_queue, never consumed
    as that command's ack."""

    def injector():
        time.sleep(0.01)
        driver.transport.simulator.inject_frame(CanFrame(arbitration_id=0x789, data=b"\xff", dlc=1))

    t = threading.Thread(target=injector)
    t.start()
    driver.send_frame(0x100, b"\x01\x02\x03")  # must succeed, not raise
    t.join()

    frame = driver.receive_frame(timeout_s=1.0)
    assert frame is not None
    assert frame.arbitration_id == 0x789


def test_drain_received_frames_returns_everything_queued(driver):
    for i in range(5):
        driver.transport.simulator.inject_frame(CanFrame(arbitration_id=i, data=b"", dlc=0))
    time.sleep(0.1)
    frames = driver.drain_received_frames()
    assert [f.arbitration_id for f in frames] == [0, 1, 2, 3, 4]
    assert driver.get_received_frame_count() == 0


def test_drain_received_frames_respects_max_count(driver):
    for i in range(5):
        driver.transport.simulator.inject_frame(CanFrame(arbitration_id=i, data=b"", dlc=0))
    time.sleep(0.1)
    frames = driver.drain_received_frames(max_count=2)
    assert len(frames) == 2
    assert driver.get_received_frame_count() == 3


def test_clear_received_frames(driver):
    driver.transport.simulator.inject_frame(CanFrame(arbitration_id=1, data=b"", dlc=0))
    time.sleep(0.05)
    driver.clear_received_frames()
    assert driver.get_received_frame_count() == 0


def test_overflow_drops_oldest_and_counts_it(driver):
    from slcan.reader import DEFAULT_RX_QUEUE_MAXSIZE

    for i in range(DEFAULT_RX_QUEUE_MAXSIZE + 5):
        driver.transport.simulator.inject_frame(CanFrame(arbitration_id=i % 0x7FF, data=b"", dlc=0))
    time.sleep(0.3)

    assert driver.get_receive_overflow_count() == 5
    assert driver.get_received_frame_count() == DEFAULT_RX_QUEUE_MAXSIZE
    frames = driver.drain_received_frames()
    # The oldest 5 (arbitration_id 0-4) were dropped; the queue starts at 5.
    assert frames[0].arbitration_id == 5


def test_reader_fault_surfaces_as_connection_error_on_next_call():
    driver = SlcanAdapter.connect_simulated()
    driver.set_bitrate(Bitrate.BPS_500K)
    driver.open_channel(ChannelMode.NORMAL)

    # Simulate the transport dying underneath the reader thread.
    driver._reader.fault = RuntimeError("simulated transport failure")

    with pytest.raises(SlcanConnectionError):
        driver.receive_frame(timeout_s=0.2)
    with pytest.raises(SlcanConnectionError):
        driver.drain_received_frames()

    driver.close()
