#!/usr/bin/env python3
"""Deterministic CEW-F2 probe for immutable primary-source PDFs.

The script verifies SHA-256, extracts page metadata with PyMuPDF and renders
full pages at a declared DPI for human evidence-region localization. Rendered
assets are review aids only; authority remains the primary PDF SourceVersion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import fitz


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(source_id: str, path: Path, expected_sha256: str, dpi: int, out_dir: Path) -> dict:
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise SystemExit(
            f"SHA256_MISMATCH {source_id}: expected={expected_sha256} actual={actual}"
        )

    doc = fitz.open(path)
    source_out = out_dir / source_id
    source_out.mkdir(parents=True, exist_ok=True)

    pages = []
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    for page_index, page in enumerate(doc):
        rect = page.rect
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        render_name = f"{source_id}_p{page_index + 1:03d}_{dpi}dpi.png"
        render_path = source_out / render_name
        pix.save(render_path)
        pages.append(
            {
                "page_index_0": page_index,
                "page_number_1": page_index + 1,
                "width_pt": round(rect.width, 6),
                "height_pt": round(rect.height, 6),
                "rotation": int(page.rotation),
                "render_dpi": dpi,
                "render_width_px": int(pix.width),
                "render_height_px": int(pix.height),
                "render_file": str(render_path),
            }
        )

    return {
        "source_id": source_id,
        "path": str(path),
        "sha256": actual,
        "page_count": len(doc),
        "pages": pages,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", default="cew-f2-reference-probe")
    p.add_argument("--dpi", type=int, default=150)
    p.add_argument(
        "--source",
        action="append",
        nargs=3,
        metavar=("SOURCE_ID", "PDF_PATH", "SHA256"),
        required=True,
    )
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "probe_contract": "CEW-F2-REFERENCE-PDF-PROBE-v1",
        "render_authority": "REVIEW_AID_ONLY",
        "coordinate_authority": "SOURCE_PDF_PAGE",
        "dpi": args.dpi,
        "sources": [],
    }
    for source_id, path, expected_sha256 in args.source:
        report["sources"].append(
            probe(source_id, Path(path), expected_sha256, args.dpi, out_dir)
        )

    report_path = out_dir / "reference_pdf_probe.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("CEW_F2_REFERENCE_PDF_PROBE_PASS")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
