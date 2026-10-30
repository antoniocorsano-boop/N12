from __future__ import annotations

from math import hypot
from typing import Any

_RECT = "RECTILINEAR_CLOSED_SHAPE"
_LINE = "LINE_SEGMENT"


def _bbox(item: dict[str, Any]) -> tuple[float, float, float, float]:
    if "bbox" in item:
        box = item["bbox"]
        return (
            float(box["x"]),
            float(box["y"]),
            float(box["width"]),
            float(box["height"]),
        )
    return (
        float(item["x"]),
        float(item["y"]),
        float(item["width"]),
        float(item["height"]),
    )


def _center(box: tuple[float, float, float, float]) -> tuple[float, float]:
    x, y, width, height = box
    return x + width / 2.0, y + height / 2.0


def _point_to_box_distance(
    point: tuple[float, float], box: tuple[float, float, float, float]
) -> float:
    px, py = point
    x, y, width, height = box
    dx = max(x - px, 0.0, px - (x + width))
    dy = max(y - py, 0.0, py - (y + height))
    return hypot(dx, dy)


def _line_orientation(item: dict[str, Any]) -> str | None:
    signature = item.get("feature_signature") or {}
    value = signature.get("orientation")
    return str(value) if value in {"HORIZONTAL", "VERTICAL"} else None


def _line_length(item: dict[str, Any]) -> float:
    signature = item.get("feature_signature") or {}
    if "length_px" in signature:
        try:
            return float(signature["length_px"])
        except (TypeError, ValueError):
            pass
    _x, _y, width, height = _bbox(item)
    return max(width, height)


def _intersects(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
    *,
    pad: float = 0.0,
) -> bool:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    return not (
        ax + aw < bx - pad
        or bx + bw < ax - pad
        or ay + ah < by - pad
        or by + bh < ay - pad
    )


def _authority() -> dict[str, bool]:
    return {
        "semantic_classification_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "section_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


def _footprint_payload(item: dict[str, Any]) -> dict[str, Any]:
    x, y, width, height = _bbox(item)
    longer = max(width, height)
    shorter = max(1.0, min(width, height))
    ratio = longer / shorter
    if width / max(height, 1.0) >= 2.5:
        orientation = "HORIZONTAL_ELONGATED"
    elif height / max(width, 1.0) >= 2.5:
        orientation = "VERTICAL_ELONGATED"
    else:
        orientation = "RECTANGULAR"
    return {
        "primitive_id": item.get("primitive_id"),
        "bbox": {"x": x, "y": y, "width": width, "height": height},
        "aspect_ratio": round(ratio, 4),
        "orientation": orientation,
        "rectangularity": (item.get("feature_signature") or {}).get("rectangularity"),
    }


def describe_local_footprint(
    anchor: dict[str, Any], primitives: list[dict[str, Any]]
) -> dict[str, Any]:
    anchor_box = _bbox(anchor)
    anchor_center = _center(anchor_box)
    anchor_scale = max(anchor_box[2], anchor_box[3], 1.0)

    rectangles: list[tuple[tuple[float, float, float], dict[str, Any]]] = []
    for item in primitives:
        if item.get("family") != _RECT:
            continue
        box = _bbox(item)
        if box[2] < anchor_box[2] * 1.1 or box[3] < anchor_box[3] * 1.1:
            continue
        if box[2] > anchor_scale * 40.0 or box[3] > anchor_scale * 40.0:
            continue
        distance = _point_to_box_distance(anchor_center, box)
        if distance > anchor_scale * 2.0:
            continue
        contains = 0.0 if distance == 0.0 else 1.0
        area = box[2] * box[3]
        rectangles.append(((contains, distance, area), item))

    rectangles.sort(key=lambda pair: pair[0])
    footprint_item = rectangles[0][1] if rectangles else None

    if footprint_item is not None:
        footprint_box = _bbox(footprint_item)
        footprint = _footprint_payload(footprint_item)
        horizontal = False
        vertical = False
        for item in primitives:
            if item.get("family") != _LINE:
                continue
            orientation = _line_orientation(item)
            if orientation is None or not _intersects(_bbox(item), footprint_box, pad=2.0):
                continue
            length = _line_length(item)
            if orientation == "HORIZONTAL" and length >= footprint_box[2] * 0.8:
                horizontal = True
            elif orientation == "VERTICAL" and length >= footprint_box[3] * 0.8:
                vertical = True
        axes = horizontal and vertical
        return {
            "anchor_id": anchor.get("normalized_id"),
            "graphical_state": (
                "P1_NUMBER_FOOTPRINT_AXES" if axes else "P2_NUMBER_FOOTPRINT_NO_AXES"
            ),
            "review_eligible": True,
            "axis_evidence_present": axes,
            "axis_evidence": {"horizontal": horizontal, "vertical": vertical},
            "footprint": footprint,
            "authority": _authority(),
        }

    local_lines: list[dict[str, Any]] = []
    window = (
        anchor_center[0] - anchor_scale * 4.0,
        anchor_center[1] - anchor_scale * 4.0,
        anchor_scale * 8.0,
        anchor_scale * 8.0,
    )
    orientations: set[str] = set()
    for item in primitives:
        if item.get("family") != _LINE:
            continue
        orientation = _line_orientation(item)
        if orientation is None or not _intersects(_bbox(item), window):
            continue
        local_lines.append(item)
        orientations.add(orientation)

    if len(local_lines) >= 3 and orientations == {"HORIZONTAL", "VERTICAL"}:
        return {
            "anchor_id": anchor.get("normalized_id"),
            "graphical_state": "P3_NUMBER_PARTIAL_FOOTPRINT",
            "review_eligible": True,
            "axis_evidence_present": False,
            "axis_evidence": {"horizontal": False, "vertical": False},
            "footprint": None,
            "partial_line_count": len(local_lines),
            "authority": _authority(),
        }

    return {
        "anchor_id": anchor.get("normalized_id"),
        "graphical_state": "NO_PLAUSIBLE_FOOTPRINT",
        "review_eligible": False,
        "axis_evidence_present": False,
        "axis_evidence": {"horizontal": False, "vertical": False},
        "footprint": None,
        "authority": _authority(),
    }
