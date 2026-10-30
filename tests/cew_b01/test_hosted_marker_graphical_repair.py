from __future__ import annotations

import copy
import unittest

from experiments.cew_b01.hosted_marker_graphical_repair import (
    carrier_topology_evidence,
    marker_alignment_evidence,
    refine_graphical_candidate,
)


def candidate(*, x: float, y: float, width: float, height: float, orientation: str) -> dict:
    return {
        "marker_primitive_id": "R",
        "marker_geometry": {"x": x, "y": y, "width": width, "height": height},
        "carrier_orientation": orientation,
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


def carrier(*, orientation: str, start: float, end: float, separation: float = 60.0) -> dict:
    return {
        "carrier_id": "C",
        "orientation": orientation,
        "overlap_start": start,
        "overlap_end": end,
        "overlap_length": end - start,
        "separation": separation,
        "track_centerlines": [170.0, 230.0],
    }


def blank(width: int = 500, height: int = 400) -> list[list[bool]]:
    return [[False for _ in range(width)] for _ in range(height)]


def draw_rectangle(
    binary: list[list[bool]],
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    thickness: int = 2,
) -> None:
    for offset in range(thickness):
        top = y + offset
        bottom = y + height - 1 - offset
        left = x + offset
        right = x + width - 1 - offset
        for xx in range(left, right + 1):
            binary[top][xx] = True
            binary[bottom][xx] = True
        for yy in range(top, bottom + 1):
            binary[yy][left] = True
            binary[yy][right] = True


def vertical_stroke(binary: list[list[bool]], x0: int, x1: int, y0: int, y1: int) -> None:
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            binary[yy][xx] = True


class CarrierTopologyEvidenceTests(unittest.TestCase):
    def test_marker_with_substantial_run_on_both_sides_is_through_linear(self):
        c = candidate(x=450, y=200, width=100, height=50, orientation="HORIZONTAL")
        h = carrier(orientation="HORIZONTAL", start=0, end=1000)

        result = carrier_topology_evidence(c, h)

        self.assertEqual(result["topology_state"], "THROUGH_LINEAR_CARRIER")
        self.assertEqual(result["before_run"], 450.0)
        self.assertEqual(result["after_run"], 450.0)
        self.assertGreaterEqual(result["minimum_side_run_ratio"], 4.0)

    def test_marker_near_carrier_end_is_terminated(self):
        c = candidate(x=450, y=200, width=100, height=50, orientation="HORIZONTAL")
        h = carrier(orientation="HORIZONTAL", start=430, end=900)

        result = carrier_topology_evidence(c, h)

        self.assertEqual(result["topology_state"], "END_OR_TERMINATED_CARRIER")
        self.assertLess(result["before_run_ratio"], 0.5)

    def test_marker_occupying_too_much_of_local_carrier_is_ambiguous(self):
        c = candidate(x=400, y=200, width=100, height=50, orientation="HORIZONTAL")
        h = carrier(orientation="HORIZONTAL", start=300, end=650)

        result = carrier_topology_evidence(c, h)

        self.assertEqual(result["topology_state"], "AMBIGUOUS_CARRIER_TOPOLOGY")
        self.assertLess(result["carrier_overlap_to_marker_long_span"], 4.0)
        self.assertGreaterEqual(result["before_run_ratio"], 1.0)
        self.assertGreaterEqual(result["after_run_ratio"], 1.0)

    def test_vertical_orientation_uses_marker_height_as_long_axis(self):
        c = candidate(x=200, y=450, width=50, height=100, orientation="VERTICAL")
        h = carrier(orientation="VERTICAL", start=0, end=1000)

        result = carrier_topology_evidence(c, h)

        self.assertEqual(result["topology_state"], "THROUGH_LINEAR_CARRIER")
        self.assertEqual(result["marker_long_span"], 100.0)

    def test_input_order_or_mutation_is_not_required_for_determinism(self):
        c = candidate(x=450, y=200, width=100, height=50, orientation="HORIZONTAL")
        h = carrier(orientation="HORIZONTAL", start=0, end=1000)
        c_before = copy.deepcopy(c)
        h_before = copy.deepcopy(h)

        first = carrier_topology_evidence(c, h)
        second = carrier_topology_evidence(copy.deepcopy(c), copy.deepcopy(h))

        self.assertEqual(first, second)
        self.assertEqual(c, c_before)
        self.assertEqual(h, h_before)
        self.assertNotIn("beam", str(first).lower())
        self.assertNotIn("pillar", str(first).lower())
        self.assertNotIn("column", str(first).lower())


class MarkerAlignmentEvidenceTests(unittest.TestCase):
    def test_aligned_rectangle_has_strong_support_on_all_four_sides(self):
        binary = blank()
        draw_rectangle(binary, x=150, y=180, width=100, height=40, thickness=2)

        result = marker_alignment_evidence(
            binary,
            {"x": 150, "y": 180, "width": 100, "height": 40},
        )

        self.assertEqual(result["alignment_state"], "ALIGNED")
        self.assertGreaterEqual(result["minimum_side_support"], 0.55)
        self.assertEqual(set(result["side_support"]), {"top", "bottom", "left", "right"})

    def test_shifted_claimed_rectangle_is_geometry_mismatch_and_not_snapped(self):
        binary = blank()
        draw_rectangle(binary, x=162, y=180, width=100, height=40, thickness=2)
        claimed = {"x": 150, "y": 180, "width": 100, "height": 40}
        claimed_before = copy.deepcopy(claimed)

        result = marker_alignment_evidence(binary, claimed)

        self.assertEqual(result["alignment_state"], "GEOMETRY_MISMATCH")
        self.assertLess(result["minimum_side_support"], 0.15)
        self.assertEqual(claimed, claimed_before)
        self.assertNotIn("refined_geometry", result)
        self.assertNotIn("snapped_geometry", result)


class GraphicalRepairRoleTests(unittest.TestCase):
    def _aligned_base(self) -> tuple[dict, dict, list[list[bool]]]:
        c = candidate(x=150, y=180, width=100, height=40, orientation="HORIZONTAL")
        h = carrier(orientation="HORIZONTAL", start=0, end=500)
        binary = blank()
        draw_rectangle(binary, x=150, y=180, width=100, height=40, thickness=2)
        return c, h, binary

    def test_aligned_through_candidate_without_transverse_section_is_eligible_alone(self):
        c, h, binary = self._aligned_base()
        result = refine_graphical_candidate(c, h, binary)
        self.assertEqual(result["graphical_repair_role"], "REVIEW_ELIGIBLE_ALONE")

    def test_bilateral_double_pair_on_aligned_through_carrier_is_eligible(self):
        c, h, binary = self._aligned_base()
        vertical_stroke(binary, 165, 168, 20, 168)
        vertical_stroke(binary, 195, 198, 20, 168)
        vertical_stroke(binary, 165, 168, 232, 390)
        vertical_stroke(binary, 195, 198, 232, 390)

        result = refine_graphical_candidate(c, h, binary)

        self.assertEqual(result["transverse_section_evidence"]["section_state"], "BILATERAL_DOUBLE_PAIR")
        self.assertEqual(result["graphical_repair_role"], "REVIEW_ELIGIBLE_BILATERAL_DOUBLE_PAIR")

    def test_unilateral_pair_is_partial_review(self):
        c, h, binary = self._aligned_base()
        vertical_stroke(binary, 165, 168, 20, 168)
        vertical_stroke(binary, 195, 198, 20, 168)

        result = refine_graphical_candidate(c, h, binary)

        self.assertEqual(result["transverse_section_evidence"]["section_state"], "UNILATERAL_PAIR_OR_PARTIAL")
        self.assertEqual(result["graphical_repair_role"], "PARTIAL_TRANSVERSE_REVIEW")

    def test_terminated_carrier_precedes_transverse_family_assignment(self):
        c, _h, binary = self._aligned_base()
        h = carrier(orientation="HORIZONTAL", start=140, end=500)

        result = refine_graphical_candidate(c, h, binary)

        self.assertEqual(result["carrier_topology_evidence"]["topology_state"], "END_OR_TERMINATED_CARRIER")
        self.assertEqual(result["graphical_repair_role"], "CARRIER_TOPOLOGY_REVIEW")

    def test_marker_mismatch_has_highest_review_precedence(self):
        c, h, _binary = self._aligned_base()
        binary = blank()
        draw_rectangle(binary, x=162, y=180, width=100, height=40, thickness=2)

        result = refine_graphical_candidate(c, h, binary)

        self.assertEqual(result["marker_alignment_evidence"]["alignment_state"], "GEOMETRY_MISMATCH")
        self.assertEqual(result["graphical_repair_role"], "MARKER_ALIGNMENT_REVIEW")
        self.assertEqual(result["marker_geometry"], c["marker_geometry"])
        self.assertIsNone(result["semantic_meaning"])
        self.assertFalse(result["structural_identity_authorized"])
        self.assertFalse(result["canonical_write_authorized"])
        self.assertFalse(result["g3_authorized"])
        self.assertFalse(result["merge_authorized"])


if __name__ == "__main__":
    unittest.main()
