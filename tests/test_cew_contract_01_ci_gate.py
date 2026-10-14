from __future__ import annotations

import unittest
from pathlib import Path

from scripts.cew_contract_01_stabilization_checks import workflow_contract_errors

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/validate-cew-contract-01-closure.yml"
CHECKOUT_SHA = "11d5960a326750d5838078e36cf38b85af677262"
SETUP_PYTHON_SHA = "a26af69be951a213d495a4c3e4e4022e16d87065"
OPERATIONAL_COMMIT = "d806dcca72779b5a186defe557a7a9b739575a90"


class ClosureGateWorkflowTests(unittest.TestCase):
    def test_closure_gate_is_durable_repository_native_exact_head_and_fail_closed(self) -> None:
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
            f"git fetch --no-tags --depth=1 origin {OPERATIONAL_COMMIT}",
            "CEW_OPERATIONAL_SOURCE_ROOT: /tmp/cew-contract-01-operational-source",
            "CEW_REPLAY_RESULT_PATH: /tmp/cew-contract-01-replay-result.json",
            "CEW_REPLAY_OUTPUT_PATH: /tmp/N12_CEW_CANONICAL_STRUCTURAL_MODEL_v0.json",
            "scripts/cew_structural_model_builder.py",
            "data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv",
            "Run deterministic ModelGeneration replay",
            "scripts/cew_contract_01_replay.py",
            "N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json",
            "tests/test_cew_contract_01_stabilization_authority.py",
            "tests/test_cew_contract_01_replay.py",
            "tests/test_cew_contract_01_fresh_review_regressions.py",
            "tests/test_cew_contract_01_stabilization_invariants.py",
            "tests/test_cew_contract_01_stabilization_mutations.py",
            "python scripts/validate_cew_contract_01_closure.py",
        )
        for marker in required:
            self.assertIn(marker, text)
        self.assertEqual(workflow_contract_errors(text), [])
        for forbidden in (
            "actions: read",
            "CEW_MODEL_OUTPUT_ROOT",
            "/actions/artifacts/",
            "artifact.zip",
            "9601773275",
            "32955421352",
            "GITHUB_TOKEN",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
