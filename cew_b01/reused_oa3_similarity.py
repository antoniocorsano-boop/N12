from __future__ import annotations

"""Bounded reuse of CEW OA-3 deterministic similarity.

Source capability: CEW-CAP-OA3-DETERMINISTIC-SIMILARITY-V1
Source PR: #116
Source ref: a7020bef3934156c917f5bfe975d888c6ba9e684
Source path: scripts/cew_oa3_deterministic_similarity.py

This module is a dependency-local port for CEW-B01. It preserves OA-3's
proposal-only authority boundary and is not a new B01 similarity subsystem.
"""

from math import atan2, degrees, hypot
from typing import Any

OA3_CAPABILITY_ID = "CEW-CAP-OA3-DETERMINISTIC-SIMILARITY-V1"
OA3_SOURCE_PR = 116
OA3_SOURCE_REF = "a7020bef3934156c917f5bfe975d888c6ba9e684"
OA3_SOURCE_PATH = "scripts/cew_oa3_deterministic_similarity.py"

WEIGHTS = {
    "GEOMETRY_KIND": 0.30,
    "DIMENSION_RATIO": 0.20,
    "ORIENTATION": 0.15,
    "TOPOLOGY_HINT": 0.15,
    "SPATIAL_CONTEXT": 0.10,
    "ASSOCIATED_TEXT": 0.10,
}


def _line_features(obj: dict[str, Any]) -> dict[str, float] | None:
    geometry = obj.get("geometry") or {}
    if geometry.get("type") != "LINE":
        return None
    first, second = geometry.get("a"), geometry.get("b")
    if not (
        isinstance(first, list)
        and isinstance(second, list)
        and len(first) >= 2
        and len(second) >= 2
    ):
        return None
    dx = float(second[0]) - float(first[0])
    dy = float(second[1]) - float(first[1])
    return {
        "length": hypot(dx, dy),
        "angle": degrees(atan2(dy, dx)) % 180.0,
    }


def _value(obj: dict[str, Any], *keys: str) -> Any:
    properties = obj.get("properties") or {}
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
        if key in properties and properties[key] is not None:
            return properties[key]
    return None


def _text_tokens(value: Any) -> set[str]:
    if not value:
        return set()
    raw = str(value).upper().replace("×", "X")
    for separator in ",;:/()[]{}-_":
        raw = raw.replace(separator, " ")
    return {token for token in raw.split() if token}


def _score_signal(
    name: str,
    prototype_anchor: dict[str, Any],
    candidate: dict[str, Any],
) -> tuple[float, str]:
    prototype_geometry = prototype_anchor.get("geometry") or {}
    candidate_geometry = candidate.get("geometry") or {}

    if name == "GEOMETRY_KIND":
        same = bool(prototype_geometry.get("type")) and (
            prototype_geometry.get("type") == candidate_geometry.get("type")
        )
        return (
            1.0 if same else 0.0,
            "GEOMETRY_KIND_MATCH" if same else "GEOMETRY_KIND_MISMATCH",
        )

    if name == "DIMENSION_RATIO":
        prototype_line = _line_features(prototype_anchor)
        candidate_line = _line_features(candidate)
        if prototype_line and candidate_line and prototype_line["length"] > 0 and candidate_line["length"] > 0:
            ratio = min(prototype_line["length"], candidate_line["length"]) / max(
                prototype_line["length"], candidate_line["length"]
            )
            return ratio, f"LENGTH_RATIO_{ratio:.3f}"
        prototype_dimension = _value(prototype_anchor, "dimension_ratio", "aspect_ratio")
        candidate_dimension = _value(candidate, "dimension_ratio", "aspect_ratio")
        if prototype_dimension is None or candidate_dimension is None:
            return 0.0, "DIMENSION_RATIO_UNAVAILABLE"
        delta = abs(float(prototype_dimension) - float(candidate_dimension))
        score = max(0.0, 1.0 - min(delta, 1.0))
        return score, f"DIMENSION_RATIO_DELTA_{delta:.3f}"

    if name == "ORIENTATION":
        prototype_line = _line_features(prototype_anchor)
        candidate_line = _line_features(candidate)
        if prototype_line and candidate_line:
            delta = abs(prototype_line["angle"] - candidate_line["angle"])
            delta = min(delta, 180.0 - delta)
            score = max(0.0, 1.0 - delta / 90.0)
            return score, f"ORIENTATION_DELTA_{delta:.1f}"
        prototype_orientation = _value(prototype_anchor, "orientation")
        candidate_orientation = _value(candidate, "orientation")
        if prototype_orientation is None or candidate_orientation is None:
            return 0.0, "ORIENTATION_UNAVAILABLE"
        same = str(prototype_orientation).upper() == str(candidate_orientation).upper()
        return 1.0 if same else 0.0, "ORIENTATION_MATCH" if same else "ORIENTATION_MISMATCH"

    if name == "TOPOLOGY_HINT":
        prototype_topology = _value(prototype_anchor, "topology_hint", "connection_count")
        candidate_topology = _value(candidate, "topology_hint", "connection_count")
        if prototype_topology is None or candidate_topology is None:
            return 0.0, "TOPOLOGY_UNAVAILABLE"
        same = str(prototype_topology) == str(candidate_topology)
        return 1.0 if same else 0.25, "TOPOLOGY_MATCH" if same else "TOPOLOGY_DIFFERENT"

    if name == "SPATIAL_CONTEXT":
        prototype_context = _value(prototype_anchor, "spatial_context", "context_role")
        candidate_context = _value(candidate, "spatial_context", "context_role")
        if prototype_context is None or candidate_context is None:
            return 0.0, "SPATIAL_CONTEXT_UNAVAILABLE"
        same = str(prototype_context).upper() == str(candidate_context).upper()
        return 1.0 if same else 0.0, "SPATIAL_CONTEXT_MATCH" if same else "SPATIAL_CONTEXT_MISMATCH"

    if name == "ASSOCIATED_TEXT":
        prototype_tokens = _text_tokens(
            _value(prototype_anchor, "associated_text", "text", "label")
        )
        candidate_tokens = _text_tokens(
            _value(candidate, "associated_text", "text", "label")
        )
        if not prototype_tokens or not candidate_tokens:
            return 0.0, "ASSOCIATED_TEXT_UNAVAILABLE"
        overlap = len(prototype_tokens & candidate_tokens) / len(
            prototype_tokens | candidate_tokens
        )
        return overlap, f"ASSOCIATED_TEXT_JACCARD_{overlap:.3f}"

    raise ValueError(f"OA3_UNKNOWN_SIGNAL:{name}")


def find_similar(
    scene: dict[str, Any],
    prototype: dict[str, Any],
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    if prototype.get("state") != "HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE":
        raise ValueError("OA3_HUMAN_TAUGHT_PROTOTYPE_REQUIRED")

    anchor_id = str(prototype.get("anchor_object_id", ""))
    anchor = next(
        (item for item in scene.get("objects", []) if item.get("object_id") == anchor_id),
        None,
    )
    if anchor is None:
        raise ValueError("OA3_PROTOTYPE_ANCHOR_NOT_IN_SCENE")

    source = scene.get("source") or {}
    evidence = prototype.get("source_evidence") or {}
    for key in ("source_version_id", "page_id", "evidence_region_id", "source_sha256"):
        if source.get(key) != evidence.get(key):
            raise ValueError("OA3_SOURCE_REVISION_MISMATCH")

    active_weights = dict(WEIGHTS if weights is None else weights)
    if set(active_weights) != set(WEIGHTS):
        raise ValueError("OA3_WEIGHT_SIGNAL_SET_MISMATCH")
    total = sum(float(value) for value in active_weights.values())
    if total <= 0:
        raise ValueError("OA3_INVALID_WEIGHTS")
    active_weights = {
        key: float(value) / total for key, value in active_weights.items()
    }

    rows: list[dict[str, Any]] = []
    for candidate in scene.get("objects", []):
        if candidate.get("object_id") == anchor_id:
            continue
        signal_scores: dict[str, float] = {}
        reasons: list[str] = []
        score = 0.0
        for signal, weight in active_weights.items():
            value, reason = _score_signal(signal, anchor, candidate)
            signal_scores[signal] = round(value, 6)
            reasons.append(reason)
            score += weight * value
        score = round(score, 6)
        state = (
            "STRONG_SIMILAR"
            if score >= 0.75
            else "POSSIBLE_SIMILAR"
            if score >= 0.50
            else "WEAK"
            if score > 0
            else "EXCLUDED"
        )
        rows.append(
            {
                "candidate_object_id": candidate.get("object_id"),
                "score": score,
                "state": state,
                "signal_scores": signal_scores,
                "reason_codes": reasons,
                "proposed_object_type": prototype.get("object_type"),
                "proposed_family_id": prototype.get("family_id"),
                "human_confirmation_required": True,
                "object_type_created": False,
                "family_membership_created": False,
                "structural_identity_created": False,
                "canonical_write_authorized": False,
            }
        )

    rows.sort(key=lambda row: (-row["score"], str(row["candidate_object_id"])))
    return {
        "state": "DETERMINISTIC_SIMILARITY_CANDIDATES",
        "prototype_id": prototype.get("prototype_id"),
        "object_type": prototype.get("object_type"),
        "family_id": prototype.get("family_id"),
        "weights": active_weights,
        "candidate_count": len(rows),
        "candidates": rows,
        "reuse_provenance": {
            "capability_id": OA3_CAPABILITY_ID,
            "source_pr": OA3_SOURCE_PR,
            "source_ref": OA3_SOURCE_REF,
            "source_path": OA3_SOURCE_PATH,
        },
        "auto_confirm_cluster_authorized": False,
        "structural_identity_created": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "next_gate": "OA-4_CLUSTER_REVIEW",
    }
