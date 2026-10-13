from __future__ import annotations

import unittest
from pathlib import Path

from scripts.cew_contract_01_stabilization_checks import workflow_contract_errors
from scripts.validate_cew_contract_01_closure import fem_debt_declared


WORKFLOW = Path(".github/workflows/validate-cew-contract-01-closure.yml")
CHAIN = "CEW-FEM-01: ModelGeneration → SolverRun → Result → Verification → Receipt"


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


class FinalReviewRound4Regressions(unittest.TestCase):
    def test_enforcement_working_directory_cannot_redirect_validator(self):
        tampered = workflow_text().replace(
            "      - name: Enforce CEW-CONTRACT-01 qualification\n        shell: bash\n",
            "      - name: Enforce CEW-CONTRACT-01 qualification\n        shell: bash\n        working-directory: bypass\n",
        )
        self.assertIn("CI_BYPASS_MANDATORY_WORKING_DIRECTORY", workflow_contract_errors(tampered))

    def test_replay_working_directory_cannot_redirect_replay(self):
        tampered = workflow_text().replace(
            "      - name: Run deterministic ModelGeneration replay\n        shell: bash\n",
            "      - name: Run deterministic ModelGeneration replay\n        shell: bash\n        working-directory: bypass\n",
        )
        self.assertIn("CI_BYPASS_MANDATORY_WORKING_DIRECTORY", workflow_contract_errors(tampered))

    def test_job_default_working_directory_cannot_redirect_mandatory_commands(self):
        tampered = workflow_text().replace(
            "  closure:\n    name: CEW-CONTRACT-01 Closure Gate\n",
            "  closure:\n    defaults:\n      run:\n        working-directory: bypass\n    name: CEW-CONTRACT-01 Closure Gate\n",
        )
        self.assertIn("CI_BYPASS_MANDATORY_WORKING_DIRECTORY", workflow_contract_errors(tampered))

    def test_workflow_default_working_directory_cannot_redirect_mandatory_commands(self):
        tampered = workflow_text().replace(
            "jobs:\n",
            "defaults:\n  run:\n    working-directory: bypass\njobs:\n",
            1,
        )
        self.assertIn("CI_BYPASS_MANDATORY_WORKING_DIRECTORY", workflow_contract_errors(tampered))

    def test_prefixed_fem_marker_is_not_affirmative_declaration(self):
        text = f"NOT_CEW_FEM_01_REQUIRED=true\n{CHAIN}\n"
        self.assertFalse(fem_debt_declared(text))

    def test_suffixed_fem_marker_is_not_affirmative_declaration(self):
        text = f"CEW_FEM_01_REQUIRED=true_extra\n{CHAIN}\n"
        self.assertFalse(fem_debt_declared(text))

    def test_exact_standalone_fem_marker_remains_valid(self):
        text = f"CEW_FEM_01_REQUIRED=true\n{CHAIN}\n"
        self.assertTrue(fem_debt_declared(text))


if __name__ == "__main__":
    unittest.main()
