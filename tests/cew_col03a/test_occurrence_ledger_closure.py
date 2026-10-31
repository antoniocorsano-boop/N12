from __future__ import annotations

import copy
import random
import unittest


SOURCE = {
    "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
    "source_path": "archive/documentazione_originaria/tavola 5.pdf",
    "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
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


def _group(candidate_id: str, *, x: float, y: float, evidence_id: str) -> dict:
    bbox = {"x": x, "y": y, "width": 0.02, "height": 0.03}
    return {
        "candidate_id": candidate_id,
        "source_proposal_ids": [candidate_id],
        "evidence_ids": [evidence_id],
        "evidence_classes": ["PROTOTYPE_CONFIRMED"],
        "graphical_decisions": ["COLUMN_FOOTPRINT_CONFIRMED"],
        "discovery_paths": ["HUMAN_PROTOTYPE_REVIEW"],
        "human_review_receipts": ["receipt.json"],
        "repair_lineage": [],
        "human_added_point_event_ids": [],
        "lineage": [{"fixture": evidence_id}],
        "anchor_bbox": dict(bbox),
        "normalized_bbox": dict(bbox),
        "primary_graphical_representation": {
            "kind": "FROZEN_PROPOSAL",
            "candidate_id": candidate_id,
            "repair_id": None,
            "bbox": dict(bbox),
        },
        "source_geometry_ref": candidate_id,
        **SOURCE,
        "exact_source_reconstructible": True,
        "lineage_complete": True,
        "dedup_state": "SINGLE_GOVERNED_LINEAGE",
        "conflict_state": "NONE",
    }


def _evidence(candidate_id: str, evidence_id: str) -> dict:
    return {
        "evidence_id": evidence_id,
        "candidate_id": candidate_id,
        "evidence_class": "PROTOTYPE_CONFIRMED",
    }


class OccurrenceLedgerClosureTests(unittest.TestCase):
    @staticmethod
    def _module():
        from experiments.cew_col03a import occurrence_ledger

        return occurrence_ledger

    def test_assign_occurrence_ids_is_stable_under_input_shuffle(self):
        module = self._module()
        groups = [
            _group("COL02-FP-0003", x=0.40, y=0.20, evidence_id="E3"),
            _group("COL02-FP-0001", x=0.10, y=0.10, evidence_id="E1"),
            _group("COL02-FP-0002", x=0.30, y=0.10, evidence_id="E2"),
        ]
        shuffled = list(groups)
        random.Random(42).shuffle(shuffled)

        first = module.assign_occurrence_ids(groups)
        second = module.assign_occurrence_ids(shuffled)
        self.assertEqual(first, second)
        self.assertEqual([row["occurrence_id"] for row in first], ["COL-OCC-0001", "COL-OCC-0002", "COL-OCC-0003"])
        self.assertEqual([row["candidate_id"] for row in first], ["COL02-FP-0001", "COL02-FP-0002", "COL02-FP-0003"])

    def test_order_depends_on_anchor_not_repaired_primary_or_structural_fields(self):
        module = self._module()
        first = _group("COL02-FP-0010", x=0.20, y=0.10, evidence_id="EA")
        second = _group("COL02-FP-0011", x=0.40, y=0.10, evidence_id="EB")
        baseline = module.assign_occurrence_ids([second, first])

        mutated = copy.deepcopy([second, first])
        mutated[1]["primary_graphical_representation"]["bbox"] = {"x": 0.90, "y": 0.90, "width": 0.02, "height": 0.03}
        mutated[1]["normalized_bbox"] = dict(mutated[1]["primary_graphical_representation"]["bbox"])
        mutated[1]["support_number"] = 999
        mutated[1]["ocr_token"] = "P999"
        mutated[1]["family"] = "FORBIDDEN_SORT_INPUT"
        mutated[1]["canonical_node_id"] = "NODE-57"
        mutated_result = module.assign_occurrence_ids(mutated)

        self.assertEqual(
            [(row["occurrence_id"], row["candidate_id"]) for row in baseline],
            [(row["occurrence_id"], row["candidate_id"]) for row in mutated_result],
        )

    def test_ledger_sets_neutral_authority_defaults(self):
        module = self._module()
        occurrences = module.assign_occurrence_ids([_group("COL02-FP-0001", x=0.1, y=0.1, evidence_id="E1")])
        ledger = module.build_occurrence_ledger(records=occurrences, source=SOURCE)
        self.assertEqual(ledger["schema_id"], "CEW_COL03A_GOVERNED_COLUMN_OCCURRENCE_LEDGER")
        self.assertEqual(ledger["schema_version"], 1)
        self.assertEqual(ledger["occurrence_count"], 1)
        row = ledger["occurrences"][0]
        self.assertEqual(row["documentary_label_state"], "NOT_EVALUATED")
        self.assertEqual(row["structural_identity_state"], "NOT_EVALUATED")
        self.assertEqual(row["canonical_geometry_state"], "NOT_AUTHORIZED")
        self.assertFalse(row["canonical_write_authorized"])
        self.assertFalse(row["g2c_promotion_authorized"])
        self.assertFalse(row["g3_promotion_authorized"])

    def test_reconciliation_is_bidirectional_and_has_no_orphans(self):
        module = self._module()
        occurrences = module.assign_occurrence_ids([
            _group("COL02-FP-0001", x=0.1, y=0.1, evidence_id="E1"),
            _group("COL02-FP-0002", x=0.2, y=0.1, evidence_id="E2"),
        ])
        evidence = [_evidence("COL02-FP-0002", "E2"), _evidence("COL02-FP-0001", "E1")]
        report = module.build_reconciliation_report(evidence_items=evidence, occurrences=occurrences, conflicts=[])
        self.assertEqual(report["schema_id"], "CEW_COL03A_COLUMN_OCCURRENCE_RECONCILIATION")
        self.assertEqual(report["final_occurrence_count"], 2)
        self.assertEqual(report["orphan_occurrence_ids"], [])
        self.assertEqual(report["missing_evidence_ids"], [])
        self.assertEqual(report["conflicts"], [])
        self.assertEqual(set(report["evidence_to_occurrence"]), {"E1", "E2"})
        self.assertEqual(set(report["occurrence_to_evidence"]), {"COL-OCC-0001", "COL-OCC-0002"})

    def test_clean_closed_set_closes_and_authority_remains_false(self):
        module = self._module()
        occurrences = module.assign_occurrence_ids([_group("COL02-FP-0001", x=0.1, y=0.1, evidence_id="E1")])
        ledger = module.build_occurrence_ledger(records=occurrences, source=SOURCE)
        report = module.build_reconciliation_report(
            evidence_items=[_evidence("COL02-FP-0001", "E1")],
            occurrences=occurrences,
            conflicts=[],
        )
        col02_closure = {"occurrence_coverage_complete": True, "authority": dict(CLOSED_AUTHORITY)}
        closure = module.build_ledger_closure(
            ledger=ledger,
            reconciliation=report,
            col02_closure=col02_closure,
            qualified_base_sha="0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4",
        )
        self.assertEqual(closure["schema_id"], "CEW_COL03A_COLUMN_OCCURRENCE_LEDGER_CLOSURE")
        self.assertTrue(closure["occurrence_ledger_complete"])
        self.assertEqual(closure["authority"], CLOSED_AUTHORITY)

    def test_conflict_or_bad_reconstruction_keeps_closure_false(self):
        module = self._module()
        base_group = _group("COL02-FP-0001", x=0.1, y=0.1, evidence_id="E1")
        occurrences = module.assign_occurrence_ids([base_group])
        ledger = module.build_occurrence_ledger(records=occurrences, source=SOURCE)
        report = module.build_reconciliation_report(
            evidence_items=[_evidence("COL02-FP-0001", "E1")],
            occurrences=occurrences,
            conflicts=[{"conflict_state": "AMBIGUOUS_DUPLICATE", "candidate_ids": ["A", "B"]}],
        )
        col02_closure = {"occurrence_coverage_complete": True, "authority": dict(CLOSED_AUTHORITY)}
        self.assertFalse(module.build_ledger_closure(
            ledger=ledger,
            reconciliation=report,
            col02_closure=col02_closure,
            qualified_base_sha="0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4",
        )["occurrence_ledger_complete"])

        broken_occurrences = copy.deepcopy(occurrences)
        broken_occurrences[0]["exact_source_reconstructible"] = False
        broken_ledger = module.build_occurrence_ledger(records=broken_occurrences, source=SOURCE)
        clean_report = module.build_reconciliation_report(
            evidence_items=[_evidence("COL02-FP-0001", "E1")],
            occurrences=broken_occurrences,
            conflicts=[],
        )
        self.assertFalse(module.build_ledger_closure(
            ledger=broken_ledger,
            reconciliation=clean_report,
            col02_closure=col02_closure,
            qualified_base_sha="0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4",
        )["occurrence_ledger_complete"])


if __name__ == "__main__":
    unittest.main()
