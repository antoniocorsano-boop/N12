from __future__ import annotations

from copy import deepcopy
from typing import Any

from cew_spiral.contracts import CLOSED_AUTHORITY_KEYS, ROUTE_SCHEMA
from cew_spiral.receipt import build_route_receipt
from cew_spiral.residuals import evidence_strength, normalize_and_order_residuals


def _validate_authority(authority: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(authority, dict):
        raise ValueError("ROUTER_AUTHORITY_SNAPSHOT_REQUIRED")
    snapshot = deepcopy(authority)
    for key in CLOSED_AUTHORITY_KEYS:
        if snapshot.get(key) is True:
            raise ValueError("ROUTER_AUTHORITY_ESCALATION_FORBIDDEN")
    if snapshot.get("engineering_authority_effect") not in (None, "NONE"):
        raise ValueError("ROUTER_AUTHORITY_ESCALATION_FORBIDDEN")
    return snapshot


def _route_for(residual: dict[str, Any]) -> tuple[str, str]:
    evidence = residual["evidence"]
    if residual["primary_identity_required"] and evidence["historical_only"]:
        return "BLOCKED_NEEDS_PRIMARY_OR_MANUAL_EVIDENCE", "MANUAL_OR_NEW_PRIMARY_EVIDENCE"
    if evidence["qualified_source_native_available"]:
        return "ROUTE_SELECTED", "QUALIFIED_SOURCE_NATIVE"
    if evidence["governed_raster_available"]:
        return "ROUTE_SELECTED", "GOVERNED_RASTER_OCR"
    return "EVIDENCE_ACQUISITION_REQUIRED", "MANUAL_OR_NEW_PRIMARY_EVIDENCE"


def route_next_residual(
    residuals: list[dict[str, Any]],
    *,
    authority: dict[str, Any],
) -> dict[str, Any]:
    """Select the next bounded residual and evidence route deterministically.

    Selection order is fixed by CEW-SPIRAL-01:
    model-relation blocker -> model impact -> evidence strength -> acquisition
    cost -> stable residual id. The router chooses work only; it cannot change
    CEW authority or decide structural truth.
    """

    authority_before = _validate_authority(authority)
    ordered = normalize_and_order_residuals(residuals)
    selected = ordered[0]
    state, route = _route_for(selected)
    authority_after = deepcopy(authority_before)

    decision = {
        "schema": ROUTE_SCHEMA,
        "selected_residual_id": selected["residual_id"],
        "state": state,
        "route": route,
        "selected_residual": deepcopy(selected),
        "selection_basis": {
            "blocker_class": selected["blocker_class"],
            "model_impact": selected["model_impact"],
            "evidence_strength": evidence_strength(selected),
            "acquisition_cost_class": selected["acquisition_cost_class"],
            "stable_residual_id": selected["residual_id"],
        },
        "residual_priority_order": [item["residual_id"] for item in ordered],
        "authority_before": authority_before,
        "authority_after": authority_after,
        "promotion_authorized": False,
        "structural_truth_decided": False,
        "human_review_required_for_promotion": True,
    }
    decision["receipt"] = build_route_receipt(decision)
    return decision
