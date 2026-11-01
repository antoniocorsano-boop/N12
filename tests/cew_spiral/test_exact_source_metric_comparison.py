from __future__ import annotations

import unittest

from cew_spiral.exact_source_metric_comparison import build_metric_comparison_bundle


REGISTRATION_ROWS = [
    {
        "sheet_id": "TAV-04S",
        "level_id": "G3",
        "source_frame": "ROT90_CCW_300DPI",
        "frame_width_px": "900",
        "frame_height_px": "600",
        "validation_state": "CROSS_VALIDATED",
        "usage_rule": "REGISTER_SHEET_TO_COMMON_PT_XY",
    },
    {
        "sheet_id": "TAV-05S",
        "level_id": "G4",
        "source_frame": "ROT90_CCW_300DPI",
        "frame_width_px": "12530",
        "frame_height_px": "7016",
        "registration_method": "SIFT_RANSAC_AFFINE_TO_TAV06S_PLUS_TAV06S_NUMBERED_SUPPORT_ANCHOR",
        "metric_x_from_u": "0",
        "metric_x_from_v": "-0.004",
        "metric_x_offset": "28",
        "metric_y_from_u": "0.004",
        "metric_y_from_v": "0",
        "metric_y_offset": "0",
        "evidence_state": "MIS+DOC",
        "validation_state": "CROSS_VALIDATED",
        "usage_rule": "REGISTER_SHEET_TO_COMMON_PT_XY",
    },
]


def structural_bridge() -> dict:
    return {
        "source": {"sha256": "2143dbcf" + "0" * 56, "path": "archive/documentazione_originaria/tavola 5.pdf", "page_index": 0},
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
                "occurrence_id": "COL-OCC-0002",
                "object_candidate_id": "OBJ-2",
                "evidence_candidate_id": "EV-2",
                "pixel_geometry": {"frame": "RASTER_PIXEL", "x": 5916.0, "y": 2425.0, "width": 200.0, "height": 150.0},
                "structural_identity_authorized": False,
                "canonical_write_authorized": False,
            },
            {
                "occurrence_id": "COL-OCC-0001",
                "object_candidate_id": "OBJ-1",
                "evidence_candidate_id": "EV-1",
                "pixel_geometry": {"frame": "RASTER_PIXEL", "x": 916.0, "y": 4925.0, "width": 200.0, "height": 150.0},
                "structural_identity_authorized": False,
                "canonical_write_authorized": False,
            },
        ],
        "structural_candidate_count": 2,
        "authority": {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
        },
    }


SUPPORTS = [
    {"node_id": "M0G-C-G4-A", "level_id": "G4", "node_role": "SUPPORT_CORE", "support_id": "A", "x_m": "4.0", "y_m": "16.0"},
    {"node_id": "M0G-C-G4-B", "level_id": "G4", "node_role": "SUPPORT_CORE", "support_id": "B", "x_m": "24.0", "y_m": "8.0"},
    {"node_id": "M0G-C-G3-X", "level_id": "G3", "node_role": "SUPPORT_CORE", "support_id": "X", "x_m": "0.0", "y_m": "0.0"},
]


class ExactSourceMetricComparisonTests(unittest.TestCase):
    def test_builds_deterministic_non_authoritative_distance_bundle(self) -> None:
        result = build_metric_comparison_bundle(
            structural_bridge=structural_bridge(),
            registration_rows=REGISTRATION_ROWS,
            historical_supports=SUPPORTS,
            registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
            comparator_commit="dba5c4c2f09161b731a26bb0f8eab5826f1d136b",
        )
        self.assertEqual(result["projection_count"], 2)
        self.assertEqual(result["comparison_count"], 2)
        self.assertEqual([r["occurrence_id"] for r in result["comparisons"]], ["COL-OCC-0001", "COL-OCC-0002"])
        self.assertEqual(result["summary"]["distance_count"], 2)
        self.assertLessEqual(result["summary"]["min_distance_m"], result["summary"]["median_distance_m"])
        self.assertLessEqual(result["summary"]["median_distance_m"], result["summary"]["max_distance_m"])
        self.assertNotIn("accepted", result["summary"])
        self.assertNotIn("threshold_m", result["summary"])
        self.assertEqual(result["comparison_semantics"], "DISTANCE_AUDIT_ONLY_NO_BINDING_NO_THRESHOLD")
        self.assertFalse(result["authority"]["canonical_geometry_authorized"])
        self.assertFalse(result["authority"]["structural_identity_authorized"])
        self.assertFalse(result["authority"]["canonical_write_authorized"])
        self.assertFalse(result["authority"]["m0g_authorized"])

    def test_rejects_missing_or_duplicate_tav05_registration(self) -> None:
        with self.assertRaisesRegex(ValueError, "TAV05_REGISTRATION_REQUIRED"):
            build_metric_comparison_bundle(
                structural_bridge=structural_bridge(),
                registration_rows=REGISTRATION_ROWS[:1],
                historical_supports=SUPPORTS,
                registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
                comparator_commit="dba5c4c2f09161b731a26bb0f8eab5826f1d136b",
            )
        with self.assertRaisesRegex(ValueError, "TAV05_REGISTRATION_REQUIRED"):
            build_metric_comparison_bundle(
                structural_bridge=structural_bridge(),
                registration_rows=REGISTRATION_ROWS + [dict(REGISTRATION_ROWS[1])],
                historical_supports=SUPPORTS,
                registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
                comparator_commit="dba5c4c2f09161b731a26bb0f8eab5826f1d136b",
            )

    def test_same_inputs_are_deterministic(self) -> None:
        kwargs = dict(
            structural_bridge=structural_bridge(),
            registration_rows=REGISTRATION_ROWS,
            historical_supports=SUPPORTS,
            registration_commit="15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57",
            comparator_commit="dba5c4c2f09161b731a26bb0f8eab5826f1d136b",
        )
        self.assertEqual(build_metric_comparison_bundle(**kwargs), build_metric_comparison_bundle(**kwargs))


if __name__ == "__main__":
    unittest.main()
