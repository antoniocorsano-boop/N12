from __future__ import annotations

import unittest
from pathlib import Path

from scripts.cew_contract_01_stabilization_checks import workflow_contract_errors


WORKFLOW = Path(".github/workflows/validate-cew-contract-01-closure.yml")


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def reindent_closure_direct_children_to_three_spaces(text: str) -> str:
    lines = text.splitlines()
    closure_index = lines.index("  closure:")
    mutated = lines[: closure_index + 1]
    mutated.append("   if: false")
    for line in lines[closure_index + 1 :]:
        if line.startswith("    ") and not line.startswith("     "):
            mutated.append(line[1:])
        else:
            mutated.append(line)
    return "\n".join(mutated) + "\n"


def reindent_closure_job_to_one_space(text: str) -> str:
    lines = text.splitlines()
    closure_index = lines.index("  closure:")
    mutated = lines[:closure_index]
    mutated.append(" closure:")
    mutated.append("  if: false")
    for line in lines[closure_index + 1 :]:
        if line.startswith("    "):
            mutated.append(line[2:])
        else:
            mutated.append(line)
    return "\n".join(mutated) + "\n"


class FinalReviewRound5Regressions(unittest.TestCase):
    def test_valid_nonstandard_job_child_indentation_cannot_hide_job_condition(self):
        tampered = reindent_closure_direct_children_to_three_spaces(workflow_text())
        self.assertIn("\n  closure:\n   if: false\n   name: CEW-CONTRACT-01 Closure Gate\n", tampered)
        self.assertIn("CI_BYPASS_JOB_CONDITIONAL", workflow_contract_errors(tampered))

    def test_valid_nonstandard_job_key_indentation_cannot_hide_job_condition(self):
        tampered = reindent_closure_job_to_one_space(workflow_text())
        self.assertIn("\njobs:\n closure:\n  if: false\n  name: CEW-CONTRACT-01 Closure Gate\n", tampered)
        self.assertIn("CI_BYPASS_JOB_CONDITIONAL", workflow_contract_errors(tampered))

    def test_nonstandard_job_defaults_indentation_cannot_redirect_mandatory_commands(self):
        tampered = workflow_text().replace(
            "  closure:\n    name: CEW-CONTRACT-01 Closure Gate\n",
            "  closure:\n    defaults:\n     run:\n      working-directory: bypass\n    name: CEW-CONTRACT-01 Closure Gate\n",
            1,
        )
        self.assertIn("CI_BYPASS_MANDATORY_WORKING_DIRECTORY", workflow_contract_errors(tampered))

    def test_nonstandard_workflow_defaults_indentation_cannot_redirect_mandatory_commands(self):
        tampered = workflow_text().replace(
            "jobs:\n",
            "defaults:\n run:\n  working-directory: bypass\njobs:\n",
            1,
        )
        self.assertIn("CI_BYPASS_MANDATORY_WORKING_DIRECTORY", workflow_contract_errors(tampered))


if __name__ == "__main__":
    unittest.main()
