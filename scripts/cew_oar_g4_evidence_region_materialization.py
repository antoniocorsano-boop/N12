#!/usr/bin/env python3
"""Materialize governed EvidenceRegionCandidate exports from confirmed G4 localization.

This module is deliberately non-canonical. It converts only human-confirmed
localization geometry into the already-governed EvidenceRegionCandidate model.
It does not create an EvidenceRegion, Observation, structural binding, OAR
classification confirmation, or canonical engineering state.
"""
from __future__ import annotations

from typing import Any

import cew_evidence_region_candidate as evidence_region_candidate
import cew_oar_g4_region_binding as region_binding

EXPORT_SCHEMA = "CEW_OAR_G4_EVIDENCE_REGION_CANDIDATE_EXPORT_v1"
PURPOSE = "OAR_G4_HUMAN_EVIDENCE_LOCALIZATION_FOR_F2_PROMOTION_REVIEW"


def _validate_report(report: dict[str, Any], contract: dict[str, Any]) -> None:
    if not isinstance(report, dict):
        raise ValueError("OAR_G4_ER_MATERIALIZATION_REPORT_REQUIRED")
    if report.get("pilot_id") != contract["pilot_id"]:
        raise ValueError("OAR_G4_ER_MATERIALIZATION_PILOT_MISMATCH")
    if report.get("binding_id") != contract["binding_id"]:
        raise ValueError("OAR_G4_ER_MATERIALIZATION_BINDING_MISMATCH")
    if report.get("document") != contract["document"]:
        raise ValueError("OAR_G4_ER_MATERIALIZATION_DOCUMENT_MISMATCH")
    if report.get("canonical_write_authorized") is not False:
        raise ValueError("OAR_G4_ER_MATERIALIZATION_CANONICAL_WRITE_REJECTED")
    if report.get("engineering_authority_effect") != "NONE":
        raise ValueError("OAR_G4_ER_MATERIALIZATION_ENGINEERING_AUTHORITY_REJECTED")

    objects = report.get("objects")
    if not isinstance(objects, list) or len(objects) != len(contract["objects"]):
        raise ValueError("OAR_G4_ER_MATERIALIZATION_OBJECT_SET_INVALID")
    expected_ids = {str(row["support_id"]) for row in contract["objects"]}
    actual_ids = {str(row.get("support_id", "")) for row in objects if isinstance(row, dict)}
    if actual_ids != expected_ids:
        raise ValueError("OAR_G4_ER_MATERIALIZATION_SUPPORT_SET_MISMATCH")


def _candidate_record(row: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    support_id = str(row.get("support_id", "")).strip()
    governed = region_binding.support_row(contract, support_id)
    if row.get("state") != "GEOMETRY_CONFIRMED":
        raise ValueError("OAR_G4_ER_MATERIALIZATION_REQUIRES_CONFIRMED_GEOMETRY")
    if row.get("evidence_object_id") != governed["evidence_object_id"]:
        raise ValueError("OAR_G4_ER_MATERIALIZATION_EVIDENCE_OBJECT_MISMATCH")
    if row.get("family_id") != governed["family_id"]:
        raise ValueError("OAR_G4_ER_MATERIALIZATION_FAMILY_CONTEXT_MISMATCH")
    confirmation_receipt_id = str(row.get("geometry_confirmation_receipt_id") or "").strip()
    if not confirmation_receipt_id:
        raise ValueError("OAR_G4_ER_MATERIALIZATION_CONFIRMATION_RECEIPT_REQUIRED")
    bbox = region_binding.normalize_bbox(row.get("bbox"))
    document = contract["document"]

    candidate = evidence_region_candidate.build_candidate(
        {
            "source_version_id": document["source_version_id"],
            "page_id": document["page_id"],
            "geometry_type": "BBOX",
            "coordinate_space": document["coordinate_system"],
            "x": bbox["x"],
            "y": bbox["y"],
            "width": bbox["w"],
            "height": bbox["h"],
            "author_type": "HUMAN",
            "purpose": PURPOSE,
            "human_note": f"Confirmed documentary localization for G4 support {support_id}",
            "originating_document_feature_candidate_id": governed["evidence_object_id"],
            "originating_task_id": contract["binding_id"],
            "target_entity_hint": None,
            "state": "PROPOSED",
        }
    )

    return {
        "support_id": support_id,
        "evidence_object_id": governed["evidence_object_id"],
        "oar_family_context": governed["family_id"],
        "oar_classification_confirmed": False,
        "geometry_confirmation_receipt_id": confirmation_receipt_id,
        "provenance": {
            "source_version_id": document["source_version_id"],
            "page_id": document["page_id"],
            "derived_asset_id": document["derived_asset_id"],
            "page_transform_id": document["page_transform_id"],
            "coordinate_system": document["coordinate_system"],
            "displayed_render_sha256": document["render_sha256"],
            "authority": "HUMAN_EVIDENCE_LOCALIZATION_ONLY",
        },
        "evidence_region_candidate": candidate,
    }


def build_export(report: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a non-persistent export pack for all confirmed G4 localizations."""
    contract = contract or region_binding.load_contract()
    _validate_report(report, contract)

    records = [
        _candidate_record(row, contract)
        for row in report["objects"]
        if row.get("state") == "GEOMETRY_CONFIRMED"
    ]
    confirmed_count = len(records)
    total = len(contract["objects"])
    return {
        "schema": EXPORT_SCHEMA,
        "pilot_id": contract["pilot_id"],
        "binding_id": contract["binding_id"],
        "source_authority": "IMMUTABLE_SOURCEVERSION_AND_REGISTERED_PAGE",
        "records": records,
        "summary": {
            "pilot_total": total,
            "geometry_confirmed": confirmed_count,
            "evidence_region_candidates_exported": confirmed_count,
            "remaining_without_confirmed_geometry": total - confirmed_count,
            "canonical_evidence_regions_materialized": 0,
            "oar_classification_confirmed": 0,
        },
        "candidate_is_evidence_region": False,
        "f2_registry_written": False,
        "observation_created": False,
        "structural_binding_created": False,
        "oar_human_confirmation": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "next_gate": "F2_PROMOTION_REVIEW_REQUIRED" if records else "CONFIRM_DOCUMENTARY_GEOMETRY_FIRST",
    }


def build_export_from_receipts(
    receipts: list[dict[str, Any]], contract: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Replay governed localization receipts before producing the export pack."""
    contract = contract or region_binding.load_contract()
    report = region_binding.aggregate(receipts, contract)
    return build_export(report, contract)
