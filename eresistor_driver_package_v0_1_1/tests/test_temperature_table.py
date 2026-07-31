import pytest

from eresistor_driver.temperature import TemperatureTable
from eresistor_driver.exceptions import TemperatureTableError


def test_temperature_interpolation():
    table = TemperatureTable.from_csv_text("temperature_c,resistance_ohm\n20,12000\n30,8000\n")
    assert table.resistance_at(25) == pytest.approx(10000)


def test_log_interpolation():
    table = TemperatureTable.from_csv_text("T,R\n0,10000\n10,1000\n")
    assert table.resistance_at(5, mode="log_resistance") == pytest.approx(3162.277660, rel=1e-6)


def test_out_of_range_rejected():
    table = TemperatureTable.from_csv_text("temperature,resistance\n20,12000\n30,8000\n")
    with pytest.raises(TemperatureTableError):
        table.resistance_at(40)
