#!/usr/bin/env python3
from __future__ import annotations

from math import atan2, degrees, hypot
from typing import Any

WEIGHTS = {
    "GEOMETRY_KIND": 0.20,
    "DIMENSION_RATIO": 0.30,
    "ORIENTATION": 0.15,
    "TOPOLOGY_HINT": 0.10,
    "SPATIAL_CONTEXT": 0.10,
    "ASSOCIATED_TEXT": 0.15,
}
STRONG_SIMILAR_MIN = 0.85
POSSIBLE_SIMILAR_MIN = 0.60


def _line_features(obj: dict[str, Any]) -> dict[str, float] | None:
    g = obj.get("geometry") or {}
    if g.get("type") != "LINE":
        return None
    a, b = g.get("a"), g.get("b")
    if not (isinstance(a, list) and isinstance(b, list) and len(a) >= 2 and len(b) >= 2):
        return None
    dx, dy = float(b[0]) - float(a[0]), float(b[1]) - float(a[1])
    length = hypot(dx, dy)
    angle = degrees(atan2(dy, dx)) % 180.0
    return {"length": length, "angle": angle}


def _section_features(obj: dict[str, Any]) -> dict[str, float] | None:
    sx = _value(obj, "section_x_cm")
    sy = _value(obj, "section_y_cm")
    if sx is None or sy is None:
        return None
    try:
        x, y = float(sx), float(sy)
    except (TypeError, ValueError):
        return None
    if x <= 0 or y <= 0:
        return None
    return {"x": x, "y": y}


def _value(obj: dict[str, Any], *keys: str):
    p = obj.get("properties") or {}
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
        if key in p and p[key] is not None:
            return p[key]
    return None


def _text_tokens(value: Any) -> set[str]:
    if not value:
        return set()
    raw = str(value).upper().replace("×", "X")
    for sep in ",;:/()[]{}-_":
        raw = raw.replace(sep, " ")
    return {token for token in raw.split() if token}


def _score_signal(name: str, prototype_anchor: dict[str, Any], candidate: dict[str, Any]) -> tuple[float, list[str]]:
    pg, cg = prototype_anchor.get("geometry") or {}, candidate.get("geometry") or {}
    if name == "GEOMETRY_KIND":
        same = bool(pg.get("type")) and pg.get("type") == cg.get("type")
        return (1.0 if same else 0.0, ["GEOMETRY_KIND_MATCH" if same else "GEOMETRY_KIND_MISMATCH"])

    if name == "DIMENSION_RATIO":
        ps, cs = _section_features(prototype_anchor), _section_features(candidate)
        if ps and cs:
            rx = min(ps["x"], cs["x"]) / max(ps["x"], cs["x"])
            ry = min(ps["y"], cs["y"]) / max(ps["y"], cs["y"])
            return (rx + ry) / 2.0, [f"SECTION_X_RATIO_{rx:.3f}", f"SECTION_Y_RATIO_{ry:.3f}"]
        pl, cl = _line_features(prototype_anchor), _line_features(candidate)
        if pl and cl and pl["length"] > 0 and cl["length"] > 0:
            ratio = min(pl["length"], cl["length"]) / max(pl["length"], cl["length"])
            return ratio, [f"LENGTH_RATIO_{ratio:.3f}"]
        pd = _value(prototype_anchor, "dimension_ratio", "aspect_ratio")
        cd = _value(candidate, "dimension_ratio", "aspect_ratio")
        if pd is None or cd is None:
            return 0.0, ["DIMENSION_RATIO_UNAVAILABLE"]
        delta = abs(float(pd) - float(cd))
        score = max(0.0, 1.0 - min(delta, 1.0))
        return score, [f"DIMENSION_RATIO_DELTA_{delta:.3f}"]

    if name == "ORIENTATION":
        po = _value(prototype_anchor, "orientation_class")
        co = _value(candidate, "orientation_class")
        if po is not None and co is not None:
            same = str(po) == str(co)
            return (1.0 if same else 0.0, ["ORIENTATION_CLASS_MATCH" if same else "ORIENTATION_CLASS_MISMATCH"])
        pl, cl = _line_features(prototype_anchor), _line_features(candidate)
        if pl and cl:
            delta = abs(pl["angle"] - cl["angle"])
            delta = min(delta, 180.0 - delta)
            score = max(0.0, 1.0 - delta / 90.0)
            return score, [f"ORIENTATION_DELTA_{delta:.1f}"]
        po = _value(prototype_anchor, "orientation")
        co = _value(candidate, "orientation")
        if po is None or co is None:
            return 0.0, ["ORIENTATION_UNAVAILABLE"]
        same = str(po).upper() == str(co).upper()
        return (1.0 if same else 0.0, ["ORIENTATION_MATCH" if same else "ORIENTATION_MISMATCH"])

    if name == "TOPOLOGY_HINT":
        p = _value(prototype_anchor, "topology_hint", "connection_count")
        c = _value(candidate, "topology_hint", "connection_count")
        if p is None or c is None:
            return 0.0, ["TOPOLOGY_UNAVAILABLE"]
        same = str(p) == str(c)
        return (1.0 if same else 0.25, ["TOPOLOGY_MATCH" if same else "TOPOLOGY_DIFFERENT"])

    if name == "SPATIAL_CONTEXT":
        p = _value(prototype_anchor, "spatial_context", "context_role")
        c = _value(candidate, "spatial_context", "context_role")
        if p is None or c is None:
            return 0.0, ["SPATIAL_CONTEXT_UNAVAILABLE"]
        same = str(p).upper() == str(c).upper()
        return (1.0 if same else 0.0, ["SPATIAL_CONTEXT_MATCH" if same else "SPATIAL_CONTEXT_MISMATCH"])

    if name == "ASSOCIATED_TEXT":
        pt = _text_tokens(_value(prototype_anchor, "associated_text", "text", "label"))
        ct = _text_tokens(_value(candidate, "associated_text", "text", "label"))
        if not pt or not ct:
            return 0.0, ["ASSOCIATED_TEXT_UNAVAILABLE"]
        overlap = len(pt & ct) / len(pt | ct)
        return overlap, [f"ASSOCIATED_TEXT_JACCARD_{overlap:.3f}"]

    raise ValueError(f"OA3_UNKNOWN_SIGNAL:{name}")


def find_similar(scene: dict[str, Any], prototype: dict[str, Any], weights: dict[str, float] | None = None) -> dict[str, Any]:
    if prototype.get("state") != "HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE":
        raise ValueError("OA3_HUMAN_TAUGHT_PROTOTYPE_REQUIRED")
    anchor_id = str(prototype.get("anchor_object_id", ""))
    anchor = next((o for o in scene.get("objects", []) if o.get("object_id") == anchor_id), None)
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
    total = sum(float(v) for v in active_weights.values())
    if total <= 0:
        raise ValueError("OA3_INVALID_WEIGHTS")
    active_weights = {k: float(v) / total for k, v in active_weights.items()}

    rows = []
    for candidate in scene.get("objects", []):
        if candidate.get("object_id") == anchor_id:
            continue
        signal_scores = {}
        reasons: list[str] = []
        score = 0.0
        for signal, weight in active_weights.items():
            value, signal_reasons = _score_signal(signal, anchor, candidate)
            signal_scores[signal] = round(value, 6)
            reasons.extend(signal_reasons)
            score += weight * value
        score = round(score, 6)
        state = "STRONG_SIMILAR" if score >= STRONG_SIMILAR_MIN else "POSSIBLE_SIMILAR" if score >= POSSIBLE_SIMILAR_MIN else "WEAK" if score > 0 else "EXCLUDED"
        rows.append({
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
        })

    rows.sort(key=lambda row: (-row["score"], str(row["candidate_object_id"])))
    return {
        "state": "DETERMINISTIC_SIMILARITY_CANDIDATES",
        "prototype_id": prototype.get("prototype_id"),
        "object_type": prototype.get("object_type"),
        "family_id": prototype.get("family_id"),
        "weights": active_weights,
        "thresholds": {"STRONG_SIMILAR_MIN": STRONG_SIMILAR_MIN, "POSSIBLE_SIMILAR_MIN": POSSIBLE_SIMILAR_MIN},
        "candidate_count": len(rows),
        "candidates": rows,
        "auto_confirm_cluster_authorized": False,
        "structural_identity_created": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "next_gate": "OA-4_CLUSTER_REVIEW",
    }
