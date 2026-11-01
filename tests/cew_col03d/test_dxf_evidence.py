from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from experiments.cew_col03d.member_verification import (
    HISTORICAL_TRANSPORT_ROOT,
    REQUIRED_MEMBER_CONTRACTS,
    reconstruct_required_member_directory,
)

try:
    from experiments.cew_col03d.dxf_evidence import audit_dxf_member
except (ImportError, ModuleNotFoundError):
    audit_dxf_member = None


DXF_NAMES = (
    "TAV5_CARPENTERIA.dxf",
    "TAV6_TRAVI.dxf",
    "TAV7_PILASTRI.dxf",
)


class HistoricalDxfEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "members"
        reconstruct_required_member_directory(
            Path(HISTORICAL_TRANSPORT_ROOT), cls.root, REQUIRED_MEMBER_CONTRACTS
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_three_recovered_dxfs_are_read_only_ac1027_evidence(self):
        self.assertIsNotNone(audit_dxf_member, "COL-03D DXF evidence auditor missing")
        for name in DXF_NAMES:
            audit = audit_dxf_member(name, (self.root / name).read_bytes())
            self.assertEqual(audit["artifact_name"], name)
            self.assertEqual(audit["dxf_version"], "AC1027")
            self.assertGreater(audit["entity_count"], 0)
            self.assertGreater(audit["layer_count"], 0)
            self.assertEqual(audit["layers"], sorted(audit["layers"]))
            self.assertGreaterEqual(audit["text_observation_count"], 0)
            self.assertEqual(audit["authority"], "HISTORICAL_DERIVED_EVIDENCE")
            self.assertFalse(audit["promotion_authorized"])
            self.assertFalse(audit["structural_identity_authorized"])

    def test_dxf_audit_is_deterministic(self):
        self.assertIsNotNone(audit_dxf_member, "COL-03D DXF evidence auditor missing")
        name = "TAV7_PILASTRI.dxf"
        data = (self.root / name).read_bytes()
        self.assertEqual(audit_dxf_member(name, data), audit_dxf_member(name, data))

    def test_wrong_dxf_version_fails_closed(self):
        self.assertIsNotNone(audit_dxf_member, "COL-03D DXF evidence auditor missing")
        invalid = b"0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n0\nENDSEC\n0\nEOF\n"
        with self.assertRaisesRegex(ValueError, "DXF_VERSION_NOT_AC1027"):
            audit_dxf_member("old.dxf", invalid)


if __name__ == "__main__":
    unittest.main()
