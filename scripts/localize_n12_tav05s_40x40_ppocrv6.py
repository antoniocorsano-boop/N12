#!/usr/bin/env python3
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "78c20a52db4f391ce0d13b9705b9f04737e218c9"
SOURCE_PATH = "archive/documentazione_originaria/tavola 5.pdf"
EXPECTED_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
OUT = ROOT / "artifacts" / "n12_tav05s_40x40_ppocrv6_locator.json"
TARGET = "40x40"
DPI = 300
TILE_W = 1800
TILE_H = 1800
OVERLAP = 160


def fail(msg: str) -> None:
    print(f"N12_TAV05S_40X40_PPOCRV6_FAIL: {msg}")
    raise SystemExit(1)


def normalize(text: str) -> str:
    s = str(text).replace("×", "x").replace("X", "x").replace("*", "x")
    s = re.sub(r"\s+", "", s)
    return s.lower()


def materialize_source(dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        fail(proc.stderr.decode("utf-8", errors="replace"))
    dst.write_bytes(proc.stdout)


def result_dict(res):
    if hasattr(res, "json"):
        val = res.json
        if callable(val):
            val = val()
        if isinstance(val, dict):
            return val.get("res", val)
    if isinstance(res, dict):
        return res.get("res", res)
    try:
        return dict(res)
    except Exception:
        return {}


def iou(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
    inter = iw * ih
    if not inter:
        return 0.0
    ua = (ax1-ax0)*(ay1-ay0) + (bx1-bx0)*(by1-by0) - inter
    return inter / ua if ua else 0.0


def main() -> int:
    tmp_pdf = ROOT / ".tmp" / "n12_tav05s_source.pdf"
    materialize_source(tmp_pdf)
    digest = hashlib.sha256(tmp_pdf.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        fail(f"source digest mismatch: {digest}")

    doc = fitz.open(tmp_pdf)
    page = doc[0]
    scale = DPI / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        device="cpu",
    )

    detections = []
    near = []
    step_x = TILE_W - OVERLAP
    step_y = TILE_H - OVERLAP
    tile_index = 0
    for y0 in range(0, img.height, step_y):
        for x0 in range(0, img.width, step_x):
            x1 = min(img.width, x0 + TILE_W)
            y1 = min(img.height, y0 + TILE_H)
            tile = np.asarray(img.crop((x0, y0, x1, y1)))
            for res in ocr.predict(tile):
                rd = result_dict(res)
                texts = rd.get("rec_texts", []) or []
                scores = rd.get("rec_scores", []) or []
                boxes = rd.get("rec_boxes", []) or []
                for i, text in enumerate(texts):
                    norm = normalize(text)
                    if not norm:
                        continue
                    score = float(scores[i]) if i < len(scores) else None
                    if i < len(boxes):
                        box = boxes[i]
                        vals = box.tolist() if hasattr(box, "tolist") else list(box)
                        if len(vals) == 4:
                            bx0, by0, bx1, by1 = [float(v) for v in vals]
                        else:
                            continue
                    else:
                        continue
                    global_box = [bx0+x0, by0+y0, bx1+x0, by1+y0]
                    rec = {
                        "raw_text": str(text),
                        "normalized_text": norm,
                        "confidence": score,
                        "tile_index": tile_index,
                        "bbox_render_300dpi": [round(v, 3) for v in global_box],
                    }
                    if norm == TARGET:
                        detections.append(rec)
                    elif "40" in norm:
                        near.append(rec)
            tile_index += 1
            if x1 == img.width:
                break
        if y1 == img.height:
            break

    # deterministic duplicate suppression across overlapping tiles
    detections.sort(key=lambda r: (r["bbox_render_300dpi"][1], r["bbox_render_300dpi"][0], -(r["confidence"] or 0)))
    unique = []
    for rec in detections:
        if any(iou(rec["bbox_render_300dpi"], old["bbox_render_300dpi"]) > 0.5 for old in unique):
            continue
        unique.append(rec)

    for idx, rec in enumerate(unique):
        x0, y0, x1, y1 = rec["bbox_render_300dpi"]
        rec["hit_index"] = idx
        rec["bbox_normalized_0_1"] = [
            round(x0 / img.width, 9), round(y0 / img.height, 9),
            round(x1 / img.width, 9), round(y1 / img.height, 9),
        ]
        rec["bbox_pdf_points"] = [
            round(x0 / scale, 6), round(y0 / scale, 6),
            round(x1 / scale, 6), round(y1 / scale, 6),
        ]

    result = {
        "schema": "N12_TAV05S_PPOCRV6_TOKEN_LOCATOR_v1",
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "source_commit": SOURCE_COMMIT,
        "source_path": SOURCE_PATH,
        "source_sha256": digest,
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "page_index": 0,
        "evidence_region_id": "CEW-N12-REG-TAV05S-G4-COLUMN-PILOT",
        "render_dpi": DPI,
        "render_size": [img.width, img.height],
        "ocr_engine": "PaddleOCR",
        "ocr_model": "PP-OCRv6-medium-default",
        "target": TARGET,
        "hit_count": len(unique),
        "hits": unique,
        "near_candidates": near[:50],
        "semantic_authority": "NONE",
        "engineering_confidence_from_ocr_forbidden": True,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not unique:
        print("N12_TAV05S_40X40_PPOCRV6_NOT_FOUND")
        return 2
    print(f"N12_TAV05S_40X40_PPOCRV6_FOUND count={len(unique)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
