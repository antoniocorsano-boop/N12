import unittest

from experiments.cew_cal01.semantic_exact_source import (
    build_tight_confirmation_plan,
    select_diverse_tight_consensus,
)


class Cal01TightLocalConfirmationContractTests(unittest.TestCase):
    def test_plan_stays_on_same_source_bbox_and_observed_orientation(self):
        cluster = {
            "representative": {
                "bbox_px": [2413.0, 5940.0, 2452.0, 6033.0],
                "ocr_rotation_degrees": 270,
            }
        }
        plan = build_tight_confirmation_plan(cluster, page_width=7016, page_height=12530)
        self.assertGreaterEqual(len(plan), 6)
        self.assertEqual({item["rotation_degrees"] for item in plan}, {270})
        self.assertEqual({tuple(item["target_bbox_px"]) for item in plan}, {(2413.0, 5940.0, 2452.0, 6033.0)})
        self.assertTrue(all(item["scope"] == "TIGHT_LOCAL_SAME_SOURCE_LOCATION" for item in plan))
        self.assertTrue(all(item["crop_bbox_px"][0] < 2413.0 < item["crop_bbox_px"][2] for item in plan))
        self.assertTrue(all(item["crop_bbox_px"][1] < 5940.0 < item["crop_bbox_px"][3] for item in plan))

    def test_diverse_consensus_requires_distinct_preprocess_psm_families(self):
        observations = [
            {"text": "120", "preprocess_mode": "RAW_GRAYSCALE", "psm": 6},
            {"text": "120", "preprocess_mode": "RAW_GRAYSCALE", "psm": 6},
            {"text": "120", "preprocess_mode": "RAW_GRAYSCALE", "psm": 7},
            {"text": "120", "preprocess_mode": "BINARY_OTSU", "psm": 13},
            {"text": "420", "preprocess_mode": "LINE_SUPPRESSED", "psm": 6},
        ]
        consensus = select_diverse_tight_consensus(observations, minimum_families=3, minimum_margin=1)
        self.assertTrue(consensus["confirmed"])
        self.assertEqual(consensus["text"], "120")
        self.assertEqual(consensus["family_count"], 3)
        self.assertEqual(consensus["runner_up_family_count"], 1)

    def test_duplicate_same_family_cannot_create_consensus(self):
        observations = [
            {"text": "120", "preprocess_mode": "RAW_GRAYSCALE", "psm": 6},
            {"text": "120", "preprocess_mode": "RAW_GRAYSCALE", "psm": 6},
            {"text": "120", "preprocess_mode": "RAW_GRAYSCALE", "psm": 6},
            {"text": "420", "preprocess_mode": "BINARY_OTSU", "psm": 13},
        ]
        consensus = select_diverse_tight_consensus(observations, minimum_families=3, minimum_margin=1)
        self.assertFalse(consensus["confirmed"])
        self.assertEqual(consensus["reason"], "TIGHT_OCR_DIVERSE_CONSENSUS_INSUFFICIENT")

    def test_tie_fails_closed(self):
        observations = [
            {"text": "120", "preprocess_mode": "RAW_GRAYSCALE", "psm": 6},
            {"text": "120", "preprocess_mode": "BINARY_OTSU", "psm": 13},
            {"text": "420", "preprocess_mode": "LINE_SUPPRESSED", "psm": 6},
            {"text": "420", "preprocess_mode": "RAW_GRAYSCALE", "psm": 7},
        ]
        consensus = select_diverse_tight_consensus(observations, minimum_families=2, minimum_margin=1)
        self.assertFalse(consensus["confirmed"])
        self.assertEqual(consensus["reason"], "TIGHT_OCR_DIVERSE_CONSENSUS_INSUFFICIENT")


if __name__ == "__main__":
    unittest.main()
