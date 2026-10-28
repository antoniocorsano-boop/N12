from __future__ import annotations

import unittest

from cew_b01.evidence_schema import (
    AxisAlignedEvidenceRegion,
    EvidenceRegionCandidate,
    EvidenceValidationError,
)
from cew_b01.records import CoordinateFrame, SourceIdentity


class CoordinateFrameEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SourceIdentity(
            repository="antoniocorsano-boop/N12",
            commit="78c20a52db4f391ce0d13b9705b9f04737e218c9",
            path="archive/documentazione_originaria/tavola 5.pdf",
            git_blob_sha="ec32cd621877e9037cb26ebc083164140a8e3e68",
            sha256="2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
            page_index=0,
        )

    def test_region_requires_typed_source_coordinate_frame(self) -> None:
        region = AxisAlignedEvidenceRegion(
            frame=CoordinateFrame.RASTER_PIXEL,
            x=10.0,
            y=20.0,
            width=30.0,
            height=40.0,
        )
        self.assertEqual(region.frame, CoordinateFrame.RASTER_PIXEL)
        self.assertEqual(region.to_mapping()["frame"], "RASTER_PIXEL")

        with self.assertRaises(EvidenceValidationError):
            AxisAlignedEvidenceRegion(
                frame="BUILDING_M",  # type: ignore[arg-type]
                x=10.0,
                y=20.0,
                width=30.0,
                height=40.0,
            )

    def test_region_rejects_invalid_geometry(self) -> None:
        with self.assertRaises(EvidenceValidationError):
            AxisAlignedEvidenceRegion(
                frame=CoordinateFrame.RASTER_PIXEL,
                x=0.0,
                y=0.0,
                width=0.0,
                height=20.0,
            )

    def test_candidate_id_and_geometry_digest_are_deterministic(self) -> None:
        geometry = AxisAlignedEvidenceRegion(
            frame=CoordinateFrame.RASTER_PIXEL,
            x=50.0,
            y=60.0,
            width=40.0,
            height=55.0,
        )
        first = EvidenceRegionCandidate.create(
            source=self.source,
            geometry=geometry,
            method="OPENCV_AXIS_ALIGNED_QUADRILATERAL_V1",
            tool_id="opencv-python-headless",
            tool_version="5.0.0.93",
            confidence=0.91,
        )
        replay = EvidenceRegionCandidate.create(
            source=self.source,
            geometry=geometry,
            method="OPENCV_AXIS_ALIGNED_QUADRILATERAL_V1",
            tool_id="opencv-python-headless",
            tool_version="5.0.0.93",
            confidence=0.91,
        )
        self.assertEqual(first.candidate_id, replay.candidate_id)
        self.assertEqual(first.geometry_digest, replay.geometry_digest)
        self.assertEqual(first.source.sha256, self.source.sha256)
        self.assertEqual(first.page_index, 0)
        self.assertEqual(first.status, "UNREVIEWED_GEOMETRIC_REGION")

        changed = EvidenceRegionCandidate.create(
            source=self.source,
            geometry=AxisAlignedEvidenceRegion(
                frame=CoordinateFrame.RASTER_PIXEL,
                x=51.0,
                y=60.0,
                width=40.0,
                height=55.0,
            ),
            method="OPENCV_AXIS_ALIGNED_QUADRILATERAL_V1",
            tool_id="opencv-python-headless",
            tool_version="5.0.0.93",
            confidence=0.91,
        )
        self.assertNotEqual(first.candidate_id, changed.candidate_id)
        self.assertNotEqual(first.geometry_digest, changed.geometry_digest)


if __name__ == "__main__":
    unittest.main()
