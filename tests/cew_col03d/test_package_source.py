from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

try:
    from experiments.cew_col03d.package_source import (
        HISTORICAL_V25_PACKAGE,
        verify_package_source,
    )
except (ImportError, ModuleNotFoundError):
    HISTORICAL_V25_PACKAGE = None
    verify_package_source = None


class HistoricalPackageSourceTests(unittest.TestCase):
    def test_package_contract_is_frozen(self):
        self.assertIsNotNone(HISTORICAL_V25_PACKAGE, "COL-03D package source implementation missing")
        self.assertEqual(HISTORICAL_V25_PACKAGE["logical_name"], "Ariano_Irpino_DXF_strutturale_v25.zip")
        self.assertEqual(HISTORICAL_V25_PACKAGE["repository_path"], "archive/historical_packages/v25/Ariano_Irpino_DXF_strutturale_v25.zip")
        self.assertEqual(HISTORICAL_V25_PACKAGE["sha256"], "10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d")
        self.assertEqual(HISTORICAL_V25_PACKAGE["size_bytes"], 5_345_286)
        self.assertEqual(HISTORICAL_V25_PACKAGE["member_count"], 91)
        self.assertEqual(HISTORICAL_V25_PACKAGE["authority"], "HISTORICAL_DERIVED_EVIDENCE")
        self.assertFalse(HISTORICAL_V25_PACKAGE["identity_promotion_authorized"])
        self.assertFalse(HISTORICAL_V25_PACKAGE["repository_materialized"])

    def test_unmaterialized_repository_package_fails_closed(self):
        self.assertIsNotNone(verify_package_source, "COL-03D package source implementation missing")
        contract = dict(HISTORICAL_V25_PACKAGE)
        self.assertFalse(Path(contract["repository_path"]).exists())
        with self.assertRaisesRegex(ValueError, "PACKAGE_SOURCE_NOT_FOUND"):
            verify_package_source(Path(contract["repository_path"]), contract)

    def test_changed_bytes_fail_as_provenance_mismatch_before_zip_semantics(self):
        self.assertIsNotNone(verify_package_source, "COL-03D package source implementation missing")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Ariano_Irpino_DXF_strutturale_v25.zip"
            path.write_bytes(b"changed bytes")
            contract = dict(HISTORICAL_V25_PACKAGE)
            with self.assertRaisesRegex(ValueError, "PROVENANCE_MISMATCH"):
                verify_package_source(path, contract)

    def test_verified_synthetic_zip_keeps_historical_authority_closed(self):
        self.assertIsNotNone(verify_package_source, "COL-03D package source implementation missing")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.zip"
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("member.txt", b"historical")
            data = path.read_bytes()
            contract = dict(HISTORICAL_V25_PACKAGE)
            contract["sha256"] = hashlib.sha256(data).hexdigest()
            contract["size_bytes"] = len(data)
            contract["member_count"] = 1
            verified = verify_package_source(path, contract, allow_test_digest_override=True)
            self.assertEqual(verified["materialization_state"], "MATERIALIZED_VERIFIED")
            self.assertEqual(verified["member_count"], 1)
            self.assertEqual(verified["authority"], "HISTORICAL_DERIVED_EVIDENCE")
            self.assertFalse(verified["identity_promotion_authorized"])

    def test_missing_package_fails_closed(self):
        self.assertIsNotNone(verify_package_source, "COL-03D package source implementation missing")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.zip"
            with self.assertRaisesRegex(ValueError, "PACKAGE_SOURCE_NOT_FOUND"):
                verify_package_source(path, dict(HISTORICAL_V25_PACKAGE))

    def test_test_override_still_requires_valid_zip(self):
        self.assertIsNotNone(verify_package_source, "COL-03D package source implementation missing")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.zip"
            data = b"not-a-zip"
            path.write_bytes(data)
            contract = dict(HISTORICAL_V25_PACKAGE)
            contract["sha256"] = hashlib.sha256(data).hexdigest()
            contract["size_bytes"] = len(data)
            with self.assertRaisesRegex(ValueError, "PACKAGE_ZIP_INVALID"):
                verify_package_source(path, contract, allow_test_digest_override=True)


if __name__ == "__main__":
    unittest.main()
