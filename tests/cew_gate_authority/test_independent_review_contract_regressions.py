from __future__ import annotations

import csv
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

    def test_rejects_unbound_model_generation_receipt_id(self):
        payload = self.mutate_json(
            "qualification/cew-contract-01/n12/model-generation-receipt.json",
            lambda obj: obj.update(receipt_id="WRONG"),
        )
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_DOCUMENT_SCHEMA_UNSUPPORTED", receipt.failure_codes)

    def test_non_object_builder_returns_unqualified_receipt(self):
        path = "qualification/cew-contract-01/n12/model-generation.json"
        for builder in (None, [], "builder", 7):
            with self.subTest(builder=builder):
                payload = self.mutate_json(path, lambda obj, value=builder: obj.update(builder=value))
                receipt = self.evaluate(payload)
                self.assertFalse(receipt.qualified)
                self.assertIn("I03_OPERATIONAL_AUTHORITY_MISMATCH", receipt.failure_codes)
                self.assertIn("I06_BUILDER_IDENTITY_MISMATCH", receipt.failure_codes)

    def test_deep_json_recursion_returns_depth_failure_receipt(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/model-generation.json"
        nested = b"[" * 1200 + b"0" + b"]" * 1200
        payload[path] = payload[path].replace(
            b'"generation_profile": "CEW_CANONICAL_STRUCTURAL_GRAPH_v0"',
            b'"generation_profile": ' + nested,
            1,
        )
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_JSON_DEPTH_EXCEEDED", receipt.failure_codes)

    def test_oversized_csv_field_returns_payload_failure_receipt(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/structural-type-minimality.csv"
        oversized = b"X" * (csv.field_size_limit() + 1)
        payload[path] = b"structural_type,status\nCEW_CORE," + oversized + b"\n"
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_CSV_ROW_INVALID", receipt.failure_codes)


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

    def test_replay_contract_allows_null_only_for_unqualified_receipts(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        replay = schema["properties"]["replay"]["properties"]
        expected_base_types = {
            "output_identity": {"string", "null"},
            "output_sha256": {"string", "null"},
            "output_size_bytes": {"integer", "null"},
            "historical_generated_at": {"string", "null"},
        }
        for key, expected in expected_base_types.items():
            with self.subTest(key=key):
                actual = replay[key].get("type")
                actual_types = {actual} if isinstance(actual, str) else set(actual or ())
                self.assertEqual(actual_types, expected)

        qualified_rules = [
            rule
            for rule in schema.get("allOf", ())
            if rule.get("if", {}).get("properties", {}).get("qualified") == {"const": True}
        ]
        qualified_replay = qualified_rules[0]["then"]["properties"]["replay"]["properties"]
        self.assertEqual(qualified_replay["output_identity"].get("type"), "string")
        self.assertEqual(qualified_replay["output_sha256"].get("type"), "string")
        self.assertEqual(qualified_replay["output_size_bytes"].get("type"), "integer")
        self.assertEqual(qualified_replay["historical_generated_at"].get("type"), "string")


if __name__ == "__main__":
    unittest.main()
