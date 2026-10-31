from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest


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

REPAIR_IDS = {
    "R01": "COL02-FP-0252",
    "R03": "COL02-FP-0073",
    "R04": "COL02-FP-0241",
    "R05": "COL02-FP-0261",
    "R06": "COL02-FP-0071",
}


class GovernedInputsTests(unittest.TestCase):
    @staticmethod
    def _load(path: str) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    @classmethod
    def _fixtures(cls):
        prototype = cls._load("governance/cew-col02/COLUMN_FOOTPRINT_HUMAN_REVIEW_v1.json")
        guided = cls._load("governance/cew-col02/COL02_PROTOTYPE_GUIDED_HUMAN_REVIEW_v1.json")
        mobile = cls._load("governance/cew-col02/COL02_RESIDUAL_MOBILE_HUMAN_REVIEW_v1.json")

        review_tasks = [
            {
                "review_task_id": "R01",
                "task_type": "REFRAME_CONFIRMATION",
                "candidate_id": "COL02-FP-0252",
                "source_event_id": "EV-R01",
            },
            {
                "review_task_id": "R02",
                "task_type": "REFRAME_CONFIRMATION",
                "candidate_id": "COL02-FP-0106",
                "source_event_id": "EV-R02",
            },
        ]
        point_rows = []
        for task_id, candidate_id, event_id in [
            ("R03", "COL02-FP-0073", "EV-A"),
            ("R04", "COL02-FP-0241", "EV-B"),
            ("R05", "COL02-FP-0261", "EV-C"),
            ("R06", "COL02-FP-0071", "EV-D"),
        ]:
            review_tasks.append(
                {
                    "review_task_id": task_id,
                    "task_type": "ADDITIONAL_OCCURRENCE_CONFIRMATION",
                    "proposal_candidate_id": candidate_id,
                    "event_id": event_id,
                }
            )
            point_rows.append(
                {
                    "event_id": event_id,
                    "status": "REVIEW_REQUIRED_EXISTING_PROPOSAL",
                    "proposal_candidate_id": candidate_id,
                }
            )

        reconciliation_manifest = {
            "schema_id": "CEW_COL02_RESIDUAL_OCCURRENCE_RECONCILIATION",
            "schema_version": 1,
            "review_tasks": review_tasks,
            "point_reconciliation": point_rows,
            "residual_candidate_review_complete": True,
            "occurrence_coverage_complete": False,
            "authority": {
                "graphical_reconciliation_review_authorized": True,
                "graphical_review_evidence_retained": True,
                **CLOSED_AUTHORITY,
            },
        }
        reconciliation_receipt = {
            "schema_id": "CEW_COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW",
            "schema_version": 1,
            "decisions": [
                {
                    "review_task_id": "R01",
                    "candidate_id": "COL02-FP-0252",
                    "decision": "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY",
                    "repair_eligible": True,
                },
                {
                    "review_task_id": "R02",
                    "candidate_id": "COL02-FP-0106",
                    "decision": "MISLOCALIZED_NOT_COLUMN",
                    "repair_eligible": False,
                },
                *[
                    {
                        "review_task_id": task_id,
                        "candidate_id": candidate_id,
                        "decision": "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY",
                        "repair_eligible": True,
                    }
                    for task_id, candidate_id in list(REPAIR_IDS.items())[1:]
                ],
            ],
            "authority": {"graphical_whole_symbol_repair_authorized": True, **CLOSED_AUTHORITY},
        }
        repair_manifest = {
            "schema": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR_MANIFEST_v1",
            "proposal_count": 611,
            "original_proposal_id_space_immutable": True,
            "repairs": [
                {
                    "repair_id": f"COL02-WSR-{index:03d}",
                    "source_candidate_id": candidate_id,
                    "status": "READY_FOR_HUMAN_GRAPHICAL_REVIEW",
                    "reconstructed_bbox": {"x": 0.01 * index, "y": 0.02 * index, "width": 0.01, "height": 0.01},
                }
                for index, candidate_id in enumerate(REPAIR_IDS.values(), start=1)
            ],
            "rejected_candidates": [
                {"candidate_id": "COL02-FP-0106", "reason": "MISLOCALIZED_NOT_COLUMN"}
            ],
            "occurrence_coverage_complete": False,
            "authority": {"graphical_whole_symbol_repair_authorized": True, **CLOSED_AUTHORITY},
        }
        repair_review = {
            "schema_id": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW",
            "schema_version": 2,
            "decisions": [
                {
                    "repair_id": f"COL02-WSR-{index:03d}",
                    "source_candidate_id": candidate_id,
                    "decision": "PASS",
                }
                for index, candidate_id in enumerate(REPAIR_IDS.values(), start=1)
            ],
            "authority": {"graphical_review_record_authorized": True, **CLOSED_AUTHORITY},
        }
        closure = {
            "schema_id": "CEW_COL02_OCCURRENCE_COVERAGE_CLOSURE",
            "schema_version": 1,
            "occurrence_coverage_complete": True,
            "proposal_count": 611,
            "original_proposal_id_space_immutable": True,
            "rejected_candidates": [
                {"candidate_id": "COL02-FP-0106", "reason": "MISLOCALIZED_NOT_COLUMN"}
            ],
            "authority": dict(CLOSED_AUTHORITY),
        }
        return (
            prototype,
            guided,
            mobile,
            reconciliation_manifest,
            reconciliation_receipt,
            repair_manifest,
            repair_review,
            closure,
        )

    def _collect(self, fixtures=None):
        from experiments.cew_col03a.governed_inputs import collect_governed_positive_evidence

        values = fixtures or self._fixtures()
        return collect_governed_positive_evidence(
            prototype_receipt=values[0],
            prototype_guided_receipt=values[1],
            mobile_receipt=values[2],
            reconciliation_manifest=values[3],
            reconciliation_receipt=values[4],
            repair_manifest=values[5],
            repair_review_receipt=values[6],
            coverage_closure=values[7],
        )

    def test_actual_receipts_produce_only_governed_positive_evidence(self):
        items = self._collect()
        by_class = {}
        for item in items:
            by_class.setdefault(item["evidence_class"], []).append(item)

        self.assertEqual(len(by_class["PROTOTYPE_CONFIRMED"]), 2)
        self.assertEqual(len(by_class["PROTOTYPE_GUIDED_CONFIRMED"]), 15)
        self.assertEqual(len(by_class["RESIDUAL_DIRECT_CONFIRMED"]), 2)
        self.assertEqual(len(by_class["REPAIRED_SUCCESSOR_CONFIRMED"]), 5)
        self.assertEqual(len(items), 24)
        self.assertEqual(len({item["evidence_id"] for item in items}), 24)

        self.assertEqual(
            {item["candidate_id"] for item in by_class["PROTOTYPE_CONFIRMED"]},
            {"COL02-FP-0363", "COL02-FP-0493"},
        )
        self.assertEqual(
            {item["candidate_id"] for item in by_class["RESIDUAL_DIRECT_CONFIRMED"]},
            {"COL02-FP-0581", "COL02-FP-0605"},
        )
        self.assertNotIn("COL02-FP-0106", {item["candidate_id"] for item in items})

    def test_mobile_undo_history_does_not_leak_undone_or_non_positive_events(self):
        items = self._collect()
        residual = [item for item in items if item["evidence_class"] == "RESIDUAL_DIRECT_CONFIRMED"]
        self.assertEqual(
            [(item["candidate_id"], item["graphical_decision"]) for item in residual],
            [
                ("COL02-FP-0581", "PILASTRO"),
                ("COL02-FP-0605", "PILASTRO"),
            ],
        )

    def test_repaired_successor_preserves_reframe_and_human_point_lineage(self):
        items = self._collect()
        repaired = {
            item["candidate_id"]: item
            for item in items
            if item["evidence_class"] == "REPAIRED_SUCCESSOR_CONFIRMED"
        }
        self.assertEqual(repaired["COL02-FP-0252"]["discovery_path"], "REFRAME_CONFIRMATION")
        self.assertEqual(repaired["COL02-FP-0252"]["human_added_point_event_ids"], [])
        self.assertEqual(repaired["COL02-FP-0073"]["discovery_path"], "ADDITIONAL_OCCURRENCE_CONFIRMATION")
        self.assertEqual(repaired["COL02-FP-0073"]["human_added_point_event_ids"], ["EV-A"])
        self.assertEqual(repaired["COL02-FP-0073"]["repair_id"], "COL02-WSR-002")

    def test_non_pass_or_non_repair_eligible_candidate_cannot_become_repaired_positive(self):
        fixtures = list(self._fixtures())
        fixtures[6] = copy.deepcopy(fixtures[6])
        fixtures[6]["decisions"][1]["decision"] = "REWORK"
        with self.assertRaises(ValueError):
            self._collect(tuple(fixtures))

    def test_incomplete_col02_coverage_fails_closed(self):
        fixtures = list(self._fixtures())
        fixtures[7] = copy.deepcopy(fixtures[7])
        fixtures[7]["occurrence_coverage_complete"] = False
        with self.assertRaises(ValueError):
            self._collect(tuple(fixtures))

    def test_downstream_authority_drift_fails_closed(self):
        from experiments.cew_col03a.governed_inputs import validate_col03a_input_authority

        payload = {"authority": dict(CLOSED_AUTHORITY)}
        validate_col03a_input_authority(payload, "fixture")
        payload["authority"]["canonical_geometry_authorized"] = True
        with self.assertRaises(ValueError):
            validate_col03a_input_authority(payload, "fixture")


if __name__ == "__main__":
    unittest.main()
