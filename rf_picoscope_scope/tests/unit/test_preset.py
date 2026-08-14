"""Preset save/load round-trip."""

from __future__ import annotations

import pytest

from picoscope_scope.driver import PicoScope


@pytest.fixture
def configured_driver():
    d = PicoScope.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_channel_range("A", 2.0)
    d.set_channel_coupling("A", "AC")
    d.set_channel_offset("A", 0.05)
    d.set_channel_enabled("B", True)
    d.set_channel_probe("B", "current", scale=10.0)
    d.set_trigger("A", threshold_v=0.5, direction="FALLING", delay_samples=3, auto_trigger_ms=50)
    d.set_timebase(sample_interval_s=1e-6, num_samples=500, pre_trigger_ratio=0.25)
    d.set_awg_waveform("triangle", frequency_hz=2000.0, peak_to_peak_v=1.5, offset_v=0.2)
    yield d
    d.close()


def test_save_preset_writes_a_file(configured_driver, tmp_path):
    out = tmp_path / "preset.json"
    configured_driver.save_preset(out)
    assert out.exists()


def test_load_preset_restores_channel_settings(configured_driver, tmp_path):
    out = tmp_path / "preset.json"
    configured_driver.save_preset(out)

    fresh = PicoScope.connect_simulated()
    fresh.load_preset(out)
    try:
        a = fresh.get_channel_settings("A")
        assert a.enabled is True
        assert a.range_v == 2.0
        assert a.coupling == "AC"
        assert a.offset_v == 0.05

        b = fresh.get_channel_settings("B")
        assert b.enabled is True
        assert b.probe_type == "CURRENT"
        assert b.probe_scale == 10.0
    finally:
        fresh.close()


def test_load_preset_restores_trigger_settings(configured_driver, tmp_path):
    out = tmp_path / "preset.json"
    configured_driver.save_preset(out)

    fresh = PicoScope.connect_simulated()
    fresh.load_preset(out)
    try:
        trigger = fresh.get_trigger_settings()
        assert trigger.enabled is True
        assert trigger.channel == "A"
        assert trigger.threshold_v == 0.5
        assert trigger.direction == "FALLING"
        assert trigger.delay_samples == 3
        assert trigger.auto_trigger_ms == 50
    finally:
        fresh.close()


def test_load_preset_restores_timebase_settings(configured_driver, tmp_path):
    out = tmp_path / "preset.json"
    configured_driver.save_preset(out)

    fresh = PicoScope.connect_simulated()
    fresh.load_preset(out)
    try:
        timebase = fresh.get_timebase_settings()
        assert timebase.num_samples == 500
        assert timebase.pre_trigger_ratio == 0.25
        assert timebase.sample_interval_s >= 1e-6
    finally:
        fresh.close()


def test_load_preset_restores_awg_settings(configured_driver, tmp_path):
    out = tmp_path / "preset.json"
    configured_driver.save_preset(out)

    fresh = PicoScope.connect_simulated()
    fresh.load_preset(out)
    try:
        awg = fresh.get_awg_settings()
        assert awg.enabled is True
        assert awg.wave_type == "TRIANGLE"
        assert awg.frequency_hz == 2000.0
        assert awg.peak_to_peak_v == 1.5
        assert awg.offset_v == 0.2
    finally:
        fresh.close()


def test_load_preset_with_disabled_trigger_and_awg_round_trips(tmp_path):
    source = PicoScope.connect_simulated()
    source.set_channel_enabled("A", True)
    source.set_timebase(sample_interval_s=1e-6, num_samples=100)
    out = tmp_path / "preset.json"
    source.save_preset(out)
    source.close()

    fresh = PicoScope.connect_simulated()
    fresh.load_preset(out)
    try:
        assert fresh.get_trigger_settings().enabled is False
        assert fresh.get_awg_settings().enabled is False
    finally:
        fresh.close()


def test_preset_round_trip_is_stable_across_a_second_save(configured_driver, tmp_path):
    first = tmp_path / "first.json"
    configured_driver.save_preset(first)

    fresh = PicoScope.connect_simulated()
    fresh.load_preset(first)
    second = tmp_path / "second.json"
    fresh.save_preset(second)
    fresh.close()

    assert first.read_text() == second.read_text()
