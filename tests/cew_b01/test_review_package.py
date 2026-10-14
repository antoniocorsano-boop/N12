from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from cew_b01.evidence_schema import AxisAlignedEvidenceRegion, EvidenceRegionCandidate
from cew_b01.records import CoordinateFrame, SourceIdentity
from cew_b01.review_package import render_review_package


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


class ReviewPackageTests(unittest.TestCase):
    def test_review_package_contains_only_visual_index_not_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raster = np.full((800, 800, 3), 255, dtype=np.uint8)
            raster_path = root / "raster.png"
            self.assertTrue(cv2.imwrite(str(raster_path), raster))
            candidates = (evidence_at(100.0, 120.0), evidence_at(500.0, 520.0))

            result = render_review_package(raster_path, candidates, root / "review")

            overview = Path(result["overview_path"])
            self.assertTrue(overview.is_file())
            self.assertGreater(len(result["contact_sheet_paths"]), 0)
            self.assertTrue(all(Path(path).is_file() for path in result["contact_sheet_paths"]))
            manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["candidate_count"], 2)
            self.assertEqual([item["review_index"] for item in manifest["candidates"]], [1, 2])
            self.assertEqual(
                {item["candidate_id"] for item in manifest["candidates"]},
                {candidate.candidate_id for candidate in candidates},
            )
            serialized = json.dumps(manifest).lower()
            for forbidden in ('"disposition"', '"decision"', '"accepted"', '"rejected"'):
                self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
