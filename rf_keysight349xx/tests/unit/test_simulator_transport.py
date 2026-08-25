import unittest

from rf_keysight349xx.protocol.scpi import ScpiProtocol
from rf_keysight349xx.exceptions import DriverTimeoutError
from rf_keysight349xx.transports.simulator import SimulatorTransport


class SimulatorTests(unittest.TestCase):
    def setUp(self):
        self.transport = SimulatorTransport("34972A")
        self.transport.open()
        self.scpi = ScpiProtocol(self.transport)

    def tearDown(self): self.transport.close()
    def test_identity_query(self): self.assertIn("34972A", self.scpi.query("*IDN?", timeout_s=1.0, operation_id="test"))
    def test_module_query(self): self.assertIn("34907A", self.scpi.query("SYST:CTYP? 300", timeout_s=1.0, operation_id="test"))
    def test_error_queue(self):
        self.scpi.write("BOGUS", timeout_s=1.0, operation_id="test")
        self.assertIn("-113", self.scpi.query("SYST:ERR?", timeout_s=1.0, operation_id="test"))
    def test_trace_captures_tx_rx(self):
        self.scpi.query("*IDN?", timeout_s=1.0, operation_id="trace-id")
        self.assertEqual([r.direction for r in self.transport.trace_records], ["TX", "RX"])
        self.assertTrue(all(r.operation_id == "trace-id" for r in self.transport.trace_records))
    def test_scpi_uses_real_lf_terminator(self):
        self.scpi.query("*IDN?", timeout_s=1.0, operation_id="bytes")
        records=self.transport.trace_records
        self.assertEqual(records[0].payload,b"*IDN?\n"); self.assertTrue(records[1].payload.endswith(b"\n")); self.assertNotIn(b"\\n",records[0].payload)
    def test_timeout_fault_injection(self):
        self.transport.fail_next_timeout=True
        with self.assertRaises(DriverTimeoutError): self.scpi.query("*IDN?",timeout_s=0.01,operation_id="timeout")
    def test_measurement_queries_at_protocol_boundary(self):
        self.assertEqual(self.scpi.query("MEAS:VOLT:DC? (@101)",timeout_s=1.0,operation_id="measure"), "+5.001000000E+00")
        self.assertEqual(self.scpi.query("MEAS:RES? 1000,1,(@103)",timeout_s=1.0,operation_id="measure"), "+1.003000000E+03")
    def test_malformed_response_fault_injection(self):
        self.transport.malformed_next_response=b"not-an-idn\n"
        self.assertEqual(self.scpi.query("*IDN?",timeout_s=1.0,operation_id="malformed"),"not-an-idn")

if __name__ == "__main__": unittest.main()
