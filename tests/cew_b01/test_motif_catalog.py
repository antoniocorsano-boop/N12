from __future__ import annotations

import unittest

from cew_b01.grammar_schema import (
    GraphicPrimitiveObservation,
    MotifClassificationState,
    PrimitiveFamily,
)
from cew_b01.motif_catalog import build_recurring_motif_catalog
from cew_b01.records import CoordinateFrame, SourceIdentity


class MotifCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SourceIdentity(
            repository="antoniocorsano-boop/N12",
            commit="1" * 40,
            path="archive/TAV5.pdf",
            git_blob_sha="2" * 40,
            sha256="3" * 64,
            page_index=0,
        )

    def _primitive(
        self,
        family: PrimitiveFamily,
        *,
        x: float,
        y: float,
        width: float,
        height: float,
        signature: dict[str, object],
    ) -> GraphicPrimitiveObservation:
        return GraphicPrimitiveObservation.create(
            source=self.source,
            frame=CoordinateFrame.RASTER_PIXEL,
            raster_width=1000,
            raster_height=1000,
            x=x,
            y=y,
            width=width,
            height=height,
            family=family,
            detector="TEST_G2",
            feature_signature=signature,
        )

    def test_translated_scaled_compatible_motifs_group_deterministically(self) -> None:
        items = (
            self._primitive(
                PrimitiveFamily.RECTILINEAR_CLOSED_SHAPE,
                x=10,
                y=20,
                width=40,
                height=20,
                signature={"vertex_count": 4, "rectangularity": 0.91},
            ),
            self._primitive(
                PrimitiveFamily.RECTILINEAR_CLOSED_SHAPE,
                x=300,
                y=400,
                width=80,
                height=40,
                signature={"vertex_count": 4, "rectangularity": 0.89},
            ),
            self._primitive(
                PrimitiveFamily.LINE_SEGMENT,
                x=100,
                y=100,
                width=120,
                height=2,
                signature={"orientation": "HORIZONTAL", "length_px": 120.0},
            ),
        )
        first = build_recurring_motif_catalog(items)
        second = build_recurring_motif_catalog(tuple(reversed(items)))
        self.assertEqual([item.to_mapping() for item in first], [item.to_mapping() for item in second])
        rectangle_groups = [item for item in first if item.neutral_descriptor.get("family") == PrimitiveFamily.RECTILINEAR_CLOSED_SHAPE.value]
        self.assertEqual(len(rectangle_groups), 1)
        self.assertEqual(rectangle_groups[0].occurrence_count, 2)

    def test_unrelated_families_remain_separate_and_nonsemantic(self) -> None:
        items = (
            self._primitive(
                PrimitiveFamily.LINE_SEGMENT,
                x=10,
                y=10,
                width=100,
                height=2,
                signature={"orientation": "HORIZONTAL", "length_px": 100.0},
            ),
            self._primitive(
                PrimitiveFamily.TEXT_BLOCK,
                x=20,
                y=40,
                width=35,
                height=12,
                signature={"component_area": 120, "ink_ratio": 0.28},
            ),
        )
        catalog = build_recurring_motif_catalog(items)
        self.assertEqual(len(catalog), 2)
        for motif in catalog:
            self.assertEqual(motif.classification_state, MotifClassificationState.UNCLASSIFIED)
            self.assertIsNone(motif.semantic_meaning)
            self.assertFalse(motif.structural_identity_authorized)
            self.assertFalse(motif.canonical_write_authorized)

    def test_recurring_unknown_graphics_are_preserved_as_visible_catalog_entry(self) -> None:
        items = (
            self._primitive(
                PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP,
                x=40,
                y=50,
                width=30,
                height=20,
                signature={"component_area": 210, "ink_ratio": 0.35},
            ),
            self._primitive(
                PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP,
                x=240,
                y=350,
                width=60,
                height=40,
                signature={"component_area": 820, "ink_ratio": 0.36},
            ),
        )
        catalog = build_recurring_motif_catalog(items)
        unknown = [item for item in catalog if item.neutral_descriptor.get("family") == PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP.value]
        self.assertEqual(len(unknown), 1)
        self.assertEqual(unknown[0].occurrence_count, 2)
        self.assertEqual(unknown[0].classification_state, MotifClassificationState.UNCLASSIFIED)

    def test_catalog_never_groups_across_source_versions(self) -> None:
        first = self._primitive(
            PrimitiveFamily.RECTILINEAR_CLOSED_SHAPE,
            x=10,
            y=20,
            width=40,
            height=20,
            signature={"vertex_count": 4, "rectangularity": 0.9},
        )
        other_source = SourceIdentity(
            repository=self.source.repository,
            commit="4" * 40,
            path=self.source.path,
            git_blob_sha="5" * 40,
            sha256="6" * 64,
            page_index=0,
        )
        second = GraphicPrimitiveObservation.create(
            source=other_source,
            frame=CoordinateFrame.RASTER_PIXEL,
            raster_width=1000,
            raster_height=1000,
            x=100,
            y=200,
            width=80,
            height=40,
            family=PrimitiveFamily.RECTILINEAR_CLOSED_SHAPE,
            detector="TEST_G2",
            feature_signature={"vertex_count": 4, "rectangularity": 0.9},
        )
        catalog = build_recurring_motif_catalog((first, second))
        self.assertEqual(len(catalog), 2)
        self.assertTrue(all(item.occurrence_count == 1 for item in catalog))


if __name__ == "__main__":
    unittest.main()
