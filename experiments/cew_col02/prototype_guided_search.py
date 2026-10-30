from __future__ import annotations

from typing import Any

from experiments.cew_col02.footprint_similarity import rank_similar_footprints


DEFAULT_LIMIT = 64


def _iou(a: dict[str, float], b: dict[str, float]) -> float:
    ax2, ay2 = a["x"] + a["width"], a["y"] + a["height"]
    bx2, by2 = b["x"] + b["width"], b["y"] + b["height"]
    ix1, iy1 = max(a["x"], b["x"]), max(a["y"], b["y"])
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    union = a["width"] * a["height"] + b["width"] * b["height"] - inter
    return inter / union if union > 0 else 0.0


def _review_sets(review_receipt: dict[str, Any]) -> tuple[list[str], set[str]]:
    positives: list[str] = []
    negatives: set[str] = set()
    for item in review_receipt.get("panel_decisions", []):
        candidate_id = str(item.get("candidate_id", "")).strip()
        decision = item.get("column_graphic_decision")
        if not candidate_id:
            continue
        if decision == "COLUMN_FOOTPRINT_CONFIRMED" and bool(item.get("prototype_eligible", False)):
            positives.append(candidate_id)
        elif decision == "NOT_COLUMN":
            negatives.add(candidate_id)
    if not positives:
        raise ValueError("human review must contain at least one prototype-eligible confirmed column footprint")
    return positives, negatives


def rank_from_human_review(
    proposals: list[dict[str, Any]],
    review_receipt: dict[str, Any],
    *,
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """Union deterministic similarity searches from human-confirmed positive footprints.

    Human-confirmed positives are teaching seeds only. Human-reviewed negatives are
    excluded from discovery output, but are not used to train or alter similarity
    weights. No support identity, family, section, structural identity or canonical
    write authority is granted here.
    """

    result_limit = max(1, min(DEFAULT_LIMIT, int(limit)))
    by_id: dict[str, dict[str, Any]] = {}
    for row in proposals:
        candidate_id = str(row.get("candidate_id", "")).strip()
        if not candidate_id:
            raise ValueError("each footprint proposal requires candidate_id")
        if candidate_id in by_id:
            raise ValueError(f"duplicate footprint proposal candidate_id: {candidate_id}")
        by_id[candidate_id] = row

    positive_ids, negative_ids = _review_sets(review_receipt)
    missing = [candidate_id for candidate_id in positive_ids if candidate_id not in by_id]
    if missing:
        raise ValueError("human positive prototype candidates missing from proposal set: " + ",".join(missing))

    excluded_ids = set(positive_ids) | negative_ids
    aggregate: dict[str, dict[str, Any]] = {}

    for prototype_id in positive_ids:
        prototype_bbox = by_id[prototype_id]["bbox"]
        # Ask the historical core for its full bounded result set. Final limiting
        # and NMS happen after union across all human-positive prototypes.
        ranked = rank_similar_footprints(prototype_bbox, proposals, limit=DEFAULT_LIMIT)
        for candidate in ranked:
            candidate_id = candidate["occurrence_candidate_id"]
            if candidate_id in excluded_ids:
                continue
            existing = aggregate.get(candidate_id)
            if existing is None:
                merged = dict(candidate)
                merged["best_prototype_candidate_id"] = prototype_id
                merged["matched_prototype_candidate_ids"] = [prototype_id]
                merged["prototype_count"] = 1
                aggregate[candidate_id] = merged
                continue

            matched = set(existing["matched_prototype_candidate_ids"])
            matched.add(prototype_id)
            existing["matched_prototype_candidate_ids"] = sorted(matched)
            existing["prototype_count"] = len(matched)
            if candidate["score"] > existing["score"]:
                lineage = {
                    "matched_prototype_candidate_ids": existing["matched_prototype_candidate_ids"],
                    "prototype_count": existing["prototype_count"],
                }
                replacement = dict(candidate)
                replacement.update(lineage)
                replacement["best_prototype_candidate_id"] = prototype_id
                aggregate[candidate_id] = replacement

    ordered = sorted(
        aggregate.values(),
        key=lambda item: (
            -float(item["score"]),
            -int(item["prototype_count"]),
            -float(item["size_similarity"]),
            str(item["occurrence_candidate_id"]),
        ),
    )

    kept: list[dict[str, Any]] = []
    for candidate in ordered:
        if any(_iou(candidate["bbox"], prior["bbox"]) > 0.45 for prior in kept):
            continue
        candidate["review_state"] = "PROTOTYPE_GUIDED_SIMILARITY_PROPOSAL"
        candidate["support_identity_authorized"] = False
        candidate["family_assignment_authorized"] = False
        candidate["structural_identity_authorized"] = False
        candidate["canonical_write_authorized"] = False
        kept.append(candidate)
        if len(kept) >= result_limit:
            break
    return kept
