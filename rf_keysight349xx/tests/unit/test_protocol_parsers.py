import unittest

from rf_keysight349xx.exceptions import DriverResponseError
from rf_keysight349xx.protocol.parsers import parse_device_error, parse_identity, parse_module_identity


class ParserTests(unittest.TestCase):
    def test_34972a_identity(self):
        item = parse_identity("Keysight Technologies,34972A,MY12345678,1.01-1.00-01-0002")
        self.assertEqual(item.model, "34972A")
        self.assertEqual(item.serial_number, "MY12345678")

    def test_34970a_identity(self):
        item = parse_identity("HEWLETT-PACKARD,34970A,0,13-2-2")
        self.assertEqual(item.model, "34970A")

    def test_rejects_unknown_identity(self):
        with self.assertRaises(DriverResponseError):
            parse_identity("Vendor,1234,SN,1.0")

    def test_module(self):
        item = parse_module_identity(300, "Keysight Technologies,34907A,0,1.0")
        self.assertTrue(item.installed)
        self.assertEqual(item.slot, 300)

    def test_empty_module(self):
        item = parse_module_identity(200, "Keysight Technologies,0,0,0")
        self.assertFalse(item.installed)

    def test_device_error(self):
        item = parse_device_error('-113,"Undefined header"')
        self.assertEqual(item["code"], -113)
        self.assertEqual(item["source"], "device")

    def test_malformed_device_error_fails(self):
        with self.assertRaises(DriverResponseError):
            parse_device_error("garbage")


if __name__ == "__main__":
    unittest.main()
