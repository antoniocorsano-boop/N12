from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from cew_b01.document_zoning import (
    apply_structural_workarea_mask,
    propose_document_zones,
    validate_zone_partition,
)
from cew_b01.evidence_schema import Task3RasterBinding
from cew_b01.grammar_schema import DocumentRegionKind, DocumentRegionMask
from cew_b01.records import CoordinateFrame, SourceIdentity


POLICY_PATH = Path("governance/cew-b01/TAV5_DOCUMENT_ZONE_POLICY_v1.json")


class DocumentZoningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SourceIdentity(
            repository="antoniocorsano-boop/N12",
            commit="1" * 40,
            path="archive/TAV5.pdf",
            git_blob_sha="2" * 40,
            sha256="3" * 64,
            page_index=0,
        )
        self.binding = Task3RasterBinding(
            source=self.source,
            raster_width_px=200,
            raster_height_px=120,
            raster_sha256="4" * 64,
            png_sha256="5" * 64,
            renderer_tool_id="pypdfium2",
            renderer_tool_version="4.30.0",
        )

    def _zone(
        self,
        kind: DocumentRegionKind,
        *,
        x: int,
        y: int,
        width: int,
        height: int,
        confirmed: bool,
    ) -> DocumentRegionMask:
        return DocumentRegionMask.create(
            source=self.source,
            frame=CoordinateFrame.RASTER_PIXEL,
            raster_width=200,
            raster_height=120,
            x=x,
            y=y,
            width=width,
            height=height,
            kind=kind,
            method="TEST_ZONE",
            human_confirmed=confirmed,
        )

    def _synthetic_sheet(self) -> np.ndarray:
        image = np.full((120, 200), 255, dtype=np.uint8)
        # Sparse structural linework in the left / central workarea.
        for x in (20, 55, 90, 125):
            cv2.line(image, (x, 15), (x, 100), 0, 2)
        for y in (25, 60, 95):
            cv2.line(image, (12, y), (135, y), 0, 2)
        # Dense orthogonal title-block grid in the lower-right corner.
        cv2.rectangle(image, (145, 72), (196, 116), 0, 2)
        for x in range(150, 196, 10):
            cv2.line(image, (x, 72), (x, 116), 0, 1)
        for y in range(78, 116, 8):
            cv2.line(image, (145, y), (196, y), 0, 1)
        return image

    def _synthetic_upper_left_title_block(self) -> np.ndarray:
        image = np.full((120, 200), 255, dtype=np.uint8)
        # Structural linework occupies the right and lower portions.
        for x in (90, 125, 160):
            cv2.line(image, (x, 35), (x, 110), 0, 2)
        for y in (45, 75, 105):
            cv2.line(image, (75, y), (190, y), 0, 2)
        # Dense title-block-like region in the upper-left corner.
        cv2.rectangle(image, (2, 2), (76, 38), 0, 2)
        for x in range(8, 76, 10):
            cv2.line(image, (x, 2), (x, 38), 0, 1)
        for y in range(8, 38, 7):
            cv2.line(image, (2, y), (76, y), 0, 1)
        return image

    def _synthetic_upper_left_title_block_after_blank_margin(self) -> np.ndarray:
        image = np.full((120, 200), 255, dtype=np.uint8)
        for x in (90, 125, 160):
            cv2.line(image, (x, 55), (x, 110), 0, 2)
        for y in (65, 90, 108):
            cv2.line(image, (75, y), (190, y), 0, 2)
        # The top blank strip is document margin and must not become TITLE_BLOCK.
        cv2.rectangle(image, (2, 10), (76, 46), 0, 2)
        for x in range(8, 76, 10):
            cv2.line(image, (x, 10), (x, 46), 0, 1)
        for y in range(16, 46, 7):
            cv2.line(image, (2, y), (76, y), 0, 1)
        return image

    def _synthetic_large_upper_left_title_block_with_sparse_header(self) -> tuple[np.ndarray, Task3RasterBinding]:
        image = np.full((480, 800), 255, dtype=np.uint8)
        binding = Task3RasterBinding(
            source=self.source,
            raster_width_px=800,
            raster_height_px=480,
            raster_sha256="6" * 64,
            png_sha256="7" * 64,
            renderer_tool_id="pypdfium2",
            renderer_tool_version="4.30.0",
        )

        # Structural linework is remote from the upper-left title block.
        for x in (420, 540, 660):
            cv2.line(image, (x, 165), (x, 440), 0, 3)
        for y in (190, 300, 410):
            cv2.line(image, (360, y), (760, y), 0, 3)

        # Real blank margin: y=0..29.
        # Sparse header: y=30..89. With a 16x16 grid, each cell is 50x30;
        # these few strokes remain well below the dense-cell threshold.
        cv2.line(image, (12, 34), (12, 86), 0, 2)
        cv2.line(image, (42, 44), (142, 44), 0, 2)
        cv2.line(image, (172, 68), (282, 68), 0, 2)

        # Dense title-block body begins around y=100 and is intentionally easy
        # for the coarse grid to detect.
        cv2.rectangle(image, (10, 100), (310, 260), 0, 3)
        for x in range(30, 310, 35):
            cv2.line(image, (x, 100), (x, 260), 0, 2)
        for y in range(120, 260, 25):
            cv2.line(image, (10, y), (310, y), 0, 2)
        return image, binding

    def test_same_raster_produces_deterministic_document_zone_proposals(self) -> None:
        image = self._synthetic_sheet()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.png"
            self.assertTrue(cv2.imwrite(str(path), image))
            first = propose_document_zones(self.binding, path)
            second = propose_document_zones(self.binding, path)
        self.assertEqual([item.to_mapping() for item in first], [item.to_mapping() for item in second])
        kinds = {item.kind for item in first}
        self.assertIn(DocumentRegionKind.STRUCTURAL_WORKAREA, kinds)
        self.assertIn(DocumentRegionKind.TITLE_BLOCK, kinds)
        for item in first:
            self.assertFalse(item.structural_identity_authorized)
            self.assertFalse(item.canonical_write_authorized)

    def test_title_block_proposal_is_corner_agnostic(self) -> None:
        image = self._synthetic_upper_left_title_block()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet-upper-left.png"
            self.assertTrue(cv2.imwrite(str(path), image))
            zones = propose_document_zones(self.binding, path)
        title_blocks = [zone for zone in zones if zone.kind == DocumentRegionKind.TITLE_BLOCK]
        self.assertEqual(len(title_blocks), 1)
        title = title_blocks[0]
        self.assertLess(title.x, 100)
        self.assertLess(title.y, 60)

    def test_title_block_proposal_does_not_absorb_leading_blank_margin(self) -> None:
        image = self._synthetic_upper_left_title_block_after_blank_margin()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet-upper-left-with-margin.png"
            self.assertTrue(cv2.imwrite(str(path), image))
            zones = propose_document_zones(self.binding, path)
        title_blocks = [zone for zone in zones if zone.kind == DocumentRegionKind.TITLE_BLOCK]
        self.assertEqual(len(title_blocks), 1)
        self.assertGreater(title_blocks[0].y, 0)

    def test_title_block_proposal_includes_sparse_header_but_keeps_true_blank_margin_out(self) -> None:
        image, binding = self._synthetic_large_upper_left_title_block_with_sparse_header()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet-upper-left-sparse-header-large.png"
            self.assertTrue(cv2.imwrite(str(path), image))
            zones = propose_document_zones(binding, path)
        title_blocks = [zone for zone in zones if zone.kind == DocumentRegionKind.TITLE_BLOCK]
        self.assertEqual(len(title_blocks), 1)
        title = title_blocks[0]
        self.assertGreater(title.y, 0)
        self.assertLessEqual(title.y, 35)

    def test_overlap_between_exclusion_and_workarea_fails_closed(self) -> None:
        zones = (
            self._zone(DocumentRegionKind.STRUCTURAL_WORKAREA, x=0, y=0, width=160, height=120, confirmed=True),
            self._zone(DocumentRegionKind.TITLE_BLOCK, x=145, y=72, width=51, height=44, confirmed=True),
        )
        with self.assertRaisesRegex(ValueError, "ZONE_PARTITION_REVIEW_REQUIRED"):
            validate_zone_partition(self.binding, zones)

    def test_two_disjoint_structural_workareas_remain_valid_distinct_regions(self) -> None:
        zones = (
            self._zone(DocumentRegionKind.STRUCTURAL_WORKAREA, x=0, y=0, width=80, height=120, confirmed=True),
            self._zone(DocumentRegionKind.STRUCTURAL_WORKAREA, x=90, y=0, width=50, height=120, confirmed=True),
            self._zone(DocumentRegionKind.TITLE_BLOCK, x=145, y=72, width=51, height=44, confirmed=True),
        )
        validate_zone_partition(self.binding, zones)
        self.assertEqual(sum(zone.kind == DocumentRegionKind.STRUCTURAL_WORKAREA for zone in zones), 2)

    def test_unconfirmed_title_block_cannot_suppress_g1_pixels(self) -> None:
        image = np.full((120, 200), 255, dtype=np.uint8)
        zones = (
            self._zone(DocumentRegionKind.STRUCTURAL_WORKAREA, x=0, y=0, width=140, height=120, confirmed=True),
            self._zone(DocumentRegionKind.TITLE_BLOCK, x=145, y=72, width=51, height=44, confirmed=False),
        )
        with self.assertRaisesRegex(ValueError, "UNCONFIRMED_EXCLUSION_MASK"):
            apply_structural_workarea_mask(image, zones)

    def test_confirmed_exclusion_zeroes_only_excluded_pixels_and_preserves_frame(self) -> None:
        image = np.full((120, 200), 255, dtype=np.uint8)
        zones = (
            self._zone(DocumentRegionKind.STRUCTURAL_WORKAREA, x=0, y=0, width=140, height=120, confirmed=True),
            self._zone(DocumentRegionKind.TITLE_BLOCK, x=145, y=72, width=51, height=44, confirmed=True),
        )
        masked = apply_structural_workarea_mask(image, zones)
        self.assertEqual(masked.shape, image.shape)
        self.assertEqual(int(masked[20, 20]), 255)
        self.assertEqual(int(masked[80, 150]), 0)
        self.assertEqual(int(masked[60, 142]), 0)  # outside confirmed structural workarea
        self.assertEqual(int(image[80, 150]), 255)  # source array not mutated

    def test_zone_policy_is_proposal_only_and_requires_human_confirmation(self) -> None:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(policy["schema"], "TAV5_DOCUMENT_ZONE_POLICY_v1")
        self.assertEqual(policy["authority_effect"], "NONE")
        self.assertTrue(policy["human_confirmation_required_for_exclusion"])
        self.assertFalse(policy["structural_identity_authorized"])
        self.assertFalse(policy["canonical_write_authorized"])
        self.assertIn("OBJECT_DETECTOR_OUTPUT", policy["forbidden_zoning_oracles"])


if __name__ == "__main__":
    unittest.main()
