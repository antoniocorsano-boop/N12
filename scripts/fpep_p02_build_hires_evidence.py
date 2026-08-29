#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
P01_IDENTITY = ROOT / "analysis" / "fpep" / "FPEP_SOURCE_IDENTITY_v1.json"
MANIFEST = ROOT / "analysis" / "fpep" / "FPEP_HIRES_EVIDENCE_MANIFEST_v1.json"
EVIDENCE_ROOT = ROOT / "analysis" / "fpep" / "hires" / "TAV01S"
RESULT = ROOT / "automation" / "inbox" / "N12_FOUNDATION_AGENT_RESULT.json"
PIPELINE_ID = "N12_FPEP_FOUNDATION_PRIMARY_EVIDENCE_PIPELINE"
WORK_ITEM_ID = "FPEP-P02-HIRES-EVIDENCE"
AGENT_ROLE = "HIRES_EVIDENCE_BUILDER"
SOURCE_REF = "archive/originali-alta-risoluzione:archive/documentazione_originaria/tavola1-2.pdf"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=capture)


def poppler_version() -> str:
    proc = subprocess.run(["pdftoppm", "-v"], text=True, capture_output=True)
    text = (proc.stdout + proc.stderr).strip().splitlines()
    return text[0] if text else "pdftoppm-version-unavailable"


def pdf_page_count(pdf: Path) -> int:
    proc = run(["pdfinfo", str(pdf)], capture=True)
    for line in proc.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise RuntimeError("pdfinfo did not report a page count")


def render_page(pdf: Path, page: int, dpi: int, out_base: Path) -> Path:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    run([
        "pdftoppm", "-f", str(page), "-l", str(page), "-singlefile",
        "-r", str(dpi), "-jpeg", "-jpegopt", "quality=94,progressive=n,optimize=y",
        str(pdf), str(out_base),
    ])
    out = out_base.with_suffix(".jpg")
    if not out.exists():
        raise RuntimeError(f"pdftoppm did not create {out}")
    return out


def expanded_grid_rects(width: int, height: int, cols: int, rows: int, overlap_fraction: float) -> list[dict[str, int]]:
    rects: list[dict[str, int]] = []
    cell_w = width / cols
    cell_h = height / rows
    pad_x = cell_w * overlap_fraction / 2.0
    pad_y = cell_h * overlap_fraction / 2.0
    for r in range(rows):
        for c in range(cols):
            core_x0 = c * cell_w
            core_x1 = (c + 1) * cell_w
            core_y0 = r * cell_h
            core_y1 = (r + 1) * cell_h
            x0 = max(0, math.floor(core_x0 - pad_x))
            y0 = max(0, math.floor(core_y0 - pad_y))
            x1 = min(width, math.ceil(core_x1 + pad_x))
            y1 = min(height, math.ceil(core_y1 + pad_y))
            rects.append({"row": r + 1, "col": c + 1, "x0": x0, "y0": y0, "x1": x1, "y1": y1})
    return rects


def image_record(path: Path, rel: str, rect: dict[str, int] | None = None) -> dict[str, Any]:
    with Image.open(path) as im:
        width, height = im.size
        gray = im.convert("L")
        stat = ImageStat.Stat(gray)
        stddev = float(stat.stddev[0])
        extrema = gray.getextrema()
        entropy = float(gray.entropy())
    rec: dict[str, Any] = {
        "path": rel,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "pixel_width": width,
        "pixel_height": height,
        "diagnostic_gray_stddev": round(stddev, 3),
        "diagnostic_gray_entropy": round(entropy, 3),
        "diagnostic_gray_range": [int(extrema[0]), int(extrema[1])],
        "readability_state": "AUTO_LOW_INFORMATION_CANDIDATE" if (stddev < 7.0 or entropy < 2.0) else "UNASSESSED_FOR_SEMANTIC_READABILITY",
        "authority": "DERIVED",
    }
    if rect:
        rec["source_rect_px"] = {k: rect[k] for k in ["x0", "y0", "x1", "y1"]}
        rec["row"] = rect["row"]
        rec["col"] = rect["col"]
    return rec


def intersection(a: dict[str, int], b: dict[str, int]) -> dict[str, int] | None:
    x0 = max(a["x0"], b["x0"])
    y0 = max(a["y0"], b["y0"])
    x1 = min(a["x1"], b["x1"])
    y1 = min(a["y1"], b["y1"])
    if x1 <= x0 or y1 <= y0:
        return None
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


def build_layer(img: Image.Image, page_dir: Path, page_no: int, *, layer: str, cols: int, rows: int, overlap: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    layer_dir = page_dir / layer
    layer_dir.mkdir(parents=True, exist_ok=True)
    width, height = img.size
    rects = expanded_grid_rects(width, height, cols, rows, overlap)
    records: list[dict[str, Any]] = []
    by_id: dict[str, tuple[dict[str, int], dict[str, Any]]] = {}
    for rect in rects:
        item_id = f"P{page_no:03d}-{layer.upper()}-R{rect['row']:02d}-C{rect['col']:02d}"
        crop = img.crop((rect["x0"], rect["y0"], rect["x1"], rect["y1"]))
        out = layer_dir / f"{item_id}.jpg"
        crop.save(out, "JPEG", quality=94, optimize=True, progressive=False)
        rel = out.relative_to(ROOT).as_posix()
        rec = {"evidence_id": item_id, **image_record(out, rel, rect)}
        records.append(rec)
        by_id[item_id] = (rect, rec)

    overlaps: list[dict[str, Any]] = []
    ids = list(by_id)
    for i, aid in enumerate(ids):
        arect, arec = by_id[aid]
        for bid in ids[i + 1:]:
            brect, brec = by_id[bid]
            if abs(arec["row"] - brec["row"]) + abs(arec["col"] - brec["col"]) != 1:
                continue
            inter = intersection(arect, brect)
            if inter:
                overlaps.append({"a": aid, "b": bid, "intersection_rect_px": inter})
    return records, overlaps


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic high-resolution evidence for FPEP P02 without semantic reading")
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--overview-dpi", type=int, default=120)
    parser.add_argument("--evidence-dpi", type=int, default=300)
    args = parser.parse_args()

    if not P01_IDENTITY.exists():
        raise SystemExit("missing P01 source identity audit")
    if RESULT.exists():
        raise SystemExit("FPEP result inbox is not empty; refusing to overwrite")
    if not args.pdf.exists():
        raise SystemExit(f"missing immutable PDF materialization: {args.pdf}")

    p01 = json.loads(P01_IDENTITY.read_text(encoding="utf-8"))
    sid = p01.get("source_identity", {})
    expected_sha = sid.get("sha256")
    actual_sha = sha256_file(args.pdf)
    if expected_sha != actual_sha:
        raise SystemExit(f"immutable PDF SHA-256 mismatch: expected {expected_sha}, actual {actual_sha}")
    expected_bytes = int(sid.get("bytes"))
    if args.pdf.stat().st_size != expected_bytes:
        raise SystemExit(f"immutable PDF byte-size mismatch: expected {expected_bytes}, actual {args.pdf.stat().st_size}")

    if EVIDENCE_ROOT.exists():
        shutil.rmtree(EVIDENCE_ROOT)
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)

    pages = pdf_page_count(args.pdf)
    manifest_pages: list[dict[str, Any]] = []
    low_information: list[dict[str, Any]] = []

    tmp_root = ROOT / "analysis" / "fpep" / ".p02_tmp"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)

    try:
        for page_no in range(1, pages + 1):
            page_dir = EVIDENCE_ROOT / f"page-{page_no:03d}"
            page_dir.mkdir(parents=True, exist_ok=True)

            overview = render_page(args.pdf, page_no, args.overview_dpi, tmp_root / f"overview-{page_no:03d}")
            overview_out = page_dir / f"P{page_no:03d}-OVERVIEW.jpg"
            shutil.copy2(overview, overview_out)
            overview_rec = {"evidence_id": f"P{page_no:03d}-OVERVIEW", **image_record(overview_out, overview_out.relative_to(ROOT).as_posix())}

            highres = render_page(args.pdf, page_no, args.evidence_dpi, tmp_root / f"highres-{page_no:03d}")
            with Image.open(highres) as hi:
                hi.load()
                regions, region_overlaps = build_layer(hi, page_dir, page_no, layer="region", cols=2, rows=2, overlap=0.06)
                tiles, tile_overlaps = build_layer(hi, page_dir, page_no, layer="tile", cols=3, rows=4, overlap=0.10)
                source_pixel_size = {"width": hi.width, "height": hi.height}

            for rec in regions + tiles:
                if rec["readability_state"] == "AUTO_LOW_INFORMATION_CANDIDATE":
                    low_information.append({
                        "evidence_id": rec["evidence_id"],
                        "source_rect_px": rec["source_rect_px"],
                        "classification": "AUTO_LOW_INFORMATION_CANDIDATE",
                        "authority": "DERIVED_DIAGNOSTIC",
                        "note": "Automatic image-statistics flag only; P03 reader must decide NOT_VISIBLE/READABLE from the rendered evidence."
                    })

            manifest_pages.append({
                "page": page_no,
                "overview": overview_rec,
                "evidence_dpi_pixel_size": source_pixel_size,
                "regions": regions,
                "region_overlap_map": region_overlaps,
                "tiles": tiles,
                "tile_overlap_map": tile_overlaps,
            })
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    now = datetime.now(timezone.utc)
    run_id = f"FPEP-P02-{now.strftime('%Y%m%dT%H%M%SZ')}"
    decision = "PASS_WITH_WATCH" if low_information else "PASS"
    semantic_gate = "WATCH" if low_information else "PASS"

    manifest = {
        "schema_version": "1.0",
        "pipeline_id": PIPELINE_ID,
        "work_item_id": WORK_ITEM_ID,
        "agent_role": AGENT_ROLE,
        "generated_at": now.isoformat(),
        "decision": decision,
        "semantic_gate": semantic_gate,
        "parent_source": {
            "source_id": sid.get("source_id"),
            "path": SOURCE_REF,
            "archive_branch": sid.get("archive_branch"),
            "remote_path": sid.get("remote_path"),
            "git_blob_sha": sid.get("git_blob_sha"),
            "sha256_expected": expected_sha,
            "sha256_actual": actual_sha,
            "sha256_match": True,
            "bytes_expected": expected_bytes,
            "bytes_actual": args.pdf.stat().st_size,
            "bytes_match": True,
            "authority": "SOURCE_PRIMARY",
            "status": "DOC_PRIMARY_IMMUTABLE"
        },
        "render_recipe": {
            "renderer": poppler_version(),
            "overview_dpi": args.overview_dpi,
            "evidence_dpi": args.evidence_dpi,
            "jpeg_quality": 94,
            "region_grid": {"cols": 2, "rows": 2, "overlap_fraction": 0.06},
            "tile_grid": {"cols": 3, "rows": 4, "overlap_fraction": 0.10},
            "coordinate_origin": "top-left of evidence-DPI page raster",
            "coordinate_units": "pixels",
            "crop_rule": "Every region/tile is a deterministic crop of the evidence-DPI page raster; source_rect_px is authoritative only for derived raster localization."
        },
        "pages_count": pages,
        "pages": manifest_pages,
        "unreadable_zones": low_information,
        "unreadable_zone_policy": "Only automatic low-information candidates are flagged at P02. Semantic readability is deliberately deferred to P03 readers; absence from this list is not a READABLE claim.",
        "epistemic_policy": {
            "immutable_pdf_outranks_all_renders": True,
            "all_rendered_evidence_authority": "DERIVED",
            "raster_coordinates_do_not_create_DOC_geometry": True,
            "no_geometry_or_topology_interpreted": True,
            "forbidden_context_used": False
        },
        "next_authorized_stages": ["FPEP-P03A-BLIND-READ-A", "FPEP-P03B-BLIND-READ-B"]
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    residuals: list[dict[str, Any]] = []
    if low_information:
        residuals.append({
            "residual_id": "P02-W001",
            "claim_id": "P02-AUTO-READABILITY-DIAGNOSTIC",
            "blocking": False,
            "reason": f"{len(low_information)} derived evidence zones meet the automatic low-information threshold.",
            "required_evidence": "P03 blind readers must classify each referenced zone as READABLE/NOT_VISIBLE from the rendered evidence; do not infer missing geometry."
        })

    p01_hash = sha256_file(P01_IDENTITY)
    result = {
        "schema_version": "1.0",
        "pipeline_id": PIPELINE_ID,
        "run_id": run_id,
        "work_item_id": WORK_ITEM_ID,
        "stage_id": WORK_ITEM_ID,
        "agent_role": AGENT_ROLE,
        "decision": decision,
        "semantic_gate": semantic_gate,
        "input_artifacts": [
            {
                "path": "analysis/fpep/FPEP_SOURCE_IDENTITY_v1.json",
                "sha256": p01_hash,
                "authority": "RECEIPT_GATED_DERIVED",
                "status": "CURRENT"
            },
            {
                "path": SOURCE_REF,
                "sha256": actual_sha,
                "authority": "SOURCE_PRIMARY",
                "status": "DOC_PRIMARY_IMMUTABLE"
            }
        ],
        "primary_sources": [
            {
                "source_id": sid.get("source_id"),
                "path": SOURCE_REF,
                "git_blob_sha": sid.get("git_blob_sha"),
                "sha256": actual_sha,
                "evidence_anchor": "analysis/fpep/FPEP_SOURCE_IDENTITY_v1.json:source_identity"
            }
        ],
        "target_outputs": ["analysis/fpep/FPEP_HIRES_EVIDENCE_MANIFEST_v1.json"],
        "provenance_summary": {"DOC": 1, "MIS": 0, "RIF": 0, "INF": 0, "INC": len(residuals), "ND": 0},
        "residuals": residuals,
        "audit_paths": ["analysis/fpep/FPEP_HIRES_EVIDENCE_MANIFEST_v1.json"],
        "information_barrier_attestation": {
            "forbidden_context_not_used": True,
            "legacy_target_counts_not_used_before_primary_gate": True,
            "downstream_model_not_used_as_primary_evidence": True,
            "majority_vote_not_used_for_authority": True
        }
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "GENERATED",
        "work_item_id": WORK_ITEM_ID,
        "decision": decision,
        "pages": pages,
        "low_information_zones": len(low_information),
        "manifest": MANIFEST.relative_to(ROOT).as_posix(),
        "result": RESULT.relative_to(ROOT).as_posix()
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
