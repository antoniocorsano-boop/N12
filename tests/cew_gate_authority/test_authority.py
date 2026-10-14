from __future__ import annotations

import unittest
from pathlib import Path

from cew_gate_authority.authority import load_authority

A0 = Path("governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json")

EXPECTED_INPUTS = {
    "data/canonical/M0G_GEOMETRY_HANDOFF_v1.json": "e6ce185e5a439e952950f1c9877b6dd35c036dcf4cb837f74da34c34ebe543d8",
    "data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv": "98d309e0c1ae9159c73e0f9d173c139bfeaf9a8335948ead64e9207cad20bce8",
    "data/canonical/M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv": "ce10cf06c6f4a5805afdbb9bd78ffd0d3d79fe5f104e18720b47488a11ffa5d6",
    "data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv": "b174517f418335ca43a66305087a4f7ae87acc224c40e0bbd81ce7d18f3ddc45",
    "data/canonical/M1F_FOUNDATION_MODEL_CURRENT_v1.csv": "aaf3636487618b39dd70c5a363626d2a6d78845ed913c32d6244f2b17c3e1ed0",
    "data/canonical/M1E_FOUNDATION_XY_SOLVER_PROJECTION_RULE_v1.json": "0e2da5eb31d5491ce1c56f27023cdd7635cfe080dc07f87ffb29f6dee938175d",
}

EXPECTED_CANDIDATE_PATHS = {
    "qualification/cew-contract-01/n12/qualification.json",
    "qualification/cew-contract-01/n12/conformance-matrix.csv",
    "qualification/cew-contract-01/n12/evidence-index.json",
    "qualification/cew-contract-01/n12/structural-type-minimality.csv",
    "qualification/cew-contract-01/n12/source-sufficiency.md",
    "qualification/cew-contract-01/n12/registration-uncertainty.json",
    "qualification/cew-contract-01/n12/model-generation.json",
    "qualification/cew-contract-01/n12/model-generation-receipt.json",
    *{
        f"qualification/cew-contract-01/n12/evidence/CASE_{i:02d}_{name}.md"
        for i, name in (
            (1, "DOCUMENTED_PROPERTY"),
            (2, "NO_PROMOTION_OF_ND"),
            (3, "MIXED_EPISTEMIC_STATE"),
            (4, "STRUCTURAL_IDENTITY"),
            (5, "RELATIONSHIP_UNCERTAINTY"),
            (6, "REAL_CONFLICT"),
            (7, "NON_DESTRUCTIVE_UPDATE"),
            (8, "SNAPSHOT_SCENARIO"),
            (9, "END_TO_END_ASSURANCE"),
            (10, "VERIFICATION_RECEIPT"),
            (11, "REGISTRATION_UNCERTAINTY"),
            (12, "MODEL_GENERATION"),
            (13, "CORE_END_TO_END_ASSURANCE"),
        )
    },
}


class FrozenAuthorityTests(unittest.TestCase):
    def test_a0_pins_existing_n12_operational_authority_without_new_engineering_values(self):
        authority = load_authority(A0)
        self.assertEqual(authority.authority_id, "N12_CEW_CONTRACT_01_A0")
        self.assertEqual(authority.operational_commit, "d806dcca72779b5a186defe557a7a9b739575a90")
        self.assertEqual(authority.canonical_snapshot_id, "N12-FROZEN-INPUTSET@d806dcca72779b5a186defe557a7a9b739575a90")
        self.assertEqual(authority.builder.path, "scripts/cew_structural_model_builder.py")
        self.assertEqual(authority.builder.git_blob_sha, "4459fd0f519d8bb9425fa1490cc720a2edb0bd0a")
        self.assertEqual(dict(authority.inputs), EXPECTED_INPUTS)
        self.assertEqual(authority.registration.support_ids, ("1", "19"))
        self.assertEqual(authority.output.sha256, "4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2")
        self.assertEqual(authority.output.size_bytes, 1068121)
        self.assertEqual(authority.output.generated_at, "2026-08-26T09:54:00.472520+00:00")
        self.assertEqual(set(authority.candidate_allowlist), EXPECTED_CANDIDATE_PATHS)
        self.assertEqual(len(authority.candidate_allowlist), 21)
        self.assertEqual(authority.limits.max_blobs, 256)
        self.assertEqual(authority.limits.max_blob_bytes, 8 * 1024 * 1024)
        self.assertEqual(authority.limits.max_aggregate_bytes, 64 * 1024 * 1024)
        self.assertEqual(authority.limits.max_json_depth, 64)
        self.assertEqual(authority.limits.max_csv_rows, 250000)

    def test_a0_requires_all_authority_boundary_flags_false_and_exact_invariants(self):
        authority = load_authority(A0)
        self.assertEqual(tuple(authority.invariants), tuple(f"I{i:02d}" for i in range(1, 18)))
        self.assertEqual(
            authority.authority_boundary,
            {
                "solver_authorized": False,
                "calculation_model_ready": False,
                "synthetic_solver_result": False,
                "solver_run": False,
                "result_entity_created": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
