from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def _projection_bands(projection: np.ndarray, threshold: int) -> list[dict[str, int]]:
    indices = np.where(projection >= threshold)[0]
    if len(indices) == 0:
        return []
    bands: list[dict[str, int]] = []
    start = previous = int(indices[0])
    for raw in indices[1:]:
        value = int(raw)
        if value <= previous + 1:
            previous = value
            continue
        segment = projection[start : previous + 1]
        peak = start + int(np.argmax(segment))
        bands.append(
            {
                "position": peak,
                "start": start,
                "end": previous,
                "support": int(segment.max()),
            }
        )
        start = previous = value
    segment = projection[start : previous + 1]
    peak = start + int(np.argmax(segment))
    bands.append(
        {
            "position": peak,
            "start": start,
            "end": previous,
            "support": int(segment.max()),
        }
    )
    return bands


def _edge_coverage(mask: np.ndarray, box: tuple[int, int, int, int], tolerance: int) -> dict[str, float]:
    x, y, width, height = box
    image_h, image_w = mask.shape[:2]
    right = x + width
    bottom = y + height
    t = max(1, tolerance)
    bands = {
        "left": mask[max(0, y) : min(image_h, bottom), max(0, x - t) : min(image_w, x + t + 1)],
        "right": mask[max(0, y) : min(image_h, bottom), max(0, right - 1 - t) : min(image_w, right + t)],
        "top": mask[max(0, y - t) : min(image_h, y + t + 1), max(0, x) : min(image_w, right)],
        "bottom": mask[max(0, bottom - 1 - t) : min(image_h, bottom + t), max(0, x) : min(image_w, right)],
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


def _contained(inner: tuple[int, int, int, int], outer: tuple[int, int, int, int], tolerance: int = 2) -> bool:
    ix, iy, iw, ih = inner
    ox, oy, ow, oh = outer
    return (
        ix >= ox - tolerance
        and iy >= oy - tolerance
        and ix + iw <= ox + ow + tolerance
        and iy + ih <= oy + oh + tolerance
    )


def _near_duplicate(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    intersection = ix * iy
    union = aw * ah + bw * bh - intersection
    iou = intersection / union if union else 0.0
    return (
        iou >= 0.80
        and abs(aw - bw) / max(aw, bw) <= 0.15
        and abs(ah - bh) / max(ah, bh) <= 0.15
    )


def reconstruct_local_axis_envelope(
    image: np.ndarray,
    seed_bbox: dict[str, float],
) -> dict[str, Any] | None:
    """Recover one local four-side envelope around a reviewed fragmented seed.

    This is a bounded graphical fallback. It uses only raster geometry around the
    supplied seed: four-side boundary continuity plus one interior horizontal and
    one interior vertical line. It does not infer support identity, section,
    family, structural identity, or canonical geometry and fails closed on a
    materially different near-tie.
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

    margin = min(420, max(90, int(round(max(seed_w, seed_h) * 3.0))))
    local_left = max(0, seed_x - margin)
    local_top = max(0, seed_y - margin)
    local_right = min(width, seed_x + seed_w + margin)
    local_bottom = min(height, seed_y + seed_h + margin)
    local = work[local_top:local_bottom, local_left:local_right]
    if local.size == 0:
        return None

    sx1 = seed_x - local_left
    sy1 = seed_y - local_top
    sx2 = sx1 + seed_w
    sy2 = sy1 + seed_h

    blurred = cv2.GaussianBlur(local, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

    line_run = max(9, int(round(min(seed_w, seed_h) * 0.22)))
    horizontal_lines = cv2.morphologyEx(
        closed,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (line_run, 1)),
    )
    vertical_lines = cv2.morphologyEx(
        closed,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, line_run)),
    )
    horizontal_bands = _projection_bands(np.sum(horizontal_lines > 0, axis=1), line_run)
    vertical_bands = _projection_bands(np.sum(vertical_lines > 0, axis=0), line_run)
    if len(horizontal_bands) < 3 or len(vertical_bands) < 3:
        return None

    max_side = min(max(local.shape[:2]), max(40, int(round(max(seed_w, seed_h) * 4.5))))
    min_height = max(5, min(20, int(round(seed_h * 0.45))))
    min_width = max(5, min(20, int(round(seed_w * 0.45))))
    seed_area = float(seed_w * seed_h)
    candidates: list[dict[str, Any]] = []

    for top_index, top_band in enumerate(horizontal_bands):
        for bottom_band in horizontal_bands[top_index + 1 :]:
            y1 = int(top_band["position"])
            y2 = int(bottom_band["position"])
            box_h = y2 - y1 + 1
            if box_h < min_height or box_h > max_side:
                continue
            overlap_h = max(0, min(y2 + 1, sy2) - max(y1, sy1))
            if overlap_h / seed_h < 0.25:
                continue

            for left_index, left_band in enumerate(vertical_bands):
                for right_band in vertical_bands[left_index + 1 :]:
                    x1 = int(left_band["position"])
                    x2 = int(right_band["position"])
                    box_w = x2 - x1 + 1
                    if box_w < min_width or box_w > max_side:
                        continue
                    overlap_w = max(0, min(x2 + 1, sx2) - max(x1, sx1))
                    seed_overlap = (overlap_w * overlap_h) / seed_area
                    if seed_overlap < 0.28:
                        continue
                    if box_w * box_h <= seed_area * 1.02:
                        continue
                    aspect_ratio = box_w / box_h
                    if aspect_ratio < 0.10 or aspect_ratio > 10.0:
                        continue

                    tolerance = max(2, int(round(min(box_w, box_h) * 0.035)))
                    coverage = _edge_coverage(closed, (x1, y1, box_w, box_h), tolerance)
                    if min(coverage.values()) < 0.35:
                        continue

                    interior_margin = max(2, int(round(min(box_w, box_h) * 0.08)))
                    interior_horizontal: list[tuple[float, dict[str, int]]] = []
                    for band in horizontal_bands:
                        position = int(band["position"])
                        if not (y1 + interior_margin < position < y2 - interior_margin):
                            continue
                        sample = horizontal_lines[
                            max(0, position - 1) : min(local.shape[0], position + 2),
                            x1 : x2 + 1,
                        ]
                        support = float(np.mean(np.any(sample > 0, axis=0))) if sample.size else 0.0
                        if support >= 0.12:
                            interior_horizontal.append((support, band))

                    interior_vertical: list[tuple[float, dict[str, int]]] = []
                    for band in vertical_bands:
                        position = int(band["position"])
                        if not (x1 + interior_margin < position < x2 - interior_margin):
                            continue
                        sample = vertical_lines[
                            y1 : y2 + 1,
                            max(0, position - 1) : min(local.shape[1], position + 2),
                        ]
                        support = float(np.mean(np.any(sample > 0, axis=1))) if sample.size else 0.0
                        if support >= 0.12:
                            interior_vertical.append((support, band))

                    if not interior_horizontal or not interior_vertical:
                        continue
                    horizontal_axis = max(interior_horizontal, key=lambda item: item[0])
                    vertical_axis = max(interior_vertical, key=lambda item: item[0])
                    minimum_boundary = min(coverage.values())
                    mean_boundary = sum(coverage.values()) / 4.0
                    axis_support = min(horizontal_axis[0], vertical_axis[0])
                    score = (
                        0.50 * minimum_boundary
                        + 0.25 * mean_boundary
                        + 0.15 * axis_support
                        + 0.10 * seed_overlap
                    )
                    candidates.append(
                        {
                            "score": score,
                            "box": (x1, y1, box_w, box_h),
                            "coverage": coverage,
                            "seed_overlap": seed_overlap,
                            "horizontal_axis": horizontal_axis,
                            "vertical_axis": vertical_axis,
                        }
                    )

    if not candidates:
        return None
    candidates.sort(key=lambda row: float(row["score"]), reverse=True)
    unique: list[dict[str, Any]] = []
    for candidate in candidates:
        if any(_near_duplicate(candidate["box"], existing["box"]) for existing in unique):
            continue
        unique.append(candidate)

    if not unique:
        return None
    chosen = unique[0]
    for competing in unique[1:]:
        if float(competing["score"]) < float(chosen["score"]) - 0.08:
            break
        if _contained(competing["box"], chosen["box"]) or _contained(chosen["box"], competing["box"]):
            continue
        return None

    x, y, box_w, box_h = chosen["box"]
    horizontal_support, horizontal_band = chosen["horizontal_axis"]
    vertical_support, vertical_band = chosen["vertical_axis"]
    global_x = x + local_left
    global_y = y + local_top
    cross_x = int(vertical_band["position"]) + local_left
    cross_y = int(horizontal_band["position"]) + local_top
    return {
        "schema": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR_v1",
        "bbox": {
            "x": global_x / width,
            "y": global_y / height,
            "width": box_w / width,
            "height": box_h / height,
        },
        "seed_bbox": dict(seed_bbox),
        "axis_cross": {"x": cross_x / width, "y": cross_y / height},
        "axis_thickness_px": {
            "horizontal": int(horizontal_band["end"]) - int(horizontal_band["start"]) + 1,
            "vertical": int(vertical_band["end"]) - int(vertical_band["start"]) + 1,
        },
        "axis_run_length_px": {
            "horizontal": int(horizontal_band["support"]),
            "vertical": int(vertical_band["support"]),
        },
        "boundary_side_count": 4,
        "boundary_coverage": dict(chosen["coverage"]),
        "seed_overlap_fraction": float(chosen["seed_overlap"]),
        "repair_score": float(chosen["score"]),
        "interior_axis_support": {
            "horizontal": float(horizontal_support),
            "vertical": float(vertical_support),
        },
        "detector": "LOCAL_AXIS_AWARE_FOUR_SIDE_ENVELOPE_REPAIR",
        "support_identity": None,
        "structural_identity": None,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
    }
