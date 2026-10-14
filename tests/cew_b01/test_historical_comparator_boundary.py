from __future__ import annotations

import copy
import inspect
import unittest

import cew_b01.object_mapping as object_mapping
from cew_b01.evidence_schema import AxisAlignedEvidenceRegion, EvidenceRegionCandidate
from cew_b01.object_mapping import (
    ReviewDecision,
    ReviewDisposition,
    ReviewValidationError,
    compare_historical_summary,
    freeze_pre_comparator_bundle,
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


def accepted_fixture():
    evidence = EvidenceRegionCandidate.create(
        source=SOURCE,
        geometry=AxisAlignedEvidenceRegion(
            frame=CoordinateFrame.RASTER_PIXEL,
            x=10.0,
            y=20.0,
            width=40.0,
            height=50.0,
        ),
        method="OPENCV_AXIS_ALIGNED_QUADRILATERAL_V1",
        tool_id="opencv-python-headless",
        tool_version="5.0.0.93",
        confidence=0.91,
    )
    decision = ReviewDecision(
        candidate_id=evidence.candidate_id,
        disposition=ReviewDisposition.ACCEPT,
        semantic_label="COLUMN",
        support_identifier="G4-01",
        section_family="40X40",
    )
    return evidence, decision


class HistoricalComparatorBoundaryTests(unittest.TestCase):
    def test_comparator_requires_a_frozen_pre_comparator_digest(self) -> None:
        with self.assertRaises(ReviewValidationError):
            compare_historical_summary(
                {"structural_candidates": []},
                {"support_count": 34, "family_count": 5},
            )

    def test_comparator_cannot_mutate_frozen_candidate_bundle(self) -> None:
        evidence, decision = accepted_fixture()
        bundle = freeze_pre_comparator_bundle((evidence,), (decision,))
        before = copy.deepcopy(bundle)
        report = compare_historical_summary(
            bundle,
            {"support_count": 34, "family_count": 5},
        )
        self.assertEqual(bundle, before)
        self.assertEqual(report["pre_comparator_bundle_sha256"], bundle["bundle_sha256"])
        self.assertEqual(report["historical_reference"]["support_count"], 34)
        self.assertEqual(report["historical_reference"]["family_count"], 5)
        self.assertEqual(report["observed_source_derived"]["support_count"], 1)
        self.assertEqual(report["observed_source_derived"]["family_count"], 1)

    def test_mapping_module_has_no_repository_or_pr132_read_path(self) -> None:
        signature = inspect.signature(compare_historical_summary)
        self.assertEqual(list(signature.parameters), ["pre_comparator_bundle", "historical_summary"])
        source = inspect.getsource(object_mapping).lower()
        for forbidden in (
            "pull/132",
            "b7a25783564c353f0e7aa23775318a3a2d78ea9c",
            "requests.get",
            "urllib.request",
            "github.com/antoniocorsano-boop/n12/pull/132",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
