from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

try:
    from experiments.cew_col03e.predecessor import load_qualified_predecessor_snapshots
except (ImportError, ModuleNotFoundError):
    load_qualified_predecessor_snapshots = None


COL03B_ROOT = Path("archive/qualified_evidence/col03b")
COL03C_ROOT = Path("archive/qualified_evidence/col03c")


class QualifiedPredecessorSnapshotTests(unittest.TestCase):
    def test_exact_qualified_snapshots_are_repository_replayable(self):
        self.assertIsNotNone(
            load_qualified_predecessor_snapshots,
            "COL-03E qualified predecessor snapshot loader missing",
        )
        snapshots = load_qualified_predecessor_snapshots(COL03B_ROOT, COL03C_ROOT)

        self.assertEqual(
            snapshots["col03b_manifest"]["source_sha"],
            "cfd9382b703d0a974daf63c23dc2b6d3d81eadad",
        )
        self.assertEqual(snapshots["col03b_manifest"]["workflow_run_id"], 41239465886)
        self.assertEqual(snapshots["col03b_manifest"]["artifact_id"], 13057251710)
        self.assertEqual(
            snapshots["col03b_manifest"]["artifact_digest"],
            "sha256:aaddc342e81983bbbd4f164a8e5c70dcbc14de5626bfc821ba7489b576821391",
        )

        self.assertEqual(
            snapshots["col03c_manifest"]["source_sha"],
            "a9daa18ddfb56eaf1834ad17f329e2f2db0af72e",
        )
        self.assertEqual(snapshots["col03c_manifest"]["workflow_run_id"], 41244244236)
        self.assertEqual(snapshots["col03c_manifest"]["artifact_id"], 13058716773)
        self.assertEqual(
            snapshots["col03c_manifest"]["artifact_digest"],
            "sha256:468108dc107d813e9d4759a208560b566d7395b2db6eedf07787375238a91a2f",
        )

    def test_qualified_snapshot_file_digests_are_frozen(self):
        self.assertIsNotNone(load_qualified_predecessor_snapshots)
        snapshots = load_qualified_predecessor_snapshots(COL03B_ROOT, COL03C_ROOT)

        self.assertEqual(
            snapshots["col03b_manifest"]["files"],
            {
                "documentary-identity-evidence-closure.json": "a7daadcb6395951f6a478f48c2e4c90b98ebadcf4824058562a7d9f9fb59239b",
                "documentary-identity-evidence-ledger.json": "058af83c8df0f9da1a9b1308adeb85f4162055163ce02c30739cfb93ff59e8cb",
                "documentary-identity-hypotheses.json": "b5d71542cdc57384e49c2e5f66068dba492bf1a4d1e68b0228586fadd0b6361c",
                "documentary-identity-reconciliation.json": "2904a28f6762c8db5623f893bf97959c53a508b6388a55478b030ad3c9e07e3b",
            },
        )
        self.assertEqual(
            snapshots["col03c_manifest"]["files"],
            {
                "cross-document-evidence-closure.json": "beb6d4a904e5340113d994601c94e7b53e5c3ac162d520a8f5be922b1e11e903",
                "cross-document-evidence-ledger.json": "16bbb69f7650468d8530fa7d839c34082f302f972a100b32fe5b8ff7fa0812af",
                "cross-document-reconciliation.json": "e6c9aff757dd54be66748af222a93175bda1978ec7dc68ada33fa72133edc352",
                "derived-reference-quality.json": "dc8a6d32d4bcfd3491647023e26c52ff01c9ef3cf42200a4706ab4e103602eca",
                "source-materialization-manifest.json": "86534627c796e5414c626eb4d4ccfc7a8ad04e72f886471589e18598d5ec41b0",
            },
        )

    def test_real_candidate_distribution_is_preserved(self):
        self.assertIsNotNone(load_qualified_predecessor_snapshots)
        snapshots = load_qualified_predecessor_snapshots(COL03B_ROOT, COL03C_ROOT)
        col03b = snapshots["col03b_ledger"]
        col03c = snapshots["col03c_ledger"]

        self.assertEqual(col03b["occurrence_count"], 22)
        self.assertEqual(col03c["occurrence_count"], 22)

        b_distribution = Counter(len(row.get("hypotheses", [])) for row in col03b["occurrences"])
        self.assertEqual(b_distribution, Counter({0: 20, 1: 2}))
        candidate_rows = {
            row["occurrence_id"]: row["hypotheses"][0]["candidate_value"]
            for row in col03b["occurrences"]
            if row.get("hypotheses")
        }
        self.assertEqual(candidate_rows, {"COL-OCC-0001": "4", "COL-OCC-0015": "30"})

        self.assertTrue(all(row["tav07_match_state"] == "EVALUATED_NO_MATCH" for row in col03c["occurrences"]))
        self.assertTrue(all(row["hypotheses"] == [] for row in col03c["occurrences"]))
        self.assertTrue(all(row["cross_document_identity_resolved"] is False for row in col03c["occurrences"]))

    def test_snapshot_authority_drift_fails_closed(self):
        self.assertIsNotNone(load_qualified_predecessor_snapshots)
        snapshots = load_qualified_predecessor_snapshots(COL03B_ROOT, COL03C_ROOT)
        for occurrence in snapshots["col03c_ledger"]["occurrences"]:
            self.assertFalse(occurrence["support_identity_authorized"])
            self.assertFalse(occurrence["structural_identity_authorized"])
            self.assertFalse(occurrence["canonical_geometry_authorized"])
            self.assertFalse(occurrence["canonical_write_authorized"])
            self.assertFalse(occurrence["merge_authorized"])


if __name__ == "__main__":
    unittest.main()
