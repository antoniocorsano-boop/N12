from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_cew_contract_01_closure.py"
REGISTRATION_FIXTURE = ROOT / "evidence" / "cew-contract-01" / "fixtures" / "N12_REGISTRATION_UNCERTAINTY_v1.json"
MODEL_GENERATION = ROOT / "evidence" / "cew-contract-01" / "model-generation" / "N12_CEW_MODEL_GENERATION_v1.json"
MODEL_RECEIPT = ROOT / "evidence" / "cew-contract-01" / "model-generation" / "N12_CEW_MODEL_GENERATION_RECEIPT_v1.json"
MINIMALITY = ROOT / "evidence" / "cew-contract-01" / "CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv"


def load_validator():
    if not VALIDATOR.exists():
        raise AssertionError("closure validator script is missing")
    spec = importlib.util.spec_from_file_location("cew_contract_01_closure", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load closure validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClosureValidatorUnitTests(unittest.TestCase):
    def test_missing_closure_artifacts_fail_closed(self) -> None:
        v = load_validator()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = v.validate_project(root)
        self.assertFalse(result["qualified"])
        self.assertIn("REGISTRATION_UNCERTAINTY_FIXTURE_MISSING", result["errors"])
        self.assertIn("MODEL_GENERATION_MANIFEST_MISSING", result["errors"])
        self.assertIn("STRUCTURAL_TYPE_MINIMALITY_MISSING", result["errors"])

    def test_gate_requires_exactly_eleven_pass_rows(self) -> None:
        v = load_validator()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            matrix = root / "docs" / "cew-contract" / "CEW_CONTRACT_01_CONFORMANCE_MATRIX.csv"
            matrix.parent.mkdir(parents=True)
            matrix.write_text(
                "test_id,status\n"
                + "".join(f"C01-T{i:02d},PASS\n" for i in range(1, 12)),
                encoding="utf-8",
            )
            status = v.read_gate_status(matrix)
        self.assertEqual(status["count"], 11)
        self.assertEqual(status["pass_count"], 11)
        self.assertTrue(status["all_pass"])

    def test_gate_rejects_non_pass_status(self) -> None:
        v = load_validator()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            matrix = root / "matrix.csv"
            rows = [f"C01-T{i:02d},PASS" for i in range(1, 12)]
            rows[-1] = "C01-T11,REVIEW_REQUIRED"
            matrix.write_text("test_id,status\n" + "\n".join(rows) + "\n", encoding="utf-8")
            status = v.read_gate_status(matrix)
        self.assertFalse(status["all_pass"])
        self.assertEqual(status["pass_count"], 10)

    def test_fem_debt_guard_requires_exact_chain(self) -> None:
        v = load_validator()
        required = "ModelGeneration → SolverRun → Result → Verification → Receipt"
        self.assertTrue(v.fem_debt_declared(f"CEW-FEM-01: {required}"))
        self.assertFalse(v.fem_debt_declared("solver later"))

    def test_registration_uncertainty_rejects_metrology_overclaim(self) -> None:
        v = load_validator()
        good = {
            "uncertainty_type": "REGISTRATION_UNCERTAINTY",
            "source_commit": "d806dcca72779b5a186defe557a7a9b739575a90",
            "source_path": "data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv",
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
                }
            ],
            "interpretive_guard": "Residuals are registration diagnostics, not tolerance, standard error, standard uncertainty, accuracy, or certified metrological uncertainty.",
        }
        self.assertEqual(v.validate_registration_uncertainty(good), [])
        bad = json.loads(json.dumps(good))
        bad["interpretive_guard"] = "residual_px is the certified accuracy tolerance"
        self.assertTrue(v.validate_registration_uncertainty(bad))

    def test_project_registration_fixture_matches_frozen_source_examples(self) -> None:
        self.assertTrue(REGISTRATION_FIXTURE.exists(), "registration fixture must exist")
        data = json.loads(REGISTRATION_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(data["source_commit"], "d806dcca72779b5a186defe557a7a9b739575a90")
        by_id = {str(item["support_id"]): item for item in data["examples"]}
        self.assertEqual(
            by_id["1"],
            {
                "support_id": "1",
                "property_ref": "PT support registration coordinate",
                "unit": "px",
                "observed": {"u": 4096.63, "v": 2823.61},
                "predicted": {"u": 4100.03, "v": 2822.89},
                "residual": {"du": 3.40, "dv": -0.72, "scalar": 3.47},
                "diagnostic_status": "PASS_DIAGNOSTIC",
                "evidence_class": "DOC_METRIC_OR_AXIS",
                "derived_bound": None,
            },
        )
        self.assertEqual(
            by_id["19"],
            {
                "support_id": "19",
                "property_ref": "PT support registration coordinate",
                "unit": "px",
                "observed": {"u": 2458.56, "v": 4200.73},
                "predicted": {"u": 2462.23, "v": 4224.46},
                "residual": {"du": 3.67, "dv": 23.73, "scalar": 24.01},
                "diagnostic_status": "WATCH",
                "evidence_class": "MIS_AFFINE_WATCH",
                "derived_bound": None,
            },
        )

    def test_model_generation_uses_real_workflow_artifact_and_input_digests(self) -> None:
        self.assertTrue(MODEL_GENERATION.exists(), "ModelGeneration manifest must exist")
        self.assertTrue(MODEL_RECEIPT.exists(), "ModelGeneration receipt must exist")
        data = json.loads(MODEL_GENERATION.read_text(encoding="utf-8"))
        self.assertEqual(data["builder"]["source_commit"], "d806dcca72779b5a186defe557a7a9b739575a90")
        self.assertEqual(data["verification"]["workflow_run_id"], 32955421352)
        self.assertEqual(data["output"]["artifact_id"], 9601773275)
        self.assertEqual(data["output"]["sha256"], "4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2")
        self.assertFalse(data["solver_authorized"])
        self.assertFalse(data["calculation_model_ready"])
        expected_inputs = {
            "data/canonical/M0G_GEOMETRY_HANDOFF_v1.json": "e6ce185e5a439e952950f1c9877b6dd35c036dcf4cb837f74da34c34ebe543d8",
            "data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv": "98d309e0c1ae9159c73e0f9d173c139bfeaf9a8335948ead64e9207cad20bce8",
            "data/canonical/M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv": "ce10cf06c6f4a5805afdbb9bd78ffd0d3d79fe5f104e18720b47488a11ffa5d6",
            "data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv": "b174517f418335ca43a66305087a4f7ae87acc224c40e0bbd81ce7d18f3ddc45",
            "data/canonical/M1F_FOUNDATION_MODEL_CURRENT_v1.csv": "aaf3636487618b39dd70c5a363626d2a6d78845ed913c32d6244f2b17c3e1ed0",
            "data/canonical/M1E_FOUNDATION_XY_SOLVER_PROJECTION_RULE_v1.json": "0e2da5eb31d5491ce1c56f27023cdd7635cfe080dc07f87ffb29f6dee938175d",
        }
        self.assertEqual({item["path"]: item["sha256"] for item in data["inputs"]}, expected_inputs)
        receipt = json.loads(MODEL_RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(receipt["receipt_class"], "QUALIFICATION_RECEIPT")
        self.assertFalse(receipt["engineering_result"])
        self.assertEqual(receipt["artifact_archive_digest"], "sha256:5278bec007f427f6535947343b29d0f586da461f4acdac6aa4502aea73a1d5a5")

    def test_project_structural_type_minimality_is_conservative(self) -> None:
        self.assertTrue(MINIMALITY.exists(), "structural type minimality fixture must exist")
        with MINIMALITY.open("r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        by_type = {row["structural_type"]: row for row in rows}
        self.assertEqual(by_type["Wall"]["classification"], "SUPPORTED_EXTENSION")
        expected_core = {"Node", "Column", "Beam", "FoundationElement"}
        actual_core = {name for name, row in by_type.items() if row["classification"] == "CORE_REQUIRED"}
        self.assertEqual(actual_core, expected_core)
        for name in expected_core:
            self.assertTrue(by_type[name]["case_ref"].strip())
        v = load_validator()
        self.assertEqual(v.validate_minimality(MINIMALITY), [])


if __name__ == "__main__":
    unittest.main()
