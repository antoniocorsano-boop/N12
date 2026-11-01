from __future__ import annotations

from math import hypot
from typing import Any, Iterable, Sequence


_ALLOWED_ROTATIONS = {0, 90, 180, 270}


def _axis_starts(start: int, stop: int, tile_size: int, overlap: int) -> list[int]:
    length = stop - start
    if start < 0 or stop <= start or tile_size <= 0 or overlap < 0 or overlap >= tile_size:
        raise ValueError("CAL01_REFINEMENT_TILE_GEOMETRY_INVALID")
    if length <= tile_size:
        return [start]
    step = tile_size - overlap
    starts = list(range(start, stop - tile_size + 1, step))
    last = stop - tile_size
    if starts[-1] != last:
        starts.append(last)
    return starts


def generate_tile_windows(
    *,
    page_width: int,
    page_height: int,
    roi_px: Sequence[int | float],
    tile_width: int,
    tile_height: int,
    overlap: int,
) -> list[list[int]]:
    """Generate deterministic overlapping tiles inside an explicit source ROI.

    The ROI is only a processing boundary. It does not carry engineering or
    calibration authority and every result must still be mapped to page space.
    """

    if page_width <= 0 or page_height <= 0 or len(roi_px) != 4:
        raise ValueError("CAL01_REFINEMENT_ROI_INVALID")
    left, top, right, bottom = (int(round(float(value))) for value in roi_px)
    if left < 0 or top < 0 or right > page_width or bottom > page_height or right <= left or bottom <= top:
        raise ValueError("CAL01_REFINEMENT_ROI_INVALID")
    if tile_width <= 0 or tile_height <= 0:
        raise ValueError("CAL01_REFINEMENT_TILE_GEOMETRY_INVALID")

    xs = _axis_starts(left, right, tile_width, overlap)
    ys = _axis_starts(top, bottom, tile_height, overlap)
    return [
        [x, y, min(right, x + tile_width), min(bottom, y + tile_height)]
        for y in ys
        for x in xs
    ]


def _inverse_rotated_point(
    x: float,
    y: float,
    *,
    width: float,
    height: float,
    rotation_deg: int,
) -> tuple[float, float]:
    rotation = int(rotation_deg) % 360
    if rotation not in _ALLOWED_ROTATIONS:
        raise ValueError("CAL01_REFINEMENT_ROTATION_UNSUPPORTED")
    if rotation == 0:
        return x, y
    if rotation == 90:
        return y, height - x
    if rotation == 180:
        return width - x, height - y
    return width - y, x


def backproject_rotated_bbox(
    bbox_px: Sequence[int | float],
    *,
    tile_bbox_px: Sequence[int | float],
    rotation_deg: int,
    ocr_scale: float = 1.0,
) -> list[float]:
    """Map an OCR bbox from a rotated/upscaled tile to the original page frame."""

    if len(bbox_px) != 4 or len(tile_bbox_px) != 4 or ocr_scale <= 0:
        raise ValueError("CAL01_REFINEMENT_BBOX_INVALID")
    tile_left, tile_top, tile_right, tile_bottom = (float(value) for value in tile_bbox_px)
    width = tile_right - tile_left
    height = tile_bottom - tile_top
    if width <= 0 or height <= 0:
        raise ValueError("CAL01_REFINEMENT_BBOX_INVALID")

    left, top, right, bottom = (float(value) / float(ocr_scale) for value in bbox_px)
    if right <= left or bottom <= top:
        raise ValueError("CAL01_REFINEMENT_BBOX_INVALID")

    corners = [
        _inverse_rotated_point(left, top, width=width, height=height, rotation_deg=rotation_deg),
        _inverse_rotated_point(right, top, width=width, height=height, rotation_deg=rotation_deg),
        _inverse_rotated_point(left, bottom, width=width, height=height, rotation_deg=rotation_deg),
        _inverse_rotated_point(right, bottom, width=width, height=height, rotation_deg=rotation_deg),
    ]
    xs = [point[0] + tile_left for point in corners]
    ys = [point[1] + tile_top for point in corners]
    return [min(xs), min(ys), max(xs), max(ys)]


def _centroid(bbox: Sequence[int | float]) -> tuple[float, float]:
    if len(bbox) != 4:
        raise ValueError("CAL01_REFINEMENT_BBOX_INVALID")
    left, top, right, bottom = (float(value) for value in bbox)
    if right <= left or bottom <= top:
        raise ValueError("CAL01_REFINEMENT_BBOX_INVALID")
    return (left + right) / 2.0, (top + bottom) / 2.0


def cluster_numeric_observations_by_location(
    observations: Iterable[dict[str, Any]],
    *,
    centroid_tolerance_px: float = 16.0,
) -> list[dict[str, Any]]:
    """Cluster OCR observations by source position before deciding numeric text.

    Unlike value-based deduplication, this stage intentionally keeps conflicting
    readings together when they refer to the same source location. The result is
    evidence for later OCR consensus; it does not repair digits or assign metric
    or engineering authority.
    """

    if centroid_tolerance_px < 0:
        raise ValueError("CAL01_REFINEMENT_CLUSTER_TOLERANCE_INVALID")

    ordered = sorted(
        (dict(item) for item in observations),
        key=lambda item: (
            _centroid(item["bbox_px"])[1],
            _centroid(item["bbox_px"])[0],
            str(item.get("raw_ocr_text") or ""),
            -float(item.get("ocr_confidence", 0.0)),
        ),
    )
    groups: list[dict[str, Any]] = []

    for item in ordered:
        raw_text = str(item.get("raw_ocr_text") or "").strip()
        if not raw_text:
            raise ValueError("CAL01_REFINEMENT_RAW_TEXT_REQUIRED")
        center = _centroid(item["bbox_px"])
        candidates: list[tuple[float, int, dict[str, Any]]] = []
        for index, group in enumerate(groups):
            gx, gy = group["cluster_centroid_px"]
            distance = hypot(center[0] - gx, center[1] - gy)
            if distance <= centroid_tolerance_px:
                candidates.append((distance, index, group))

        if not candidates:
            groups.append(
                {
                    "cluster_centroid_px": [center[0], center[1]],
                    "members": [item],
                }
            )
            continue

        _, _, matched = min(candidates, key=lambda value: (value[0], value[1]))
        matched["members"].append(item)
        centers = [_centroid(member["bbox_px"]) for member in matched["members"]]
        matched["cluster_centroid_px"] = [
            sum(value[0] for value in centers) / len(centers),
            sum(value[1] for value in centers) / len(centers),
        ]

    result: list[dict[str, Any]] = []
    for group in groups:
        members = group["members"]
        best = max(
            members,
            key=lambda item: (
                float(item.get("ocr_confidence", 0.0)),
                str(item.get("raw_ocr_text") or ""),
                -int(item.get("ocr_rotation_degrees", item.get("rotation_deg", 0))),
            ),
        )
        readings = sorted(str(member.get("raw_ocr_text") or "").strip() for member in members)
        rotations = sorted(
            {
                int(member.get("ocr_rotation_degrees", member.get("rotation_deg", 0))) % 360
                for member in members
            }
        )
        tile_ids = sorted(
            {
                str(member.get("tile_index", member.get("tile_id", "")))
                for member in members
            }
        )
        result.append(
            {
                "cluster_centroid_px": list(group["cluster_centroid_px"]),
                "observation_count": len(members),
                "readings": readings,
                "observed_rotations_deg": rotations,
                "supporting_tile_ids": tile_ids,
                "representative": dict(best),
                "primary_anchor_authorized": False,
                "canonical_geometry_authorized": False,
                "engineering_authority_effect": "NONE",
            }
        )

    result.sort(
        key=lambda item: (
            item["cluster_centroid_px"][1],
            item["cluster_centroid_px"][0],
        )
    )
    return result


def deduplicate_metric_observations(
    observations: Iterable[dict[str, Any]],
    *,
    centroid_tolerance_px: float = 16.0,
) -> list[dict[str, Any]]:
    """Merge same-value OCR observations by true source-space proximity.

    The highest-confidence observation is retained as representative while all
    observed rotations/tile ids remain audit evidence. Conflicting numeric
    values are never merged here; they must be handled by the later consensus
    and document-role gate.
    """

    if centroid_tolerance_px < 0:
        raise ValueError("CAL01_REFINEMENT_DEDUP_TOLERANCE_INVALID")

    groups: list[dict[str, Any]] = []
    ordered = sorted(
        (dict(item) for item in observations),
        key=lambda item: (
            str(item.get("normalized_metric_text")),
            _centroid(item["bbox_px"])[1],
            _centroid(item["bbox_px"])[0],
            -float(item.get("ocr_confidence", 0.0)),
        ),
    )

    for item in ordered:
        text = str(item.get("normalized_metric_text") or "")
        if not text:
            raise ValueError("CAL01_REFINEMENT_TEXT_REQUIRED")
        center = _centroid(item["bbox_px"])
        matched = None
        for group in groups:
            if group["normalized_metric_text"] != text:
                continue
            gx, gy = group["cluster_centroid_px"]
            if hypot(center[0] - gx, center[1] - gy) <= centroid_tolerance_px:
                matched = group
                break

        if matched is None:
            groups.append(
                {
                    "normalized_metric_text": text,
                    "cluster_centroid_px": [center[0], center[1]],
                    "members": [item],
                }
            )
        else:
            matched["members"].append(item)
            centers = [_centroid(member["bbox_px"]) for member in matched["members"]]
            matched["cluster_centroid_px"] = [
                sum(value[0] for value in centers) / len(centers),
                sum(value[1] for value in centers) / len(centers),
            ]

    result: list[dict[str, Any]] = []
    for group in groups:
        members = group["members"]
        best = max(
            members,
            key=lambda item: (
                float(item.get("ocr_confidence", 0.0)),
                -int(item.get("rotation_deg", item.get("ocr_rotation_degrees", 0))),
            ),
        )
        enriched = dict(best)
        rotations = sorted(
            {
                int(member.get("rotation_deg", member.get("ocr_rotation_degrees", 0))) % 360
                for member in members
            }
        )
        tile_ids = sorted(
            {
                str(member.get("tile_id", member.get("tile_index", "")))
                for member in members
            }
        )
        enriched["supporting_observation_count"] = len(members)
        enriched["observed_rotations_deg"] = rotations
        enriched["supporting_tile_ids"] = tile_ids
        enriched["cluster_centroid_px"] = list(group["cluster_centroid_px"])
        result.append(enriched)

    result.sort(
        key=lambda item: (
            item["cluster_centroid_px"][1],
            item["cluster_centroid_px"][0],
            item["normalized_metric_text"],
        )
    )
    return result
