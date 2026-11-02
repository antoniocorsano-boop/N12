import unittest

from experiments.cew_cal01.structural_grid_dimension import (
    build_cross_sheet_summary,
    classify_structural_grid_observations,
    select_structural_grid_envelope_bbox,
)


class Cal01StructuralGridDimensionContractTests(unittest.TestCase):
    def test_fragmented_grid_components_are_grouped_without_absorbing_title_block(self):
        components = [
            {"bbox_px": [200, 150, 490, 440], "ink_area_px": 12000},
            {"bbox_px": [510, 150, 800, 440], "ink_area_px": 11500},
            {"bbox_px": [200, 460, 490, 850], "ink_area_px": 13000},
            {"bbox_px": [510, 460, 800, 850], "ink_area_px": 12500},
            {"bbox_px": [20, 20, 180, 130], "ink_area_px": 9000},
        ]
        result = select_structural_grid_envelope_bbox(
            components,
            page_width=1000,
            page_height=1000,
            join_gap_px=30,
        )
        self.assertEqual(result["bbox_px"], [200, 150, 800, 850])
        self.assertEqual(result["selection_mode"], "FRAGMENT_CLUSTER")
        self.assertEqual(result["member_count"], 4)

    def test_fragment_cluster_does_not_bridge_to_title_block_through_tiny_marks(self):
        components = [
            {"bbox_px": [400, 180, 630, 470], "ink_area_px": 9000},
            {"bbox_px": [650, 180, 900, 470], "ink_area_px": 8800},
            {"bbox_px": [400, 490, 630, 820], "ink_area_px": 9200},
            {"bbox_px": [650, 490, 900, 820], "ink_area_px": 9100},
            {"bbox_px": [20, 500, 250, 820], "ink_area_px": 8500},
            {"bbox_px": [270, 790, 285, 805], "ink_area_px": 120},
            {"bbox_px": [305, 790, 320, 805], "ink_area_px": 120},
            {"bbox_px": [340, 790, 355, 805], "ink_area_px": 120},
            {"bbox_px": [375, 790, 390, 805], "ink_area_px": 120},
        ]
        result = select_structural_grid_envelope_bbox(
            components,
            page_width=1000,
            page_height=1000,
            join_gap_px=30,
        )
        self.assertEqual(result["bbox_px"], [400, 180, 900, 820])
        self.assertEqual(result["selection_mode"], "FRAGMENT_CLUSTER")
        self.assertEqual(result["member_count"], 4)

    def test_component_rounding_overflow_is_clipped_to_page_frame(self):
        components = [
            {"bbox_px": [0, 120, 510, 1002], "ink_area_px": 16000},
            {"bbox_px": [530, 120, 1001, 1002], "ink_area_px": 15000},
        ]
        result = select_structural_grid_envelope_bbox(
            components,
            page_width=1000,
            page_height=1000,
            join_gap_px=30,
        )
        self.assertEqual(result["bbox_px"], [0, 120, 510, 1000])
        self.assertEqual(result["selection_mode"], "SINGLE_COMPONENT")
        self.assertTrue(all(0 <= value <= 1000 for value in result["bbox_px"]))

    def test_only_two_reference_geometry_becomes_grid_candidate(self):
        observations = [
            {
                "observation_id": "a",
                "normalized_metric_text": "5.45",
                "metric_value_m": 5.45,
                "source_id": "TAV-01S",
                "geometry": {
                    "geometrically_bound": True,
                    "geometry_role": "DIMENSION_LINE_WITH_TWO_REFERENCES",
                    "orientation": "HORIZONTAL",
                },
            },
            {
                "observation_id": "b",
                "normalized_metric_text": "2.65",
                "metric_value_m": 2.65,
                "source_id": "TAV-01S",
                "geometry": {"geometrically_bound": False, "reason": "NO_LOCAL_LINES"},
            },
        ]
        result = classify_structural_grid_observations(observations)
        self.assertEqual(result["candidate_count"], 1)
        candidate = result["candidates"][0]
        self.assertEqual(candidate["semantic_role"], "STRUCTURAL_GRID_LINEAR_DIMENSION_CANDIDATE")
        self.assertTrue(candidate["primary_visual_validation_required"])
        self.assertFalse(candidate["fit_eligible"])
        self.assertFalse(candidate["metric_anchor_promoted"])
        self.assertEqual(result["primary_anchor_count"], 0)
        self.assertEqual(result["rejected_observation_count"], 1)

    def test_zero_candidate_result_is_valid_and_closed(self):
        result = classify_structural_grid_observations(
            [
                {
                    "observation_id": "a",
                    "source_id": "TAV-02S",
                    "geometry": {"geometrically_bound": False, "reason": "SINGLE_REFERENCE_ONLY"},
                }
            ]
        )
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["status"], "STRUCTURAL_GRID_DIMENSION_CHAINS_NOT_OBSERVED")
        self.assertEqual(result["primary_anchor_count"], 0)

    def test_cross_sheet_equal_values_do_not_auto_match(self):
        discoveries = [
            {
                "source": {"source_id": "TAV-01S", "sha256": "a" * 64},
                "candidate_count": 1,
                "candidates": [{"normalized_metric_text": "5.45", "metric_value_m": 5.45}],
                "discovery_digest": "sha256:111",
            },
            {
                "source": {"source_id": "TAV-02S", "sha256": "b" * 64},
                "candidate_count": 1,
                "candidates": [{"normalized_metric_text": "5.45", "metric_value_m": 5.45}],
                "discovery_digest": "sha256:222",
            },
        ]
        result = build_cross_sheet_summary(discoveries)
        self.assertEqual(result["source_order"], ["TAV-01S", "TAV-02S"])
        self.assertEqual(result["cross_sheet_relation_count"], 0)
        self.assertEqual(result["cross_sheet_matching_status"], "PENDING_HUMAN_VALIDATION")
        self.assertEqual(result["primary_anchor_count"], 0)
        self.assertFalse(result["authority"]["canonical_geometry_authorized"])

    def test_cross_sheet_summary_digest_is_order_independent(self):
        rows = [
            {
                "source": {"source_id": "TAV-01S", "sha256": "a" * 64},
                "candidate_count": 2,
                "candidates": [],
                "discovery_digest": "sha256:111",
            },
            {
                "source": {"source_id": "TAV-02S", "sha256": "b" * 64},
                "candidate_count": 3,
                "candidates": [],
                "discovery_digest": "sha256:222",
            },
        ]
        left = build_cross_sheet_summary(rows)
        right = build_cross_sheet_summary(list(reversed(rows)))
        self.assertEqual(left["cross_sheet_digest"], right["cross_sheet_digest"])
        self.assertEqual(left["sources"], right["sources"])


if __name__ == "__main__":
    unittest.main()
