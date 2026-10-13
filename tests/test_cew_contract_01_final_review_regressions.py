from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_cew_contract_01_closure.py"
EXPECTED_OPERATIONAL_COMMIT = "d806dcca72779b5a186defe557a7a9b739575a90"
EXPECTED_SNAPSHOT = f"N12-FROZEN-INPUTSET@{EXPECTED_OPERATIONAL_COMMIT}"
EXPECTED_INPUT_PATHS = (
    "data/canonical/M0G_GEOMETRY_HANDOFF_v1.json",
    "data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv",
    "data/canonical/M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv",
    "data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv",
    "data/canonical/M1F_FOUNDATION_MODEL_CURRENT_v1.csv",
    "data/canonical/M1E_FOUNDATION_XY_SOLVER_PROJECTION_RULE_v1.json",
)
REGISTRATION_SOURCE = "data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv"


def load_validator():
    spec = importlib.util.spec_from_file_location("cew_contract_01_final_review", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load closure validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


class FinalReviewRegressionTests(unittest.TestCase):
    def make_project(self, root: Path, operational: Path, output_root: Path) -> dict[str, Path]:
        fixture = root / "evidence/cew-contract-01/fixtures/N12_REGISTRATION_UNCERTAINTY_v1.json"
        manifest = root / "evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_v1.json"
        receipt = root / "evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_RECEIPT_v1.json"
        minimality = root / "evidence/cew-contract-01/CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv"
        evidence = root / "evidence/case.md"
        matrix = root / "docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.csv"
        report = root / "docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md"
        for path in (fixture, manifest, receipt, minimality, evidence, matrix, report):
            path.parent.mkdir(parents=True, exist_ok=True)

        registration_bytes = (
            "support_id,u_observed_px,v_observed_px,u_predicted_px,v_predicted_px,du_px,dv_px,residual_px,residual_status,evidence_class\n"
            "1,4096.63,2823.61,4100.03,2822.89,3.40,-0.72,3.47,PASS_DIAGNOSTIC,DOC_METRIC_OR_AXIS\n"
            "19,2458.56,4200.73,2462.23,4224.46,3.67,23.73,24.01,WATCH,MIS_AFFINE_WATCH\n"
        ).encode("utf-8")
        registration_source = operational / REGISTRATION_SOURCE
        registration_source.parent.mkdir(parents=True, exist_ok=True)
        registration_source.write_bytes(registration_bytes)
        fixture.write_text(
            json.dumps(
                {
                    "uncertainty_type": "REGISTRATION_UNCERTAINTY",
                    "source_commit": EXPECTED_OPERATIONAL_COMMIT,
                    "source_path": REGISTRATION_SOURCE,
                    "source_git_blob_sha": git_blob_sha(registration_bytes),
                    "examples": [
                        {
                            "support_id": "1",
                            "unit": "px",
                            "observed": {"u": 4096.63, "v": 2823.61},
                            "predicted": {"u": 4100.03, "v": 2822.89},
                            "residual": {"du": 3.40, "dv": -0.72, "scalar": 3.47},
                            "diagnostic_status": "PASS_DIAGNOSTIC",
                            "evidence_class": "DOC_METRIC_OR_AXIS",
                            "derived_bound": None,
                        },
                        {
                            "support_id": "19",
                            "unit": "px",
                            "observed": {"u": 2458.56, "v": 4200.73},
                            "predicted": {"u": 2462.23, "v": 4224.46},
                            "residual": {"du": 3.67, "dv": 23.73, "scalar": 24.01},
                            "diagnostic_status": "WATCH",
                            "evidence_class": "MIS_AFFINE_WATCH",
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

        inputs = []
        for index, rel in enumerate(EXPECTED_INPUT_PATHS, start=1):
            source = operational / rel
            source.parent.mkdir(parents=True, exist_ok=True)
            payload = f"frozen-input-{index}\n".encode("utf-8")
            source.write_bytes(payload)
            inputs.append({"path": rel, "sha256": sha256(payload)})

        output_root.mkdir(parents=True, exist_ok=True)
        output_bytes = b"derived-output"
        output_name = "output.json"
        archive = output_root / "artifact.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(output_name, output_bytes)
        archive_digest = "sha256:" + sha256(archive.read_bytes())
        metadata = {
            "id": 7,
            "name": "artifact",
            "expired": False,
            "digest": archive_digest,
            "workflow_run": {"id": 42, "head_sha": EXPECTED_OPERATIONAL_COMMIT},
        }
        (output_root / "artifact-metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        model = {
            "model_generation_id": "N12-CEW-MG-TEST",
            "canonical_snapshot_id": EXPECTED_SNAPSHOT,
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
            "inputs": inputs,
            "output": {
                "identity": output_name,
                "sha256": sha256(output_bytes),
                "size_bytes": len(output_bytes),
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
        receipt.write_text(
            json.dumps(
                {
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
                    "output_file": output_name,
                    "output_sha256": sha256(output_bytes),
                    "output_size_bytes": len(output_bytes),
                    "input_sha256": {item["path"]: item["sha256"] for item in inputs},
                    "verification": {"status": "PASS", "workflow_run_id": 42},
                }
            ),
            encoding="utf-8",
        )
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
            "registration_source": registration_source,
            "archive": archive,
        }

    def validate(self, root: Path, operational: Path, output_root: Path):
        v = load_validator()
        with patch.dict(
            os.environ,
            {
                "CEW_OPERATIONAL_SOURCE_ROOT": str(operational),
                "CEW_MODEL_OUTPUT_ROOT": str(output_root),
            },
        ):
            return v.validate_project(root)

    def test_model_generation_requires_exact_six_input_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd, tempfile.TemporaryDirectory() as od:
            root, operational, output_root = Path(td), Path(sd), Path(od)
            paths = self.make_project(root, operational, output_root)
            model = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            removed = model["inputs"].pop()
            paths["manifest"].write_text(json.dumps(model), encoding="utf-8")
            receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
            receipt["input_sha256"].pop(removed["path"])
            paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")
            result = self.validate(root, operational, output_root)
        self.assertFalse(result["qualified"])
        self.assertIn("MODEL_GENERATION_INPUT_SET_INVALID", result["errors"])

    def test_canonical_snapshot_must_identify_expected_frozen_commit(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd, tempfile.TemporaryDirectory() as od:
            root, operational, output_root = Path(td), Path(sd), Path(od)
            paths = self.make_project(root, operational, output_root)
            model = json.loads(paths["manifest"].read_text(encoding="utf-8"))
            model["canonical_snapshot_id"] = None
            paths["manifest"].write_text(json.dumps(model), encoding="utf-8")
            result = self.validate(root, operational, output_root)
        self.assertFalse(result["qualified"])
        self.assertIn("MODEL_GENERATION_CANONICAL_SNAPSHOT_INVALID", result["errors"])

    def test_registration_fixture_must_match_pinned_source_blob_and_values(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd, tempfile.TemporaryDirectory() as od:
            root, operational, output_root = Path(td), Path(sd), Path(od)
            paths = self.make_project(root, operational, output_root)
            fixture = json.loads(paths["fixture"].read_text(encoding="utf-8"))
            fixture["source_git_blob_sha"] = "fake"
            fixture["examples"][0]["observed"]["u"] = 999.0
            paths["fixture"].write_text(json.dumps(fixture), encoding="utf-8")
            result = self.validate(root, operational, output_root)
        self.assertFalse(result["qualified"])
        self.assertIn("REGISTRATION_SOURCE_BLOB_SHA_MISMATCH", result["errors"])
        self.assertTrue(any(error.startswith("REGISTRATION_SOURCE_EXAMPLE_MISMATCH") for error in result["errors"]))

    def test_model_generation_output_bytes_and_archive_are_verified(self) -> None:
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as sd, tempfile.TemporaryDirectory() as od:
            root, operational, output_root = Path(td), Path(sd), Path(od)
            paths = self.make_project(root, operational, output_root)
            with zipfile.ZipFile(paths["archive"], "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("output.json", b"tampered-output")
            result = self.validate(root, operational, output_root)
        self.assertFalse(result["qualified"])
        self.assertTrue(
            "MODEL_GENERATION_ARTIFACT_ARCHIVE_DIGEST_MISMATCH" in result["errors"]
            or "MODEL_GENERATION_OUTPUT_SHA256_MISMATCH" in result["errors"]
        )


if __name__ == "__main__":
    unittest.main()
