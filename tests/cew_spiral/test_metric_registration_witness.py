from __future__ import annotations

import unittest

from cew_spiral.metric_registration_witness import (
    build_metric_registration_witness,
    compare_witness_to_historical_supports,
)


REGISTRATION = {
    "sheet_id": "TAV-05S",
    "level_id": "G4",
    "source_frame": "ROT90_CCW_300DPI",
    "frame_width_px": "12530",
    "frame_height_px": "7016",
    "registration_method": "SIFT_RANSAC_AFFINE_TO_TAV06S_PLUS_TAV06S_NUMBERED_SUPPORT_ANCHOR",
    "anchor_or_good_match_count": "212",
    "inlier_count": "160",
    "qa_rms_px_preview": "0.744029",
    "metric_x_from_u": "0.00000225238111",
    "metric_x_from_v": "-0.00415500526",
    "metric_x_offset": "20.83078859",
    "metric_y_from_u": "0.00419596604",
    "metric_y_from_v": "-0.0000367109668",
    "metric_y_offset": "-15.07490278",
    "evidence_state": "MIS+DOC",
    "validation_state": "CROSS_VALIDATED",
    "usage_rule": "REGISTER_SHEET_TO_COMMON_PT_XY",
}


def bridge() -> dict:
    return {
        "source": {
            "sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
            "path": "archive/documentazione_originaria/tavola 5.pdf",
            "page_index": 0,
        },
        "governed_raster": {
            "frame": "RASTER_PIXEL",
            "width_px": 7016,
            "height_px": 12530,
            "raster_sha256": "4" * 64,
            "renderer_tool_id": "pypdfium2",
            "renderer_tool_version": "5.14.0",
        },
        "occurrence_bridge": [
            {
                "occurrence_id": "COL-OCC-0001",
                "object_candidate_id": "CEW-B01-OBJ-000000000000000000000001",
                "evidence_candidate_id": "CEW-B01-EV-000000000000000000000001",
                "pixel_geometry": {
                    "frame": "RASTER_PIXEL",
                    "x": 100.0,
                    "y": 200.0,
                    "width": 20.0,
                    "height": 40.0,
                },
                "structural_identity_authorized": False,
                "canonical_write_authorized": False,
            }
        ],
        "structural_candidate_count": 1,
        "authority": {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
        },
    }


class MetricRegistrationWitnessTests(unittest.TestCase):
    def test_projects_candidate_center_only_as_non_authoritative_witness(self) -> None:
        result = build_metric_registration_witness(
            structural_bridge=bridge(),
            registration=REGISTRATION,
            registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
            registration_provenance="HISTORICAL_NONREPLAYABLE_WITNESS",
        )
        self.assertEqual(result["projection_count"], 1)
        row = result["projections"][0]
        # Current portrait raster and historical ROT90_CCW frame are exact swapped dimensions.
        self.assertAlmostEqual(row["registered_u_px"], 220.0, places=9)
        self.assertAlmostEqual(row["registered_v_px"], 6906.0, places=9)
        expected_x = 0.00000225238111 * 220.0 - 0.00415500526 * 6906.0 + 20.83078859
        expected_y = 0.00419596604 * 220.0 - 0.0000367109668 * 6906.0 - 15.07490278
        self.assertAlmostEqual(row["projected_x_m"], expected_x, places=9)
        self.assertAlmostEqual(row["projected_y_m"], expected_y, places=9)
        self.assertEqual(row["metric_state"], "HISTORICAL_WITNESS_PROJECTION_ONLY")
        self.assertFalse(row["canonical_geometry_authorized"])
        self.assertFalse(row["structural_identity_authorized"])
        self.assertFalse(result["authority"]["canonical_write_authorized"])
        self.assertFalse(result["authority"]["m0g_authorized"])

    def test_rejects_frame_or_provenance_drift(self) -> None:
        bad = dict(REGISTRATION)
        bad["frame_width_px"] = "12529"
        with self.assertRaisesRegex(ValueError, "REGISTRATION_FRAME_MISMATCH"):
            build_metric_registration_witness(
                structural_bridge=bridge(),
                registration=bad,
                registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
                registration_provenance="HISTORICAL_NONREPLAYABLE_WITNESS",
            )
        with self.assertRaisesRegex(ValueError, "REGISTRATION_PROVENANCE_NOT_WITNESS"):
            build_metric_registration_witness(
                structural_bridge=bridge(),
                registration=REGISTRATION,
                registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
                registration_provenance="CANONICAL",
            )

    def test_historical_nearest_support_is_audit_only_never_binding(self) -> None:
        witness = build_metric_registration_witness(
            structural_bridge=bridge(),
            registration=REGISTRATION,
            registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
            registration_provenance="HISTORICAL_NONREPLAYABLE_WITNESS",
        )
        supports = [
            {"node_id": "M0G-C-G4-1", "level_id": "G4", "node_role": "SUPPORT_CORE", "support_id": "1", "x_m": 1.0, "y_m": -14.4},
            {"node_id": "M0G-C-G4-2", "level_id": "G4", "node_role": "SUPPORT_CORE", "support_id": "2", "x_m": 10.0, "y_m": 10.0},
        ]
        audit = compare_witness_to_historical_supports(witness=witness, supports=supports, level_id="G4")
        self.assertEqual(audit["comparison_count"], 1)
        row = audit["comparisons"][0]
        self.assertEqual(row["nearest_historical_node_id"], "M0G-C-G4-1")
        self.assertEqual(row["binding_status"], "NO_AUTOMATIC_BINDING")
        self.assertFalse(row["historical_witness_may_mutate_current_candidate"])
        self.assertFalse(audit["authority"]["canonical_geometry_authorized"])

    def test_same_inputs_are_deterministic(self) -> None:
        kwargs = dict(
            structural_bridge=bridge(),
            registration=REGISTRATION,
            registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
            registration_provenance="HISTORICAL_NONREPLAYABLE_WITNESS",
        )
        self.assertEqual(build_metric_registration_witness(**kwargs), build_metric_registration_witness(**kwargs))


if __name__ == "__main__":
    unittest.main()
