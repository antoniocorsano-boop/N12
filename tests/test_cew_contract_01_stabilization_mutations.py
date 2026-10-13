from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT))


def load_checks():
    spec = importlib.util.spec_from_file_location("checks", SCRIPTS / "cew_contract_01_stabilization_checks.py")
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load checks")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validator():
    spec = importlib.util.spec_from_file_location("closure", SCRIPTS / "validate_cew_contract_01_closure.py")
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load closure validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALID_WORKFLOW = """name: CEW-CONTRACT-01 Closure Gate
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
        run: python scripts/cew_contract_01_replay.py --authority evidence/authority.json --source-root /tmp/source --output /tmp/out.json --result /tmp/replay.json
      - name: Enforce CEW-CONTRACT-01 qualification
        run: python scripts/validate_cew_contract_01_closure.py
"""


class StabilizationMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.c = load_checks()

    def make_case(self, root: Path):
        (root / "evidence/cew-contract-01/stabilization").mkdir(parents=True)
        source_root = root / "operational"
        (source_root / "scripts").mkdir(parents=True)
        builder = source_root / "scripts/builder.py"
        builder.write_text("x=1\n", encoding="utf-8")
        blob = self.c.git_blob_sha_file(builder)
        inputs = [{"path": f"i{i}", "sha256": f"sha{i}"} for i in range(6)]
        authority = {
            "operational_commit": "abc",
            "canonical_snapshot_id": "snap@abc",
            "model_generation_id": "MG-001",
            "builder": {"path": "scripts/builder.py", "git_blob_sha": blob},
            "generation_profile": "P",
            "inputs": inputs,
            "registration": {"source_path": "reg.csv", "source_git_blob_sha": "regblob", "support_ids": ["1", "19"]},
            "output": {"identity": "out.json", "generation_id_inside_artifact": "CSM-v0", "sha256": "outsha", "size_bytes": 10},
            "generated_at": "2026-08-26T09:54:00+00:00",
            "authority_flags": {"solver_authorized": False, "calculation_model_ready": False, "synthetic_solver_result": False, "solver_run": False, "result_entity_created": False},
            "gate_evidence": {f"C01-T{i:02d}": ["e"] for i in range(1, 12)},
        }
        (root / "evidence/cew-contract-01/stabilization/N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json").write_text(json.dumps(authority), encoding="utf-8")
        historical = {
            "runtime_dependency": False,
            "run": {"id": 42, "workflow_path": "wf.yml", "head_sha": "abc", "status": "completed", "conclusion": "success"},
            "artifact": {"id": 7, "name": "artifact", "archive_digest": "zipsha"},
            "output": {"identity": "out.json", "sha256": "outsha", "size_bytes": 10},
            "verification": {
                "archive_sha256_verified": True,
                "output_sha256_verified": True,
                "output_size_verified": True,
            },
        }
        (root / "evidence/cew-contract-01/stabilization/N12_CEW_MODEL_GENERATION_HISTORICAL_RECEIPT_v1.json").write_text(json.dumps(historical), encoding="utf-8")
        model = {
            "model_generation_id": "MG-001",
            "canonical_snapshot_id": "snap@abc", "generation_profile": "P",
            "builder": {"path": "scripts/builder.py", "source_commit": "abc", "git_blob_sha": blob},
            "inputs": inputs,
            "output": {"identity": "out.json", "generation_id_inside_artifact": "CSM-v0", "sha256": "outsha", "size_bytes": 10, "artifact_id": 7, "artifact_name": "artifact", "artifact_archive_digest": "zipsha"},
            "generated_at": authority["generated_at"],
            "workflow": {"path": "wf.yml", "workflow_run_id": 42},
            "verification": {"status": "PASS", "workflow_run_id": 42},
            "solver_authorized": False, "calculation_model_ready": False, "synthetic_solver_result": False,
        }
        receipt = {
            "model_generation_id": "MG-001",
            "generation_id_inside_artifact": "CSM-v0",
            "solver_run": False,
            "result_entity_created": False,
            "engineering_result": False,
        }
        fixture = {"source_commit": "abc", "source_path": "reg.csv", "source_git_blob_sha": "regblob", "examples": [{"support_id": "1"}, {"support_id": "19"}]}
        replay = {"passed": True, "identity": "out.json", "sha256": "outsha", "size_bytes": 10, "generated_at": authority["generated_at"], "errors": []}
        return source_root, model, receipt, fixture, replay

    def errors(self, root, source, model, receipt, fixture, replay):
        return self.c.validate_stabilization(root, model, receipt, fixture, source, replay)

    def test_workflow_exact_head_mutation_is_rejected(self):
        text = VALID_WORKFLOW.replace("github.event.pull_request.head.sha", "github.sha")
        self.assertIn("CI_BYPASS_EXACT_HEAD_MISSING", self.c.workflow_contract_errors(text))

    def test_workflow_unpinned_action_mutation_is_rejected(self):
        text = VALID_WORKFLOW.replace("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", "actions/checkout@v4")
        self.assertIn("CI_BYPASS_UNPINNED_ACTION:actions/checkout@v4", self.c.workflow_contract_errors(text))

    def test_workflow_conditional_bypass_mutation_is_rejected(self):
        text = VALID_WORKFLOW.replace("      - name: Enforce", "      - if: success()\n      - name: Enforce")
        self.assertIn("CI_BYPASS_CONDITIONAL_STEP", self.c.workflow_contract_errors(text))

    def test_workflow_ephemeral_artifact_dependency_is_rejected(self):
        text = VALID_WORKFLOW + "\n# /actions/artifacts/9601773275/zip\n"
        self.assertIn("CI_BYPASS_EPHEMERAL_ACTIONS_DEPENDENCY", self.c.workflow_contract_errors(text))

    def test_frozen_operational_commit_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source, model, receipt, fixture, replay = self.make_case(root)
            model["builder"]["source_commit"] = "def"
            self.assertIn("AUTHORITY_IDENTITY_OPERATIONAL_COMMIT_MISMATCH", self.errors(root, source, model, receipt, fixture, replay))

    def test_builder_blob_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source, model, receipt, fixture, replay = self.make_case(root)
            (source / "scripts/builder.py").write_text("tampered\n", encoding="utf-8")
            self.assertIn("BUILDER_IDENTITY_BLOB_MISMATCH", self.errors(root, source, model, receipt, fixture, replay))

    def test_input_set_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source, model, receipt, fixture, replay = self.make_case(root)
            model["inputs"].pop()
            self.assertIn("INPUT_SET_AUTHORITY_MISMATCH", self.errors(root, source, model, receipt, fixture, replay))

    def test_replay_output_digest_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source, model, receipt, fixture, replay = self.make_case(root)
            replay["sha256"] = "wrong"
            self.assertIn("REPLAY_OUTPUT_MISMATCH:sha256", self.errors(root, source, model, receipt, fixture, replay))

    def test_authority_boundary_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source, model, receipt, fixture, replay = self.make_case(root)
            receipt["solver_run"] = True
            self.assertIn("AUTHORITY_BOUNDARY_INVALID:solver_run", self.errors(root, source, model, receipt, fixture, replay))

    def test_missing_support_1_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source, model, receipt, fixture, replay = self.make_case(root)
            fixture["examples"] = [{"support_id": "19"}]
            self.assertIn("REGISTRATION_EXAMPLE_SET_INVALID", self.errors(root, source, model, receipt, fixture, replay))

    def test_missing_support_19_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source, model, receipt, fixture, replay = self.make_case(root)
            fixture["examples"] = [{"support_id": "1"}]
            self.assertIn("REGISTRATION_EXAMPLE_SET_INVALID", self.errors(root, source, model, receipt, fixture, replay))

    def test_unexpected_registration_support_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source, model, receipt, fixture, replay = self.make_case(root)
            fixture["examples"].append({"support_id": "20"})
            self.assertIn("REGISTRATION_EXAMPLE_SET_INVALID", self.errors(root, source, model, receipt, fixture, replay))

    def test_historical_runtime_dependency_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); source, model, receipt, fixture, replay = self.make_case(root)
            path = root / "evidence/cew-contract-01/stabilization/N12_CEW_MODEL_GENERATION_HISTORICAL_RECEIPT_v1.json"
            data = json.loads(path.read_text(encoding="utf-8")); data["runtime_dependency"] = True; path.write_text(json.dumps(data), encoding="utf-8")
            self.assertIn("AUTHORITY_IDENTITY_HISTORICAL_RUNTIME_DEPENDENCY", self.errors(root, source, model, receipt, fixture, replay))

    def test_gate_matrix_duplicate_id_mutation_is_rejected(self):
        v = load_validator()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            matrix = root / "matrix.csv"
            with matrix.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(["test_id", "status", "evidence"])
                for index in range(1, 12):
                    test_id = "C01-T01" if index == 2 else f"C01-T{index:02d}"
                    writer.writerow([test_id, "PASS", "evidence.md"])
            status = v.read_gate_status(matrix)
        self.assertFalse(status["all_pass"])
        self.assertFalse(status["exact_test_ids"])

    def test_gate_evidence_missing_mutation_is_rejected(self):
        v = load_validator()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            matrix = root / "matrix.csv"
            with matrix.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(["test_id", "status", "evidence"])
                for index in range(1, 12):
                    writer.writerow([f"C01-T{index:02d}", "PASS", "missing.md"])
            status = v.read_gate_status(matrix, root=root)
        self.assertFalse(status["all_pass"])
        self.assertTrue(any(error.startswith("C01_GATE_EVIDENCE_MISSING") for error in status["evidence_errors"]))


if __name__ == "__main__":
    unittest.main()
