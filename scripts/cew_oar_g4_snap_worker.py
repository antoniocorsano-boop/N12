#!/usr/bin/env python3
"""Build-only raster contour candidates for assisted G4 localization.

The output is an interaction aid only. It does not identify supports, confirm
families, write EvidenceRegion state, or grant engineering authority.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import cv2

FAMILY_RATIOS = {
    "COL-G4-40X40": 1.0,
    "COL-G4-45X30": 45.0 / 30.0,
    "COL-G4-30X45": 30.0 / 45.0,
    "COL-G4-30X110": 30.0 / 110.0,
    "COL-G4-110X30": 110.0 / 30.0,
}
MAX_CANDIDATES = 6000


def _ratio_error(actual: float, expected: float) -> float:
    if actual <= 0 or expected <= 0:
        return 999.0
    return abs(math.log(actual / expected))


def _iou(a: dict, b: dict) -> float:
    ax1, ay1, ax2, ay2 = a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]
    bx1, by1, bx2, by2 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
    ix1, iy1, ix2, iy2 = max(ax1, bx1), max(ay1, by1), min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    union = a["w"] * a["h"] + b["w"] * b["h"] - inter
    return inter / union if union > 0 else 0.0


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: cew_oar_g4_snap_worker.py INPUT_JPEG OUTPUT_JSON")
    image_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise SystemExit("OAR_G4_SNAP_IMAGE_UNREADABLE")

    original_h, original_w = image.shape[:2]
    # Work at half resolution. Candidate coordinates are normalized back to the
    # governed 7016x12530 asset, so this only affects build cost, not receipts.
    work = cv2.resize(image, (original_w // 2, original_h // 2), interpolation=cv2.INTER_AREA)
    h, w = work.shape[:2]
    blurred = cv2.GaussianBlur(work, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    contours, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    raw: list[dict] = []
    min_side = max(5, int(min(w, h) * 0.0010))
    max_side = int(min(w, h) * 0.060)
    for contour in contours:
        x, y, bw, bh = cv2.boundingRect(contour)
        if bw < min_side or bh < min_side or bw > max_side or bh > max_side:
            continue
        rect_area = float(bw * bh)
        if rect_area <= 0:
            continue
        contour_area = abs(float(cv2.contourArea(contour)))
        rectangularity = contour_area / rect_area
        if rectangularity < 0.12:
            continue
        ratio = float(bw) / float(bh)
        errors = {family: _ratio_error(ratio, target) for family, target in FAMILY_RATIOS.items()}
        best_family, best_error = min(errors.items(), key=lambda item: item[1])
        # Very dissimilar contours are usually text/lines rather than one of the
        # five pilot footprint shapes. Keep a generous threshold; human review
        # and tap distance still control the final proposal.
        if best_error > math.log(2.25):
            continue

        margin_x = bw * 0.12
        margin_y = bh * 0.12
        nx = max(0.0, (x - margin_x) / w)
        ny = max(0.0, (y - margin_y) / h)
        nx2 = min(1.0, (x + bw + margin_x) / w)
        ny2 = min(1.0, (y + bh + margin_y) / h)
        bbox = {"x": nx, "y": ny, "w": nx2 - nx, "h": ny2 - ny}
        score = min(1.0, 0.55 * min(1.0, rectangularity) + 0.45 * math.exp(-best_error))
        raw.append({
            "bbox": bbox,
            "center": {"x": (nx + nx2) / 2.0, "y": (ny + ny2) / 2.0},
            "aspect_ratio": ratio,
            "rectangularity": rectangularity,
            "best_family_prior": best_family,
            "family_ratio_error": errors,
            "build_quality": score,
        })

    raw.sort(key=lambda row: row["build_quality"], reverse=True)
    kept: list[dict] = []
    for row in raw:
        if any(_iou(row["bbox"], existing["bbox"]) > 0.82 for existing in kept[-800:]):
            continue
        kept.append(row)
        if len(kept) >= MAX_CANDIDATES:
            break

    for idx, row in enumerate(kept, start=1):
        row["candidate_id"] = f"G4-SNAP-{idx:04d}"

    output = {
        "schema": "CEW_OAR_G4_SNAP_CANDIDATES_v1",
        "source_asset": "CEW-N12-ASSET-TAV05S-P001-OAR-300DPI",
        "source_dimensions_px": [original_w, original_h],
        "analysis_dimensions_px": [w, h],
        "coordinate_system": "NORMALIZED_0_1",
        "candidate_count": len(kept),
        "candidates": kept,
        "authority": {
            "snap_candidates_are_authority": False,
            "oar_classification_confirmed": False,
            "canonical_write_authorized": False,
            "structural_identity_authorized": False,
            "engineering_authority_effect": "NONE",
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"CEW_OAR_G4_SNAP_WORKER_PASS candidates={len(kept)}")


if __name__ == "__main__":
    main()
