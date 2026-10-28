from __future__ import annotations

import unittest

from cew_b01.pdf_probe import (
    RENDER_DPI,
    pdf_point_to_raster_transform,
    should_trigger_ocr,
)
from cew_b01.records import (
    Coordinate2D,
    CoordinateFrame,
    FrameTransformError,
    PdfProbeResult,
    RecordValidationError,
    SourceIdentity,
    ToolProbeResult,
    ToolResultStatus,
)


class PdfProbeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SourceIdentity(
            repository="antoniocorsano-boop/N12",
            commit="78c20a52db4f391ce0d13b9705b9f04737e218c9",
            path="archive/documentazione_originaria/tavola 5.pdf",
            git_blob_sha="ec32cd621877e9037cb26ebc083164140a8e3e68",
            sha256="2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
            page_index=0,
        )

    def _probe_with_ocr_transport_sha(self, output_sha256: str) -> PdfProbeResult:
        trigger = should_trigger_ocr({"non_whitespace_text_char_count": 0})
        transform = pdf_point_to_raster_transform(page_height_points=792.0)
        common_metrics = {
            "trigger": trigger.to_mapping(),
            "returncode": 0,
            "output_role": "OCR_DERIVATIVE_EVIDENCE_NOT_SOURCE_AUTHORITY",
            "output_sha256": output_sha256,
        }
        return PdfProbeResult(
            source=self.source,
            renderer_tool_id="pypdfium2",
            renderer_version="5.14.0",
            render_dpi=300,
            page_width_points=612.0,
            page_height_points=792.0,
            raster_width_px=2550,
            raster_height_px=3300,
            raster_sha256="1" * 64,
            render_transform=transform,
            ocr_trigger=trigger,
            tool_results=(
                ToolProbeResult(
                    source=self.source,
                    tool_id="ocrmypdf",
                    tool_version="17.13.0",
                    status=ToolResultStatus.PASS,
                    metrics=common_metrics,
                ),
                ToolProbeResult(
                    source=self.source,
                    tool_id="tesseract",
                    tool_version="5.3.4",
                    status=ToolResultStatus.PASS,
                    metrics=common_metrics,
                ),
            ),
        )

    def test_coordinate_frames_are_typed_and_closed(self) -> None:
        self.assertEqual(
            {frame.value for frame in CoordinateFrame},
            {"PDF_POINT", "RASTER_PIXEL", "PAGE_MM"},
        )

    def test_coordinates_cannot_be_mixed_without_explicit_transform(self) -> None:
        pdf_point = Coordinate2D(CoordinateFrame.PDF_POINT, 72.0, 72.0)
        pixel = Coordinate2D(CoordinateFrame.RASTER_PIXEL, 300.0, 300.0)
        with self.assertRaises(TypeError):
            _ = pdf_point + pixel
        transform = pdf_point_to_raster_transform(page_height_points=792.0)
        with self.assertRaises(FrameTransformError):
            transform.apply(pixel)

    def test_300_dpi_transform_is_explicit_and_y_flipped(self) -> None:
        self.assertEqual(RENDER_DPI, 300)
        transform = pdf_point_to_raster_transform(page_height_points=792.0)
        self.assertEqual(transform.source_frame, CoordinateFrame.PDF_POINT)
        self.assertEqual(transform.target_frame, CoordinateFrame.RASTER_PIXEL)
        self.assertEqual(transform.metadata["dpi"], 300)
        mapped = transform.apply(Coordinate2D(CoordinateFrame.PDF_POINT, 72.0, 72.0))
        self.assertAlmostEqual(mapped.x, 300.0, places=9)
        self.assertAlmostEqual(mapped.y, 3000.0, places=9)

    def test_tool_result_requires_exact_source_and_tool_version(self) -> None:
        with self.assertRaises(RecordValidationError):
            ToolProbeResult(
                source=self.source,
                tool_id="pdfplumber",
                tool_version="",
                status=ToolResultStatus.PASS,
                metrics={},
            )

        result = ToolProbeResult(
            source=self.source,
            tool_id="pdfplumber",
            tool_version="0.11.10",
            status=ToolResultStatus.PASS,
            metrics={"text_char_count": 12, "non_whitespace_text_char_count": 8},
        )
        self.assertEqual(result.source.sha256, self.source.sha256)
        self.assertEqual(result.tool_version, "0.11.10")

    def test_pdf_probe_rejects_tool_result_bound_to_other_source(self) -> None:
        other_source = SourceIdentity(
            repository=self.source.repository,
            commit=self.source.commit,
            path=self.source.path,
            git_blob_sha=self.source.git_blob_sha,
            sha256="0" * 64,
            page_index=self.source.page_index,
        )
        wrong = ToolProbeResult(
            source=other_source,
            tool_id="pdfplumber",
            tool_version="0.11.10",
            status=ToolResultStatus.PASS,
            metrics={"text_char_count": 12, "non_whitespace_text_char_count": 8},
        )
        transform = pdf_point_to_raster_transform(page_height_points=792.0)
        with self.assertRaises(RecordValidationError):
            PdfProbeResult(
                source=self.source,
                renderer_tool_id="pypdfium2",
                renderer_version="5.14.0",
                render_dpi=300,
                page_width_points=612.0,
                page_height_points=792.0,
                raster_width_px=2550,
                raster_height_px=3300,
                raster_sha256="1" * 64,
                render_transform=transform,
                ocr_trigger=should_trigger_ocr({"non_whitespace_text_char_count": 8}),
                tool_results=(wrong,),
            )

    def test_ocr_trigger_is_deterministic_from_parser_output(self) -> None:
        usable = should_trigger_ocr(
            {
                "text_char_count": 12,
                "non_whitespace_text_char_count": 8,
            }
        )
        empty = should_trigger_ocr(
            {
                "text_char_count": 3,
                "non_whitespace_text_char_count": 0,
            }
        )
        self.assertFalse(usable.triggered)
        self.assertEqual(usable.reason, "USABLE_NATIVE_TEXT_LAYER")
        self.assertTrue(empty.triggered)
        self.assertEqual(empty.reason, "NO_NON_WHITESPACE_NATIVE_TEXT")

    def test_volatile_ocr_transport_sha_is_audited_but_excluded_from_receipt(self) -> None:
        first = self._probe_with_ocr_transport_sha("a" * 64)
        replay = self._probe_with_ocr_transport_sha("b" * 64)

        self.assertNotEqual(first.to_mapping(), replay.to_mapping())
        self.assertEqual(
            first.deterministic_receipt_sha256(),
            replay.deterministic_receipt_sha256(),
        )
        self.assertEqual(first.receipt_mapping(), replay.receipt_mapping())
        self.assertEqual(
            first.to_mapping()["tool_results"][0]["metrics"]["output_sha256"],
            "a" * 64,
        )
        self.assertNotIn(
            "output_sha256",
            first.receipt_mapping()["tool_results"][0]["metrics"],
        )


if __name__ == "__main__":
    unittest.main()
