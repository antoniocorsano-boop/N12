from __future__ import annotations

import json

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

    def test_rejects_numeric_overflow_decoded_as_infinity(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/model-generation.json"
        payload[path] = payload[path].replace(
            b'"generation_profile": "CEW_CANONICAL_STRUCTURAL_GRAPH_v0"',
            b'"generation_profile": 1e400',
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

    def test_rejects_boolean_qualification_schema_version(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/qualification.json"
        document = json.loads(payload[path])
        document["schema_version"] = True
        payload[path] = json.dumps(document).encode()
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_QUALIFICATION_SCHEMA_UNSUPPORTED", receipt.failure_codes)

    def test_rejects_float_document_schema_version(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/evidence-index.json"
        document = json.loads(payload[path])
        document["schema_version"] = 1.0
        payload[path] = json.dumps(document).encode()
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_DOCUMENT_SCHEMA_UNSUPPORTED", receipt.failure_codes)

    def test_rejects_empty_value_in_contracted_csv_row(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/structural-type-minimality.csv"
        payload[path] = payload[path].replace(
            b"CEW_CORE,MINIMAL\n",
            b"CEW_CORE,\n",
            1,
        )
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_CSV_ROW_INVALID", receipt.failure_codes)
