from __future__ import annotations

from typing import Any

import cv2
import numpy as np


SUPPORTED_FINDING = "TOP_TRUNCATED_INTERNAL_LINE_SELECTED"
TARGET_REPAIR_ID = "COL02-WSR-003"
TARGET_SOURCE_CANDIDATE_ID = "COL02-FP-0241"

_CLOSED_AUTHORITY_KEYS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "structural_identity_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)


def authorized_completion_requests(receipt: dict[str, Any]) -> dict[str, str]:
    """Return the single bounded review-directed completion authorized by the receipt."""

    if receipt.get("schema_id") != "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW" or receipt.get("schema_version") != 1:
        raise ValueError("unexpected graphical review receipt schema")
    if receipt.get("review_scope") != "graphical_whole_symbol_geometry_only":
        raise ValueError("unexpected graphical review scope")

    authority = receipt.get("authority")
    if not isinstance(authority, dict) or authority.get("graphical_review_record_authorized") is not True:
        raise ValueError("graphical review authority is not explicit")
    for key in _CLOSED_AUTHORITY_KEYS:
        if authority.get(key) is not False:
            raise ValueError(f"graphical review authority drift: {key}")

    decisions = receipt.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("graphical review decisions are missing")

    authorized: dict[str, str] = {}
    seen_repairs: set[str] = set()
    seen_candidates: set[str] = set()
    for row in decisions:
        if not isinstance(row, dict):
            raise ValueError("invalid graphical review decision")
        repair_id = str(row.get("repair_id", ""))
        candidate_id = str(row.get("source_candidate_id", ""))
        if not repair_id or not candidate_id or repair_id in seen_repairs or candidate_id in seen_candidates:
            raise ValueError("graphical review decision identity drift")
        seen_repairs.add(repair_id)
        seen_candidates.add(candidate_id)

        finding = str(row.get("finding", ""))
        if row.get("decision") != "REWORK" or finding != SUPPORTED_FINDING:
            continue
        if repair_id != TARGET_REPAIR_ID or candidate_id != TARGET_SOURCE_CANDIDATE_ID:
            raise ValueError("review-directed completion target drift")
        authorized[candidate_id] = finding

    if authorized != {TARGET_SOURCE_CANDIDATE_ID: SUPPORTED_FINDING}:
        raise ValueError("expected review-directed completion authorization is missing")
    return authorized


def _bands_from_boolean(values: np.ndarray) -> list[tuple[int, int]]:
    indices = np.where(values)[0]
    if len(indices) == 0:
        return []
    bands: list[tuple[int, int]] = []
    start = previous = int(indices[0])
    for raw in indices[1:]:
        value = int(raw)
        if value <= previous + 1:
            previous = value
            continue
        bands.append((start, previous))
        start = previous = value
    bands.append((start, previous))
    return bands


def complete_review_directed_outer_envelope(
    image: np.ndarray,
    base_result: dict[str, Any],
    *,
    finding: str,
) -> dict[str, Any] | None:
    """Complete only a review-authorized missing top edge; fail closed on ambiguity."""

    if finding != SUPPORTED_FINDING:
        return None
    if image is None or not isinstance(image, np.ndarray) or image.ndim != 2 or image.size == 0:
        raise ValueError("image must be a non-empty grayscale numpy array")

    bbox = base_result.get("bbox")
    coverage = base_result.get("boundary_coverage")
    if not isinstance(bbox, dict) or set(bbox) != {"x", "y", "width", "height"}:
        raise ValueError("base_result bbox is missing or malformed")
    if not isinstance(coverage, dict):
        return None
    if min(float(coverage.get(side, 0.0)) for side in ("left", "right", "bottom")) < 0.80:
        return None

    image_h, image_w = image.shape[:2]
    x1 = int(round(float(bbox["x"]) * image_w))
    y1 = int(round(float(bbox["y"]) * image_h))
    x2 = int(round((float(bbox["x"]) + float(bbox["width"])) * image_w))
    y2 = int(round((float(bbox["y"]) + float(bbox["height"])) * image_h))
    x1 = max(0, min(image_w - 1, x1))
    y1 = max(0, min(image_h - 1, y1))
    x2 = max(x1 + 1, min(image_w, x2))
    y2 = max(y1 + 1, min(image_h, y2))

    box_w = x2 - x1
    box_h = y2 - y1
    if box_w < 5 or box_h < 5:
        return None

    maximum_extension = max(12, min(int(round(box_h * 1.25)), max(box_h, box_w)))
    search_top = max(0, y1 - maximum_extension)
    search_bottom = max(search_top, y1 - max(4, int(round(box_h * 0.06))))
    if search_bottom <= search_top:
        return None

    blurred = cv2.GaussianBlur(image, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    closed = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)),
        iterations=1,
    )
    horizontal_run = max(9, int(round(box_w * 0.35)))
    horizontal_lines = cv2.morphologyEx(
        closed,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_run, 1)),
    )

    search_strip = horizontal_lines[search_top:search_bottom, x1:x2]
    if search_strip.size == 0:
        return None
    row_coverage = np.mean(search_strip > 0, axis=1)
    candidate_bands = _bands_from_boolean(row_coverage >= 0.55)
    if not candidate_bands:
        return None

    tolerance = max(2, int(round(min(box_w, box_h) * 0.04)))

    def horizontal_coverage(position: int) -> float:
        sample = horizontal_lines[
            max(0, position - tolerance) : min(image_h, position + tolerance + 1),
            x1:x2,
        ]
        return float(np.mean(np.any(sample > 0, axis=0))) if sample.size else 0.0

    def vertical_closure(position: int, top: int) -> float:
        sample = closed[
            top:y2,
            max(0, position - tolerance) : min(image_w, position + tolerance + 1),
        ]
        return float(np.mean(np.any(sample > 0, axis=1))) if sample.size else 0.0

    bottom_sample = closed[
        max(0, y2 - 1 - tolerance) : min(image_h, y2 + tolerance),
        x1:x2,
    ]
    bottom_coverage = float(np.mean(np.any(bottom_sample > 0, axis=0))) if bottom_sample.size else 0.0
    if bottom_coverage < 0.70:
        return None

    candidates: list[dict[str, float | int]] = []
    for start, end in candidate_bands:
        segment = row_coverage[start : end + 1]
        position = search_top + start + int(np.argmax(segment))
        top_coverage = horizontal_coverage(position)
        left_closure = vertical_closure(x1, position)
        right_closure = vertical_closure(x2 - 1, position)
        if top_coverage < 0.60 or left_closure < 0.70 or right_closure < 0.70:
            continue
        minimum = min(top_coverage, left_closure, right_closure, bottom_coverage)
        mean = (top_coverage + left_closure + right_closure + bottom_coverage) / 4.0
        candidates.append(
            {
                "position": position,
                "top": top_coverage,
                "left": left_closure,
                "right": right_closure,
                "bottom": bottom_coverage,
                "score": minimum + 0.10 * mean,
            }
        )

    if not candidates:
        return None
    candidates.sort(key=lambda row: float(row["score"]), reverse=True)
    best = candidates[0]
    separation = max(3, int(round(box_h * 0.08)))
    for competing in candidates[1:]:
        if (
            abs(int(competing["position"]) - int(best["position"])) > separation
            and float(best["score"]) - float(competing["score"]) <= 0.05
        ):
            return None

    completed_top = int(best["position"])
    if completed_top >= y1:
        return None

    base_bottom = float(bbox["y"]) + float(bbox["height"])
    completed_y = completed_top / image_h
    completed_height = base_bottom - completed_y
    if completed_height <= float(bbox["height"]):
        return None

    result = dict(base_result)
    result["bbox"] = {
        "x": float(bbox["x"]),
        "y": completed_y,
        "width": float(bbox["width"]),
        "height": completed_height,
    }
    result["boundary_side_count"] = 4
    result["boundary_coverage"] = {
        "left": float(best["left"]),
        "right": float(best["right"]),
        "top": float(best["top"]),
        "bottom": float(best["bottom"]),
    }
    result["detector"] = "REVIEW_DIRECTED_OUTER_ENVELOPE_COMPLETION"
    result["review_directed_completion"] = {
        "finding": finding,
        "completed_side": "top",
        "frozen_sides": ["left", "right", "bottom"],
        "original_top_px": y1,
        "completed_top_px": completed_top,
        "search_top_px": search_top,
        "search_bottom_px": search_bottom,
        "top_edge_coverage": float(best["top"]),
        "left_closure_coverage": float(best["left"]),
        "right_closure_coverage": float(best["right"]),
        "bottom_edge_coverage": float(best["bottom"]),
    }
    result["canonical_geometry_authorized"] = False
    result["canonical_write_authorized"] = False
    return result
