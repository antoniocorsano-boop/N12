import unittest

from experiments.cew_cal01.numeric_role import dimension_tick_relation
from experiments.cew_cal01.semantic_exact_source import (
    build_confirmation_pass_plan,
    merge_local_line_evidence,
    select_confirmation_token,
)


class Cal01SemanticConfirmationContractTests(unittest.TestCase):
    def test_confirmation_plan_reuses_only_observed_tile_rotation_pairs(self):
        cluster = {
            "observations": [
                {"tile_index": 7, "tile_bounds_px": [3600, 5400, 5800, 7600], "ocr_rotation_degrees": 270},
                {"tile_index": 8, "tile_bounds_px": [4800, 5400, 7000, 7600], "ocr_rotation_degrees": 270},
                {"tile_index": 7, "tile_bounds_px": [3600, 5400, 5800, 7600], "ocr_rotation_degrees": 270},
            ]
        }
        plan = build_confirmation_pass_plan(cluster)
        self.assertEqual(len(plan), 4)
        self.assertEqual(
            {(item["tile_index"], item["rotation_degrees"], item["preprocess_mode"], item["psm"]) for item in plan},
            {
                (7, 270, "RAW_GRAYSCALE", 6),
                (7, 270, "LINE_SUPPRESSED", 6),
                (8, 270, "RAW_GRAYSCALE", 6),
                (8, 270, "LINE_SUPPRESSED", 6),
            },
        )

    def test_confirmation_token_selects_nearest_numeric_observation_only(self):
        target = [100.0, 160.0, 140.0, 220.0]
        tokens = [
            {"text": "120", "confidence": 81.0, "bbox_px": [102.0, 159.0, 142.0, 221.0]},
            {"text": "25", "confidence": 95.0, "bbox_px": [170.0, 160.0, 196.0, 220.0]},
            {"text": "N12", "confidence": 99.0, "bbox_px": [101.0, 160.0, 141.0, 220.0]},
        ]
        selected = select_confirmation_token(tokens, target_bbox_px=target)
        self.assertIsNotNone(selected)
        self.assertEqual(selected["text"], "120")
        self.assertEqual(selected["confidence"], 81.0)

    def test_confirmation_token_fails_closed_when_numeric_tokens_are_too_far(self):
        selected = select_confirmation_token(
            [{"text": "120", "confidence": 99.0, "bbox_px": [400.0, 400.0, 440.0, 420.0]}],
            target_bbox_px=[100.0, 160.0, 140.0, 220.0],
        )
        self.assertIsNone(selected)

    def test_local_tick_channel_recovers_source_regression_without_replacing_main_lines(self):
        # Captured from the exact-source TAV.5 120-dimension neighbourhood.
        primary = [
            [2400.0, 5847.0, 2405.0, 6140.0],
            [2071.0, 5885.0, 2643.0, 5876.0],
            [2108.0, 6126.0, 2696.0, 6116.0],
        ]
        short_tick_channel = [
            [2400.0, 5870.0, 2406.0, 5884.0],
            [2388.0, 6111.0, 2419.0, 6122.0],
            [2000.0, 5800.0, 2600.0, 6400.0],  # long structural diagonal: must be excluded
        ]
        merged = merge_local_line_evidence(primary, short_tick_channel, max_tick_length_px=90.0)
        self.assertEqual(merged[:3], primary)
        self.assertIn([2400.0, 5870.0, 2406.0, 5884.0], merged)
        self.assertIn([2388.0, 6111.0, 2419.0, 6122.0], merged)
        self.assertNotIn([2000.0, 5800.0, 2600.0, 6400.0], merged)

        relation = dimension_tick_relation(
            merged,
            token_bbox_px=[2413.0, 5940.0, 2452.0, 6033.0],
            expected_orientation="VERTICAL",
        )
        self.assertTrue(relation["confirmed"])
        self.assertEqual(relation["tick_style"], "DIAGONAL_SLASH")
        self.assertLess(relation["endpoint_a_px"][1], 5900.0)
        self.assertGreater(relation["endpoint_b_px"][1], 6100.0)


if __name__ == "__main__":
    unittest.main()
