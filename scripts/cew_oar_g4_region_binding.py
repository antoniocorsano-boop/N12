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
_CONFIRM_EQUIVALENCE_FIELDS = (
    "support_id",
    "evidence_object_id",
    "family_id",
    "pilot_id",
    "binding_id",
    "source_version_id",
    "page_id",
    "derived_asset_id",
    "page_transform_id",
    "coordinate_system",
    "base_proposal_decision_id",
    "authority",
    "oar_human_confirmation",
    "structural_identity_authorized",
    "canonical_write_authorized",
    "engineering_authority_effect",
)


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


def _receipt_timestamp(receipt: dict[str, Any]) -> datetime:
    raw = receipt.get("timestamp")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("OAR_REGION_TIMESTAMP_REQUIRED")
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("OAR_REGION_TIMESTAMP_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("OAR_REGION_TIMESTAMP_TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc)


def _ordered_receipts(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    governed = [receipt for receipt in receipts if receipt.get("receipt_type") == RECEIPT_TYPE]
    return sorted(
        governed,
        key=lambda receipt: (
            _receipt_timestamp(receipt),
            str(receipt.get("decision_id", "")),
        ),
    )


def _validate_receipt_governance(
    receipt: dict[str, Any],
    row: dict[str, Any],
    contract: dict[str, Any],
) -> str:
    action = receipt.get("action")
    if action not in {PROPOSAL_ACTION, CONFIRM_ACTION}:
        raise ValueError("OAR_REGION_ACTION_INVALID")

    document = contract["document"]
    expected = {
        "task_id": contract["binding_id"],
        "residual_id": row["evidence_object_id"],
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
        "authority": "WORKING_GEOMETRY_ONLY" if action == PROPOSAL_ACTION else "HUMAN_EVIDENCE_LOCALIZATION_ONLY",
        "oar_human_confirmation": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError(f"OAR_REGION_GOVERNED_FIELD_MISMATCH_{key.upper()}")
    anchor = receipt.get("base_proposal_decision_id")
    if anchor is not None and (not isinstance(anchor, str) or not anchor.strip()):
        raise ValueError("OAR_REGION_BASE_PROPOSAL_DECISION_ID_INVALID")
    return action


def _equivalent_confirmation(existing: dict[str, Any], receipt: dict[str, Any], bbox: dict[str, float]) -> bool:
    if receipt.get("action") != CONFIRM_ACTION:
        return False
    if any(existing.get(key) != receipt.get(key) for key in _CONFIRM_EQUIVALENCE_FIELDS):
        return False
    return existing.get("bbox") == bbox


def build_receipt(
    *,
    decision_id: str,
    support_id: str,
    bbox: Any,
    action: str,
    actor: str = "AUTHENTICATED_OPERATOR",
    timestamp: str | None = None,
    base_proposal_decision_id: str | None = None,
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
    if base_proposal_decision_id is not None:
        base_proposal_decision_id = str(base_proposal_decision_id).strip()
        if not base_proposal_decision_id:
            raise ValueError("OAR_REGION_BASE_PROPOSAL_DECISION_ID_INVALID")
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    _receipt_timestamp({"timestamp": timestamp})
    document = contract["document"]
    return {
        "receipt_type": RECEIPT_TYPE,
        "decision_id": decision_id,
        "task_id": contract["binding_id"],
        "residual_id": row["evidence_object_id"],
        "timestamp": timestamp,
        "actor": actor,
        "action": action,
        "base_proposal_decision_id": base_proposal_decision_id,
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
        "authority": "WORKING_GEOMETRY_ONLY" if action == PROPOSAL_ACTION else "HUMAN_EVIDENCE_LOCALIZATION_ONLY",
        "oar_human_confirmation": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def aggregate(receipts: list[dict[str, Any]], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_contract()
    latest_proposal: dict[str, dict[str, Any]] = {}
    proposal_history: dict[str, dict[str, dict[str, Any]]] = {}
    confirmed: dict[str, dict[str, Any]] = {}
    stale_transition_count = 0
    seen_decisions: set[str] = set()

    for receipt in _ordered_receipts(receipts):
        decision_id = str(receipt.get("decision_id", ""))
        if not decision_id or decision_id in seen_decisions:
            raise ValueError("OAR_REGION_DUPLICATE_DECISION_ID")
        seen_decisions.add(decision_id)
        support_id = str(receipt.get("support_id", ""))
        row = support_row(contract, support_id)
        action = _validate_receipt_governance(receipt, row, contract)
        bbox = normalize_bbox(receipt.get("bbox"))
        anchor = receipt.get("base_proposal_decision_id")
        history = proposal_history.setdefault(support_id, {})

        if action == PROPOSAL_ACTION:
            existing_confirmation = confirmed.get(support_id)
            if existing_confirmation is not None:
                # A proposal created from the same predecessor as an already-applied
                # confirmation is a concurrent loser. Keep it in audit history but
                # do not mutate state. Unanchored/other post-confirm proposals remain fatal.
                if anchor is not None and anchor == existing_confirmation.get("base_proposal_decision_id"):
                    stale_transition_count += 1
                    continue
                raise ValueError("OAR_REGION_GEOMETRY_ALREADY_CONFIRMED")

            current = latest_proposal.get(support_id)
            if current is not None and anchor is not None and anchor != current["decision_id"]:
                # Another replacement already advanced the proposal revision.
                stale_transition_count += 1
                continue
            if current is None and anchor is not None:
                # Anchored proposal references a revision that is not current/known.
                if anchor in history:
                    stale_transition_count += 1
                    continue
                raise ValueError("OAR_REGION_BASE_PROPOSAL_NOT_FOUND")

            proposal = {**receipt, "bbox": bbox}
            latest_proposal[support_id] = proposal
            history[decision_id] = proposal

        elif action == CONFIRM_ACTION:
            existing = confirmed.get(support_id)
            if existing is not None:
                if _equivalent_confirmation(existing, receipt, bbox):
                    continue
                # A confirmation anchored to a revision already consumed by the
                # winning confirmation is stale only if it confirms that exact prior bbox.
                anchored = history.get(str(anchor)) if anchor is not None else None
                if anchored is not None and anchored.get("bbox") == bbox:
                    stale_transition_count += 1
                    continue
                raise ValueError("OAR_REGION_GEOMETRY_ALREADY_CONFIRMED")

            proposal = latest_proposal.get(support_id)
            if proposal is None:
                raise ValueError("OAR_REGION_CONFIRMATION_WITHOUT_PROPOSAL")
            if anchor is not None and anchor != proposal["decision_id"]:
                anchored = history.get(str(anchor))
                if anchored is not None and anchored.get("bbox") == bbox:
                    # A concurrent replacement won first; this confirmation is bound
                    # to the previous proposal revision and cannot mutate the newer one.
                    stale_transition_count += 1
                    continue
                raise ValueError("OAR_REGION_BASE_PROPOSAL_MISMATCH")
            if bbox != proposal["bbox"]:
                raise ValueError("OAR_REGION_CONFIRMATION_BBOX_MISMATCH")
            confirmed[support_id] = {**receipt, "bbox": bbox}

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
            "geometry_proposal_receipt_id": proposal["decision_id"] if proposal else None,
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
            "stale_concurrent_transitions": stale_transition_count,
            "oar_human_confirmed": 0,
            "canonical_evidence_regions_materialized": 0,
        },
        "next_gate": "LOCALIZE_REMAINING_OBJECTS" if counts["UNBOUND"] else "GOVERNED_EVIDENCE_REGION_MATERIALIZATION_REVIEW",
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
