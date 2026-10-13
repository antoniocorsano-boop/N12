from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate-cew-contract-01-closure.yml"

CHECKOUT_SHA = "11d5960a326750d5838078e36cf38b85af677262"
SETUP_PYTHON_SHA = "a26af69be951a213d495a4c3e4e4022e16d87065"
OPERATIONAL_COMMIT = "d806dcca72779b5a186defe557a7a9b739575a90"


class ClosureGateWorkflowTests(unittest.TestCase):
    def test_closure_gate_is_repository_native_exact_head_and_fail_closed(self) -> None:
        self.assertTrue(WORKFLOW.exists(), "CEW-CONTRACT-01 closure workflow must exist")
        text = WORKFLOW.read_text(encoding="utf-8")
        required = (
            "name: CEW-CONTRACT-01 Closure Gate",
            "pull_request:",
            "workflow_dispatch:",
            "contents: read",
            f"uses: actions/checkout@{CHECKOUT_SHA}",
            f"uses: actions/setup-python@{SETUP_PYTHON_SHA}",
            "persist-credentials: false",
            "github.event.pull_request.head.sha",
            "github.sha",
            f"git fetch --no-tags --depth=1 origin {OPERATIONAL_COMMIT}",
            "CEW_OPERATIONAL_SOURCE_ROOT: /tmp/cew-contract-01-operational-source",
            "python -m py_compile scripts/validate_cew_contract_01_closure.py",
            "python -m unittest tests/test_cew_contract_01_closure.py -v",
            "python -m unittest tests/test_cew_contract_01_ci_gate.py -v",
            "python scripts/validate_cew_contract_01_closure.py",
        )
        for marker in required:
            self.assertIn(marker, text)

        self.assertNotRegex(text, r"uses:\s+actions/(?:checkout|setup-python)@v\d")
        self.assertNotRegex(text, r"(?m)^\s*if\s*:")
        self.assertNotIn("continue-on-error:", text)
        self.assertNotIn("|| true", text)
        self.assertNotIn("; true", text)
        self.assertNotIn("ref: work/m0-global-model", text)

        enforcement = re.search(
            r"- name: Enforce CEW-CONTRACT-01 qualification\s*\n"
            r"\s*run: python scripts/validate_cew_contract_01_closure\.py",
            text,
        )
        self.assertIsNotNone(enforcement, "qualification validator must be an unconditional run step")


if __name__ == "__main__":
    unittest.main()
