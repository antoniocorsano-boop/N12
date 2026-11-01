from __future__ import annotations

from pathlib import Path
import unittest

try:
    from experiments.cew_col03d.package_asset import (
        PACKAGE_ASSET_MANIFEST_PATH,
        load_package_asset_manifest,
        validate_package_asset_metadata,
        verified_asset_package_witness,
    )
except (ImportError, ModuleNotFoundError):
    PACKAGE_ASSET_MANIFEST_PATH = None
    load_package_asset_manifest = None
    validate_package_asset_metadata = None
    verified_asset_package_witness = None


EXPECTED_SHA256 = "10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d"
EXPECTED_SIZE = 5_345_286
EXPECTED_MEMBER_COUNT = 91
EXPECTED_RELEASE_ID = 430_435_574
EXPECTED_ASSET_ID = 697_696_555
EXPECTED_ASSET_NAME = "Ariano_Irpino_DXF_strutturale_v25.zip"


class HistoricalPackageAssetTests(unittest.TestCase):
    def test_repository_manifest_pins_private_release_asset_identity(self):
        self.assertIsNotNone(load_package_asset_manifest, "COL-03D package asset implementation missing")
        self.assertIsNotNone(PACKAGE_ASSET_MANIFEST_PATH, "COL-03D package asset manifest path missing")
        manifest = load_package_asset_manifest(PACKAGE_ASSET_MANIFEST_PATH)
        self.assertEqual(manifest["schema"], "CEW_COL03D_PACKAGE_ASSET_V1")
        self.assertEqual(manifest["repository"], "antoniocorsano-boop/N12")
        self.assertEqual(manifest["release_id"], EXPECTED_RELEASE_ID)
        self.assertTrue(manifest["release_must_remain_draft"])
        self.assertEqual(manifest["asset_id"], EXPECTED_ASSET_ID)
        self.assertEqual(manifest["asset_name"], EXPECTED_ASSET_NAME)
        self.assertEqual(manifest["asset_content_type"], "application/zip")
        self.assertEqual(manifest["package_sha256"], EXPECTED_SHA256)
        self.assertEqual(manifest["package_size_bytes"], EXPECTED_SIZE)
        self.assertEqual(manifest["package_member_count"], EXPECTED_MEMBER_COUNT)
        self.assertEqual(manifest["authority"], "HISTORICAL_DERIVED_EVIDENCE")
        self.assertFalse(manifest["identity_promotion_authorized"])

    def test_exact_github_metadata_is_accepted_and_drift_fails_closed(self):
        self.assertIsNotNone(validate_package_asset_metadata, "COL-03D package asset implementation missing")
        manifest = {
            "schema": "CEW_COL03D_PACKAGE_ASSET_V1",
            "repository": "antoniocorsano-boop/N12",
            "release_id": EXPECTED_RELEASE_ID,
            "release_must_remain_draft": True,
            "asset_id": EXPECTED_ASSET_ID,
            "asset_name": EXPECTED_ASSET_NAME,
            "asset_content_type": "application/zip",
            "package_sha256": EXPECTED_SHA256,
            "package_size_bytes": EXPECTED_SIZE,
            "package_member_count": EXPECTED_MEMBER_COUNT,
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "identity_promotion_authorized": False,
        }
        metadata = {
            "release_id": EXPECTED_RELEASE_ID,
            "release_draft": True,
            "asset_id": EXPECTED_ASSET_ID,
            "name": EXPECTED_ASSET_NAME,
            "content_type": "application/zip",
            "size": EXPECTED_SIZE,
            "digest": f"sha256:{EXPECTED_SHA256}",
            "state": "uploaded",
        }
        accepted = validate_package_asset_metadata(manifest, metadata)
        self.assertEqual(accepted["asset_id"], EXPECTED_ASSET_ID)
        self.assertEqual(accepted["asset_digest"], f"sha256:{EXPECTED_SHA256}")
        self.assertEqual(accepted["authority"], "HISTORICAL_DERIVED_EVIDENCE")
        self.assertFalse(accepted["identity_promotion_authorized"])
        for key, changed in (
            ("release_draft", False),
            ("asset_id", EXPECTED_ASSET_ID + 1),
            ("name", "same-looking-other.zip"),
            ("size", EXPECTED_SIZE - 1),
            ("digest", "sha256:" + "0" * 64),
            ("state", "new"),
        ):
            drifted = dict(metadata)
            drifted[key] = changed
            with self.assertRaisesRegex(ValueError, "PACKAGE_ASSET_METADATA_MISMATCH"):
                validate_package_asset_metadata(manifest, drifted)

    def test_verified_package_can_only_be_promoted_to_replayable_evidence_not_structural_authority(self):
        self.assertIsNotNone(verified_asset_package_witness, "COL-03D package asset implementation missing")
        manifest = {
            "schema": "CEW_COL03D_PACKAGE_ASSET_V1",
            "repository": "antoniocorsano-boop/N12",
            "release_id": EXPECTED_RELEASE_ID,
            "release_must_remain_draft": True,
            "asset_id": EXPECTED_ASSET_ID,
            "asset_name": EXPECTED_ASSET_NAME,
            "asset_content_type": "application/zip",
            "package_sha256": EXPECTED_SHA256,
            "package_size_bytes": EXPECTED_SIZE,
            "package_member_count": EXPECTED_MEMBER_COUNT,
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "identity_promotion_authorized": False,
        }
        package_verification = {
            "logical_name": EXPECTED_ASSET_NAME,
            "sha256": EXPECTED_SHA256,
            "size_bytes": EXPECTED_SIZE,
            "member_count": EXPECTED_MEMBER_COUNT,
            "materialization_state": "MATERIALIZED_VERIFIED",
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "identity_promotion_authorized": False,
        }
        witness = verified_asset_package_witness(manifest, package_verification)
        self.assertTrue(witness["repository_materialized"])
        self.assertTrue(witness["exact_source_replayable"])
        self.assertEqual(witness["verification_state"], "MATERIALIZED_VERIFIED")
        self.assertEqual(witness["asset_id"], EXPECTED_ASSET_ID)
        self.assertFalse(witness["identity_promotion_authorized"])
        self.assertFalse(witness["structural_identity_authorized"])
        self.assertFalse(witness["canonical_geometry_authorized"])
        self.assertFalse(witness["canonical_write_authorized"])


if __name__ == "__main__":
    unittest.main()
