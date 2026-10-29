from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from cew_b01.evidence_extraction import (
    ExtractionConfig,
    _deduplicate_rectangles,
    extract_g4_evidence_candidates,
)
from cew_b01.evidence_schema import Task3RasterBinding


SOURCE = {
    "repository": "antoniocorsano-boop/N12",
    "commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
    "path": "archive/documentazione_originaria/tavola 5.pdf",
    "git_blob_sha": "ec32cd621877e9037cb26ebc083164140a8e3e68",
    "sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    "page_index": 0,
}


def _binding(path: Path, *, width: int, height: int) -> Task3RasterBinding:
    png_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return Task3RasterBinding.from_probe_mapping(
        {
            "source": SOURCE,
            "raster": {"width_px": width, "height_px": height, "sha256": "7" * 64},
            "tool_results": [
                {
                    "source": SOURCE,
                    "tool_id": "pypdfium2",
                    "tool_version": "5.14.0",
                    "status": "PASS",
                    "metrics": {
                        "png_sha256": png_sha256,
                        "png_role": "EVIDENCE_RENDER_ONLY_NOT_STRUCTURAL_TRUTH",
                    },
                    "limitations": [],
                }
            ],
        }
    )


def _config() -> ExtractionConfig:
    return ExtractionConfig(
        threshold=180,
        min_width_px=20,
        min_height_px=20,
        max_width_px=140,
        max_height_px=140,
        min_rectangularity=0.45,
        max_aspect_ratio=5.0,
        duplicate_iou_threshold=0.72,
    )


class EvidenceExtractionV3HardeningTests(unittest.TestCase):
    def test_nested_subregions_are_suppressed_when_outer_envelope_exists(self) -> None:
        # Shape measured from the V3 review class: one valid 89x85 envelope plus
        # four internal quadrants from the same physical drawing symbol.
        rectangles = [
            (2928, 10710, 89, 85, 0.776662),
            (2929, 10710, 56, 46, 1.0),
            (2986, 10710, 31, 45, 1.0),
            (2928, 10757, 57, 38, 1.0),
            (2987, 10757, 29, 37, 1.0),
        ]

        deduplicated = _deduplicate_rectangles(rectangles, threshold=0.72)

        self.assertEqual(deduplicated, [(2928, 10710, 89, 85, 0.776662)])

    def test_isolated_closed_mark_without_external_drawing_context_is_not_step4_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            raster = np.full((320, 360), 255, dtype=np.uint8)

            # Looks locally like a framed annotation, but there is no linework
            # entering/leaving the frame. This represents the cartiglio/text-noise
            # class seen in the V3 human-review package.
            cv2.rectangle(raster, (120, 105), (190, 185), 0, 3)
            cv2.line(raster, (140, 128), (157, 118), 0, 3)
            cv2.line(raster, (157, 118), (157, 150), 0, 3)
            cv2.line(raster, (139, 163), (170, 163), 0, 3)
            cv2.line(raster, (170, 163), (151, 178), 0, 3)

            path = directory / "isolated-framed-mark.png"
            self.assertTrue(cv2.imwrite(str(path), raster))
            candidates = extract_g4_evidence_candidates(
                _binding(path, width=360, height=320),
                path,
                config=_config(),
            )

        self.assertEqual(candidates, ())


if __name__ == "__main__":
    unittest.main()
