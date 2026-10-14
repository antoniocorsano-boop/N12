from __future__ import annotations

import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping

from .records import (
    Coordinate2D,
    CoordinateFrame,
    FrameTransform,
    OcrTriggerDecision,
    PdfProbeResult,
    SourceIdentity,
    ToolProbeResult,
    ToolResultStatus,
)
from .source_contract import MaterializedSource


RENDER_DPI = 300
PDF_POINTS_PER_INCH = 72.0
_OCR_RULE_ID = "NON_WHITESPACE_NATIVE_TEXT_GT_ZERO_V1"


def pdf_point_to_raster_transform(page_height_points: float) -> FrameTransform:
    if isinstance(page_height_points, bool) or not isinstance(page_height_points, (int, float)):
        raise ValueError("page_height_points must be numeric")
    height = float(page_height_points)
    if not math.isfinite(height) or height <= 0:
        raise ValueError("page_height_points must be finite and positive")
    scale = RENDER_DPI / PDF_POINTS_PER_INCH
    return FrameTransform(
        source_frame=CoordinateFrame.PDF_POINT,
        target_frame=CoordinateFrame.RASTER_PIXEL,
        matrix=(
            scale,
            0.0,
            0.0,
            0.0,
            -scale,
            height * scale,
            0.0,
            0.0,
            1.0,
        ),
        metadata={
            "transform_id": "PDF_POINT_BOTTOM_LEFT_TO_RASTER_PIXEL_TOP_LEFT_V1",
            "dpi": RENDER_DPI,
            "pdf_points_per_inch": PDF_POINTS_PER_INCH,
            "y_axis_flip": True,
        },
    )


def should_trigger_ocr(parser_metrics: Mapping[str, Any]) -> OcrTriggerDecision:
    raw = parser_metrics.get("non_whitespace_text_char_count", 0)
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
        raise ValueError("non_whitespace_text_char_count must be a non-negative integer")
    triggered = raw == 0
    return OcrTriggerDecision(
        triggered=triggered,
        reason=(
            "NO_NON_WHITESPACE_NATIVE_TEXT"
            if triggered
            else "USABLE_NATIVE_TEXT_LAYER"
        ),
        basis={
            "rule_id": _OCR_RULE_ID,
            "non_whitespace_text_char_count": raw,
        },
    )


def _pixel_digest(image: Any) -> str:
    mode = str(image.mode)
    header = f"{image.width}x{image.height}|{mode}|".encode("ascii")
    return hashlib.sha256(header + image.tobytes()).hexdigest()


def _safe_extent(objects: Iterable[Mapping[str, Any]]) -> dict[str, float] | None:
    x0s: list[float] = []
    x1s: list[float] = []
    tops: list[float] = []
    bottoms: list[float] = []
    for item in objects:
        for key, target in (
            ("x0", x0s),
            ("x1", x1s),
            ("top", tops),
            ("bottom", bottoms),
        ):
            value = item.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
                target.append(float(value))
    if not (x0s and x1s and tops and bottoms):
        return None
    return {
        "x0_min": min(x0s),
        "x1_max": max(x1s),
        "top_min": min(tops),
        "bottom_max": max(bottoms),
    }


def _render_with_pdfium(
    source: SourceIdentity,
    pdf_path: Path,
    evidence_dir: Path,
) -> tuple[ToolProbeResult, dict[str, Any]]:
    import pypdfium2 as pdfium

    tool_version = version("pypdfium2")
    document = pdfium.PdfDocument(str(pdf_path))
    try:
        page_count = len(document)
        if source.page_index >= page_count:
            raise IndexError(f"page_index {source.page_index} outside PDF page_count {page_count}")
        page = document[source.page_index]
        try:
            width_points, height_points = (float(value) for value in page.get_size())
            scale = RENDER_DPI / PDF_POINTS_PER_INCH
            bitmap = page.render(scale=scale, rotation=0)
            try:
                image = bitmap.to_pil().convert("RGB")
                digest = _pixel_digest(image)
                evidence_dir.mkdir(parents=True, exist_ok=True)
                png_path = evidence_dir / f"tav5-page{source.page_index}-{RENDER_DPI}dpi.png"
                image.save(png_path, format="PNG", optimize=False, compress_level=9)
                png_sha256 = hashlib.sha256(png_path.read_bytes()).hexdigest()
            finally:
                close_bitmap = getattr(bitmap, "close", None)
                if callable(close_bitmap):
                    close_bitmap()
        finally:
            close_page = getattr(page, "close", None)
            if callable(close_page):
                close_page()
    finally:
        close_document = getattr(document, "close", None)
        if callable(close_document):
            close_document()

    transform = pdf_point_to_raster_transform(height_points)
    metrics = {
        "page_count": page_count,
        "page_width_points": width_points,
        "page_height_points": height_points,
        "render_dpi": RENDER_DPI,
        "raster_width_px": image.width,
        "raster_height_px": image.height,
        "raster_sha256": digest,
        "raster_digest_basis": "RGB_RAW_PIXELS_WITH_DIMENSIONS_V1",
        "png_sha256": png_sha256,
        "png_role": "EVIDENCE_RENDER_ONLY_NOT_STRUCTURAL_TRUTH",
        "transform": transform.to_mapping(),
    }
    return (
        ToolProbeResult(
            source=source,
            tool_id="pypdfium2",
            tool_version=tool_version,
            status=ToolResultStatus.PASS,
            metrics=metrics,
        ),
        {
            "width_points": width_points,
            "height_points": height_points,
            "raster_width_px": image.width,
            "raster_height_px": image.height,
            "raster_sha256": digest,
            "transform": transform,
        },
    )


def _probe_with_pdfplumber(source: SourceIdentity, pdf_path: Path) -> ToolProbeResult:
    import pdfplumber

    tool_version = version("pdfplumber")
    try:
        with pdfplumber.open(str(pdf_path)) as document:
            page = document.pages[source.page_index]
            chars = list(page.chars)
            lines = list(page.lines)
            rects = list(page.rects)
            curves = list(page.curves)
            words = list(page.extract_words() or [])
            text = page.extract_text() or ""
            objects: list[Mapping[str, Any]] = []
            objects.extend(chars)
            objects.extend(lines)
            objects.extend(rects)
            objects.extend(curves)
            metrics = {
                "page_width_points": float(page.width),
                "page_height_points": float(page.height),
                "text_char_count": len(chars),
                "non_whitespace_text_char_count": sum(
                    1 for char in chars if str(char.get("text", "")).strip()
                ),
                "extracted_text_length": len(text),
                "word_count": len(words),
                "line_count": len(lines),
                "rect_count": len(rects),
                "curve_count": len(curves),
                "coordinate_extent": _safe_extent(objects),
                "coordinate_extent_frame": "PDF_POINT_TOP_ORIGIN_PDFPLUMBER",
                "structural_truth_authorized": False,
            }
        return ToolProbeResult(
            source=source,
            tool_id="pdfplumber",
            tool_version=tool_version,
            status=ToolResultStatus.PASS,
            metrics=metrics,
        )
    except Exception as exc:
        return ToolProbeResult(
            source=source,
            tool_id="pdfplumber",
            tool_version=tool_version,
            status=ToolResultStatus.FAIL,
            metrics={"exception_type": type(exc).__name__},
            limitations=(str(exc),),
        )


def _cell_text(cell: Any) -> str:
    value = getattr(cell, "text", "")
    return value if isinstance(value, str) else str(value or "")


def _probe_with_docling_parse(source: SourceIdentity, pdf_path: Path) -> ToolProbeResult:
    tool_version = version("docling-parse")
    try:
        from docling_parse.pdf_parser import (
            ContentConfig,
            ContentLevel,
            DecodeConfig,
            DoclingPdfParser,
        )

        parser = DoclingPdfParser(loglevel="fatal")
        content_config = ContentConfig(
            char_cells_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE,
            word_cells_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE,
            line_cells_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE,
            shapes_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE,
            bitmaps_content_level=ContentLevel.SKIP,
        )
        pdf_doc = parser.load(
            path_or_stream=str(pdf_path),
            decode_config=DecodeConfig(do_sanitization=True, keep_glyphs=False),
            content_config=content_config,
        )
        if pdf_doc is None:
            raise RuntimeError("docling-parse returned no PdfDocument")
        page = pdf_doc.get_page(page_no=source.page_index + 1)
        char_cells = list(page.char_cells)
        word_cells = list(page.word_cells)
        line_cells = list(page.textline_cells)
        shapes = list(page.shapes)
        char_text = "".join(_cell_text(cell) for cell in char_cells)
        metrics = {
            "page_number_api": source.page_index + 1,
            "char_cell_count": len(char_cells),
            "word_cell_count": len(word_cells),
            "textline_cell_count": len(line_cells),
            "shape_count": len(shapes),
            "text_char_count": len(char_text),
            "non_whitespace_text_char_count": sum(1 for char in char_text if not char.isspace()),
            "layout_cells_available": bool(char_cells or word_cells or line_cells or shapes),
            "structural_truth_authorized": False,
        }
        return ToolProbeResult(
            source=source,
            tool_id="docling-parse",
            tool_version=tool_version,
            status=ToolResultStatus.PASS,
            metrics=metrics,
        )
    except Exception as exc:
        return ToolProbeResult(
            source=source,
            tool_id="docling-parse",
            tool_version=tool_version,
            status=ToolResultStatus.LIMITED,
            metrics={"exception_type": type(exc).__name__},
            limitations=(str(exc),),
        )


def _probe_with_docling(source: SourceIdentity, pdf_path: Path) -> ToolProbeResult:
    tool_version = version("docling")
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import NativePdfPipelineOptions
        from docling.document_converter import DocumentConverter, NativePdfFormatOption

        options = NativePdfPipelineOptions()
        converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: NativePdfFormatOption(pipeline_options=options)},
        )
        result = converter.convert(
            str(pdf_path),
            page_range=(source.page_index + 1, source.page_index + 1),
        )
        document = result.document
        text = document.export_to_text() or ""
        exported = document.export_to_dict()
        pages = getattr(document, "pages", {})
        metrics = {
            "pipeline": "NATIVE_PDF_NO_MODELS",
            "structured_document_available": bool(exported),
            "exported_text_length": len(text),
            "non_whitespace_text_char_count": sum(1 for char in text if not char.isspace()),
            "page_count_in_result": len(pages) if hasattr(pages, "__len__") else None,
            "structural_truth_authorized": False,
        }
        return ToolProbeResult(
            source=source,
            tool_id="docling",
            tool_version=tool_version,
            status=ToolResultStatus.PASS,
            metrics=metrics,
        )
    except Exception as exc:
        return ToolProbeResult(
            source=source,
            tool_id="docling",
            tool_version=tool_version,
            status=ToolResultStatus.LIMITED,
            metrics={"pipeline": "NATIVE_PDF_NO_MODELS", "exception_type": type(exc).__name__},
            limitations=(str(exc),),
        )


def _ocr_results(
    source: SourceIdentity,
    pdf_path: Path,
    evidence_dir: Path,
    decision: OcrTriggerDecision,
) -> tuple[ToolProbeResult, ToolProbeResult]:
    ocr_version = version("ocrmypdf")
    tesseract_version = "5.3.4"
    if not decision.triggered:
        metrics = {"trigger": decision.to_mapping()}
        return (
            ToolProbeResult(
                source=source,
                tool_id="ocrmypdf",
                tool_version=ocr_version,
                status=ToolResultStatus.NOT_TRIGGERED,
                metrics=metrics,
            ),
            ToolProbeResult(
                source=source,
                tool_id="tesseract",
                tool_version=tesseract_version,
                status=ToolResultStatus.NOT_TRIGGERED,
                metrics=metrics,
            ),
        )

    evidence_dir.mkdir(parents=True, exist_ok=True)
    output_pdf = evidence_dir / "tav5-ocr-triggered.pdf"
    command = [
        "ocrmypdf",
        "--skip-text",
        "--output-type",
        "pdf",
        "--optimize",
        "0",
        str(pdf_path),
        str(output_pdf),
    ]
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not output_pdf.exists():
        limitation = (proc.stderr or proc.stdout or "OCRmyPDF failed without diagnostic").strip()
        metrics = {
            "trigger": decision.to_mapping(),
            "returncode": proc.returncode,
            "output_created": output_pdf.exists(),
        }
        return (
            ToolProbeResult(
                source=source,
                tool_id="ocrmypdf",
                tool_version=ocr_version,
                status=ToolResultStatus.FAIL,
                metrics=metrics,
                limitations=(limitation,),
            ),
            ToolProbeResult(
                source=source,
                tool_id="tesseract",
                tool_version=tesseract_version,
                status=ToolResultStatus.FAIL,
                metrics=metrics,
                limitations=("OCR trigger path did not complete through OCRmyPDF/Tesseract",),
            ),
        )

    output_digest = hashlib.sha256(output_pdf.read_bytes()).hexdigest()
    metrics = {
        "trigger": decision.to_mapping(),
        "returncode": 0,
        "output_sha256": output_digest,
        "output_role": "OCR_DERIVATIVE_EVIDENCE_NOT_SOURCE_AUTHORITY",
    }
    return (
        ToolProbeResult(
            source=source,
            tool_id="ocrmypdf",
            tool_version=ocr_version,
            status=ToolResultStatus.PASS,
            metrics=metrics,
        ),
        ToolProbeResult(
            source=source,
            tool_id="tesseract",
            tool_version=tesseract_version,
            status=ToolResultStatus.PASS,
            metrics=metrics,
        ),
    )


def _native_text_basis(*results: ToolProbeResult) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        value = result.metrics.get("non_whitespace_text_char_count", 0)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            counts[result.tool_id] = value
    return {
        "text_char_count": sum(counts.values()),
        "non_whitespace_text_char_count": max(counts.values(), default=0),
        "per_parser_non_whitespace_counts": counts,
    }


def probe_pdf(materialized: MaterializedSource, evidence_dir: Path | str) -> PdfProbeResult:
    evidence_path = Path(evidence_dir)
    source = SourceIdentity.from_materialized(materialized)
    pdf_path = Path(materialized.destination)

    renderer_result, render = _render_with_pdfium(source, pdf_path, evidence_path)
    pdfplumber_result = _probe_with_pdfplumber(source, pdf_path)
    docling_parse_result = _probe_with_docling_parse(source, pdf_path)
    docling_result = _probe_with_docling(source, pdf_path)

    native_text_basis = _native_text_basis(
        pdfplumber_result,
        docling_parse_result,
        docling_result,
    )
    ocr_trigger = should_trigger_ocr(native_text_basis)
    ocrmypdf_result, tesseract_result = _ocr_results(
        source,
        pdf_path,
        evidence_path,
        ocr_trigger,
    )

    result = PdfProbeResult(
        source=source,
        renderer_tool_id="pypdfium2",
        renderer_version=renderer_result.tool_version,
        render_dpi=RENDER_DPI,
        page_width_points=render["width_points"],
        page_height_points=render["height_points"],
        raster_width_px=render["raster_width_px"],
        raster_height_px=render["raster_height_px"],
        raster_sha256=render["raster_sha256"],
        render_transform=render["transform"],
        ocr_trigger=ocr_trigger,
        tool_results=(
            renderer_result,
            pdfplumber_result,
            docling_parse_result,
            docling_result,
            ocrmypdf_result,
            tesseract_result,
        ),
    )

    evidence_path.mkdir(parents=True, exist_ok=True)
    record_path = evidence_path / "pdf-probe-result.json"
    record_path.write_text(
        json.dumps(result.to_mapping(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result
