from __future__ import annotations

import unittest

from scripts.cew_contract_01_stabilization_checks import workflow_contract_errors
from scripts.validate_cew_contract_01_closure import fem_debt_declared
from tests.test_cew_contract_01_fresh_review_regressions import VALID_BASE


class FinalReviewRound3Regressions(unittest.TestCase):
    def test_job_level_if_cannot_skip_closure_gate(self):
        tampered = VALID_BASE.replace(
            "  closure:\n    steps:",
            "  closure:\n    if: false\n    steps:",
        )
        self.assertIn("CI_BYPASS_JOB_CONDITIONAL", workflow_contract_errors(tampered))

    def test_custom_shell_cannot_neutralize_final_enforcement(self):
        text = VALID_BASE + """      - name: Enforce CEW-CONTRACT-01 qualification
        shell: echo {0}
        run: python scripts/validate_cew_contract_01_closure.py
"""
        self.assertIn("CI_BYPASS_MANDATORY_SHELL", workflow_contract_errors(text))

    def test_replay_command_with_shell_fallback_is_rejected(self):
        tampered = VALID_BASE.replace(
            "run: python scripts/cew_contract_01_replay.py",
            "run: python scripts/cew_contract_01_replay.py || printf fake > \"$CEW_REPLAY_RESULT_PATH\"",
        )
        self.assertIn("CI_BYPASS_REPLAY_COMMAND_INVALID", workflow_contract_errors(tampered))

    def test_fem_debt_negation_does_not_count_as_affirmative_declaration(self):
        text = (
            "CEW-FEM-01 is no longer required. "
            "ModelGeneration → SolverRun → Result → Verification → Receipt"
        )
        self.assertFalse(fem_debt_declared(text))


if __name__ == "__main__":
    unittest.main()
