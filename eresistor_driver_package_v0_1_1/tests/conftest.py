from __future__ import annotations

import pytest

from eresistor_driver.calibration import parse_compact_calibration


def compact_cal_text() -> str:
    # Powers of two-ish conductance ladder. CH1..CH8 same data.
    sections = []
    values = [626, 1240, 2500, 5000, 10000, 20000, 40000, 80000, 160000, 320000, 640000, 1_280_000, 2_560_000, 5_120_000, 10_240_000, 20_000_000]
    for ch in range(1, 9):
        records = [f"{bit},Q{16-bit},{values[bit]}" for bit in range(16)]
        sections.append(f"CH{ch}:" + ";".join(records))
    return "|".join(sections)


@pytest.fixture
def device_calibration():
    return parse_compact_calibration(compact_cal_text())
