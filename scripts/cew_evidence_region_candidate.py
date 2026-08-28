#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "data/canonical/CEW_PAGE_REGISTRY_v1.csv"
MODEL = ROOT / "automation/CEW_EVIDENCE_REGION_CANDIDATE_MODEL_v1.json"


def rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def model() -> dict:
    return json.loads(MODEL.read_text(encoding="utf-8"))


def page_map() -> dict[str, dict]:
    return {r["page_id"]: r for r in rows(PAGES)}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_candidate(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("OBJECT_REQUIRED")
    m = model()
    for key in m["required_fields"]:
        if payload.get(key) in (None, ""):
            raise ValueError(f"MISSING_{key.upper()}")

    page_id = str(payload["page_id"]).strip()
    page = page_map().get(page_id)
    if not page:
        raise ValueError("PAGE_NOT_REGISTERED")
    if page.get("readiness_state") != "READY":
        raise ValueError("PAGE_NOT_READY")

    source_version_id = str(payload["source_version_id"]).strip()
    if source_version_id != page.get("source_version_id"):
        raise ValueError("SOURCEVERSION_PAGE_MISMATCH")

    if payload.get("geometry_type") != "BBOX":
        raise ValueError("UNSUPPORTED_GEOMETRY_TYPE")
    if payload.get("coordinate_space") != "NORMALIZED_0_1":
        raise ValueError("UNSUPPORTED_COORDINATE_SPACE")
    if payload.get("author_type") not in set(m["author_types"]):
        raise ValueError("UNSUPPORTED_AUTHOR_TYPE")

    try:
        x = float(payload["x"]); y = float(payload["y"]); w = float(payload["width"]); h = float(payload["height"])
    except (TypeError, ValueError):
        raise ValueError("BBOX_NOT_NUMERIC")
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1.000001 or y + h > 1.000001:
        raise ValueError("BBOX_OUTSIDE_NORMALIZED_PAGE")
    if w * h < float(m["geometry_policy"]["minimum_normalized_area"]):
        raise ValueError("BBOX_AREA_TOO_SMALL")

    purpose = str(payload.get("purpose") or "").strip()
    if not purpose:
        raise ValueError("PURPOSE_REQUIRED")
    human_note = str(payload.get("human_note") or "").strip() or None
    state = str(payload.get("state") or "PROPOSED").strip().upper()
    if state not in {"DRAFT", "PROPOSED", "REVIEW_REQUIRED"}:
        raise ValueError("INITIAL_STATE_NOT_ALLOWED")

    identity = {
        "source_version_id": source_version_id,
        "page_id": page_id,
        "bbox": [round(v, 9) for v in (x, y, w, h)],
        "author_type": payload["author_type"],
        "purpose": purpose,
        "originating_document_feature_candidate_id": payload.get("originating_document_feature_candidate_id"),
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()[:20].upper()

    return {
        "candidate_id": f"CEW-ER-CAND-{digest}",
        "source_version_id": source_version_id,
        "page_id": page_id,
        "geometry_type": "BBOX",
        "coordinate_space": "NORMALIZED_0_1",
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "author_type": payload["author_type"],
        "purpose": purpose,
        "human_note": human_note,
        "originating_document_feature_candidate_id": payload.get("originating_document_feature_candidate_id"),
        "originating_task_id": payload.get("originating_task_id"),
        "target_entity_hint": payload.get("target_entity_hint"),
        "state": state,
        "created_at": str(payload.get("created_at") or now_iso()),
        "candidate_is_evidence_region": False,
        "observation_created": False,
        "structural_binding_created": False,
        "epistemic_state_changed": False,
        "f2_registry_written": False,
        "canonical_write_authorized": False,
        "next_gate": "F2_PROMOTION_REVIEW_REQUIRED",
    }
