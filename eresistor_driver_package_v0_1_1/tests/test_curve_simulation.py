from eresistor_driver.simulation import CurveProfile


def test_time_resistance_curve_parse():
    profile = CurveProfile.from_csv_text("time_s,resistance_ohm\n0,10000\n1,12000\n")
    assert len(profile.points) == 2
    assert profile.points[0].value_type == "resistance"


def test_dwell_temperature_curve_parse():
    profile = CurveProfile.from_csv_text("temperature_c,dwell_s\n25,5\n40,10\n")
    assert profile.points[0].time_s == 0
    assert profile.points[1].time_s == 5
    assert profile.points[0].value_type == "temperature"
