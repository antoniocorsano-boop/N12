from __future__ import annotations

import unittest

from experiments.cew_b01.prototype_guided_occurrence_search import (
    shortlist_prototype_guided_occurrences,
)


PARTIAL = "RECT_PLUS_PARTIAL_TRANSVERSE_TRACES"
DOUBLE = "RECT_PLUS_DOUBLE_TRANSVERSE_BAND"


def record(
    marker_id: str,
    *,
    state: str = PARTIAL,
    topology: str = "THROUGH_CONTINUOUS",
    matched: int = 0,
    negative: int = 0,
    positive: int = 0,
    evidence: list[str] | None = None,
) -> dict:
    return {
        "marker_primitive_id": marker_id,
        "carrier_topology": {"topology_state": topology},
        "transverse_band": {
            "graphical_state": state,
            "matched_cross_side_pair_count": matched,
            "negative_side_count": negative,
            "positive_side_count": positive,
            "evidence_sources": list(evidence or []),
        },
    }


class PrototypeGuidedOccurrenceSearchTests(unittest.TestCase):
    def test_shortlists_only_through_continuous_partial_candidates(self):
        records = [
            record("A", matched=1, negative=1, positive=4, evidence=["G1_LINE_TRACKS", "RASTER_LOCAL_PROFILE"]),
            record("D", state=DOUBLE, matched=2, negative=2, positive=2, evidence=["G1_LINE_TRACKS", "RASTER_LOCAL_PROFILE"]),
            record("J", topology="JUNCTION_COMPLEX", matched=1, negative=1, positive=4, evidence=["G1_LINE_TRACKS", "RASTER_LOCAL_PROFILE"]),
        ]
        result = shortlist_prototype_guided_occurrences(records, excluded_ids=set())
        self.assertEqual([item["marker_primitive_id"] for item in result], ["A"])

    def test_excludes_known_negative_control_by_primitive_id(self):
        records = [record("NEG", matched=1, negative=1, positive=4, evidence=["G1_LINE_TRACKS", "RASTER_LOCAL_PROFILE"])]
        result = shortlist_prototype_guided_occurrences(records, excluded_ids={"NEG"})
        self.assertEqual(result, [])

    def test_assigns_review_priority_a_b_c_without_t1_t2_classification(self):
        records = [
            record("A", matched=1, negative=1, positive=4, evidence=["G1_LINE_TRACKS", "RASTER_LOCAL_PROFILE"]),
            record("B", matched=0, negative=3, positive=0, evidence=["G1_LINE_TRACKS", "RASTER_LOCAL_PROFILE"]),
            record("C", matched=0, negative=4, positive=0, evidence=["RASTER_LOCAL_PROFILE"]),
        ]
        result = shortlist_prototype_guided_occurrences(records, excluded_ids=set())
        self.assertEqual([item["review_priority"] for item in result], ["A", "B", "C"])
        for item in result:
            self.assertEqual(item["prototype_match_state"], "PROTOTYPE_MATCH_PENDING_HUMAN_REVIEW")
            self.assertIsNone(item["proposed_graphical_match"])
            self.assertFalse(item["semantic_classification_authorized"])
            self.assertFalse(item["structural_identity_authorized"])
            self.assertFalse(item["canonical_write_authorized"])
            self.assertFalse(item["g2c_promotion_authorized"])
            self.assertFalse(item["g3_authorized"])
            self.assertFalse(item["merge_authorized"])

    def test_drops_partial_record_that_does_not_meet_a_b_or_c_review_evidence(self):
        records = [record("WEAK", matched=0, negative=1, positive=0, evidence=["RASTER_LOCAL_PROFILE"])]
        self.assertEqual(shortlist_prototype_guided_occurrences(records, excluded_ids=set()), [])

    def test_reversed_input_is_deterministic(self):
        records = [
            record("A2", matched=1, negative=1, positive=4, evidence=["G1_LINE_TRACKS", "RASTER_LOCAL_PROFILE"]),
            record("A1", matched=1, negative=4, positive=1, evidence=["G1_LINE_TRACKS", "RASTER_LOCAL_PROFILE"]),
            record("B1", matched=0, negative=3, positive=0, evidence=["G1_LINE_TRACKS", "RASTER_LOCAL_PROFILE"]),
        ]
        forward = shortlist_prototype_guided_occurrences(records, excluded_ids=set())
        reverse = shortlist_prototype_guided_occurrences(list(reversed(records)), excluded_ids=set())
        self.assertEqual(forward, reverse)
        self.assertEqual([item["marker_primitive_id"] for item in forward], ["A1", "A2", "B1"])


if __name__ == "__main__":
    unittest.main()
