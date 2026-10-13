from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate-cew-contract-01-closure.yml"


class ClosureGateWorkflowTests(unittest.TestCase):
    def test_closure_gate_is_repository_native_and_fail_closed(self) -> None:
        self.assertTrue(WORKFLOW.exists(), "CEW-CONTRACT-01 closure workflow must exist")
        text = WORKFLOW.read_text(encoding="utf-8")
        required = (
            "name: CEW-CONTRACT-01 Closure Gate",
            "pull_request:",
            "workflow_dispatch:",
            "contents: read",
            "python -m py_compile scripts/validate_cew_contract_01_closure.py",
            "python -m unittest tests/test_cew_contract_01_closure.py -v",
            "python -m unittest tests/test_cew_contract_01_ci_gate.py -v",
            "python scripts/validate_cew_contract_01_closure.py",
        )
        for marker in required:
            self.assertIn(marker, text)
        self.assertNotIn("continue-on-error: true", text)
        self.assertNotIn("ref: work/m0-global-model", text)


if __name__ == "__main__":
    unittest.main()
