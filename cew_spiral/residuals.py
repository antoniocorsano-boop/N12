from __future__ import annotations

from copy import deepcopy
from typing import Any

from cew_spiral.contracts import COST_RANK


def normalize_residual(residual: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(residual, dict):
        raise ValueError("RESIDUAL_OBJECT_REQUIRED")
    residual_id = str(residual.get("residual_id") or "").strip()
    if not residual_id:
        raise ValueError("RESIDUAL_ID_REQUIRED")
    blocker_class = str(residual.get("blocker_class") or "").strip().upper()
    if not blocker_class:
        raise ValueError("RESIDUAL_BLOCKER_CLASS_REQUIRED")
    try:
        model_impact = int(residual.get("model_impact", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("RESIDUAL_MODEL_IMPACT_INVALID") from exc
    if model_impact < 0:
        raise ValueError("RESIDUAL_MODEL_IMPACT_INVALID")
    acquisition_cost_class = str(residual.get("acquisition_cost_class") or "").strip().upper()
    if acquisition_cost_class not in COST_RANK:
        raise ValueError("RESIDUAL_ACQUISITION_COST_INVALID")
    evidence = residual.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("RESIDUAL_EVIDENCE_REQUIRED")

    normalized = deepcopy(residual)
    normalized["residual_id"] = residual_id
    normalized["blocker_class"] = blocker_class
    normalized["model_impact"] = model_impact
    normalized["acquisition_cost_class"] = acquisition_cost_class
    normalized["primary_identity_required"] = bool(residual.get("primary_identity_required", False))
    normalized["evidence"] = {
        "qualified_source_native_available": bool(evidence.get("qualified_source_native_available", False)),
        "governed_raster_available": bool(evidence.get("governed_raster_available", False)),
        "historical_only": bool(evidence.get("historical_only", False)),
    }
    return normalized


def evidence_strength(residual: dict[str, Any]) -> int:
    evidence = residual["evidence"]
    if evidence["qualified_source_native_available"]:
        return 2
    if evidence["governed_raster_available"]:
        return 1
    return 0


def residual_priority_key(residual: dict[str, Any]) -> tuple[int, int, int, int, str]:
    return (
        0 if residual["blocker_class"] == "MODEL_RELATION" else 1,
        -int(residual["model_impact"]),
        -evidence_strength(residual),
        COST_RANK[residual["acquisition_cost_class"]],
        str(residual["residual_id"]),
    )


def normalize_and_order_residuals(residuals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(residuals, list) or not residuals:
        raise ValueError("RESIDUAL_QUEUE_REQUIRED")
    normalized = [normalize_residual(item) for item in residuals]
    ids = [item["residual_id"] for item in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError("RESIDUAL_ID_DUPLICATE")
    return sorted(normalized, key=residual_priority_key)
