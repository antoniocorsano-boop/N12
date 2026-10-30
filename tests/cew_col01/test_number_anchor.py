from __future__ import annotations

import unittest

from experiments.cew_col01.number_anchor import (
    normalize_support_identifier,
    parse_support_like_tsv,
)


def tsv(rows: list[tuple[str, str, int, int, int, int]]) -> str:
    header = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
    body = []
    for index, (text, conf, left, top, width, height) in enumerate(rows, start=1):
        body.append(
            f"5\t1\t1\t1\t1\t{index}\t{left}\t{top}\t{width}\t{height}\t{conf}\t{text}"
        )
    return "\n".join([header, *body, ""])


class NumberAnchorTests(unittest.TestCase):
    def test_normalizes_integer_and_apostrophe_support_ids(self):
        self.assertEqual(normalize_support_identifier("18"), "18")
        self.assertEqual(normalize_support_identifier("22'"), "22'")
        self.assertEqual(normalize_support_identifier("22’"), "22'")
        self.assertIsNone(normalize_support_identifier("3.50"))
        self.assertIsNone(normalize_support_identifier("P18"))
        self.assertIsNone(normalize_support_identifier("0"))
        self.assertIsNone(normalize_support_identifier("123"))

    def test_parses_support_like_tokens_with_geometry_and_confidence(self):
        result = parse_support_like_tsv(
            tsv(
                [
                    ("18", "91.4", 100, 200, 22, 18),
                    ("23", "88", 300, 400, 20, 17),
                    ("30", "76.5", 500, 600, 24, 19),
                    ("3.50", "99", 700, 800, 40, 18),
                    ("NOTE", "98", 900, 1000, 50, 20),
                ]
            )
        )
        self.assertEqual([item["normalized_id"] for item in result], ["18", "23", "30"])
        self.assertEqual(result[0]["bbox"], {"x": 100, "y": 200, "width": 22, "height": 18})
        self.assertEqual(result[0]["confidence"], 91.4)

    def test_keeps_duplicate_identifier_observations_explicit(self):
        result = parse_support_like_tsv(
            tsv(
                [
                    ("18", "90", 100, 200, 20, 16),
                    ("18", "89", 450, 700, 20, 16),
                ]
            )
        )
        self.assertEqual(len(result), 2)
        self.assertEqual([item["normalized_id"] for item in result], ["18", "18"])
        self.assertNotEqual(result[0]["bbox"], result[1]["bbox"])

    def test_rejects_low_confidence_tokens(self):
        result = parse_support_like_tsv(
            tsv(
                [
                    ("18", "24.9", 100, 200, 20, 16),
                    ("23", "25.0", 300, 400, 20, 16),
                ]
            ),
            min_confidence=25.0,
        )
        self.assertEqual([item["normalized_id"] for item in result], ["23"])

    def test_sorting_is_deterministic_by_position_then_identifier(self):
        source = tsv(
            [
                ("30", "80", 500, 600, 20, 16),
                ("18", "80", 300, 200, 20, 16),
                ("23", "80", 100, 200, 20, 16),
            ]
        )
        result = parse_support_like_tsv(source)
        self.assertEqual([item["normalized_id"] for item in result], ["23", "18", "30"])


if __name__ == "__main__":
    unittest.main()
