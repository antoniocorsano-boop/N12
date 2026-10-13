from __future__ import annotations

import json
import unittest

from tests.cew_gate_authority.test_qualification import QualificationEngineTests, valid_payload


class IndependentReviewSemanticRegressions(QualificationEngineTests):
    def test_rejects_unapproved_qualification_schema_id(self):
        receipt = self.evaluate(
            self.mutate_json(
                "qualification/cew-contract-01/n12/qualification.json",
                lambda obj: obj.update(schema_id="UNSUPPORTED_SCHEMA"),
            )
        )
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_QUALIFICATION_SCHEMA_UNSUPPORTED", receipt.failure_codes)

    def test_rejects_future_qualification_schema_version(self):
        receipt = self.evaluate(
            self.mutate_json(
                "qualification/cew-contract-01/n12/qualification.json",
                lambda obj: obj.update(schema_version=2),
            )
        )
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_QUALIFICATION_SCHEMA_UNSUPPORTED", receipt.failure_codes)

    def test_i15_rejects_allowlisted_but_wrong_evidence_path(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/evidence-index.json"
        index = json.loads(payload[path])
        index["evidence"]["C01-T01"] = "qualification/cew-contract-01/n12/qualification.json"
        payload[path] = json.dumps(index).encode()
        self.assert_failure(self.evaluate(payload), "I15", "I15_EVIDENCE_INVALID")

    def test_i15_rejects_reusing_one_allowlisted_evidence_for_all_tests(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/evidence-index.json"
        index = json.loads(payload[path])
        reused = "qualification/cew-contract-01/n12/evidence/CASE_01_DOCUMENTED_PROPERTY.md"
        index["evidence"] = {key: reused for key in index["evidence"]}
        payload[path] = json.dumps(index).encode()
        self.assert_failure(self.evaluate(payload), "I15", "I15_EVIDENCE_INVALID")


if __name__ == "__main__":
    unittest.main()
