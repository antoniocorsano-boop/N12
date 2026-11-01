import unittest

from experiments.cew_cal01.numeric_role import (
    classify_numeric_graphic_role,
    dimension_tick_relation,
    expected_dimension_orientation,
)


class Cal01NumericRoleGateTests(unittest.TestCase):
    def test_text_orientation_constrains_dimension_orientation(self):
        self.assertEqual(expected_dimension_orientation(0), "HORIZONTAL")
        self.assertEqual(expected_dimension_orientation(180), "HORIZONTAL")
        self.assertEqual(expected_dimension_orientation(90), "VERTICAL")
        self.assertEqual(expected_dimension_orientation(270), "VERTICAL")

    def test_vertical_dimension_requires_two_short_terminal_ticks(self):
        segments = [
            (100, 20, 100, 180),
            (84, 20, 116, 20),
            (84, 180, 116, 180),
        ]
        relation = dimension_tick_relation(
            segments,
            token_bbox_px=[106, 80, 128, 120],
            expected_orientation="VERTICAL",
        )
        self.assertTrue(relation["confirmed"])
        self.assertEqual(relation["orientation"], "VERTICAL")
        self.assertEqual(relation["terminal_tick_count"], 2)
        self.assertEqual(relation["endpoint_a_px"], [100.0, 20.0])
        self.assertEqual(relation["endpoint_b_px"], [100.0, 180.0])

    def test_vertical_dimension_accepts_two_short_diagonal_slash_ticks(self):
        segments = [
            (100, 20, 100, 180),
            (88, 8, 112, 32),
            (88, 168, 112, 192),
        ]
        relation = dimension_tick_relation(
            segments,
            token_bbox_px=[106, 80, 128, 120],
            expected_orientation="VERTICAL",
        )
        self.assertTrue(relation["confirmed"])
        self.assertEqual(relation["tick_style"], "DIAGONAL_SLASH")
        self.assertEqual(relation["terminal_tick_count"], 2)
        self.assertEqual(relation["endpoint_a_px"], [100.0, 20.0])
        self.assertEqual(relation["endpoint_b_px"], [100.0, 180.0])

    def test_horizontal_dimension_accepts_two_short_diagonal_slash_ticks(self):
        segments = [
            (20, 100, 180, 100),
            (8, 88, 32, 112),
            (168, 88, 192, 112),
        ]
        relation = dimension_tick_relation(
            segments,
            token_bbox_px=[80, 106, 120, 128],
            expected_orientation="HORIZONTAL",
        )
        self.assertTrue(relation["confirmed"])
        self.assertEqual(relation["tick_style"], "DIAGONAL_SLASH")
        self.assertEqual(relation["endpoint_a_px"], [20.0, 100.0])
        self.assertEqual(relation["endpoint_b_px"], [180.0, 100.0])

    def test_long_structural_crossings_do_not_count_as_dimension_ticks(self):
        segments = [
            (100, 20, 100, 180),
            (0, 20, 300, 20),
            (0, 180, 300, 180),
        ]
        relation = dimension_tick_relation(
            segments,
            token_bbox_px=[106, 80, 128, 120],
            expected_orientation="VERTICAL",
        )
        self.assertFalse(relation["confirmed"])
        self.assertEqual(relation["reason"], "TWO_SHORT_TERMINAL_TICKS_NOT_OBSERVED")

    def test_long_diagonal_structural_lines_do_not_count_as_slash_ticks(self):
        segments = [
            (100, 20, 100, 180),
            (0, -80, 200, 120),
            (0, 80, 200, 280),
        ]
        relation = dimension_tick_relation(
            segments,
            token_bbox_px=[106, 80, 128, 120],
            expected_orientation="VERTICAL",
        )
        self.assertFalse(relation["confirmed"])

    def test_orientation_mismatch_fails_closed(self):
        segments = [
            (20, 100, 180, 100),
            (20, 84, 20, 116),
            (180, 84, 180, 116),
        ]
        relation = dimension_tick_relation(
            segments,
            token_bbox_px=[80, 106, 120, 128],
            expected_orientation="VERTICAL",
        )
        self.assertFalse(relation["confirmed"])

    def test_confirmed_dimension_role_requires_consensus_and_tick_grammar(self):
        segments = [
            (100, 20, 100, 180),
            (84, 20, 116, 20),
            (84, 180, 116, 180),
        ]
        result = classify_numeric_graphic_role(
            raw_text="120",
            consensus_text="120",
            consensus_count=3,
            ocr_rotation_degrees=270,
            token_bbox_px=[106, 80, 128, 120],
            line_segments=segments,
            nearby_closed_frame=False,
        )
        self.assertEqual(result["role"], "LINEAR_DIMENSION")
        self.assertEqual(result["documented_text"], "120")
        self.assertIsNone(result["metric_value_m"])
        self.assertFalse(result["primary_anchor_authorized"])

    def test_nearby_closed_frame_without_dimension_grammar_is_section_measure(self):
        result = classify_numeric_graphic_role(
            raw_text="40",
            consensus_text="40",
            consensus_count=3,
            ocr_rotation_degrees=0,
            token_bbox_px=[100, 80, 125, 100],
            line_segments=[(80, 60, 140, 60), (140, 60, 140, 120), (140, 120, 80, 120), (80, 120, 80, 60)],
            nearby_closed_frame=True,
        )
        self.assertEqual(result["role"], "SECTION_MEASURE")
        self.assertIsNone(result["metric_value_m"])
        self.assertFalse(result["primary_anchor_authorized"])

    def test_dimension_and_section_evidence_conflict_stays_unresolved(self):
        segments = [
            (100, 20, 100, 180),
            (84, 20, 116, 20),
            (84, 180, 116, 180),
        ]
        result = classify_numeric_graphic_role(
            raw_text="120",
            consensus_text="120",
            consensus_count=4,
            ocr_rotation_degrees=270,
            token_bbox_px=[106, 80, 128, 120],
            line_segments=segments,
            nearby_closed_frame=True,
        )
        self.assertEqual(result["role"], "UNRESOLVED")
        self.assertEqual(result["reason"], "DIMENSION_SECTION_ROLE_CONFLICT")
        self.assertFalse(result["primary_anchor_authorized"])

    def test_low_consensus_remains_unresolved(self):
        result = classify_numeric_graphic_role(
            raw_text="129",
            consensus_text=None,
            consensus_count=1,
            ocr_rotation_degrees=270,
            token_bbox_px=[100, 80, 125, 120],
            line_segments=[],
            nearby_closed_frame=False,
        )
        self.assertEqual(result["role"], "UNRESOLVED")
        self.assertFalse(result["primary_anchor_authorized"])


if __name__ == "__main__":
    unittest.main()
