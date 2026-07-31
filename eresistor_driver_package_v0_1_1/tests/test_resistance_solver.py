import math

import pytest

from eresistor_driver.resistance import ResistanceSolver
from eresistor_driver.models import SafetyConfig
from eresistor_driver.exceptions import SafetyLimitError


def test_equivalent_resistance(device_calibration):
    solver = ResistanceSolver(device_calibration, SafetyConfig(min_resistance_ohm=None, max_resistance_ohm=None))
    assert math.isinf(solver.equivalent_resistance(1, "0000"))
    assert solver.equivalent_resistance(1, "0001") == pytest.approx(626)
    r = solver.equivalent_resistance(1, "0003")
    assert r == pytest.approx(1 / (1 / 626 + 1 / 1240))


def test_find_closest(device_calibration):
    solver = ResistanceSolver(device_calibration, SafetyConfig(min_resistance_ohm=None, max_resistance_ohm=None))
    result = solver.find_closest(1, 10_000)
    assert result.channel == 1
    assert result.mask
    assert result.calculated_ohm > 0
    assert abs(result.error_percent) < 20


def test_safety_rejects_low(device_calibration):
    solver = ResistanceSolver(device_calibration, SafetyConfig(min_resistance_ohm=1000, max_resistance_ohm=20_000_000))
    with pytest.raises(SafetyLimitError):
        solver.find_closest(1, 500)
