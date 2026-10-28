from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

import cew_b01.evidence_extraction as evidence_extraction
from cew_b01.evidence_extraction import (
    ExtractionConfig,
    evidence_bundle_mapping,
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

EXPECTED_METHOD = "OPENCV_DRAWING_GRAMMAR_CANDIDATE_UNION_V3"


def _binding(path: Path, *, width: int, height: int) -> Task3RasterBinding:
    png_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return Task3RasterBinding.from_probe_mapping(
        {
            "source": SOURCE,
            "raster": {"width_px": width, "height_px": height, "sha256": "6" * 64},
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


class EvidenceExtractionV3Tests(unittest.TestCase):
    def test_closed_frame_internal_mark_channel_recovers_non_four_cell_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            raster = np.full((320, 360), 255, dtype=np.uint8)

            cv2.rectangle(raster, (120, 105), (190, 185), 0, 3)
            cv2.line(raster, (140, 128), (157, 118), 0, 3)
            cv2.line(raster, (157, 118), (157, 150), 0, 3)
            cv2.line(raster, (139, 163), (170, 163), 0, 3)
            cv2.line(raster, (170, 163), (151, 178), 0, 3)
            cv2.line(raster, (70, 145), (120, 145), 0, 2)
            cv2.line(raster, (190, 145), (245, 145), 0, 2)

            path = directory / "numbered-frame.png"
            self.assertTrue(cv2.imwrite(str(path), raster))
            candidates = extract_g4_evidence_candidates(
                _binding(path, width=360, height=320),
                path,
                config=_config(),
            )

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.method, EXPECTED_METHOD)
        self.assertAlmostEqual(candidate.geometry.x, 120.0, delta=7.0)
        self.assertAlmostEqual(candidate.geometry.y, 105.0, delta=7.0)
        self.assertFalse(candidate.structural_identity_authorized)

    def test_overlapping_compound_and_drawing_grammar_channels_deduplicate_to_one_region(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            raster = np.full((320, 360), 255, dtype=np.uint8)

            cv2.rectangle(raster, (120, 105), (190, 185), 0, 3)
            cv2.line(raster, (155, 105), (155, 185), 0, 2)
            cv2.line(raster, (120, 145), (190, 145), 0, 2)
            cv2.line(raster, (70, 105), (120, 105), 0, 2)
            cv2.line(raster, (70, 185), (120, 185), 0, 2)

            path = directory / "overlap.png"
            self.assertTrue(cv2.imwrite(str(path), raster))
            candidates = extract_g4_evidence_candidates(
                _binding(path, width=360, height=320),
                path,
                config=_config(),
            )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].method, EXPECTED_METHOD)

    def test_evidence_bundle_declares_proposal_channels_and_reuse_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            raster = np.full((240, 260), 255, dtype=np.uint8)
            cv2.rectangle(raster, (90, 70), (155, 145), 0, 3)
            cv2.line(raster, (110, 92), (128, 82), 0, 3)
            cv2.line(raster, (128, 82), (128, 118), 0, 3)
            path = directory / "bundle-provenance.png"
            self.assertTrue(cv2.imwrite(str(path), raster))
            binding = _binding(path, width=260, height=240)
            candidates = extract_g4_evidence_candidates(binding, path, config=_config())
            bundle = evidence_bundle_mapping(binding, candidates, config=_config())

        channel_ids = {
            item["capability_id"] for item in bundle["extraction"]["proposal_channels"]
        }
        self.assertEqual(
            channel_ids,
            {
                "CEW-CAP-B01-V2-COMPOUND-CELL-DETECTOR",
                "CEW-CAP-B01-CLOSED-FRAME-INTERNAL-MARK-SPIKE",
            },
        )
        reconciliation = bundle["reconciliation_provenance"]
        self.assertEqual(
            reconciliation["oa3_similarity"]["source_ref"],
            "a7020bef3934156c917f5bfe975d888c6ba9e684",
        )
        self.assertEqual(
            reconciliation["structured_descriptor"]["source_ref"],
            "320755e66a7263f1842f73dc14fb9a0ea8ccd7f8",
        )
        self.assertEqual(
            reconciliation["engineering_grammar"]["source_ref"],
            "098f98d2724c0a16b9293adc366a585f356bc9fc",
        )
        self.assertEqual(
            reconciliation["oa3_similarity"]["execution_state"],
            "AVAILABLE_REQUIRES_HUMAN_TAUGHT_PROTOTYPE",
        )
        self.assertFalse(bundle["authority"]["structural_identity_authorized"])
        self.assertFalse(bundle["authority"]["canonical_write_authorized"])

    def test_v3_source_has_no_historical_number_or_semantic_oracle(self) -> None:
        source = inspect.getsource(evidence_extraction).lower()
        for forbidden in (
            "p-19",
            "p-22",
            "object_number_whitelist",
            "expected_support_count",
            "historical_support",
            "ocr_required",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
