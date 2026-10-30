from __future__ import annotations

import copy
import unittest

from experiments.cew_b01.hosted_marker_graphical_repair import carrier_topology_evidence


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
    }


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


if __name__ == "__main__":
    unittest.main()
