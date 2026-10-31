from __future__ import annotations

import math
from typing import Any


REVIEW_ID = "CEW-COL02-VISIBLE-SIBLING-RESIDUAL-MOBILE-v1"
PRODUCER_EXACT_SHA = "5664614d813cd11cf357bed40d7cdfaa843720f2"
SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
PROTOTYPE_GUIDED_REPLAY_SHA256 = "11dc8a03789628c6167a8c7cc10fe41d318c5fa22535065598e1c36aa56fd1ac"
OCCURRENCE_SWEEP_REPLAY_SHA256 = "bdf6dbdb6a071312727a3ca8146159d4f47514a7bcaec5225235987b0ccb1070"
HUMAN_REVIEW_BUNDLE_SHA256 = "896036dd048bac77555b383eb7af8329118dedc7f6dd4b5b7373e489f406a0d7"

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


def _expanded_context_bbox(
    target_bbox: dict[str, Any],
    *,
    source_width: int,
    source_height: int,
) -> dict[str, float]:
    if source_width <= 0 or source_height <= 0:
        raise ValueError("source dimensions must be positive")
    target = _validate_bbox(target_bbox, "target_bbox")
    left = int(round(target["x"] * source_width))
    top = int(round(target["y"] * source_height))
    right = int(round((target["x"] + target["width"]) * source_width))
    bottom = int(round((target["y"] + target["height"]) * source_height))
    span = max(right - left, bottom - top, 1)
    margin = max(120, int(round(span * 3.0)))
    x1 = max(0, left - margin)
    y1 = max(0, top - margin)
    x2 = min(source_width, right + margin)
    y2 = min(source_height, bottom + margin)
    return {
        "x": x1 / source_width,
        "y": y1 / source_height,
        "width": (x2 - x1) / source_width,
        "height": (y2 - y1) / source_height,
    }


def build_reframe_tasks(
    search: dict[str, Any],
    effective_decisions: list[dict[str, Any]],
    *,
    source_width: int,
    source_height: int,
) -> list[dict[str, Any]]:
    """Build context-only review tasks for human-positive misframed candidates.

    The original candidate ID and target bbox are preserved verbatim; only context expands.
    """
    panels = search.get("review_panels")
    if not isinstance(panels, list):
        raise ValueError("search.review_panels must be a list")
    panels_by_candidate: dict[str, dict[str, Any]] = {}
    for panel in panels:
        if not isinstance(panel, dict):
            raise ValueError("every review panel must be an object")
        candidate_id = str(panel.get("candidate_id") or "").strip()
        if not candidate_id:
            raise ValueError("review panel candidate_id must be non-empty")
        if candidate_id in panels_by_candidate:
            raise ValueError(f"duplicate review panel candidate_id: {candidate_id}")
        panels_by_candidate[candidate_id] = panel

    tasks: list[dict[str, Any]] = []
    seen_candidates: set[str] = set()
    for decision in effective_decisions:
        if not isinstance(decision, dict) or decision.get("action") != "INQUADRATO_MALE":
            continue
        candidate_id = str(decision.get("candidate_id") or "").strip()
        if not candidate_id or candidate_id in seen_candidates:
            raise ValueError(f"duplicate or empty misframed candidate decision: {candidate_id!r}")
        seen_candidates.add(candidate_id)
        panel = panels_by_candidate.get(candidate_id)
        if panel is None:
            raise ValueError(f"missing review panel for misframed candidate {candidate_id}")
        original_bbox = panel.get("bbox")
        _validate_bbox(original_bbox, f"review panel {candidate_id} bbox")
        tasks.append(
            {
                "task_type": "REFRAME_CONFIRMATION",
                "candidate_id": candidate_id,
                "source_panel_id": panel.get("panel_id"),
                "source_event_id": decision.get("event_id"),
                "original_action": "INQUADRATO_MALE",
                "target_bbox": dict(original_bbox),
                "context_bbox": _expanded_context_bbox(
                    original_bbox,
                    source_width=source_width,
                    source_height=source_height,
                ),
            }
        )
    return tasks


def _mobile_crop_bbox(
    panel_bbox: dict[str, Any],
    *,
    source_width: int,
    source_height: int,
) -> dict[str, float]:
    """Reproduce the source-only crop geometry used by the mobile COL-02 adapter."""
    if source_width <= 0 or source_height <= 0:
        raise ValueError("source dimensions must be positive")
    box = _validate_bbox(panel_bbox, "panel_bbox")
    left = max(0, min(source_width, int(round(box["x"] * source_width))))
    top = max(0, min(source_height, int(round(box["y"] * source_height))))
    right = max(left + 1, min(source_width, int(round((box["x"] + box["width"]) * source_width))))
    bottom = max(top + 1, min(source_height, int(round((box["y"] + box["height"]) * source_height))))
    span = max(right - left, bottom - top, 70)
    margin = max(120, int(round(span * 1.8)))
    x1 = max(0, left - margin)
    y1 = max(0, top - margin)
    x2 = min(source_width, right + margin)
    y2 = min(source_height, bottom + margin)
    return {
        "x": x1 / source_width,
        "y": y1 / source_height,
        "width": (x2 - x1) / source_width,
        "height": (y2 - y1) / source_height,
    }


def select_residual_occurrences(search: dict[str, Any], sweep: dict[str, Any]) -> list[dict[str, Any]]:
    """Select one deterministic visible occurrence for each non-target residual candidate."""
    review_panels = search.get("review_panels")
    sweep_panels = sweep.get("panels")
    if not isinstance(review_panels, list) or not review_panels:
        raise ValueError("search.review_panels must be non-empty")
    if not isinstance(sweep_panels, list) or not sweep_panels:
        raise ValueError("sweep.panels must be non-empty")

    reviewed_targets = {str(panel.get("candidate_id") or "").strip() for panel in review_panels}
    reviewed_targets.discard("")
    search_panel_ids = {str(panel.get("panel_id") or "").strip() for panel in review_panels}

    first_order: dict[str, int] = {}
    best: dict[str, dict[str, Any]] = {}
    sequence = 0
    for panel in sweep_panels:
        panel_id = str(panel.get("panel_id") or "").strip()
        context_target_id = str(panel.get("target_candidate_id") or "").strip()
        if not panel_id or panel_id not in search_panel_ids:
            raise ValueError(f"sweep panel has no matching search review panel: {panel_id!r}")
        if not context_target_id:
            raise ValueError(f"missing target_candidate_id for sweep panel {panel_id}")
        siblings = panel.get("visible_sibling_candidates")
        if not isinstance(siblings, list):
            raise ValueError(f"visible_sibling_candidates must be a list for {panel_id}")
        for sibling in siblings:
            candidate_id = str(sibling.get("candidate_id") or "").strip()
            if not candidate_id or candidate_id in reviewed_targets:
                continue
            bbox = sibling.get("bbox")
            _validate_bbox(bbox, f"residual {candidate_id} bbox")
            visible_fraction = float(sibling.get("visible_fraction_in_crop"))
            score = float(sibling.get("score", 0.0))
            if not (0.0 < visible_fraction <= 1.0):
                raise ValueError(f"invalid visible fraction for {candidate_id}")
            if candidate_id not in first_order:
                first_order[candidate_id] = sequence
                sequence += 1
            record = {
                "candidate_id": candidate_id,
                "source_panel_id": panel_id,
                "context_target_candidate_id": context_target_id,
                "target_bbox": dict(bbox),
                "score": score,
                "visible_fraction_in_crop": visible_fraction,
            }
            current = best.get(candidate_id)
            if current is None or (
                visible_fraction,
                score,
                panel_id,
            ) > (
                float(current["visible_fraction_in_crop"]),
                float(current["score"]),
                str(current["source_panel_id"]),
            ):
                best[candidate_id] = record

    return [best[candidate_id] for candidate_id, _ in sorted(first_order.items(), key=lambda item: item[1])]


def _reconciliation_authority() -> dict[str, bool]:
    return {
        "graphical_reconciliation_review_authorized": True,
        "graphical_review_evidence_retained": True,
        "support_identity_authorized": False,
        "text_identity_binding_authorized": False,
        "family_assignment_authorized": False,
        "section_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


def build_reconciliation_manifest(
    bundle: dict[str, Any],
    *,
    search: dict[str, Any],
    sweep: dict[str, Any],
    audit: dict[str, Any],
    proposals: list[dict[str, Any]],
    human_review_bundle_sha256: str,
) -> dict[str, Any]:
    """Assemble the bounded successor Human Review manifest from frozen inputs."""
    _require_equal(human_review_bundle_sha256, HUMAN_REVIEW_BUNDLE_SHA256, "human_review_bundle_sha256")
    replay = replay_mobile_review(bundle)
    _require_equal(search.get("replay_sha256"), PROTOTYPE_GUIDED_REPLAY_SHA256, "search.replay_sha256")
    _require_equal(sweep.get("replay_sha256"), OCCURRENCE_SWEEP_REPLAY_SHA256, "sweep.replay_sha256")
    _require_equal(
        sweep.get("source_search_replay_sha256"),
        PROTOTYPE_GUIDED_REPLAY_SHA256,
        "sweep.source_search_replay_sha256",
    )
    search_source = search.get("source")
    if not isinstance(search_source, dict):
        raise ValueError("search.source must be an object")
    _require_equal(search_source.get("sha256"), SOURCE_SHA256, "search.source.sha256")
    audit_source = audit.get("source")
    if not isinstance(audit_source, dict):
        raise ValueError("audit.source must be an object")
    if audit_source.get("sha256") is not None:
        _require_equal(audit_source.get("sha256"), SOURCE_SHA256, "audit.source.sha256")
    source_width = int(audit_source.get("raster_width_px") or 0)
    source_height = int(audit_source.get("raster_height_px") or 0)
    if source_width <= 0 or source_height <= 0:
        raise ValueError("audit source raster dimensions must be positive")

    selected = select_residual_occurrences(search, sweep)
    selected_by_id = {item["candidate_id"]: item for item in selected}
    residual_panels: list[dict[str, Any]] = []
    for candidate_id in replay["misframed_candidate_ids"]:
        occurrence = selected_by_id.get(candidate_id)
        if occurrence is None:
            raise ValueError(f"missing selected residual occurrence for {candidate_id}")
        residual_panels.append(
            {
                "panel_id": occurrence["source_panel_id"],
                "candidate_id": candidate_id,
                "bbox": occurrence["target_bbox"],
            }
        )
    reframe_tasks = build_reframe_tasks(
        {"review_panels": residual_panels},
        replay["decisions"],
        source_width=source_width,
        source_height=source_height,
    )

    search_panels_by_id = {str(panel.get("panel_id")): panel for panel in search["review_panels"]}
    point_inputs: list[dict[str, Any]] = []
    point_context_by_event: dict[str, dict[str, Any]] = {}
    for event in replay["additional_occurrences"]:
        host_candidate_id = str(event["candidate_id"])
        occurrence = selected_by_id.get(host_candidate_id)
        if occurrence is None:
            raise ValueError(f"missing selected residual occurrence for point host {host_candidate_id}")
        source_panel_id = str(occurrence["source_panel_id"])
        source_panel = search_panels_by_id.get(source_panel_id)
        if source_panel is None:
            raise ValueError(f"missing source review panel {source_panel_id}")
        crop_bbox = _mobile_crop_bbox(
            source_panel.get("bbox"),
            source_width=source_width,
            source_height=source_height,
        )
        source_point = project_crop_point(event["point"], crop_bbox)
        point_inputs.append({"event_id": event["event_id"], "source_point": source_point})
        point_context_by_event[event["event_id"]] = {
            "host_candidate_id": host_candidate_id,
            "source_panel_id": source_panel_id,
            "context_target_candidate_id": occurrence["context_target_candidate_id"],
            "mobile_point": dict(event["point"]),
            "mobile_crop_bbox": crop_bbox,
        }

    reviewed_ids = {str(panel.get("candidate_id")) for panel in search["review_panels"]}
    reviewed_ids.update(RESIDUAL_CANDIDATE_IDS)
    point_reconciliation = reconcile_human_points(point_inputs, proposals, reviewed_ids)
    for record in point_reconciliation:
        record.update(point_context_by_event[record["event_id"]])

    review_tasks: list[dict[str, Any]] = [dict(task) for task in reframe_tasks]
    for record in point_reconciliation:
        if record["status"] == "REVIEW_REQUIRED_EXISTING_PROPOSAL":
            review_tasks.append({"task_type": "ADDITIONAL_OCCURRENCE_CONFIRMATION", **record})
        elif record["status"] == "HUMAN_POINT_UNBOUND":
            review_tasks.append({"task_type": "HUMAN_POINT_UNBOUND", **record})

    if len(reframe_tasks) != 2:
        raise ValueError(f"expected exactly 2 reframe tasks, got {len(reframe_tasks)}")
    if len(point_reconciliation) != 4:
        raise ValueError(f"expected exactly 4 point reconciliation records, got {len(point_reconciliation)}")

    return {
        "schema_id": "CEW_COL02_RESIDUAL_OCCURRENCE_RECONCILIATION",
        "schema_version": 1,
        "status": "RESIDUAL_OCCURRENCE_RECONCILIATION_READY_FOR_HUMAN_REVIEW",
        "source": {
            "producer_exact_sha": PRODUCER_EXACT_SHA,
            "source_sha256": SOURCE_SHA256,
            "prototype_guided_replay_sha256": PROTOTYPE_GUIDED_REPLAY_SHA256,
            "occurrence_sweep_replay_sha256": OCCURRENCE_SWEEP_REPLAY_SHA256,
        },
        "human_review_bundle_sha256": human_review_bundle_sha256,
        "effective_human_review": {
            "decision_count": len(replay["decisions"]),
            "additional_occurrence_count": len(replay["additional_occurrences"]),
            "misframed_candidate_ids": list(replay["misframed_candidate_ids"]),
        },
        "selected_residual_occurrences": selected,
        "reframe_tasks": reframe_tasks,
        "point_reconciliation": point_reconciliation,
        "review_tasks": review_tasks,
        "residual_candidate_review_complete": True,
        "occurrence_coverage_complete": False,
        "authority": _reconciliation_authority(),
    }


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
