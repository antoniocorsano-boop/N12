#!/usr/bin/env python3
"""Prototype-led similar-object search for the G4 / TAV-05S OAR pilot.

This module reuses the CEW Object Acquisition domain primitives already present
in ``cew_object_acquisition.py``. A human-selected bbox becomes a project-local
training prototype; the search then ranks page-wide occurrence proposals by
geometric similarity to that example. Results are review aids only: they do not
assign support identity, confirm an OAR family, materialize EvidenceRegion, or
grant CAD/structural/engineering authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any

import cew_oar_g4_region_binding as binding
import cew_runtime_audit_store as audit_store
from cew_object_acquisition import (
    EvidenceProvenance,
    ObjectFamily,
    ObjectPrototype,
    ObjectSignature,
    ObjectType,
)

ROOT = Path(__file__).resolve().parents[1]
SNAP_JSON = ROOT / "artifacts" / "cew_oar_g4_assisted" / "snap_candidates.json"
RUNTIME_STORE = ROOT / "runtime" / "oar_g4_prototype_receipts"
RECEIPT_TYPE = "CEW_OAR_PROTOTYPE_TEACH_RECEIPT_v1"
MAX_RESULTS = 64


def _load_snap_payload() -> dict[str, Any]:
    payload = json.loads(SNAP_JSON.read_text(encoding="utf-8"))
    if payload.get("schema") != "CEW_OAR_G4_SNAP_CANDIDATES_v1":
        raise ValueError("OAR_PROTOTYPE_SNAP_SCHEMA_INVALID")
    if payload.get("authority", {}).get("snap_candidates_are_authority") is not False:
        raise ValueError("OAR_PROTOTYPE_SNAP_AUTHORITY_DRIFT")
    return payload


def _area(box: dict[str, float]) -> float:
    return float(box["w"]) * float(box["h"])


def _intersection_area(a: dict[str, float], b: dict[str, float]) -> float:
    ax1, ay1, ax2, ay2 = a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]
    bx1, by1, bx2, by2 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1)


def _iou(a: dict[str, float], b: dict[str, float]) -> float:
    inter = _intersection_area(a, b)
    union = _area(a) + _area(b) - inter
    return inter / union if union > 0 else 0.0


def _prototype_id(
    *, support_id: str, family_id: str, bbox: dict[str, float], decision_id: str, document: dict[str, Any]
) -> str:
    payload = {
        "support_id": support_id,
        "family_id": family_id,
        "bbox": bbox,
        "decision_id": decision_id,
        "source_version_id": document["source_version_id"],
        "page_id": document["page_id"],
        "page_transform_id": document["page_transform_id"],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "OPROT-G4-" + sha256(raw).hexdigest()[:20]


def _prototype_objects(
    *, support_id: str, family_id: str, bbox: dict[str, float], decision_id: str, document: dict[str, Any]
) -> tuple[ObjectPrototype, ObjectFamily]:
    ratio = bbox["w"] / bbox["h"]
    signature = ObjectSignature(
        cad_topology={"primitive": "HUMAN_RECTANGULAR_FOOTPRINT_EXAMPLE"},
        shape={"kind": "RECT", "bbox_aspect_ratio": round(ratio, 8)},
        dimensions={
            "normalized_width": round(bbox["w"], 10),
            "normalized_height": round(bbox["h"], 10),
        },
        context={
            "pilot_id": "OAR-PILOT-G4-COLUMNS",
            "support_id": support_id,
            "family_candidate": family_id,
            "source_sheet": "TAV-05S",
            "prototype_role": "PROJECT_LOCAL_HUMAN_TRAINING_EXAMPLE",
        },
    )
    prototype_id = _prototype_id(
        support_id=support_id,
        family_id=family_id,
        bbox=bbox,
        decision_id=decision_id,
        document=document,
    )
    provenance = EvidenceProvenance(
        source_version_id=document["source_version_id"],
        page_id=document["page_id"],
        evidence_region_id="",
        evidence_fingerprint=sha256(
            json.dumps(
                {
                    "source_version_id": document["source_version_id"],
                    "page_id": document["page_id"],
                    "page_transform_id": document["page_transform_id"],
                    "bbox": bbox,
                    "support_id": support_id,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        registration_id=decision_id,
    )
    prototype = ObjectPrototype(
        prototype_id=prototype_id,
        object_type=ObjectType.COLUMN,
        family_id=family_id,
        signature=signature,
        provenance=provenance,
        human_validated=True,
    )
    family = ObjectFamily(
        family_id=family_id,
        object_type=ObjectType.COLUMN,
        prototype_ids=(prototype_id,),
        project_local=True,
    )
    return prototype, family


def build_teach_receipt(
    *,
    decision_id: str,
    support_id: str,
    bbox: Any,
    actor: str = "AUTHENTICATED_OPERATOR",
    timestamp: str | None = None,
) -> dict[str, Any]:
    decision_id = str(decision_id).strip()
    if not decision_id:
        raise ValueError("OAR_PROTOTYPE_DECISION_ID_REQUIRED")
    contract = binding.load_contract()
    row = binding.support_row(contract, str(support_id))
    geometry = binding.normalize_bbox(bbox)
    document = contract["document"]
    support_id = str(row["support_id"])
    family_id = str(row["family_id"])
    prototype, family = _prototype_objects(
        support_id=support_id,
        family_id=family_id,
        bbox=geometry,
        decision_id=decision_id,
        document=document,
    )
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    return {
        "receipt_type": RECEIPT_TYPE,
        "decision_id": decision_id,
        "task_id": "CEW-OAR-G4-PROTOTYPE-TEACH",
        "residual_id": row["evidence_object_id"],
        "timestamp": timestamp,
        "actor": actor,
        "pilot_id": contract["pilot_id"],
        "support_id": support_id,
        "evidence_object_id": row["evidence_object_id"],
        "family_id": family_id,
        "family_assignment_authority": "SOURCE_DERIVED_CANDIDATE_GROUPING_ONLY",
        "source_version_id": document["source_version_id"],
        "page_id": document["page_id"],
        "derived_asset_id": document["derived_asset_id"],
        "page_transform_id": document["page_transform_id"],
        "coordinate_system": document["coordinate_system"],
        "bbox": geometry,
        "prototype": {
            "prototype_id": prototype.prototype_id,
            "object_type": prototype.object_type.value,
            "family_id": prototype.family_id,
            "signature_fingerprint": prototype.signature.fingerprint(),
            "evidence_fingerprint": prototype.provenance.evidence_fingerprint,
            "human_validated_training_example": prototype.human_validated,
            "evidence_region_complete": prototype.provenance.complete(),
        },
        "object_family": {
            "family_id": family.family_id,
            "object_type": family.object_type.value,
            "prototype_ids": list(family.prototype_ids),
            "project_local": family.project_local,
        },
        "prototype_authority": "HUMAN_TRAINING_EXAMPLE_ONLY",
        "oar_human_confirmation": False,
        "oar_classification_confirmed": False,
        "f2_registry_written": False,
        "canonical_write_authorized": False,
        "structural_identity_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def persist_teach_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("receipt_type") != RECEIPT_TYPE:
        raise ValueError("OAR_PROTOTYPE_RECEIPT_TYPE_INVALID")
    stored = audit_store.persist_runtime_receipt(receipt, RUNTIME_STORE)
    return {
        **stored,
        "prototype_id": receipt["prototype"]["prototype_id"],
        "support_id": receipt["support_id"],
        "family_id": receipt["family_id"],
        "bbox": receipt["bbox"],
        "prototype_authority": receipt["prototype_authority"],
        "oar_classification_confirmed": False,
        "canonical_write_authorized": False,
        "structural_identity_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def load_teach_receipts() -> dict[str, Any]:
    return audit_store.load_runtime_receipts(RECEIPT_TYPE, RUNTIME_STORE)


def _receipt_for_prototype(prototype_id: str) -> dict[str, Any]:
    prototype_id = str(prototype_id).strip()
    if not prototype_id:
        raise ValueError("OAR_PROTOTYPE_ID_REQUIRED")
    receipts = load_teach_receipts()["receipts"]
    matches = [r for r in receipts if r.get("prototype", {}).get("prototype_id") == prototype_id]
    if len(matches) != 1:
        raise ValueError("OAR_PROTOTYPE_NOT_FOUND_OR_AMBIGUOUS")
    return matches[0]


def _candidate_similarity(prototype_bbox: dict[str, float], row: dict[str, Any]) -> dict[str, float]:
    candidate_bbox = binding.normalize_bbox(row["bbox"])
    pw, ph = prototype_bbox["w"], prototype_bbox["h"]
    cw, ch = candidate_bbox["w"], candidate_bbox["h"]
    if min(pw, ph, cw, ch) <= 0:
        return {"score": 0.0, "size": 0.0, "ratio": 0.0, "rectangularity": 0.0, "envelope": 0.0}
    size_error = 0.5 * (abs(math.log(cw / pw)) + abs(math.log(ch / ph)))
    ratio_error = abs(math.log((cw / ch) / (pw / ph)))
    size_score = math.exp(-size_error)
    ratio_score = math.exp(-ratio_error)
    rectangularity = max(0.0, min(1.0, float(row.get("rectangularity", 0.0))))
    envelope_score = 1.0 if row.get("detector") == "LONG_AXIS_SUPPRESSED" else 0.55
    score = 0.50 * size_score + 0.25 * ratio_score + 0.15 * rectangularity + 0.10 * envelope_score
    return {
        "score": score,
        "size": size_score,
        "ratio": ratio_score,
        "rectangularity": rectangularity,
        "envelope": envelope_score,
    }


def search_similar(prototype_id: str, *, limit: int = 32) -> dict[str, Any]:
    limit = max(1, min(MAX_RESULTS, int(limit)))
    receipt = _receipt_for_prototype(prototype_id)
    prototype_bbox = binding.normalize_bbox(receipt["bbox"])
    snap = _load_snap_payload()
    ranked: list[dict[str, Any]] = []
    excluded_prototype_region = 0
    for row in snap["candidates"]:
        bbox = binding.normalize_bbox(row["bbox"])
        if _iou(prototype_bbox, bbox) >= 0.65:
            excluded_prototype_region += 1
            continue
        sim = _candidate_similarity(prototype_bbox, row)
        # Same-sheet symbols should be close in both footprint scale and ratio.
        # Small internal cells therefore fail here even if they are locally near
        # the user's original tap.
        if sim["size"] < 0.45 or sim["ratio"] < 0.50:
            continue
        ranked.append({
            "occurrence_candidate_id": row["candidate_id"],
            "bbox": bbox,
            "score": round(sim["score"], 6),
            "size_similarity": round(sim["size"], 6),
            "ratio_similarity": round(sim["ratio"], 6),
            "rectangularity": round(sim["rectangularity"], 6),
            "envelope_preference": round(sim["envelope"], 6),
            "detector": row.get("detector"),
            "best_family_prior": row.get("best_family_prior"),
            "support_identity": None,
            "review_state": "SIMILARITY_PROPOSAL",
        })
    ranked.sort(key=lambda item: (-item["score"], -item["size_similarity"], item["occurrence_candidate_id"]))

    # Collapse multiple region proposals for the same physical occurrence. This
    # is candidate-level NMS only and does not establish object identity.
    kept: list[dict[str, Any]] = []
    for candidate in ranked:
        if any(_iou(candidate["bbox"], existing["bbox"]) > 0.45 for existing in kept):
            continue
        kept.append(candidate)
        if len(kept) >= limit:
            break

    contract = binding.load_contract()
    expected_family_count = sum(1 for row in contract["objects"] if row["family_id"] == receipt["family_id"])
    return {
        "state": "SIMILAR_OBJECT_PROPOSALS_READY" if kept else "NO_SIMILAR_OBJECT_PROPOSALS",
        "prototype_id": prototype_id,
        "prototype_support_id": receipt["support_id"],
        "family_id": receipt["family_id"],
        "family_assignment_authority": "SOURCE_DERIVED_CANDIDATE_GROUPING_ONLY",
        "prototype_bbox": prototype_bbox,
        "expected_family_occurrence_count_prior": expected_family_count,
        "excluded_prototype_region_count": excluded_prototype_region,
        "candidate_count": len(kept),
        "candidates": kept,
        "search_method": "PROJECT_LOCAL_HUMAN_PROTOTYPE_GEOMETRIC_SIMILARITY_V1",
        "search_uses_tap_distance": False,
        "search_auto_assigns_support_identity": False,
        "search_auto_confirms_family": False,
        "human_group_review_required": True,
        "oar_human_confirmation": False,
        "oar_classification_confirmed": False,
        "f2_registry_written": False,
        "canonical_write_authorized": False,
        "structural_identity_authorized": False,
        "engineering_authority_effect": "NONE",
    }
