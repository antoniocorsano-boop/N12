import hashlib
import tempfile
import unittest
from pathlib import Path

from experiments.cew_col03d.member_verification import (
    HISTORICAL_TRANSPORT_ROOT,
    REQUIRED_MEMBER_CONTRACTS,
    reconstruct_required_member_directory,
)

try:
    from experiments.cew_dxf01.reader import read_dxf_path
except (ImportError, ModuleNotFoundError):
    read_dxf_path = None


ROOT = Path(__file__).resolve().parents[2]
DXF_CONTRACTS = tuple(
    row for row in REQUIRED_MEMBER_CONTRACTS if str(row["artifact_name"]).lower().endswith(".dxf")
)


class Dxf01InventoryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.materialized = Path(cls.tmp.name) / "members"
        reconstruct_required_member_directory(
            ROOT / HISTORICAL_TRANSPORT_ROOT,
            cls.materialized,
            contracts=DXF_CONTRACTS,
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_reader_structures_exact_recovered_dxfs_deterministically_without_writes(self):
        self.assertIsNotNone(
            read_dxf_path,
            "CEW-DXF-01 RED: governed structured reader is not implemented",
        )
        for contract in DXF_CONTRACTS:
            path = self.materialized / contract["artifact_name"]
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result_a = read_dxf_path(
                path,
                artifact_name=contract["artifact_name"],
                expected_sha256=contract["sha256"],
                expected_size_bytes=contract["size_bytes"],
            )
            result_b = read_dxf_path(
                path,
                artifact_name=contract["artifact_name"],
                expected_sha256=contract["sha256"],
                expected_size_bytes=contract["size_bytes"],
            )
            after = hashlib.sha256(path.read_bytes()).hexdigest()

            self.assertEqual(before, contract["sha256"])
            self.assertEqual(after, before)
            self.assertEqual(result_a, result_b)
            self.assertEqual(result_a["source"]["sha256"], contract["sha256"])
            self.assertEqual(result_a["source"]["size_bytes"], contract["size_bytes"])
            self.assertEqual(result_a["source"]["dxf_version"], "AC1027")
            self.assertEqual(result_a["toolchain"]["ezdxf_version"], "1.4.5")
            self.assertEqual(result_a["authority"]["authority_effect"], "NONE")
            self.assertFalse(result_a["authority"]["structural_identity_authorized"])
            self.assertFalse(result_a["authority"]["canonical_write_authorized"])
            self.assertTrue(result_a["inventories"]["layers"])
            self.assertTrue(result_a["inventories"]["entity_counts"])
            self.assertIn("text_entities", result_a["inventories"])
            self.assertIn("inserts", result_a["inventories"])
            self.assertIn("blocks", result_a["inventories"])
            self.assertIn("dimensions", result_a["inventories"])
            self.assertIn("extents", result_a["inventories"])
            self.assertEqual(len(result_a["normalized_sha256"]), 64)

            entity_ids = []
            for key in ("text_entities", "inserts", "dimensions"):
                entity_ids.extend(row["stable_id"] for row in result_a["inventories"][key])
            self.assertEqual(len(entity_ids), len(set(entity_ids)))


if __name__ == "__main__":
    unittest.main()
