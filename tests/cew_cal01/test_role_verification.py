import itertools
import unittest

import experiments.cew_cal01.role_verification as role_verification
from experiments.cew_cal01.role_verification import (
    detect_nearby_closed_frame,
    select_ocr_consensus,
)


class Cal01RoleVerificationContractTests(unittest.TestCase):
    def test_consensus_requires_dominant_repeated_reading(self):
        result = select_ocr_consensus(["120", "120", "120", "129", "120", "129"])
        self.assertEqual(result["text"], "120")
        self.assertEqual(result["count"], 4)
        self.assertEqual(result["runner_up_count"], 2)
        self.assertTrue(result["confirmed"])

    def test_ambiguous_consensus_fails_closed(self):
        result = select_ocr_consensus(["120", "120", "129", "129", "40"])
        self.assertIsNone(result["text"])
        self.assertFalse(result["confirmed"])
        self.assertEqual(result["reason"], "OCR_CONSENSUS_NOT_DOMINANT")

    def test_segment_rectangle_near_token_is_detected(self):
        segments = [
            (20, 20, 80, 20),
            (80, 20, 80, 70),
            (80, 70, 20, 70),
            (20, 70, 20, 20),
        ]
        result = detect_nearby_closed_frame(
            segments,
            token_bbox_px=[82, 30, 105, 55],
            max_distance_px=60,
        )
        self.assertTrue(result["detected"])
        self.assertEqual(result["bbox_px"], [20.0, 20.0, 80.0, 70.0])

    def test_distant_rectangle_does_not_create_section_context(self):
        segments = [
            (20, 20, 80, 20),
            (80, 20, 80, 70),
            (80, 70, 20, 70),
            (20, 70, 20, 20),
        ]
        result = detect_nearby_closed_frame(
            segments,
            token_bbox_px=[220, 230, 245, 255],
            max_distance_px=60,
        )
        self.assertFalse(result["detected"])

    def test_open_three_sided_shape_is_not_a_closed_frame(self):
        segments = [
            (20, 20, 80, 20),
            (80, 20, 80, 70),
            (80, 70, 20, 70),
        ]
        result = detect_nearby_closed_frame(
            segments,
            token_bbox_px=[82, 30, 105, 55],
            max_distance_px=60,
        )
        self.assertFalse(result["detected"])

    def test_dense_context_does_not_regenerate_vertical_pair_space_per_horizontal_pair(self):
        segments = []
        for y in range(20, 201, 10):
            segments.append((20, y, 200, y))
        for x in range(20, 201, 10):
            segments.append((x, 20, x, 200))

        real_combinations = itertools.combinations
        invocation_count = 0

        def counted_combinations(iterable, r):
            nonlocal invocation_count
            invocation_count += 1
            if invocation_count > 2:
                raise AssertionError("CAL01_CLOSED_FRAME_CARTESIAN_REGENERATION")
            return real_combinations(iterable, r)

        original = role_verification.combinations
        role_verification.combinations = counted_combinations
        try:
            result = role_verification.detect_nearby_closed_frame(
                segments,
                token_bbox_px=[92, 92, 108, 108],
                max_distance_px=60,
            )
        finally:
            role_verification.combinations = original

        self.assertTrue(result["detected"])
        self.assertLessEqual(invocation_count, 2)


if __name__ == "__main__":
    unittest.main()
