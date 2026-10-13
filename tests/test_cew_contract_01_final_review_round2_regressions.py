from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.cew_contract_01_stabilization_checks import (
    validate_stabilization,
    workflow_contract_errors,
)
from tests.test_cew_contract_01_fresh_review_regressions import (
    FinalFreshReviewRegressions,
    VALID_BASE,
)


class FinalReviewRound2Regressions(unittest.TestCase):
    def test_checkout_ref_must_match_approved_expression(self):
        tampered = VALID_BASE.replace(
            "github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha",
            "false && github.event.pull_request.head.sha || github.sha",
        )
        self.assertIn("CI_BYPASS_EXACT_HEAD_MISSING", workflow_contract_errors(tampered))

    def test_quoted_if_key_cannot_skip_enforcement(self):
        text = VALID_BASE + """      - name: Enforce CEW-CONTRACT-01 qualification
        \"if\": false
        run: python scripts/validate_cew_contract_01_closure.py
"""
        self.assertIn("CI_BYPASS_CONDITIONAL_STEP", workflow_contract_errors(text))

    def test_receipt_generation_timestamp_mismatch_is_rejected(self):
        helper = FinalFreshReviewRegressions(methodName="test_inert_heredoc_cannot_impersonate_enforcement_step")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, source, model, receipt, fixture, replay = helper.make_case(root)
            receipt["generated_artifact_timestamp"] = "2099-01-01T00:00:00+00:00"
            self.assertIn(
                "RECEIPT_GENERATION_TIMESTAMP_MISMATCH",
                validate_stabilization(root, model, receipt, fixture, source, replay),
            )


if __name__ == "__main__":
    unittest.main()
