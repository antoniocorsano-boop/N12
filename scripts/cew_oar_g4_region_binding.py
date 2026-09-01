#!/usr/bin/env python3
"""Governed human-in-the-loop geometry binding for the G4 / TAV-05S OAR pilot.

This module deliberately separates three authorities:
1. a working bbox proposal on the verified full page;
2. explicit human confirmation that the bbox localizes the documentary object;
3. OAR classification confirmation / canonical EvidenceRegion materialization.

Only (1) and (2) live here. Runtime receipts are audit evidence only and never
write the canonical EvidenceRegion registry directly.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_OAR_G4_COLUMN_REGION_BINDING_v1.json"

RECEIPT_TYPE = "CEW_OAR_REGION_GEOMETRY_RECEIPT_v1"
PROPOSAL_ACTION = "PROPOSE_GEOMETRY"
CONFIRM_ACTION = "CONFIRM_GEOMETRY"


def load_contract(path: Path = CONTRACT) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_contract(payload)
    return payload


def validate_contract(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "CEW_OAR_G4_COLUMN_REGION_BINDING_v1":
        raise ValueError("OAR_REGION_BINDING_SCHEMA_INVALID")
    document = payload.get("document")
    if not isinstance(document, dict):
        raise ValueError("OAR_REGION_BINDING_DOCUMENT_REQUIRED")
    expected = {
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "derived_asset_id": "CEW-N12-ASSET-TAV05S-P001-300DPI",
        "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
        "coordinate_system": "NORMALIZED_0_1",
    }
    for key, value in expected.items():
        if document.get(key) != value:
            raise ValueError(f"OAR_REGION_BINDING_{key.upper()}_INVALID")
    objects = payload.get("objects")
    if not isinstance(objects, list) or len(objects) != 34:
        raise ValueError("OAR_REGION_BINDING_OBJECT_COUNT_INVALID")
    ids = [str(row.get("support_id", "")) for row in objects]
    if len(set(ids)) != 34 or any(not item for item in ids):
        raise ValueError("OAR_REGION_BINDING_SUPPORT_IDS_INVALID")
    if any(row.get("state") != "UNBOUND" for row in objects):
        raise ValueError("OAR_REGION_BINDING_CONTRACT_MUST_START_UNBOUND")
    workflow = payload.get("workflow", {})
    if workflow.get("canonical_write_authorized") is not False:
        raise ValueError("OAR_REGION_BINDING_CANONICAL_WRITE_MUST_BE_FALSE")
    if workflow.get("oar_classification_authority") != "SEPARATE_REVIEW_REQUIRED":
        raise ValueError("OAR_REGION_BINDING_AUTHORITY_COLLAPSE_REJECTED")


def normalize_bbox(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError("OAR_REGION_BBOX_REQUIRED")
    try:
        bbox = {key: float(value[key]) for key in ("x", "y", "w", "h")}
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("OAR_REGION_BBOX_INVALID") from exc
    if not all(0.0 <= bbox[key] <= 1.0 for key in bbox):
        raise ValueError("OAR_REGION_BBOX_OUT_OF_RANGE")
    if bbox["w"] <= 0.0 or bbox["h"] <= 0.0:
        raise ValueError("OAR_REGION_BBOX_EMPTY")
    if bbox["x"] + bbox["w"] > 1.0 or bbox["y"] + bbox["h"] > 1.0:
        raise ValueError("OAR_REGION_BBOX_EXCEEDS_PAGE")
    return bbox


def support_row(contract: dict[str, Any], support_id: str) -> dict[str, Any]:
    support_id = str(support_id).strip()
    row = next((item for item in contract["objects"] if str(item["support_id"]) == support_id), None)
    if row is None:
        raise ValueError("OAR_REGION_SUPPORT_NOT_IN_PILOT")
    return row


def build_receipt(
    *,
    decision_id: str,
    support_id: str,
    bbox: Any,
    action: str,
    actor: str = "AUTHENTICATED_OPERATOR",
    timestamp: str | None = None,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = contract or load_contract()
    row = support_row(contract, support_id)
    if action not in {PROPOSAL_ACTION, CONFIRM_ACTION}:
        raise ValueError("OAR_REGION_ACTION_INVALID")
    geometry = normalize_bbox(bbox)
    decision_id = str(decision_id).strip()
    if not decision_id:
        raise ValueError("OAR_REGION_DECISION_ID_REQUIRED")
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    document = contract["document"]
    return {
        "receipt_type": RECEIPT_TYPE,
        "decision_id": decision_id,
        "task_id": contract["binding_id"],
        "residual_id": row["evidence_object_id"],
        "timestamp": timestamp,
        "actor": actor,
        "action": action,
        "pilot_id": contract["pilot_id"],
        "binding_id": contract["binding_id"],
        "support_id": str(row["support_id"]),
        "evidence_object_id": row["evidence_object_id"],
        "family_id": row["family_id"],
        "source_version_id": document["source_version_id"],
        "page_id": document["page_id"],
        "derived_asset_id": document["derived_asset_id"],
        "page_transform_id": document["page_transform_id"],
        "coordinate_system": document["coordinate_system"],
        "bbox": geometry,
        "authority": (
            "WORKING_GEOMETRY_ONLY"
            if action == PROPOSAL_ACTION
            else "HUMAN_EVIDENCE_LOCALIZATION_ONLY"
        ),
        "oar_human_confirmation": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def aggregate(receipts: list[dict[str, Any]], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_contract()
    latest_proposal: dict[str, dict[str, Any]] = {}
    confirmed: dict[str, dict[str, Any]] = {}
    seen_decisions: set[str] = set()

    for receipt in receipts:
        if receipt.get("receipt_type") != RECEIPT_TYPE:
            continue
        decision_id = str(receipt.get("decision_id", ""))
        if not decision_id or decision_id in seen_decisions:
            raise ValueError("OAR_REGION_DUPLICATE_DECISION_ID")
        seen_decisions.add(decision_id)
        support_id = str(receipt.get("support_id", ""))
        row = support_row(contract, support_id)
        if receipt.get("evidence_object_id") != row["evidence_object_id"]:
            raise ValueError("OAR_REGION_OBJECT_ID_MISMATCH")
        document = contract["document"]
        for key in ("source_version_id", "page_id", "derived_asset_id", "page_transform_id", "coordinate_system"):
            if receipt.get(key) != document[key]:
                raise ValueError("OAR_REGION_DOCUMENT_BINDING_MISMATCH")
        bbox = normalize_bbox(receipt.get("bbox"))
        action = receipt.get("action")
        if action == PROPOSAL_ACTION:
            if support_id in confirmed:
                raise ValueError("OAR_REGION_GEOMETRY_ALREADY_CONFIRMED")
            latest_proposal[support_id] = {**receipt, "bbox": bbox}
        elif action == CONFIRM_ACTION:
            if support_id in confirmed:
                raise ValueError("OAR_REGION_GEOMETRY_ALREADY_CONFIRMED")
            proposal = latest_proposal.get(support_id)
            if proposal is None:
                raise ValueError("OAR_REGION_CONFIRMATION_WITHOUT_PROPOSAL")
            if bbox != proposal["bbox"]:
                raise ValueError("OAR_REGION_CONFIRMATION_BBOX_MISMATCH")
            confirmed[support_id] = {**receipt, "bbox": bbox}
        else:
            raise ValueError("OAR_REGION_ACTION_INVALID")

    objects = []
    for row in contract["objects"]:
        sid = str(row["support_id"])
        proposal = latest_proposal.get(sid)
        confirmation = confirmed.get(sid)
        state = "GEOMETRY_CONFIRMED" if confirmation else ("PROPOSED" if proposal else "UNBOUND")
        objects.append({
            **row,
            "state": state,
            "bbox": confirmation["bbox"] if confirmation else (proposal["bbox"] if proposal else None),
            "geometry_confirmation_receipt_id": confirmation["decision_id"] if confirmation else None,
            "oar_human_confirmation": False,
            "canonical_write_authorized": False,
        })
    counts = {state: sum(1 for row in objects if row["state"] == state) for state in ("UNBOUND", "PROPOSED", "GEOMETRY_CONFIRMED")}
    return {
        "state": "READY_FOR_REGION_LOCALIZATION",
        "pilot_id": contract["pilot_id"],
        "binding_id": contract["binding_id"],
        "document": contract["document"],
        "objects": objects,
        "summary": {
            "total": 34,
            **counts,
            "oar_human_confirmed": 0,
            "canonical_evidence_regions_materialized": 0,
        },
        "next_gate": "LOCALIZE_REMAINING_OBJECTS" if counts["UNBOUND"] else "GOVERNED_EVIDENCE_REGION_MATERIALIZATION_REVIEW",
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
