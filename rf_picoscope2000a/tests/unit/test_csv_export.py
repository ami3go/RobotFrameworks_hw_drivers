"""Per-channel and combined CSV waveform export."""

from __future__ import annotations

import csv

import pytest

from picoscope2000a.driver import PicoScope2000A

_SAMPLE_INTERVAL_S = 20e-6
_NUM_SAMPLES = 50


@pytest.fixture
def captured_driver():
    d = PicoScope2000A.connect_simulated()
    d.set_channel_enabled("A", True)
    d.set_channel_enabled("B", True)
    d.set_channel_probe("B", "current", scale=10.0)
    d.set_timebase(sample_interval_s=_SAMPLE_INTERVAL_S, num_samples=_NUM_SAMPLES)
    d.capture_block()
    yield d
    d.close()


def test_save_waveform_to_csv_writes_header_and_all_rows(captured_driver, tmp_path):
    out = tmp_path / "channel_a.csv"
    captured_driver.save_waveform_to_csv(out, "A")

    with out.open(newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["time_s", "value_v"]
    assert len(rows) == _NUM_SAMPLES + 1

    waveform = captured_driver.get_waveform("A")
    assert float(rows[1][0]) == pytest.approx(waveform.time_s[0])
    assert float(rows[1][1]) == pytest.approx(waveform.values[0])
    assert float(rows[-1][0]) == pytest.approx(waveform.time_s[-1])
    assert float(rows[-1][1]) == pytest.approx(waveform.values[-1])


def test_save_waveform_to_csv_uses_amps_column_for_current_probe(captured_driver, tmp_path):
    out = tmp_path / "channel_b.csv"
    captured_driver.save_waveform_to_csv(out, "B")
    with out.open(newline="") as handle:
        header = next(csv.reader(handle))
    assert header == ["time_s", "value_a"]


def test_save_waveform_to_csv_creates_parent_directories(captured_driver, tmp_path):
    out = tmp_path / "nested" / "dir" / "channel_a.csv"
    captured_driver.save_waveform_to_csv(out, "A")
    assert out.exists()


def test_save_all_waveforms_to_csv_has_one_shared_time_column_and_per_channel_values(
    captured_driver, tmp_path
):
    out = tmp_path / "all_channels.csv"
    captured_driver.save_all_waveforms_to_csv(out)

    with out.open(newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["time_s", "A_v", "B_a"]
    assert len(rows) == _NUM_SAMPLES + 1

    waveform_a = captured_driver.get_waveform("A")
    waveform_b = captured_driver.get_waveform("B")
    assert float(rows[1][0]) == pytest.approx(waveform_a.time_s[0])
    assert float(rows[1][1]) == pytest.approx(waveform_a.values[0])
    assert float(rows[1][2]) == pytest.approx(waveform_b.values[0])
    # Both channels share one sample clock -> identical time column.
    for i, row in enumerate(rows[1:]):
        assert float(row[0]) == pytest.approx(waveform_a.time_s[i])
        assert float(row[2]) == pytest.approx(waveform_b.values[i])
