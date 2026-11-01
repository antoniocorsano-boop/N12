from __future__ import annotations

import unittest

try:
    from experiments.cew_col03f.exact_source import (
        bbox_to_pixels,
        crop_specs,
        map_crop_bbox_to_page,
        normalize_targeted_anchors,
    )
except (ImportError, ModuleNotFoundError):
    bbox_to_pixels = None
    crop_specs = None
    map_crop_bbox_to_page = None
    normalize_targeted_anchors = None


class ExactSourceGeometryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(bbox_to_pixels, "COL-03F exact-source geometry module missing")
        self.assertIsNotNone(crop_specs, "COL-03F crop specification helper missing")
        self.assertIsNotNone(map_crop_bbox_to_page, "COL-03F coordinate mapper missing")

    def test_bbox_to_pixels_is_deterministic_and_clipped_to_page(self):
        self.assertEqual(
            bbox_to_pixels({"x": 0.10, "y": 0.20, "width": 0.30, "height": 0.40}, 100, 200),
            (10, 40, 40, 120),
        )
        self.assertEqual(
            bbox_to_pixels({"x": 0.98, "y": 0.97, "width": 0.02, "height": 0.03}, 100, 200),
            (98, 194, 100, 200),
        )

    def test_crop_specs_are_nested_and_never_leave_page(self):
        specs = crop_specs(
            {"x": 0.001, "y": 0.002, "width": 0.02, "height": 0.03},
            1000,
            2000,
        )
        self.assertEqual(set(specs), {"FOOTPRINT", "LOCAL", "CONTEXT"})
        footprint = specs["FOOTPRINT"]
        local = specs["LOCAL"]
        context = specs["CONTEXT"]
        for left, top, right, bottom in specs.values():
            self.assertGreaterEqual(left, 0)
            self.assertGreaterEqual(top, 0)
            self.assertLessEqual(right, 1000)
            self.assertLessEqual(bottom, 2000)
            self.assertLess(left, right)
            self.assertLess(top, bottom)
        self.assertLessEqual(local[0], footprint[0])
        self.assertLessEqual(local[1], footprint[1])
        self.assertGreaterEqual(local[2], footprint[2])
        self.assertGreaterEqual(local[3], footprint[3])
        self.assertLessEqual(context[0], local[0])
        self.assertLessEqual(context[1], local[1])
        self.assertGreaterEqual(context[2], local[2])
        self.assertGreaterEqual(context[3], local[3])

    def test_scaled_crop_token_bbox_maps_back_to_exact_page_coordinates(self):
        mapped = map_crop_bbox_to_page(
            token_bbox={"x": 20, "y": 40, "width": 20, "height": 10},
            crop_bounds=(10, 20, 110, 120),
            scale=2.0,
            page_width=1000,
            page_height=500,
        )
        self.assertAlmostEqual(mapped["x"], 0.020)
        self.assertAlmostEqual(mapped["y"], 0.080)
        self.assertAlmostEqual(mapped["width"], 0.010)
        self.assertAlmostEqual(mapped["height"], 0.010)
        self.assertGreaterEqual(mapped["x"], 0.0)
        self.assertGreaterEqual(mapped["y"], 0.0)
        self.assertLessEqual(mapped["x"] + mapped["width"], 1.0)
        self.assertLessEqual(mapped["y"] + mapped["height"], 1.0)


class TargetedObservationNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(normalize_targeted_anchors, "COL-03F targeted observation normalizer missing")

    def test_anchor_is_mapped_and_classified_without_mutating_occurrence_bbox(self):
        occurrence_bbox = {"x": 0.10, "y": 0.20, "width": 0.10, "height": 0.10}
        original = dict(occurrence_bbox)
        observations = normalize_targeted_anchors(
            anchors=[
                {
                    "text": "12",
                    "normalized_id": "12",
                    "confidence": 93.0,
                    "bbox": {"x": 40, "y": 40, "width": 20, "height": 20},
                }
            ],
            occurrence_id="COL-OCC-0002",
            region_class="FOOTPRINT",
            ocr_configuration="PSM6",
            crop_bounds=(50, 150, 250, 350),
            scale=2.0,
            page_width=500,
            page_height=500,
            occurrence_bbox=occurrence_bbox,
            local_region={"x": 0.05, "y": 0.15, "width": 0.20, "height": 0.20},
            provenance_prefix="CEW-N12-XFORM-TAV05S-P001:COL03F",
        )
        self.assertEqual(occurrence_bbox, original)
        self.assertEqual(len(observations), 1)
        row = observations[0]
        self.assertEqual(row["normalized_text"], "12")
        self.assertEqual(row["ocr_configuration"], "PSM6")
        self.assertEqual(row["region_class"], "FOOTPRINT")
        self.assertEqual(row["relation"], "INTERNAL")
        self.assertTrue(row["exact_source_reconstructible"])
        self.assertEqual(row["page_bbox"], {"x": 0.14, "y": 0.34, "width": 0.02, "height": 0.02})
        self.assertIn("COL-OCC-0002:FOOTPRINT:PSM6:001", row["provenance_ref"])

    def test_normalization_order_is_stable_even_when_anchor_input_is_reversed(self):
        anchors = [
            {"text": "30", "normalized_id": "30", "confidence": 80.0, "bbox": {"x": 30, "y": 10, "width": 10, "height": 10}},
            {"text": "4", "normalized_id": "4", "confidence": 90.0, "bbox": {"x": 10, "y": 10, "width": 10, "height": 10}},
        ]
        kwargs = dict(
            occurrence_id="COL-OCC-0001",
            region_class="LOCAL",
            ocr_configuration="PSM11",
            crop_bounds=(0, 0, 100, 100),
            scale=1.0,
            page_width=100,
            page_height=100,
            occurrence_bbox={"x": 0.0, "y": 0.0, "width": 0.5, "height": 0.5},
            local_region={"x": 0.0, "y": 0.0, "width": 0.8, "height": 0.8},
            provenance_prefix="P",
        )
        first = normalize_targeted_anchors(anchors=anchors, **kwargs)
        second = normalize_targeted_anchors(anchors=list(reversed(anchors)), **kwargs)
        self.assertEqual(first, second)
        self.assertEqual([row["normalized_text"] for row in first], ["4", "30"])


if __name__ == "__main__":
    unittest.main()
