from __future__ import annotations

import unittest

from cew_b01.evidence_schema import AxisAlignedEvidenceRegion, EvidenceRegionCandidate
from cew_b01.object_mapping import (
    ReviewDecision,
    ReviewDisposition,
    ReviewValidationError,
    freeze_pre_comparator_bundle,
    map_reviewed_evidence,
)
from cew_b01.records import CoordinateFrame, SourceIdentity


SOURCE = SourceIdentity(
    repository="antoniocorsano-boop/N12",
    commit="78c20a52db4f391ce0d13b9705b9f04737e218c9",
    path="archive/documentazione_originaria/tavola 5.pdf",
    git_blob_sha="ec32cd621877e9037cb26ebc083164140a8e3e68",
    sha256="2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    page_index=0,
)


def evidence_at(x: float, y: float) -> EvidenceRegionCandidate:
    return EvidenceRegionCandidate.create(
        source=SOURCE,
        geometry=AxisAlignedEvidenceRegion(
            frame=CoordinateFrame.RASTER_PIXEL,
            x=x,
            y=y,
            width=40.0,
            height=50.0,
        ),
        method="OPENCV_AXIS_ALIGNED_QUADRILATERAL_V1",
        tool_id="opencv-python-headless",
        tool_version="5.0.0.93",
        confidence=0.91,
    )


class ObjectMappingTests(unittest.TestCase):
    def test_review_decision_rejects_ad_hoc_coordinates(self) -> None:
        evidence = evidence_at(10.0, 20.0)
        with self.assertRaises(ReviewValidationError):
            ReviewDecision.from_mapping(
                {
                    "candidate_id": evidence.candidate_id,
                    "disposition": "ACCEPT",
                    "semantic_label": "COLUMN",
                    "support_identifier": "G4-01",
                    "section_family": "40X40",
                    "x": 123.0,
                }
            )

    def test_ambiguous_and_rejected_decisions_are_not_promoted(self) -> None:
        first = evidence_at(10.0, 20.0)
        second = evidence_at(100.0, 120.0)
        decisions = (
            ReviewDecision(
                candidate_id=first.candidate_id,
                disposition=ReviewDisposition.AMBIGUOUS,
                note="insufficient visual evidence",
            ),
            ReviewDecision(
                candidate_id=second.candidate_id,
                disposition=ReviewDisposition.REJECT,
                note="not a structural support",
            ),
        )
        mapped = map_reviewed_evidence((first, second), decisions)
        self.assertEqual(mapped, ())

    def test_accepted_decision_maps_stably_without_copying_coordinates(self) -> None:
        evidence = evidence_at(10.0, 20.0)
        decision = ReviewDecision(
            candidate_id=evidence.candidate_id,
            disposition=ReviewDisposition.ACCEPT,
            semantic_label="COLUMN",
            support_identifier="G4-01",
            section_family="40X40",
        )
        first = map_reviewed_evidence((evidence,), (decision,))
        replay = map_reviewed_evidence((evidence,), (decision,))
        self.assertEqual(first, replay)
        self.assertEqual(len(first), 1)
        mapped = first[0].to_mapping()
        self.assertFalse(mapped["canonical"])
        self.assertFalse(mapped["structural_identity_authorized"])
        self.assertEqual(mapped["evidence_candidate_id"], evidence.candidate_id)
        self.assertEqual(mapped["evidence_geometry_digest"], evidence.geometry_digest)
        serialized = str(mapped).lower()
        for forbidden in ("'x':", "'y':", "'width':", "'height':", "coordinates"):
            self.assertNotIn(forbidden, serialized)

    def test_unknown_or_duplicate_review_target_fails_closed(self) -> None:
        evidence = evidence_at(10.0, 20.0)
        decision = ReviewDecision(
            candidate_id=evidence.candidate_id,
            disposition=ReviewDisposition.ACCEPT,
            semantic_label="COLUMN",
        )
        with self.assertRaises(ReviewValidationError):
            map_reviewed_evidence((), (decision,))
        with self.assertRaises(ReviewValidationError):
            map_reviewed_evidence((evidence,), (decision, decision))

    def test_pre_comparator_bundle_is_deterministic_and_preserves_review_states(self) -> None:
        first = evidence_at(10.0, 20.0)
        second = evidence_at(100.0, 120.0)
        decisions = (
            ReviewDecision(
                candidate_id=first.candidate_id,
                disposition=ReviewDisposition.ACCEPT,
                semantic_label="COLUMN",
                support_identifier="G4-01",
                section_family="40X40",
            ),
            ReviewDecision(
                candidate_id=second.candidate_id,
                disposition=ReviewDisposition.AMBIGUOUS,
                note="needs human follow-up",
            ),
        )
        first_bundle = freeze_pre_comparator_bundle((first, second), decisions)
        replay_bundle = freeze_pre_comparator_bundle((first, second), decisions)
        self.assertEqual(first_bundle, replay_bundle)
        self.assertEqual(first_bundle["review_summary"]["accepted"], 1)
        self.assertEqual(first_bundle["review_summary"]["ambiguous"], 1)
        self.assertEqual(first_bundle["review_summary"]["rejected"], 0)
        self.assertEqual(first_bundle["structural_candidate_count"], 1)
        self.assertRegex(first_bundle["bundle_sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
