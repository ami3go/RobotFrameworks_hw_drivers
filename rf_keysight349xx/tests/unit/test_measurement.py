import unittest

from rf_keysight349xx.core.measurement import (
    MEASUREMENT_SPECS,
    build_measurement_query,
    parse_scalar_measurement,
)
from rf_keysight349xx.exceptions import (
    DriverDeviceError,
    DriverNotSupportedError,
    DriverValidationError,
)
from rf_keysight349xx.library import Keysight349xxLibrary


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.lib = Keysight349xxLibrary()
        self.lib.connect("SIM::34972A", alias="daq")

    def tearDown(self):
        self.lib.disconnect_all()

    def _last_tx(self):
        transport = self.lib._session("daq").transport
        return [r.payload for r in transport.trace_records if r.direction == "TX"][-1]

    def test_channel_inventory_from_installed_measurement_modules(self):
        channels = self.lib.list_channels("daq")
        self.assertEqual(channels[0], "101")
        self.assertEqual(channels[-1], "122")
        self.assertEqual(len(channels), 22)
        self.assertTrue(self.lib.validate_channel(101, "daq"))
        self.assertTrue(self.lib.validate_channel("122", "daq"))
        self.assertFalse(self.lib.validate_channel(123, "daq"))
        self.assertFalse(self.lib.validate_channel(301, "daq"))
        with self.assertRaises(DriverValidationError):
            self.lib.validate_channel("not-a-channel", "daq")

    def test_measure_dc_voltage_default_query(self):
        from rf_keysight349xx.transports.base import ReplayPolicy
        value = self.lib.measure_dc_voltage(101, alias="daq")
        self.assertAlmostEqual(value, 5.001)
        self.assertEqual(self._last_tx(), b"MEAS:VOLT:DC? (@101)\n")
        self.assertEqual(self.lib._session("daq").transport.last_replay_policy, ReplayPolicy.NEVER)

    def test_measure_ac_voltage_manual_range_and_resolution(self):
        value = self.lib.measure_ac_voltage(102, range_value=10, resolution=0.001, alias="daq")
        self.assertGreater(value, 0)
        self.assertEqual(self._last_tx(), b"MEAS:VOLT:AC? 10,0.001,(@102)\n")

    def test_measure_dc_current_only_34901a_channels_21_22(self):
        value = self.lib.measure_dc_current(121, range_value=1, alias="daq")
        self.assertGreater(value, 0)
        self.assertEqual(self._last_tx(), b"MEAS:CURR:DC? 1,(@121)\n")
        with self.assertRaises(DriverValidationError):
            self.lib.measure_dc_current(101, alias="daq")

    def test_measure_ac_current(self):
        value = self.lib.measure_ac_current(122, alias="daq")
        self.assertGreater(value, 0)
        self.assertEqual(self._last_tx(), b"MEAS:CURR:AC? (@122)\n")

    def test_measure_two_wire_resistance(self):
        value = self.lib.measure_resistance(103, alias="daq")
        self.assertAlmostEqual(value, 1003.0)
        self.assertEqual(self._last_tx(), b"MEAS:RES? (@103)\n")

    def test_measure_four_wire_resistance_pairing_source_channel(self):
        value = self.lib.measure_4_wire_resistance(104, range_value=1000, resolution=1, alias="daq")
        self.assertAlmostEqual(value, 1003.0)
        self.assertEqual(self._last_tx(), b"MEAS:FRES? 1000,1,(@104)\n")
        with self.assertRaises(DriverValidationError):
            self.lib.measure_4_wire_resistance(111, alias="daq")

    def test_measure_frequency_and_period(self):
        freq = self.lib.measure_frequency(105, alias="daq")
        period = self.lib.measure_period(105, alias="daq")
        self.assertAlmostEqual(freq, 1005.0)
        self.assertAlmostEqual(period, 1.0 / 1005.0)
        transport = self.lib._session("daq").transport
        payloads = [r.payload for r in transport.trace_records if r.direction == "TX"]
        self.assertEqual(payloads[-2:], [b"MEAS:FREQ? (@105)\n", b"MEAS:PER? (@105)\n"])

    def test_34902a_four_wire_and_34908a_restriction(self):
        self.lib.disconnect("daq")
        self.lib.connect("SIM::34972A", alias="daq2", simulator_modules="100=34902A,200=34908A,300=0")
        self.assertGreater(self.lib.measure_4_wire_resistance(108, alias="daq2"), 0)
        with self.assertRaises(DriverValidationError): self.lib.measure_4_wire_resistance(109, alias="daq2")
        with self.assertRaises(DriverNotSupportedError): self.lib.measure_4_wire_resistance(201, alias="daq2")
        self.assertGreater(self.lib.measure_dc_voltage(240, alias="daq2"), 0)

    def test_documented_range_guards(self):
        with self.assertRaises(DriverValidationError): self.lib.measure_dc_voltage(101, range_value=301, alias="daq")
        with self.assertRaises(DriverValidationError): self.lib.measure_dc_current(121, range_value=1.1, alias="daq")
        with self.assertRaises(DriverValidationError): self.lib.measure_resistance(101, range_value=100_000_001, alias="daq")
        with self.assertRaises(DriverValidationError): self.lib.measure_frequency(101, range_value=2.9, alias="daq")

    def test_resolution_requires_manual_or_explicit_range(self):
        with self.assertRaises(DriverValidationError): self.lib.measure_dc_voltage(101, resolution=0.001, alias="daq")
        with self.assertRaises(DriverValidationError): self.lib.measure_dc_voltage(101, range_value="AUTO", resolution=0.001, alias="daq")

    def test_command_builder_supports_documented_tokens(self):
        spec = MEASUREMENT_SPECS["dc_voltage"]
        self.assertEqual(build_measurement_query("dc_voltage", "101", range_value="MAX"), "MEAS:VOLT:DC? MAX,(@101)")
        self.assertEqual(spec.unit, "V")

    def test_overload_is_not_returned_as_large_numeric_value(self):
        with self.assertRaises(DriverDeviceError):
            parse_scalar_measurement("+9.90000000E+37", measurement_key="dc_voltage", channel="101")


if __name__ == "__main__": unittest.main()
