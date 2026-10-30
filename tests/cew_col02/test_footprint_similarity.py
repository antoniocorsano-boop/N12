from __future__ import annotations

import unittest

from experiments.cew_col02.footprint_similarity import rank_similar_footprints


class FootprintSimilarityTests(unittest.TestCase):
    @staticmethod
    def proposal(
        candidate_id: str,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        rectangularity: float = 0.9,
        detector: str = "LONG_AXIS_SUPPRESSED",
        axis_evidence_present: bool = False,
    ) -> dict:
        return {
            "candidate_id": candidate_id,
            "bbox": {"x": x, "y": y, "width": width, "height": height},
            "rectangularity": rectangularity,
            "detector": detector,
            "axis_evidence_present": axis_evidence_present,
        }

    def test_exact_scale_ratio_envelope_candidate_scores_high(self) -> None:
        prototype = {"x": 0.0, "y": 0.0, "width": 0.03, "height": 0.11}
        rows = [self.proposal("P1", 0.3, 0.3, 0.03, 0.11)]
        ranked = rank_similar_footprints(prototype, rows)
        self.assertEqual(len(ranked), 1)
        self.assertGreaterEqual(ranked[0]["score"], 0.98)
        self.assertAlmostEqual(ranked[0]["size_similarity"], 1.0)
        self.assertAlmostEqual(ranked[0]["ratio_similarity"], 1.0)
        self.assertIsNone(ranked[0]["support_identity"])
        self.assertFalse(ranked[0]["structural_identity_authorized"])

    def test_candidate_overlapping_taught_prototype_is_excluded(self) -> None:
        prototype = {"x": 0.10, "y": 0.10, "width": 0.04, "height": 0.04}
        rows = [self.proposal("SELF", 0.101, 0.101, 0.04, 0.04)]
        self.assertEqual(rank_similar_footprints(prototype, rows), [])

    def test_size_similarity_below_historical_threshold_is_filtered(self) -> None:
        prototype = {"x": 0.0, "y": 0.0, "width": 0.04, "height": 0.04}
        rows = [self.proposal("SMALL", 0.5, 0.5, 0.008, 0.008)]
        self.assertEqual(rank_similar_footprints(prototype, rows), [])

    def test_ratio_similarity_below_historical_threshold_is_filtered(self) -> None:
        prototype = {"x": 0.0, "y": 0.0, "width": 0.04, "height": 0.04}
        rows = [self.proposal("WRONG-RATIO", 0.5, 0.5, 0.12, 0.01)]
        self.assertEqual(rank_similar_footprints(prototype, rows), [])

    def test_nms_collapses_overlapping_occurrence_proposals(self) -> None:
        prototype = {"x": 0.0, "y": 0.0, "width": 0.04, "height": 0.04}
        rows = [
            self.proposal("A", 0.30, 0.30, 0.04, 0.04, rectangularity=0.95),
            self.proposal("B", 0.305, 0.305, 0.04, 0.04, rectangularity=0.90),
        ]
        ranked = rank_similar_footprints(prototype, rows)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["occurrence_candidate_id"], "A")

    def test_elongated_candidate_without_axes_remains_eligible(self) -> None:
        prototype = {"x": 0.0, "y": 0.0, "width": 0.03, "height": 0.11}
        rows = [
            self.proposal(
                "LONG-NO-AXES",
                0.50,
                0.40,
                0.03,
                0.11,
                axis_evidence_present=False,
            )
        ]
        ranked = rank_similar_footprints(prototype, rows)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["occurrence_candidate_id"], "LONG-NO-AXES")
        self.assertFalse(ranked[0]["axis_evidence_present"])
        self.assertEqual(ranked[0]["review_state"], "SIMILARITY_PROPOSAL")

    def test_raw_contour_gets_lower_envelope_preference_than_axis_suppressed(self) -> None:
        prototype = {"x": 0.0, "y": 0.0, "width": 0.04, "height": 0.04}
        rows = [
            self.proposal("ENV", 0.30, 0.30, 0.04, 0.04, detector="LONG_AXIS_SUPPRESSED"),
            self.proposal("RAW", 0.60, 0.60, 0.04, 0.04, detector="RAW_CONTOUR"),
        ]
        ranked = rank_similar_footprints(prototype, rows)
        by_id = {item["occurrence_candidate_id"]: item for item in ranked}
        self.assertGreater(by_id["ENV"]["envelope_preference"], by_id["RAW"]["envelope_preference"])
        self.assertGreater(by_id["ENV"]["score"], by_id["RAW"]["score"])


if __name__ == "__main__":
    unittest.main()
