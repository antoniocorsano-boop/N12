from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_cew_contract_01_closure.py"
EXPECTED_OPERATIONAL_COMMIT = "d806dcca72779b5a186defe557a7a9b739575a90"


def load_validator():
    spec = importlib.util.spec_from_file_location("cew_contract_01_closure_review", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load closure validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ClosureReviewRegressionTests(unittest.TestCase):
    def make_valid_project(self, root: Path, operational_root: Path) -> dict[str, Path]:
        fixture = root / "evidence/cew-contract-01/fixtures/N12_REGISTRATION_UNCERTAINTY_v1.json"
        manifest = root / "evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_v1.json"
        receipt = root / "evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_RECEIPT_v1.json"
        minimality = root / "evidence/cew-contract-01/CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv"
        evidence = root / "evidence/case.md"
        matrix = root / "docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.csv"
        report = root / "docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md"
        source = operational_root / "data/source.txt"

        for path in (fixture, manifest, receipt, minimality, evidence, matrix, report, source):
            path.parent.mkdir(parents=True, exist_ok=True)

        fixture.write_text(
            json.dumps(
                {
                    "uncertainty_type": "REGISTRATION_UNCERTAINTY",
                    "source_commit": EXPECTED_OPERATIONAL_COMMIT,
                    "source_path": "data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv",
                    "examples": [
                        {
                            "support_id": "1",
                            "unit": "px",
                            "observed": {"u": 1.0, "v": 2.0},
                            "predicted": {"u": 1.1, "v": 2.1},
                            "residual": {"du": 0.1, "dv": 0.1, "scalar": 0.14},
                            "diagnostic_status": "PASS_DIAGNOSTIC",
                            "derived_bound": None,
                        },
                        {
                            "support_id": "19",
                            "unit": "px",
                            "observed": {"u": 3.0, "v": 4.0},
                            "predicted": {"u": 3.2, "v": 4.2},
                            "residual": {"du": 0.2, "dv": 0.2, "scalar": 0.28},
                            "diagnostic_status": "WATCH",
                            "derived_bound": None,
                        },
                    ],
                    "interpretive_guard": "Residuals are registration diagnostics, not tolerance, standard error, standard uncertainty, accuracy, or certified metrological uncertainty.",
                    "epistemic_guard": {
                        "residual_is_new_measurement": False,
                        "residual_promotable_to_DOC": False,
                        "residual_promotable_to_MIS": False,
                        "unsourced_plus_minus_interval_allowed": False,
                    },
                }
            ),
            encoding="utf-8",
        )

        trusted = b"trusted-operational-input\n"
        source.write_bytes(trusted)
        input_digest = sha256(trusted)
        output_digest = sha256(b"derived-output")
        archive_digest = "sha256:" + sha256(b"artifact-archive")
        model = {
            "model_generation_id": "N12-CEW-MG-TEST",
            "canonical_snapshot_id": f"snapshot@{EXPECTED_OPERATIONAL_COMMIT}",
            "scenario_id": None,
            "generation_profile": "TEST_PROFILE",
            "builder": {
                "path": "scripts/cew_structural_model_builder.py",
                "source_commit": EXPECTED_OPERATIONAL_COMMIT,
                "git_blob_sha": "builder-blob",
            },
            "workflow": {
                "path": ".github/workflows/validate-cew-structural-model-builder.yml",
                "workflow_run_id": 42,
                "conclusion": "success",
            },
            "parameters": {},
            "inputs": [{"path": "data/source.txt", "sha256": input_digest}],
            "output": {
                "identity": "output.json",
                "sha256": output_digest,
                "size_bytes": 14,
                "artifact_id": 7,
                "artifact_name": "artifact",
                "artifact_archive_digest": archive_digest,
            },
            "warnings": [],
            "generated_at": "2026-10-13T00:00:00Z",
            "verification": {"status": "PASS", "workflow_run_id": 42},
            "receipt_ref": "evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_RECEIPT_v1.json",
            "solver_authorized": False,
            "calculation_model_ready": False,
            "synthetic_solver_result": False,
        }
        manifest.write_text(json.dumps(model), encoding="utf-8")

        receipt_data = {
            "receipt_class": "QUALIFICATION_RECEIPT",
            "engineering_result": False,
            "solver_run": False,
            "result_entity_created": False,
            "source_commit": EXPECTED_OPERATIONAL_COMMIT,
            "builder_path": model["builder"]["path"],
            "workflow_path": model["workflow"]["path"],
            "workflow_run_id": 42,
            "workflow_conclusion": "success",
            "artifact_id": 7,
            "artifact_name": "artifact",
            "artifact_archive_digest": archive_digest,
            "output_file": "output.json",
            "output_sha256": output_digest,
            "output_size_bytes": 14,
            "input_sha256": {"data/source.txt": input_digest},
            "verification": {"status": "PASS", "workflow_run_id": 42},
        }
        receipt.write_text(json.dumps(receipt_data), encoding="utf-8")

        minimality.write_text(
            "structural_type,classification,case_ref\n"
            "Node,CORE_REQUIRED,evidence/case.md\n"
            "Wall,SUPPORTED_EXTENSION,\n",
            encoding="utf-8",
        )
        evidence.write_text("qualified evidence\n", encoding="utf-8")
        with matrix.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["test_id", "status", "evidence"])
            for index in range(1, 12):
                writer.writerow([f"C01-T{index:02d}", "PASS", "evidence/case.md"])
        report.write_text(
            "CEW-FEM-01: ModelGeneration → SolverRun → Result → Verification → Receipt\n",
            encoding="utf-8",
        )
        return {
            "fixture": fixture,
            "manifest": manifest,
            "receipt": receipt,
            "evidence": evidence,
            "source": source,
        }

    def validate(self, root: Path, operational_root: Path):
        v = load_validator()
        with patch.dict(os.environ, {"CEW_OPERATIONAL_SOURCE_ROOT": str(operational_root)}):
            return v.validate_project(root)

    def test_epistemic_guard_must_keep_all_promotions_forbidden(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd:
            root, operational = Path(td), Path(sd)
            paths = self.make_valid_project(root, operational)
            data = json.loads(paths["fixture"].read_text(encoding="utf-8"))
            data["epistemic_guard"]["residual_promotable_to_DOC"] = True
            paths["fixture"].write_text(json.dumps(data), encoding="utf-8")
            result = self.validate(root, operational)
        self.assertFalse(result["qualified"])
        self.assertTrue(any(error.startswith("REGISTRATION_EPISTEMIC_GUARD") for error in result["errors"]))

    def test_model_generation_verification_must_be_pass(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd:
            root, operational = Path(td), Path(sd)
            paths = self.make_valid_project(root, operational)
            data = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            data["verification"]["status"] = "FAIL"
            paths["manifest"].write_text(json.dumps(data), encoding="utf-8")
            result = self.validate(root, operational)
        self.assertFalse(result["qualified"])
        self.assertIn("MODEL_GENERATION_VERIFICATION_NOT_PASS", result["errors"])

    def test_model_generation_requires_workflow_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd:
            root, operational = Path(td), Path(sd)
            paths = self.make_valid_project(root, operational)
            data = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            data["workflow"] = {}
            paths["manifest"].write_text(json.dumps(data), encoding="utf-8")
            result = self.validate(root, operational)
        self.assertFalse(result["qualified"])
        self.assertIn("MODEL_GENERATION_WORKFLOW_IDENTITY_MISSING", result["errors"])

    def test_model_generation_requires_output_artifact_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd:
            root, operational = Path(td), Path(sd)
            paths = self.make_valid_project(root, operational)
            data = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            data["output"]["artifact_archive_digest"] = ""
            paths["manifest"].write_text(json.dumps(data), encoding="utf-8")
            result = self.validate(root, operational)
        self.assertFalse(result["qualified"])
        self.assertIn("MODEL_GENERATION_OUTPUT_IDENTITY_MISSING", result["errors"])

    def test_receipt_must_match_manifest_and_remain_non_engineering(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd:
            root, operational = Path(td), Path(sd)
            paths = self.make_valid_project(root, operational)
            data = json.loads(paths["receipt"].read_text(encoding="utf-8"))
            data["solver_run"] = True
            data["output_sha256"] = "mismatch"
            paths["receipt"].write_text(json.dumps(data), encoding="utf-8")
            result = self.validate(root, operational)
        self.assertFalse(result["qualified"])
        self.assertTrue(any(error.startswith("MODEL_GENERATION_RECEIPT_") for error in result["errors"]))

    def test_every_pass_row_requires_existing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd:
            root, operational = Path(td), Path(sd)
            paths = self.make_valid_project(root, operational)
            paths["evidence"].unlink()
            result = self.validate(root, operational)
        self.assertFalse(result["qualified"])
        self.assertTrue(any(error.startswith("C01_GATE_EVIDENCE_") for error in result["errors"]))

    def test_pinned_model_input_digest_is_recomputed(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd:
            root, operational = Path(td), Path(sd)
            paths = self.make_valid_project(root, operational)
            paths["source"].write_bytes(b"tampered-operational-input\n")
            result = self.validate(root, operational)
        self.assertFalse(result["qualified"])
        self.assertIn("MODEL_GENERATION_INPUT_0_DIGEST_MISMATCH", result["errors"])


if __name__ == "__main__":
    unittest.main()
