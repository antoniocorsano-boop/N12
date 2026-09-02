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


def _area(box: dict) -> float:
    return max(0.0, float(box["w"])) * max(0.0, float(box["h"]))


def _intersection_area(a: dict, b: dict) -> float:
    ax1, ay1, ax2, ay2 = a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]
    bx1, by1, bx2, by2 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
    ix1, iy1, ix2, iy2 = max(ax1, bx1), max(ay1, by1), min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1)


def _iou(a: dict, b: dict) -> float:
    inter = _intersection_area(a, b)
    union = _area(a) + _area(b) - inter
    return inter / union if union > 0 else 0.0


def _contained_fraction(inner: dict, outer: dict) -> float:
    inner_area = _area(inner)
    return _intersection_area(inner, outer) / inner_area if inner_area > 0 else 0.0


def _extract_candidates(mask, w: int, h: int, min_side: int, max_side: int, detector: str) -> list[dict]:
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    raw: list[dict] = []
    envelope_detector = detector == "LONG_AXIS_SUPPRESSED"
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
        if best_error > math.log(2.25):
            continue

        # Axis-suppressed contours are intended to recover the whole footprint,
        # so they need less visual halo than fallback raw contours.
        margin_factor = 0.08 if envelope_detector else 0.12
        margin_x = bw * margin_factor
        margin_y = bh * margin_factor
        nx = max(0.0, (x - margin_x) / w)
        ny = max(0.0, (y - margin_y) / h)
        nx2 = min(1.0, (x + bw + margin_x) / w)
        ny2 = min(1.0, (y + bh + margin_y) / h)
        bbox = {"x": nx, "y": ny, "w": nx2 - nx, "h": ny2 - ny}
        ratio_compatibility = math.exp(-best_error)
        base_quality = min(1.0, 0.55 * min(1.0, rectangularity) + 0.45 * ratio_compatibility)
        envelope_confidence = (
            min(1.0, 0.55 * min(1.0, rectangularity) + 0.45 * ratio_compatibility)
            if envelope_detector
            else 0.0
        )
        build_quality = min(1.0, base_quality + (0.10 if envelope_detector else 0.0))
        raw.append({
            "bbox": bbox,
            "center": {"x": (nx + nx2) / 2.0, "y": (ny + ny2) / 2.0},
            "aspect_ratio": ratio,
            "rectangularity": rectangularity,
            "best_family_prior": best_family,
            "family_ratio_error": errors,
            "build_quality": build_quality,
            "detector": detector,
            "footprint_envelope_confidence": envelope_confidence,
        })
    return raw


def _suppress_nested_raw_candidates(rows: list[dict]) -> tuple[list[dict], int]:
    envelopes = [row for row in rows if row.get("detector") == "LONG_AXIS_SUPPRESSED"]
    filtered: list[dict] = []
    suppressed = 0
    for row in rows:
        if row.get("detector") != "RAW_CONTOUR":
            filtered.append(row)
            continue
        row_area = _area(row["bbox"])
        nested = False
        for envelope in envelopes:
            if envelope.get("best_family_prior") != row.get("best_family_prior"):
                continue
            envelope_area = _area(envelope["bbox"])
            if row_area <= 0 or envelope_area < row_area * 1.55 or envelope_area > row_area * 7.0:
                continue
            if _contained_fraction(row["bbox"], envelope["bbox"]) < 0.82:
                continue
            family = row["best_family_prior"]
            if float(envelope["family_ratio_error"][family]) > float(row["family_ratio_error"][family]) + 0.12:
                continue
            nested = True
            break
        if nested:
            suppressed += 1
        else:
            filtered.append(row)
    return filtered, suppressed


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: cew_oar_g4_snap_worker.py INPUT_JPEG OUTPUT_JSON")
    image_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise SystemExit("OAR_G4_SNAP_IMAGE_UNREADABLE")

    original_h, original_w = image.shape[:2]
    work = cv2.resize(image, (original_w // 2, original_h // 2), interpolation=cv2.INTER_AREA)
    h, w = work.shape[:2]
    blurred = cv2.GaussianBlur(work, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    min_side = max(5, int(min(w, h) * 0.0010))
    max_side = int(min(w, h) * 0.060)

    # Any horizontal/vertical run longer than the maximum admitted footprint
    # cannot itself be one pilot column footprint. Remove those long runs before
    # contouring so grid/axis lines do not split a column into internal cells.
    long_run = max_side + 5
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (long_run, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, long_run))
    long_horizontal = cv2.morphologyEx(closed, cv2.MORPH_OPEN, horizontal_kernel)
    long_vertical = cv2.morphologyEx(closed, cv2.MORPH_OPEN, vertical_kernel)
    long_axes = cv2.bitwise_or(long_horizontal, long_vertical)
    axis_suppressed = cv2.subtract(closed, long_axes)
    axis_suppressed = cv2.morphologyEx(axis_suppressed, cv2.MORPH_CLOSE, kernel, iterations=2)

    raw = _extract_candidates(
        axis_suppressed, w, h, min_side, max_side, "LONG_AXIS_SUPPRESSED"
    )
    raw.extend(_extract_candidates(closed, w, h, min_side, max_side, "RAW_CONTOUR"))
    raw, suppressed_nested_count = _suppress_nested_raw_candidates(raw)

    raw.sort(
        key=lambda row: (
            row["build_quality"],
            row.get("footprint_envelope_confidence", 0.0),
        ),
        reverse=True,
    )
    kept: list[dict] = []
    for row in raw:
        if any(_iou(row["bbox"], existing["bbox"]) > 0.82 for existing in kept[-800:]):
            continue
        kept.append(row)
        if len(kept) >= MAX_CANDIDATES:
            break

    for idx, row in enumerate(kept, start=1):
        row["candidate_id"] = f"G4-SNAP-{idx:04d}"

    envelope_count = sum(1 for row in kept if row["detector"] == "LONG_AXIS_SUPPRESSED")
    if envelope_count <= 0:
        raise SystemExit("OAR_G4_SNAP_AXIS_SUPPRESSED_ENVELOPE_EMPTY")
    if suppressed_nested_count <= 0:
        raise SystemExit("OAR_G4_SNAP_NESTED_SUPPRESSION_NOT_EXERCISED")

    output = {
        "schema": "CEW_OAR_G4_SNAP_CANDIDATES_v1",
        "source_asset": "CEW-N12-ASSET-TAV05S-P001-OAR-300DPI",
        "source_dimensions_px": [original_w, original_h],
        "analysis_dimensions_px": [w, h],
        "coordinate_system": "NORMALIZED_0_1",
        "candidate_count": len(kept),
        "detectors": ["LONG_AXIS_SUPPRESSED", "RAW_CONTOUR"],
        "axis_suppressed_candidate_count": envelope_count,
        "nested_raw_candidate_suppressed_count": suppressed_nested_count,
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
    print(
        f"CEW_OAR_G4_SNAP_WORKER_PASS candidates={len(kept)} "
        f"axis_suppressed={envelope_count} nested_raw_suppressed={suppressed_nested_count}"
    )


if __name__ == "__main__":
    main()
