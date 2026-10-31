from __future__ import annotations

import unittest


SOURCE = {
    "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
    "source_path": "archive/documentazione_originaria/tavola 5.pdf",
    "sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    "page_id": "CEW-N12-PAGE-TAV05S-P001",
    "page_index": 0,
    "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
}

CLOSED_AUTHORITY = {
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
}


def _proposals() -> dict:
    candidates = []
    for index in range(1, 612):
        candidates.append(
            {
                "candidate_id": f"COL02-FP-{index:04d}",
                "bbox": {
                    "x": ((index - 1) % 50) * 0.015,
                    "y": ((index - 1) // 50) * 0.02,
                    "width": 0.01,
                    "height": 0.012,
                },
            }
        )
    candidates[247]["bbox"] = {"x": 0.10, "y": 0.10, "width": 0.02, "height": 0.02}
    candidates[330]["bbox"] = {"x": 0.095, "y": 0.095, "width": 0.03, "height": 0.03}
    return {"candidate_count": 611, "candidates": candidates}


def _evidence(candidate_id: str, evidence_id: str) -> dict:
    return {
        "evidence_id": evidence_id,
        "candidate_id": candidate_id,
        "evidence_class": "PROTOTYPE_GUIDED_CONFIRMED",
        "graphical_decision": "COLUMN_FOOTPRINT_CONFIRMED",
        "discovery_path": "PROTOTYPE_GUIDED_HUMAN_REVIEW",
        "human_review_receipt": "fixture.json",
        "repair_id": None,
        "human_added_point_event_ids": [],
        "lineage": {"fixture": True},
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
                }
            ]
        },
        "authority": {"graphical_occurrence_equivalence_authorized": True, **CLOSED_AUTHORITY},
    }


class ExactSourceHumanEquivalenceTests(unittest.TestCase):
    def test_build_pipeline_applies_governed_equivalence_without_losing_input_evidence(self):
        from experiments.cew_col03a.exact_source import build_col03a_from_payloads

        ledger, reconciliation, closure = build_col03a_from_payloads(
            evidence_items=[
                _evidence("COL02-FP-0248", "E1"),
                _evidence("COL02-FP-0331", "E2"),
            ],
            proposals=_proposals(),
            repair_manifest={"repairs": []},
            col02_closure={"occurrence_coverage_complete": True, "authority": dict(CLOSED_AUTHORITY)},
            source=SOURCE,
            equivalence_receipt=_receipt(),
        )

        self.assertEqual(ledger["occurrence_count"], 1)
        self.assertEqual(ledger["conflict_count"], 0)
        self.assertEqual(reconciliation["input_evidence_count"], 2)
        self.assertEqual(reconciliation["final_occurrence_count"], 1)
        self.assertEqual(reconciliation["missing_evidence_ids"], [])
        self.assertEqual(set(ledger["occurrences"][0]["source_proposal_ids"]), {"COL02-FP-0248", "COL02-FP-0331"})
        self.assertTrue(closure["occurrence_ledger_complete"])


if __name__ == "__main__":
    unittest.main()
