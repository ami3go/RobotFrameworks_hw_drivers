import unittest

from rf_keysight349xx.library import Keysight349xxLibrary
from rf_keysight349xx.exceptions import DriverResponseError, DriverStateError, DriverTimeoutError, DriverValidationError
from rf_keysight349xx.transports.simulator import SimulatorTransport


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.lib = Keysight349xxLibrary()

    def tearDown(self):
        self.lib.disconnect_all()

    def test_constructor_does_not_connect(self):
        self.assertFalse(self.lib.is_connected())

    def test_connect_34972a_simulator(self):
        state = self.lib.connect("SIM::34972A", alias="daq")
        self.assertTrue(state["connected"])
        self.assertTrue(state["communication_ok"])
        self.assertTrue(state["simulated"])
        self.assertIn("34972A", self.lib.get_identity("daq"))

    def test_connect_is_idempotent_same_resource(self):
        a = self.lib.connect("SIM::34972A", alias="daq")
        b = self.lib.connect("SIM::34972A", alias="daq")
        self.assertEqual(a.keys(), b.keys())
        self.assertEqual(a["resource"], b["resource"])

    def test_alias_conflict_rejected(self):
        self.lib.connect("SIM::34972A", alias="daq")
        with self.assertRaises(DriverStateError):
            self.lib.connect("SIM::34970A", alias="daq")

    def test_unknown_state_is_disconnected(self):
        state = self.lib.get_connection_state("missing")
        self.assertFalse(state["connected"])
        self.assertEqual(state["state"], "disconnected")

    def test_module_discovery(self):
        self.lib.connect("SIM::34972A", alias="daq")
        modules = self.lib.get_installed_modules("daq")
        self.assertEqual([m["slot"] for m in modules], [100, 300])
        self.assertEqual(self.lib.get_module_information(300, "daq")["model"], "34907A")

    def test_scpi_version(self):
        self.lib.connect("SIM::34972A", alias="daq")
        self.assertEqual(self.lib.get_scpi_version("daq"), "1994.0")

    def test_cached_and_live_identity_have_distinct_io_semantics(self):
        self.lib.connect("SIM::34972A", alias="daq")
        transport = self.lib._session("daq").transport
        tx_before = [r for r in transport.trace_records if r.direction == "TX"]
        self.assertEqual([r.payload for r in tx_before], [
            b"*IDN?\n", b"SYST:CTYP? 100\n", b"SYST:CTYP? 200\n", b"SYST:CTYP? 300\n"
        ])
        self.lib.get_identity("daq", refresh=False)
        self.assertEqual(len([r for r in transport.trace_records if r.direction == "TX"]), 4)
        self.lib.check_communication("daq")
        self.lib.get_identity("daq", refresh=True)
        payloads = [r.payload for r in transport.trace_records if r.direction == "TX"]
        self.assertEqual(payloads[-2:], [b"*IDN?\n", b"*IDN?\n"])

    def test_error_queue_group(self):
        self.lib.connect("SIM::34972A", alias="daq")
        self.lib.device_error_queue_should_be_empty("daq")
        self.assertEqual(self.lib.get_all_device_errors("daq"), [])

    def test_timeout_validation(self):
        with self.assertRaises(DriverValidationError):
            self.lib.set_communication_timeout(0)

    def test_nonfinite_timeouts_are_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaises(DriverValidationError):
                    self.lib.set_communication_timeout(value)

    def test_refresh_failure_updates_cached_communication_state(self):
        self.lib.connect("SIM::34972A", alias="daq")
        transport = self.lib._session("daq").transport
        transport.fail_next_timeout = True
        with self.assertRaises(DriverTimeoutError):
            self.lib.get_connection_state("daq", refresh=True)
        cached = self.lib.get_connection_state("daq", refresh=False)
        self.assertFalse(cached["communication_ok"])
        self.assertEqual(cached["state"], "faulted")

    def test_partial_connect_failure_closes_transport_and_does_not_register_session(self):
        bad_transport = SimulatorTransport("34972A")
        bad_transport.malformed_next_response = b"invalid-idn\n"

        class Factory:
            def create(self, resource, *, timeout_s, options=None):
                return bad_transport

        self.lib._transport_factory = Factory()
        with self.assertRaises(DriverResponseError):
            self.lib.connect("SIM::34972A", alias="bad")
        self.assertFalse(bad_transport.is_open)
        self.assertFalse(self.lib.is_connected("bad"))

    def test_driver_info_offline(self):
        info = self.lib.get_driver_information()
        self.assertEqual(info["name"], "rf_keysight349xx")
        self.assertIn("simulation", info["capability_ids"])


if __name__ == "__main__":
    unittest.main()
