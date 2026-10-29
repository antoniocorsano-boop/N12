from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from cew_b01.evidence_schema import Task3RasterBinding
from cew_b01.grammar_schema import DocumentRegionKind, DocumentRegionMask, PrimitiveFamily
from cew_b01.primitive_census import extract_neutral_primitives
from cew_b01.records import CoordinateFrame, SourceIdentity


class PrimitiveCensusTests(unittest.TestCase):
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
            raster_width_px=320,
            raster_height_px=220,
            raster_sha256="4" * 64,
            png_sha256="5" * 64,
            renderer_tool_id="pypdfium2",
            renderer_tool_version="4.30.0",
        )

    def _zone(self, kind: DocumentRegionKind, *, x: int, y: int, width: int, height: int, confirmed: bool) -> DocumentRegionMask:
        return DocumentRegionMask.create(
            source=self.source,
            frame=CoordinateFrame.RASTER_PIXEL,
            raster_width=self.binding.raster_width_px,
            raster_height=self.binding.raster_height_px,
            x=x,
            y=y,
            width=width,
            height=height,
            kind=kind,
            method="TEST_G1_ZONE",
            human_confirmed=confirmed,
        )

    def _zones(self, *, confirmed: bool = True) -> tuple[DocumentRegionMask, ...]:
        return (
            self._zone(DocumentRegionKind.STRUCTURAL_WORKAREA, x=0, y=0, width=250, height=220, confirmed=confirmed),
            self._zone(DocumentRegionKind.TITLE_BLOCK, x=250, y=0, width=70, height=220, confirmed=confirmed),
        )

    def _synthetic_sheet(self) -> np.ndarray:
        image = np.full((220, 320), 255, dtype=np.uint8)
        # Long neutral linear strokes and an orthogonal crossing.
        cv2.line(image, (20, 35), (220, 35), 0, 2)
        cv2.line(image, (100, 10), (100, 100), 0, 2)
        # Parallel pair.
        cv2.line(image, (20, 70), (180, 70), 0, 2)
        cv2.line(image, (20, 78), (180, 78), 0, 2)
        # Closed rectangle and deliberately broken rectangle.
        cv2.rectangle(image, (30, 115), (75, 155), 0, 2)
        cv2.line(image, (95, 115), (135, 115), 0, 2)
        cv2.line(image, (95, 115), (95, 155), 0, 2)
        cv2.line(image, (95, 155), (125, 155), 0, 2)
        # L and T motifs.
        cv2.line(image, (155, 120), (155, 165), 0, 2)
        cv2.line(image, (155, 165), (195, 165), 0, 2)
        cv2.line(image, (210, 120), (210, 170), 0, 2)
        cv2.line(image, (190, 135), (230, 135), 0, 2)
        # Text-like connected groups and a small filled/hatch region.
        cv2.putText(image, "A12", (25, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.55, 0, 1, cv2.LINE_AA)
        cv2.rectangle(image, (145, 185), (190, 210), 0, -1)
        for x in range(148, 190, 7):
            cv2.line(image, (x, 185), (x, 210), 255, 1)
        # Dense title-block-like graphics outside STRUCTURAL_WORKAREA: forbidden in G1 output.
        cv2.rectangle(image, (260, 20), (312, 205), 0, 2)
        for y in range(30, 205, 12):
            cv2.line(image, (260, y), (312, y), 0, 1)
        return image

    def test_g1_requires_human_confirmed_zone_partition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.png"
            self.assertTrue(cv2.imwrite(str(path), self._synthetic_sheet()))
            with self.assertRaisesRegex(ValueError, "G1_REQUIRES_CONFIRMED_G0_ZONES"):
                extract_neutral_primitives(self.binding, path, self._zones(confirmed=False))

    def test_neutral_census_is_deterministic_source_bound_and_nonauthoritative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.png"
            self.assertTrue(cv2.imwrite(str(path), self._synthetic_sheet()))
            first = extract_neutral_primitives(self.binding, path, self._zones())
            second = extract_neutral_primitives(self.binding, path, self._zones())
        self.assertTrue(first)
        self.assertEqual([item.to_mapping() for item in first], [item.to_mapping() for item in second])
        for item in first:
            self.assertEqual(item.source, self.source)
            self.assertIsNone(item.semantic_meaning)
            self.assertFalse(item.structural_identity_authorized)
            self.assertFalse(item.canonical_write_authorized)
            self.assertLess(item.x + item.width, 251)

    def test_census_exposes_multiple_neutral_primitive_families(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.png"
            self.assertTrue(cv2.imwrite(str(path), self._synthetic_sheet()))
            items = extract_neutral_primitives(self.binding, path, self._zones())
        families = {item.family for item in items}
        self.assertIn(PrimitiveFamily.LINE_SEGMENT, families)
        self.assertIn(PrimitiveFamily.INTERSECTION, families)
        self.assertIn(PrimitiveFamily.PARALLEL_LINE_PAIR, families)
        self.assertIn(PrimitiveFamily.RECTILINEAR_CLOSED_SHAPE, families)
        self.assertTrue(
            PrimitiveFamily.RECTILINEAR_OPEN_SHAPE in families
            or PrimitiveFamily.L_SHAPED_MOTIF in families
            or PrimitiveFamily.T_SHAPED_MOTIF in families
            or PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP in families
        )
        self.assertTrue(
            PrimitiveFamily.TEXT_BLOCK in families
            or PrimitiveFamily.COMPLEX_GRAPHIC_GROUP in families
            or PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP in families
        )

    def test_broken_scanned_shape_is_not_silently_dropped(self) -> None:
        image = np.full((220, 320), 255, dtype=np.uint8)
        cv2.line(image, (40, 40), (100, 40), 0, 2)
        cv2.line(image, (40, 40), (40, 100), 0, 2)
        cv2.line(image, (40, 100), (90, 100), 0, 2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.png"
            self.assertTrue(cv2.imwrite(str(path), image))
            items = extract_neutral_primitives(self.binding, path, self._zones())
        relevant = [item for item in items if item.x < 120 and item.y < 120]
        self.assertTrue(relevant)
        self.assertTrue(any(item.family in {
            PrimitiveFamily.LINE_SEGMENT,
            PrimitiveFamily.RECTILINEAR_OPEN_SHAPE,
            PrimitiveFamily.L_SHAPED_MOTIF,
            PrimitiveFamily.COMPLEX_GRAPHIC_GROUP,
            PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP,
        } for item in relevant))

    def test_every_emitted_primitive_bbox_is_fully_inside_confirmed_workarea(self) -> None:
        image = np.full((220, 320), 255, dtype=np.uint8)
        # The crossing is centered inside the workarea but its relation box extends
        # across x=250 into the confirmed TITLE_BLOCK. Center-only admission is unsafe.
        cv2.line(image, (150, 110), (249, 110), 0, 2)
        cv2.line(image, (248, 45), (248, 175), 0, 2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "boundary-crossing.png"
            self.assertTrue(cv2.imwrite(str(path), image))
            items = extract_neutral_primitives(self.binding, path, self._zones())

        self.assertTrue(items)
        for item in items:
            self.assertGreaterEqual(item.x, 0)
            self.assertGreaterEqual(item.y, 0)
            self.assertLessEqual(item.x + item.width, 250)
            self.assertLessEqual(item.y + item.height, 220)


if __name__ == "__main__":
    unittest.main()
