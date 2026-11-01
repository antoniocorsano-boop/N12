import unittest

try:
    from experiments.cew_dxf01.reader import read_dxf_path
except (ImportError, ModuleNotFoundError):
    read_dxf_path = None


class Dxf01FailClosedContractTests(unittest.TestCase):
    def test_reader_exists_before_fail_closed_source_guards_can_qualify(self):
        self.assertIsNotNone(
            read_dxf_path,
            "CEW-DXF-01 RED: read-only exact-source guard is not implemented",
        )


if __name__ == "__main__":
    unittest.main()
