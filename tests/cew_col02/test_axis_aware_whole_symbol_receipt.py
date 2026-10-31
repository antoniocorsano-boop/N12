from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path


RECEIPT = Path("governance/cew-col02/COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW_v1.json")


class AxisAwareWholeSymbolReceiptTests(unittest.TestCase):
    def test_human_micro_gate_distinguishes_five_fragmented_symbols_from_r02_false_target(self) -> None:
        self.assertTrue(RECEIPT.exists(), "governed residual reconciliation Human Review receipt is missing")
        payload = json.loads(RECEIPT.read_text(encoding="utf-8"))

        self.assertEqual(payload["schema_id"], "CEW_COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW")
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["source_exact_sha"], "ead0c9a85a9c6e639dc8d94af7e0902f7b7744c4")

        decisions = {row["review_task_id"]: row for row in payload["decisions"]}
        self.assertEqual(set(decisions), {"R01", "R02", "R03", "R04", "R05", "R06"})

        expected_fragmented = {
            "R01": "COL02-FP-0252",
            "R03": "COL02-FP-0073",
            "R04": "COL02-FP-0241",
            "R05": "COL02-FP-0261",
            "R06": "COL02-FP-0071",
        }
        for task_id, candidate_id in expected_fragmented.items():
            self.assertEqual(decisions[task_id]["candidate_id"], candidate_id)
            self.assertEqual(decisions[task_id]["decision"], "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY")
            self.assertTrue(decisions[task_id]["axis_partition_observed"])

        self.assertEqual(decisions["R02"]["candidate_id"], "COL02-FP-0106")
        self.assertEqual(decisions["R02"]["decision"], "MISLOCALIZED_NOT_COLUMN")
        self.assertFalse(decisions["R02"]["repair_eligible"])

        repair_ids = {
            row["candidate_id"]
            for row in payload["decisions"]
            if row.get("repair_eligible") is True
        }
        self.assertEqual(repair_ids, set(expected_fragmented.values()))

        self.assertTrue(payload["authority"]["graphical_whole_symbol_repair_authorized"])
        for key in (
            "support_identity_authorized",
            "text_identity_binding_authorized",
            "family_assignment_authorized",
            "section_assignment_authorized",
            "fixed_line_assignment_authorized",
            "structural_identity_authorized",
            "canonical_geometry_authorized",
            "canonical_write_authorized",
            "g2c_promotion_authorized",
            "g3_authorized",
            "merge_authorized",
        ):
            self.assertFalse(payload["authority"][key], key)

    def test_loader_returns_only_explicit_repair_seeds_and_rejects_authority_drift(self) -> None:
        try:
            from experiments.cew_col02.axis_aware_whole_symbol import load_axis_aware_repair_receipt
        except ModuleNotFoundError:
            self.fail("axis-aware whole-symbol receipt loader is missing")

        payload = load_axis_aware_repair_receipt(RECEIPT)
        self.assertEqual(
            payload["repair_candidate_ids"],
            [
                "COL02-FP-0252",
                "COL02-FP-0073",
                "COL02-FP-0241",
                "COL02-FP-0261",
                "COL02-FP-0071",
            ],
        )
        self.assertEqual(payload["rejected_candidate_ids"], ["COL02-FP-0106"])

        tampered = json.loads(RECEIPT.read_text(encoding="utf-8"))
        tampered = copy.deepcopy(tampered)
        tampered["authority"]["canonical_write_authorized"] = True
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tampered.json"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "authority"):
                load_axis_aware_repair_receipt(path)


if __name__ == "__main__":
    unittest.main()
