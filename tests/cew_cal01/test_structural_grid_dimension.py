import unittest

from experiments.cew_cal01.structural_grid_dimension import (
    build_cross_sheet_summary,
    classify_structural_grid_observations,
)


class Cal01StructuralGridDimensionContractTests(unittest.TestCase):
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
