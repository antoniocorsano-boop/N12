from __future__ import annotations

import unittest

from experiments.cew_col03b.hypotheses import (
    build_identity_hypothesis,
    evidence_independence_key,
)


class HypothesisTests(unittest.TestCase):
    def test_same_ocr_observation_counts_as_one_discriminant(self) -> None:
        first = {
            "evidence_id": "TXT-1",
            "channel": "nearby_text_evidence",
            "evidence_class": "PROXIMITY_ONLY",
            "observation_root_id": "OCR-REGION-1-TOKEN-4",
            "provenance_ref": "SRC-REGION-1",
        }
        derivative = {
            "evidence_id": "TXT-1-NORM",
            "channel": "intersecting_text_evidence",
            "evidence_class": "AMBIGUOUS_TEXT",
            "observation_root_id": "OCR-REGION-1-TOKEN-4",
            "provenance_ref": "SRC-REGION-1",
        }
        self.assertEqual(evidence_independence_key(first), evidence_independence_key(derivative))
        hypothesis = build_identity_hypothesis(
            occurrence_id="COL-OCC-0001",
            hypothesis_kind="SUPPORT_NUMBER_CANDIDATE",
            candidate_value="P12",
            supporting=[first, derivative],
            contradicting=[],
        )
        self.assertEqual(hypothesis["independent_channel_count"], 1)
        self.assertEqual(hypothesis["state"], "SINGLE_CHANNEL")
        self.assertFalse(hypothesis["promotion_authorized"])

    def test_callout_and_tav7_match_are_independent(self) -> None:
        callout = {
            "evidence_id": "CALL-1",
            "channel": "callout_evidence",
            "evidence_class": "DIRECT_GRAPHICAL_BINDING",
            "observation_root_id": "CALL-ROOT-1",
            "provenance_ref": "SRC-REGION-1",
        }
        tav7 = {
            "evidence_id": "XREF-1",
            "channel": "cross_document_evidence",
            "evidence_class": "INDEPENDENT_DOCUMENTARY_CORRESPONDENCE",
            "observation_root_id": "TAV7-N012",
            "provenance_ref": "TAV7-v25",
        }
        hypothesis = build_identity_hypothesis(
            occurrence_id="COL-OCC-0001",
            hypothesis_kind="SUPPORT_NUMBER_CANDIDATE",
            candidate_value="P12",
            supporting=[callout, tav7],
            contradicting=[],
        )
        self.assertEqual(hypothesis["independent_channel_count"], 2)
        self.assertEqual(hypothesis["state"], "MULTI_CHANNEL_SUPPORTED")
        self.assertFalse(hypothesis["promotion_authorized"])

    def test_contradiction_overrides_multi_channel_support(self) -> None:
        support = [
            {"evidence_id": "CALL-1", "channel": "callout_evidence", "observation_root_id": "A", "provenance_ref": "SRC-A"},
            {"evidence_id": "XREF-1", "channel": "cross_document_evidence", "observation_root_id": "B", "provenance_ref": "SRC-B"},
        ]
        contradiction = [
            {"evidence_id": "XREF-2", "channel": "cross_document_evidence", "observation_root_id": "C", "provenance_ref": "SRC-C"}
        ]
        hypothesis = build_identity_hypothesis(
            occurrence_id="COL-OCC-0001",
            hypothesis_kind="CROSS_DOCUMENT_COUNTERPART_CANDIDATE",
            candidate_value="N012",
            supporting=support,
            contradicting=contradiction,
        )
        self.assertEqual(hypothesis["state"], "CONTRADICTED")
        self.assertEqual(hypothesis["contradicting_evidence_ids"], ["XREF-2"])
        self.assertFalse(hypothesis["promotion_authorized"])

    def test_ambiguous_support_stays_ambiguous(self) -> None:
        hypothesis = build_identity_hypothesis(
            occurrence_id="COL-OCC-0001",
            hypothesis_kind="DOCUMENTARY_LABEL_CANDIDATE",
            candidate_value="12",
            supporting=[
                {
                    "evidence_id": "TXT-2",
                    "channel": "nearby_text_evidence",
                    "observation_root_id": "OCR-2",
                    "provenance_ref": "SRC-2",
                    "ambiguous": True,
                }
            ],
            contradicting=[],
        )
        self.assertEqual(hypothesis["state"], "AMBIGUOUS")
        self.assertFalse(hypothesis["promotion_authorized"])

    def test_rejects_unapproved_hypothesis_kind(self) -> None:
        with self.assertRaisesRegex(ValueError, "hypothesis kind"):
            build_identity_hypothesis(
                occurrence_id="COL-OCC-0001",
                hypothesis_kind="STRUCTURAL_IDENTITY",
                candidate_value="P12",
                supporting=[],
                contradicting=[],
            )


if __name__ == "__main__":
    unittest.main()
