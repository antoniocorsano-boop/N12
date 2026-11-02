import unittest

from experiments.cew_cal01.intersource_human_review import (
    build_review_board_html,
    compute_context_crop_bbox,
    resolve_normalized_dimensions,
)


class TargetedInterSourceReviewAssetTests(unittest.TestCase):
    def test_context_crop_is_centered_and_clamped_to_source_raster(self):
        self.assertEqual(
            compute_context_crop_bbox([3500.0, 6000.0], 7016, 12530, half_span_px=700),
            [2800, 5300, 4200, 6700],
        )
        self.assertEqual(
            compute_context_crop_bbox([200.0, 12400.0], 7016, 12530, half_span_px=700),
            [0, 11700, 900, 12530],
        )

    def test_normalized_dimensions_follow_explicit_quadrant_transform(self):
        self.assertEqual(resolve_normalized_dimensions(7016, 12914, "IDENTITY"), (7016, 12914))
        self.assertEqual(
            resolve_normalized_dimensions(7016, 12914, "ROTATE_90_COUNTERCLOCKWISE"),
            (12914, 7016),
        )
        self.assertEqual(
            resolve_normalized_dimensions(7016, 12914, "ROTATE_90_CLOCKWISE"),
            (12914, 7016),
        )
        self.assertEqual(resolve_normalized_dimensions(7016, 12914, "ROTATE_180"), (7016, 12914))
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_REVIEW_NORMALIZATION_UNSUPPORTED"):
            resolve_normalized_dimensions(7016, 12914, "FREE_ROTATION")

    def test_static_board_is_evidence_only_and_contains_no_implicit_matching_fields(self):
        manifest = {
            "schema": "CEW_CAL01_INTERSOURCE_TARGETED_HUMAN_REVIEW_v1",
            "review_package_digest": "sha256:" + "1" * 64,
            "tav5_source": {"sha256": "a" * 64},
            "tav5_raster": {"raster_sha256": "b" * 64},
            "tav02_source": {"source_id": "TAV-02S", "sha256": "c" * 64},
            "tav02_lattice_digest": "sha256:" + "d" * 64,
            "tav02_coordinate_frame": "LOCAL_RELATIVE_METRIC",
            "selection_strategy": "SOURCE_ONLY_FARTHEST_POINT_COVERAGE_V1",
            "target_geometry_used_for_selection": False,
            "target_node_ranking_performed": False,
            "automatic_homology_proposed": False,
            "target_overview_asset": {"file": "tav02-lattice-overview.png"},
            "review_items": [
                {
                    "occurrence_id": "COL-OCC-0013",
                    "source_evidence_refs": ["PRIMARY:E13"],
                    "source_context_asset": {"file": "tav5-col-occ-0013-context.png"},
                    "decision_required": "IDENTIFY_PRIMARY_HOMOLOGOUS_LATTICE_NODE_OR_REJECT",
                },
                {
                    "occurrence_id": "COL-OCC-0016",
                    "source_evidence_refs": ["PRIMARY:E16"],
                    "source_context_asset": {"file": "tav5-col-occ-0016-context.png"},
                    "decision_required": "IDENTIFY_PRIMARY_HOMOLOGOUS_LATTICE_NODE_OR_REJECT",
                },
            ],
            "target_lattice_context": [
                {
                    "lattice_node_id": "TAV-02S:LATTICE:X0:Y0",
                    "local_metric_xy_m": [0.0, 0.0],
                    "source_point_normalized_px": [4233.375, 3805.0],
                },
                {
                    "lattice_node_id": "TAV-02S:LATTICE:X1:Y0",
                    "local_metric_xy_m": [4.7, 0.0],
                    "source_point_normalized_px": [5346.2, 3805.0],
                },
            ],
        }
        html = build_review_board_html(manifest)
        self.assertIn("COL-OCC-0013", html)
        self.assertIn("tav5-col-occ-0013-context.png", html)
        self.assertIn("tav02-lattice-overview.png", html)
        self.assertIn("TAV-02S:LATTICE:X0:Y0", html)
        self.assertIn("No target identity is suggested by the system", html)
        self.assertIn("not surveyed or project coordinates", html)
        lowered = html.lower()
        for forbidden in ("nearest", "suggested_identity", "suggested_target", "similarity_score", "confidence_score"):
            self.assertNotIn(forbidden, lowered)


if __name__ == "__main__":
    unittest.main()
