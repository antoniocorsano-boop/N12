import unittest

from experiments.cew_cal01.numeric_role import dimension_tick_relation


class Cal01DimensionGeometryBracketingTests(unittest.TestCase):
    def test_long_horizontal_dimension_line_uses_internal_perpendicular_ticks_bracketing_token(self):
        relation = dimension_tick_relation(
            [
                (20.0, 100.0, 280.0, 100.0),
                (80.0, 80.0, 80.0, 120.0),
                (220.0, 80.0, 220.0, 120.0),
            ],
            token_bbox_px=[130.0, 90.0, 170.0, 110.0],
            expected_orientation="HORIZONTAL",
        )
        self.assertTrue(relation["confirmed"])
        self.assertEqual(relation["tick_style"], "PERPENDICULAR")
        self.assertEqual(relation["endpoint_a_px"], [80.0, 100.0])
        self.assertEqual(relation["endpoint_b_px"], [220.0, 100.0])

    def test_perpendicular_ticks_on_same_side_of_token_do_not_bind(self):
        relation = dimension_tick_relation(
            [
                (20.0, 100.0, 280.0, 100.0),
                (40.0, 80.0, 40.0, 120.0),
                (80.0, 80.0, 80.0, 120.0),
            ],
            token_bbox_px=[130.0, 90.0, 170.0, 110.0],
            expected_orientation="HORIZONTAL",
        )
        self.assertFalse(relation["confirmed"])

    def test_long_vertical_dimension_line_uses_internal_perpendicular_ticks_bracketing_token(self):
        relation = dimension_tick_relation(
            [
                (100.0, 20.0, 100.0, 280.0),
                (80.0, 80.0, 120.0, 80.0),
                (80.0, 220.0, 120.0, 220.0),
            ],
            token_bbox_px=[90.0, 130.0, 110.0, 170.0],
            expected_orientation="VERTICAL",
        )
        self.assertTrue(relation["confirmed"])
        self.assertEqual(relation["tick_style"], "PERPENDICULAR")
        self.assertEqual(relation["endpoint_a_px"], [100.0, 80.0])
        self.assertEqual(relation["endpoint_b_px"], [100.0, 220.0])


if __name__ == "__main__":
    unittest.main()
