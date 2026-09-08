#!/usr/bin/env python3
"""Document-first discovery core for CEW.

Unknown PDFs are pre-acquired without semantic object priors. A raw local PDF is
preview-only. Human learning is enabled only when bytes come from the governed
Source Workspace and every page used for teaching has a READY Page Registry
identity. Project-local LearningReceipt records never authorize project truth,
CAD writes, structural identity or engineering effects.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import secrets
from threading import RLock
from typing import Any

import pymupdf

import cew_dinov3_provider as dinov3
import cew_new_project_preacquisition as preacquisition
import cew_visual_learning as learning

MAX_PDF_BYTES = 12 * 1024 * 1024
MAX_PAGES = 40
MAX_SESSIONS = 8
SESSION_LOCK = RLock()
SESSIONS: dict[str, dict[str, Any]] = {}

AUTHORITY = {
    "project_semantic_authority": "NONE",
    "oar_human_confirmation": False,
    "oar_classification_confirmed": False,
    "f2_registry_written": False,
    "canonical_write_authorized": False,
    "structural_identity_authorized": False,
    "engineering_authority_effect": "NONE",
    "human_project_validation_required": True,
}


def _text(value: Any, field: str) -> str:
    value = str(value or "").strip()
    if not value:
        raise ValueError(f"DOCUMENT_DISCOVERY_{field.upper()}_REQUIRED")
    return value


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha_json(value: Any) -> str:
    return sha256(_canonical(value).encode()).hexdigest()


def clear_sessions() -> None:
    with SESSION_LOCK:
        SESSIONS.clear()


def _validate_pdf(payload: bytes) -> None:
    if not payload or len(payload) > MAX_PDF_BYTES or not payload.startswith(b"%PDF"):
        raise ValueError("DOCUMENT_DISCOVERY_PDF_INVALID_OR_TOO_LARGE")
    try:
        with pymupdf.open(stream=payload, filetype="pdf") as doc:
            if doc.page_count < 1 or doc.page_count > MAX_PAGES:
                raise ValueError("DOCUMENT_DISCOVERY_PAGE_COUNT_INVALID")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("DOCUMENT_DISCOVERY_PDF_INVALID") from exc


def page_registry(source_workspace, source_id: str) -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    if not hasattr(source_workspace, "maps"):
        return rows
    for page in (source_workspace.maps().get("pages") or {}).values():
        if str(page.get("logical_source_code") or "") != source_id:
            continue
        if str(page.get("readiness_state") or "") != "READY":
            continue
        index = int(page.get("page_index", -1))
        if index < 0 or index in rows:
            raise ValueError("DOCUMENT_DISCOVERY_PAGE_REGISTRY_AMBIGUOUS")
        rows[index] = {
            "page_index": index,
            "page_id": _text(page.get("page_id"), "page_id"),
            "source_version_id": _text(page.get("source_version_id"), "source_version_id"),
            "readiness_state": "READY",
        }
    return rows


def governed_sources(source_workspace) -> list[dict[str, Any]]:
    if not hasattr(source_workspace, "maps"):
        return []
    output = []
    for source_id, source in sorted((source_workspace.maps().get("sources") or {}).items()):
        if str(source.get("status") or "") != "DOC_PRIMARY_IMMUTABLE":
            continue
        pages = page_registry(source_workspace, str(source_id))
        output.append({
            "source_id": str(source_id),
            "sha256": str(source.get("sha256") or ""),
            "ready_page_count": len(pages),
            "teaching_possible": bool(pages),
        })
    return output


def provider_states() -> dict[str, Any]:
    dino = dinov3.provider_environment_status()
    return {
        "structured_graphic": {
            "provider_id": learning.STRUCTURED_PROVIDER_ID,
            "state": "READY",
            "used_now": True,
        },
        "visual_foundation": {
            "provider_id": dinov3.PROVIDER_ID,
            "state": dino["implementation_state"],
            "missing_environment": dino.get("missing_environment", []),
            "used_now": False,
            "simulated": False,
        },
    }


def _save_session(session: dict[str, Any]) -> dict[str, Any]:
    with SESSION_LOCK:
        while len(SESSIONS) >= MAX_SESSIONS:
            oldest = min(SESSIONS, key=lambda key: SESSIONS[key]["created_at"])
            SESSIONS.pop(oldest, None)
        SESSIONS[session["session_id"]] = session
    return session


def _build_session(*, payload: bytes, project_id: str, source_id: str | None,
                   source_version_id: str, source_sha256: str,
                   registration_state: str, pages: dict[int, dict[str, Any]]) -> dict[str, Any]:
    _validate_pdf(payload)
    digest = sha256(payload).hexdigest()
    if digest != source_sha256.lower():
        raise ValueError("DOCUMENT_DISCOVERY_SOURCE_SHA256_MISMATCH")
    report = preacquisition.preacquire_pdf(
        payload,
        source_version_id=source_version_id,
        expected_sha256=digest,
        library_pack=None,
    )
    all_pages_ready = all(index in pages for index in range(int(report["page_count"])))
    teaching = registration_state == "GOVERNED_IMMUTABLE_SOURCE" and all_pages_ready
    return _save_session({
        "session_id": "DISC-" + secrets.token_hex(12),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_id": _text(project_id, "project_id"),
        "source_id": source_id,
        "source_version_id": source_version_id,
        "source_sha256": digest,
        "source_registration_state": registration_state,
        "page_registry": pages,
        "teaching_enabled": teaching,
        "teaching_blocker": None if teaching else "IMMUTABLE_SOURCE_AND_READY_PAGE_REGISTRATION_REQUIRED",
        "payload": payload,
        "report": report,
        "authority": dict(AUTHORITY),
    })


def create_preview(payload: bytes, project_id: str) -> dict[str, Any]:
    _validate_pdf(payload)
    digest = sha256(payload).hexdigest()
    return _build_session(
        payload=payload,
        project_id=project_id,
        source_id=None,
        source_version_id="PREVIEW-" + digest[:24],
        source_sha256=digest,
        registration_state="UNREGISTERED_PREVIEW",
        pages={},
    )


def create_governed(source_workspace, source_id: str, project_id: str) -> dict[str, Any]:
    source_id = _text(source_id, "source_id")
    if not hasattr(source_workspace, "fetch_verified_source"):
        raise ValueError("DOCUMENT_DISCOVERY_SOURCE_FETCH_UNAVAILABLE")
    payload, source = source_workspace.fetch_verified_source(source_id)
    digest = _text(source.get("sha256"), "source_sha256").lower()
    if sha256(payload).hexdigest() != digest:
        raise ValueError("DOCUMENT_DISCOVERY_SOURCE_SHA256_MISMATCH")
    pages = page_registry(source_workspace, source_id)
    versions = sorted({row["source_version_id"] for row in pages.values()})
    if len(versions) != 1:
        raise ValueError("DOCUMENT_DISCOVERY_SOURCE_VERSION_REGISTRY_REQUIRED")
    return _build_session(
        payload=payload,
        project_id=project_id,
        source_id=source_id,
        source_version_id=versions[0],
        source_sha256=digest,
        registration_state="GOVERNED_IMMUTABLE_SOURCE",
        pages=pages,
    )


def get_session(session_id: str) -> dict[str, Any]:
    with SESSION_LOCK:
        session = SESSIONS.get(_text(session_id, "session_id"))
    if session is None:
        raise ValueError("DOCUMENT_DISCOVERY_SESSION_NOT_FOUND")
    return session


def candidate_map(session: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["candidate_id"]): row for row in session["report"]["primitive_candidates"]}


def cluster_view(session: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = candidate_map(session)
    output = []
    for cluster in session["report"]["graphic_clusters"]:
        ids = list(cluster["member_candidate_ids"])
        representative = candidates[ids[0]] if ids else None
        output.append({
            "cluster_id": cluster["cluster_id"],
            "occurrence_count": cluster["occurrence_count"],
            "page_indices": cluster["page_indices"],
            "feature_signature": cluster["feature_signature"],
            "member_candidate_ids": ids,
            "representative": None if representative is None else {
                "candidate_id": representative["candidate_id"],
                "page_index": representative["page_index"],
                "bbox": representative["bbox"],
                "primitive_family": representative["primitive_family"],
            },
            "semantic_meaning": None,
            "human_review_required": True,
        })
    return output


def _project_receipts(project_id: str) -> list[dict[str, Any]]:
    loaded = learning.load_learning_receipts()
    return [row for row in loaded.get("receipts", []) if row.get("project_id") == project_id]


def memory(project_id: str, concept_id: str, meaning: str) -> dict[str, Any]:
    rows = [
        row for row in _project_receipts(project_id)
        if row.get("concept_id") == concept_id and row.get("meaning") == meaning
    ]
    return learning.replay_memory(
        project_id=project_id,
        concept_id=concept_id,
        meaning=meaning,
        receipts=rows,
    )


def concepts(project_id: str) -> list[dict[str, Any]]:
    keys = sorted({
        (str(row.get("concept_id") or ""), str(row.get("meaning") or ""))
        for row in _project_receipts(project_id)
        if row.get("concept_id") and row.get("meaning")
    })
    output = []
    for concept_id, meaning in keys:
        item = memory(project_id, concept_id, meaning)
        output.append({
            "concept_id": concept_id,
            "meaning": meaning,
            "example_counts": item["example_counts"],
            "memory_fingerprint": item["memory_fingerprint"],
            "search_ready": item["example_counts"]["POSITIVE"] > 0,
        })
    return output


def status(session_id: str) -> dict[str, Any]:
    session = get_session(session_id)
    report = session["report"]
    return {
        "state": "DOCUMENT_DISCOVERY_READY",
        "session_id": session_id,
        "project_id": session["project_id"],
        "source_id": session["source_id"],
        "source_version_id": session["source_version_id"],
        "source_sha256": session["source_sha256"],
        "source_registration_state": session["source_registration_state"],
        "teaching_enabled": session["teaching_enabled"],
        "teaching_blocker": session["teaching_blocker"],
        "page_count": report["page_count"],
        "pages": report["pages"],
        "primitive_candidate_count": report["primitive_candidate_count"],
        "graphic_cluster_count": report["graphic_cluster_count"],
        "clusters": cluster_view(session),
        "library_state": report["library_state"],
        "semantic_labels_assigned_automatically": False,
        "provider_states": provider_states(),
        "concepts": concepts(session["project_id"]),
        "authority": dict(AUTHORITY),
    }


def _evidence_fingerprint(session: dict[str, Any], candidate: dict[str, Any], page: dict[str, Any]) -> str:
    return "sha256:" + _sha_json({
        "source_version_id": page["source_version_id"],
        "source_sha256": session["source_sha256"],
        "page_id": page["page_id"],
        "page_index": candidate["page_index"],
        "coordinate_system": candidate["coordinate_system"],
        "bbox": candidate["bbox"],
        "candidate_id": candidate["candidate_id"],
        "feature_signature": candidate["feature_signature"],
    })


def teach(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    session = get_session(session_id)
    if not session["teaching_enabled"]:
        raise ValueError("DOCUMENT_DISCOVERY_TEACHING_REQUIRES_GOVERNED_SOURCE")
    candidate_id = _text(payload.get("candidate_id"), "candidate_id")
    candidate = candidate_map(session).get(candidate_id)
    if candidate is None:
        raise ValueError("DOCUMENT_DISCOVERY_CANDIDATE_NOT_FOUND")
    role = _text(payload.get("role"), "role").upper()
    if role not in learning.LEARNING_ROLES:
        raise ValueError("DOCUMENT_DISCOVERY_LEARNING_ROLE_INVALID")
    concept_id = _text(payload.get("concept_id"), "concept_id")
    meaning = _text(payload.get("meaning"), "meaning")
    current = memory(session["project_id"], concept_id, meaning)
    if role in {"NEGATIVE", "AMBIGUOUS"} and current["example_counts"]["POSITIVE"] < 1:
        raise ValueError("DOCUMENT_DISCOVERY_POSITIVE_PROTOTYPE_REQUIRED")
    page = session["page_registry"].get(int(candidate["page_index"]))
    if page is None or page.get("readiness_state") != "READY":
        raise ValueError("DOCUMENT_DISCOVERY_READY_PAGE_REGISTRATION_REQUIRED")
    if candidate["source_version_id"] != page["source_version_id"]:
        raise ValueError("DOCUMENT_DISCOVERY_SOURCE_VERSION_DRIFT")
    embedding = learning.structured_embedding_from_candidate(candidate)
    receipt = learning.build_learning_receipt(
        decision_id="learn-" + secrets.token_hex(16),
        project_id=session["project_id"],
        concept_id=concept_id,
        meaning=meaning,
        reviewer=_text(payload.get("reviewer"), "reviewer"),
        role=role,
        candidate_id=candidate_id,
        source_version_id=page["source_version_id"],
        page_id=page["page_id"],
        evidence_fingerprint=_evidence_fingerprint(session, candidate, page),
        embedding=embedding,
        rationale=_text(payload.get("rationale"), "rationale"),
    )
    persisted = learning.persist_learning_receipt(receipt)
    updated = memory(session["project_id"], concept_id, meaning)
    return {
        "state": "PROJECT_LOCAL_LEARNING_RECEIPT_PERSISTED",
        "decision_id": receipt["decision_id"],
        "role": role,
        "candidate_id": candidate_id,
        "concept_id": concept_id,
        "meaning": meaning,
        "example_counts": updated["example_counts"],
        "memory_fingerprint": updated["memory_fingerprint"],
        "audit_backend": persisted["audit_backend"],
        "authority": dict(AUTHORITY),
    }


def find_similar(session_id: str, concept_id: str, meaning: str, limit: int = 40) -> dict[str, Any]:
    session = get_session(session_id)
    current = memory(session["project_id"], _text(concept_id, "concept_id"), _text(meaning, "meaning"))
    if current["example_counts"]["POSITIVE"] < 1:
        raise ValueError("DOCUMENT_DISCOVERY_POSITIVE_PROTOTYPE_REQUIRED")
    ranked = learning.rank_preacquisition_candidates(
        current,
        session["report"]["primitive_candidates"],
        limit=max(1, min(100, int(limit))),
    )
    candidates = candidate_map(session)
    trained = {row["candidate_id"] for row in current["examples"]}
    rows = []
    for result in ranked["candidates"]:
        candidate = candidates[result["candidate_id"]]
        rows.append({
            **result,
            "bbox": candidate["bbox"],
            "primitive_family": candidate["primitive_family"],
            "is_training_example": result["candidate_id"] in trained,
        })
    return {
        **ranked,
        "candidates": rows,
        "candidate_count": len(rows),
        "search_channel_state": "STRUCTURED_GRAPHIC_ONLY_DINOV3_NOT_PROVISIONED",
        "visual_foundation_used": False,
        "automatic_classification": False,
        "authority": dict(AUTHORITY),
    }


def render_page(session_id: str, page_index: int, max_pixels: int = 4_500_000) -> bytes:
    session = get_session(session_id)
    with pymupdf.open(stream=session["payload"], filetype="pdf") as doc:
        if page_index < 0 or page_index >= doc.page_count:
            raise ValueError("DOCUMENT_DISCOVERY_PAGE_INDEX_INVALID")
        page = doc.load_page(page_index)
        scale = min(2.0, max(0.5, (max_pixels / max(1.0, page.rect.width * page.rect.height)) ** 0.5))
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        return pix.tobytes("jpeg", jpg_quality=86)
