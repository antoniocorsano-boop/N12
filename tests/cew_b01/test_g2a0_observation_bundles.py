from __future__ import annotations

import unittest

from experiments.cew_b01.g2a0_observation_bundles import bundle_observations


def primitive(pid: str, family: str, *, x: float, y: float, w: float, h: float, orientation: str | None = None):
    signature = {}
    if orientation is not None:
        signature["orientation"] = orientation
    return {
        "primitive_id": pid,
        "source": {"sha256": "s" * 64},
        "page_index": 0,
        "frame": "RASTER_PIXEL",
        "geometry": {"x": x, "y": y, "width": w, "height": h},
        "family": family,
        "detector": "TEST",
        "feature_signature": signature,
    }


class ObservationBundleTests(unittest.TestCase):
    def test_co_spatial_derived_relations_fuse_and_preserve_members(self):
        items = [
            primitive("i", "INTERSECTION", x=100, y=100, w=8, h=8),
            primitive("c", "CROSS_MOTIF", x=97, y=97, w=14, h=14),
            primitive("t", "T_SHAPED_MOTIF", x=98, y=97, w=14, h=14),
        ]
        bundles, membership = bundle_observations(items)
        self.assertEqual(len(bundles), 1)
        self.assertEqual(set(bundles[0]["member_primitive_ids"]), {"i", "c", "t"})
        self.assertEqual(set(membership), {"i", "c", "t"})
        self.assertEqual(len(set(membership.values())), 1)

    def test_long_line_is_not_absorbed_into_compact_local_event(self):
        items = [
            primitive("i", "INTERSECTION", x=100, y=100, w=8, h=8),
            primitive("line", "LINE_SEGMENT", x=20, y=103, w=240, h=2, orientation="HORIZONTAL"),
        ]
        bundles, membership = bundle_observations(items)
        self.assertEqual(len(bundles), 2)
        self.assertNotEqual(membership["i"], membership["line"])

    def test_nearby_but_distinct_local_events_remain_separate(self):
        items = [
            primitive("a", "INTERSECTION", x=100, y=100, w=8, h=8),
            primitive("b", "CROSS_MOTIF", x=118, y=100, w=14, h=14),
        ]
        bundles, membership = bundle_observations(items)
        self.assertEqual(len(bundles), 2)
        self.assertNotEqual(membership["a"], membership["b"])

    def test_duplicate_parallel_pairs_can_coalesce_when_geometry_is_nearly_identical(self):
        items = [
            primitive("p1", "PARALLEL_LINE_PAIR", x=10, y=20, w=440, h=446, orientation="VERTICAL"),
            primitive("p2", "PARALLEL_LINE_PAIR", x=10, y=21, w=439, h=445, orientation="VERTICAL"),
            primitive("p3", "PARALLEL_LINE_PAIR", x=10, y=20, w=438, h=447, orientation="VERTICAL"),
        ]
        bundles, membership = bundle_observations(items)
        self.assertEqual(len(bundles), 1)
        self.assertEqual(set(bundles[0]["member_primitive_ids"]), {"p1", "p2", "p3"})
        self.assertEqual(len(set(membership.values())), 1)

    def test_reversed_input_is_deterministic_and_membership_is_complete(self):
        items = [
            primitive("i", "INTERSECTION", x=100, y=100, w=8, h=8),
            primitive("c", "CROSS_MOTIF", x=97, y=97, w=14, h=14),
            primitive("r", "RECTILINEAR_CLOSED_SHAPE", x=80, y=80, w=60, h=40),
        ]
        first = bundle_observations(items)
        second = bundle_observations(list(reversed(items)))
        self.assertEqual(first, second)
        self.assertEqual(set(first[1]), {"i", "c", "r"})
        self.assertEqual(sum(len(bundle["member_primitive_ids"]) for bundle in first[0]), 3)


if __name__ == "__main__":
    unittest.main()
