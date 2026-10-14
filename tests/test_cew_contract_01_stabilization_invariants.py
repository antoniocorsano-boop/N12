from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path


class StabilizationChecksTests(unittest.TestCase):
    def make_case(self, root: Path):
        from scripts.cew_contract_01_stabilization_checks import git_blob_sha_file

        (root / "evidence/cew-contract-01/stabilization").mkdir(parents=True)
        source_root = root / "operational"
        (source_root / "scripts").mkdir(parents=True)
        builder = source_root / "scripts/builder.py"
        builder.write_text("x=1\n", encoding="utf-8")
        inputs = []
        for index in range(6):
            path = source_root / f"i{index}.txt"
            path.write_text(f"{index}\n", encoding="utf-8")
            inputs.append({"path": f"i{index}.txt", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        authority = {
            "operational_commit": "abc",
            "canonical_snapshot_id": "snap@abc",
            "model_generation_id": "MG-001",
            "builder": {"path": "scripts/builder.py", "git_blob_sha": git_blob_sha_file(builder), "declared_builder": "B"},
            "generation_profile": "P",
            "inputs": inputs,
            "registration": {"source_path": "reg.csv", "source_git_blob_sha": "blob", "support_ids": ["1", "19"]},
            "output": {"identity": "out.json", "generation_id_inside_artifact": "CSM-v0", "sha256": "outsha", "size_bytes": 10},
            "generated_at": "2026-01-01T00:00:00+00:00",
            "authority_flags": {
                "solver_authorized": False,
                "calculation_model_ready": False,
                "synthetic_solver_result": False,
                "solver_run": False,
                "result_entity_created": False,
            },
            "gate_evidence": {f"C01-T{i:02d}": ["x"] for i in range(1, 12)},
        }
        authority_path = root / "evidence/cew-contract-01/stabilization/N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json"
        authority_path.write_text(json.dumps(authority), encoding="utf-8")
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
        historical_path = root / "evidence/cew-contract-01/stabilization/N12_CEW_MODEL_GENERATION_HISTORICAL_RECEIPT_v1.json"
        historical_path.write_text(json.dumps(historical), encoding="utf-8")
        model = {
            "model_generation_id": "MG-001",
            "canonical_snapshot_id": "snap@abc",
            "generation_profile": "P",
            "builder": {"path": "scripts/builder.py", "source_commit": "abc", "git_blob_sha": authority["builder"]["git_blob_sha"]},
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
            "solver_authorized": False,
            "calculation_model_ready": False,
            "synthetic_solver_result": False,
        }
        receipt = {
            "model_generation_id": "MG-001",
            "generation_id_inside_artifact": "CSM-v0",
            "generated_artifact_timestamp": authority["generated_at"],
            "source_commit": "abc",
            "solver_run": False,
            "result_entity_created": False,
            "engineering_result": False,
            "artifact_id": 7,
            "artifact_name": "artifact",
            "artifact_archive_digest": "zipsha",
            "output_file": "out.json",
            "output_sha256": "outsha",
            "output_size_bytes": 10,
        }
        fixture = {
            "source_commit": "abc",
            "source_path": "reg.csv",
            "source_git_blob_sha": "blob",
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
        return source_root, model, receipt, fixture, replay, historical_path

    def validate(self, *args):
        from scripts.cew_contract_01_stabilization_checks import validate_stabilization
        return validate_stabilization(*args)

    def test_happy_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_root, model, receipt, fixture, replay, _ = self.make_case(root)
            self.assertEqual(self.validate(root, model, receipt, fixture, source_root, replay), [])

    def test_builder_blob_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_root, model, receipt, fixture, replay, _ = self.make_case(root)
            (source_root / "scripts/builder.py").write_text("tamper\n", encoding="utf-8")
            self.assertIn("BUILDER_IDENTITY_BLOB_MISMATCH", self.validate(root, model, receipt, fixture, source_root, replay))

    def test_registration_examples_must_be_exact(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_root, model, receipt, fixture, replay, _ = self.make_case(root)
            fixture["examples"] = [{"support_id": "1"}]
            self.assertIn("REGISTRATION_EXAMPLE_SET_INVALID", self.validate(root, model, receipt, fixture, source_root, replay))

    def test_profile_disagreement_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_root, model, receipt, fixture, replay, _ = self.make_case(root)
            model["output"]["sha256"] = "different"
            self.assertIn("OUTPUT_AUTHORITY_MISMATCH:sha256", self.validate(root, model, receipt, fixture, source_root, replay))

    def test_missing_or_bad_replay_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_root, model, receipt, fixture, replay, _ = self.make_case(root)
            self.assertIn("REPLAY_RESULT_MISSING", self.validate(root, model, receipt, fixture, source_root, None))
            replay["sha256"] = "bad"
            self.assertIn("REPLAY_OUTPUT_MISMATCH:sha256", self.validate(root, model, receipt, fixture, source_root, replay))

    def test_authority_boundary_mutation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_root, model, receipt, fixture, replay, _ = self.make_case(root)
            model["solver_authorized"] = True
            self.assertIn("AUTHORITY_BOUNDARY_INVALID:solver_authorized", self.validate(root, model, receipt, fixture, source_root, replay))

    def test_historical_receipt_cannot_be_runtime_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_root, model, receipt, fixture, replay, historical_path = self.make_case(root)
            historical = json.loads(historical_path.read_text(encoding="utf-8"))
            historical["runtime_dependency"] = True
            historical_path.write_text(json.dumps(historical), encoding="utf-8")
            self.assertIn("AUTHORITY_IDENTITY_HISTORICAL_RUNTIME_DEPENDENCY", self.validate(root, model, receipt, fixture, source_root, replay))


if __name__ == "__main__":
    unittest.main()
