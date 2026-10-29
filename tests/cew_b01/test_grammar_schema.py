from __future__ import annotations

import unittest

from cew_b01.records import CoordinateFrame, SourceIdentity
from cew_b01.grammar_schema import (
    DocumentRegionKind,
    DocumentRegionMask,
    GraphicPrimitiveObservation,
    MotifClassificationState,
    PrimitiveFamily,
    RecurringMotif,
)


class GrammarSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SourceIdentity(
            repository="antoniocorsano-boop/N12",
            commit="1" * 40,
            path="archive/TAV5.pdf",
            git_blob_sha="2" * 40,
            sha256="3" * 64,
            page_index=0,
        )

    def test_document_region_kind_is_exhaustive_for_g0_v1(self) -> None:
        self.assertEqual(
            {item.value for item in DocumentRegionKind},
            {
                "STRUCTURAL_WORKAREA",
                "TITLE_BLOCK",
                "LOCATION_DIAGRAM",
                "APPROVAL_STAMP_SIGNATURE",
                "NOTE_OR_LEGEND_REGION",
                "MARGIN_VOID",
                "SCAN_ARTIFACT",
                "UNKNOWN_DOCUMENT_REGION",
            },
        )

    def test_document_region_rejects_nonpositive_or_out_of_frame_geometry(self) -> None:
        invalid = (
            dict(x=-1, y=0, width=10, height=10),
            dict(x=0, y=0, width=0, height=10),
            dict(x=0, y=0, width=10, height=-1),
            dict(x=95, y=0, width=10, height=10),
        )
        for geometry in invalid:
            with self.subTest(geometry=geometry), self.assertRaises(ValueError):
                DocumentRegionMask.create(
                    source=self.source,
                    frame=CoordinateFrame.RASTER_PIXEL,
                    raster_width=100,
                    raster_height=100,
                    kind=DocumentRegionKind.STRUCTURAL_WORKAREA,
                    method="TEST",
                    human_confirmed=False,
                    **geometry,
                )

    def test_region_requires_source_and_typed_coordinate_frame(self) -> None:
        with self.assertRaises(ValueError):
            DocumentRegionMask.create(
                source=self.source,
                frame="RASTER_PIXEL",  # type: ignore[arg-type]
                raster_width=100,
                raster_height=100,
                x=1,
                y=2,
                width=20,
                height=30,
                kind=DocumentRegionKind.TITLE_BLOCK,
                method="TEST",
                human_confirmed=False,
            )

    def test_graphic_primitive_is_nonauthoritative(self) -> None:
        observation = GraphicPrimitiveObservation.create(
            source=self.source,
            frame=CoordinateFrame.RASTER_PIXEL,
            raster_width=100,
            raster_height=100,
            x=10,
            y=12,
            width=20,
            height=8,
            family=PrimitiveFamily.RECTILINEAR_CLOSED_SHAPE,
            detector="SYNTHETIC",
            feature_signature={"aspect_bucket": "WIDE"},
        )
        self.assertIsNone(observation.semantic_meaning)
        self.assertFalse(observation.structural_identity_authorized)
        self.assertFalse(observation.canonical_write_authorized)
        self.assertEqual(observation.page_index, self.source.page_index)
        self.assertEqual(observation.frame, CoordinateFrame.RASTER_PIXEL)

    def test_recurring_motif_defaults_to_unclassified_and_nonauthoritative(self) -> None:
        primitive = GraphicPrimitiveObservation.create(
            source=self.source,
            frame=CoordinateFrame.RASTER_PIXEL,
            raster_width=100,
            raster_height=100,
            x=10,
            y=12,
            width=20,
            height=8,
            family=PrimitiveFamily.COMPLEX_GRAPHIC_GROUP,
            detector="SYNTHETIC",
            feature_signature={"complexity_bucket": "FEW"},
        )
        motif = RecurringMotif.create(
            source=self.source,
            member_primitive_ids=(primitive.primitive_id,),
            representative_primitive_id=primitive.primitive_id,
            neutral_descriptor={"primitive_family": primitive.family.value},
        )
        self.assertEqual(motif.classification_state, MotifClassificationState.UNCLASSIFIED)
        self.assertIsNone(motif.semantic_meaning)
        self.assertFalse(motif.structural_identity_authorized)
        self.assertFalse(motif.canonical_write_authorized)

    def test_stable_ids_are_repeatable_and_geometry_sensitive(self) -> None:
        common = dict(
            source=self.source,
            frame=CoordinateFrame.RASTER_PIXEL,
            raster_width=100,
            raster_height=100,
            y=2,
            width=20,
            height=30,
            kind=DocumentRegionKind.TITLE_BLOCK,
            method="TEST",
            human_confirmed=False,
        )
        first = DocumentRegionMask.create(x=1, **common)
        repeated = DocumentRegionMask.create(x=1, **common)
        moved = DocumentRegionMask.create(x=2, **common)
        self.assertEqual(first.region_id, repeated.region_id)
        self.assertEqual(first.geometry_digest, repeated.geometry_digest)
        self.assertNotEqual(first.region_id, moved.region_id)
        self.assertNotEqual(first.geometry_digest, moved.geometry_digest)
        self.assertEqual(first.to_mapping(), repeated.to_mapping())


if __name__ == "__main__":
    unittest.main()
