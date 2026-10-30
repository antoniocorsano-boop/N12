from __future__ import annotations

import unittest

from experiments.cew_b01.beam_hosted_markers import detect_local_transverse_pair_from_binary


def blank(width: int = 400, height: int = 400) -> list[list[bool]]:
    return [[False for _ in range(width)] for _ in range(height)]


def vertical_stroke(binary: list[list[bool]], x0: int, x1: int, y0: int, y1: int) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            binary[y][x] = True


def horizontal_stroke(binary: list[list[bool]], y0: int, y1: int, x0: int, x1: int) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            binary[y][x] = True


class LocalRasterTransversePairTests(unittest.TestCase):
    def test_horizontal_carrier_detects_two_distinct_marker_anchored_vertical_strokes(self):
        binary = blank()
        vertical_stroke(binary, 175, 178, 70, 198)
        vertical_stroke(binary, 205, 208, 70, 198)
        result = detect_local_transverse_pair_from_binary(
            binary,
            marker_geometry={"x": 120, "y": 208, "width": 100, "height": 46},
            carrier_orientation="HORIZONTAL",
            carrier_track_centerlines=[200, 260],
        )
        self.assertTrue(result["pair_detected"])
        self.assertEqual(result["side"], "BEFORE_CROSS_AXIS")
        self.assertEqual(len(result["pair_strokes"]), 2)
        self.assertLess(result["pair_strokes"][0]["center"], result["pair_strokes"][1]["center"])

    def test_single_marker_anchored_stroke_does_not_form_pair(self):
        binary = blank()
        vertical_stroke(binary, 175, 178, 70, 198)
        result = detect_local_transverse_pair_from_binary(
            binary,
            marker_geometry={"x": 120, "y": 208, "width": 100, "height": 46},
            carrier_orientation="HORIZONTAL",
            carrier_track_centerlines=[200, 260],
        )
        self.assertFalse(result["pair_detected"])
        self.assertEqual(len(result["stroke_runs"]), 1)

    def test_remote_strokes_outside_marker_longitudinal_window_are_ignored(self):
        binary = blank()
        vertical_stroke(binary, 25, 28, 70, 198)
        vertical_stroke(binary, 330, 333, 70, 198)
        result = detect_local_transverse_pair_from_binary(
            binary,
            marker_geometry={"x": 120, "y": 208, "width": 100, "height": 46},
            carrier_orientation="HORIZONTAL",
            carrier_track_centerlines=[200, 260],
        )
        self.assertFalse(result["pair_detected"])
        self.assertEqual(result["stroke_runs"], [])

    def test_vertical_carrier_detects_two_horizontal_strokes_symmetrically(self):
        binary = blank()
        horizontal_stroke(binary, 175, 178, 70, 198)
        horizontal_stroke(binary, 205, 208, 70, 198)
        result = detect_local_transverse_pair_from_binary(
            binary,
            marker_geometry={"x": 208, "y": 120, "width": 46, "height": 100},
            carrier_orientation="VERTICAL",
            carrier_track_centerlines=[200, 260],
        )
        self.assertTrue(result["pair_detected"])
        self.assertEqual(result["side"], "BEFORE_CROSS_AXIS")
        self.assertEqual(len(result["pair_strokes"]), 2)


if __name__ == "__main__":
    unittest.main()
