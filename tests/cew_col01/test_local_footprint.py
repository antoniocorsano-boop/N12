from __future__ import annotations

import unittest

from experiments.cew_col01.local_footprint import describe_local_footprint


def anchor(identifier: str = "18", *, x: int = 50, y: int = 50, width: int = 12, height: int = 10) -> dict:
    return {
        "normalized_id": identifier,
        "text": identifier,
        "confidence": 90.0,
        "bbox": {"x": x, "y": y, "width": width, "height": height},
    }


def primitive(family: str, x: float, y: float, width: float, height: float, **signature: object) -> dict:
    return {
        "primitive_id": f"{family}-{x}-{y}-{width}-{height}",
        "family": family,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "feature_signature": signature,
    }


class LocalFootprintTests(unittest.TestCase):
    def test_closed_footprint_with_crossing_axes_is_p1(self):
        result = describe_local_footprint(
            anchor(),
            [
                primitive("RECTILINEAR_CLOSED_SHAPE", 35, 35, 45, 40, rectangularity=0.9),
                primitive("LINE_SEGMENT", 20, 54, 90, 2, orientation="HORIZONTAL", length_px=90),
                primitive("LINE_SEGMENT", 55, 15, 2, 90, orientation="VERTICAL", length_px=90),
            ],
        )
        self.assertEqual(result["graphical_state"], "P1_NUMBER_FOOTPRINT_AXES")
        self.assertTrue(result["review_eligible"])
        self.assertTrue(result["axis_evidence_present"])

    def test_closed_footprint_without_axes_is_p2_and_review_eligible(self):
        result = describe_local_footprint(
            anchor(),
            [primitive("RECTILINEAR_CLOSED_SHAPE", 35, 35, 45, 40, rectangularity=0.9)],
        )
        self.assertEqual(result["graphical_state"], "P2_NUMBER_FOOTPRINT_NO_AXES")
        self.assertTrue(result["review_eligible"])
        self.assertFalse(result["axis_evidence_present"])

    def test_elongated_footprint_without_axes_remains_p2(self):
        result = describe_local_footprint(
            anchor(x=90, y=50),
            [primitive("RECTILINEAR_CLOSED_SHAPE", 30, 35, 150, 40, rectangularity=0.85)],
        )
        self.assertEqual(result["graphical_state"], "P2_NUMBER_FOOTPRINT_NO_AXES")
        self.assertTrue(result["review_eligible"])
        self.assertGreaterEqual(result["footprint"]["aspect_ratio"], 3.0)
        self.assertEqual(result["footprint"]["orientation"], "HORIZONTAL_ELONGATED")

    def test_local_orthogonal_fragments_without_closed_shape_are_p3(self):
        result = describe_local_footprint(
            anchor(),
            [
                primitive("LINE_SEGMENT", 35, 35, 45, 2, orientation="HORIZONTAL", length_px=45),
                primitive("LINE_SEGMENT", 35, 35, 2, 40, orientation="VERTICAL", length_px=40),
                primitive("LINE_SEGMENT", 35, 73, 45, 2, orientation="HORIZONTAL", length_px=45),
            ],
        )
        self.assertEqual(result["graphical_state"], "P3_NUMBER_PARTIAL_FOOTPRINT")
        self.assertTrue(result["review_eligible"])
        self.assertFalse(result["axis_evidence_present"])

    def test_isolated_number_is_not_promoted_to_column(self):
        result = describe_local_footprint(anchor(), [])
        self.assertEqual(result["graphical_state"], "NO_PLAUSIBLE_FOOTPRINT")
        self.assertFalse(result["review_eligible"])
        self.assertIsNone(result["footprint"])

    def test_authority_is_always_closed(self):
        result = describe_local_footprint(
            anchor(),
            [primitive("RECTILINEAR_CLOSED_SHAPE", 35, 35, 45, 40, rectangularity=0.9)],
        )
        for key in (
            "semantic_classification_authorized",
            "structural_identity_authorized",
            "canonical_geometry_authorized",
            "canonical_write_authorized",
            "section_assignment_authorized",
            "fixed_line_assignment_authorized",
            "g2c_promotion_authorized",
            "g3_authorized",
            "merge_authorized",
        ):
            self.assertFalse(result["authority"][key], key)


if __name__ == "__main__":
    unittest.main()
