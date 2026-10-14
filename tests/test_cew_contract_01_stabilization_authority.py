from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "evidence/cew-contract-01/stabilization/N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json"
HIST = ROOT / "evidence/cew-contract-01/stabilization/N12_CEW_MODEL_GENERATION_HISTORICAL_RECEIPT_v1.json"
COMMIT = "d806dcca72779b5a186defe557a7a9b739575a90"
INPUTS = {
    "data/canonical/M0G_GEOMETRY_HANDOFF_v1.json": "e6ce185e5a439e952950f1c9877b6dd35c036dcf4cb837f74da34c34ebe543d8",
    "data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv": "98d309e0c1ae9159c73e0f9d173c139bfeaf9a8335948ead64e9207cad20bce8",
    "data/canonical/M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv": "ce10cf06c6f4a5805afdbb9bd78ffd0d3d79fe5f104e18720b47488a11ffa5d6",
    "data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv": "b174517f418335ca43a66305087a4f7ae87acc224c40e0bbd81ce7d18f3ddc45",
    "data/canonical/M1F_FOUNDATION_MODEL_CURRENT_v1.csv": "aaf3636487618b39dd70c5a363626d2a6d78845ed913c32d6244f2b17c3e1ed0",
    "data/canonical/M1E_FOUNDATION_XY_SOLVER_PROJECTION_RULE_v1.json": "0e2da5eb31d5491ce1c56f27023cdd7635cfe080dc07f87ffb29f6dee938175d",
}


class AuthorityTests(unittest.TestCase):
    def test_frozen_authority_exact_values(self) -> None:
        data = json.loads(AUTH.read_text(encoding="utf-8"))
        self.assertEqual(data["operational_commit"], COMMIT)
        self.assertEqual(data["canonical_snapshot_id"], f"N12-FROZEN-INPUTSET@{COMMIT}")
        self.assertEqual(data["model_generation_id"], "N12-CEW-MG-001")
        self.assertEqual(data["builder"]["path"], "scripts/cew_structural_model_builder.py")
        self.assertEqual(data["builder"]["git_blob_sha"], "4459fd0f519d8bb9425fa1490cc720a2edb0bd0a")
        self.assertEqual({item["path"]: item["sha256"] for item in data["inputs"]}, INPUTS)
        self.assertEqual(data["registration"]["source_path"], "data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv")
        self.assertEqual(data["registration"]["source_git_blob_sha"], "fa28cf034a03d98aaa8e8ac1deb1549ddef6d64a")
        self.assertEqual(data["registration"]["support_ids"], ["1", "19"])
        self.assertEqual(data["output"]["identity"], "N12_CEW_CANONICAL_STRUCTURAL_MODEL_v0.json")
        self.assertEqual(data["output"]["generation_id_inside_artifact"], "N12-CEW-CSM-v0")
        self.assertEqual(data["output"]["sha256"], "4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2")
        self.assertEqual(data["output"]["size_bytes"], 1068121)
        self.assertEqual(data["generated_at"], "2026-08-26T09:54:00.472520+00:00")
        self.assertEqual(
            data["authority_flags"],
            {
                "solver_authorized": False,
                "calculation_model_ready": False,
                "synthetic_solver_result": False,
                "solver_run": False,
                "result_entity_created": False,
            },
        )
        self.assertEqual(sorted(data["gate_evidence"]), [f"C01-T{i:02d}" for i in range(1, 12)])
        self.assertTrue(all(data["gate_evidence"][key] for key in data["gate_evidence"]))

    def test_historical_receipt_is_evidence_not_runtime_dependency(self) -> None:
        data = json.loads(HIST.read_text(encoding="utf-8"))
        self.assertFalse(data["runtime_dependency"])
        self.assertEqual(data["run"]["id"], 32955421352)
        self.assertEqual(data["run"]["workflow_name"], "Validate CEW Structural Model Builder")
        self.assertEqual(data["run"]["workflow_path"], ".github/workflows/validate-cew-structural-model-builder.yml")
        self.assertEqual(data["run"]["head_sha"], COMMIT)
        self.assertEqual(data["run"]["status"], "completed")
        self.assertEqual(data["run"]["conclusion"], "success")
        self.assertEqual(data["artifact"]["id"], 9601773275)
        self.assertEqual(data["artifact"]["archive_digest"], "sha256:5278bec007f427f6535947343b29d0f586da461f4acdac6aa4502aea73a1d5a5")
        self.assertEqual(data["output"]["sha256"], "4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2")
        self.assertEqual(data["output"]["size_bytes"], 1068121)
        self.assertIs(data["verification"]["archive_sha256_verified"], True)
        self.assertIs(data["verification"]["output_sha256_verified"], True)
        self.assertIs(data["verification"]["output_size_verified"], True)


if __name__ == "__main__":
    unittest.main()
