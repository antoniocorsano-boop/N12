#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "data/canonical/CEW_PAGE_REGISTRY_v1.csv"
MODEL = ROOT / "automation/CEW_DOCUMENT_MAP_MODEL_v1.json"
CANDIDATES = ROOT / "automation/CEW_DOCUMENT_FEATURE_CANDIDATES_v1.json"

MACHINE_STATES = {"DETECTED", "CANDIDATE", "SUPPORTED"}
DETECTOR_FAMILIES = {
    "PDF_TEXT",
    "OCR_TEXT",
    "PDF_VECTOR",
    "RASTER_GEOMETRY",
    "INDEPENDENT_CONSENSUS",
    "SCAN2DXF",
    "MULTIMODAL_AI",
}


def rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def model() -> dict:
    return json.loads(MODEL.read_text(encoding="utf-8"))


def page_map() -> dict[str, dict]:
    return {r["page_id"]: r for r in rows(PAGES)}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bbox(raw) -> list[float] | None:
    if raw in (None, ""):
        return None
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        raise ValueError("BBOX_REQUIRES_X_Y_WIDTH_HEIGHT")
    try:
        x, y, w, h = [float(v) for v in raw]
    except (TypeError, ValueError):
        raise ValueError("BBOX_NOT_NUMERIC")
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1.000001 or y + h > 1.000001:
        raise ValueError("BBOX_OUTSIDE_NORMALIZED_PAGE")
    return [x, y, w, h]


def normalize(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("OBJECT_REQUIRED")

    family = str(raw.get("detector_family") or "").strip().upper()
    if family not in DETECTOR_FAMILIES:
        raise ValueError("UNSUPPORTED_DETECTOR_FAMILY")

    detector = str(raw.get("detector") or "").strip()
    version = str(raw.get("detector_version") or "").strip()
    if not detector or not version:
        raise ValueError("DETECTOR_IDENTITY_REQUIRED")

    page_id = str(raw.get("page_id") or "").strip()
    page = page_map().get(page_id)
    if not page:
        raise ValueError("PAGE_NOT_REGISTERED")
    if page.get("readiness_state") != "READY":
        raise ValueError("PAGE_NOT_READY")

    source_version_id = str(raw.get("source_version_id") or "").strip()
    if source_version_id != page.get("source_version_id"):
        raise ValueError("SOURCEVERSION_PAGE_MISMATCH")

    feature_type = str(raw.get("feature_type") or "").strip().upper()
    if feature_type not in set(model().get("feature_types", [])):
        raise ValueError("UNKNOWN_FEATURE_TYPE")

    state = str(raw.get("state") or "CANDIDATE").strip().upper()
    if state not in MACHINE_STATES:
        raise ValueError("MACHINE_STATE_NOT_ALLOWED")

    confidence = raw.get("confidence")
    if confidence is not None:
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            raise ValueError("CONFIDENCE_NOT_NUMERIC")
        if confidence < 0 or confidence > 1:
            raise ValueError("CONFIDENCE_OUT_OF_RANGE")

    bbox = _bbox(raw.get("bbox_normalized_0_1"))
    projection_note = str(raw.get("projection_note") or "").strip()
    if raw.get("detector_coordinate_space") not in (None, "", "NORMALIZED_0_1") and not projection_note:
        raise ValueError("COORDINATE_PROJECTION_NOTE_REQUIRED")

    value_text = raw.get("value_text")
    source_basis = str(raw.get("source_basis") or "").strip()
    if not source_basis:
        raise ValueError("SOURCE_BASIS_REQUIRED")

    identity_payload = {
        "source_version_id": source_version_id,
        "page_id": page_id,
        "feature_type": feature_type,
        "detector_family": family,
        "detector": detector,
        "detector_version": version,
        "bbox": bbox,
        "value_text": value_text,
        "source_basis": source_basis,
    }
    digest = hashlib.sha256(json.dumps(identity_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()[:20]

    return {
        "candidate_id": f"CEW-DOC-CAND-{digest.upper()}",
        "source_version_id": source_version_id,
        "page_id": page_id,
        "feature_type": feature_type,
        "state": state,
        "detector_or_author": f"{family}:{detector}",
        "detector_version": version,
        "created_at": str(raw.get("created_at") or now_iso()),
        "bbox_normalized_0_1": bbox,
        "value_text": value_text,
        "confidence": confidence,
        "source_basis": source_basis,
        "projection_note": projection_note or None,
        "machine_candidate": True,
        "human_review_required_for_validation": True,
        "evidence_region_created": False,
        "structural_binding_created": False,
        "canonical_engineering_promotion": False,
    }


def existing_candidate_count() -> int:
    payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    return len(payload.get("candidates", []))
