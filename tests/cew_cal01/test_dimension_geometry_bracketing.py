import unittest

try:
    from experiments.cew_cal01.exact_source import _bracketing_reference_pair
except (ImportError, ModuleNotFoundError):
    _bracketing_reference_pair = None


class Cal01DimensionGeometryBracketingTests(unittest.TestCase):
    def test_long_horizontal_dimension_line_uses_internal_references_bracketing_token(self):
        self.assertTrue(callable(_bracketing_reference_pair))
        pair = _bracketing_reference_pair(
            main=(20.0, 100.0, 280.0, 100.0),
            perpendicular=[
                (80.0, 60.0, 80.0, 140.0),
                (220.0, 60.0, 220.0, 140.0),
            ],
            token_center=(150.0, 100.0),
            orientation="HORIZONTAL",
        )
        self.assertEqual(pair, ((80.0, 100.0), (220.0, 100.0)))

    def test_references_on_same_side_of_token_do_not_bind(self):
        self.assertTrue(callable(_bracketing_reference_pair))
        pair = _bracketing_reference_pair(
            main=(20.0, 100.0, 280.0, 100.0),
            perpendicular=[
                (40.0, 60.0, 40.0, 140.0),
                (80.0, 60.0, 80.0, 140.0),
            ],
            token_center=(150.0, 100.0),
            orientation="HORIZONTAL",
        )
        self.assertIsNone(pair)

    def test_long_vertical_dimension_line_uses_internal_references_bracketing_token(self):
        self.assertTrue(callable(_bracketing_reference_pair))
        pair = _bracketing_reference_pair(
            main=(100.0, 20.0, 100.0, 280.0),
            perpendicular=[
                (60.0, 80.0, 140.0, 80.0),
                (60.0, 220.0, 140.0, 220.0),
            ],
            token_center=(100.0, 150.0),
            orientation="VERTICAL",
        )
        self.assertEqual(pair, ((100.0, 80.0), (100.0, 220.0)))


if __name__ == "__main__":
    unittest.main()
