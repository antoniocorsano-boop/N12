from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

import cew_b01.evidence_extraction as evidence_extraction
from cew_b01.evidence_extraction import ExtractionConfig, extract_g4_evidence_candidates
from cew_b01.evidence_schema import Task3RasterBinding


SOURCE = {
    "repository": "antoniocorsano-boop/N12",
    "commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
    "path": "archive/documentazione_originaria/tavola 5.pdf",
    "git_blob_sha": "ec32cd621877e9037cb26ebc083164140a8e3e68",
    "sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    "page_index": 0,
}


class EvidenceExtractionTests(unittest.TestCase):
    def _synthetic_raster(self, directory: Path) -> tuple[Path, Task3RasterBinding]:
        raster = np.full((512, 512), 255, dtype=np.uint8)
        cv2.rectangle(raster, (50, 60), (95, 125), 0, 3)
        cv2.rectangle(raster, (220, 250), (270, 290), 0, 3)
        cv2.line(raster, (10, 400), (490, 400), 0, 2)
        path = directory / "step3-raster.png"
        self.assertTrue(cv2.imwrite(str(path), raster))
        png_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        probe_mapping = {
            "source": SOURCE,
            "raster": {"width_px": 512, "height_px": 512, "sha256": "1" * 64},
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
        return path, Task3RasterBinding.from_probe_mapping(probe_mapping)

    def test_extraction_is_deterministic_from_exact_step3_raster(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path, binding = self._synthetic_raster(Path(tmp))
            config = ExtractionConfig(
                threshold=180,
                min_width_px=20,
                min_height_px=20,
                max_width_px=120,
                max_height_px=120,
                min_rectangularity=0.55,
                max_aspect_ratio=5.0,
                duplicate_iou_threshold=0.75,
            )
            first = extract_g4_evidence_candidates(binding, path, config=config)
            replay = extract_g4_evidence_candidates(binding, path, config=config)

        self.assertGreaterEqual(len(first), 2)
        self.assertEqual(
            [candidate.candidate_id for candidate in first],
            [candidate.candidate_id for candidate in replay],
        )
        self.assertEqual(
            [candidate.geometry_digest for candidate in first],
            [candidate.geometry_digest for candidate in replay],
        )
        self.assertTrue(all(item.source.sha256 == SOURCE["sha256"] for item in first))
        self.assertTrue(all(item.geometry.frame.value == "RASTER_PIXEL" for item in first))
        self.assertTrue(all(item.structural_identity_authorized is False for item in first))

    def test_extraction_fails_closed_if_step3_png_identity_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path, binding = self._synthetic_raster(Path(tmp))
            path.write_bytes(path.read_bytes() + b"tampered")
            with self.assertRaises(ValueError):
                extract_g4_evidence_candidates(binding, path)

    def test_task3_binding_requires_governed_render_role(self) -> None:
        mapping = {
            "source": SOURCE,
            "raster": {"width_px": 10, "height_px": 10, "sha256": "1" * 64},
            "tool_results": [
                {
                    "source": SOURCE,
                    "tool_id": "pypdfium2",
                    "tool_version": "5.14.0",
                    "status": "PASS",
                    "metrics": {
                        "png_sha256": "2" * 64,
                        "png_role": "UNCONTROLLED_RENDER",
                    },
                    "limitations": [],
                }
            ],
        }
        with self.assertRaises(ValueError):
            Task3RasterBinding.from_probe_mapping(mapping)

    def test_extraction_code_has_no_historical_oracle_interface(self) -> None:
        signature = inspect.signature(extract_g4_evidence_candidates)
        self.assertEqual(list(signature.parameters), ["binding", "raster_path", "config"])
        source = inspect.getsource(evidence_extraction).lower()
        for forbidden in (
            "oar",
            "pr #132",
            "pull/132",
            "historical_support",
            "expected_support_count",
            "family_count",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
