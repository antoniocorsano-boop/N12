#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any

RECEIPT_TYPE = "CEW_PRECISION_GCP_RECEIPT_V1"
SOURCE_FIELDS = ("source_version_id", "page_id", "evidence_region_id", "source_sha256")
FEATURE_TYPES = {"COLUMN_CENTER", "GRID_INTERSECTION", "DOCUMENT_CONTROL_POINT"}
SELECTION_METHODS = {"HUMAN_DOCUMENT_SNAP", "HUMAN_EXPLICIT_POINT"}


def _raw(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(_raw(value).encode("utf-8")).hexdigest()


def source_evidence_from_context(ctx: dict[str, Any]) -> dict[str, str]:
    source = ctx.get("source") or {}
    binding = ctx.get("binding") or {}
    page = ctx.get("page") or {}
    region = ctx.get("region") or {}
    evidence = {
        "source_version_id": str(binding.get("source_version_id", "")).strip(),
        "page_id": str(page.get("page_id", binding.get("page_id", ""))).strip(),
        "evidence_region_id": str(region.get("evidence_region_id", binding.get("evidence_region_id", ""))).strip(),
        "source_sha256": str(source.get("sha256", "")).strip().lower(),
    }
    if not all(evidence.values()):
        raise ValueError("PRECISION_GCP_SOURCE_EVIDENCE_INCOMPLETE")
    return evidence


def _number(payload: dict[str, Any], field: str) -> float:
    try:
        value = float(payload[field])
    except Exception as exc:
        raise ValueError(f"PRECISION_GCP_{field.upper()}_REQUIRED") from exc
    if not math.isfinite(value):
        raise ValueError(f"PRECISION_GCP_{field.upper()}_NONFINITE")
    return value


def build_receipt(
    *,
    task_id: str,
    revision: str,
    reviewer: str,
    payload: dict[str, Any],
    expected_source: dict[str, str],
    timestamp: str | None = None,
) -> dict[str, Any]:
    task_id = task_id.strip()
    revision = revision.strip()
    reviewer = reviewer.strip()
    if not task_id:
        raise ValueError("PRECISION_GCP_TASK_REQUIRED")
    if not revision:
        raise ValueError("PRECISION_GCP_REVISION_REQUIRED")
    if not reviewer:
        raise ValueError("PRECISION_GCP_REVIEWER_REQUIRED")
    if not isinstance(payload, dict):
        raise ValueError("PRECISION_GCP_PAYLOAD_OBJECT_REQUIRED")

    supplied = payload.get("source_evidence")
    if not isinstance(supplied, dict):
        raise ValueError("PRECISION_GCP_SOURCE_EVIDENCE_REQUIRED")
    for field in SOURCE_FIELDS:
        if str(supplied.get(field, "")).strip().lower() != expected_source[field].lower():
            raise ValueError(f"PRECISION_GCP_SOURCE_MISMATCH_{field.upper()}")

    support_id = str(payload.get("support_id", "")).strip()
    if not support_id:
        raise ValueError("PRECISION_GCP_SUPPORT_ID_REQUIRED")
    feature_type = str(payload.get("feature_type", "")).strip()
    if feature_type not in FEATURE_TYPES:
        raise ValueError("PRECISION_GCP_FEATURE_TYPE_INVALID")
    selection_method = str(payload.get("selection_method", "")).strip()
    if selection_method not in SELECTION_METHODS:
        raise ValueError("PRECISION_GCP_SELECTION_METHOD_INVALID")
    if payload.get("human_attestation") is not True:
        raise ValueError("PRECISION_GCP_HUMAN_ATTESTATION_REQUIRED")
    if payload.get("navigation_only") is not True:
        raise ValueError("PRECISION_GCP_NAVIGATION_ONLY_REQUIRED")
    for forbidden in ("canonical_write_authorized", "canonical_geometry_authorized", "structural_identity_authorized"):
        if payload.get(forbidden) is True:
            raise ValueError(f"PRECISION_GCP_FORBIDDEN_AUTHORITY_{forbidden.upper()}")

    predicted_x = _number(payload, "predicted_native_x_px")
    predicted_y = _number(payload, "predicted_native_y_px")
    snapped_x = _number(payload, "snapped_native_x_px")
    snapped_y = _number(payload, "snapped_native_y_px")
    common_x = _number(payload, "common_x_m")
    common_y = _number(payload, "common_y_m")
    residual_dx = snapped_x - predicted_x
    residual_dy = snapped_y - predicted_y
    residual_norm = math.hypot(residual_dx, residual_dy)

    normalized_payload = dict(payload)
    normalized_payload.update({
        "support_id": support_id,
        "feature_type": feature_type,
        "selection_method": selection_method,
        "predicted_native_x_px": predicted_x,
        "predicted_native_y_px": predicted_y,
        "snapped_native_x_px": snapped_x,
        "snapped_native_y_px": snapped_y,
        "common_x_m": common_x,
        "common_y_m": common_y,
        "residual_dx_px": residual_dx,
        "residual_dy_px": residual_dy,
        "residual_norm_px": residual_norm,
        "gcp_state": "HUMAN_VERIFIED_STRUCTURAL_GCP",
        "locator_promotion_authorized": False,
        "canonical_write_authorized": False,
        "canonical_geometry_authorized": False,
        "structural_identity_authorized": False,
    })
    payload_fp = fingerprint(normalized_payload)
    decision_seed = {
        "task_id": task_id,
        "revision": revision,
        "reviewer": reviewer,
        "support_id": support_id,
        "feature_type": feature_type,
        "payload_fingerprint": payload_fp,
    }
    decision_id = "GCP-" + fingerprint(decision_seed)[:24]
    receipt = {
        "receipt_type": RECEIPT_TYPE,
        "decision_id": decision_id,
        "task_id": task_id,
        "stage": "PR2_STRUCTURAL_GCP_CAPTURE",
        "revision": revision,
        "reviewer": reviewer,
        "source_evidence": dict(expected_source),
        "payload_fingerprint": payload_fp,
        "payload": normalized_payload,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "authority": "HUMAN_DOCUMENT_CONTROL_POINT_EVIDENCE",
        "engineering_authority_effect": "NONE",
        "canonical_write_authorized": False,
        "project_material_ready": False,
    }
    receipt["receipt_fingerprint"] = fingerprint({k: v for k, v in receipt.items() if k != "receipt_fingerprint"})
    return receipt


def index_receipts(receipts: list[dict[str, Any]], task_id: str) -> dict[str, dict[str, Any]]:
    rows = [r for r in receipts if r.get("receipt_type") == RECEIPT_TYPE and r.get("task_id") == task_id]
    rows.sort(key=lambda r: (str(r.get("timestamp", "")), str(r.get("decision_id", ""))))
    return {str(r["decision_id"]): r for r in rows if r.get("decision_id")}
