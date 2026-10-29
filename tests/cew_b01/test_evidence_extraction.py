from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

import cew_b01.evidence_extraction as evidence_extraction
from cew_b01.drawing_grammar import DrawingGrammarConfig, extract_drawing_motifs
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


def _binding_for_raster(path: Path, *, width: int, height: int, raster_sha: str) -> Task3RasterBinding:
    png_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    probe_mapping = {
        "source": SOURCE,
        "raster": {"width_px": width, "height_px": height, "sha256": raster_sha},
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
    return Task3RasterBinding.from_probe_mapping(probe_mapping)


class DrawingGrammarTests(unittest.TestCase):
    def _grammar_config(self) -> DrawingGrammarConfig:
        return DrawingGrammarConfig(
            min_width_px=24,
            min_height_px=24,
            max_width_px=120,
            max_height_px=120,
            max_aspect_ratio=2.5,
            min_frame_coverage=0.62,
            min_internal_ink_ratio=0.01,
            min_internal_components=1,
        )

    def test_closed_frame_with_internal_digit_like_strokes_emits_motif(self) -> None:
        raster = np.zeros((240, 240), dtype=np.uint8)
        cv2.rectangle(raster, (80, 70), (150, 150), 255, 3)
        cv2.line(raster, (100, 92), (116, 82), 255, 3)
        cv2.line(raster, (116, 82), (116, 112), 255, 3)
        cv2.line(raster, (98, 126), (125, 126), 255, 3)
        cv2.line(raster, (125, 126), (106, 143), 255, 3)

        motifs = extract_drawing_motifs(raster, self._grammar_config())

        self.assertEqual(len(motifs), 1)
        motif = motifs[0]
        self.assertGreaterEqual(motif.internal_component_count, 1)
        self.assertGreater(motif.internal_ink_ratio, 0.0)
        self.assertFalse(motif.single_full_span_divider)
        self.assertEqual(motif.semantic_identity, None)

    def test_empty_frame_and_single_full_span_divider_do_not_emit_motifs(self) -> None:
        raster = np.zeros((300, 320), dtype=np.uint8)
        cv2.rectangle(raster, (40, 50), (110, 130), 255, 3)
        cv2.rectangle(raster, (180, 50), (250, 130), 255, 3)
        cv2.line(raster, (215, 53), (215, 127), 255, 3)

        motifs = extract_drawing_motifs(raster, self._grammar_config())

        self.assertEqual(motifs, ())

    def test_context_features_are_source_local_and_nonsemantic(self) -> None:
        raster = np.zeros((360, 520), dtype=np.uint8)
        for x, y in ((60, 70), (230, 190)):
            cv2.rectangle(raster, (x, y), (x + 70, y + 80), 255, 3)
            cv2.line(raster, (x + 22, y + 18), (x + 40, y + 10), 255, 3)
            cv2.line(raster, (x + 40, y + 10), (x + 40, y + 38), 255, 3)
            cv2.line(raster, (x - 45, y + 40), (x, y + 40), 255, 2)
            cv2.line(raster, (x + 70, y + 40), (x + 110, y + 40), 255, 2)

        cv2.rectangle(raster, (390, 60), (460, 140), 255, 3)
        cv2.line(raster, (412, 78), (430, 70), 255, 3)
        cv2.line(raster, (430, 70), (430, 98), 255, 3)
        cv2.line(raster, (425, 140), (425, 205), 255, 2)

        motifs = extract_drawing_motifs(raster, self._grammar_config())

        self.assertEqual(len(motifs), 3)
        self.assertTrue(all(item.semantic_identity is None for item in motifs))
        self.assertTrue(all(len(item.context_signature) == 4 for item in motifs))
        active_patterns = {
            tuple(value >= 0.03 for value in item.context_signature)
            for item in motifs
        }
        self.assertGreaterEqual(len(active_patterns), 2)


class EvidenceExtractionTests(unittest.TestCase):
    def _synthetic_raster(self, directory: Path) -> tuple[Path, Task3RasterBinding]:
        raster = np.full((512, 512), 255, dtype=np.uint8)

        # Two valid composite symbols. Internal orthogonal strokes split each
        # physical symbol into four source cells that must be recomposed once.
        cv2.line(raster, (20, 100), (210, 100), 0, 2)
        cv2.line(raster, (100, 20), (100, 210), 0, 2)
        cv2.rectangle(raster, (70, 65), (130, 135), 0, 3)

        cv2.line(raster, (250, 340), (490, 340), 0, 2)
        cv2.line(raster, (360, 225), (360, 475), 0, 2)
        cv2.rectangle(raster, (325, 305), (395, 375), 0, 3)

        # Closed rectangle without the compound-cell grammar: never a support
        # candidate merely because it is rectangular.
        cv2.rectangle(raster, (220, 70), (275, 110), 0, 3)

        path = directory / "step3-raster.png"
        self.assertTrue(cv2.imwrite(str(path), raster))
        return path, _binding_for_raster(path, width=512, height=512, raster_sha="1" * 64)

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

        self.assertEqual(len(first), 2)
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

    def test_axis_crossed_column_is_recomposed_once_and_single_axis_section_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            raster = np.full((512, 512), 255, dtype=np.uint8)

            # True object pattern: a closed column symbol crossed by both structural axes.
            cv2.line(raster, (40, 150), (260, 150), 0, 2)
            cv2.line(raster, (150, 40), (150, 260), 0, 2)
            cv2.rectangle(raster, (120, 115), (180, 185), 0, 3)

            # False-positive pattern seen in the real review package: a beam/section
            # rectangle attached to only one long structural direction.
            cv2.line(raster, (300, 150), (480, 150), 0, 2)
            cv2.rectangle(raster, (350, 132), (400, 168), 0, 3)

            path = directory / "axis-object-raster.png"
            self.assertTrue(cv2.imwrite(str(path), raster))
            binding = _binding_for_raster(path, width=512, height=512, raster_sha="3" * 64)
            candidates = extract_g4_evidence_candidates(
                binding,
                path,
                config=ExtractionConfig(
                    threshold=180,
                    min_width_px=15,
                    min_height_px=15,
                    max_width_px=120,
                    max_height_px=120,
                    min_rectangularity=0.50,
                    max_aspect_ratio=5.0,
                    duplicate_iou_threshold=0.75,
                ),
            )

        self.assertEqual(len(candidates), 1)
        column = candidates[0].geometry
        self.assertAlmostEqual(column.x + column.width / 2.0, 150.0, delta=5.0)
        self.assertAlmostEqual(column.y + column.height / 2.0, 150.0, delta=5.0)
        self.assertGreaterEqual(column.width, 55.0)
        self.assertGreaterEqual(column.height, 65.0)

    def test_source_like_compound_symbol_does_not_require_axes_to_continue_on_both_sides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            raster = np.full((512, 512), 255, dtype=np.uint8)

            # Source-like support: a closed outer frame split into four internal
            # cells. Beam edges attach from the left and a thin centre line exits
            # only above the frame; there is no bidirectional external cross.
            cv2.rectangle(raster, (120, 115), (180, 185), 0, 3)
            cv2.line(raster, (150, 115), (150, 185), 0, 2)
            cv2.line(raster, (120, 150), (180, 150), 0, 2)
            cv2.line(raster, (40, 115), (120, 115), 0, 2)
            cv2.line(raster, (40, 185), (120, 185), 0, 2)
            cv2.line(raster, (150, 60), (150, 115), 0, 2)

            # A neighbouring beam bay has only a single subdivision and must not
            # be promoted into the same geometric object grammar.
            cv2.rectangle(raster, (300, 120), (420, 180), 0, 3)
            cv2.line(raster, (360, 120), (360, 180), 0, 2)

            path = directory / "source-like-compound-raster.png"
            self.assertTrue(cv2.imwrite(str(path), raster))
            binding = _binding_for_raster(path, width=512, height=512, raster_sha="5" * 64)
            candidates = extract_g4_evidence_candidates(
                binding,
                path,
                config=ExtractionConfig(
                    threshold=180,
                    min_width_px=15,
                    min_height_px=15,
                    max_width_px=140,
                    max_height_px=140,
                    min_rectangularity=0.45,
                    max_aspect_ratio=5.0,
                    duplicate_iou_threshold=0.75,
                ),
            )

        self.assertEqual(len(candidates), 1)
        support = candidates[0].geometry
        self.assertAlmostEqual(support.x, 120.0, delta=5.0)
        self.assertAlmostEqual(support.y, 115.0, delta=5.0)
        self.assertAlmostEqual(support.width, 60.0, delta=7.0)
        self.assertAlmostEqual(support.height, 70.0, delta=7.0)

    def test_t_junction_is_not_mistaken_for_bidirectional_cross_axis_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            raster = np.full((512, 512), 255, dtype=np.uint8)

            # Both orientations exist, but the vertical line terminates at the
            # rectangle. A detector that merely asks for horizontal+vertical
            # pixels nearby would incorrectly accept this beam/T-junction pattern.
            cv2.line(raster, (280, 200), (480, 200), 0, 2)
            cv2.line(raster, (390, 20), (390, 182), 0, 2)
            cv2.rectangle(raster, (350, 182), (430, 218), 0, 3)

            path = directory / "t-junction-raster.png"
            self.assertTrue(cv2.imwrite(str(path), raster))
            binding = _binding_for_raster(path, width=512, height=512, raster_sha="4" * 64)
            candidates = extract_g4_evidence_candidates(
                binding,
                path,
                config=ExtractionConfig(
                    threshold=180,
                    min_width_px=15,
                    min_height_px=15,
                    max_width_px=120,
                    max_height_px=120,
                    min_rectangularity=0.50,
                    max_aspect_ratio=5.0,
                    duplicate_iou_threshold=0.75,
                ),
            )

        self.assertEqual(candidates, ())

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
