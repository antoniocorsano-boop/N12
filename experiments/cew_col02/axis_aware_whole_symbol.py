from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


EXPECTED_SCHEMA_ID = "CEW_COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW"
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_REPAIR_TASKS = {
    "R01": "COL02-FP-0252",
    "R03": "COL02-FP-0073",
    "R04": "COL02-FP-0241",
    "R05": "COL02-FP-0261",
    "R06": "COL02-FP-0071",
}
EXPECTED_REJECTED_TASKS = {"R02": "COL02-FP-0106"}
CLOSED_AUTHORITY_KEYS = (
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


def load_axis_aware_repair_receipt(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_id") != EXPECTED_SCHEMA_ID or payload.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise ValueError("unexpected axis-aware repair receipt schema")

    authority = payload.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("repair receipt authority is missing")
    if authority.get("graphical_whole_symbol_repair_authorized") is not True:
        raise ValueError("graphical whole-symbol repair authority is not explicitly authorized")
    for key in CLOSED_AUTHORITY_KEYS:
        if authority.get(key) is not False:
            raise ValueError(f"repair receipt authority must remain closed: {key}")

    decisions = payload.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 6:
        raise ValueError("repair receipt must contain exactly six bounded decisions")
    by_task: dict[str, dict[str, Any]] = {}
    for row in decisions:
        task_id = str(row.get("review_task_id", ""))
        if not task_id or task_id in by_task:
            raise ValueError("repair receipt review task IDs must be unique")
        by_task[task_id] = row

    if set(by_task) != set(EXPECTED_REPAIR_TASKS) | set(EXPECTED_REJECTED_TASKS):
        raise ValueError("repair receipt task set drift")

    repair_candidate_ids: list[str] = []
    for task_id, candidate_id in EXPECTED_REPAIR_TASKS.items():
        row = by_task[task_id]
        if row.get("candidate_id") != candidate_id:
            raise ValueError(f"repair receipt candidate drift for {task_id}")
        if row.get("decision") != "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY":
            raise ValueError(f"repair receipt decision drift for {task_id}")
        if row.get("axis_partition_observed") is not True or row.get("repair_eligible") is not True:
            raise ValueError(f"repair receipt eligibility drift for {task_id}")
        repair_candidate_ids.append(candidate_id)

    rejected_candidate_ids: list[str] = []
    for task_id, candidate_id in EXPECTED_REJECTED_TASKS.items():
        row = by_task[task_id]
        if row.get("candidate_id") != candidate_id:
            raise ValueError(f"repair receipt candidate drift for {task_id}")
        if row.get("decision") != "MISLOCALIZED_NOT_COLUMN" or row.get("repair_eligible") is not False:
            raise ValueError(f"repair receipt rejection drift for {task_id}")
        rejected_candidate_ids.append(candidate_id)

    result = dict(payload)
    result["repair_candidate_ids"] = repair_candidate_ids
    result["rejected_candidate_ids"] = rejected_candidate_ids
    return result


def _pixel_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    intersection = ix * iy
    union = aw * ah + bw * bh - intersection
    return intersection / union if union > 0 else 0.0


def _edge_coverage(mask: np.ndarray, box: tuple[int, int, int, int], tolerance: int) -> dict[str, float]:
    x, y, width, height = box
    image_h, image_w = mask.shape[:2]
    right = x + width
    bottom = y + height
    t = max(1, int(tolerance))
    bands = {
        "left": mask[max(0, y):min(image_h, bottom), max(0, x - t):min(image_w, x + t + 1)],
        "right": mask[max(0, y):min(image_h, bottom), max(0, right - 1 - t):min(image_w, right + t)],
        "top": mask[max(0, y - t):min(image_h, y + t + 1), max(0, x):min(image_w, right)],
        "bottom": mask[max(0, bottom - 1 - t):min(image_h, bottom + t), max(0, x):min(image_w, right)],
    }
    coverage: dict[str, float] = {}
    for side, band in bands.items():
        if band.size == 0:
            coverage[side] = 0.0
        elif side in {"left", "right"}:
            coverage[side] = float(np.mean(np.any(band > 0, axis=1)))
        else:
            coverage[side] = float(np.mean(np.any(band > 0, axis=0)))
    return coverage


def _run_length_horizontal(mask: np.ndarray, x: int, y: int) -> int:
    row = mask[y] > 0
    if not row[x]:
        return 0
    left = x
    while left > 0 and row[left - 1]:
        left -= 1
    right = x
    while right + 1 < row.shape[0] and row[right + 1]:
        right += 1
    return right - left + 1


def _run_length_vertical(mask: np.ndarray, x: int, y: int) -> int:
    column = mask[:, x] > 0
    if not column[y]:
        return 0
    top = y
    while top > 0 and column[top - 1]:
        top -= 1
    bottom = y
    while bottom + 1 < column.shape[0] and column[bottom + 1]:
        bottom += 1
    return bottom - top + 1


def _near_duplicate_envelope(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    if _pixel_iou(a, b) < 0.80:
        return False
    _ax, _ay, aw, ah = a
    _bx, _by, bw, bh = b
    width_delta = abs(aw - bw) / max(aw, bw)
    height_delta = abs(ah - bh) / max(ah, bh)
    return width_delta <= 0.15 and height_delta <= 0.15


def _projection_bands(projection: np.ndarray, threshold: int) -> list[dict[str, int]]:
    indices = np.where(projection >= int(threshold))[0]
    if len(indices) == 0:
        return []
    bands: list[dict[str, int]] = []
    start = previous = int(indices[0])
    for raw in indices[1:]:
        value = int(raw)
        if value <= previous + 1:
            previous = value
            continue
        segment = projection[start:previous + 1]
        peak = start + int(np.argmax(segment))
        bands.append(
            {
                "position": peak,
                "start": start,
                "end": previous,
                "thickness": previous - start + 1,
                "support": int(segment.max()),
            }
        )
        start = previous = value
    segment = projection[start:previous + 1]
    peak = start + int(np.argmax(segment))
    bands.append(
        {
            "position": peak,
            "start": start,
            "end": previous,
            "thickness": previous - start + 1,
            "support": int(segment.max()),
        }
    )
    return bands


def _box_contains(outer: tuple[int, int, int, int], inner: tuple[int, int, int, int]) -> bool:
    ox, oy, ow, oh = outer
    ix, iy, iw, ih = inner
    tolerance = max(2, int(round(min(ow, oh) * 0.04)))
    return (
        ox <= ix + tolerance
        and oy <= iy + tolerance
        and ox + ow >= ix + iw - tolerance
        and oy + oh >= iy + ih - tolerance
    )


def _maximal_four_side_envelope_repair(
    *,
    closed: np.ndarray,
    seed_bbox: dict[str, float],
    seed_x: int,
    seed_y: int,
    seed_w: int,
    seed_h: int,
    width: int,
    height: int,
) -> dict[str, Any] | None:
    """Recover the outer graphical rectangle when local axes create nested sub-rectangles.

    This fallback does not infer structural identity. It searches only for four
    strongly supported graphical sides around the already human-authorized seed,
    removes nested sub-envelopes generated by internal axes, and fails closed if
    more than one materially different maximal envelope remains.
    """

    min_segment = max(9, int(round(min(seed_w, seed_h) * 0.25)))
    horizontal_lines = cv2.morphologyEx(
        closed,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (min_segment, 1)),
    )
    vertical_lines = cv2.morphologyEx(
        closed,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, min_segment)),
    )
    horizontal_projection = np.sum(horizontal_lines > 0, axis=1)
    vertical_projection = np.sum(vertical_lines > 0, axis=0)
    horizontal_bands = _projection_bands(
        horizontal_projection,
        max(min_segment, int(round(seed_w * 0.25))),
    )
    vertical_bands = _projection_bands(
        vertical_projection,
        max(min_segment, int(round(seed_h * 0.25))),
    )
    if len(horizontal_bands) < 2 or len(vertical_bands) < 2:
        return None

    seed_center_x = seed_x + seed_w / 2.0
    seed_center_y = seed_y + seed_h / 2.0
    max_local_side = min(
        int(round(min(width, height) * 0.30)),
        max(40, int(round(max(seed_w, seed_h) * 4.0))),
    )
    candidates: list[dict[str, Any]] = []

    for top_band in horizontal_bands:
        for bottom_band in horizontal_bands:
            top = int(top_band["position"])
            bottom = int(bottom_band["position"])
            if bottom <= top or not (top <= seed_center_y <= bottom):
                continue
            box_h = bottom - top + 1
            if box_h < max(5, int(round(seed_h * 0.40))) or box_h > max_local_side:
                continue
            for left_band in vertical_bands:
                for right_band in vertical_bands:
                    left = int(left_band["position"])
                    right = int(right_band["position"])
                    if right <= left or not (left <= seed_center_x <= right):
                        continue
                    box_w = right - left + 1
                    if box_w < max(5, int(round(seed_w * 0.40))) or box_w > max_local_side:
                        continue
                    aspect = box_w / box_h
                    if aspect < 0.10 or aspect > 10.0:
                        continue

                    overlap_w = max(0, min(right + 1, seed_x + seed_w) - max(left, seed_x))
                    overlap_h = max(0, min(bottom + 1, seed_y + seed_h) - max(top, seed_y))
                    overlap_fraction = (overlap_w * overlap_h) / max(1, seed_w * seed_h)
                    if overlap_fraction < 0.35:
                        continue
                    if box_w * box_h <= seed_w * seed_h * 1.02:
                        continue

                    tolerance = max(2, int(round(min(box_w, box_h) * 0.03)))
                    coverage = _edge_coverage(closed, (left, top, box_w, box_h), tolerance)
                    if min(coverage.values()) < 0.80:
                        continue

                    margin = max(2, int(round(min(box_w, box_h) * 0.10)))
                    interior_horizontal: list[tuple[float, dict[str, int]]] = []
                    for band in horizontal_bands:
                        y = int(band["position"])
                        if not (top + margin < y < bottom - margin):
                            continue
                        sample = horizontal_lines[
                            max(0, y - 1):min(height, y + 2),
                            left:right + 1,
                        ]
                        support = float(np.mean(np.any(sample > 0, axis=0))) if sample.size else 0.0
                        if support >= 0.15:
                            interior_horizontal.append((support, band))

                    interior_vertical: list[tuple[float, dict[str, int]]] = []
                    for band in vertical_bands:
                        x = int(band["position"])
                        if not (left + margin < x < right - margin):
                            continue
                        sample = vertical_lines[
                            top:bottom + 1,
                            max(0, x - 1):min(width, x + 2),
                        ]
                        support = float(np.mean(np.any(sample > 0, axis=1))) if sample.size else 0.0
                        if support >= 0.15:
                            interior_vertical.append((support, band))

                    if not interior_horizontal or not interior_vertical:
                        continue
                    best_horizontal = max(interior_horizontal, key=lambda row: row[0])
                    best_vertical = max(interior_vertical, key=lambda row: row[0])
                    candidates.append(
                        {
                            "box": (left, top, box_w, box_h),
                            "area": box_w * box_h,
                            "coverage": coverage,
                            "horizontal_axis_support": best_horizontal[0],
                            "horizontal_axis_band": best_horizontal[1],
                            "vertical_axis_support": best_vertical[0],
                            "vertical_axis_band": best_vertical[1],
                            "seed_overlap_fraction": overlap_fraction,
                        }
                    )

    unique: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=lambda row: int(row["area"]), reverse=True):
        if any(_near_duplicate_envelope(candidate["box"], existing["box"]) for existing in unique):
            continue
        unique.append(candidate)

    maximal: list[dict[str, Any]] = []
    for candidate in unique:
        if any(
            int(other["area"]) > int(candidate["area"]) * 1.08
            and _box_contains(other["box"], candidate["box"])
            for other in unique
        ):
            continue
        maximal.append(candidate)
    if len(maximal) != 1:
        return None

    chosen = maximal[0]
    x, y, box_w, box_h = chosen["box"]
    horizontal_band = chosen["horizontal_axis_band"]
    vertical_band = chosen["vertical_axis_band"]
    cross_x = float(vertical_band["position"])
    cross_y = float(horizontal_band["position"])
    return {
        "schema": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR_v1",
        "bbox": {
            "x": x / width,
            "y": y / height,
            "width": box_w / width,
            "height": box_h / height,
        },
        "seed_bbox": dict(seed_bbox),
        "axis_cross": {"x": cross_x / width, "y": cross_y / height},
        "axis_thickness_px": {
            "horizontal": int(horizontal_band["thickness"]),
            "vertical": int(vertical_band["thickness"]),
        },
        "axis_run_length_px": {
            "horizontal": int(horizontal_band["support"]),
            "vertical": int(vertical_band["support"]),
        },
        "boundary_side_count": 4,
        "boundary_coverage": dict(chosen["coverage"]),
        "seed_overlap_fraction": float(chosen["seed_overlap_fraction"]),
        "detector": "MAXIMAL_FOUR_SIDE_ENVELOPE_REPAIR",
        "support_identity": None,
        "structural_identity": None,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
    }


def reconstruct_axis_split_whole_symbol(
    image: np.ndarray,
    seed_bbox: dict[str, float],
) -> dict[str, Any] | None:
    """Reconstruct one review-only whole graphical symbol around axis partitions.

    The function is intentionally seeded: it may only repair geometry already
    classified by Human Review as an axis-fragmented graphical column symbol.
    It never assigns support or structural identity and fails closed when the
    source raster does not yield one unambiguous four-side envelope.
    """

    if image is None or not isinstance(image, np.ndarray) or image.ndim != 2 or image.size == 0:
        raise ValueError("image must be a non-empty grayscale numpy array")
    required = {"x", "y", "width", "height"}
    if set(seed_bbox) != required:
        raise ValueError("seed_bbox must contain x, y, width and height")
    if any(float(seed_bbox[key]) < 0.0 for key in required):
        raise ValueError("seed_bbox values must be non-negative")
    if float(seed_bbox["width"]) <= 0.0 or float(seed_bbox["height"]) <= 0.0:
        raise ValueError("seed_bbox must have positive area")
    if float(seed_bbox["x"]) + float(seed_bbox["width"]) > 1.0 or float(seed_bbox["y"]) + float(seed_bbox["height"]) > 1.0:
        raise ValueError("seed_bbox must lie inside normalized source bounds")

    original_h, original_w = image.shape[:2]
    if min(original_w, original_h) >= 1200:
        work = cv2.resize(
            image,
            (max(1, original_w // 2), max(1, original_h // 2)),
            interpolation=cv2.INTER_AREA,
        )
    else:
        work = image.copy()
    height, width = work.shape[:2]

    seed_x = int(round(float(seed_bbox["x"]) * width))
    seed_y = int(round(float(seed_bbox["y"]) * height))
    seed_w = max(1, int(round(float(seed_bbox["width"]) * width)))
    seed_h = max(1, int(round(float(seed_bbox["height"]) * height)))
    seed_center_x = seed_x + seed_w / 2.0
    seed_center_y = seed_y + seed_h / 2.0

    blurred = cv2.GaussianBlur(work, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    fallback_kwargs = {
        "closed": closed,
        "seed_bbox": seed_bbox,
        "seed_x": seed_x,
        "seed_y": seed_y,
        "seed_w": seed_w,
        "seed_h": seed_h,
        "width": width,
        "height": height,
    }

    # First retain the stricter v1 repair path for page-scale axes.
    page_axis_run = max(
        61,
        int(round(max(seed_w, seed_h) * 3.0)),
        int(round(min(width, height) * 0.12)),
    )
    page_axis_run = min(page_axis_run, max(61, int(round(min(width, height) * 0.50))))
    horizontal_axes = cv2.morphologyEx(
        closed,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (page_axis_run, 1)),
    )
    vertical_axes = cv2.morphologyEx(
        closed,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, page_axis_run)),
    )
    cross_mask = cv2.bitwise_and(horizontal_axes, vertical_axes)
    count, _labels, stats, centroids = cv2.connectedComponentsWithStats(
        (cross_mask > 0).astype(np.uint8),
        8,
    )

    crossing_candidates: list[dict[str, float | int]] = []
    search_radius = max(page_axis_run, int(round(max(seed_w, seed_h) * 2.5)))
    for component in range(1, count):
        _x, _y, cross_w, cross_h, _area = stats[component]
        cross_x, cross_y = centroids[component]
        if abs(cross_x - seed_center_x) > search_radius or abs(cross_y - seed_center_y) > search_radius:
            continue
        px = max(0, min(width - 1, int(round(cross_x))))
        py = max(0, min(height - 1, int(round(cross_y))))
        horizontal_run = _run_length_horizontal(horizontal_axes, px, py)
        vertical_run = _run_length_vertical(vertical_axes, px, py)
        if horizontal_run < page_axis_run or vertical_run < page_axis_run:
            continue
        crossing_candidates.append(
            {
                "x": float(cross_x),
                "y": float(cross_y),
                "width": int(cross_w),
                "height": int(cross_h),
                "horizontal_run": int(horizontal_run),
                "vertical_run": int(vertical_run),
                "strength": int(horizontal_run * vertical_run),
            }
        )
    if not crossing_candidates:
        return _maximal_four_side_envelope_repair(**fallback_kwargs)

    strongest = max(int(row["strength"]) for row in crossing_candidates)
    comparable = [row for row in crossing_candidates if int(row["strength"]) >= strongest * 0.80]
    comparable.sort(
        key=lambda row: (
            (float(row["x"]) - seed_center_x) ** 2 + (float(row["y"]) - seed_center_y) ** 2,
            -int(row["strength"]),
        )
    )
    crossing = comparable[0]
    cross_x = float(crossing["x"])
    cross_y = float(crossing["y"])
    cross_w = int(crossing["width"])
    cross_h = int(crossing["height"])

    axis_suppressed = cv2.subtract(closed, cv2.bitwise_or(horizontal_axes, vertical_axes))
    bridge_x = max(5, cross_w * 2 + 3)
    bridge_y = max(5, cross_h * 2 + 3)
    repaired = cv2.morphologyEx(
        axis_suppressed,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (bridge_x, 1)),
    )
    repaired = cv2.morphologyEx(
        repaired,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, bridge_y)),
    )
    repaired = cv2.morphologyEx(repaired, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(repaired, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    max_local_side = min(
        int(round(min(width, height) * 0.30)),
        max(40, int(round(max(seed_w, seed_h) * 4.0))),
    )
    envelope_candidates: list[tuple[tuple[int, int, int, int], dict[str, float]]] = []
    for contour in contours:
        x, y, box_w, box_h = cv2.boundingRect(contour)
        if box_w < 5 or box_h < 5 or box_w > max_local_side or box_h > max_local_side:
            continue
        if not (x < cross_x < x + box_w and y < cross_y < y + box_h):
            continue
        overlap_w = max(0, min(x + box_w, seed_x + seed_w) - max(x, seed_x))
        overlap_h = max(0, min(y + box_h, seed_y + seed_h) - max(y, seed_y))
        if overlap_w * overlap_h <= 0:
            continue
        if box_w * box_h <= seed_w * seed_h * 1.05:
            continue
        tolerance = max(2, int(round(min(box_w, box_h) * 0.06)))
        coverage = _edge_coverage(closed, (x, y, box_w, box_h), tolerance)
        if min(coverage.values()) < 0.45:
            continue
        envelope_candidates.append(((x, y, box_w, box_h), coverage))

    unique_envelopes: list[tuple[tuple[int, int, int, int], dict[str, float]]] = []
    for candidate in sorted(
        envelope_candidates,
        key=lambda row: row[0][2] * row[0][3],
        reverse=True,
    ):
        if any(_near_duplicate_envelope(candidate[0], existing[0]) for existing in unique_envelopes):
            continue
        unique_envelopes.append(candidate)

    if len(unique_envelopes) != 1:
        return _maximal_four_side_envelope_repair(**fallback_kwargs)

    (x, y, box_w, box_h), coverage = unique_envelopes[0]
    return {
        "schema": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR_v1",
        "bbox": {
            "x": x / width,
            "y": y / height,
            "width": box_w / width,
            "height": box_h / height,
        },
        "seed_bbox": dict(seed_bbox),
        "axis_cross": {"x": cross_x / width, "y": cross_y / height},
        "axis_thickness_px": {
            "horizontal": cross_h,
            "vertical": cross_w,
        },
        "axis_run_length_px": {
            "horizontal": int(crossing["horizontal_run"]),
            "vertical": int(crossing["vertical_run"]),
        },
        "boundary_side_count": 4,
        "boundary_coverage": coverage,
        "detector": "AXIS_AWARE_WHOLE_SYMBOL_REPAIR",
        "support_identity": None,
        "structural_identity": None,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
    }
