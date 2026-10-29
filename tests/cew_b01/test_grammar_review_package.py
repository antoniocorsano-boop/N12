from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from cew_b01.evidence_schema import Task3RasterBinding
from cew_b01.grammar_review_package import render_grammar_foundation_review_package
from cew_b01.grammar_schema import (
    DocumentRegionKind,
    DocumentRegionMask,
    GraphicPrimitiveObservation,
    PrimitiveFamily,
    RecurringMotif,
)
from cew_b01.records import CoordinateFrame, SourceIdentity


class GrammarReviewPackageTests(unittest.TestCase):
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
            raster_width_px=240,
            raster_height_px=160,
            raster_sha256="4" * 64,
            png_sha256="5" * 64,
            renderer_tool_id="pypdfium2",
            renderer_tool_version="4.30.0",
        )
        self.workarea = DocumentRegionMask.create(
            source=self.source,
            frame=CoordinateFrame.RASTER_PIXEL,
            raster_width=240,
            raster_height=160,
            x=0,
            y=0,
            width=180,
            height=160,
            kind=DocumentRegionKind.STRUCTURAL_WORKAREA,
            method="TEST_G0",
            human_confirmed=True,
        )
        self.title = DocumentRegionMask.create(
            source=self.source,
            frame=CoordinateFrame.RASTER_PIXEL,
            raster_width=240,
            raster_height=160,
            x=180,
            y=0,
            width=60,
            height=160,
            kind=DocumentRegionKind.TITLE_BLOCK,
            method="TEST_G0",
            human_confirmed=True,
        )
        self.zones = (self.workarea, self.title)

    def _primitive(self, family: PrimitiveFamily, *, x: int, y: int, width: int, height: int) -> GraphicPrimitiveObservation:
        return GraphicPrimitiveObservation.create(
            source=self.source,
            frame=CoordinateFrame.RASTER_PIXEL,
            raster_width=240,
            raster_height=160,
            x=x,
            y=y,
            width=width,
            height=height,
            family=family,
            detector="TEST_G1",
            feature_signature={"ink_ratio": 0.35},
        )

    def _raster(self, path: Path) -> None:
        image = np.full((160, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(image, (20, 20), (60, 55), (0, 0, 0), 2)
        cv2.line(image, (20, 90), (160, 90), (0, 0, 0), 2)
        # Unaccounted significant workarea mark: must appear in coverage summary.
        cv2.circle(image, (145, 125), 8, (0, 0, 0), 2)
        # Dense title-block graphics that must never appear in motif crops.
        cv2.rectangle(image, (185, 10), (232, 150), (0, 0, 0), 2)
        for yy in range(20, 150, 12):
            cv2.line(image, (185, yy), (232, yy), (0, 0, 0), 1)
        self.assertTrue(cv2.imwrite(str(path), image))

    def test_package_renders_unknown_motifs_and_reports_unaccounted_ink(self) -> None:
        p1 = self._primitive(PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP, x=18, y=18, width=45, height=40)
        p2 = self._primitive(PrimitiveFamily.LINE_SEGMENT, x=18, y=87, width=145, height=7)
        motifs = (
            RecurringMotif.create(
                source=self.source,
                member_primitive_ids=(p1.primitive_id,),
                representative_primitive_id=p1.primitive_id,
                neutral_descriptor={"family": PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP.value, "aspect_bin": 1.0},
            ),
            RecurringMotif.create(
                source=self.source,
                member_primitive_ids=(p2.primitive_id,),
                representative_primitive_id=p2.primitive_id,
                neutral_descriptor={"family": PrimitiveFamily.LINE_SEGMENT.value, "orientation": "HORIZONTAL"},
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raster = root / "sheet.png"
            self._raster(raster)
            result = render_grammar_foundation_review_package(
                self.binding,
                raster,
                self.zones,
                (p1, p2),
                motifs,
                root / "out",
            )
            manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["review_state"], "PENDING_HUMAN_MOTIF_REVIEW")
            self.assertTrue(manifest["g0_g2_engineering_pass"])
            self.assertGreater(manifest["coverage"]["unaccounted_ink_pixels"], 0)
            self.assertEqual(manifest["motifs"]["unknown_motif_count"], 1)
            self.assertTrue(Path(result["zone_overview_path"]).exists())
            self.assertTrue(Path(result["coverage_overlay_path"]).exists())
            self.assertGreaterEqual(len(result["motif_atlas_paths"]), 1)

    def test_title_block_primitive_is_rejected_from_grammar_atlas(self) -> None:
        illegal = self._primitive(PrimitiveFamily.TEXT_BLOCK, x=190, y=30, width=30, height=20)
        motif = RecurringMotif.create(
            source=self.source,
            member_primitive_ids=(illegal.primitive_id,),
            representative_primitive_id=illegal.primitive_id,
            neutral_descriptor={"family": PrimitiveFamily.TEXT_BLOCK.value},
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raster = root / "sheet.png"
            self._raster(raster)
            with self.assertRaisesRegex(ValueError, "GRAMMAR_REVIEW_PRIMITIVE_OUTSIDE_WORKAREA"):
                render_grammar_foundation_review_package(
                    self.binding,
                    raster,
                    self.zones,
                    (illegal,),
                    (motif,),
                    root / "out",
                )

    def test_unknown_motif_cannot_be_omitted_from_manifest(self) -> None:
        unknown = self._primitive(PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP, x=30, y=30, width=20, height=20)
        motif = RecurringMotif.create(
            source=self.source,
            member_primitive_ids=(unknown.primitive_id,),
            representative_primitive_id=unknown.primitive_id,
            neutral_descriptor={"family": PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP.value},
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raster = root / "sheet.png"
            self._raster(raster)
            result = render_grammar_foundation_review_package(
                self.binding,
                raster,
                self.zones,
                (unknown,),
                (motif,),
                root / "out",
            )
            manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
            motif_ids = {item["motif_id"] for item in manifest["motifs"]["items"]}
            self.assertIn(motif.motif_id, motif_ids)
            self.assertEqual(manifest["motifs"]["unknown_motif_count"], 1)


if __name__ == "__main__":
    unittest.main()
