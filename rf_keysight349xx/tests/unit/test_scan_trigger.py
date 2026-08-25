import unittest

from rf_keysight349xx.exceptions import DriverValidationError
from rf_keysight349xx.library import Keysight349xxLibrary


class ScanTriggerTests(unittest.TestCase):
    def setUp(self):
        self.lib = Keysight349xxLibrary()
        self.lib.connect("SIM::34972A", alias="daq")

    def tearDown(self):
        self.lib.disconnect_all()

    def test_measurement_configuration_does_not_trigger_reading(self):
        channel = self.lib.configure_dc_voltage(101, range_value=10, resolution=0.001, alias="daq")
        self.assertEqual(channel, "101")
        tx = [r.payload for r in self.lib._session("daq").transport.trace_records if r.direction == "TX"][-1]
        self.assertEqual(tx, b"CONF:VOLT:DC 10,0.001,(@101)\n")

    def test_scan_list_round_trip_and_clear(self):
        self.lib.configure_dc_voltage(101, alias="daq")
        self.lib.configure_dc_voltage(102, alias="daq")
        self.assertEqual(self.lib.configure_scan_list([102, 101], alias="daq"), ["101", "102"])
        self.assertEqual(self.lib.get_scan_list("daq"), ["101", "102"])
        self.lib.clear_scan_list("daq")
        self.assertEqual(self.lib.get_scan_list("daq"), [])

    def test_scan_list_rejects_unavailable_channel_before_io(self):
        transport = self.lib._session("daq").transport
        before = len(transport.trace_records)
        with self.assertRaises(DriverValidationError):
            self.lib.configure_scan_list([101, 301], alias="daq")
        self.assertEqual(len(transport.trace_records), before)

    def test_trigger_source_round_trip(self):
        self.assertEqual(self.lib.configure_trigger_source("timer", alias="daq"), "TIM")
        self.assertEqual(self.lib.get_trigger_source("daq"), "TIM")
        with self.assertRaises(DriverValidationError):
            self.lib.configure_triggger_source("invalid", alias="daq")

    def test_trigger_count_and_timer_round_trip(self):
        self.assertEqual(self.lib.set_trigger_count(10, alias="daq"), 10)
        self.assertEqual(self.lib.get_trigger_count("daq"), 10)
        self.assertEqual(self.lib.set_trigger_count("INF", alias="daq"), "INF")
        self.assertEqual(self.lib.get_trigger_count("daq"), "INF")
        self.assertAlmostEqual(self.lib.set_trigger_timer(0.03, alias="daq"), 0.03)
        self.assertAlmostEqual(self.lib.get_trigger_timer("daq"), 0.03)
        with self.assertRaises(DriverValidationError):
            self.lib.set_trigger_count(50001, alias="daq")
        with self.assertRaises(DriverValidationError):
            self.lib.set_trigger_timer(360000, alias="daq")


if __name__ == "__main__":
    unittest.main()
