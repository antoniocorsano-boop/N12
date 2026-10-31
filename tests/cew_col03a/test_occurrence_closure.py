from __future__ import annotations

import copy
import json
import unittest


BASE_SHA = "0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4"
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


def _group(
    candidate_id: str,
    *,
    x: float,
    y: float,
    width: float = 0.02,
    height: float = 0.03,
    evidence_ids: list[str] | None = None,
    primary_bbox: dict[str, float] | None = None,
) -> dict:
    anchor = {"x": x, "y": y, "width": width, "height": height}
    primary = primary_bbox or anchor
    return {
        "candidate_id": candidate_id,
        "source_proposal_ids": [candidate_id],
        "evidence_ids": list(evidence_ids or [f"E:{candidate_id}"]),
        "evidence_classes": ["PROTOTYPE_CONFIRMED"],
        "graphical_decisions": ["COLUMN_FOOTPRINT_CONFIRMED"],
        "discovery_paths": ["HUMAN_PROTOTYPE_REVIEW"],
        "human_review_receipts": ["fixture.json"],
        "repair_lineage": [],
        "human_added_point_event_ids": [],
        "lineage": [{"fixture": candidate_id}],
        "anchor_bbox": anchor,
        "normalized_bbox": dict(primary),
        "primary_graphical_representation": {
            "kind": "FROZEN_PROPOSAL",
            "candidate_id": candidate_id,
            "repair_id": None,
            "bbox": dict(primary),
        },
        "source_geometry_ref": candidate_id,
        **SOURCE,
        "exact_source_reconstructible": True,
        "lineage_complete": True,
        "dedup_state": "SINGLE_GOVERNED_LINEAGE",
        "conflict_state": "NONE",
    }


def _evidence(evidence_id: str, candidate_id: str, evidence_class: str = "PROTOTYPE_CONFIRMED") -> dict:
    return {
        "evidence_id": evidence_id,
        "candidate_id": candidate_id,
        "evidence_class": evidence_class,
        "graphical_decision": "COLUMN_FOOTPRINT_CONFIRMED",
        "discovery_path": "FIXTURE",
        "human_review_receipt": "fixture.json",
        "repair_id": None,
        "human_added_point_event_ids": [],
        "lineage": {"fixture": evidence_id},
    }


def _col02_closure() -> dict:
    return {
        "schema_id": "CEW_COL02_OCCURRENCE_COVERAGE_CLOSURE",
        "schema_version": 1,
        "occurrence_coverage_complete": True,
        "proposal_count": 611,
        "original_proposal_id_space_immutable": True,
        "authority": dict(CLOSED_AUTHORITY),
    }


class DeterministicOccurrenceIdTests(unittest.TestCase):
    @staticmethod
    def _module():
        from experiments.cew_col03a import occurrence_ledger

        return occurrence_ledger

    def test_shuffled_groups_produce_same_contiguous_occurrence_ids(self):
        module = self._module()
        groups = [
            _group("COL02-FP-0003", x=0.30, y=0.20),
            _group("COL02-FP-0001", x=0.40, y=0.10),
            _group("COL02-FP-0002", x=0.20, y=0.10),
        ]
        first = module.assign_occurrence_ids(groups)
        second = module.assign_occurrence_ids(list(reversed(groups)))
        self.assertEqual(first, second)
        self.assertEqual(
            [(row["occurrence_id"], row["candidate_id"]) for row in first],
            [
                ("COL-OCC-0001", "COL02-FP-0002"),
                ("COL-OCC-0002", "COL02-FP-0001"),
                ("COL-OCC-0003", "COL02-FP-0003"),
            ],
        )

    def test_repaired_primary_geometry_does_not_change_occurrence_order(self):
        module = self._module()
        repaired_primary = {"x": 0.90, "y": 0.90, "width": 0.02, "height": 0.03}
        first_group = _group(
            "COL02-FP-0100",
            x=0.10,
            y=0.10,
            primary_bbox=repaired_primary,
        )
        second_group = _group("COL02-FP-0101", x=0.10, y=0.20)
        assigned = module.assign_occurrence_ids([second_group, first_group])
        self.assertEqual([row["candidate_id"] for row in assigned], ["COL02-FP-0100", "COL02-FP-0101"])

    def test_semantic_future_fields_cannot_affect_sort_key(self):
        module = self._module()
        a = _group("COL02-FP-0200", x=0.20, y=0.20)
        b = _group("COL02-FP-0201", x=0.30, y=0.20)
        for row, suffix in [(a, "A"), (b, "B")]:
            row.update(
                {
                    "support_identity": f"SUP-{suffix}",
                    "ocr_token": f"TXT-{suffix}",
                    "family_id": f"FAM-{suffix}",
                    "canonical_node_id": f"NODE-{suffix}",
                    "vertical_chain_id": f"CHAIN-{suffix}",
                }
            )
        baseline = module.assign_occurrence_ids([a, b])
        a["support_identity"], b["support_identity"] = b["support_identity"], a["support_identity"]
        a["ocr_token"], b["ocr_token"] = b["ocr_token"], a["ocr_token"]
        changed = module.assign_occurrence_ids([b, a])
        self.assertEqual(
            [(row["occurrence_id"], row["candidate_id"]) for row in baseline],
            [(row["occurrence_id"], row["candidate_id"]) for row in changed],
        )

    def test_per_occurrence_authority_defaults_are_fail_closed(self):
        module = self._module()
        occurrence = module.assign_occurrence_ids([_group("COL02-FP-0300", x=0.10, y=0.10)])[0]
        self.assertEqual(occurrence["documentary_label_state"], "NOT_EVALUATED")
        self.assertEqual(occurrence["structural_identity_state"], "NOT_EVALUATED")
        self.assertEqual(occurrence["canonical_geometry_state"], "NOT_AUTHORIZED")
        self.assertFalse(occurrence["canonical_write_authorized"])
        self.assertFalse(occurrence["g2c_promotion_authorized"])
        self.assertFalse(occurrence["g3_promotion_authorized"])


class LedgerClosureTests(unittest.TestCase):
    @staticmethod
    def _module():
        from experiments.cew_col03a import occurrence_ledger

        return occurrence_ledger

    def _clean(self):
        module = self._module()
        groups = [
            _group("COL02-FP-0400", x=0.10, y=0.10, evidence_ids=["E1"]),
            _group("COL02-FP-0401", x=0.30, y=0.10, evidence_ids=["E2"]),
        ]
        ledger = module.build_occurrence_ledger(records=groups, source=SOURCE)
        evidence = [_evidence("E1", "COL02-FP-0400"), _evidence("E2", "COL02-FP-0401")]
        reconciliation = module.build_reconciliation_report(
            evidence_items=evidence,
            occurrences=ledger["occurrences"],
            conflicts=ledger["conflicts"],
        )
        closure = module.build_ledger_closure(
            ledger=ledger,
            reconciliation=reconciliation,
            col02_closure=_col02_closure(),
            qualified_base_sha=BASE_SHA,
        )
        return ledger, reconciliation, closure

    def test_clean_closed_set_closes_bidirectionally(self):
        ledger, reconciliation, closure = self._clean()
        self.assertEqual(ledger["schema_id"], "CEW_COL03A_GOVERNED_COLUMN_OCCURRENCE_LEDGER")
        self.assertEqual(reconciliation["schema_id"], "CEW_COL03A_COLUMN_OCCURRENCE_RECONCILIATION")
        self.assertEqual(closure["schema_id"], "CEW_COL03A_COLUMN_OCCURRENCE_LEDGER_CLOSURE")
        self.assertEqual(ledger["occurrence_count"], 2)
        self.assertEqual(reconciliation["missing_source_evidence_ids"], [])
        self.assertEqual(reconciliation["orphan_occurrence_ids"], [])
        self.assertTrue(reconciliation["bidirectional_closed_set_complete"])
        self.assertTrue(closure["occurrence_ledger_complete"])
        self.assertEqual(closure["authority"], CLOSED_AUTHORITY)

    def test_reconciliation_reports_missing_source_evidence_and_orphan_occurrence(self):
        module = self._module()
        occurrences = module.assign_occurrence_ids(
            [
                _group("COL02-FP-0500", x=0.10, y=0.10, evidence_ids=["E1"]),
                _group("COL02-FP-0501", x=0.30, y=0.10, evidence_ids=["E999"]),
            ]
        )
        reconciliation = module.build_reconciliation_report(
            evidence_items=[_evidence("E1", "COL02-FP-0500"), _evidence("E2", "COL02-FP-0502")],
            occurrences=occurrences,
            conflicts=[],
        )
        self.assertEqual(reconciliation["missing_source_evidence_ids"], ["E2"])
        self.assertEqual(reconciliation["orphan_occurrence_ids"], ["COL-OCC-0002"])
        self.assertFalse(reconciliation["bidirectional_closed_set_complete"])

    def test_conflict_or_incomplete_reconstruction_keeps_closure_false(self):
        module = self._module()
        groups = [
            _group("COL02-FP-0600", x=0.10, y=0.10, width=0.10, height=0.10, evidence_ids=["E1"]),
            _group("COL02-FP-0601", x=0.105, y=0.105, width=0.095, height=0.095, evidence_ids=["E2"]),
        ]
        ledger = module.build_occurrence_ledger(records=groups, source=SOURCE)
        self.assertEqual(ledger["conflict_count"], 1)
        reconciliation = module.build_reconciliation_report(
            evidence_items=[_evidence("E1", "COL02-FP-0600"), _evidence("E2", "COL02-FP-0601")],
            occurrences=ledger["occurrences"],
            conflicts=ledger["conflicts"],
        )
        closure = module.build_ledger_closure(
            ledger=ledger,
            reconciliation=reconciliation,
            col02_closure=_col02_closure(),
            qualified_base_sha=BASE_SHA,
        )
        self.assertFalse(closure["occurrence_ledger_complete"])
        self.assertIn("UNRESOLVED_CONFLICTS", closure["blocking_reasons"])

        ledger_no_conflict = copy.deepcopy(ledger)
        ledger_no_conflict["conflicts"] = []
        ledger_no_conflict["conflict_count"] = 0
        ledger_no_conflict["occurrences"][0]["exact_source_reconstructible"] = False
        reconciliation_no_conflict = copy.deepcopy(reconciliation)
        reconciliation_no_conflict["conflicts"] = []
        reconciliation_no_conflict["conflict_count"] = 0
        closure = module.build_ledger_closure(
            ledger=ledger_no_conflict,
            reconciliation=reconciliation_no_conflict,
            col02_closure=_col02_closure(),
            qualified_base_sha=BASE_SHA,
        )
        self.assertFalse(closure["occurrence_ledger_complete"])
        self.assertIn("SOURCE_RECONSTRUCTION_FAILED", closure["blocking_reasons"])

    def test_incomplete_lineage_wrong_base_or_authority_drift_fails_closed(self):
        module = self._module()
        ledger, reconciliation, _closure = self._clean()

        broken_lineage = copy.deepcopy(ledger)
        broken_lineage["occurrences"][0]["lineage_complete"] = False
        closure = module.build_ledger_closure(
            ledger=broken_lineage,
            reconciliation=reconciliation,
            col02_closure=_col02_closure(),
            qualified_base_sha=BASE_SHA,
        )
        self.assertFalse(closure["occurrence_ledger_complete"])
        self.assertIn("MISSING_LINEAGE", closure["blocking_reasons"])

        wrong_base = module.build_ledger_closure(
            ledger=ledger,
            reconciliation=reconciliation,
            col02_closure=_col02_closure(),
            qualified_base_sha="0" * 40,
        )
        self.assertFalse(wrong_base["occurrence_ledger_complete"])
        self.assertIn("QUALIFIED_BASE_DRIFT", wrong_base["blocking_reasons"])

        drifted = copy.deepcopy(ledger)
        drifted["authority"]["canonical_geometry_authorized"] = True
        authority = module.build_ledger_closure(
            ledger=drifted,
            reconciliation=reconciliation,
            col02_closure=_col02_closure(),
            qualified_base_sha=BASE_SHA,
        )
        self.assertFalse(authority["occurrence_ledger_complete"])
        self.assertIn("AUTHORITY_DRIFT", authority["blocking_reasons"])

    def test_reconciliation_and_ledger_are_deterministic_under_input_order(self):
        module = self._module()
        groups = [
            _group("COL02-FP-0701", x=0.30, y=0.20, evidence_ids=["E2"]),
            _group("COL02-FP-0700", x=0.10, y=0.10, evidence_ids=["E1"]),
        ]
        first = module.build_occurrence_ledger(records=groups, source=SOURCE)
        second = module.build_occurrence_ledger(records=list(reversed(groups)), source=SOURCE)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

        evidence = [_evidence("E2", "COL02-FP-0701"), _evidence("E1", "COL02-FP-0700")]
        first_reconciliation = module.build_reconciliation_report(
            evidence_items=evidence,
            occurrences=first["occurrences"],
            conflicts=first["conflicts"],
        )
        second_reconciliation = module.build_reconciliation_report(
            evidence_items=list(reversed(evidence)),
            occurrences=second["occurrences"],
            conflicts=second["conflicts"],
        )
        self.assertEqual(first_reconciliation, second_reconciliation)


if __name__ == "__main__":
    unittest.main()
