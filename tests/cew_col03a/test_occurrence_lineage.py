from __future__ import annotations

import copy
import unittest


SOURCE_FIELDS = {
    "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
    "source_path": "archive/documentazione_originaria/tavola 5.pdf",
    "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    "page_id": "CEW-N12-PAGE-TAV05S-P001",
    "page_index": 0,
    "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
}


def _record(
    candidate_id: str,
    bbox: dict[str, float],
    *,
    evidence_id: str,
    decision: str = "COLUMN_FOOTPRINT_CONFIRMED",
    discovery_path: str = "HUMAN_PROTOTYPE_REVIEW",
    receipt: str = "receipt-a.json",
    repair_id: str | None = None,
    primary_bbox: dict[str, float] | None = None,
    human_event_ids: list[str] | None = None,
) -> dict:
    primary = primary_bbox or bbox
    return {
        "evidence_id": evidence_id,
        "candidate_id": candidate_id,
        "evidence_class": "REPAIRED_SUCCESSOR_CONFIRMED" if repair_id else "PROTOTYPE_CONFIRMED",
        "graphical_decision": decision,
        "discovery_path": discovery_path,
        "human_review_receipt": receipt,
        "repair_id": repair_id,
        "human_added_point_event_ids": list(human_event_ids or []),
        "lineage": {"fixture": evidence_id},
        "anchor_bbox": dict(bbox),
        "normalized_bbox": dict(primary),
        "primary_graphical_representation": {
            "kind": "GOVERNED_WHOLE_SYMBOL_REPAIR" if repair_id else "FROZEN_PROPOSAL",
            "candidate_id": candidate_id,
            "repair_id": repair_id,
            "bbox": dict(primary),
        },
        "source_geometry_ref": candidate_id,
        **SOURCE_FIELDS,
        "exact_source_reconstructible": True,
        "lineage_complete": True,
    }


class StrongLineageReconciliationTests(unittest.TestCase):
    @staticmethod
    def _module():
        from experiments.cew_col03a import occurrence_ledger

        return occurrence_ledger

    def test_same_frozen_candidate_collapses_and_retains_all_governed_paths(self):
        module = self._module()
        bbox = {"x": 0.10, "y": 0.20, "width": 0.02, "height": 0.03}
        first = _record("COL02-FP-0363", bbox, evidence_id="E1")
        second = _record(
            "COL02-FP-0363",
            bbox,
            evidence_id="E2",
            decision="PILASTRO",
            discovery_path="RESIDUAL_MOBILE_DIRECT",
            receipt="receipt-b.json",
        )

        groups = module.collapse_strong_lineage([second, first])
        self.assertEqual(len(groups), 1)
        group = groups[0]
        self.assertEqual(group["candidate_id"], "COL02-FP-0363")
        self.assertEqual(group["evidence_ids"], ["E1", "E2"])
        self.assertEqual(group["discovery_paths"], ["HUMAN_PROTOTYPE_REVIEW", "RESIDUAL_MOBILE_DIRECT"])
        self.assertEqual(group["human_review_receipts"], ["receipt-a.json", "receipt-b.json"])
        self.assertEqual(group["source_proposal_ids"], ["COL02-FP-0363"])
        self.assertEqual(group["conflict_state"], "NONE")
        self.assertEqual(group["dedup_state"], "STRONG_LINEAGE_COLLAPSED")

    def test_repair_lineage_remains_same_occurrence_and_repair_representation_wins(self):
        module = self._module()
        anchor = {"x": 0.30, "y": 0.40, "width": 0.018, "height": 0.024}
        repaired = {"x": 0.295, "y": 0.395, "width": 0.030, "height": 0.036}
        base = _record("COL02-FP-0252", anchor, evidence_id="E1")
        repair = _record(
            "COL02-FP-0252",
            anchor,
            evidence_id="E2",
            decision="PASS",
            discovery_path="REFRAME_CONFIRMATION",
            receipt="repair-review.json",
            repair_id="COL02-WSR-001",
            primary_bbox=repaired,
        )

        groups = module.collapse_strong_lineage([base, repair])
        self.assertEqual(len(groups), 1)
        group = groups[0]
        self.assertEqual(group["anchor_bbox"], anchor)
        self.assertEqual(group["repair_lineage"], ["COL02-WSR-001"])
        self.assertEqual(group["primary_graphical_representation"]["kind"], "GOVERNED_WHOLE_SYMBOL_REPAIR")
        self.assertEqual(group["primary_graphical_representation"]["bbox"], repaired)
        self.assertEqual(group["source_proposal_ids"], ["COL02-FP-0252"])

    def test_geometry_overlap_never_auto_merges_distinct_candidate_ids(self):
        module = self._module()
        a = _record(
            "COL02-FP-0100",
            {"x": 0.10, "y": 0.10, "width": 0.10, "height": 0.10},
            evidence_id="A",
        )
        b = _record(
            "COL02-FP-0101",
            {"x": 0.105, "y": 0.105, "width": 0.095, "height": 0.095},
            evidence_id="B",
        )
        groups = module.collapse_strong_lineage([a, b])
        self.assertEqual(len(groups), 2)

        conflicts = module.detect_ambiguous_duplicates(groups, overlap_threshold=0.90)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["conflict_state"], "AMBIGUOUS_DUPLICATE")
        self.assertEqual(conflicts[0]["candidate_ids"], ["COL02-FP-0100", "COL02-FP-0101"])
        self.assertGreaterEqual(conflicts[0]["overlap_of_smaller_bbox"], 0.90)

    def test_adjacent_candidates_remain_independent_without_conflict(self):
        module = self._module()
        a = _record(
            "COL02-FP-0200",
            {"x": 0.10, "y": 0.10, "width": 0.05, "height": 0.05},
            evidence_id="A",
        )
        b = _record(
            "COL02-FP-0201",
            {"x": 0.16, "y": 0.10, "width": 0.05, "height": 0.05},
            evidence_id="B",
        )
        groups = module.collapse_strong_lineage([a, b])
        self.assertEqual(module.detect_ambiguous_duplicates(groups), [])
        self.assertEqual([row["conflict_state"] for row in groups], ["NONE", "NONE"])

    def test_contradictory_governed_decisions_fail_closed_in_same_lineage_group(self):
        module = self._module()
        bbox = {"x": 0.20, "y": 0.30, "width": 0.04, "height": 0.05}
        positive = _record("COL02-FP-0300", bbox, evidence_id="P")
        negative = _record(
            "COL02-FP-0300",
            bbox,
            evidence_id="N",
            decision="NOT_COLUMN",
            discovery_path="CONTRADICTORY_FIXTURE",
            receipt="negative.json",
        )
        group = module.collapse_strong_lineage([positive, negative])[0]
        self.assertEqual(group["conflict_state"], "CONTRADICTORY_GRAPHICAL_DECISIONS")
        self.assertEqual(group["graphical_decisions"], ["COLUMN_FOOTPRINT_CONFIRMED", "NOT_COLUMN"])

    def test_smaller_bbox_overlap_is_intersection_over_smaller_area(self):
        module = self._module()
        outer = {"x": 0.10, "y": 0.10, "width": 0.20, "height": 0.20}
        inner = {"x": 0.12, "y": 0.12, "width": 0.05, "height": 0.05}
        self.assertAlmostEqual(module.smaller_bbox_overlap(outer, inner), 1.0)


if __name__ == "__main__":
    unittest.main()
