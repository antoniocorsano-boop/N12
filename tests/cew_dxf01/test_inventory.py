import unittest

try:
    from experiments.cew_dxf01.reader import read_dxf_path
except (ImportError, ModuleNotFoundError):
    read_dxf_path = None


class Dxf01InventoryContractTests(unittest.TestCase):
    def test_reader_exists_before_structured_inventory_can_qualify(self):
        self.assertIsNotNone(
            read_dxf_path,
            "CEW-DXF-01 RED: governed structured reader is not implemented",
        )


if __name__ == "__main__":
    unittest.main()
