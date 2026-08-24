import unittest


class ImportIsolationTests(unittest.TestCase):
    def test_import_and_construction_do_not_open_hardware(self):
        from rf_keysight349xx.library import Keysight349xxLibrary
        lib = Keysight349xxLibrary()
        self.assertFalse(lib.is_connected())
        self.assertEqual(lib.list_connections(), [])


if __name__ == "__main__":
    unittest.main()
