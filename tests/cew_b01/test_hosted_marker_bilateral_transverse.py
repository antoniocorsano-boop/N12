from __future__ import annotations

import unittest

from experiments.cew_b01.beam_hosted_marker_raster import detect_bilateral_transverse_section_from_binary


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


class BilateralTransverseSectionTests(unittest.TestCase):
    def test_horizontal_carrier_requires_two_strokes_before_and_two_after(self):
        binary = blank()
        # Pair above the horizontal carrier band.
        vertical_stroke(binary, 165, 168, 70, 198)
        vertical_stroke(binary, 195, 198, 70, 198)
        # Pair below the horizontal carrier band.
        vertical_stroke(binary, 165, 168, 262, 390)
        vertical_stroke(binary, 195, 198, 262, 390)

        result = detect_bilateral_transverse_section_from_binary(
            binary,
            marker_geometry={"x": 120, "y": 208, "width": 100, "height": 46},
            carrier_orientation="HORIZONTAL",
            carrier_track_centerlines=[200, 260],
        )

        self.assertTrue(result["bilateral_double_pair_detected"])
        self.assertEqual(result["pair_side_count"], 2)
        self.assertEqual(result["section_state"], "BILATERAL_DOUBLE_PAIR")
        self.assertEqual(len(result["before"]["pair_strokes"]), 2)
        self.assertEqual(len(result["after"]["pair_strokes"]), 2)

    def test_one_side_pair_is_partial_not_bilateral(self):
        binary = blank()
        vertical_stroke(binary, 165, 168, 70, 198)
        vertical_stroke(binary, 195, 198, 70, 198)

        result = detect_bilateral_transverse_section_from_binary(
            binary,
            marker_geometry={"x": 120, "y": 208, "width": 100, "height": 46},
            carrier_orientation="HORIZONTAL",
            carrier_track_centerlines=[200, 260],
        )

        self.assertFalse(result["bilateral_double_pair_detected"])
        self.assertEqual(result["pair_side_count"], 1)
        self.assertEqual(result["section_state"], "UNILATERAL_PAIR_OR_PARTIAL")
        self.assertEqual(len(result["before"]["pair_strokes"]), 2)
        self.assertEqual(result["after"]["pair_strokes"], [])

    def test_no_pair_is_no_transverse_section(self):
        result = detect_bilateral_transverse_section_from_binary(
            blank(),
            marker_geometry={"x": 120, "y": 208, "width": 100, "height": 46},
            carrier_orientation="HORIZONTAL",
            carrier_track_centerlines=[200, 260],
        )

        self.assertFalse(result["bilateral_double_pair_detected"])
        self.assertEqual(result["pair_side_count"], 0)
        self.assertEqual(result["section_state"], "NO_TRANSVERSE_SECTION")

    def test_vertical_carrier_is_symmetric(self):
        binary = blank()
        horizontal_stroke(binary, 165, 168, 70, 198)
        horizontal_stroke(binary, 195, 198, 70, 198)
        horizontal_stroke(binary, 165, 168, 262, 390)
        horizontal_stroke(binary, 195, 198, 262, 390)

        result = detect_bilateral_transverse_section_from_binary(
            binary,
            marker_geometry={"x": 208, "y": 120, "width": 46, "height": 100},
            carrier_orientation="VERTICAL",
            carrier_track_centerlines=[200, 260],
        )

        self.assertTrue(result["bilateral_double_pair_detected"])
        self.assertEqual(result["section_state"], "BILATERAL_DOUBLE_PAIR")


if __name__ == "__main__":
    unittest.main()
