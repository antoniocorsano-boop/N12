from __future__ import annotations

import unittest

import cv2
import numpy as np

import experiments.cew_col02.axis_aware_whole_symbol as whole_symbol
from experiments.cew_col02.footprint_proposals import extract_footprint_proposals


def _bbox(x1: int, y1: int, x2: int, y2: int, size: int = 600) -> dict[str, float]:
    return {
        "x": x1 / size,
        "y": y1 / size,
        "width": (x2 - x1) / size,
        "height": (y2 - y1) / size,
    }


class AxisAwareWholeSymbolGeometryTests(unittest.TestCase):
    def _repair(self, image: np.ndarray, seed: dict[str, float]):
        fn = getattr(whole_symbol, "reconstruct_axis_split_whole_symbol", None)
        self.assertTrue(callable(fn), "axis-aware whole-symbol reconstruction is missing")
        return fn(image, seed)

    def test_reconstructs_whole_rectangle_from_axis_split_quadrant_seed(self) -> None:
        image = np.full((600, 600), 255, dtype=np.uint8)
        cv2.rectangle(image, (260, 240), (340, 360), 0, 3)
        cv2.line(image, (50, 300), (550, 300), 0, 3)
        cv2.line(image, (300, 50), (300, 550), 0, 3)
        seed = _bbox(302, 302, 342, 362)

        result = self._repair(image, seed)
        self.assertIsNotNone(result)
        assert result is not None
        repaired = result["bbox"]
        self.assertAlmostEqual(repaired["x"], 260 / 600, delta=0.02)
        self.assertAlmostEqual(repaired["y"], 240 / 600, delta=0.02)
        self.assertAlmostEqual(repaired["width"], 80 / 600, delta=0.03)
        self.assertAlmostEqual(repaired["height"], 120 / 600, delta=0.03)
        self.assertEqual(result["boundary_side_count"], 4)
        self.assertAlmostEqual(result["axis_cross"]["x"], 0.5, delta=0.02)
        self.assertAlmostEqual(result["axis_cross"]["y"], 0.5, delta=0.02)

    def test_thick_axes_are_bridged_without_shrinking_outer_symbol(self) -> None:
        image = np.full((600, 600), 255, dtype=np.uint8)
        cv2.rectangle(image, (250, 250), (350, 350), 0, 4)
        cv2.line(image, (40, 300), (560, 300), 0, 9)
        cv2.line(image, (300, 40), (300, 560), 0, 9)
        seed = _bbox(305, 305, 355, 355)

        result = self._repair(image, seed)
        self.assertIsNotNone(result)
        assert result is not None
        repaired = result["bbox"]
        self.assertLess(repaired["x"], 0.44)
        self.assertLess(repaired["y"], 0.44)
        self.assertGreater(repaired["x"] + repaired["width"], 0.56)
        self.assertGreater(repaired["y"] + repaired["height"], 0.56)
        self.assertGreaterEqual(result["axis_thickness_px"]["horizontal"], 5)
        self.assertGreaterEqual(result["axis_thickness_px"]["vertical"], 5)

    def test_beam_column_junction_seed_without_four_side_envelope_is_rejected(self) -> None:
        image = np.full((600, 600), 255, dtype=np.uint8)
        cv2.rectangle(image, (240, 240), (290, 360), 0, 3)
        cv2.line(image, (290, 280), (560, 280), 0, 3)
        cv2.line(image, (290, 320), (560, 320), 0, 3)
        cv2.line(image, (50, 300), (550, 300), 0, 3)
        cv2.line(image, (265, 50), (265, 550), 0, 3)
        seed = _bbox(292, 288, 330, 314)

        result = self._repair(image, seed)
        self.assertIsNone(result)

    def test_nested_equal_envelopes_fail_closed_as_ambiguous(self) -> None:
        image = np.full((600, 600), 255, dtype=np.uint8)
        cv2.rectangle(image, (245, 245), (355, 355), 0, 3)
        cv2.rectangle(image, (260, 260), (340, 340), 0, 3)
        cv2.line(image, (50, 300), (550, 300), 0, 3)
        cv2.line(image, (300, 50), (300, 550), 0, 3)
        seed = _bbox(302, 302, 342, 342)

        result = self._repair(image, seed)
        self.assertIsNone(result)

    def test_repair_helper_does_not_mutate_v1_proposal_replay(self) -> None:
        image = np.full((600, 600), 255, dtype=np.uint8)
        cv2.rectangle(image, (260, 240), (340, 360), 0, 3)
        cv2.line(image, (50, 300), (550, 300), 0, 3)
        cv2.line(image, (300, 50), (300, 550), 0, 3)
        seed = _bbox(302, 302, 342, 362)

        before = extract_footprint_proposals(image, max_candidates=200)
        self._repair(image, seed)
        after = extract_footprint_proposals(image, max_candidates=200)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
