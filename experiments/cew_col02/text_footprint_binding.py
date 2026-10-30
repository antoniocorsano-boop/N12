from __future__ import annotations

import math
from typing import Any


BBox = dict[str, float]


def _box(raw: dict[str, Any], *, name: str) -> BBox:
    try:
        box = {
            "x": float(raw["x"]),
            "y": float(raw["y"]),
            "width": float(raw["width"]),
            "height": float(raw["height"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} must contain numeric x/y/width/height") from exc
    if not all(math.isfinite(value) for value in box.values()):
        raise ValueError(f"{name} values must be finite")
    if box["width"] <= 0 or box["height"] <= 0:
        raise ValueError(f"{name} width/height must be positive")
    return box


def _intersection_area(a: BBox, b: BBox) -> float:
    left = max(a["x"], b["x"])
    top = max(a["y"], b["y"])
    right = min(a["x"] + a["width"], b["x"] + b["width"])
    bottom = min(a["y"] + a["height"], b["y"] + b["height"])
    if right <= left or bottom <= top:
        return 0.0
    return (right - left) * (bottom - top)


def _center(box: BBox) -> tuple[float, float]:
    return box["x"] + box["width"] / 2.0, box["y"] + box["height"] / 2.0


def _edge_distance(a: BBox, b: BBox) -> float:
    a_right = a["x"] + a["width"]
    a_bottom = a["y"] + a["height"]
    b_right = b["x"] + b["width"]
    b_bottom = b["y"] + b["height"]
    dx = max(a["x"] - b_right, b["x"] - a_right, 0.0)
    dy = max(a["y"] - b_bottom, b["y"] - a_bottom, 0.0)
    return math.hypot(dx, dy)


def classify_text_relation(
    footprint: dict[str, Any],
    text: dict[str, Any],
    *,
    near_radius: float = 0.35,
) -> dict[str, Any]:
    """Classify one text bbox relative to one candidate footprint.

    The result is geometric review evidence only. It does not identify a support,
    confirm a column, assign a family, or grant structural/canonical authority.
    ``near_radius`` is expressed as a fraction of the footprint's larger side.
    """

    fp = _box(footprint, name="footprint")
    tx = _box(text, name="text")
    radius = float(near_radius)
    if not math.isfinite(radius) or radius < 0:
        raise ValueError("near_radius must be a finite non-negative number")

    intersection = _intersection_area(fp, tx)
    text_area = tx["width"] * tx["height"]
    contained_fraction = intersection / text_area

    fp_cx, fp_cy = _center(fp)
    tx_cx, tx_cy = _center(tx)
    center_in = (
        fp["x"] <= tx_cx <= fp["x"] + fp["width"]
        and fp["y"] <= tx_cy <= fp["y"] + fp["height"]
    )
    scale = max(fp["width"], fp["height"])
    normalized_center_distance = math.hypot(tx_cx - fp_cx, tx_cy - fp_cy) / scale
    edge_distance = _edge_distance(fp, tx)
    normalized_edge_distance = edge_distance / scale

    if center_in and contained_fraction >= 0.80:
        relation = "INSIDE_FOOTPRINT"
    elif intersection > 0.0:
        relation = "INTERSECTS_FOOTPRINT"
    elif normalized_edge_distance <= radius:
        relation = "NEAR_OUTSIDE_FOOTPRINT"
    else:
        relation = "UNRELATED_OR_UNBOUND"

    return {
        "relation": relation,
        "intersection_area": intersection,
        "text_contained_fraction": contained_fraction,
        "center_in_footprint": center_in,
        "normalized_center_distance": normalized_center_distance,
        "edge_distance": edge_distance,
        "normalized_edge_distance": normalized_edge_distance,
        "support_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }
