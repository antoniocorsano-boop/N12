from __future__ import annotations

from typing import Any


def _box(raw: dict[str, Any]) -> dict[str, float]:
    box = {
        "x": float(raw["x"]),
        "y": float(raw["y"]),
        "width": float(raw["width"]),
        "height": float(raw["height"]),
    }
    if box["width"] <= 0 or box["height"] <= 0:
        raise ValueError("bbox width/height must be positive")
    return box


def _intersection_area(a: dict[str, float], b: dict[str, float]) -> float:
    ax2, ay2 = a["x"] + a["width"], a["y"] + a["height"]
    bx2, by2 = b["x"] + b["width"], b["y"] + b["height"]
    ix1, iy1 = max(a["x"], b["x"]), max(a["y"], b["y"])
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1)


def visible_similarity_siblings(
    target_candidate_id: str,
    crop_bbox: dict[str, Any],
    similarity_results: list[dict[str, Any]],
    *,
    min_visible_fraction: float = 0.75,
) -> list[dict[str, Any]]:
    """Return non-target similarity proposals substantially visible in a review crop.

    This is an occurrence-completeness aid only. It does not classify the sibling
    proposals and grants no support, family, section, structural or canonical
    authority.
    """

    crop = _box(crop_bbox)
    if not 0.0 < float(min_visible_fraction) <= 1.0:
        raise ValueError("min_visible_fraction must be in (0, 1]")

    visible: list[dict[str, Any]] = []
    for item in similarity_results:
        candidate_id = str(item.get("occurrence_candidate_id", "")).strip()
        if not candidate_id or candidate_id == target_candidate_id:
            continue
        bbox = _box(item["bbox"])
        area = bbox["width"] * bbox["height"]
        fraction = _intersection_area(crop, bbox) / area
        if fraction + 1e-12 < float(min_visible_fraction):
            continue
        row = dict(item)
        row["visible_fraction_in_crop"] = round(fraction, 6)
        row["occurrence_review_state"] = "VISIBLE_SIBLING_SIMILARITY_PROPOSAL"
        row["support_identity_authorized"] = False
        row["family_assignment_authorized"] = False
        row["structural_identity_authorized"] = False
        row["canonical_write_authorized"] = False
        visible.append(row)

    visible.sort(
        key=lambda item: (
            -float(item.get("score", 0.0)),
            str(item["occurrence_candidate_id"]),
        )
    )
    return visible
