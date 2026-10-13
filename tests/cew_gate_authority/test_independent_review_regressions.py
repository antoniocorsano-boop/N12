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

    def test_rejects_future_registration_schema_version(self):
        receipt = self.evaluate(
            self.mutate_json(
                "qualification/cew-contract-01/n12/registration-uncertainty.json",
                lambda obj: obj.update(schema_version="999.0"),
            )
        )
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_DOCUMENT_SCHEMA_UNSUPPORTED", receipt.failure_codes)

    def test_rejects_future_model_generation_schema_version(self):
        receipt = self.evaluate(
            self.mutate_json(
                "qualification/cew-contract-01/n12/model-generation.json",
                lambda obj: obj.update(schema_version="999.0"),
            )
        )
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_DOCUMENT_SCHEMA_UNSUPPORTED", receipt.failure_codes)

    def test_rejects_future_model_generation_receipt_schema_version(self):
        receipt = self.evaluate(
            self.mutate_json(
                "qualification/cew-contract-01/n12/model-generation-receipt.json",
                lambda obj: obj.update(schema_version="999.0"),
            )
        )
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_DOCUMENT_SCHEMA_UNSUPPORTED", receipt.failure_codes)

    def test_rejects_future_evidence_index_schema_version_before_i15(self):
        receipt = self.evaluate(
            self.mutate_json(
                "qualification/cew-contract-01/n12/evidence-index.json",
                lambda obj: obj.update(schema_version=2),
            )
        )
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_DOCUMENT_SCHEMA_UNSUPPORTED", receipt.failure_codes)

    def test_rejects_unexpected_root_field_in_registration_document(self):
        receipt = self.evaluate(
            self.mutate_json(
                "qualification/cew-contract-01/n12/registration-uncertainty.json",
                lambda obj: obj.update(unexpected="x"),
            )
        )
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_DOCUMENT_UNEXPECTED_FIELD", receipt.failure_codes)

    def test_i10_binds_receipt_source_repository_to_a0(self):
        payload = self.mutate_json(
            "qualification/cew-contract-01/n12/model-generation-receipt.json",
            lambda obj: obj.update(source_repository="example/other"),
        )
        self.assert_failure(self.evaluate(payload), "I10", "I10_MANIFEST_RECEIPT_INCOHERENT")

    def test_i10_binds_receipt_builder_path_to_a0(self):
        payload = self.mutate_json(
            "qualification/cew-contract-01/n12/model-generation-receipt.json",
            lambda obj: obj.update(builder_path="scripts/other_builder.py"),
        )
        self.assert_failure(self.evaluate(payload), "I10", "I10_MANIFEST_RECEIPT_INCOHERENT")

    def test_i16_rejects_boundary_true_anywhere_in_structured_json(self):
        payload = self.mutate_json(
            "qualification/cew-contract-01/n12/model-generation.json",
            lambda obj: obj["builder"].update(solver_run=True),
        )
        self.assert_failure(self.evaluate(payload), "I16", "I16_AUTHORITY_BOUNDARY_VIOLATION")

    def _assert_duplicate_key_rejected(self, payload):
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_JSON_DUPLICATE_KEY", receipt.failure_codes)

    def test_rejects_duplicate_boundary_key_true_then_false(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/model-generation.json"
        payload[path] = payload[path].replace(
            b'"solver_authorized": false',
            b'"solver_authorized": true, "solver_authorized": false',
            1,
        )
        self._assert_duplicate_key_rejected(payload)

    def test_rejects_duplicate_schema_version_even_when_last_value_is_supported(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/qualification.json"
        payload[path] = payload[path].replace(
            b'"schema_version": 1',
            b'"schema_version": 999, "schema_version": 1',
            1,
        )
        self._assert_duplicate_key_rejected(payload)

    def test_rejects_duplicate_provenance_key_even_when_last_value_is_trusted(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/model-generation-receipt.json"
        payload[path] = payload[path].replace(
            b'"source_repository": "antoniocorsano-boop/N12"',
            b'"source_repository": "example/other", "source_repository": "antoniocorsano-boop/N12"',
            1,
        )
        self._assert_duplicate_key_rejected(payload)

    def test_rejects_semantically_innocuous_duplicate_key(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/evidence-index.json"
        payload[path] = payload[path].replace(
            b'"schema_id": "CEW_EVIDENCE_INDEX"',
            b'"schema_id": "CEW_EVIDENCE_INDEX", "schema_id": "CEW_EVIDENCE_INDEX"',
            1,
        )
        self._assert_duplicate_key_rejected(payload)

    def test_rejects_wrong_conformance_matrix_header(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/conformance-matrix.csv"
        payload[path] = payload[path].replace(b"test_id,status,evidence_id", b"test_id,status,other")
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_CSV_HEADER_UNSUPPORTED", receipt.failure_codes)

    def test_rejects_wrong_structural_minimality_header(self):
        payload = valid_payload(self.authority)
        path = "qualification/cew-contract-01/n12/structural-type-minimality.csv"
        payload[path] = payload[path].replace(b"structural_type,status", b"structural_type,other")
        receipt = self.evaluate(payload)
        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_CSV_HEADER_UNSUPPORTED", receipt.failure_codes)


if __name__ == "__main__":
    unittest.main()
