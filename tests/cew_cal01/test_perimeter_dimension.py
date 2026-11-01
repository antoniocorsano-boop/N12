import unittest

try:
    from experiments.cew_cal01.perimeter_dimension import (
        _normalize_for_plan_detection,
        _select_structural_envelope_bbox,
        build_perimeter_bands,
        classify_perimeter_observations,
    )
except (ImportError, ModuleNotFoundError):
    _normalize_for_plan_detection = None
    _select_structural_envelope_bbox = None
    build_perimeter_bands = None
    classify_perimeter_observations = None


class Cal01PerimeterDimensionContractTests(unittest.TestCase):
    def test_contract_functions_exist(self):
        self.assertTrue(callable(_normalize_for_plan_detection))
        self.assertTrue(callable(_select_structural_envelope_bbox))
        self.assertTrue(callable(build_perimeter_bands))
        self.assertTrue(callable(classify_perimeter_observations))

    def test_portrait_page_is_normalized_counterclockwise_for_plan_detection(self):
        import numpy as np

        image = np.full((100, 50), 255, dtype=np.uint8)
        normalized, record = _normalize_for_plan_detection(image)
        self.assertEqual(normalized.shape, (50, 100))
        self.assertEqual(record["transform"], "ROTATE_90_COUNTERCLOCKWISE")
        self.assertEqual(record["source_width_px"], 50)
        self.assertEqual(record["source_height_px"], 100)
        self.assertEqual(record["normalized_width_px"], 100)
        self.assertEqual(record["normalized_height_px"], 50)

    def test_structural_envelope_selection_rejects_large_title_block_by_span(self):
        components = [
            {"bbox_px": [0, 35, 55, 100], "ink_area_px": 4000},
            {"bbox_px": [70, 5, 195, 95], "ink_area_px": 1500},
            {"bbox_px": [90, 10, 145, 45], "ink_area_px": 3000},
        ]
        selected = _select_structural_envelope_bbox(
            components,
            page_width=200,
            page_height=100,
            min_width_fraction=0.45,
            min_height_fraction=0.60,
        )
        self.assertEqual(selected, [70, 5, 195, 95])

    def test_perimeter_bands_are_deterministic_and_clipped_to_page(self):
        bands = build_perimeter_bands(
            [40, 20, 160, 80],
            page_width=200,
            page_height=100,
            outer_margin_px=25,
            inner_overlap_px=5,
        )
        self.assertEqual(
            bands,
            [
                {"side": "TOP", "bbox_px": [40, 0, 160, 25]},
                {"side": "RIGHT", "bbox_px": [155, 20, 185, 80]},
                {"side": "BOTTOM", "bbox_px": [40, 75, 160, 100]},
                {"side": "LEFT", "bbox_px": [15, 20, 45, 80]},
            ],
        )

    def test_only_two_reference_geometry_becomes_perimeter_candidate(self):
        observations = [
            {
                "observation_id": "OBS-BOUND",
                "normalized_metric_text": "4.70",
                "metric_value_m": 4.70,
                "geometry": {
                    "geometrically_bound": True,
                    "geometry_role": "DIMENSION_LINE_WITH_TWO_REFERENCES",
                    "endpoint_a_px": [10.0, 20.0],
                    "endpoint_b_px": [90.0, 20.0],
                },
            },
            {
                "observation_id": "OBS-SECTION",
                "normalized_metric_text": "0.70",
                "metric_value_m": 0.70,
                "geometry": {
                    "geometrically_bound": False,
                    "reason": "TWO_REFERENCE_LINES_NOT_OBSERVED",
                },
            },
        ]
        result = classify_perimeter_observations(observations)
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["candidates"][0]["observation_id"], "OBS-BOUND")
        self.assertEqual(result["candidates"][0]["semantic_role"], "PERIMETER_LINEAR_DIMENSION_CANDIDATE")
        self.assertEqual(result["rejected_observation_count"], 1)
        self.assertEqual(result["status"], "PERIMETER_DIMENSION_CHAINS_OBSERVED")
        self.assertEqual(result["primary_anchor_count"], 0)

    def test_zero_bound_observations_is_valid_closed_result(self):
        result = classify_perimeter_observations(
            [
                {
                    "observation_id": "OBS-UNBOUND",
                    "geometry": {"geometrically_bound": False, "reason": "NO_LOCAL_LINES"},
                }
            ]
        )
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["status"], "PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED")
        self.assertEqual(result["primary_anchor_count"], 0)


if __name__ == "__main__":
    unittest.main()
