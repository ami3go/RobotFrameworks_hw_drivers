import unittest

from rf_keysight349xx.exceptions import DriverStateError
from rf_keysight349xx.library import Keysight349xxLibrary
from rf_keysight349xx.transports.base import ReplayPolicy


class AcquisitionMemoryTests(unittest.TestCase):
    def setUp(self):
        self.lib = Keysight349xxLibrary()
        self.lib.connect("SIM::34972A", alias="daq")
        self.lib.configure_dc_voltage(101, alias="daq")
        self.lib.configure_dc_voltage(102, alias="daq")
        self.lib.configure_scan_list([101, 102], alias="daq")

    def tearDown(self):
        self.lib.disconnect_all()

    def test_initiate_fetch_and_buffered_read_semantics(self):
        self.lib.initiate_scan("daq")
        self.assertEqual(self.lib.get_reading_count("daq"), 2)
        fetched = self.lib.fetch_readings("daq")
        self.assertEqual(len(fetched), 2)
        self.assertEqual(self.lib.get_reading_count("daq"), 2)
        drained = self.lib.read_buffered_readings(1, "daq")
        self.assertEqual(len(drained), 1)
        self.assertEqual(self.lib._session("daq").transport.last_replay_policy, ReplayPolicy.NEVER)
        self.assertEqual(self.lib.get_reading_count("daq"), 1)

    def test_data_remove_is_destructive_and_prevalidated(self):
        self.lib.set_trigger_count(2, alias="daq")
        self.lib.initiate_scan("daq")
        self.assertEqual(self.lib.get_reading_count("daq"), 4)
        removed = self.lib.remove_readings(2, "daq")
        self.assertEqual(len(removed), 2)
        self.assertEqual(self.lib.get_reading_count("daq"), 2)
        with self.assertRaises(DriverStateError):
            self.lib.remove_readings(3, "daq")
        self.assertEqual(self.lib.get_reading_count("daq"), 2)

    def test_clear_reading_memory_drains_stored_readings(self):
        self.lib.initiate_scan("daq")
        self.assertEqual(self.lib.clear_reading_memory("daq"), 2)
        self.assertEqual(self.lib.get_reading_count("daq"), 0)

    def test_read_scan_34972a_retains_memory(self):
        readings = self.lib.read_scan("daq")
        self.assertEqual(len(readings), 2)
        self.assertEqual(self.lib.get_reading_count("daq"), 2)
        self.assertIsNotNone(self.lib.get_scan_start_time("daq"))

    def test_read_scan_34970a_does_not_retain_memory(self):
        lib = Keysight349xxLibrary()
        try:
            lib.connect("SIM::34970A", alias="old")
            lib.configure_dc_voltage(101, alias="old")
            lib.configure_scan_list([101], alias="old")
            self.assertEqual(len(lib.read_scan("old")), 1)
            self.assertEqual(lib.get_reading_count("old"), 0)
        finally:
            lib.disconnect_all()

    def test_read_scan_rejects_bus_trigger(self):
        self.lib.configure_trigger_source("BUS", alias="daq")
        with self.assertRaises(DriverStateError):
            self.lib.read_scan("daq")

    def test_initiate_rejects_empty_scan_list_before_init(self):
        self.lib.clear_scan_list("daq")
        transport = self.lib._session("daq").transport
        before = len(transport.trace_records)
        with self.assertRaises(DriverStateError):
            self.lib.initiate_scan("daq")
        tx = [r.payload for r in transport.trace_records[before:] if r.direction == "TX"]
        self.assertEqual(tx, [b"ROUT:SCAN?\n"])

    def test_abort_preserves_memory(self):
        self.lib.initiate_scan("daq")
        before = self.lib.get_reading_count("daq")
        self.lib.abort_scan("daq")
        self.assertEqual(self.lib.get_reading_count("daq"), before)


if __name__ == "__main__":
    unittest.main()
