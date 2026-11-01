from __future__ import annotations

import json
import unittest

try:
    from experiments.cew_col03d.recovery import build_recovery_artifacts
except (ImportError, ModuleNotFoundError):
    build_recovery_artifacts = None


PREDECESSOR_SHA = "a9daa18ddfb56eaf1834ad17f329e2f2db0af72e"
PACKAGE_SHA256 = "10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d"


def _inputs():
    package = {
        "logical_name": "Ariano_Irpino_DXF_strutturale_v25.zip",
        "sha256": PACKAGE_SHA256,
        "size_bytes": 5_345_286,
        "member_count": 91,
        "verification_state": "EXTERNALLY_VERIFIED_IMMUTABLE_WITNESS",
        "repository_materialized": False,
        "exact_source_replayable": False,
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "identity_promotion_authorized": False,
    }
    members = [
        {
            "artifact_name": f"artifact-{index:02d}",
            "sha256": f"sha-{index:02d}",
            "size_bytes": index,
            "materialization_state": "MATERIALIZED_VERIFIED",
            "transport_reconstruction_state": "LOSSLESS_RECONSTRUCTED",
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
        }
        for index in range(1, 9)
    ]
    inventory = [
        {
            "artifact_name": row["artifact_name"],
            "governed_inventory_member": True,
            "package_presence_state": "PRESENT",
            "materialization_state": "PACKAGE_MEMBER_DISCOVERED",
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
        }
        for row in members
    ]
    csv_evidence = [
        {
            "artifact_name": "rows-a.csv",
            "row_count": 57,
            "source_sha256": "csv-a",
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
            "structural_identity_authorized": False,
        },
        {
            "artifact_name": "rows-b.csv",
            "row_count": 27,
            "source_sha256": "csv-b",
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
            "structural_identity_authorized": False,
        },
    ]
    dxf_evidence = [
        {
            "artifact_name": "drawing-a.dxf",
            "source_sha256": "dxf-a",
            "dxf_version": "AC1027",
            "entity_count": 10,
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
        }
    ]
    quality = {
        "status": "EVIDENCE_ONLY",
        "row_counts": {"rows-a.csv": 57, "rows-b.csv": 27},
        "historical_state_counts": {"RIF": 4, "VER": 3},
        "blocking_findings": ["COLUMN_ASSOCIATION_NOT_DEMONSTRATED"],
        "identity_promotion_authorized": False,
        "structural_identity_authorized": False,
        "section_assignment_authorized": False,
        "vertical_chain_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
    }
    return package, members, inventory, csv_evidence, dxf_evidence, quality


class RecoveryClosureTests(unittest.TestCase):
    def test_builds_exact_five_artifact_surface_with_fail_closed_package_replay(self):
        self.assertIsNotNone(build_recovery_artifacts, "COL-03D recovery implementation missing")
        package, members, inventory, csv_evidence, dxf_evidence, quality = _inputs()
        artifacts = build_recovery_artifacts(
            predecessor_sha=PREDECESSOR_SHA,
            package_witness=package,
            member_rows=members,
            inventory_rows=inventory,
            csv_evidence=csv_evidence,
            dxf_evidence=dxf_evidence,
            historical_quality=quality,
        )
        self.assertEqual(
            set(artifacts),
            {
                "historical-package-recovery-manifest.json",
                "historical-member-manifest.json",
                "historical-derived-data-quality.json",
                "historical-recovery-reconciliation.json",
                "historical-recovery-closure.json",
            },
        )
        closure = artifacts["historical-recovery-closure.json"]
        self.assertTrue(closure["historical_package_source_verified"])
        self.assertFalse(closure["historical_package_repository_materialized"])
        self.assertFalse(closure["historical_package_exact_source_replayable"])
        self.assertTrue(closure["required_historical_members_materialized"])
        self.assertTrue(closure["historical_row_level_evidence_recovered"])
        self.assertFalse(closure["historical_evidence_identity_promoted"])
        self.assertFalse(closure["col03d_exact_source_qualification_complete"])
        self.assertIn("HISTORICAL_PACKAGE_NOT_REPOSITORY_REPLAYABLE", closure["qualification_blockers"])
        for key in (
            "support_identity_authorized",
            "text_identity_binding_authorized",
            "family_assignment_authorized",
            "section_assignment_authorized",
            "fixed_line_assignment_authorized",
            "vertical_chain_assignment_authorized",
            "structural_identity_authorized",
            "canonical_node_assignment_authorized",
            "canonical_geometry_authorized",
            "canonical_write_authorized",
            "g2c_promotion_authorized",
            "g3_authorized",
            "merge_authorized",
        ):
            self.assertFalse(closure[key], key)

    def test_output_is_deterministic_under_input_order_changes(self):
        self.assertIsNotNone(build_recovery_artifacts, "COL-03D recovery implementation missing")
        package, members, inventory, csv_evidence, dxf_evidence, quality = _inputs()
        first = build_recovery_artifacts(
            predecessor_sha=PREDECESSOR_SHA,
            package_witness=package,
            member_rows=members,
            inventory_rows=inventory,
            csv_evidence=csv_evidence,
            dxf_evidence=dxf_evidence,
            historical_quality=quality,
        )
        second = build_recovery_artifacts(
            predecessor_sha=PREDECESSOR_SHA,
            package_witness=dict(reversed(list(package.items()))),
            member_rows=list(reversed(members)),
            inventory_rows=list(reversed(inventory)),
            csv_evidence=list(reversed(csv_evidence)),
            dxf_evidence=list(reversed(dxf_evidence)),
            historical_quality=dict(reversed(list(quality.items()))),
        )
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_authority_drift_fails_closed(self):
        self.assertIsNotNone(build_recovery_artifacts, "COL-03D recovery implementation missing")
        package, members, inventory, csv_evidence, dxf_evidence, quality = _inputs()
        members[0]["promotion_authorized"] = True
        with self.assertRaisesRegex(ValueError, "HISTORICAL_RECOVERY_AUTHORITY_DRIFT"):
            build_recovery_artifacts(
                predecessor_sha=PREDECESSOR_SHA,
                package_witness=package,
                member_rows=members,
                inventory_rows=inventory,
                csv_evidence=csv_evidence,
                dxf_evidence=dxf_evidence,
                historical_quality=quality,
            )


if __name__ == "__main__":
    unittest.main()
