from __future__ import annotations

from math import atan2, degrees, hypot
from typing import Any


SOURCE_CAPABILITIES = {
    "prototype_memory": {
        "source": "PR#137",
        "ref": "320755e66a7263f1842f73dc14fb9a0ea8ccd7f8",
        "schema": "CEW_PROTOTYPE_MEMORY_v1",
    },
    "deterministic_similarity": {
        "source": "PR#116",
        "ref": "a7020bef3934156c917f5bfe975d888c6ba9e684",
        "weights": {
            "GEOMETRY_KIND": 0.30,
            "DIMENSION_RATIO": 0.20,
            "ORIENTATION": 0.15,
            "TOPOLOGY_HINT": 0.15,
            "SPATIAL_CONTEXT": 0.10,
            "ASSOCIATED_TEXT": 0.10,
        },
    },
}

WEIGHTS = dict(SOURCE_CAPABILITIES["deterministic_similarity"]["weights"])


def _line_features(obj: dict[str, Any]) -> dict[str, float] | None:
    geometry = obj.get("geometry") or {}
    if geometry.get("type") != "LINE":
        return None
    a, b = geometry.get("a"), geometry.get("b")
    if not (isinstance(a, list) and isinstance(b, list) and len(a) >= 2 and len(b) >= 2):
        return None
    dx = float(b[0]) - float(a[0])
    dy = float(b[1]) - float(a[1])
    length = hypot(dx, dy)
    return {"length": length, "angle": degrees(atan2(dy, dx)) % 180.0}


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


def _score_signal(name: str, anchor: dict[str, Any], candidate: dict[str, Any]) -> tuple[float, str]:
    anchor_geometry = anchor.get("geometry") or {}
    candidate_geometry = candidate.get("geometry") or {}

    if name == "GEOMETRY_KIND":
        same = bool(anchor_geometry.get("type")) and anchor_geometry.get("type") == candidate_geometry.get("type")
        return (1.0 if same else 0.0, "GEOMETRY_KIND_MATCH" if same else "GEOMETRY_KIND_MISMATCH")

    if name == "DIMENSION_RATIO":
        left = _line_features(anchor)
        right = _line_features(candidate)
        if left and right and left["length"] > 0 and right["length"] > 0:
            ratio = min(left["length"], right["length"]) / max(left["length"], right["length"])
            return ratio, f"LENGTH_RATIO_{ratio:.3f}"
        left_ratio = _value(anchor, "dimension_ratio", "aspect_ratio")
        right_ratio = _value(candidate, "dimension_ratio", "aspect_ratio")
        if left_ratio is None or right_ratio is None:
            return 0.0, "DIMENSION_RATIO_UNAVAILABLE"
        delta = abs(float(left_ratio) - float(right_ratio))
        return max(0.0, 1.0 - min(delta, 1.0)), f"DIMENSION_RATIO_DELTA_{delta:.3f}"

    if name == "ORIENTATION":
        left = _line_features(anchor)
        right = _line_features(candidate)
        if left and right:
            delta = abs(left["angle"] - right["angle"])
            delta = min(delta, 180.0 - delta)
            return max(0.0, 1.0 - delta / 90.0), f"ORIENTATION_DELTA_{delta:.1f}"
        left_orientation = _value(anchor, "orientation")
        right_orientation = _value(candidate, "orientation")
        if left_orientation is None or right_orientation is None:
            return 0.0, "ORIENTATION_UNAVAILABLE"
        same = str(left_orientation).upper() == str(right_orientation).upper()
        return (1.0 if same else 0.0, "ORIENTATION_MATCH" if same else "ORIENTATION_MISMATCH")

    if name == "TOPOLOGY_HINT":
        left = _value(anchor, "topology_hint", "connection_count")
        right = _value(candidate, "topology_hint", "connection_count")
        if left is None or right is None:
            return 0.0, "TOPOLOGY_UNAVAILABLE"
        same = str(left) == str(right)
        return (1.0 if same else 0.25, "TOPOLOGY_MATCH" if same else "TOPOLOGY_DIFFERENT")

    if name == "SPATIAL_CONTEXT":
        left = _value(anchor, "spatial_context", "context_role")
        right = _value(candidate, "spatial_context", "context_role")
        if left is None or right is None:
            return 0.0, "SPATIAL_CONTEXT_UNAVAILABLE"
        same = str(left).upper() == str(right).upper()
        return (1.0 if same else 0.0, "SPATIAL_CONTEXT_MATCH" if same else "SPATIAL_CONTEXT_MISMATCH")

    if name == "ASSOCIATED_TEXT":
        left_tokens = _text_tokens(_value(anchor, "associated_text", "text", "label"))
        right_tokens = _text_tokens(_value(candidate, "associated_text", "text", "label"))
        if not left_tokens or not right_tokens:
            return 0.0, "ASSOCIATED_TEXT_UNAVAILABLE"
        overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
        return overlap, f"ASSOCIATED_TEXT_JACCARD_{overlap:.3f}"

    raise ValueError(f"SPIRAL_UNKNOWN_SIMILARITY_SIGNAL:{name}")


def _validate_memory(memory: dict[str, Any]) -> None:
    if memory.get("schema") != "CEW_PROTOTYPE_MEMORY_v1" or memory.get("scope") != "PROJECT_LOCAL":
        raise ValueError("PROJECT_LOCAL_MEMORY_REQUIRED")
    authority = memory.get("authority") or {}
    if authority.get("canonical_write_authorized") is not False:
        raise ValueError("PROTOTYPE_MEMORY_AUTHORITY_DRIFT")
    if authority.get("structural_identity_authorized") is not False:
        raise ValueError("PROTOTYPE_MEMORY_AUTHORITY_DRIFT")
    if authority.get("engineering_authority_effect") != "NONE":
        raise ValueError("PROTOTYPE_MEMORY_AUTHORITY_DRIFT")
    if authority.get("human_project_validation_required") is not True:
        raise ValueError("PROTOTYPE_MEMORY_AUTHORITY_DRIFT")


def _validated_examples(scene: dict[str, Any], memory: dict[str, Any]) -> tuple[list[dict[str, Any]], set[str], list[str]]:
    source_version_id = str((scene.get("source") or {}).get("source_version_id") or "")
    if not source_version_id:
        raise ValueError("SCENE_SOURCE_REVISION_REQUIRED")

    examples = memory.get("examples") or []
    if not isinstance(examples, list):
        raise ValueError("PROTOTYPE_MEMORY_EXAMPLES_INVALID")

    positives: list[dict[str, Any]] = []
    negative_ids: set[str] = set()
    ambiguous_ids: list[str] = []
    for example in examples:
        if not isinstance(example, dict):
            raise ValueError("PROTOTYPE_MEMORY_EXAMPLES_INVALID")
        role = str(example.get("role") or "").upper()
        candidate_id = str(example.get("candidate_id") or "")
        example_source = str(example.get("source_version_id") or "")
        if role not in {"POSITIVE", "NEGATIVE", "AMBIGUOUS"} or not candidate_id:
            raise ValueError("PROTOTYPE_MEMORY_EXAMPLE_INVALID")
        if example_source != source_version_id:
            raise ValueError("PROTOTYPE_SOURCE_REVISION_MISMATCH")
        if role == "POSITIVE":
            positives.append(example)
        elif role == "NEGATIVE":
            negative_ids.add(candidate_id)
        else:
            ambiguous_ids.append(candidate_id)

    if not positives:
        raise ValueError("HUMAN_TAUGHT_POSITIVE_REQUIRED")
    positives.sort(key=lambda row: str(row["candidate_id"]))
    ambiguous_ids.sort()
    return positives, negative_ids, ambiguous_ids


def rank_from_project_memory(scene: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    """Adapt PR #137 project-local memory into PR #116 deterministic ranking.

    This adapter does not learn, mutate prototype memory, create semantics, or
    promote structural identity. It only ranks review candidates from already
    governed human teaching receipts represented in CEW_PROTOTYPE_MEMORY_v1.
    """

    if not isinstance(scene, dict) or not isinstance(memory, dict):
        raise ValueError("SCENE_AND_MEMORY_REQUIRED")
    _validate_memory(memory)
    positives, negative_ids, ambiguous_ids = _validated_examples(scene, memory)

    objects = scene.get("objects") or []
    if not isinstance(objects, list):
        raise ValueError("SCENE_OBJECTS_INVALID")
    objects_by_id = {str(obj.get("object_id") or ""): obj for obj in objects if isinstance(obj, dict)}

    anchor_id = str(positives[0]["candidate_id"])
    anchor = objects_by_id.get(anchor_id)
    if anchor is None:
        raise ValueError("PROTOTYPE_ANCHOR_NOT_IN_SCENE")

    rows: list[dict[str, Any]] = []
    for candidate_id in sorted(objects_by_id):
        if candidate_id == anchor_id:
            continue
        candidate = objects_by_id[candidate_id]
        signal_scores: dict[str, float] = {}
        reason_codes: list[str] = []
        score = 0.0
        for signal, weight in WEIGHTS.items():
            value, reason = _score_signal(signal, anchor, candidate)
            signal_scores[signal] = round(value, 6)
            reason_codes.append(reason)
            score += float(weight) * value

        negative_penalty = candidate_id in negative_ids
        if negative_penalty:
            score *= 0.10
            reason_codes.append("HUMAN_NEGATIVE_EXAMPLE_PENALTY")

        score = round(score, 6)
        if score >= 0.75:
            state = "STRONG_SIMILAR"
        elif score >= 0.50:
            state = "POSSIBLE_SIMILAR"
        elif score > 0:
            state = "WEAK"
        else:
            state = "EXCLUDED"

        rows.append(
            {
                "candidate_object_id": candidate_id,
                "score": score,
                "state": state,
                "signal_scores": signal_scores,
                "reason_codes": reason_codes,
                "negative_example_penalty_applied": negative_penalty,
                "proposal_concept_id": memory.get("concept_id"),
                "proposed_meaning": memory.get("meaning"),
                "human_confirmation_required": True,
                "object_type_created": False,
                "family_membership_created": False,
                "structural_identity_created": False,
                "canonical_write_authorized": False,
            }
        )

    rows.sort(key=lambda row: (-float(row["score"]), str(row["candidate_object_id"])))
    return {
        "schema": "CEW_SPIRAL_PROTOTYPE_SIMILARITY_ADAPTER_v1",
        "state": "DETERMINISTIC_SIMILARITY_CANDIDATES",
        "project_id": memory.get("project_id"),
        "concept_id": memory.get("concept_id"),
        "prototype_anchor_id": anchor_id,
        "ignored_ambiguous_example_ids": ambiguous_ids,
        "weights": dict(WEIGHTS),
        "candidate_count": len(rows),
        "candidates": rows,
        "source_capabilities": SOURCE_CAPABILITIES,
        "auto_confirm_cluster_authorized": False,
        "structural_identity_created": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "next_gate": "HUMAN_CLUSTER_REVIEW",
    }
