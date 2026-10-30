from __future__ import annotations

from typing import Any

import cv2
import numpy as np


MAX_CANDIDATES = 6000


def _area(box: dict[str, float]) -> float:
    return max(0.0, float(box["width"])) * max(0.0, float(box["height"]))


def _intersection_area(a: dict[str, float], b: dict[str, float]) -> float:
    ax2 = a["x"] + a["width"]
    ay2 = a["y"] + a["height"]
    bx2 = b["x"] + b["width"]
    by2 = b["y"] + b["height"]
    ix1 = max(a["x"], b["x"])
    iy1 = max(a["y"], b["y"])
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1)


def _iou(a: dict[str, float], b: dict[str, float]) -> float:
    intersection = _intersection_area(a, b)
    union = _area(a) + _area(b) - intersection
    return intersection / union if union > 0 else 0.0


def _contained_fraction(inner: dict[str, float], outer: dict[str, float]) -> float:
    area = _area(inner)
    return _intersection_area(inner, outer) / area if area > 0 else 0.0


def _extract_candidates(
    mask: np.ndarray,
    *,
    width: int,
    height: int,
    min_side: int,
    max_side: int,
    detector: str,
) -> list[dict[str, Any]]:
    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    rows: list[dict[str, Any]] = []
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

        margin_factor = 0.08 if envelope_detector else 0.12
        margin_x = bw * margin_factor
        margin_y = bh * margin_factor
        nx = max(0.0, (x - margin_x) / width)
        ny = max(0.0, (y - margin_y) / height)
        nx2 = min(1.0, (x + bw + margin_x) / width)
        ny2 = min(1.0, (y + bh + margin_y) / height)
        bbox = {
            "x": nx,
            "y": ny,
            "width": nx2 - nx,
            "height": ny2 - ny,
        }
        envelope_confidence = min(1.0, rectangularity) if envelope_detector else 0.0
        build_quality = min(
            1.0,
            0.90 * min(1.0, rectangularity) + (0.10 if envelope_detector else 0.0),
        )
        rows.append(
            {
                "bbox": bbox,
                "center": {"x": (nx + nx2) / 2.0, "y": (ny + ny2) / 2.0},
                "aspect_ratio": float(bw) / float(bh),
                "rectangularity": rectangularity,
                "build_quality": build_quality,
                "detector": detector,
                "footprint_envelope_confidence": envelope_confidence,
                "axis_evidence_present": False,
                "support_identity": None,
                "family_id": None,
            }
        )
    return rows


def _suppress_nested_raw_candidates(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Suppress small raw cells contained in an axis-suppressed outer envelope.

    This is purely geometric. No known support family, aspect-ratio registry, or
    expected identifier participates in the decision.
    """

    envelopes = [row for row in rows if row.get("detector") == "LONG_AXIS_SUPPRESSED"]
    filtered: list[dict[str, Any]] = []
    suppressed = 0
    for row in rows:
        if row.get("detector") != "RAW_CONTOUR":
            filtered.append(row)
            continue
        row_area = _area(row["bbox"])
        nested = False
        for envelope in envelopes:
            envelope_area = _area(envelope["bbox"])
            if row_area <= 0 or envelope_area < row_area * 1.55 or envelope_area > row_area * 7.0:
                continue
            if _contained_fraction(row["bbox"], envelope["bbox"]) < 0.82:
                continue
            if float(envelope.get("rectangularity", 0.0)) < 0.12:
                continue
            nested = True
            break
        if nested:
            suppressed += 1
        else:
            filtered.append(row)
    return filtered, suppressed


def extract_footprint_proposals(
    image: np.ndarray,
    *,
    max_candidates: int = MAX_CANDIDATES,
) -> dict[str, Any]:
    """Build review-only rectangular footprint proposals from a grayscale raster.

    The implementation adapts the PR #136 axis-suppression/nested-contour repair
    while deliberately removing all historical family-ratio or support-ID oracles.
    """

    if image is None or not isinstance(image, np.ndarray) or image.ndim != 2 or image.size == 0:
        raise ValueError("image must be a non-empty grayscale numpy array")
    limit = max(1, min(MAX_CANDIDATES, int(max_candidates)))
    original_h, original_w = image.shape[:2]

    # Preserve the historical half-scale analysis path for large sheets, but do
    # not upsample small unit-test rasters.
    if min(original_w, original_h) >= 1200:
        work = cv2.resize(
            image,
            (max(1, original_w // 2), max(1, original_h // 2)),
            interpolation=cv2.INTER_AREA,
        )
    else:
        work = image.copy()
    height, width = work.shape[:2]

    blurred = cv2.GaussianBlur(work, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    min_side = max(5, int(min(width, height) * 0.0010))
    max_side = max(min_side + 1, int(min(width, height) * 0.060))
    long_run = max_side + 5
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (long_run, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, long_run))
    long_horizontal = cv2.morphologyEx(closed, cv2.MORPH_OPEN, horizontal_kernel)
    long_vertical = cv2.morphologyEx(closed, cv2.MORPH_OPEN, vertical_kernel)
    long_axes = cv2.bitwise_or(long_horizontal, long_vertical)
    axis_suppressed = cv2.subtract(closed, long_axes)
    axis_suppressed = cv2.morphologyEx(axis_suppressed, cv2.MORPH_CLOSE, kernel, iterations=2)

    rows = _extract_candidates(
        axis_suppressed,
        width=width,
        height=height,
        min_side=min_side,
        max_side=max_side,
        detector="LONG_AXIS_SUPPRESSED",
    )
    rows.extend(
        _extract_candidates(
            closed,
            width=width,
            height=height,
            min_side=min_side,
            max_side=max_side,
            detector="RAW_CONTOUR",
        )
    )
    rows, nested_suppressed = _suppress_nested_raw_candidates(rows)
    rows.sort(
        key=lambda row: (
            float(row.get("build_quality", 0.0)),
            float(row.get("footprint_envelope_confidence", 0.0)),
        ),
        reverse=True,
    )

    kept: list[dict[str, Any]] = []
    for row in rows:
        if any(_iou(row["bbox"], existing["bbox"]) > 0.82 for existing in kept[-800:]):
            continue
        kept.append(row)
        if len(kept) >= limit:
            break

    for index, row in enumerate(kept, start=1):
        row["candidate_id"] = f"COL02-FP-{index:04d}"

    return {
        "schema": "CEW_COL02_FOOTPRINT_PROPOSALS_v1",
        "source_dimensions_px": [original_w, original_h],
        "analysis_dimensions_px": [width, height],
        "coordinate_system": "NORMALIZED_0_1",
        "candidate_count": len(kept),
        "detectors": ["LONG_AXIS_SUPPRESSED", "RAW_CONTOUR"],
        "axis_suppressed_candidate_count": sum(
            1 for row in kept if row["detector"] == "LONG_AXIS_SUPPRESSED"
        ),
        "nested_raw_candidate_suppressed_count": nested_suppressed,
        "candidates": kept,
        "authority": {
            "support_identity_authorized": False,
            "family_assignment_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
        },
    }
