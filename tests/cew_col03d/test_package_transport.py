from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

try:
    from experiments.cew_col03d.package_transport import (
        PACKAGE_TRANSPORT_MANIFEST_PATH,
        load_package_transport_manifest,
        reconstruct_historical_package_from_transport,
        verify_package_transport,
    )
except (ImportError, ModuleNotFoundError):
    PACKAGE_TRANSPORT_MANIFEST_PATH = None
    load_package_transport_manifest = None
    reconstruct_historical_package_from_transport = None
    verify_package_transport = None


TRANSPORT_ROOT = Path("archive/historical_packages/v25/package_transport")
EXPECTED_PACKAGE_SHA256 = "10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d"
EXPECTED_PACKAGE_SIZE = 5_345_286
EXPECTED_MEMBER_COUNT = 91
EXPECTED_PART_COUNT = 21


class HistoricalPackageTransportTests(unittest.TestCase):
    def test_transport_manifest_contract_is_repository_owned_and_complete(self):
        self.assertIsNotNone(load_package_transport_manifest, "COL-03D package transport implementation missing")
        self.assertIsNotNone(PACKAGE_TRANSPORT_MANIFEST_PATH, "COL-03D package transport manifest path missing")
        manifest = load_package_transport_manifest(PACKAGE_TRANSPORT_MANIFEST_PATH)
        self.assertEqual(manifest["schema"], "CEW_COL03D_PACKAGE_TRANSPORT_V1")
        self.assertEqual(manifest["transport_kind"], "RAW_SPLIT_CONCAT_V1")
        self.assertEqual(manifest["package_sha256"], EXPECTED_PACKAGE_SHA256)
        self.assertEqual(manifest["package_size_bytes"], EXPECTED_PACKAGE_SIZE)
        self.assertEqual(manifest["package_member_count"], EXPECTED_MEMBER_COUNT)
        self.assertEqual(manifest["part_count"], EXPECTED_PART_COUNT)
        self.assertEqual(len(manifest["parts"]), EXPECTED_PART_COUNT)
        self.assertEqual(
            [row["name"] for row in manifest["parts"]],
            [f"Ariano_Irpino_DXF_strutturale_v25.zip.part{i:03d}" for i in range(EXPECTED_PART_COUNT)],
        )

    def test_exact_checkout_transport_reconstructs_frozen_package(self):
        self.assertIsNotNone(reconstruct_historical_package_from_transport, "COL-03D package transport implementation missing")
        manifest = load_package_transport_manifest(PACKAGE_TRANSPORT_MANIFEST_PATH)
        verified_parts = verify_package_transport(TRANSPORT_ROOT, manifest)
        self.assertEqual(len(verified_parts), EXPECTED_PART_COUNT)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "Ariano_Irpino_DXF_strutturale_v25.zip"
            witness = reconstruct_historical_package_from_transport(TRANSPORT_ROOT, output, manifest)
            self.assertEqual(witness["sha256"], EXPECTED_PACKAGE_SHA256)
            self.assertEqual(witness["size_bytes"], EXPECTED_PACKAGE_SIZE)
            self.assertEqual(witness["member_count"], EXPECTED_MEMBER_COUNT)
            self.assertTrue(witness["repository_materialized"])
            self.assertTrue(witness["exact_source_replayable"])
            self.assertEqual(witness["authority"], "HISTORICAL_DERIVED_EVIDENCE")
            self.assertFalse(witness["identity_promotion_authorized"])

    def test_missing_or_extra_transport_part_fails_closed(self):
        self.assertIsNotNone(verify_package_transport, "COL-03D package transport implementation missing")
        synthetic_manifest = {
            "schema": "CEW_COL03D_PACKAGE_TRANSPORT_V1",
            "transport_kind": "RAW_SPLIT_CONCAT_V1",
            "package_sha256": EXPECTED_PACKAGE_SHA256,
            "package_size_bytes": EXPECTED_PACKAGE_SIZE,
            "package_member_count": EXPECTED_MEMBER_COUNT,
            "part_count": 1,
            "parts": [{"name": "Ariano_Irpino_DXF_strutturale_v25.zip.part000", "size_bytes": 1, "sha256": "00" * 32}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "PACKAGE_TRANSPORT_PART_MISSING"):
                verify_package_transport(root, synthetic_manifest)
            (root / synthetic_manifest["parts"][0]["name"]).write_bytes(b"x")
            (root / "Ariano_Irpino_DXF_strutturale_v25.zip.part999").write_bytes(b"y")
            with self.assertRaisesRegex(ValueError, "PACKAGE_TRANSPORT_SURFACE_DRIFT"):
                verify_package_transport(root, synthetic_manifest)


if __name__ == "__main__":
    unittest.main()
