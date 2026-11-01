import unittest

from experiments.cew_cal01.anchor_discovery import (
    discover_dimension_geometry,
    normalize_dimension_text,
    proposal_from_ocr_token,
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
        # Main horizontal dimension line and two vertical extension/tick references.
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


if __name__ == "__main__":
    unittest.main()
