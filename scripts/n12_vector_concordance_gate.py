#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SOURCES = {
    "TAV-03S": {
        "path": "archive/documentazione_originaria/tavola3-2.pdf",
        "sha256": "c28612f58a734d5859a0d3485b28e370b31b292d0a32171832db41e0052fa8d5",
        "level": "G2",
    },
    "TAV-04S": {
        "path": "archive/documentazione_originaria/tavola4-2.pdf",
        "sha256": "2b878bcefde54ff2b42bafa2a4fdc8a8420bd71514a7e6966a864f009ade685e",
        "level": "G3",
    },
    "TAV-05S": {
        "path": "archive/documentazione_originaria/tavola 5.pdf",
        "sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
        "level": "G4",
    },
    "TAV-06S": {
        "path": "archive/documentazione_originaria/tavola 6-1.pdf",
        "sha256": "ca454c844049cab12af6eeaaf5167f934a9be0e2f72d34dd392d4db0bf3d341d",
        "level": "G5",
    },
}


@dataclass(frozen=True)
class Segment:
    engine: str
    page: int
    orientation: str
    x1: float
    y1: float
    x2: float
    y2: float
    length: float

    @property
    def midpoint(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify_segment(
    engine: str,
    page: int,
    a: tuple[float, float],
    b: tuple[float, float],
    min_length: float,
    axis_tolerance_deg: float,
) -> Segment | None:
    x1, y1 = a
    x2, y2 = b
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < min_length:
        return None
    angle = abs(math.degrees(math.atan2(dy, dx))) % 180.0
    dist_h = min(angle, abs(180.0 - angle))
    dist_v = abs(90.0 - angle)
    if dist_h <= axis_tolerance_deg:
        orientation = "H"
    elif dist_v <= axis_tolerance_deg:
        orientation = "V"
    else:
        return None
    if (x2, y2) < (x1, y1):
        x1, y1, x2, y2 = x2, y2, x1, y1
    return Segment(engine, page, orientation, x1, y1, x2, y2, length)


def rect_edges(rect) -> Iterable[tuple[tuple[float, float], tuple[float, float]]]:
    p = [
        (float(rect.x0), float(rect.y0)),
        (float(rect.x1), float(rect.y0)),
        (float(rect.x1), float(rect.y1)),
        (float(rect.x0), float(rect.y1)),
    ]
    for i in range(4):
        yield p[i], p[(i + 1) % 4]


def extract_pymupdf(pdf: Path, min_length: float, axis_tolerance_deg: float) -> list[Segment]:
    import pymupdf

    out: list[Segment] = []
    doc = pymupdf.open(pdf)
    for page_index, page in enumerate(doc, start=1):
        for drawing in page.get_drawings():
            for item in drawing.get("items", []):
                op = item[0]
                candidates: list[tuple[tuple[float, float], tuple[float, float]]] = []
                if op == "l":
                    candidates.append(((float(item[1].x), float(item[1].y)), (float(item[2].x), float(item[2].y))))
                elif op == "re":
                    candidates.extend(rect_edges(item[1]))
                elif op == "qu":
                    q = item[1]
                    pts = [(float(q.ul.x), float(q.ul.y)), (float(q.ur.x), float(q.ur.y)), (float(q.lr.x), float(q.lr.y)), (float(q.ll.x), float(q.ll.y))]
                    candidates.extend((pts[i], pts[(i + 1) % 4]) for i in range(4))
                for a, b in candidates:
                    seg = classify_segment("pymupdf", page_index, a, b, min_length, axis_tolerance_deg)
                    if seg:
                        out.append(seg)
    doc.close()
    return out


def extract_docling(pdf: Path, min_length: float, axis_tolerance_deg: float) -> list[Segment]:
    from docling_parse.pdf_parser import ContentConfig, ContentLevel, DecodeConfig, DoclingPdfParser

    parser = DoclingPdfParser(loglevel="fatal")
    doc = parser.load(
        path_or_stream=str(pdf),
        decode_config=DecodeConfig(do_sanitization=True, keep_glyphs=False),
        content_config=ContentConfig(
            char_cells_content_level=ContentLevel.SKIP,
            word_cells_content_level=ContentLevel.SKIP,
            line_cells_content_level=ContentLevel.SKIP,
            shapes_content_level=ContentLevel.COMPUTE_AND_MATERIALIZE,
            bitmaps_content_level=ContentLevel.SKIP,
        ),
    )
    out: list[Segment] = []
    for page_no, page in doc.iterate_pages():
        height = float(page.dimension.height)
        for shape in page.shapes:
            pts = [(float(p.x), height - float(p.y)) for p in shape.points]
            for a, b in zip(pts, pts[1:]):
                seg = classify_segment("docling", int(page_no), a, b, min_length, axis_tolerance_deg)
                if seg:
                    out.append(seg)
    return out


def endpoint_distance(a: Segment, b: Segment) -> float:
    direct = max(math.hypot(a.x1 - b.x1, a.y1 - b.y1), math.hypot(a.x2 - b.x2, a.y2 - b.y2))
    reverse = max(math.hypot(a.x1 - b.x2, a.y1 - b.y2), math.hypot(a.x2 - b.x1, a.y2 - b.y1))
    return min(direct, reverse)


def match_segments(primary: list[Segment], secondary: list[Segment], tolerance_pt: float) -> tuple[list[dict], set[int], set[int]]:
    candidates: list[tuple[float, int, int]] = []
    for i, a in enumerate(primary):
        for j, b in enumerate(secondary):
            if a.page != b.page or a.orientation != b.orientation:
                continue
            d = endpoint_distance(a, b)
            if d <= tolerance_pt:
                candidates.append((d, i, j))
    candidates.sort()
    used_a: set[int] = set()
    used_b: set[int] = set()
    matches: list[dict] = []
    for d, i, j in candidates:
        if i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        matches.append({"distance_pt": round(d, 4), "pymupdf_index": i, "docling_index": j})
    return matches, used_a, used_b


def write_segments(path: Path, segments: list[Segment]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(asdict(segments[0]).keys()) if segments else ["engine", "page", "orientation", "x1", "y1", "x2", "y2", "length"])
        writer.writeheader()
        for seg in segments:
            writer.writerow(asdict(seg))


def write_matches(path: Path, matches: list[dict], a: list[Segment], b: list[Segment]) -> None:
    fields = ["distance_pt", "pymupdf_index", "docling_index", "page", "orientation", "pymupdf_length", "docling_length"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for m in matches:
            pa, db = a[m["pymupdf_index"]], b[m["docling_index"]]
            writer.writerow({**m, "page": pa.page, "orientation": pa.orientation, "pymupdf_length": round(pa.length, 4), "docling_length": round(db.length, 4)})


def acquire_source(archive_ref: str, source_id: str, target: Path) -> None:
    spec = SOURCES[source_id]
    with target.open("wb") as fh:
        subprocess.run(["git", "show", f"{archive_ref}:{spec['path']}"], check=True, stdout=fh)


def self_test() -> None:
    a = classify_segment("a", 1, (0, 0), (100, 0.2), 10, 1)
    b = classify_segment("b", 1, (0.3, 0.1), (100.2, 0.0), 10, 1)
    assert a and b and a.orientation == b.orientation == "H"
    matches, ua, ub = match_segments([a], [b], 1.0)
    assert len(matches) == len(ua) == len(ub) == 1
    assert classify_segment("a", 1, (0, 0), (5, 5), 10, 1) is None
    print("SELF_TEST_PASS")


def run(args: argparse.Namespace) -> int:
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    batch_summary = []
    overall_ok = True
    with tempfile.TemporaryDirectory(prefix="n12-vector-") as td:
        temp = Path(td)
        for source_id, spec in SOURCES.items():
            pdf = temp / f"{source_id}.pdf"
            acquire_source(args.archive_ref, source_id, pdf)
            actual_sha = sha256(pdf)
            source_ok = actual_sha == spec["sha256"]
            target = out_root / source_id
            target.mkdir(parents=True, exist_ok=True)
            pymu = extract_pymupdf(pdf, args.min_length_pt, args.axis_tolerance_deg)
            docl = extract_docling(pdf, args.min_length_pt, args.axis_tolerance_deg)
            matches, used_p, used_d = match_segments(pymu, docl, args.match_tolerance_pt)
            p_ratio = len(matches) / len(pymu) if pymu else 0.0
            d_ratio = len(matches) / len(docl) if docl else 0.0
            parser_ok = bool(pymu) and bool(docl)
            measured_gate = source_ok and parser_ok
            overall_ok = overall_ok and measured_gate
            write_segments(target / "pymupdf_segments.csv", pymu)
            write_segments(target / "docling_segments.csv", docl)
            write_matches(target / "matches.csv", matches, pymu, docl)
            receipt = {
                "schema_version": "1.0",
                "experiment": "PYMUPDF_DOCLING_VECTOR_CONCORDANCE",
                "source_id": source_id,
                "level": spec["level"],
                "source_path": spec["path"],
                "expected_sha256": spec["sha256"],
                "actual_sha256": actual_sha,
                "source_integrity": "PASS" if source_ok else "FAIL",
                "parameters": {
                    "min_length_pt": args.min_length_pt,
                    "axis_tolerance_deg": args.axis_tolerance_deg,
                    "match_tolerance_pt": args.match_tolerance_pt,
                },
                "counts": {
                    "pymupdf_axis_segments": len(pymu),
                    "docling_axis_segments": len(docl),
                    "matched_pairs": len(matches),
                    "pymupdf_unmatched": len(pymu) - len(used_p),
                    "docling_unmatched": len(docl) - len(used_d),
                },
                "concordance": {
                    "matched_over_pymupdf": round(p_ratio, 6),
                    "matched_over_docling": round(d_ratio, 6),
                },
                "gate": "MEASURED_REVIEW" if measured_gate else "FAIL",
                "epistemic_effect": "NONE",
                "promotion_prohibited": True,
                "note": "Experimental parser-concordance evidence only. No DOC/MIS promotion and no canonical geometry mutation.",
            }
            (target / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            batch_summary.append(receipt)
    (out_root / "batch_receipt.json").write_text(json.dumps({"sources": batch_summary, "overall_gate": "MEASURED_REVIEW" if overall_ok else "FAIL", "epistemic_effect": "NONE"}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall_gate": "MEASURED_REVIEW" if overall_ok else "FAIL", "sources": [{"source_id": x["source_id"], "counts": x["counts"], "concordance": x["concordance"]} for x in batch_summary]}, indent=2))
    return 0 if overall_ok else 2


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare axis-aligned vector segments independently extracted by PyMuPDF and Docling Parse.")
    p.add_argument("--archive-ref", default="origin/archive/originali-alta-risoluzione")
    p.add_argument("--out-dir", default="analysis/vector_concordance")
    p.add_argument("--min-length-pt", type=float, default=8.0)
    p.add_argument("--axis-tolerance-deg", type=float, default=0.75)
    p.add_argument("--match-tolerance-pt", type=float, default=1.5)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    ns = parse_args()
    if ns.self_test:
        self_test()
        raise SystemExit(0)
    raise SystemExit(run(ns))
