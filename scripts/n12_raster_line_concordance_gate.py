#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import tempfile
from dataclasses import asdict
from pathlib import Path

import numpy as np
from PIL import Image

from n12_vector_concordance_gate import SOURCES, Segment, acquire_source, classify_segment, sha256


def normalize_image(img: Image.Image, max_dimension: int) -> Image.Image:
    img = img.convert("L")
    scale = min(1.0, max_dimension / max(img.size))
    size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    if size != img.size:
        img = img.resize(size, Image.Resampling.LANCZOS)
    return img


def render_pymupdf(pdf: Path, max_dimension: int) -> Image.Image:
    import pymupdf

    doc = pymupdf.open(pdf)
    page = doc[0]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(1, 1), alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return normalize_image(img, max_dimension)


def render_docling(pdf: Path, max_dimension: int) -> Image.Image:
    from docling_parse.pdf_parser import ContentConfig, ContentLevel, DecodeConfig, DoclingPdfParser

    parser = DoclingPdfParser(loglevel="fatal")
    doc = parser.load(
        path_or_stream=str(pdf),
        decode_config=DecodeConfig(do_sanitization=True, keep_glyphs=False),
        content_config=ContentConfig(
            char_cells_content_level=ContentLevel.SKIP,
            word_cells_content_level=ContentLevel.SKIP,
            line_cells_content_level=ContentLevel.SKIP,
            shapes_content_level=ContentLevel.SKIP,
            bitmaps_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE,
            include_bitmap_bytes=True,
        ),
    )
    page = doc.get_page(1)
    img = page.render_as_image()
    return normalize_image(img, max_dimension)


def align_pair(a: Image.Image, b: Image.Image) -> tuple[Image.Image, Image.Image]:
    if a.size == b.size:
        return a, b
    return a, b.resize(a.size, Image.Resampling.LANCZOS)


def renderer_difference(a: Image.Image, b: Image.Image) -> dict:
    a, b = align_pair(a, b)
    aa = np.asarray(a, dtype=np.float32)
    bb = np.asarray(b, dtype=np.float32)
    diff = np.abs(aa - bb)
    return {
        "width_px": a.width,
        "height_px": a.height,
        "mean_abs_difference_0_255": round(float(np.mean(diff)), 4),
        "p95_abs_difference_0_255": round(float(np.percentile(diff, 95)), 4),
    }


def detect_lsd(img: Image.Image, min_length_px: float, axis_tolerance_deg: float) -> list[Segment]:
    import cv2

    arr = np.asarray(img, dtype=np.uint8)
    detector = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    detected = detector.detect(arr)[0]
    out: list[Segment] = []
    if detected is None:
        return out
    for raw in detected[:, 0, :]:
        x1, y1, x2, y2 = map(float, raw)
        seg = classify_segment("opencv_lsd", 1, (x1, y1), (x2, y2), min_length_px, axis_tolerance_deg)
        if seg:
            out.append(seg)
    return out


def detect_hough(img: Image.Image, min_length_px: int, axis_tolerance_deg: float) -> list[Segment]:
    from skimage.feature import canny
    from skimage.transform import probabilistic_hough_line

    arr = np.asarray(img, dtype=np.float32) / 255.0
    edges = canny(arr, sigma=1.5)
    lines = probabilistic_hough_line(
        edges,
        threshold=10,
        line_length=min_length_px,
        line_gap=max(3, min_length_px // 20),
        rng=12,
    )
    out: list[Segment] = []
    for p0, p1 in lines:
        seg = classify_segment("skimage_hough", 1, (float(p0[0]), float(p0[1])), (float(p1[0]), float(p1[1])), float(min_length_px), axis_tolerance_deg)
        if seg:
            out.append(seg)
    return out


def axis_coordinate(seg: Segment) -> float:
    return (seg.y1 + seg.y2) / 2.0 if seg.orientation == "H" else (seg.x1 + seg.x2) / 2.0


def interval(seg: Segment) -> tuple[float, float]:
    return (min(seg.x1, seg.x2), max(seg.x1, seg.x2)) if seg.orientation == "H" else (min(seg.y1, seg.y2), max(seg.y1, seg.y2))


def overlap_ratio(a: Segment, b: Segment) -> float:
    a0, a1 = interval(a)
    b0, b1 = interval(b)
    overlap = max(0.0, min(a1, b1) - max(a0, b0))
    denom = max(1e-9, min(a1 - a0, b1 - b0))
    return overlap / denom


def match_lines(a: list[Segment], b: list[Segment], coordinate_tolerance_px: float, min_overlap_ratio: float) -> tuple[list[dict], set[int], set[int]]:
    candidates: list[tuple[float, int, int, float, float]] = []
    for i, sa in enumerate(a):
        for j, sb in enumerate(b):
            if sa.orientation != sb.orientation:
                continue
            coord = abs(axis_coordinate(sa) - axis_coordinate(sb))
            overlap = overlap_ratio(sa, sb)
            if coord <= coordinate_tolerance_px and overlap >= min_overlap_ratio:
                score = coord + (1.0 - overlap) * coordinate_tolerance_px
                candidates.append((score, i, j, coord, overlap))
    candidates.sort()
    used_a: set[int] = set()
    used_b: set[int] = set()
    matches: list[dict] = []
    for _, i, j, coord, overlap in candidates:
        if i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        matches.append({"lsd_index": i, "hough_index": j, "coordinate_delta_px": round(coord, 4), "overlap_ratio": round(overlap, 6)})
    return matches, used_a, used_b


def write_segments(path: Path, rows: list[Segment]) -> None:
    fields = ["engine", "page", "orientation", "x1", "y1", "x2", "y2", "length"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_matches(path: Path, matches: list[dict], a: list[Segment], b: list[Segment]) -> None:
    fields = ["lsd_index", "hough_index", "coordinate_delta_px", "overlap_ratio", "orientation", "lsd_length", "hough_length"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for m in matches:
            sa, sb = a[m["lsd_index"]], b[m["hough_index"]]
            writer.writerow({**m, "orientation": sa.orientation, "lsd_length": round(sa.length, 4), "hough_length": round(sb.length, 4)})


def self_test() -> None:
    a = [Segment("opencv_lsd", 1, "H", 10, 100, 300, 100, 290), Segment("opencv_lsd", 1, "V", 200, 20, 200, 350, 330)]
    b = [Segment("skimage_hough", 1, "H", 20, 102, 290, 102, 270), Segment("skimage_hough", 1, "V", 198, 30, 198, 340, 310)]
    matches, ua, ub = match_lines(a, b, 4.0, 0.8)
    assert len(matches) == len(ua) == len(ub) == 2
    print("RASTER_SELF_TEST_PASS")


def run(args: argparse.Namespace) -> int:
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    receipts = []
    overall_ok = True
    with tempfile.TemporaryDirectory(prefix="n12-raster-lines-") as td:
        temp = Path(td)
        for source_id, spec in SOURCES.items():
            pdf = temp / f"{source_id}.pdf"
            acquire_source(args.archive_ref, source_id, pdf)
            source_ok = sha256(pdf) == spec["sha256"]
            pymu_img = render_pymupdf(pdf, args.max_dimension_px)
            docl_img = render_docling(pdf, args.max_dimension_px)
            pymu_img, docl_img = align_pair(pymu_img, docl_img)
            render_diag = renderer_difference(pymu_img, docl_img)
            min_length = max(args.min_length_px, round(max(pymu_img.size) * args.min_length_fraction))
            lsd = detect_lsd(pymu_img, float(min_length), args.axis_tolerance_deg)
            hough = detect_hough(docl_img, int(min_length), args.axis_tolerance_deg)
            matches, used_lsd, used_hough = match_lines(lsd, hough, args.coordinate_tolerance_px, args.min_overlap_ratio)
            target = out_root / source_id
            target.mkdir(parents=True, exist_ok=True)
            write_segments(target / "opencv_lsd_segments.csv", lsd)
            write_segments(target / "skimage_hough_segments.csv", hough)
            write_matches(target / "matches.csv", matches, lsd, hough)
            lsd_ratio = len(matches) / len(lsd) if lsd else 0.0
            hough_ratio = len(matches) / len(hough) if hough else 0.0
            detector_ok = bool(lsd) and bool(hough)
            gate = "RASTER_CANDIDATE_REVIEW" if source_ok and detector_ok else "FAIL"
            overall_ok = overall_ok and gate != "FAIL"
            receipt = {
                "schema_version": "1.0",
                "experiment": "INDEPENDENT_RASTER_LINE_CONCORDANCE",
                "source_id": source_id,
                "level": spec["level"],
                "source_integrity": "PASS" if source_ok else "FAIL",
                "renderers": {"A": "PyMuPDF", "B": "Docling Parse"},
                "detectors": {"A": "OpenCV LSD", "B": "scikit-image probabilistic Hough"},
                "renderer_difference": render_diag,
                "parameters": {"max_dimension_px": args.max_dimension_px, "min_length_px_effective": min_length, "axis_tolerance_deg": args.axis_tolerance_deg, "coordinate_tolerance_px": args.coordinate_tolerance_px, "min_overlap_ratio": args.min_overlap_ratio},
                "counts": {"opencv_lsd_axis_segments": len(lsd), "skimage_hough_axis_segments": len(hough), "matched_pairs": len(matches), "opencv_lsd_unmatched": len(lsd) - len(used_lsd), "skimage_hough_unmatched": len(hough) - len(used_hough)},
                "concordance": {"matched_over_opencv_lsd": round(lsd_ratio, 6), "matched_over_skimage_hough": round(hough_ratio, 6)},
                "gate": gate,
                "epistemic_effect": "NONE",
                "promotion_prohibited": True,
                "note": "Candidate geometry only. Agreement between independent raster render/detection paths is evidence for review, never automatic DOC/MIS promotion.",
            }
            (target / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            receipts.append(receipt)
    overall_gate = "RASTER_DIAGNOSTIC_COMPLETE" if overall_ok else "FAIL"
    (out_root / "batch_receipt.json").write_text(json.dumps({"overall_gate": overall_gate, "sources": receipts, "epistemic_effect": "NONE"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall_gate": overall_gate, "sources": [{"source_id": r["source_id"], "renderer_difference": r["renderer_difference"], "counts": r["counts"], "concordance": r["concordance"], "gate": r["gate"]} for r in receipts]}, indent=2))
    return 0 if overall_ok else 2


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare long H/V line candidates from independent raster renderer+detector paths.")
    p.add_argument("--archive-ref", default="origin/archive/originali-alta-risoluzione")
    p.add_argument("--out-dir", default="analysis/raster_line_concordance")
    p.add_argument("--max-dimension-px", type=int, default=2200)
    p.add_argument("--min-length-px", type=int, default=120)
    p.add_argument("--min-length-fraction", type=float, default=0.05)
    p.add_argument("--axis-tolerance-deg", type=float, default=1.0)
    p.add_argument("--coordinate-tolerance-px", type=float, default=8.0)
    p.add_argument("--min-overlap-ratio", type=float, default=0.65)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    ns = parse_args()
    if ns.self_test:
        self_test()
        raise SystemExit(0)
    raise SystemExit(run(ns))
