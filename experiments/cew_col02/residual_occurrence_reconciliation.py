from __future__ import annotations

import math
from typing import Any


REVIEW_ID = "CEW-COL02-VISIBLE-SIBLING-RESIDUAL-MOBILE-v1"
PRODUCER_EXACT_SHA = "5664614d813cd11cf357bed40d7cdfaa843720f2"
SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
PROTOTYPE_GUIDED_REPLAY_SHA256 = "11dc8a03789628c6167a8c7cc10fe41d318c5fa22535065598e1c36aa56fd1ac"
OCCURRENCE_SWEEP_REPLAY_SHA256 = "bdf6dbdb6a071312727a3ca8146159d4f47514a7bcaec5225235987b0ccb1070"

RESIDUAL_CANDIDATE_IDS = (
    "COL02-FP-0515",
    "COL02-FP-0252",
    "COL02-FP-0028",
    "COL02-FP-0581",
    "COL02-FP-0577",
    "COL02-FP-0605",
    "COL02-FP-0490",
    "COL02-FP-0106",
    "COL02-FP-0572",
    "COL02-FP-0243",
)

TERMINAL_ACTIONS = {"PILASTRO", "NON_PILASTRO", "INQUADRATO_MALE"}


def _require_equal(actual: Any, expected: Any, field: str) -> None:
    if actual != expected:
        raise ValueError(f"{field} mismatch: expected {expected!r}, got {actual!r}")


def _validate_point(point: Any, event_id: str) -> dict[str, float]:
    if not isinstance(point, dict):
        raise ValueError(f"additional occurrence {event_id} point must be an object")
    try:
        x = float(point["x"])
        y = float(point["y"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"additional occurrence {event_id} point must contain numeric x/y") from exc
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
        raise ValueError(f"additional occurrence {event_id} point must be normalized")
    return {"x": x, "y": y}


def _validate_bbox(box: Any, label: str) -> dict[str, float]:
    if not isinstance(box, dict):
        raise ValueError(f"{label} must be an object")
    try:
        x = float(box["x"])
        y = float(box["y"])
        width = float(box["width"])
        height = float(box["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain numeric x/y/width/height") from exc
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and width > 0.0 and height > 0.0):
        raise ValueError(f"{label} has invalid normalized geometry")
    if x + width > 1.0 + 1e-12 or y + height > 1.0 + 1e-12:
        raise ValueError(f"{label} exceeds normalized source bounds")
    return {"x": x, "y": y, "width": width, "height": height}


def project_crop_point(point: dict[str, Any], crop_bbox: dict[str, Any]) -> dict[str, float]:
    """Project a point normalized to a review crop back to normalized source coordinates."""
    local = _validate_point(point, "crop-point")
    crop = _validate_bbox(crop_bbox, "crop_bbox")
    return {
        "x": crop["x"] + local["x"] * crop["width"],
        "y": crop["y"] + local["y"] * crop["height"],
    }


def _point_inside_bbox(point: dict[str, float], box: dict[str, float]) -> bool:
    return (
        box["x"] <= point["x"] <= box["x"] + box["width"]
        and box["y"] <= point["y"] <= box["y"] + box["height"]
    )


def _center_distance(point: dict[str, float], box: dict[str, float]) -> float:
    cx = box["x"] + box["width"] / 2.0
    cy = box["y"] + box["height"] / 2.0
    return math.hypot(point["x"] - cx, point["y"] - cy)


def reconcile_human_points(
    points: list[dict[str, Any]],
    proposals: list[dict[str, Any]],
    reviewed_ids: set[str],
) -> list[dict[str, Any]]:
    """Bind source-normalized human points to the frozen proposal set, fail-closed.

    Proposal IDs are only graphical occurrence identifiers. Equal geometric evidence remains
    ambiguous; lexical candidate order is used only to make ambiguity reporting deterministic.
    """
    normalized_proposals: list[dict[str, Any]] = []
    proposal_ids: set[str] = set()
    for proposal in proposals:
        candidate_id = str(proposal.get("candidate_id") or "").strip()
        if not candidate_id or candidate_id in proposal_ids:
            raise ValueError(f"proposal candidate_id must be non-empty and unique: {candidate_id!r}")
        proposal_ids.add(candidate_id)
        normalized_proposals.append(
            {
                "candidate_id": candidate_id,
                "bbox": _validate_bbox(proposal.get("bbox"), f"proposal {candidate_id} bbox"),
            }
        )

    results: list[dict[str, Any]] = []
    claimed_by_event: dict[str, str] = {}
    seen_event_ids: set[str] = set()

    for raw_point in points:
        event_id = str(raw_point.get("event_id") or "").strip()
        if not event_id or event_id in seen_event_ids:
            raise ValueError(f"point event_id must be non-empty and unique: {event_id!r}")
        seen_event_ids.add(event_id)
        source_point = _validate_point(raw_point.get("source_point"), event_id)

        ranked: list[tuple[bool, float, str, dict[str, float]]] = []
        for proposal in normalized_proposals:
            box = proposal["bbox"]
            contains = _point_inside_bbox(source_point, box)
            distance = _center_distance(source_point, box)
            local_limit = 1.5 * max(box["width"], box["height"])
            if contains or distance <= local_limit:
                ranked.append((contains, distance, proposal["candidate_id"], box))

        ranked.sort(key=lambda item: (not item[0], item[1], item[2]))
        base = {"event_id": event_id, "source_point": source_point}
        if not ranked:
            results.append({**base, "status": "HUMAN_POINT_UNBOUND", "ambiguous_candidate_ids": []})
            continue

        top = ranked[0]
        same_geometric_rank = [
            item
            for item in ranked
            if item[0] == top[0] and math.isclose(item[1], top[1], rel_tol=0.0, abs_tol=1e-12)
        ]
        if len(same_geometric_rank) > 1:
            results.append(
                {
                    **base,
                    "status": "HUMAN_POINT_UNBOUND",
                    "ambiguous_candidate_ids": sorted(item[2] for item in same_geometric_rank),
                }
            )
            continue

        candidate_id = top[2]
        matched = {
            **base,
            "proposal_candidate_id": candidate_id,
            "proposal_bbox": dict(top[3]),
            "point_inside_proposal": bool(top[0]),
            "center_distance": top[1],
        }
        if candidate_id in reviewed_ids:
            results.append({**matched, "status": "DUPLICATE_EXISTING_OCCURRENCE"})
            continue
        if candidate_id in claimed_by_event:
            results.append(
                {
                    **matched,
                    "status": "DUPLICATE_POINT_RESOLUTION",
                    "duplicate_of_event_id": claimed_by_event[candidate_id],
                }
            )
            continue

        claimed_by_event[candidate_id] = event_id
        results.append({**matched, "status": "REVIEW_REQUIRED_EXISTING_PROPOSAL"})

    return results


def replay_mobile_review(bundle: dict[str, Any]) -> dict[str, Any]:
    """Replay the append-only mobile receipt and return its effective graphical state.

    This function validates only the frozen COL-02 graphical-review lineage. It grants no
    structural, canonical, or promotion authority.
    """
    if not isinstance(bundle, dict):
        raise ValueError("mobile review bundle must be an object")

    _require_equal(bundle.get("schema_version"), "cew-mobile-review-bundle-v1", "schema_version")
    _require_equal(bundle.get("review_id"), REVIEW_ID, "review_id")
    _require_equal(bundle.get("candidate_ids"), list(RESIDUAL_CANDIDATE_IDS), "candidate_ids")

    source = bundle.get("source")
    if not isinstance(source, dict):
        raise ValueError("source must be an object")
    _require_equal(source.get("producer_exact_sha"), PRODUCER_EXACT_SHA, "producer_exact_sha")
    _require_equal(source.get("source_sha256"), SOURCE_SHA256, "source_sha256")
    _require_equal(
        source.get("prototype_guided_replay_sha256"),
        PROTOTYPE_GUIDED_REPLAY_SHA256,
        "prototype_guided_replay_sha256",
    )
    _require_equal(
        source.get("occurrence_sweep_replay_sha256"),
        OCCURRENCE_SWEEP_REPLAY_SHA256,
        "occurrence_sweep_replay_sha256",
    )

    authority = bundle.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("authority must be an object")
    if any(bool(value) for value in authority.values()):
        raise ValueError("mobile review authority must remain fail-closed")
    if bundle.get("canonical_write_authorized") is not False:
        raise ValueError("canonical_write_authorized must be false")
    if bundle.get("canonical_write_performed") is not False:
        raise ValueError("canonical_write_performed must be false")

    events = bundle.get("events")
    if not isinstance(events, list):
        raise ValueError("events must be a list")

    seen_event_ids: set[str] = set()
    undone_ids: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("every event must be an object")
        event_id = str(event.get("event_id") or "").strip()
        if not event_id or event_id in seen_event_ids:
            raise ValueError(f"event_id must be non-empty and unique: {event_id!r}")
        seen_event_ids.add(event_id)
        if event.get("event_type") == "UNDO_LAST":
            target = str(event.get("undoes_event_id") or "").strip()
            if not target or target not in seen_event_ids:
                raise ValueError(f"UNDO_LAST {event_id} must reference an earlier event")
            undone_ids.add(target)

    effective_events = [
        event
        for event in events
        if event.get("event_type") != "UNDO_LAST" and event.get("event_id") not in undone_ids
    ]

    decisions_by_candidate: dict[str, dict[str, Any]] = {}
    additional_occurrences: list[dict[str, Any]] = []
    residual_set = set(RESIDUAL_CANDIDATE_IDS)

    for event in effective_events:
        event_type = event.get("event_type")
        candidate_id = str(event.get("candidate_id") or "").strip()
        if candidate_id not in residual_set:
            raise ValueError(f"event references unknown residual candidate: {candidate_id!r}")

        if event_type == "CANDIDATE_DECISION":
            action = event.get("action")
            if event.get("terminal") is not True or action not in TERMINAL_ACTIONS:
                raise ValueError(f"invalid terminal decision for {candidate_id}")
            if candidate_id in decisions_by_candidate:
                raise ValueError(
                    f"candidate {candidate_id} must have exactly one effective terminal decision"
                )
            decisions_by_candidate[candidate_id] = dict(event)
        elif event_type == "ADDITIONAL_OCCURRENCE":
            if event.get("action") != "ALTRO_PILASTRO" or event.get("terminal") is not False:
                raise ValueError(f"invalid additional occurrence event for {candidate_id}")
            normalized = dict(event)
            normalized["point"] = _validate_point(event.get("point"), str(event.get("event_id")))
            additional_occurrences.append(normalized)
        else:
            raise ValueError(f"unsupported effective event_type: {event_type!r}")

    for candidate_id in RESIDUAL_CANDIDATE_IDS:
        if candidate_id not in decisions_by_candidate:
            raise ValueError(
                f"candidate {candidate_id} must have exactly one effective terminal decision"
            )

    decisions = [decisions_by_candidate[candidate_id] for candidate_id in RESIDUAL_CANDIDATE_IDS]
    misframed_candidate_ids = [
        item["candidate_id"] for item in decisions if item.get("action") == "INQUADRATO_MALE"
    ]

    return {
        "source": dict(source),
        "decisions": decisions,
        "additional_occurrences": additional_occurrences,
        "misframed_candidate_ids": misframed_candidate_ids,
        "source_event_count": len(events),
        "effective_event_count": len(effective_events),
    }
