from __future__ import annotations

from tests.cew_gate_authority.test_qualification import QualificationEngineTests, valid_payload


class IndependentReviewParserRegressions(QualificationEngineTests):
    def test_rejects_nonfinite_json_constant_before_qualification(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/model-generation.json"
        payload[path] = payload[path].replace(
            b'"generation_profile": "CEW_CANONICAL_STRUCTURAL_GRAPH_v0"',
            b'"generation_profile": NaN',
            1,
        )
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_JSON_INVALID", receipt.failure_codes)

    def test_rejects_csv_row_wider_than_frozen_contract(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/conformance-matrix.csv"
        payload[path] = payload[path].replace(
            b"C01-T01,PASS,C01-T01\n",
            b"C01-T01,PASS,C01-T01,EXTRA\n",
            1,
        )
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_CSV_ROW_INVALID", receipt.failure_codes)
