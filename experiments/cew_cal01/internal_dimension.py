from __future__ import annotations

import hashlib
import json
from typing import Any

from experiments.cew_cal01.exact_source import SOURCE_SHA256


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _stable_id(prefix: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return prefix + hashlib.sha256(encoded).hexdigest()[:20]


def select_internal_search_roi(perimeter_payload: dict[str, Any]) -> list[int]:
    """Return the exact-source structural envelope only after perimeter search closes empty."""

    if perimeter_payload.get("source", {}).get("sha256") != SOURCE_SHA256:
        raise RuntimeError("CAL01_INTERNAL_SOURCE_DIGEST_DRIFT")
    if perimeter_payload.get("historical_comparator_loaded") is not False:
        raise RuntimeError("CAL01_INTERNAL_HISTORICAL_INPUT_FORBIDDEN")
    if perimeter_payload.get("historical_affine_loaded") is not False:
        raise RuntimeError("CAL01_INTERNAL_HISTORICAL_INPUT_FORBIDDEN")
    if perimeter_payload.get("tav02s_evidence_loaded") is not False:
        raise RuntimeError("CAL01_INTERNAL_TAV02_INPUT_FORBIDDEN")
    if int(perimeter_payload.get("primary_anchor_count", -1)) != 0:
        raise RuntimeError("CAL01_INTERNAL_UPSTREAM_AUTHORITY_DRIFT")

    candidate_count = int(perimeter_payload.get("candidate_count", -1))
    status = str(perimeter_payload.get("status") or "")
    if candidate_count != 0 or status != "PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED":
        raise RuntimeError("CAL01_INTERNAL_SEARCH_DEFERRED_PERIMETER_CANDIDATES_PRESENT")

    raw_bbox = perimeter_payload.get("structural_plan_envelope", {}).get("envelope_bbox_source_px")
    if not isinstance(raw_bbox, (list, tuple)) or len(raw_bbox) != 4:
        raise RuntimeError("CAL01_INTERNAL_SOURCE_ENVELOPE_REQUIRED")
    bbox = [int(round(float(value))) for value in raw_bbox]
    left, top, right, bottom = bbox
    if left < 0 or top < 0 or right <= left or bottom <= top:
        raise RuntimeError("CAL01_INTERNAL_SOURCE_ENVELOPE_INVALID")
    return bbox


def classify_internal_role_result(cluster: dict[str, Any], role_result: dict[str, Any]) -> dict[str, Any]:
    """Admit only semantic LINEAR_DIMENSION results to human-review candidate state."""

    cluster_index = int(cluster.get("cluster_index", -1))
    role = str(role_result.get("role") or "UNRESOLVED")
    reason = role_result.get("reason")

    if role != "LINEAR_DIMENSION":
        return {
            "accepted": False,
            "rejected": {
                "cluster_index": cluster_index,
                "role": role,
                "reason": reason,
                "engineering_authority_effect": "NONE",
            },
        }

    relation = role_result.get("dimension_relation")
    if not isinstance(relation, dict) or relation.get("confirmed") is not True:
        return {
            "accepted": False,
            "rejected": {
                "cluster_index": cluster_index,
                "role": "UNRESOLVED",
                "reason": "LINEAR_DIMENSION_WITHOUT_CONFIRMED_RELATION",
                "engineering_authority_effect": "NONE",
            },
        }
    endpoint_a = relation.get("endpoint_a_px")
    endpoint_b = relation.get("endpoint_b_px")
    if not isinstance(endpoint_a, (list, tuple)) or not isinstance(endpoint_b, (list, tuple)):
        return {
            "accepted": False,
            "rejected": {
                "cluster_index": cluster_index,
                "role": "UNRESOLVED",
                "reason": "LINEAR_DIMENSION_ENDPOINTS_REQUIRED",
                "engineering_authority_effect": "NONE",
            },
        }

    identity = {
        "cluster_index": cluster_index,
        "documented_text": role_result.get("documented_text"),
        "endpoint_a_px": [float(value) for value in endpoint_a],
        "endpoint_b_px": [float(value) for value in endpoint_b],
    }
    candidate = {
        "candidate_id": _stable_id("CEW-CAL01-INTDIM-", identity),
        "cluster_index": cluster_index,
        "semantic_role": "INTERNAL_LINEAR_DIMENSION_CANDIDATE",
        "documented_text": role_result.get("documented_text"),
        "role_reason": reason,
        "dimension_relation": dict(relation),
        "primary_visual_validation_required": True,
        "validation_state": "HUMAN_REVIEW_REQUIRED",
        "fit_eligible": False,
        "eligible_for_anchor": False,
        "metric_anchor_promoted": False,
        "engineering_authority_effect": "NONE",
    }
    return {"accepted": True, "candidate": candidate}
