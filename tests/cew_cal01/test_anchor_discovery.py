import unittest

from experiments.cew_cal01.anchor_discovery import (
    discover_dimension_geometry,
    normalize_dimension_text,
    proposal_from_ocr_token,
)
from experiments.cew_cal01.exact_source import _normalize_hough_lines
from experiments.cew_cal01.oriented_discovery import (
    _iter_tile_bounds,
    _map_oriented_bbox_to_page,
)


def blank_image(width=420, height=240):
    return [[255 for _ in range(width)] for _ in range(height)]


def draw_black_rect(image, left, top, right, bottom):
    for y in range(top, bottom):
        for x in range(left, right):
            image[y][x] = 0


class Cal01DimensionDiscoveryContractTests(unittest.TestCase):
    def test_numeric_text_is_only_a_proposal_without_geometry(self):
        token = {
            "text": "4.70",
            "confidence": 92.0,
            "bbox_px": [180, 80, 240, 110],
        }
        proposal = proposal_from_ocr_token(token, page_width=500, page_height=300)
        self.assertEqual(proposal["normalized_metric_text"], "4.70")
        self.assertEqual(proposal["metric_value_m"], 4.70)
        self.assertEqual(proposal["state"], "NUMERIC_TEXT_PROPOSAL")
        self.assertFalse(proposal["eligible_for_anchor"])
        self.assertEqual(proposal["source_role"], "OCR_DERIVATIVE_LOCALIZER_ONLY")

    def test_normalizer_rejects_plain_support_ids_and_accepts_metric_formats(self):
        self.assertEqual(normalize_dimension_text("4.70"), ("4.70", 4.70))
        self.assertEqual(normalize_dimension_text("4,05"), ("4.05", 4.05))
        self.assertEqual(normalize_dimension_text("470"), ("4.70", 4.70))
        self.assertIsNone(normalize_dimension_text("N031"))
        self.assertIsNone(normalize_dimension_text("40x40"))
        self.assertIsNone(normalize_dimension_text("30"))

    def test_horizontal_dimension_geometry_requires_two_extension_references(self):
        image = blank_image()
        draw_black_rect(image, 70, 120, 350, 123)
        draw_black_rect(image, 70, 65, 73, 175)
        draw_black_rect(image, 347, 65, 350, 175)
        geometry = discover_dimension_geometry(
            image,
            token_bbox_px=[185, 88, 235, 112],
        )
        self.assertTrue(geometry["geometrically_bound"])
        self.assertEqual(geometry["orientation"], "HORIZONTAL")
        self.assertLess(geometry["endpoint_a_px"][0], geometry["endpoint_b_px"][0])
        self.assertEqual(geometry["geometry_role"], "DIMENSION_LINE_WITH_TWO_REFERENCES")
        self.assertFalse(geometry["metric_anchor_promoted"])

    def test_single_reference_fails_closed(self):
        image = blank_image()
        draw_black_rect(image, 70, 120, 350, 123)
        draw_black_rect(image, 70, 65, 73, 175)
        geometry = discover_dimension_geometry(
            image,
            token_bbox_px=[185, 88, 235, 112],
        )
        self.assertFalse(geometry["geometrically_bound"])
        self.assertEqual(geometry["reason"], "TWO_REFERENCE_LINES_NOT_OBSERVED")

    def test_hough_line_normalizer_accepts_opencv_4_and_5_shapes(self):
        shape_n_4 = [[1, 2, 3, 4], [5, 6, 7, 8]]
        shape_n_1_4 = [[[1, 2, 3, 4]], [[5, 6, 7, 8]]]
        expected = [(1.0, 2.0, 3.0, 4.0), (5.0, 6.0, 7.0, 8.0)]
        self.assertEqual(_normalize_hough_lines(shape_n_4), expected)
        self.assertEqual(_normalize_hough_lines(shape_n_1_4), expected)

    def test_overlapping_tiles_cover_page_edges_deterministically(self):
        first = _iter_tile_bounds(1000, 900, tile_size=400, overlap=100)
        second = _iter_tile_bounds(1000, 900, tile_size=400, overlap=100)
        self.assertEqual(first, second)
        self.assertEqual(first[0], (0, 0, 400, 400))
        self.assertIn((600, 500, 1000, 900), first)
        self.assertEqual(len(first), len(set(first)))

    def test_oriented_bbox_roundtrips_to_original_page_frame(self):
        tile = (100, 200, 300, 500)  # local width 200, height 300
        expected = [120.0, 230.0, 160.0, 250.0]
        cases = {
            0: [20.0, 30.0, 60.0, 50.0],
            90: [250.0, 20.0, 270.0, 60.0],
            180: [140.0, 250.0, 180.0, 270.0],
            270: [30.0, 140.0, 50.0, 180.0],
        }
        for rotation, rotated_bbox in cases.items():
            with self.subTest(rotation=rotation):
                actual = _map_oriented_bbox_to_page(
                    rotated_bbox,
                    tile_bounds=tile,
                    rotation_degrees=rotation,
                    ocr_scale=1.0,
                )
                self.assertEqual(actual, expected)

    def test_oriented_bbox_mapping_undoes_ocr_upscale(self):
        actual = _map_oriented_bbox_to_page(
            [500.0, 40.0, 540.0, 120.0],
            tile_bounds=(100, 200, 300, 500),
            rotation_degrees=90,
            ocr_scale=2.0,
        )
        self.assertEqual(actual, [120.0, 230.0, 160.0, 250.0])


if __name__ == "__main__":
    unittest.main()
