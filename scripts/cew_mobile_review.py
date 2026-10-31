#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = "cew-mobile-candidate-review-v1"
EVENT_SCHEMA_VERSION = "cew-mobile-review-event-v1"
EXPORT_SCHEMA_VERSION = "cew-mobile-review-bundle-v1"

PRIMARY_ACTIONS = (
    "PILASTRO",
    "NON_PILASTRO",
    "INQUADRATO_MALE",
    "ALTRO_PILASTRO",
)
TERMINAL_ACTIONS = frozenset({"PILASTRO", "NON_PILASTRO", "INQUADRATO_MALE"})
NEGATIVE_REASONS = frozenset({"TRAVE", "QUOTA", "LINEA_DI_DISEGNO", "RITAGLIO_INCOMPLETO", "ALTRO"})

AUTHORITY_CLOSED = {
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_text(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def validate_manifest(manifest: dict) -> dict:
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    _require_text(manifest.get("review_id"), "review_id")
    source = manifest.get("source")
    if not isinstance(source, dict):
        raise ValueError("source must be an object")
    _require_text(source.get("source_id"), "source.source_id")
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidates must be a non-empty list")
    seen: set[str] = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise ValueError(f"candidate {index} must be an object")
        candidate_id = _require_text(candidate.get("candidate_id"), f"candidate {index}.candidate_id")
        if candidate_id in seen:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        seen.add(candidate_id)
        _require_text(candidate.get("image_uri"), f"candidate {candidate_id}.image_uri")
    return manifest


def normalize_point(x: float, y: float, width: float, height: float) -> dict[str, float]:
    if width <= 0 or height <= 0:
        raise ValueError("evidence dimensions must be positive")
    nx = min(1.0, max(0.0, float(x) / float(width)))
    ny = min(1.0, max(0.0, float(y) / float(height)))
    return {"x": round(nx, 6), "y": round(ny, 6)}


def _event_id(events: list[dict], candidate_id: str, event_type: str) -> str:
    return f"EV-{len(events)+1:05d}-{candidate_id}-{event_type}"


def append_action(
    events: list[dict],
    candidate_id: str,
    action: str,
    *,
    reason: str | None = None,
    point: dict[str, float] | None = None,
    timestamp: str | None = None,
) -> list[dict]:
    candidate_id = _require_text(candidate_id, "candidate_id")
    if action not in PRIMARY_ACTIONS:
        raise ValueError(f"unsupported action: {action}")
    if reason is not None:
        if action != "NON_PILASTRO":
            raise ValueError("reason is allowed only for NON_PILASTRO")
        if reason not in NEGATIVE_REASONS:
            raise ValueError(f"unsupported negative reason: {reason}")
    if action == "ALTRO_PILASTRO":
        if not isinstance(point, dict) or set(point) != {"x", "y"}:
            raise ValueError("ALTRO_PILASTRO requires normalized point {x,y}")
        px, py = float(point["x"]), float(point["y"])
        if not (0.0 <= px <= 1.0 and 0.0 <= py <= 1.0):
            raise ValueError("point coordinates must be normalized to [0,1]")
    elif point is not None:
        raise ValueError("point is valid only for ALTRO_PILASTRO")

    event_type = "ADDITIONAL_OCCURRENCE" if action == "ALTRO_PILASTRO" else "CANDIDATE_DECISION"
    event: dict[str, Any] = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": _event_id(events, candidate_id, event_type),
        "event_type": event_type,
        "candidate_id": candidate_id,
        "action": action,
        "terminal": action in TERMINAL_ACTIONS,
        "timestamp": timestamp or _now(),
    }
    if reason is not None:
        event["reason"] = reason
    if point is not None:
        event["point"] = {"x": float(point["x"]), "y": float(point["y"])}
    return [*deepcopy(events), event]


def _undone_ids(events: list[dict]) -> set[str]:
    return {str(event.get("undoes_event_id")) for event in events if event.get("event_type") == "UNDO_LAST"}


def append_undo(events: list[dict], *, timestamp: str | None = None) -> list[dict]:
    undone = _undone_ids(events)
    target = None
    for event in reversed(events):
        event_id = str(event.get("event_id", ""))
        if event.get("event_type") != "UNDO_LAST" and event_id and event_id not in undone:
            target = event
            break
    if target is None:
        raise ValueError("nothing to undo")
    event = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": f"EV-{len(events)+1:05d}-UNDO_LAST",
        "event_type": "UNDO_LAST",
        "undoes_event_id": target["event_id"],
        "candidate_id": target.get("candidate_id"),
        "terminal": False,
        "timestamp": timestamp or _now(),
    }
    return [*deepcopy(events), event]


def replay_effective_state(events: list[dict]) -> dict[str, dict]:
    undone = _undone_ids(events)
    state: dict[str, dict] = {}
    occurrences: dict[str, list[dict]] = {}
    for event in events:
        if event.get("event_type") == "UNDO_LAST" or event.get("event_id") in undone:
            continue
        candidate_id = str(event.get("candidate_id", ""))
        if not candidate_id:
            continue
        if event.get("event_type") == "CANDIDATE_DECISION":
            state[candidate_id] = {
                "decision": event.get("action"),
                "reason": event.get("reason"),
                "event_id": event.get("event_id"),
            }
        elif event.get("event_type") == "ADDITIONAL_OCCURRENCE":
            occurrences.setdefault(candidate_id, []).append({
                "point": deepcopy(event.get("point")),
                "event_id": event.get("event_id"),
            })
    for candidate_id, items in occurrences.items():
        state.setdefault(candidate_id, {})["additional_occurrences"] = items
    return state


def export_review_bundle(manifest: dict, events: list[dict]) -> dict:
    validate_manifest(manifest)
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "review_id": manifest["review_id"],
        "source": deepcopy(manifest["source"]),
        "candidate_ids": [candidate["candidate_id"] for candidate in manifest["candidates"]],
        "events": deepcopy(events),
        "effective_state": replay_effective_state(events),
        "authority": deepcopy(AUTHORITY_CLOSED),
        "canonical_write_authorized": False,
        "canonical_write_performed": False,
    }
