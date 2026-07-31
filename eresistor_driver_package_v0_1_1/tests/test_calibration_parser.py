import pytest

from eresistor_driver.calibration import parse_begin_end_calibration, parse_compact_calibration, parse_resistance_value
from eresistor_driver.exceptions import CalibrationError
from conftest import compact_cal_text


def test_parse_resistance_suffixes():
    assert parse_resistance_value("626R") == 626
    assert parse_resistance_value("1.2K") == 1200
    assert parse_resistance_value("2M") == 2_000_000


def test_parse_compact_calibration():
    cal = parse_compact_calibration(compact_cal_text())
    assert sorted(cal.channels) == list(range(1, 9))
    assert cal.channels[1].branches[0].mosfet_name == "Q16"
    assert cal.channels[1].branches[15].mosfet_name == "Q1"


def test_parse_begin_end_calibration():
    text = """#BEGIN CH1 path=/ch1.csv saved=1 size=123
bit,mosfet_name,nominal_resistance
0,Q16,626R
1,Q15,1.24K
2,Q14,2.5K
3,Q13,5K
4,Q12,10K
5,Q11,20K
6,Q10,40K
7,Q9,80K
8,Q8,160K
9,Q7,320K
10,Q6,640K
11,Q5,1.28M
12,Q4,2.56M
13,Q3,5.12M
14,Q2,10.24M
15,Q1,20M
#END CH1
"""
    cal = parse_begin_end_calibration(text)
    assert cal.channels[1].branches[0].resistance_ohm == 626
    assert cal.channels[1].branches[15].resistance_ohm == 20_000_000


def test_invalid_calibration_rejected():
    text = "CH1:0,Q16,0;" + ";".join(f"{i},Q{i},{1000+i}" for i in range(1, 16))
    with pytest.raises(CalibrationError):
        parse_compact_calibration(text)
