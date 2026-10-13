from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.cew_gate_authority.test_qualification import QualificationEngineTests, valid_payload

SCHEMA = Path("governance/cew-gate-authority/schemas/QUALIFICATION_RECEIPT_v1.schema.json")
EXPECTED_INVARIANTS = tuple(f"I{i:02d}" for i in range(1, 18))
BOUNDARY_KEYS = {
    "solver_authorized",
    "calculation_model_ready",
    "synthetic_solver_result",
    "solver_run",
    "result_entity_created",
}


class IndependentReviewCandidateContractRegressions(QualificationEngineTests):
    def test_rejects_structural_minimality_contradiction(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/structural-type-minimality.csv"
        payload[path] = b"structural_type,status\nCEW_CORE,NOT_MINIMAL\n"
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_STRUCTURAL_MINIMALITY_MISMATCH", receipt.failure_codes)

    def test_rejects_blank_mandatory_markdown_artifacts(self):
        for path in (
            "qualification/cew-contract-01/n12/source-sufficiency.md",
            "qualification/cew-contract-01/n12/evidence/CASE_12_MODEL_GENERATION.md",
            "qualification/cew-contract-01/n12/evidence/CASE_13_CORE_END_TO_END_ASSURANCE.md",
        ):
            with self.subTest(path=path):
                payload = valid_payload(self.authority)
                payload[path] = b"\n\t  \n"
                receipt = self.evaluate(payload)
                self.assertFalse(receipt.qualified)
                self.assertIn("CANDIDATE_MARKDOWN_EMPTY", receipt.failure_codes)


class IndependentReviewReceiptSchemaRegressions(unittest.TestCase):
    def test_receipt_schema_freezes_nested_contracts_and_qualified_consistency(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        expected_nested = {
            "control_plane": {"base_commit_sha"},
            "gate_core": {"repository", "commit_sha", "version"},
            "authority": {"authority_id", "authority_sha256"},
            "candidate": {"base_repository", "pr_number", "head_repository", "head_sha"},
            "operational_authority": {"commit_sha"},
            "replay": {"output_identity", "output_sha256", "output_size_bytes", "historical_generated_at"},
            "authority_boundary": BOUNDARY_KEYS,
        }
        for name, required in expected_nested.items():
            with self.subTest(name=name):
                contract = schema["properties"][name]
                self.assertIs(contract.get("additionalProperties"), False)
                self.assertEqual(set(contract.get("required", ())), set(required))
                self.assertEqual(set(contract.get("properties", ())), set(required))

        invariants = schema["properties"]["invariants"]
        self.assertIs(invariants.get("additionalProperties"), False)
        self.assertEqual(set(invariants.get("required", ())), set(EXPECTED_INVARIANTS))
        self.assertEqual(set(invariants.get("properties", ())), set(EXPECTED_INVARIANTS))
        for key in EXPECTED_INVARIANTS:
            self.assertEqual(
                invariants["properties"][key].get("enum"),
                ["PASS", "FAIL", "NOT_APPLICABLE"],
            )

        qualified_rules = [
            rule
            for rule in schema.get("allOf", ())
            if rule.get("if", {}).get("properties", {}).get("qualified") == {"const": True}
        ]
        self.assertEqual(len(qualified_rules), 1)
        qualified = qualified_rules[0]["then"]["properties"]
        self.assertEqual(qualified["failure_codes"].get("maxItems"), 0)
        self.assertEqual(qualified["cew_fem_01_required"], {"const": True})
        for key in BOUNDARY_KEYS:
            self.assertEqual(
                qualified["authority_boundary"]["properties"][key],
                {"const": False},
            )
        for key in EXPECTED_INVARIANTS:
            self.assertEqual(qualified["invariants"]["properties"][key], {"const": "PASS"})


if __name__ == "__main__":
    unittest.main()
