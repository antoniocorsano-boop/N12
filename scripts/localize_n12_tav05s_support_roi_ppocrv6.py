#!/usr/bin/env python3
import csv
import hashlib
import io
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
GEOMETRY_COMMIT = "a65951b634fd3183223139a6fd1226e4586fec14"
REG_PATH = "data/canonical/STOREY_SUPPORT_XY_REGISTRATION_v1.csv"
SUPPORT_PATH = "data/canonical/VERTICAL_SUPPORT_LINES_CURRENT_v1.csv"
OUT = ROOT / "artifacts" / "n12_tav05s_support_roi_ppocrv6_locator.json"
DPI = 300
ROI_HALF = 480
PAIR_MAX_CENTER_DISTANCE = 220.0


def fail(msg: str) -> None:
    print(f"N12_TAV05S_SUPPORT_ROI_PPOCRV6_FAIL: {msg}")
    raise SystemExit(1)


def git_bytes(commit: str, path: str) -> bytes:
    proc = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        fail(f"cannot materialize {commit}:{path}: {proc.stderr.decode('utf-8', errors='replace')}")
    return proc.stdout


def normalize(text: str) -> str:
    s = str(text).replace("×", "x").replace("X", "x").replace("*", "x")
    return re.sub(r"\s+", "", s).lower()


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


def inverse_affine(x, y, row):
    a = float(row["metric_x_from_u"])
    b = float(row["metric_x_from_v"])
    c = float(row["metric_x_offset"])
    d = float(row["metric_y_from_u"])
    e = float(row["metric_y_from_v"])
    f = float(row["metric_y_offset"])
    det = a * e - b * d
    if abs(det) < 1e-12:
        fail("singular G4 registration")
    xx, yy = x - c, y - f
    u = (e * xx - b * yy) / det
    v = (-d * xx + a * yy) / det
    return u, v


def iou(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    if not inter:
        return 0.0
    union = (ax1-ax0)*(ay1-ay0) + (bx1-bx0)*(by1-by0) - inter
    return inter / union if union else 0.0


def orientation(box):
    x0, y0, x1, y1 = box
    w = max(1.0, x1 - x0)
    h = max(1.0, y1 - y0)
    if w / h >= 1.20:
        return "HORIZONTAL_LIKE"
    if h / w >= 1.20:
        return "VERTICAL_LIKE"
    return "SQUARE_LIKE"


def center(box):
    x0, y0, x1, y1 = box
    return ((x0+x1)/2.0, (y0+y1)/2.0)


def add_coordinate_forms(rec, img, scale):
    x0, y0, x1, y1 = rec["bbox_render_300dpi"]
    rec["bbox_normalized_0_1"] = [
        round(x0/img.width, 9), round(y0/img.height, 9),
        round(x1/img.width, 9), round(y1/img.height, 9),
    ]
    rec["bbox_pdf_points"] = [
        round(x0/scale, 6), round(y0/scale, 6),
        round(x1/scale, 6), round(y1/scale, 6),
    ]
    rec["bbox_orientation"] = orientation(rec["bbox_render_300dpi"])


def main() -> int:
    source_bytes = git_bytes(SOURCE_COMMIT, SOURCE_PATH)
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != EXPECTED_SHA256:
        fail(f"source digest mismatch: {digest}")

    reg_rows = list(csv.DictReader(io.StringIO(git_bytes(GEOMETRY_COMMIT, REG_PATH).decode("utf-8"))))
    reg = next((r for r in reg_rows if r["sheet_id"] == "TAV-05S" and r["level_id"] == "G4"), None)
    if not reg or reg["validation_state"] != "CROSS_VALIDATED":
        fail("missing CROSS_VALIDATED TAV-05S/G4 registration")

    support_rows = list(csv.DictReader(io.StringIO(git_bytes(GEOMETRY_COMMIT, SUPPORT_PATH).decode("utf-8"))))
    supports = [r for r in support_rows if r["entity_type"] == "NUMBERED_PILLAR" and r["g4_present"] == "PRESENT"]
    if len(supports) != 34:
        fail(f"expected 34 G4 numbered supports, found {len(supports)}")

    doc = fitz.open(stream=source_bytes, filetype="pdf")
    page = doc[0]
    scale = DPI / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    if [img.width, img.height] != [7016, 12530]:
        fail(f"unexpected 300dpi render size: {img.width}x{img.height}")

    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        device="cpu",
    )

    all_40 = []
    exact_40x40 = []
    roi_register = []
    for support in supports:
        sid = support["support_id"]
        x = float(support["x_global_m"])
        y = float(support["y_global_m"])
        u, v = inverse_affine(x, y, reg)
        cx = img.width - v
        cy = u
        if not (0 <= cx <= img.width and 0 <= cy <= img.height):
            fail(f"support {sid} transformed outside native render: ({cx}, {cy})")
        x0 = max(0, int(round(cx - ROI_HALF)))
        y0 = max(0, int(round(cy - ROI_HALF)))
        x1 = min(img.width, int(round(cx + ROI_HALF)))
        y1 = min(img.height, int(round(cy + ROI_HALF)))
        roi_register.append({
            "support_id": sid,
            "metric_xy_m": [x, y],
            "rot90_frame_uv_px": [round(u, 3), round(v, 3)],
            "native_center_300dpi_px": [round(cx, 3), round(cy, 3)],
            "roi_300dpi_px": [x0, y0, x1, y1],
            "locator_authority": "REGISTERED_DERIVED_NAVIGATION_ONLY",
        })
        tile = np.asarray(img.crop((x0, y0, x1, y1)))
        for res in ocr.predict(tile):
            rd = result_dict(res)
            texts = rd.get("rec_texts", []) or []
            scores = rd.get("rec_scores", []) or []
            boxes = rd.get("rec_boxes", []) or []
            for i, text in enumerate(texts):
                norm = normalize(text)
                if norm not in {"40", "40x40"} or i >= len(boxes):
                    continue
                vals = boxes[i].tolist() if hasattr(boxes[i], "tolist") else list(boxes[i])
                if len(vals) != 4:
                    continue
                bx0, by0, bx1, by1 = [float(z) for z in vals]
                rec = {
                    "support_roi_id": sid,
                    "raw_text": str(text),
                    "normalized_text": norm,
                    "confidence": float(scores[i]) if i < len(scores) else None,
                    "bbox_render_300dpi": [round(bx0+x0, 3), round(by0+y0, 3), round(bx1+x0, 3), round(by1+y0, 3)],
                }
                add_coordinate_forms(rec, img, scale)
                (exact_40x40 if norm == "40x40" else all_40).append(rec)

    # Deduplicate repeated OCR of the same mark caused by overlapping support ROIs.
    all_40.sort(key=lambda r: (r["bbox_render_300dpi"][1], r["bbox_render_300dpi"][0], -(r["confidence"] or 0)))
    unique_40 = []
    for rec in all_40:
        if any(iou(rec["bbox_render_300dpi"], old["bbox_render_300dpi"]) > 0.5 for old in unique_40):
            continue
        unique_40.append(rec)

    # Build only relation candidates. Two 40 tokens must come from the same governed support ROI,
    # be spatially close, and have different bbox orientation classes. This does NOT bind them
    # to the support symbol and does NOT assert a 40x40 structural section.
    pair_candidates = []
    by_roi = {}
    for rec in unique_40:
        by_roi.setdefault(rec["support_roi_id"], []).append(rec)
    for sid, tokens in by_roi.items():
        for i in range(len(tokens)):
            for j in range(i+1, len(tokens)):
                a, b = tokens[i], tokens[j]
                oa, ob = a["bbox_orientation"], b["bbox_orientation"]
                if {oa, ob} != {"HORIZONTAL_LIKE", "VERTICAL_LIKE"}:
                    continue
                ca, cb = center(a["bbox_render_300dpi"]), center(b["bbox_render_300dpi"])
                dist = math.hypot(ca[0]-cb[0], ca[1]-cb[1])
                if dist > PAIR_MAX_CENTER_DISTANCE:
                    continue
                pair_candidates.append({
                    "pair_id": f"PAIR-{sid}-{i}-{j}",
                    "support_roi_id": sid,
                    "normalized_dimension_pair": [40, 40],
                    "relation": "ORTHOGONAL_DIMENSION_TOKEN_PAIR_CANDIDATE",
                    "center_distance_300dpi_px": round(dist, 3),
                    "token_a": a,
                    "token_b": b,
                    "pair_confidence_min_ocr_only": min(a["confidence"] or 0.0, b["confidence"] or 0.0),
                    "target_relation": None,
                    "engineering_semantics": "SECTION_DIMENSION_CANDIDATE_NEEDS_TARGET_BINDING",
                    "structural_section_assertion": False,
                })

    pair_candidates.sort(key=lambda p: (-p["pair_confidence_min_ocr_only"], p["center_distance_300dpi_px"], p["support_roi_id"]))
    selected_pair = pair_candidates[0] if pair_candidates else None

    result = {
        "schema": "N12_TAV05S_SUPPORT_ROI_PPOCRV6_LOCATOR_v2",
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "source_commit": SOURCE_COMMIT,
        "source_sha256": digest,
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "evidence_region_id": "CEW-N12-REG-TAV05S-G4-COLUMN-PILOT",
        "geometry_commit": GEOMETRY_COMMIT,
        "registration_validation_state": reg["validation_state"],
        "registration_inlier_count": int(reg["inlier_count"]),
        "roi_basis": "ALL_34_G4_NUMBERED_SUPPORTS_NO_FAMILY_FILTER",
        "roi_count": len(roi_register),
        "roi_register": roi_register,
        "render_dpi": DPI,
        "render_size": [img.width, img.height],
        "ocr_engine": "PaddleOCR",
        "ocr_model": "PP-OCRv6-medium-default",
        "exact_40x40_hit_count": len(exact_40x40),
        "exact_40x40_hits": exact_40x40,
        "numeric_40_token_count": len(unique_40),
        "numeric_40_tokens": unique_40,
        "dimension_pair_candidate_count": len(pair_candidates),
        "dimension_pair_candidates": pair_candidates,
        "selected_dimension_pair_candidate": selected_pair,
        "selected_candidate_semantics": "SECTION_DIMENSION_CANDIDATE_NEEDS_TARGET_BINDING" if selected_pair else None,
        "engineering_confidence_from_ocr_forbidden": True,
        "automatic_target_binding_forbidden": True,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not selected_pair:
        print("N12_TAV05S_40_40_DIMENSION_PAIR_NOT_RECOVERED")
        return 2
    print("N12_TAV05S_40_40_DIMENSION_PAIR_CANDIDATE_RECOVERED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
