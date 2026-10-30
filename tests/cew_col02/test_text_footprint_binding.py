from __future__ import annotations

import unittest

from experiments.cew_col02.text_footprint_binding import classify_text_relation


class TextFootprintRelationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.footprint = {"x": 0.0, "y": 0.0, "width": 10.0, "height": 10.0}

    def test_text_well_inside_footprint_is_inside(self) -> None:
        result = classify_text_relation(
            self.footprint,
            {"x": 3.0, "y": 4.0, "width": 2.0, "height": 1.0},
        )
        self.assertEqual(result["relation"], "INSIDE_FOOTPRINT")
        self.assertTrue(result["center_in_footprint"])
        self.assertAlmostEqual(result["text_contained_fraction"], 1.0)
        self.assertAlmostEqual(result["edge_distance"], 0.0)

    def test_partial_overlap_is_intersects(self) -> None:
        result = classify_text_relation(
            self.footprint,
            {"x": 9.0, "y": 4.0, "width": 3.0, "height": 2.0},
        )
        self.assertEqual(result["relation"], "INTERSECTS_FOOTPRINT")
        self.assertGreater(result["intersection_area"], 0.0)
        self.assertLess(result["text_contained_fraction"], 0.80)

    def test_near_external_dimension_remains_near_outside(self) -> None:
        result = classify_text_relation(
            self.footprint,
            {"x": 10.5, "y": 4.0, "width": 2.0, "height": 2.0},
            near_radius=0.35,
        )
        self.assertEqual(result["relation"], "NEAR_OUTSIDE_FOOTPRINT")
        self.assertFalse(result["center_in_footprint"])
        self.assertAlmostEqual(result["intersection_area"], 0.0)
        self.assertGreater(result["edge_distance"], 0.0)

    def test_far_external_text_is_unbound(self) -> None:
        result = classify_text_relation(
            self.footprint,
            {"x": 20.0, "y": 4.0, "width": 2.0, "height": 2.0},
            near_radius=0.35,
        )
        self.assertEqual(result["relation"], "UNRELATED_OR_UNBOUND")
        self.assertGreater(result["normalized_center_distance"], 1.0)

    def test_center_inside_but_low_containment_is_not_inside(self) -> None:
        result = classify_text_relation(
            self.footprint,
            {"x": -5.0, "y": 4.0, "width": 12.0, "height": 2.0},
        )
        self.assertTrue(result["center_in_footprint"])
        self.assertLess(result["text_contained_fraction"], 0.80)
        self.assertEqual(result["relation"], "INTERSECTS_FOOTPRINT")

    def test_zero_area_bbox_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            classify_text_relation(
                self.footprint,
                {"x": 1.0, "y": 1.0, "width": 0.0, "height": 1.0},
            )


if __name__ == "__main__":
    unittest.main()
