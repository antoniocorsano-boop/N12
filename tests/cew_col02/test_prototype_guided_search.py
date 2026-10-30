from __future__ import annotations

import unittest

from experiments.cew_col02.prototype_guided_search import rank_from_human_review


class PrototypeGuidedSearchTests(unittest.TestCase):
    @staticmethod
    def row(candidate_id: str, x: float, y: float, w: float, h: float, *, rectangularity: float = 0.95) -> dict:
        return {
            "candidate_id": candidate_id,
            "bbox": {"x": x, "y": y, "width": w, "height": h},
            "rectangularity": rectangularity,
            "detector": "LONG_AXIS_SUPPRESSED",
            "axis_evidence_present": False,
        }

    @staticmethod
    def review() -> dict:
        return {
            "panel_decisions": [
                {"panel_id": "P01", "candidate_id": "SEED-A", "column_graphic_decision": "COLUMN_FOOTPRINT_CONFIRMED", "prototype_eligible": True},
                {"panel_id": "P02", "candidate_id": "SEED-B", "column_graphic_decision": "COLUMN_FOOTPRINT_CONFIRMED", "prototype_eligible": True},
                {"panel_id": "P03", "candidate_id": "NEG", "column_graphic_decision": "NOT_COLUMN", "prototype_eligible": False},
            ]
        }

    def test_uses_both_human_positive_seeds(self) -> None:
        rows = [
            self.row("SEED-A", 0.10, 0.10, 0.03, 0.09),
            self.row("SEED-B", 0.20, 0.10, 0.05, 0.05),
            self.row("MATCH-A", 0.50, 0.50, 0.03, 0.09),
            self.row("MATCH-B", 0.70, 0.50, 0.05, 0.05),
            self.row("NEG", 0.40, 0.40, 0.03, 0.09),
        ]
        result = rank_from_human_review(rows, self.review(), limit=20)
        by_id = {item["occurrence_candidate_id"]: item for item in result}
        self.assertIn("MATCH-A", by_id)
        self.assertIn("MATCH-B", by_id)
        self.assertEqual(by_id["MATCH-A"]["best_prototype_candidate_id"], "SEED-A")
        self.assertEqual(by_id["MATCH-B"]["best_prototype_candidate_id"], "SEED-B")

    def test_excludes_positive_seeds_and_reviewed_negatives_from_results(self) -> None:
        rows = [
            self.row("SEED-A", 0.10, 0.10, 0.03, 0.09),
            self.row("SEED-B", 0.20, 0.10, 0.05, 0.05),
            self.row("NEG", 0.40, 0.40, 0.03, 0.09),
            self.row("MATCH", 0.70, 0.70, 0.03, 0.09),
        ]
        ids = {item["occurrence_candidate_id"] for item in rank_from_human_review(rows, self.review())}
        self.assertNotIn("SEED-A", ids)
        self.assertNotIn("SEED-B", ids)
        self.assertNotIn("NEG", ids)
        self.assertIn("MATCH", ids)

    def test_same_candidate_retrieved_by_two_seeds_is_deduplicated_with_lineage(self) -> None:
        review = {
            "panel_decisions": [
                {"panel_id": "P01", "candidate_id": "SEED-A", "column_graphic_decision": "COLUMN_FOOTPRINT_CONFIRMED", "prototype_eligible": True},
                {"panel_id": "P02", "candidate_id": "SEED-B", "column_graphic_decision": "COLUMN_FOOTPRINT_CONFIRMED", "prototype_eligible": True},
            ]
        }
        rows = [
            self.row("SEED-A", 0.10, 0.10, 0.04, 0.04),
            self.row("SEED-B", 0.20, 0.10, 0.041, 0.039),
            self.row("MATCH", 0.70, 0.70, 0.04, 0.04),
        ]
        result = rank_from_human_review(rows, review)
        match = [item for item in result if item["occurrence_candidate_id"] == "MATCH"]
        self.assertEqual(len(match), 1)
        self.assertEqual(set(match[0]["matched_prototype_candidate_ids"]), {"SEED-A", "SEED-B"})
        self.assertFalse(match[0]["support_identity_authorized"])
        self.assertFalse(match[0]["canonical_write_authorized"])

    def test_missing_human_positive_seed_fails_closed(self) -> None:
        rows = [self.row("OTHER", 0.5, 0.5, 0.04, 0.04)]
        with self.assertRaises(ValueError):
            rank_from_human_review(rows, self.review())


if __name__ == "__main__":
    unittest.main()
