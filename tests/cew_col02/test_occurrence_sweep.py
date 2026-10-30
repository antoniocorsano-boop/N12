from __future__ import annotations

import unittest

from experiments.cew_col02.occurrence_sweep import visible_similarity_siblings


class OccurrenceSweepTests(unittest.TestCase):
    @staticmethod
    def row(candidate_id: str, x: float, y: float, w: float, h: float) -> dict:
        return {
            "occurrence_candidate_id": candidate_id,
            "bbox": {"x": x, "y": y, "width": w, "height": h},
            "score": 0.8,
        }

    def test_returns_non_target_similarity_candidates_visible_in_crop(self) -> None:
        crop = {"x": 0.30, "y": 0.30, "width": 0.40, "height": 0.40}
        rows = [
            self.row("TARGET", 0.45, 0.45, 0.05, 0.05),
            self.row("SIBLING", 0.58, 0.48, 0.04, 0.06),
            self.row("OUTSIDE", 0.85, 0.85, 0.04, 0.04),
        ]
        result = visible_similarity_siblings("TARGET", crop, rows)
        self.assertEqual([item["occurrence_candidate_id"] for item in result], ["SIBLING"])

    def test_requires_most_of_sibling_footprint_to_be_visible(self) -> None:
        crop = {"x": 0.30, "y": 0.30, "width": 0.40, "height": 0.40}
        rows = [
            self.row("TARGET", 0.45, 0.45, 0.05, 0.05),
            self.row("EDGE", 0.68, 0.45, 0.08, 0.08),
        ]
        result = visible_similarity_siblings("TARGET", crop, rows, min_visible_fraction=0.75)
        self.assertEqual(result, [])

    def test_orders_visible_siblings_by_score_then_id(self) -> None:
        crop = {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}
        rows = [
            {**self.row("B", 0.2, 0.2, 0.03, 0.03), "score": 0.7},
            {**self.row("A", 0.3, 0.3, 0.03, 0.03), "score": 0.9},
            {**self.row("C", 0.4, 0.4, 0.03, 0.03), "score": 0.9},
        ]
        result = visible_similarity_siblings("NONE", crop, rows)
        self.assertEqual([item["occurrence_candidate_id"] for item in result], ["A", "C", "B"])


if __name__ == "__main__":
    unittest.main()
