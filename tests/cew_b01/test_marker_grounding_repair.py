from __future__ import annotations

import copy
import unittest

from experiments.cew_b01.marker_topology_repair import refine_marker_grounding


def blank(width: int = 160, height: int = 100) -> list[list[bool]]:
    return [[False for _ in range(width)] for _ in range(height)]


def draw_rect(binary: list[list[bool]], *, x: int, y: int, width: int, height: int) -> None:
    x1 = x + width
    y1 = y + height
    for px in range(x, x1 + 1):
        binary[y][px] = True
        binary[y1][px] = True
    for py in range(y, y1 + 1):
        binary[py][x] = True
        binary[py][x1] = True


def candidate(*, x: float, y: float, width: float, height: float) -> dict:
    return {
        "marker_primitive_id": "R",
        "marker_geometry": {"x": x, "y": y, "width": width, "height": height},
        "carrier_orientation": "HORIZONTAL",
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


class MarkerGroundingRepairTests(unittest.TestCase):
    def test_aligned_rectangle_stays_g1_exact(self):
        binary = blank()
        draw_rect(binary, x=40, y=30, width=50, height=20)
        result = refine_marker_grounding(candidate(x=40, y=30, width=50, height=20), binary)
        self.assertEqual(result["source_marker_geometry"], {"x": 40.0, "y": 30.0, "width": 50.0, "height": 20.0})
        self.assertEqual(result["review_marker_geometry"], result["source_marker_geometry"])
        self.assertEqual(result["marker_grounding"]["method"], "G1_EXACT")
        self.assertTrue(result["marker_grounding"]["qualified"])
        self.assertAlmostEqual(result["marker_grounding"]["center_shift_px"], 0.0)

    def test_shifted_source_box_refines_to_supported_raster_edges(self):
        binary = blank()
        draw_rect(binary, x=43, y=32, width=50, height=20)
        result = refine_marker_grounding(candidate(x=40, y=30, width=50, height=20), binary)
        self.assertEqual(result["review_marker_geometry"], {"x": 43.0, "y": 32.0, "width": 50.0, "height": 20.0})
        self.assertEqual(result["marker_grounding"]["method"], "RASTER_REFINED_LOCAL_RECT")
        self.assertTrue(result["marker_grounding"]["qualified"])
        self.assertGreater(result["marker_grounding"]["source_edge_residual"], result["marker_grounding"]["review_edge_residual"])
        self.assertGreater(result["marker_grounding"]["center_shift_px"], 0.0)

    def test_refinement_cannot_jump_to_adjacent_rectangle(self):
        binary = blank()
        draw_rect(binary, x=40, y=30, width=50, height=20)
        draw_rect(binary, x=105, y=30, width=40, height=20)
        result = refine_marker_grounding(candidate(x=40, y=30, width=50, height=20), binary)
        self.assertEqual(result["review_marker_geometry"], {"x": 40.0, "y": 30.0, "width": 50.0, "height": 20.0})
        self.assertLess(result["marker_grounding"]["search_radius_px"], 15.0)

    def test_source_geometry_is_preserved_byte_for_byte(self):
        original = candidate(x=40, y=30, width=50, height=20)
        before = copy.deepcopy(original)
        binary = blank()
        draw_rect(binary, x=43, y=32, width=50, height=20)
        result = refine_marker_grounding(original, binary)
        self.assertEqual(original, before)
        self.assertEqual(result["source_marker_geometry"], before["marker_geometry"])
        self.assertIsNone(result["semantic_meaning"])
        self.assertFalse(result["structural_identity_authorized"])
        self.assertFalse(result["canonical_write_authorized"])
        self.assertFalse(result["g3_authorized"])
        self.assertFalse(result["merge_authorized"])


if __name__ == "__main__":
    unittest.main()
