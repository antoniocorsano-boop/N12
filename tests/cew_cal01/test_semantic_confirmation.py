import unittest

from experiments.cew_cal01.semantic_exact_source import (
    build_confirmation_pass_plan,
    select_confirmation_token,
)


class Cal01SemanticConfirmationContractTests(unittest.TestCase):
    def test_confirmation_plan_reuses_only_observed_tile_rotation_pairs(self):
        cluster = {
            "observations": [
                {
                    "tile_index": 7,
                    "tile_bounds_px": [3600, 5400, 5800, 7600],
                    "ocr_rotation_degrees": 270,
                },
                {
                    "tile_index": 8,
                    "tile_bounds_px": [4800, 5400, 7000, 7600],
                    "ocr_rotation_degrees": 270,
                },
                {
                    "tile_index": 7,
                    "tile_bounds_px": [3600, 5400, 5800, 7600],
                    "ocr_rotation_degrees": 270,
                },
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


if __name__ == "__main__":
    unittest.main()
