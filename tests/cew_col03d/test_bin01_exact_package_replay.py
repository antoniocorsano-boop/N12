from __future__ import annotations

from pathlib import Path
import unittest

from experiments.cew_col03d.exact_source import build_exact_source_recovery
from experiments.cew_col03d.package_source import HISTORICAL_V25_PACKAGE, verify_package_source
from experiments.cew_col03d.recovery import PREDECESSOR_COL03C_SHA


PACKAGE_PATH = Path(HISTORICAL_V25_PACKAGE["repository_path"])
TRANSPORT_ROOT = Path("archive/historical_packages/v25/transport")
INVENTORY_PATH = Path("archive/ARTEFATTI_STORICI.md")


class ExactPackageReplayBin01Tests(unittest.TestCase):
    def test_exact_historical_package_is_repository_materialized_and_verified(self):
        self.assertTrue(PACKAGE_PATH.is_file(), "BIN-01 exact package missing from repository checkout")
        verified = verify_package_source(PACKAGE_PATH)
        self.assertEqual(verified["sha256"], HISTORICAL_V25_PACKAGE["sha256"])
        self.assertEqual(verified["size_bytes"], 5_345_286)
        self.assertEqual(verified["member_count"], 91)
        self.assertTrue(verified["repository_materialized"])
        self.assertEqual(verified["materialization_state"], "MATERIALIZED_VERIFIED")
        self.assertFalse(verified["identity_promotion_authorized"])

    def test_exact_source_closes_only_repository_replay_blocker(self):
        artifacts = build_exact_source_recovery(
            transport_root=TRANSPORT_ROOT,
            inventory_text=INVENTORY_PATH.read_text(encoding="utf-8"),
            predecessor_sha=PREDECESSOR_COL03C_SHA,
        )
        package = artifacts["historical-package-recovery-manifest.json"]
        closure = artifacts["historical-recovery-closure.json"]

        self.assertTrue(package["historical_package_repository_materialized"])
        self.assertTrue(package["historical_package_exact_source_replayable"])
        self.assertTrue(closure["historical_package_repository_materialized"])
        self.assertTrue(closure["historical_package_exact_source_replayable"])
        self.assertTrue(closure["col03d_exact_source_qualification_complete"])
        self.assertEqual(closure["qualification_blockers"], [])
        self.assertFalse(closure["historical_evidence_identity_promoted"])

        for key in (
            "support_identity_authorized",
            "text_identity_binding_authorized",
            "family_assignment_authorized",
            "section_assignment_authorized",
            "fixed_line_assignment_authorized",
            "vertical_chain_assignment_authorized",
            "structural_identity_authorized",
            "canonical_node_assignment_authorized",
            "canonical_geometry_authorized",
            "canonical_write_authorized",
            "g2c_promotion_authorized",
            "g3_authorized",
            "merge_authorized",
        ):
            self.assertFalse(closure[key], key)


if __name__ == "__main__":
    unittest.main()
