from __future__ import annotations

import unittest

from tests.cew_gate_authority.test_qualification import QualificationEngineTests, valid_payload


class IndependentReviewRound6Regressions(QualificationEngineTests):
    def test_rejects_additional_blob_under_qualification_root(self):
        payload = valid_payload(self.authority)
        payload["qualification/cew-contract-01/n12/solver-result.json"] = b'{"solver_run": true}'

        receipt = self.evaluate(payload)

        self.assertFalse(receipt.qualified)
        self.assertIn("CANDIDATE_SURFACE_INVALID", receipt.failure_codes)

    def test_rejects_nonempty_markdown_that_does_not_match_a0_evidence(self):
        for path in (
            "qualification/cew-contract-01/n12/source-sufficiency.md",
            "qualification/cew-contract-01/n12/evidence/CASE_01_DOCUMENTED_PROPERTY.md",
            "qualification/cew-contract-01/n12/evidence/CASE_12_MODEL_GENERATION.md",
            "qualification/cew-contract-01/n12/evidence/CASE_13_CORE_END_TO_END_ASSURANCE.md",
        ):
            with self.subTest(path=path):
                payload = valid_payload(self.authority)
                payload[path] = b"FAIL: evidence is insufficient\n"

                receipt = self.evaluate(payload)

                self.assertFalse(receipt.qualified)
                self.assertIn("CANDIDATE_MARKDOWN_DIGEST_MISMATCH", receipt.failure_codes)

    def test_binds_registration_fixture_identity_to_a0(self):
        path = "qualification/cew-contract-01/n12/registration-uncertainty.json"
        for field, value in (
            ("fixture_id", "UNRELATED_FIXTURE"),
            ("uncertainty_type", "UNRELATED_UNCERTAINTY"),
        ):
            with self.subTest(field=field):
                payload = self.mutate_json(path, lambda obj, key=field, replacement=value: obj.update({key: replacement}))

                receipt = self.evaluate(payload)

                self.assert_failure(receipt, "I11", "I11_REGISTRATION_SOURCE_MISMATCH")

    def test_binds_model_generation_profile_and_declared_builder_to_a0(self):
        path = "qualification/cew-contract-01/n12/model-generation.json"
        mutations = (
            lambda obj: obj.update(generation_profile="UNRELATED_PROFILE"),
            lambda obj: obj["builder"].update(declared_builder="UNRELATED_BUILDER"),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                payload = self.mutate_json(path, mutate)

                receipt = self.evaluate(payload)

                self.assert_failure(receipt, "I06", "I06_BUILDER_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
