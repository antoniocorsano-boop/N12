from __future__ import annotations

import json
import unittest

try:
    from experiments.cew_col03d.recovery import build_recovery_artifacts
except (ImportError, ModuleNotFoundError):
    build_recovery_artifacts = None


PREDECESSOR_SHA = "a9daa18ddfb56eaf1834ad17f329e2f2db0af72e"
PACKAGE_SHA256 = "10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d"
MEMBER_NAMES = (
    "TAV5_CARPENTERIA.dxf",
    "TAV6_TRAVI.dxf",
    "TAV7_PILASTRI.dxf",
    "ABACO_TOPOLOGICO_TAV5_v11.csv",
    "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv",
    "MATRICE_PILASTRI_27x5_v22.csv",
    "ABACO_TRAVI_TAV6_v23.csv",
    "ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv",
)
CSV_COUNTS = {
    "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv": 27,
    "ABACO_TOPOLOGICO_TAV5_v11.csv": 57,
    "ABACO_TRAVI_TAV6_v23.csv": 46,
    "ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv": 46,
    "MATRICE_PILASTRI_27x5_v22.csv": 135,
}
DXF_NAMES = ("TAV5_CARPENTERIA.dxf", "TAV6_TRAVI.dxf", "TAV7_PILASTRI.dxf")


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
            "artifact_name": name,
            "sha256": f"sha-{index:02d}",
            "size_bytes": index,
            "materialization_state": "MATERIALIZED_VERIFIED",
            "transport_reconstruction_state": "LOSSLESS_RECONSTRUCTED",
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
        }
        for index, name in enumerate(MEMBER_NAMES, start=1)
    ]
    inventory = [
        {
            "artifact_name": name,
            "governed_inventory_member": True,
            "package_presence_state": "PRESENT",
            "materialization_state": "PACKAGE_MEMBER_DISCOVERED",
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
        }
        for name in MEMBER_NAMES
    ]
    csv_evidence = [
        {
            "artifact_name": name,
            "row_count": count,
            "source_sha256": f"csv-{index:02d}",
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
            "structural_identity_authorized": False,
        }
        for index, (name, count) in enumerate(sorted(CSV_COUNTS.items()), start=1)
    ]
    dxf_evidence = [
        {
            "artifact_name": name,
            "source_sha256": f"dxf-{index:02d}",
            "dxf_version": "AC1027",
            "entity_count": 10,
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
        }
        for index, name in enumerate(DXF_NAMES, start=1)
    ]
    quality = {
        "status": "EVIDENCE_ONLY",
        "row_counts": dict(CSV_COUNTS),
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
    def _build(self, package, members, inventory, csv_evidence, dxf_evidence, quality):
        return build_recovery_artifacts(
            predecessor_sha=PREDECESSOR_SHA,
            package_witness=package,
            member_rows=members,
            inventory_rows=inventory,
            csv_evidence=csv_evidence,
            dxf_evidence=dxf_evidence,
            historical_quality=quality,
        )

    def test_builds_exact_five_artifact_surface_with_fail_closed_package_replay(self):
        self.assertIsNotNone(build_recovery_artifacts, "COL-03D recovery implementation missing")
        artifacts = self._build(*_inputs())
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
        self.assertEqual(closure["qualification_blockers"], ["HISTORICAL_PACKAGE_NOT_REPOSITORY_REPLAYABLE"])
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
        package, members, inventory, csv_evidence, dxf_evidence, quality = _inputs()
        first = self._build(package, members, inventory, csv_evidence, dxf_evidence, quality)
        second = self._build(
            dict(reversed(list(package.items()))),
            list(reversed(members)),
            list(reversed(inventory)),
            list(reversed(csv_evidence)),
            list(reversed(dxf_evidence)),
            dict(reversed(list(quality.items()))),
        )
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_authority_drift_fails_closed(self):
        package, members, inventory, csv_evidence, dxf_evidence, quality = _inputs()
        members[0]["promotion_authorized"] = True
        with self.assertRaisesRegex(ValueError, "HISTORICAL_RECOVERY_AUTHORITY_DRIFT"):
            self._build(package, members, inventory, csv_evidence, dxf_evidence, quality)

    def test_duplicate_member_names_cannot_fake_required_set(self):
        package, members, inventory, csv_evidence, dxf_evidence, quality = _inputs()
        members[-1] = dict(members[0])
        with self.assertRaisesRegex(ValueError, "HISTORICAL_RECOVERY_MEMBER_SET_DRIFT"):
            self._build(package, members, inventory, csv_evidence, dxf_evidence, quality)

    def test_missing_required_csv_cannot_fake_row_level_recovery(self):
        package, members, inventory, csv_evidence, dxf_evidence, quality = _inputs()
        csv_evidence.pop()
        with self.assertRaisesRegex(ValueError, "HISTORICAL_RECOVERY_CSV_SET_DRIFT"):
            self._build(package, members, inventory, csv_evidence, dxf_evidence, quality)

    def test_inventory_set_must_match_required_member_set_exactly(self):
        package, members, inventory, csv_evidence, dxf_evidence, quality = _inputs()
        inventory.pop()
        with self.assertRaisesRegex(ValueError, "HISTORICAL_RECOVERY_INVENTORY_SET_DRIFT"):
            self._build(package, members, inventory, csv_evidence, dxf_evidence, quality)

    def test_package_witness_contract_drift_fails_closed(self):
        package, members, inventory, csv_evidence, dxf_evidence, quality = _inputs()
        package["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "HISTORICAL_RECOVERY_PACKAGE_WITNESS_DRIFT"):
            self._build(package, members, inventory, csv_evidence, dxf_evidence, quality)

    def test_package_cannot_claim_exact_replay_without_repository_materialization(self):
        package, members, inventory, csv_evidence, dxf_evidence, quality = _inputs()
        package["exact_source_replayable"] = True
        with self.assertRaisesRegex(ValueError, "HISTORICAL_RECOVERY_PACKAGE_WITNESS_DRIFT"):
            self._build(package, members, inventory, csv_evidence, dxf_evidence, quality)


if __name__ == "__main__":
    unittest.main()
