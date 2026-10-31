from __future__ import annotations

import unittest


class ReconciliationConflictSeparationTests(unittest.TestCase):
    def test_geometry_conflict_does_not_make_bidirectional_mapping_incomplete(self):
        from experiments.cew_col03a.occurrence_ledger import build_reconciliation_report

        evidence = [
            {"evidence_id": "E1", "candidate_id": "COL02-FP-0001", "evidence_class": "PROTOTYPE_CONFIRMED"},
            {"evidence_id": "E2", "candidate_id": "COL02-FP-0002", "evidence_class": "PROTOTYPE_CONFIRMED"},
        ]
        occurrences = [
            {
                "occurrence_id": "COL-OCC-0001",
                "candidate_id": "COL02-FP-0001",
                "evidence_ids": ["E1"],
            },
            {
                "occurrence_id": "COL-OCC-0002",
                "candidate_id": "COL02-FP-0002",
                "evidence_ids": ["E2"],
            },
        ]
        conflicts = [
            {
                "conflict_state": "AMBIGUOUS_DUPLICATE",
                "candidate_ids": ["COL02-FP-0001", "COL02-FP-0002"],
                "overlap_of_smaller_bbox": 0.95,
                "resolution": "HUMAN_REVIEW_REQUIRED",
            }
        ]

        report = build_reconciliation_report(
            evidence_items=evidence,
            occurrences=occurrences,
            conflicts=conflicts,
        )

        self.assertEqual(report["missing_source_evidence_ids"], [])
        self.assertEqual(report["orphan_occurrence_ids"], [])
        self.assertEqual(report["duplicate_source_evidence_ids"], [])
        self.assertEqual(report["duplicate_occurrence_claim_evidence_ids"], [])
        self.assertTrue(report["bidirectional_closed_set_complete"])
        self.assertEqual(report["conflict_count"], 1)
        self.assertEqual(report["conflicts"][0]["conflict_state"], "AMBIGUOUS_DUPLICATE")


if __name__ == "__main__":
    unittest.main()
