#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Segment:
    x1: float
    y1: float
    x2: float
    y2: float
    source: str
    kind: str

    @property
    def length(self) -> float:
        return math.hypot(self.x2 - self.x1, self.y2 - self.y1)

    @property
    def angle_deg(self) -> float:
        return math.degrees(math.atan2(self.y2 - self.y1, self.x2 - self.x1)) % 180.0

    def flipped_y(self, page_height: float) -> "Segment":
        return Segment(
            self.x1,
            page_height - self.y1,
            self.x2,
            page_height - self.y2,
            self.source,
            self.kind,
        )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _point_xy(p: Any) -> tuple[float, float]:
    if hasattr(p, "x") and hasattr(p, "y"):
        return float(p.x), float(p.y)
    if isinstance(p, (list, tuple)) and len(p) >= 2:
        return float(p[0]), float(p[1])
    raise TypeError(f"Unsupported point: {p!r}")


def _append_segment(
    out: list[Segment], p1: Any, p2: Any, source: str, kind: str, min_len: float
) -> None:
    x1, y1 = _point_xy(p1)
    x2, y2 = _point_xy(p2)
    segment = Segment(x1, y1, x2, y2, source, kind)
    if segment.length >= min_len:
        out.append(segment)


def extract_pymupdf(
    pdf: Path, page_no: int, min_len: float
) -> tuple[list[Segment], float, float, str]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is not installed") from exc

    doc = fitz.open(pdf)
    try:
        page = doc[page_no - 1]
        rect = page.rect
        out: list[Segment] = []
        for drawing in page.get_drawings():
            for item in drawing.get("items", []):
                op = item[0]
                if op == "l":
                    _append_segment(out, item[1], item[2], "PyMuPDF", "line", min_len)
                elif op == "re":
                    r = item[1]
                    pts = [
                        (r.x0, r.y0),
                        (r.x1, r.y0),
                        (r.x1, r.y1),
                        (r.x0, r.y1),
                    ]
                    for a, b in zip(pts, pts[1:] + pts[:1]):
                        _append_segment(
                            out, a, b, "PyMuPDF", "rectangle_edge", min_len
                        )
                elif op == "qu":
                    q = item[1]
                    pts = [q.ul, q.ur, q.lr, q.ll]
                    for a, b in zip(pts, pts[1:] + pts[:1]):
                        _append_segment(out, a, b, "PyMuPDF", "quad_edge", min_len)
        return (
            out,
            float(rect.width),
            float(rect.height),
            getattr(fitz, "VersionBind", "unknown"),
        )
    finally:
        doc.close()


def extract_docling(
    pdf: Path, page_no: int, min_len: float
) -> tuple[list[Segment], float, float, str]:
    try:
        import importlib.metadata
        from docling_parse.pdf_parser import (
            ContentConfig,
            ContentLevel,
            DoclingPdfParser,
        )
    except ImportError as exc:
        raise RuntimeError("docling-parse is not installed") from exc

    parser = DoclingPdfParser(loglevel="fatal")
    doc = parser.load(pdf, lazy=True)
    try:
        cfg = ContentConfig(
            char_cells_content_level=ContentLevel.SKIP,
            word_cells_content_level=ContentLevel.SKIP,
            line_cells_content_level=ContentLevel.SKIP,
            shapes_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE,
            bitmaps_content_level=ContentLevel.SKIP,
            include_bitmap_bytes=False,
        )
        page = doc.get_page(page_no, content_config=cfg)
        out: list[Segment] = []
        for shape in page.shapes:
            pts = list(shape.points)
            for p1, p2 in zip(pts, pts[1:]):
                _append_segment(
                    out, p1, p2, "DoclingParse", "shape_edge", min_len
                )
        page_rect = page.dimension.rect
        return (
            out,
            float(page_rect.width),
            float(page_rect.height),
            importlib.metadata.version("docling-parse"),
        )
    finally:
        doc.unload()


def angle_delta(a: float, b: float) -> float:
    delta = abs(a - b) % 180.0
    return min(delta, 180.0 - delta)


def endpoint_error(a: Segment, b: Segment) -> float:
    direct = max(
        math.hypot(a.x1 - b.x1, a.y1 - b.y1),
        math.hypot(a.x2 - b.x2, a.y2 - b.y2),
    )
    reverse = max(
        math.hypot(a.x1 - b.x2, a.y1 - b.y2),
        math.hypot(a.x2 - b.x1, a.y2 - b.y1),
    )
    return min(direct, reverse)


def relative_length_error(a: Segment, b: Segment) -> float:
    denominator = max(a.length, b.length, 1e-9)
    return abs(a.length - b.length) / denominator


def match_segments(
    reference: list[Segment], candidate: list[Segment], tol: dict[str, float]
) -> dict[str, Any]:
    unmatched = set(range(len(candidate)))
    matches: list[dict[str, Any]] = []
    for i, ref in enumerate(reference):
        best: tuple[float, int, float, float] | None = None
        for j in unmatched:
            cand = candidate[j]
            angle_error = angle_delta(ref.angle_deg, cand.angle_deg)
            length_error = relative_length_error(ref, cand)
            end_error = endpoint_error(ref, cand)
            if (
                angle_error > tol["angle_difference_deg"]
                or length_error > tol["relative_length_difference"]
                or end_error > tol["endpoint_distance_pt"]
            ):
                continue
            score = end_error + angle_error * 0.1 + length_error * max(ref.length, 1.0)
            if best is None or score < best[0]:
                best = (score, j, end_error, length_error)
        if best is not None:
            _, j, end_error, length_error = best
            unmatched.remove(j)
            matches.append(
                {
                    "reference_index": i,
                    "candidate_index": j,
                    "endpoint_error_pt": round(end_error, 6),
                    "angle_error_deg": round(
                        angle_delta(ref.angle_deg, candidate[j].angle_deg), 6
                    ),
                    "relative_length_error": round(length_error, 8),
                }
            )

    denominator = max(len(reference), len(candidate), 1)
    endpoint_errors = [m["endpoint_error_pt"] for m in matches]
    return {
        "matches": matches,
        "match_ratio": len(matches) / denominator,
        "reference_count": len(reference),
        "candidate_count": len(candidate),
        "unmatched_reference": len(reference) - len(matches),
        "unmatched_candidate": len(candidate) - len(matches),
        "median_endpoint_error_pt": (
            statistics.median(endpoint_errors) if endpoint_errors else None
        ),
        "max_endpoint_error_pt": max(endpoint_errors, default=None),
    }


def choose_coordinate_mapping(
    py: list[Segment], dp: list[Segment], page_height: float, tol: dict[str, float]
) -> tuple[str, list[Segment], dict[str, Any]]:
    direct = match_segments(py, dp, tol)
    flipped_dp = [segment.flipped_y(page_height) for segment in dp]
    flipped = match_segments(py, flipped_dp, tol)
    direct_key = (
        direct["match_ratio"],
        -(direct["median_endpoint_error_pt"] or 1e12),
    )
    flipped_key = (
        flipped["match_ratio"],
        -(flipped["median_endpoint_error_pt"] or 1e12),
    )
    if flipped_key > direct_key:
        return "DOCLING_VERTICAL_FLIP", flipped_dp, flipped
    return "DIRECT", dp, direct


def intersection(
    a: Segment, b: Segment, eps: float = 1e-9
) -> tuple[float, float] | None:
    x1, y1, x2, y2 = a.x1, a.y1, a.x2, a.y2
    x3, y3, x4, y4 = b.x1, b.y1, b.x2, b.y2
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denominator) < eps:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denominator
    if -eps <= t <= 1 + eps and -eps <= u <= 1 + eps:
        return x1 + t * (x2 - x1), y1 + t * (y2 - y1)
    return None


def unique_intersections(
    segments: list[Segment], merge_tol: float
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for i, first in enumerate(segments):
        for second in segments[i + 1 :]:
            point = intersection(first, second)
            if point is None:
                continue
            if not any(
                math.hypot(point[0] - known[0], point[1] - known[1]) <= merge_tol
                for known in points
            ):
                points.append(point)
    return points


def match_points(
    reference: list[tuple[float, float]],
    candidate: list[tuple[float, float]],
    tolerance: float,
) -> dict[str, Any]:
    unused = set(range(len(candidate)))
    errors: list[float] = []
    for point in reference:
        best: tuple[float, int] | None = None
        for j in unused:
            error = math.hypot(
                point[0] - candidate[j][0], point[1] - candidate[j][1]
            )
            if error <= tolerance and (best is None or error < best[0]):
                best = (error, j)
        if best is not None:
            errors.append(best[0])
            unused.remove(best[1])
    denominator = max(len(reference), len(candidate), 1)
    return {
        "reference_count": len(reference),
        "candidate_count": len(candidate),
        "matches": len(errors),
        "match_ratio": len(errors) / denominator,
        "median_error_pt": statistics.median(errors) if errors else None,
        "max_error_pt": max(errors, default=None),
    }


def classify_outcome(
    segment_ratio: float, intersection_ratio: float, tol: dict[str, float]
) -> str:
    ratio = min(segment_ratio, intersection_ratio) if intersection_ratio > 0 else segment_ratio
    if ratio >= tol["minimum_match_ratio_for_agree"]:
        return "AGREE"
    if ratio >= tol["minimum_match_ratio_for_partial"]:
        return "PARTIAL"
    return "DISAGREE"


def run(pdf: Path, page_no: int, contract_path: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    tol = contract["tolerance_profile"]
    source_hash = sha256(pdf)

    try:
        py, py_width, py_height, py_version = extract_pymupdf(
            pdf, page_no, tol["minimum_line_length_pt"]
        )
    except RuntimeError as exc:
        return {
            "outcome": "MISSING_PYMUPDF",
            "error": str(exc),
            "pdf_sha256": source_hash,
            "page": page_no,
        }

    try:
        dp, dp_width, dp_height, dp_version = extract_docling(
            pdf, page_no, tol["minimum_line_length_pt"]
        )
    except RuntimeError as exc:
        return {
            "outcome": "MISSING_DOCLING",
            "error": str(exc),
            "pdf_sha256": source_hash,
            "page": page_no,
            "pymupdf_version": py_version,
        }

    if (
        abs(py_width - dp_width) > tol["endpoint_distance_pt"]
        or abs(py_height - dp_height) > tol["endpoint_distance_pt"]
    ):
        return {
            "outcome": "UNCOMPARABLE",
            "reason": "page dimensions differ beyond endpoint tolerance; no scale correction is permitted",
            "pdf_sha256": source_hash,
            "page": page_no,
            "pymupdf_page_size_pt": [py_width, py_height],
            "docling_page_size_pt": [dp_width, dp_height],
        }

    mapping, dp_mapped, segment_result = choose_coordinate_mapping(
        py, dp, py_height, tol
    )
    py_intersections = unique_intersections(
        py, tol["intersection_distance_pt"]
    )
    dp_intersections = unique_intersections(
        dp_mapped, tol["intersection_distance_pt"]
    )
    intersection_result = match_points(
        py_intersections, dp_intersections, tol["intersection_distance_pt"]
    )
    decision = classify_outcome(
        segment_result["match_ratio"], intersection_result["match_ratio"], tol
    )

    return {
        "schema_version": "1.0",
        "gate": "CEW_DUAL_VECTOR_AGREEMENT_v1",
        "authority_state": "DERIVED_REVIEW_EVIDENCE",
        "canonical_mutation": False,
        "outcome": decision,
        "pdf": str(pdf),
        "pdf_sha256": source_hash,
        "page": page_no,
        "page_size_pt": [py_width, py_height],
        "coordinate_mapping": mapping,
        "extractors": {
            "pymupdf": py_version,
            "docling_parse": dp_version,
        },
        "tolerance_profile": tol,
        "segments": segment_result,
        "intersections": intersection_result,
        "guards": [
            "This result cannot promote DOC or MIS.",
            "This result cannot mutate frozen M0-G geometry.",
            "Disagreement requires claim-scoped source review, not automatic geometry replacement.",
        ],
    }


def self_test() -> None:
    tol = {
        "endpoint_distance_pt": 0.75,
        "angle_difference_deg": 0.5,
        "relative_length_difference": 0.005,
        "intersection_distance_pt": 1.0,
        "minimum_match_ratio_for_agree": 0.95,
        "minimum_match_ratio_for_partial": 0.80,
    }
    reference = [
        Segment(0, 0, 10, 0, "A", "line"),
        Segment(5, -5, 5, 5, "A", "line"),
    ]
    candidate = [
        Segment(0.1, 0.1, 10.1, 0.1, "B", "line"),
        Segment(5.1, -5, 5.1, 5, "B", "line"),
    ]
    segment_result = match_segments(reference, candidate, tol)
    assert segment_result["match_ratio"] == 1.0
    ref_intersections = unique_intersections(reference, 0.1)
    cand_intersections = unique_intersections(candidate, 0.1)
    intersection_result = match_points(ref_intersections, cand_intersections, 1.0)
    assert intersection_result["match_ratio"] == 1.0
    assert (
        classify_outcome(
            segment_result["match_ratio"], intersection_result["match_ratio"], tol
        )
        == "AGREE"
    )
    print("SELF_TEST: PASS")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Claim-scoped PyMuPDF ↔ Docling Parse vector concordance check."
    )
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("automation/CEW_DUAL_VECTOR_AGREEMENT_CONTRACT_v1.json"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.pdf or not args.output:
        parser.error("--pdf and --output are required unless --self-test is used")

    result = run(args.pdf, args.page, args.contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f'{result.get("outcome")}: {args.output}')


if __name__ == "__main__":
    main()
