#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_professional_workbench_geometry"
MANIFEST = ASSET_ROOT / "manifest.json"
REQUIRED_SOURCES = ("TAV-05A", "TAV-06A", "TAV-05S", "TAV-06S")


def runtime_revision() -> str:
    env = os.getenv("RENDER_GIT_COMMIT") or os.getenv("VERCEL_GIT_COMMIT_SHA") or os.getenv("GITHUB_SHA")
    if env:
        return env.strip()
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNRESOLVED"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _artifact_digest(payload: dict[str, Any]) -> str:
    body = dict(payload)
    body.pop("artifact_content_sha256", None)
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST.is_file():
        raise ValueError("DOCUMENT_GEOMETRY_MANIFEST_MISSING")
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("DOCUMENT_GEOMETRY_MANIFEST_INVALID") from exc
    return manifest


def validate_manifest() -> dict[str, Any]:
    manifest = _load_manifest()
    if manifest.get("artifact_contract") != "CEW_WORKBENCH_DOCUMENT_GEOMETRY_v1":
        raise ValueError("DOCUMENT_GEOMETRY_CONTRACT_MISMATCH")
    if manifest.get("build_state") != "READY":
        raise ValueError("DOCUMENT_GEOMETRY_BUILD_NOT_READY")
    if manifest.get("build_revision") != runtime_revision():
        raise ValueError("DOCUMENT_GEOMETRY_RUNTIME_REVISION_MISMATCH")
    if manifest.get("canonical_write_authorized") is not False:
        raise ValueError("DOCUMENT_GEOMETRY_CANONICAL_WRITE_DRIFT")
    if manifest.get("engineering_authority_effect") != "NONE":
        raise ValueError("DOCUMENT_GEOMETRY_AUTHORITY_DRIFT")
    if manifest.get("runtime_docling_required") is not False:
        raise ValueError("DOCUMENT_GEOMETRY_RUNTIME_DOCLING_FORBIDDEN")

    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("DOCUMENT_GEOMETRY_ENTRIES_REQUIRED")
    if {entry.get("source_code") for entry in entries} != set(REQUIRED_SOURCES):
        raise ValueError("DOCUMENT_GEOMETRY_SOURCE_COVERAGE_MISMATCH")

    seen_versions: set[str] = set()
    for entry in entries:
        source_version_id = str(entry.get("source_version_id", ""))
        if not source_version_id or source_version_id in seen_versions:
            raise ValueError("DOCUMENT_GEOMETRY_SOURCE_VERSION_NOT_UNIQUE")
        seen_versions.add(source_version_id)
        filename = str(entry.get("filename", ""))
        if not filename or Path(filename).name != filename:
            raise ValueError("DOCUMENT_GEOMETRY_FILENAME_REJECTED")
        path = ASSET_ROOT / filename
        if not path.is_file():
            raise ValueError("DOCUMENT_GEOMETRY_REQUIRED_ARTIFACT_MISSING")
        if _sha256(path) != entry.get("file_sha256"):
            raise ValueError("DOCUMENT_GEOMETRY_FILE_DIGEST_MISMATCH")
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError("DOCUMENT_GEOMETRY_ARTIFACT_INVALID") from exc
        if artifact.get("source_version_id") != source_version_id:
            raise ValueError("DOCUMENT_GEOMETRY_SOURCE_VERSION_DRIFT")
        if artifact.get("source_sha256") != entry.get("source_sha256"):
            raise ValueError("DOCUMENT_GEOMETRY_SOURCE_DIGEST_DRIFT")
        if artifact.get("agreement_outcome") != entry.get("agreement_outcome"):
            raise ValueError("DOCUMENT_GEOMETRY_OUTCOME_DRIFT")
        if artifact.get("scene_materialization_authorized") != entry.get("scene_materialization_authorized"):
            raise ValueError("DOCUMENT_GEOMETRY_MATERIALIZATION_DRIFT")
        if artifact.get("artifact_content_sha256") != entry.get("artifact_content_sha256"):
            raise ValueError("DOCUMENT_GEOMETRY_CONTENT_DIGEST_REFERENCE_DRIFT")
        if _artifact_digest(artifact) != artifact.get("artifact_content_sha256"):
            raise ValueError("DOCUMENT_GEOMETRY_CONTENT_DIGEST_MISMATCH")
        if artifact.get("canonical_write_authorized") is not False:
            raise ValueError("DOCUMENT_GEOMETRY_ARTIFACT_CANONICAL_WRITE_DRIFT")
        if artifact.get("engineering_authority_effect") != "NONE":
            raise ValueError("DOCUMENT_GEOMETRY_ARTIFACT_AUTHORITY_DRIFT")
        objects = artifact.get("objects")
        if not isinstance(objects, list):
            raise ValueError("DOCUMENT_GEOMETRY_OBJECT_LIST_REQUIRED")
        if artifact.get("agreement_outcome") != "AGREE" and objects:
            raise ValueError("DOCUMENT_GEOMETRY_NON_AGREED_OBJECT_PUBLICATION_FORBIDDEN")
        if bool(objects) != bool(entry.get("object_count")):
            raise ValueError("DOCUMENT_GEOMETRY_OBJECT_COUNT_DRIFT")
        for obj in objects:
            if obj.get("object_family") != "DocumentGraphicPrimitive":
                raise ValueError("DOCUMENT_GEOMETRY_OBJECT_FAMILY_INVALID")
            if obj.get("coordinate_space") != "SOURCE_PAGE_PT":
                raise ValueError("DOCUMENT_GEOMETRY_COORDINATE_SPACE_INVALID")
            if obj.get("technical_identity_authorized") is not False:
                raise ValueError("DOCUMENT_GEOMETRY_TECHNICAL_IDENTITY_FORBIDDEN")
            if obj.get("canonical_write_authorized") is not False:
                raise ValueError("DOCUMENT_GEOMETRY_OBJECT_CANONICAL_WRITE_FORBIDDEN")
            provenance = obj.get("provenance") or {}
            if provenance.get("source_version_id") != source_version_id:
                raise ValueError("DOCUMENT_GEOMETRY_OBJECT_PROVENANCE_DRIFT")
    return manifest


def status() -> dict[str, Any]:
    try:
        manifest = validate_manifest()
    except ValueError as exc:
        return {
            "state": "UNAVAILABLE",
            "reason": str(exc),
            "runtime_revision": runtime_revision(),
            "runtime_docling_required": False,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    return {
        "state": "READY",
        "build_revision": manifest["build_revision"],
        "source_coverage": manifest.get("source_coverage"),
        "extractor_pins": manifest.get("extractor_pins", {}),
        "runtime_docling_required": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def scene_objects(*, source_version_id: str, source_sha256: str, page: int) -> dict[str, Any]:
    manifest = validate_manifest()
    matches = [
        entry
        for entry in manifest["entries"]
        if entry.get("source_version_id") == source_version_id and int(entry.get("page", 0)) == int(page)
    ]
    if len(matches) != 1:
        raise ValueError("DOCUMENT_GEOMETRY_SOURCE_PAGE_NOT_UNIQUE")
    entry = matches[0]
    if entry.get("source_sha256") != source_sha256:
        raise ValueError("DOCUMENT_GEOMETRY_REQUEST_SOURCE_DIGEST_MISMATCH")
    path = ASSET_ROOT / entry["filename"]
    artifact = json.loads(path.read_text(encoding="utf-8"))

    if artifact.get("agreement_outcome") != "AGREE" or artifact.get("scene_materialization_authorized") is not True:
        return {
            "state": "NOT_MATERIALIZED_FAIL_CLOSED",
            "agreement_outcome": artifact.get("agreement_outcome"),
            "objects": [],
            "reason": "ONLY_AGREE_ARTIFACTS_MAY_ENTER_THE_WORKBENCH_SCENE",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }

    return {
        "state": "READY_AGREED_DOCUMENT_GEOMETRY",
        "agreement_outcome": "AGREE",
        "coordinate_mapping": artifact.get("coordinate_mapping"),
        "object_count": len(artifact["objects"]),
        "objects": artifact["objects"],
        "artifact_content_sha256": artifact["artifact_content_sha256"],
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
