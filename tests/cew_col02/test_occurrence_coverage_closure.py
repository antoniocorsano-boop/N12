from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_NAME = "experiments.cew_col02.occurrence_coverage_closure"
EXPECTED_REPAIR_DIGEST = "e688c22753d8804edfdded8e9f89651c60b7a864a016b400a027d708329b1228"
EXPECTED_RECONCILIATION_REPLAY = "b68526f71e77a072b0849d2d3cd2fcab886b03c86a99681717d7aee5cd13bf3c"
REPAIR_IDS = {
    "R01": "COL02-FP-0252",
    "R03": "COL02-FP-0073",
    "R04": "COL02-FP-0241",
    "R05": "COL02-FP-0261",
    "R06": "COL02-FP-0071",
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


class OccurrenceCoverageClosureTests(unittest.TestCase):
    def _module(self):
        spec = importlib.util.find_spec(MODULE_NAME)
        self.assertIsNotNone(spec, "occurrence-coverage closure module is missing")
        return importlib.import_module(MODULE_NAME)

    @staticmethod
    def _fixtures():
        tasks = []
        for task_id, candidate_id in [
            ("R01", "COL02-FP-0252"),
            ("R02", "COL02-FP-0106"),
            ("R03", "COL02-FP-0073"),
            ("R04", "COL02-FP-0241"),
            ("R05", "COL02-FP-0261"),
            ("R06", "COL02-FP-0071"),
        ]:
            tasks.append({
                "review_task_id": task_id,
                "candidate_id": candidate_id if task_id in {"R01", "R02"} else None,
                "proposal_candidate_id": candidate_id if task_id not in {"R01", "R02"} else None,
                "task_type": "REFRAME_CONFIRMATION" if task_id in {"R01", "R02"} else "ADDITIONAL_OCCURRENCE_CONFIRMATION",
                "graphical_decision": "PENDING_HUMAN_REVIEW",
            })
        reconciliation = {
            "schema_id": "CEW_COL02_RESIDUAL_OCCURRENCE_RECONCILIATION",
            "residual_candidate_review_complete": True,
            "occurrence_coverage_complete": False,
            "replay_sha256": EXPECTED_RECONCILIATION_REPLAY,
            "review_tasks": tasks,
            "point_reconciliation": [
                {"event_id": f"EV-{i}", "status": "REVIEW_REQUIRED_EXISTING_PROPOSAL", "proposal_candidate_id": cid}
                for i, cid in enumerate(["COL02-FP-0073", "COL02-FP-0241", "COL02-FP-0261", "COL02-FP-0071"], start=1)
            ],
            "authority": {"graphical_reconciliation_review_authorized": True, **CLOSED_AUTHORITY},
        }
        reconciliation_receipt = {
            "schema_id": "CEW_COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW",
            "schema_version": 1,
            "decisions": [
                {"review_task_id": "R01", "candidate_id": "COL02-FP-0252", "decision": "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY", "repair_eligible": True},
                {"review_task_id": "R02", "candidate_id": "COL02-FP-0106", "decision": "MISLOCALIZED_NOT_COLUMN", "repair_eligible": False},
                {"review_task_id": "R03", "candidate_id": "COL02-FP-0073", "decision": "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY", "repair_eligible": True},
                {"review_task_id": "R04", "candidate_id": "COL02-FP-0241", "decision": "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY", "repair_eligible": True},
                {"review_task_id": "R05", "candidate_id": "COL02-FP-0261", "decision": "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY", "repair_eligible": True},
                {"review_task_id": "R06", "candidate_id": "COL02-FP-0071", "decision": "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY", "repair_eligible": True},
            ],
            "authority": {"graphical_whole_symbol_repair_authorized": True, **CLOSED_AUTHORITY},
        }
        repair_manifest = {
            "schema": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR_MANIFEST_v1",
            "proposal_count": 611,
            "original_proposal_id_space_immutable": True,
            "repair_candidate_count": 5,
            "ready_for_human_review_count": 5,
            "unresolved_repair_count": 0,
            "rejected_candidates": [{"candidate_id": "COL02-FP-0106", "reason": "MISLOCALIZED_NOT_COLUMN"}],
            "repairs": [
                {"repair_id": f"COL02-WSR-{i:03d}", "source_candidate_id": cid, "status": "READY_FOR_HUMAN_GRAPHICAL_REVIEW"}
                for i, cid in enumerate(REPAIR_IDS.values(), start=1)
            ],
            "occurrence_coverage_complete": False,
            "authority": {"graphical_whole_symbol_repair_authorized": True, **CLOSED_AUTHORITY},
        }
        repair_bytes = b"reviewed-repair-manifest"
        graphical_receipt = {
            "schema_id": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW",
            "schema_version": 2,
            "decisions": [
                {"repair_id": f"COL02-WSR-{i:03d}", "source_candidate_id": cid, "decision": "PASS"}
                for i, cid in enumerate(REPAIR_IDS.values(), start=1)
            ],
            "summary": {"reviewed": 5, "pass": 5, "rework": 0, "unreviewed": 0, "occurrence_coverage_complete": False},
            "authority": {"graphical_review_record_authorized": True, **CLOSED_AUTHORITY},
        }
        return reconciliation, reconciliation_receipt, repair_manifest, repair_bytes, graphical_receipt

    def _build(self, *, mutate=None):
        module = self._module()
        reconciliation, reconciliation_receipt, repair_manifest, repair_bytes, graphical_receipt = self._fixtures()
        if mutate:
            mutate(reconciliation, reconciliation_receipt, repair_manifest, graphical_receipt)
        return module.build_occurrence_coverage_closure(
            reconciliation_manifest=reconciliation,
            reconciliation_receipt=reconciliation_receipt,
            repair_manifest=repair_manifest,
            repair_manifest_bytes=repair_bytes,
            graphical_review_receipt=graphical_receipt,
            expected_repair_manifest_sha256=hashlib.sha256(repair_bytes).hexdigest(),
        )

    def test_fully_adjudicated_six_item_chain_closes_occurrence_coverage(self):
        result = self._build()
        self.assertTrue(result["occurrence_coverage_complete"])
        self.assertEqual(result["terminal_successor_item_count"], 6)
        self.assertEqual(result["bound_human_point_count"], 4)
        self.assertEqual(result["repair_pass_count"], 5)
        self.assertEqual(result["rejected_candidate_count"], 1)
        self.assertEqual(result["authority"], CLOSED_AUTHORITY)

    def test_unbound_human_point_fails_closed(self):
        def mutate(reconciliation, *_):
            reconciliation["point_reconciliation"][0]["status"] = "HUMAN_POINT_UNBOUND"
            reconciliation["point_reconciliation"][0].pop("proposal_candidate_id", None)
        with self.assertRaises(ValueError):
            self._build(mutate=mutate)

    def test_missing_terminal_reconciliation_decision_fails_closed(self):
        def mutate(_reconciliation, receipt, *_):
            receipt["decisions"].pop()
        with self.assertRaises(ValueError):
            self._build(mutate=mutate)

    def test_non_pass_repair_review_fails_closed(self):
        def mutate(_reconciliation, _receipt, _repair, graphical):
            graphical["decisions"][2]["decision"] = "REWORK"
        with self.assertRaises(ValueError):
            self._build(mutate=mutate)

    def test_repair_manifest_digest_mismatch_fails_closed(self):
        module = self._module()
        reconciliation, receipt, repair_manifest, repair_bytes, graphical = self._fixtures()
        with self.assertRaises(ValueError):
            module.build_occurrence_coverage_closure(
                reconciliation_manifest=reconciliation,
                reconciliation_receipt=receipt,
                repair_manifest=repair_manifest,
                repair_manifest_bytes=repair_bytes,
                graphical_review_receipt=graphical,
                expected_repair_manifest_sha256="0" * 64,
            )

    def test_downstream_authority_drift_fails_closed(self):
        def mutate(_reconciliation, _receipt, repair, _graphical):
            repair["authority"]["canonical_geometry_authorized"] = True
        with self.assertRaises(ValueError):
            self._build(mutate=mutate)

    def test_exact_source_writer_emits_canonical_closure_artifact(self):
        module = self._module()
        writer = getattr(module, "write_occurrence_coverage_closure", None)
        self.assertTrue(callable(writer), "exact-source occurrence-coverage writer is missing")
        reconciliation, receipt, repair_manifest, _repair_bytes, graphical = self._fixtures()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reconciliation_path = root / "reconciliation.json"
            receipt_path = root / "reconciliation-review.json"
            repair_path = root / "repair.json"
            graphical_path = root / "graphical-review.json"
            output_path = root / "closure.json"
            reconciliation_path.write_text(json.dumps(reconciliation), encoding="utf-8")
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            repair_path.write_text(json.dumps(repair_manifest, sort_keys=True), encoding="utf-8")
            graphical_path.write_text(json.dumps(graphical), encoding="utf-8")
            expected_digest = hashlib.sha256(repair_path.read_bytes()).hexdigest()

            result = writer(
                reconciliation_path=reconciliation_path,
                reconciliation_receipt_path=receipt_path,
                repair_manifest_path=repair_path,
                graphical_review_receipt_path=graphical_path,
                output_path=output_path,
                expected_repair_manifest_sha256=expected_digest,
            )

            self.assertTrue(output_path.exists())
            emitted = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(emitted, result)
            self.assertTrue(emitted["occurrence_coverage_complete"])
            self.assertEqual(emitted["reconciliation_replay_sha256"], EXPECTED_RECONCILIATION_REPLAY)
            self.assertEqual(emitted["reviewed_repair_manifest_sha256"], expected_digest)
            self.assertEqual(emitted["authority"], CLOSED_AUTHORITY)


if __name__ == "__main__":
    unittest.main()
