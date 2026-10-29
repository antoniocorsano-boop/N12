from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from cew_b01.evidence_schema import Task3RasterBinding
from cew_b01.grammar_schema import DocumentRegionKind, DocumentRegionMask
from cew_b01.records import CoordinateFrame, SourceIdentity
from cew_b01.zone_review_package import (
    build_zone_confirmation_receipt,
    confirmed_zones_from_receipt,
    render_zone_review_package,
    zone_set_digest,
)


class ZoneReviewPackageTests(unittest.TestCase):
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
            raster_width_px=160,
            raster_height_px=100,
            raster_sha256="4" * 64,
            png_sha256="5" * 64,
            renderer_tool_id="pypdfium2",
            renderer_tool_version="4.30.0",
        )
        self.zones = (
            DocumentRegionMask.create(
                source=self.source,
                frame=CoordinateFrame.RASTER_PIXEL,
                raster_width=160,
                raster_height=100,
                x=0,
                y=0,
                width=115,
                height=100,
                kind=DocumentRegionKind.STRUCTURAL_WORKAREA,
                method="TEST_PROPOSAL",
                human_confirmed=False,
            ),
            DocumentRegionMask.create(
                source=self.source,
                frame=CoordinateFrame.RASTER_PIXEL,
                raster_width=160,
                raster_height=100,
                x=115,
                y=55,
                width=45,
                height=45,
                kind=DocumentRegionKind.TITLE_BLOCK,
                method="TEST_PROPOSAL",
                human_confirmed=False,
            ),
            DocumentRegionMask.create(
                source=self.source,
                frame=CoordinateFrame.RASTER_PIXEL,
                raster_width=160,
                raster_height=100,
                x=115,
                y=0,
                width=45,
                height=55,
                kind=DocumentRegionKind.STRUCTURAL_WORKAREA,
                method="TEST_PROPOSAL",
                human_confirmed=False,
            ),
        )

    def _raster(self, path: Path) -> None:
        image = np.full((100, 160, 3), 255, dtype=np.uint8)
        cv2.rectangle(image, (115, 55), (159, 99), (0, 0, 0), 1)
        self.assertTrue(cv2.imwrite(str(path), image))

    def test_pending_package_cannot_claim_g0_pass_and_keeps_source_identities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raster = root / "tav5.png"
            self._raster(raster)
            result = render_zone_review_package(
                self.binding,
                raster,
                self.zones,
                root / "out",
            )
            manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["review_state"], "PENDING_HUMAN_ZONE_REVIEW")
            self.assertFalse(manifest["g0_document_zoning_pass"])
            self.assertEqual(manifest["source"]["sha256"], self.source.sha256)
            self.assertEqual(manifest["raster"]["png_sha256"], self.binding.png_sha256)
            self.assertEqual(manifest["zone_set_digest"], zone_set_digest(self.zones))
            self.assertTrue(Path(result["overview_path"]).exists())
            self.assertEqual(len(result["zone_crop_paths"]), len(self.zones))

    def test_confirmation_receipt_is_bound_to_exact_source_raster_and_zone_digest(self) -> None:
        receipt = build_zone_confirmation_receipt(
            binding=self.binding,
            zones=self.zones,
            reviewer_decision_id="HUMAN-G0-TEST-001",
        )
        self.assertEqual(receipt["source_sha256"], self.source.sha256)
        self.assertEqual(receipt["raster_png_sha256"], self.binding.png_sha256)
        self.assertEqual(receipt["zone_set_digest"], zone_set_digest(self.zones))
        self.assertEqual(receipt["decision"], "CONFIRMED_FOR_G0_DOCUMENT_FUNCTION_ONLY")
        self.assertFalse(receipt["structural_identity_authorized"])
        self.assertFalse(receipt["canonical_write_authorized"])

    def test_matching_receipt_confirms_same_zone_ids_and_enables_g0_pass(self) -> None:
        receipt = build_zone_confirmation_receipt(
            binding=self.binding,
            zones=self.zones,
            reviewer_decision_id="HUMAN-G0-TEST-002",
        )
        confirmed = confirmed_zones_from_receipt(self.binding, self.zones, receipt)
        self.assertEqual([z.region_id for z in confirmed], [z.region_id for z in self.zones])
        self.assertTrue(all(z.human_confirmed for z in confirmed))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raster = root / "tav5.png"
            self._raster(raster)
            result = render_zone_review_package(
                self.binding,
                raster,
                self.zones,
                root / "out",
                confirmation_receipt=receipt,
            )
            manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["review_state"], "G0_DOCUMENT_ZONING_PASS")
            self.assertTrue(manifest["g0_document_zoning_pass"])

    def test_mismatched_receipt_fails_closed(self) -> None:
        receipt = build_zone_confirmation_receipt(
            binding=self.binding,
            zones=self.zones,
            reviewer_decision_id="HUMAN-G0-TEST-003",
        )
        receipt["zone_set_digest"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "ZONE_CONFIRMATION_RECEIPT_MISMATCH"):
            confirmed_zones_from_receipt(self.binding, self.zones, receipt)


if __name__ == "__main__":
    unittest.main()
