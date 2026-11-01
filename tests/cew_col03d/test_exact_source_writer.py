from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

try:
    from experiments.cew_col03d.exact_source import (
        build_exact_source_recovery,
        write_col03d_artifacts,
    )
except (ImportError, ModuleNotFoundError):
    build_exact_source_recovery = None
    write_col03d_artifacts = None


PREDECESSOR_SHA = "a9daa18ddfb56eaf1834ad17f329e2f2db0af72e"
TRANSPORT_ROOT = Path("archive/historical_packages/v25/transport")
INVENTORY_PATH = Path("archive/ARTEFATTI_STORICI.md")
EXPECTED_OUTPUTS = {
    "historical-package-recovery-manifest.json",
    "historical-member-manifest.json",
    "historical-derived-data-quality.json",
    "historical-recovery-reconciliation.json",
    "historical-recovery-closure.json",
}


class ExactSourceWriterTests(unittest.TestCase):
    def test_exact_source_reconstructs_all_required_members_and_real_row_counts(self):
        self.assertIsNotNone(build_exact_source_recovery, "COL-03D exact-source implementation missing")
        artifacts = build_exact_source_recovery(
            transport_root=TRANSPORT_ROOT,
            inventory_text=INVENTORY_PATH.read_text(encoding="utf-8"),
            predecessor_sha=PREDECESSOR_SHA,
        )
        self.assertEqual(set(artifacts), EXPECTED_OUTPUTS)
        members = artifacts["historical-member-manifest.json"]
        self.assertEqual(members["required_member_count"], 8)
        self.assertEqual(members["materialized_verified_count"], 8)
        self.assertEqual(
            artifacts["historical-derived-data-quality.json"]["row_counts"],
            {
                "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv": 27,
                "ABACO_TOPOLOGICO_TAV5_v11.csv": 57,
                "ABACO_TRAVI_TAV6_v23.csv": 46,
                "ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv": 46,
                "MATRICE_PILASTRI_27x5_v22.csv": 135,
            },
        )
        closure = artifacts["historical-recovery-closure.json"]
        self.assertTrue(closure["required_historical_members_materialized"])
        self.assertTrue(closure["historical_row_level_evidence_recovered"])
        self.assertFalse(closure["historical_package_repository_materialized"])
        self.assertFalse(closure["historical_package_exact_source_replayable"])
        self.assertFalse(closure["historical_evidence_identity_promoted"])

    def test_writer_persists_only_the_five_governed_json_artifacts_deterministically(self):
        self.assertIsNotNone(build_exact_source_recovery, "COL-03D exact-source implementation missing")
        self.assertIsNotNone(write_col03d_artifacts, "COL-03D exact-source writer missing")
        inventory_text = INVENTORY_PATH.read_text(encoding="utf-8")
        first = build_exact_source_recovery(
            transport_root=TRANSPORT_ROOT,
            inventory_text=inventory_text,
            predecessor_sha=PREDECESSOR_SHA,
        )
        second = build_exact_source_recovery(
            transport_root=TRANSPORT_ROOT,
            inventory_text=inventory_text,
            predecessor_sha=PREDECESSOR_SHA,
        )
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "evidence" / "cew-col03d"
            written = write_col03d_artifacts(output_root, first)
            self.assertEqual({path.name for path in written}, EXPECTED_OUTPUTS)
            self.assertEqual({path.name for path in output_root.iterdir()}, EXPECTED_OUTPUTS)
            digests_a = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(written)
            }
            written_again = write_col03d_artifacts(output_root, second)
            digests_b = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(written_again)
            }
            self.assertEqual(digests_a, digests_b)


if __name__ == "__main__":
    unittest.main()
