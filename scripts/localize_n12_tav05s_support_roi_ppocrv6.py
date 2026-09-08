#!/usr/bin/env python3
import csv
import hashlib
import io
import json
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
TARGET = "40x40"
DPI = 300
ROI_HALF = 480


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
    # x = a*u + b*v + c ; y = d*u + e*v + f
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

    raw_hits = []
    roi_register = []
    for support in supports:
        sid = support["support_id"]
        x = float(support["x_global_m"])
        y = float(support["y_global_m"])
        u, v = inverse_affine(x, y, reg)
        # CEW EWS-3.1 verified adapter from ROT90_CCW frame to native portrait DZI/render.
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
                if norm != TARGET:
                    continue
                if i >= len(boxes):
                    continue
                vals = boxes[i].tolist() if hasattr(boxes[i], "tolist") else list(boxes[i])
                if len(vals) != 4:
                    continue
                bx0, by0, bx1, by1 = [float(z) for z in vals]
                global_box = [bx0+x0, by0+y0, bx1+x0, by1+y0]
                raw_hits.append({
                    "support_roi_id": sid,
                    "raw_text": str(text),
                    "normalized_text": norm,
                    "confidence": float(scores[i]) if i < len(scores) else None,
                    "bbox_render_300dpi": [round(z, 3) for z in global_box],
                })

    raw_hits.sort(key=lambda r: (r["bbox_render_300dpi"][1], r["bbox_render_300dpi"][0], -(r["confidence"] or 0)))
    unique = []
    for rec in raw_hits:
        if any(iou(rec["bbox_render_300dpi"], old["bbox_render_300dpi"]) > 0.5 for old in unique):
            continue
        unique.append(rec)

    for idx, rec in enumerate(unique):
        x0, y0, x1, y1 = rec["bbox_render_300dpi"]
        rec["hit_index"] = idx
        rec["bbox_normalized_0_1"] = [
            round(x0/img.width, 9), round(y0/img.height, 9),
            round(x1/img.width, 9), round(y1/img.height, 9),
        ]
        rec["bbox_pdf_points"] = [
            round(x0/scale, 6), round(y0/scale, 6),
            round(x1/scale, 6), round(y1/scale, 6),
        ]

    selected = None
    if unique:
        selected = sorted(unique, key=lambda r: (-(r["confidence"] or 0), r["bbox_render_300dpi"][1], r["bbox_render_300dpi"][0]))[0]

    result = {
        "schema": "N12_TAV05S_SUPPORT_ROI_PPOCRV6_LOCATOR_v1",
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
        "target": TARGET,
        "hit_count": len(unique),
        "hits": unique,
        "selected_token_observation": selected,
        "selected_token_semantics": "TECHNICAL_TOKEN_OBSERVATION_ONLY",
        "target_relation": None,
        "engineering_confidence_from_ocr_forbidden": True,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not unique:
        print("N12_TAV05S_SUPPORT_ROI_40X40_PPOCRV6_NOT_FOUND")
        return 2
    print(f"N12_TAV05S_SUPPORT_ROI_40X40_PPOCRV6_FOUND count={len(unique)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
