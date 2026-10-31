from __future__ import annotations

import unittest


SOURCE = {
    "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
    "source_path": "archive/documentazione_originaria/tavola 5.pdf",
    "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    "page_id": "CEW-N12-PAGE-TAV05S-P001",
    "page_index": 0,
    "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
}


def _group(candidate_id: str, evidence_id: str, bbox: dict[str, float], *, repair_id: str | None = None) -> dict:
    primary = {
        "kind": "GOVERNED_WHOLE_SYMBOL_REPAIR" if repair_id else "FROZEN_PROPOSAL",
        "candidate_id": candidate_id,
        "repair_id": repair_id,
        "bbox": dict(bbox),
    }
    return {
        "candidate_id": candidate_id,
        "source_proposal_ids": [candidate_id],
        "evidence_ids": [evidence_id],
        "evidence_classes": ["REPAIRED_SUCCESSOR_CONFIRMED" if repair_id else "PROTOTYPE_GUIDED_CONFIRMED"],
        "graphical_decisions": ["PASS" if repair_id else "COLUMN_FOOTPRINT_CONFIRMED"],
        "discovery_paths": ["REFRAME_CONFIRMATION" if repair_id else "PROTOTYPE_GUIDED_HUMAN_REVIEW"],
        "human_review_receipts": ["fixture.json"],
        "repair_lineage": [repair_id] if repair_id else [],
        "human_added_point_event_ids": [],
        "lineage": [{"fixture": True}],
        "anchor_bbox": dict(bbox),
        "normalized_bbox": dict(bbox),
        "primary_graphical_representation": primary,
        "source_geometry_ref": candidate_id,
        "exact_source_reconstructible": True,
        "lineage_complete": True,
        "dedup_state": "SINGLE_GOVERNED_LINEAGE",
        "conflict_state": "NONE",
        **SOURCE,
    }


def _receipt() -> dict:
    return {
        "schema_id": "CEW_COL03A_OCCURRENCE_EQUIVALENCE_HUMAN_REVIEW",
        "schema_version": 1,
        "status": "HUMAN_GRAPHICAL_EQUIVALENCE_REVIEW_COMPLETE",
        "receipt_ref": "governance/cew-col03a/COL03A_OCCURRENCE_EQUIVALENCE_HUMAN_REVIEW_v1.json",
        "human_decision": {
            "decisions": [
                {
                    "decision_id": "A",
                    "candidate_ids": ["COL02-FP-0248", "COL02-FP-0331"],
                    "decision": "SAME_OCCURRENCE",
                    "scope": "GRAPHICAL_OCCURRENCE_EQUIVALENCE_ONLY",
                },
                {
                    "decision_id": "B",
                    "candidate_ids": ["COL02-FP-0073", "COL02-FP-0538"],
                    "decision": "SAME_OCCURRENCE",
                    "scope": "GRAPHICAL_OCCURRENCE_EQUIVALENCE_ONLY",
                },
            ]
        },
        "authority": {
            "graphical_occurrence_equivalence_authorized": True,
            "support_identity_authorized": False,
            "text_identity_binding_authorized": False,
            "family_assignment_authorized": False,
            "section_assignment_authorized": False,
            "fixed_line_assignment_authorized": False,
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "g2c_promotion_authorized": False,
            "g3_authorized": False,
            "merge_authorized": False,
        },
    }


class HumanOccurrenceEquivalenceTests(unittest.TestCase):
    def test_confirmed_same_occurrence_collapses_only_reviewed_pairs_and_preserves_all_lineage(self):
        from experiments.cew_col03a.occurrence_ledger import (
            apply_human_occurrence_equivalence,
            build_occurrence_ledger,
        )

        groups = [
            _group("COL02-FP-0248", "E:A1", {"x": 0.10, "y": 0.10, "width": 0.02, "height": 0.02}),
            _group("COL02-FP-0331", "E:A2", {"x": 0.095, "y": 0.095, "width": 0.03, "height": 0.03}),
            _group("COL02-FP-0073", "E:B1", {"x": 0.50, "y": 0.50, "width": 0.02, "height": 0.02}, repair_id="COL02-WSR-002"),
            _group("COL02-FP-0538", "E:B2", {"x": 0.495, "y": 0.495, "width": 0.03, "height": 0.03}),
        ]

        collapsed = apply_human_occurrence_equivalence(groups=groups, receipt=_receipt())
        self.assertEqual(len(collapsed), 2)
        source_sets = {frozenset(row["source_proposal_ids"]): row for row in collapsed}
        self.assertEqual(set(source_sets), {
            frozenset({"COL02-FP-0248", "COL02-FP-0331"}),
            frozenset({"COL02-FP-0073", "COL02-FP-0538"}),
        })
        self.assertEqual(set(source_sets[frozenset({"COL02-FP-0248", "COL02-FP-0331"})]["evidence_ids"]), {"E:A1", "E:A2"})
        b = source_sets[frozenset({"COL02-FP-0073", "COL02-FP-0538"})]
        self.assertEqual(set(b["evidence_ids"]), {"E:B1", "E:B2"})
        self.assertEqual(b["primary_graphical_representation"]["kind"], "GOVERNED_WHOLE_SYMBOL_REPAIR")
        self.assertEqual(b["primary_graphical_representation"]["repair_id"], "COL02-WSR-002")
        for row in collapsed:
            self.assertEqual(row["dedup_state"], "HUMAN_EQUIVALENCE_COLLAPSED")
            self.assertEqual(row["conflict_state"], "NONE")
            self.assertEqual(row["human_equivalence_decision_ids"], ["A"] if "COL02-FP-0248" in row["source_proposal_ids"] else ["B"])

        ledger = build_occurrence_ledger(records=collapsed, source=SOURCE)
        self.assertEqual(ledger["occurrence_count"], 2)
        self.assertEqual(ledger["conflict_count"], 0)

    def test_reconciliation_accepts_source_candidate_when_it_is_preserved_in_merged_source_proposal_ids(self):
        from experiments.cew_col03a.occurrence_ledger import build_reconciliation_report

        evidence = [
            {"evidence_id": "E1", "candidate_id": "COL02-FP-0248", "evidence_class": "PROTOTYPE_GUIDED_CONFIRMED"},
            {"evidence_id": "E2", "candidate_id": "COL02-FP-0331", "evidence_class": "PROTOTYPE_GUIDED_CONFIRMED"},
        ]
        occurrences = [
            {
                "occurrence_id": "COL-OCC-0001",
                "candidate_id": "COL02-FP-0248",
                "source_proposal_ids": ["COL02-FP-0248", "COL02-FP-0331"],
                "evidence_ids": ["E1", "E2"],
            }
        ]

        report = build_reconciliation_report(evidence_items=evidence, occurrences=occurrences, conflicts=[])
        self.assertTrue(report["bidirectional_closed_set_complete"])
        self.assertEqual(report["conflict_count"], 0)
        self.assertEqual(report["missing_evidence_ids"], [])
        self.assertEqual(report["orphan_occurrence_ids"], [])
        self.assertEqual(report["evidence_to_occurrence"], {"E1": "COL-OCC-0001", "E2": "COL-OCC-0001"})


if __name__ == "__main__":
    unittest.main()
