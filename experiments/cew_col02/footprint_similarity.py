from __future__ import annotations

import math
from typing import Any


MAX_RESULTS = 64


def _box(raw: dict[str, Any]) -> dict[str, float]:
    try:
        box = {
            "x": float(raw["x"]),
            "y": float(raw["y"]),
            "width": float(raw["width"]),
            "height": float(raw["height"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("bbox must contain numeric x/y/width/height") from exc
    if not all(math.isfinite(value) for value in box.values()):
        raise ValueError("bbox values must be finite")
    if box["width"] <= 0 or box["height"] <= 0:
        raise ValueError("bbox width/height must be positive")
    return box


def _area(box: dict[str, float]) -> float:
    return box["width"] * box["height"]


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


def _candidate_similarity(
    prototype_bbox: dict[str, float],
    candidate_bbox: dict[str, float],
    *,
    rectangularity: float,
    detector: str | None,
) -> dict[str, float]:
    pw, ph = prototype_bbox["width"], prototype_bbox["height"]
    cw, ch = candidate_bbox["width"], candidate_bbox["height"]
    size_error = 0.5 * (abs(math.log(cw / pw)) + abs(math.log(ch / ph)))
    ratio_error = abs(math.log((cw / ch) / (pw / ph)))
    size_score = math.exp(-size_error)
    ratio_score = math.exp(-ratio_error)
    rectangularity_score = max(0.0, min(1.0, float(rectangularity)))
    envelope_score = 1.0 if detector == "LONG_AXIS_SUPPRESSED" else 0.55
    score = (
        0.50 * size_score
        + 0.25 * ratio_score
        + 0.15 * rectangularity_score
        + 0.10 * envelope_score
    )
    return {
        "score": score,
        "size": size_score,
        "ratio": ratio_score,
        "rectangularity": rectangularity_score,
        "envelope": envelope_score,
    }


def rank_similar_footprints(
    prototype_bbox: dict[str, Any],
    proposals: list[dict[str, Any]],
    *,
    limit: int = MAX_RESULTS,
) -> list[dict[str, Any]]:
    """Rank footprint proposals using the bounded historical PR #136 core.

    This function intentionally removes all support/family lookup dependencies.
    It produces retrieval proposals only and never assigns support identity,
    structural identity, family membership, or canonical authority.
    """

    prototype = _box(prototype_bbox)
    result_limit = max(1, min(MAX_RESULTS, int(limit)))
    ranked: list[dict[str, Any]] = []

    for row in proposals:
        candidate_id = str(row.get("candidate_id", "")).strip()
        if not candidate_id:
            raise ValueError("each footprint proposal requires candidate_id")
        if not isinstance(row.get("bbox"), dict):
            raise ValueError(f"proposal {candidate_id} requires bbox")
        bbox = _box(row["bbox"])

        # Historical PR #136 behavior: the taught region is not returned as a
        # discovery result.
        if _iou(prototype, bbox) >= 0.65:
            continue

        similarity = _candidate_similarity(
            prototype,
            bbox,
            rectangularity=float(row.get("rectangularity", 0.0)),
            detector=row.get("detector"),
        )
        if similarity["size"] < 0.45 or similarity["ratio"] < 0.50:
            continue

        ranked.append(
            {
                "occurrence_candidate_id": candidate_id,
                "bbox": bbox,
                "score": round(similarity["score"], 6),
                "size_similarity": round(similarity["size"], 6),
                "ratio_similarity": round(similarity["ratio"], 6),
                "rectangularity": round(similarity["rectangularity"], 6),
                "envelope_preference": round(similarity["envelope"], 6),
                "detector": row.get("detector"),
                "axis_evidence_present": bool(row.get("axis_evidence_present", False)),
                "support_identity": None,
                "family_id": None,
                "review_state": "SIMILARITY_PROPOSAL",
                "support_identity_authorized": False,
                "family_assignment_authorized": False,
                "structural_identity_authorized": False,
                "canonical_write_authorized": False,
            }
        )

    ranked.sort(
        key=lambda item: (
            -item["score"],
            -item["size_similarity"],
            item["occurrence_candidate_id"],
        )
    )

    kept: list[dict[str, Any]] = []
    for candidate in ranked:
        if any(_iou(candidate["bbox"], existing["bbox"]) > 0.45 for existing in kept):
            continue
        kept.append(candidate)
        if len(kept) >= result_limit:
            break
    return kept
