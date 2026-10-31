from __future__ import annotations

import unittest

from experiments.cew_col03b.predecessor import (
    build_evidence_bundle_skeleton,
    validate_col03a_predecessor,
)


QUALIFIED_SHA = "0d4a43cf02eadd2ab6f4b2641888395586c08a98"


def _occurrence(index: int) -> dict:
    row = {
        "occurrence_id": f"COL-OCC-{index:04d}",
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "source_path": "archive/documentazione_originaria/tavola 5.pdf",
        "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "page_index": 0,
        "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
        "primary_graphical_representation": {
            "kind": "FROZEN_PROPOSAL",
            "candidate_id": f"COL02-FP-{index:04d}",
            "repair_id": None,
            "bbox": {"x": 0.01 * index, "y": 0.01, "width": 0.005, "height": 0.005},
        },
        "source_proposal_ids": [f"COL02-FP-{index:04d}"],
        "dedup_state": "SINGLE_GOVERNED_LINEAGE",
        "conflict_state": "NONE",
        "exact_source_reconstructible": True,
        "lineage_complete": True,
        "documentary_label_state": "NOT_EVALUATED",
        "structural_identity_state": "NOT_EVALUATED",
        "canonical_geometry_state": "NOT_AUTHORIZED",
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_promotion_authorized": False,
    }
    if index == 1:
        row["source_proposal_ids"] = ["COL02-FP-0248", "COL02-FP-0331"]
        row["dedup_state"] = "HUMAN_EQUIVALENCE_COLLAPSED"
        row["human_equivalence_decision_ids"] = ["A"]
    if index == 2:
        row["source_proposal_ids"] = ["COL02-FP-0073", "COL02-FP-0538"]
        row["dedup_state"] = "HUMAN_EQUIVALENCE_COLLAPSED"
        row["human_equivalence_decision_ids"] = ["B"]
        row["primary_graphical_representation"] = {
            "kind": "GOVERNED_WHOLE_SYMBOL_REPAIR",
            "candidate_id": "COL02-FP-0073",
            "repair_id": "COL02-WSR-002",
            "bbox": {"x": 0.02, "y": 0.01, "width": 0.005, "height": 0.005},
        }
    return row


def _ledger() -> dict:
    return {
        "occurrence_count": 22,
        "occurrences": [_occurrence(index) for index in range(1, 23)],
        "authority": {
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


def _reconciliation() -> dict:
    return {
        "final_occurrence_count": 22,
        "conflict_count": 0,
        "missing_evidence_ids": [],
        "orphan_occurrence_ids": [],
        "bidirectional_closed_set_complete": True,
    }


def _closure() -> dict:
    return {
        "qualified_base_sha": QUALIFIED_SHA,
        "occurrence_ledger_complete": True,
        "blocking_reasons": [],
        "authority": {
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


class PredecessorContractTests(unittest.TestCase):
    def test_accepts_exact_22_occurrence_predecessor(self) -> None:
        occurrences = validate_col03a_predecessor(
            ledger=_ledger(),
            reconciliation=_reconciliation(),
            closure=_closure(),
            expected_sha=QUALIFIED_SHA,
        )
        self.assertEqual([row["occurrence_id"] for row in occurrences], [f"COL-OCC-{i:04d}" for i in range(1, 23)])
        collapsed = [row for row in occurrences if row["dedup_state"] == "HUMAN_EQUIVALENCE_COLLAPSED"]
        self.assertEqual(len(collapsed), 2)
        self.assertEqual(collapsed[0]["human_equivalence_decision_ids"], ["A"])
        self.assertEqual(collapsed[1]["human_equivalence_decision_ids"], ["B"])

    def test_rejects_authority_drift(self) -> None:
        ledger = _ledger()
        ledger["authority"]["support_identity_authorized"] = True
        with self.assertRaisesRegex(ValueError, "authority drift"):
            validate_col03a_predecessor(
                ledger=ledger,
                reconciliation=_reconciliation(),
                closure=_closure(),
                expected_sha=QUALIFIED_SHA,
            )

    def test_rejects_noncontiguous_occurrence_ids(self) -> None:
        ledger = _ledger()
        ledger["occurrences"][5]["occurrence_id"] = "COL-OCC-9999"
        with self.assertRaisesRegex(ValueError, "occurrence ID drift"):
            validate_col03a_predecessor(
                ledger=ledger,
                reconciliation=_reconciliation(),
                closure=_closure(),
                expected_sha=QUALIFIED_SHA,
            )

    def test_bundle_skeleton_has_all_channels_and_closed_authority(self) -> None:
        bundle = build_evidence_bundle_skeleton(_occurrence(1), col03a_ledger_digest="abc123")
        for key in (
            "internal_text_evidence",
            "intersecting_text_evidence",
            "nearby_text_evidence",
            "high_resolution_read_evidence",
            "callout_evidence",
            "local_topology_evidence",
            "cross_document_evidence",
        ):
            self.assertEqual(bundle[key], [])
            self.assertIn(key, bundle["missing_channels"])
        self.assertEqual(bundle["documentary_evidence_state"], "NOT_EVALUATED")
        self.assertEqual(bundle["documentary_identity_resolution_state"], "UNRESOLVED")
        self.assertFalse(bundle["support_identity_authorized"])
        self.assertFalse(bundle["structural_identity_authorized"])
        self.assertFalse(bundle["canonical_write_authorized"])


if __name__ == "__main__":
    unittest.main()
