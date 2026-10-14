from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.cew_contract_01_stabilization_checks import (
    git_blob_sha_file,
    validate_stabilization,
    workflow_contract_errors,
)


VALID_BASE = """name: CEW-CONTRACT-01 Closure Gate
permissions:
  contents: read
jobs:
  closure:
    steps:
      - name: Checkout PR exact head
        uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          ref: ${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}
          persist-credentials: false
      - name: Set up Python
        uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
      - name: Run deterministic ModelGeneration replay
        run: python scripts/cew_contract_01_replay.py
"""


class FinalFreshReviewRegressions(unittest.TestCase):
    def make_case(self, root: Path):
        stabilization = root / "evidence/cew-contract-01/stabilization"
        stabilization.mkdir(parents=True)
        source_root = root / "operational"
        (source_root / "scripts").mkdir(parents=True)
        builder = source_root / "scripts/builder.py"
        builder.write_text("x=1\n", encoding="utf-8")
        blob = git_blob_sha_file(builder)
        inputs = [{"path": f"i{i}", "sha256": f"sha{i}"} for i in range(6)]

        authority = {
            "operational_commit": "abc",
            "canonical_snapshot_id": "snap@abc",
            "model_generation_id": "MG-001",
            "builder": {"path": "scripts/builder.py", "git_blob_sha": blob},
            "generation_profile": "P",
            "inputs": inputs,
            "registration": {
                "source_path": "reg.csv",
                "source_git_blob_sha": "regblob",
                "support_ids": ["1", "19"],
            },
            "output": {
                "identity": "out.json",
                "generation_id_inside_artifact": "CSM-v0",
                "sha256": "outsha",
                "size_bytes": 10,
            },
            "generated_at": "2026-08-26T09:54:00+00:00",
            "authority_flags": {
                "solver_authorized": False,
                "calculation_model_ready": False,
                "synthetic_solver_result": False,
                "solver_run": False,
                "result_entity_created": False,
            },
            "gate_evidence": {f"C01-T{i:02d}": ["e"] for i in range(1, 12)},
        }
        (stabilization / "N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json").write_text(
            json.dumps(authority), encoding="utf-8"
        )

        historical = {
            "runtime_dependency": False,
            "run": {
                "id": 42,
                "workflow_path": "wf.yml",
                "head_sha": "abc",
                "status": "completed",
                "conclusion": "success",
            },
            "artifact": {"id": 7, "name": "artifact", "archive_digest": "zipsha"},
            "output": {"identity": "out.json", "sha256": "outsha", "size_bytes": 10},
            "verification": {
                "archive_sha256_verified": True,
                "output_sha256_verified": True,
                "output_size_verified": True,
            },
        }
        historical_path = stabilization / "N12_CEW_MODEL_GENERATION_HISTORICAL_RECEIPT_v1.json"
        historical_path.write_text(json.dumps(historical), encoding="utf-8")

        model = {
            "model_generation_id": "MG-001",
            "canonical_snapshot_id": "snap@abc",
            "generation_profile": "P",
            "builder": {"path": "scripts/builder.py", "source_commit": "abc", "git_blob_sha": blob},
            "inputs": inputs,
            "output": {
                "identity": "out.json",
                "generation_id_inside_artifact": "CSM-v0",
                "sha256": "outsha",
                "size_bytes": 10,
                "artifact_id": 7,
                "artifact_name": "artifact",
                "artifact_archive_digest": "zipsha",
            },
            "generated_at": authority["generated_at"],
            "workflow": {"path": "wf.yml", "workflow_run_id": 42},
            "verification": {"status": "PASS", "workflow_run_id": 42},
            "solver_authorized": False,
            "calculation_model_ready": False,
            "synthetic_solver_result": False,
        }
        receipt = {
            "model_generation_id": "MG-001",
            "generation_id_inside_artifact": "CSM-v0",
            "solver_run": False,
            "result_entity_created": False,
            "engineering_result": False,
        }
        fixture = {
            "source_commit": "abc",
            "source_path": "reg.csv",
            "source_git_blob_sha": "regblob",
            "examples": [{"support_id": "1"}, {"support_id": "19"}],
        }
        replay = {
            "passed": True,
            "identity": "out.json",
            "sha256": "outsha",
            "size_bytes": 10,
            "generated_at": authority["generated_at"],
            "errors": [],
        }
        return historical_path, source_root, model, receipt, fixture, replay

    def errors(self, root, source, model, receipt, fixture, replay):
        return validate_stabilization(root, model, receipt, fixture, source, replay)

    def test_inert_heredoc_cannot_impersonate_enforcement_step(self):
        text = VALID_BASE + """      - name: Harmless shell step
        run: |
          cat <<'EOF' >/dev/null
          - name: Enforce CEW-CONTRACT-01 qualification
            run: python scripts/validate_cew_contract_01_closure.py
          EOF
"""
        self.assertIn("CI_BYPASS_ENFORCEMENT_MISSING", workflow_contract_errors(text))

    def test_model_generation_id_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, source, model, receipt, fixture, replay = self.make_case(root)
            model["model_generation_id"] = "MG-TAMPERED"
            self.assertIn(
                "GENERATION_IDENTITY_MISMATCH:model_generation_id",
                self.errors(root, source, model, receipt, fixture, replay),
            )

    def test_output_generation_id_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, source, model, receipt, fixture, replay = self.make_case(root)
            model["output"]["generation_id_inside_artifact"] = "CSM-TAMPERED"
            self.assertIn(
                "GENERATION_IDENTITY_MISMATCH:generation_id_inside_artifact",
                self.errors(root, source, model, receipt, fixture, replay),
            )

    def test_historical_verification_false_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            historical_path, source, model, receipt, fixture, replay = self.make_case(root)
            historical = json.loads(historical_path.read_text(encoding="utf-8"))
            historical["verification"]["output_sha256_verified"] = False
            historical_path.write_text(json.dumps(historical), encoding="utf-8")
            self.assertIn(
                "AUTHORITY_IDENTITY_HISTORICAL_VERIFICATION_INVALID:output_sha256_verified",
                self.errors(root, source, model, receipt, fixture, replay),
            )

    def test_historical_verification_missing_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            historical_path, source, model, receipt, fixture, replay = self.make_case(root)
            historical = json.loads(historical_path.read_text(encoding="utf-8"))
            historical.pop("verification")
            historical_path.write_text(json.dumps(historical), encoding="utf-8")
            self.assertIn(
                "AUTHORITY_IDENTITY_HISTORICAL_VERIFICATION_INVALID:archive_sha256_verified",
                self.errors(root, source, model, receipt, fixture, replay),
            )


if __name__ == "__main__":
    unittest.main()
