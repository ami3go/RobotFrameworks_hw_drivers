"""The background reader thread must actually stop on close()/Disconnect —
a leaked thread should fail these tests, not hang the suite."""

from __future__ import annotations

from slcan.driver import SlcanAdapter


def test_reader_thread_stops_on_close():
    driver = SlcanAdapter.connect_simulated()
    assert driver._reader.is_alive() is True
    driver.close()
    assert driver._reader.is_alive() is False


def test_reader_thread_stops_promptly():
    """Bounds how long close() can take — a wedged thread would make this
    test time out rather than pass silently."""

    import time

    driver = SlcanAdapter.connect_simulated()
    start = time.monotonic()
    driver.close()
    elapsed = time.monotonic() - start
    assert elapsed < 2.0


def test_reconnect_after_close_starts_a_fresh_thread():
    driver = SlcanAdapter.connect_simulated()
    driver.close()
    assert driver._reader.is_alive() is False

    driver2 = SlcanAdapter.connect_simulated()
    assert driver2._reader.is_alive() is True
    driver2.close()


def test_multiple_sessions_each_have_independent_reader_threads():
    driver_a = SlcanAdapter.connect_simulated()
    driver_b = SlcanAdapter.connect_simulated()
    assert driver_a._reader.is_alive() is True
    assert driver_b._reader.is_alive() is True

    driver_a.close()
    assert driver_a._reader.is_alive() is False
    assert driver_b._reader.is_alive() is True  # unaffected

    driver_b.close()
