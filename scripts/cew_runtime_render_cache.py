#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import cew_drawing_viewer as drawing_viewer
import cew_source_evidence_workspace as source_workspace

ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT / ".cew_runtime_render_cache"
MANIFEST_PATH = CACHE_ROOT / "manifest.json"
MANIFEST_SCHEMA_VERSION = "1.0"


def _runtime_revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or "UNRESOLVED_RUNTIME_REVISION"
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_manifest() -> dict:
    if not MANIFEST_PATH.is_file():
        raise RuntimeError("RUNTIME_RENDER_CACHE_MANIFEST_MISSING")
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError("RUNTIME_RENDER_CACHE_MANIFEST_INVALID") from exc
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise RuntimeError("RUNTIME_RENDER_CACHE_SCHEMA_MISMATCH")
    revision = _runtime_revision()
    build_revision = str(manifest.get("build_revision") or "")
    if revision != "UNRESOLVED_RUNTIME_REVISION" and build_revision != revision:
        raise RuntimeError("RUNTIME_RENDER_CACHE_REVISION_MISMATCH")
    return manifest


def _entry(key: str) -> dict:
    manifest = _load_manifest()
    entries = manifest.get("entries") or {}
    entry = entries.get(key)
    if not isinstance(entry, dict):
        raise RuntimeError("RUNTIME_RENDER_CACHE_ENTRY_MISSING")
    if entry.get("authority") != "READING_AID_ONLY" or entry.get("canonical_write_authorized") is not False:
        raise RuntimeError("RUNTIME_RENDER_CACHE_AUTHORITY_INVALID")
    return entry


def _payload(entry: dict) -> bytes:
    relative = str(entry.get("file") or "")
    target = (CACHE_ROOT / relative).resolve()
    root = CACHE_ROOT.resolve()
    if target == root or root not in target.parents:
        raise RuntimeError("RUNTIME_RENDER_CACHE_PATH_INVALID")
    if not target.is_file():
        raise RuntimeError("RUNTIME_RENDER_CACHE_FILE_MISSING")
    payload = target.read_bytes()
    if _sha256_bytes(payload) != entry.get("file_sha256"):
        raise RuntimeError("RUNTIME_RENDER_CACHE_FILE_SHA256_MISMATCH")
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("RUNTIME_RENDER_CACHE_FILE_NOT_PNG")
    return payload


def _assert_source_identity(entry: dict, ctx: dict) -> None:
    source = ctx["source"]
    binding = ctx.get("binding") or {}
    page = ctx.get("page") or {}
    region = ctx.get("region") or {}
    if entry.get("source_id") != ctx["task"]["source_id"]:
        raise RuntimeError("RUNTIME_RENDER_CACHE_SOURCE_ID_MISMATCH")
    if entry.get("source_sha256") != source.get("sha256"):
        raise RuntimeError("RUNTIME_RENDER_CACHE_SOURCE_SHA256_MISMATCH")
    if entry.get("source_version_id") != binding.get("source_version_id"):
        raise RuntimeError("RUNTIME_RENDER_CACHE_SOURCE_VERSION_MISMATCH")
    if entry.get("page_id") != page.get("page_id"):
        raise RuntimeError("RUNTIME_RENDER_CACHE_PAGE_MISMATCH")
    if entry.get("evidence_region_id") != region.get("evidence_region_id"):
        raise RuntimeError("RUNTIME_RENDER_CACHE_REGION_MISMATCH")


def render_task_source_cached(task_id: str, scale: str) -> tuple[bytes, dict]:
    normalized_scale = scale.upper()
    if normalized_scale not in {"MICRO", "MESO", "MACRO"}:
        raise ValueError("UNKNOWN_SOURCE_SCALE")
    ctx = source_workspace.task_context(task_id)
    entry = _entry(f"EVIDENCE_SOURCE:{task_id}:{normalized_scale}")
    _assert_source_identity(entry, ctx)
    payload = _payload(entry)
    return payload, {
        **ctx,
        "verified_sha256": entry["source_sha256"],
        "scale": normalized_scale,
        "requested_dpi": entry["requested_dpi"],
        "effective_dpi": entry["effective_dpi"],
        "render_pixels": entry["render_pixels"],
        "render_pixel_budget": entry["render_pixel_budget"],
        "runtime_render_source": "BUILD_TIME_VERIFIED_CACHE",
    }


def render_full_page_cached(source_id: str, dpi: int = drawing_viewer.DEFAULT_DPI) -> tuple[bytes, dict]:
    if dpi not in drawing_viewer.ALLOWED_DPI:
        raise ValueError("UNSUPPORTED_DRAWING_DPI")
    ctx = drawing_viewer.drawing_context(source_id)
    if not ctx["viewer_ready"]:
        raise ValueError(ctx["viewer_reason"])
    entry = _entry(f"DRAWING_FULL_PAGE:{source_id}:{dpi}")
    source = ctx["source"]
    page = ctx["page"]
    if entry.get("source_id") != source_id:
        raise RuntimeError("RUNTIME_RENDER_CACHE_SOURCE_ID_MISMATCH")
    if entry.get("source_sha256") != source.get("sha256"):
        raise RuntimeError("RUNTIME_RENDER_CACHE_SOURCE_SHA256_MISMATCH")
    if entry.get("page_id") != page.get("page_id"):
        raise RuntimeError("RUNTIME_RENDER_CACHE_PAGE_MISMATCH")
    payload = _payload(entry)
    return payload, {
        **ctx,
        "dpi": entry["effective_dpi"],
        "requested_dpi": entry["requested_dpi"],
        "effective_dpi": entry["effective_dpi"],
        "render_pixels": entry["render_pixels"],
        "render_pixel_budget": entry["render_pixel_budget"],
        "verified_sha256": entry["source_sha256"],
        "derived_authority": "READING_AID_ONLY",
        "canonical_write_authorized": False,
        "runtime_render_source": "BUILD_TIME_VERIFIED_CACHE",
    }


def cache_status() -> dict:
    try:
        manifest = _load_manifest()
        entries = manifest.get("entries") or {}
        for key, entry in entries.items():
            if not isinstance(entry, dict):
                raise RuntimeError(f"invalid entry: {key}")
            _payload(entry)
        return {
            "state": "READY",
            "build_revision": manifest.get("build_revision"),
            "entry_count": len(entries),
            "authority": "READING_AID_ONLY",
            "canonical_write_authorized": False,
        }
    except Exception as exc:
        return {
            "state": "NOT_READY",
            "reason": str(exc),
            "authority": "READING_AID_ONLY",
            "canonical_write_authorized": False,
        }


def install() -> None:
    source_workspace.render_task_source = render_task_source_cached
    drawing_viewer.render_full_page = render_full_page_cached
