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
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("DOCUMENT_GEOMETRY_MANIFEST_INVALID") from exc


def _validate_object(obj: dict[str, Any], *, source_version_id: str, source_sha256: str, evidence_region_id: str) -> None:
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
    if provenance.get("source_sha256") != source_sha256:
        raise ValueError("DOCUMENT_GEOMETRY_OBJECT_SOURCE_DIGEST_DRIFT")
    if provenance.get("evidence_region_id") != evidence_region_id:
        raise ValueError("DOCUMENT_GEOMETRY_OBJECT_REGION_PROVENANCE_DRIFT")
    if provenance.get("artifact_role") != "CORROBORATED_CLAIM_SCOPED_DOCUMENT_GEOMETRY":
        raise ValueError("DOCUMENT_GEOMETRY_OBJECT_ARTIFACT_ROLE_DRIFT")


def validate_manifest() -> dict[str, Any]:
    manifest = _load_manifest()
    if manifest.get("schema_version") != "1.1":
        raise ValueError("DOCUMENT_GEOMETRY_MANIFEST_SCHEMA_MISMATCH")
    if manifest.get("artifact_contract") != "CEW_WORKBENCH_DOCUMENT_GEOMETRY_v1":
        raise ValueError("DOCUMENT_GEOMETRY_CONTRACT_MISMATCH")
    if manifest.get("build_state") != "READY":
        raise ValueError("DOCUMENT_GEOMETRY_BUILD_NOT_READY")
    if manifest.get("build_revision") != runtime_revision():
        raise ValueError("DOCUMENT_GEOMETRY_RUNTIME_REVISION_MISMATCH")
    if manifest.get("comparison_scope") != "GOVERNED_EVIDENCE_REGION_WHERE_AVAILABLE":
        raise ValueError("DOCUMENT_GEOMETRY_COMPARISON_SCOPE_DRIFT")
    if manifest.get("page_level_role") != "DIAGNOSTIC_ONLY":
        raise ValueError("DOCUMENT_GEOMETRY_PAGE_ROLE_DRIFT")
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
    seen_regions: set[str] = set()
    total_regions = 0
    total_agreed = 0
    total_objects = 0
    for entry in entries:
        source_version_id = str(entry.get("source_version_id", ""))
        source_sha256 = str(entry.get("source_sha256", ""))
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
        if artifact.get("schema_version") != "1.1":
            raise ValueError("DOCUMENT_GEOMETRY_ARTIFACT_SCHEMA_MISMATCH")
        if artifact.get("source_version_id") != source_version_id:
            raise ValueError("DOCUMENT_GEOMETRY_SOURCE_VERSION_DRIFT")
        if artifact.get("source_sha256") != source_sha256:
            raise ValueError("DOCUMENT_GEOMETRY_SOURCE_DIGEST_DRIFT")
        if artifact.get("artifact_content_sha256") != entry.get("artifact_content_sha256"):
            raise ValueError("DOCUMENT_GEOMETRY_CONTENT_DIGEST_REFERENCE_DRIFT")
        if _artifact_digest(artifact) != artifact.get("artifact_content_sha256"):
            raise ValueError("DOCUMENT_GEOMETRY_CONTENT_DIGEST_MISMATCH")
        if artifact.get("canonical_write_authorized") is not False:
            raise ValueError("DOCUMENT_GEOMETRY_ARTIFACT_CANONICAL_WRITE_DRIFT")
        if artifact.get("engineering_authority_effect") != "NONE":
            raise ValueError("DOCUMENT_GEOMETRY_ARTIFACT_AUTHORITY_DRIFT")
        if (artifact.get("page_diagnostic") or {}).get("role") != "DIAGNOSTIC_ONLY_NOT_A_SCENE_MATERIALIZATION_GATE":
            raise ValueError("DOCUMENT_GEOMETRY_PAGE_DIAGNOSTIC_ROLE_DRIFT")
        if (artifact.get("page_diagnostic") or {}).get("agreement_outcome") != entry.get("page_diagnostic_outcome"):
            raise ValueError("DOCUMENT_GEOMETRY_PAGE_OUTCOME_DRIFT")

        regions = artifact.get("regions")
        if not isinstance(regions, list):
            raise ValueError("DOCUMENT_GEOMETRY_REGION_LIST_REQUIRED")
        if len(regions) != int(entry.get("governed_region_count", -1)):
            raise ValueError("DOCUMENT_GEOMETRY_REGION_COUNT_DRIFT")
        agreed = 0
        object_count = 0
        for region in regions:
            region_id = str(region.get("evidence_region_id", ""))
            if not region_id or region_id in seen_regions:
                raise ValueError("DOCUMENT_GEOMETRY_REGION_ID_NOT_UNIQUE")
            seen_regions.add(region_id)
            if region.get("coordinate_space") != "NORMALIZED_0_1":
                raise ValueError("DOCUMENT_GEOMETRY_REGION_COORDINATE_SPACE_DRIFT")
            if region.get("canonical_write_authorized") is not False or region.get("engineering_authority_effect") != "NONE":
                raise ValueError("DOCUMENT_GEOMETRY_REGION_AUTHORITY_DRIFT")
            outcome = region.get("agreement_outcome")
            if outcome not in {"AGREE", "PARTIAL", "DISAGREE", "UNCOMPARABLE"}:
                raise ValueError("DOCUMENT_GEOMETRY_REGION_OUTCOME_INVALID")
            objects = region.get("objects")
            if not isinstance(objects, list):
                raise ValueError("DOCUMENT_GEOMETRY_REGION_OBJECT_LIST_REQUIRED")
            if outcome != "AGREE" and objects:
                raise ValueError("DOCUMENT_GEOMETRY_NON_AGREED_OBJECT_PUBLICATION_FORBIDDEN")
            if region.get("scene_materialization_authorized") is not (outcome == "AGREE"):
                raise ValueError("DOCUMENT_GEOMETRY_REGION_MATERIALIZATION_DRIFT")
            if region.get("unmatched_geometry_published") is not False:
                raise ValueError("DOCUMENT_GEOMETRY_UNMATCHED_PUBLICATION_FORBIDDEN")
            if outcome == "AGREE":
                agreed += 1
            object_count += len(objects)
            for obj in objects:
                _validate_object(
                    obj,
                    source_version_id=source_version_id,
                    source_sha256=source_sha256,
                    evidence_region_id=region_id,
                )
        if agreed != int(entry.get("agreed_region_count", -1)):
            raise ValueError("DOCUMENT_GEOMETRY_AGREED_REGION_COUNT_DRIFT")
        if object_count != int(entry.get("region_object_count", -1)):
            raise ValueError("DOCUMENT_GEOMETRY_OBJECT_COUNT_DRIFT")
        if artifact.get("agreed_region_count") != agreed or artifact.get("region_object_count") != object_count:
            raise ValueError("DOCUMENT_GEOMETRY_ARTIFACT_SUMMARY_DRIFT")
        total_regions += len(regions)
        total_agreed += agreed
        total_objects += object_count

    if total_regions != int(manifest.get("governed_region_count", -1)):
        raise ValueError("DOCUMENT_GEOMETRY_MANIFEST_REGION_COUNT_DRIFT")
    if total_agreed != int(manifest.get("agreed_region_count", -1)):
        raise ValueError("DOCUMENT_GEOMETRY_MANIFEST_AGREED_COUNT_DRIFT")
    if total_objects != int(manifest.get("region_object_count", -1)):
        raise ValueError("DOCUMENT_GEOMETRY_MANIFEST_OBJECT_COUNT_DRIFT")
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
        "governed_region_count": manifest.get("governed_region_count"),
        "agreed_region_count": manifest.get("agreed_region_count"),
        "region_object_count": manifest.get("region_object_count"),
        "comparison_scope": manifest.get("comparison_scope"),
        "page_level_role": manifest.get("page_level_role"),
        "extractor_pins": manifest.get("extractor_pins", {}),
        "runtime_docling_required": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def scene_objects(
    *, source_version_id: str, source_sha256: str, page: int, evidence_region_id: str
) -> dict[str, Any]:
    manifest = validate_manifest()
    matches = [
        entry
        for entry in manifest["entries"]
        if entry.get("source_version_id") == source_version_id and int(entry.get("pdf_page_no", 0)) == int(page)
    ]
    if len(matches) != 1:
        raise ValueError("DOCUMENT_GEOMETRY_SOURCE_PAGE_NOT_UNIQUE")
    entry = matches[0]
    if entry.get("source_sha256") != source_sha256:
        raise ValueError("DOCUMENT_GEOMETRY_REQUEST_SOURCE_DIGEST_MISMATCH")
    artifact = json.loads((ASSET_ROOT / entry["filename"]).read_text(encoding="utf-8"))
    regions = [region for region in artifact["regions"] if region.get("evidence_region_id") == evidence_region_id]
    if len(regions) != 1:
        return {
            "state": "NO_GOVERNED_EVIDENCE_REGION_FAIL_CLOSED",
            "agreement_outcome": None,
            "objects": [],
            "reason": "EXACT_READY_EVIDENCE_REGION_REQUIRED_FOR_SCENE_GEOMETRY",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    region = regions[0]
    if region.get("agreement_outcome") != "AGREE" or region.get("scene_materialization_authorized") is not True:
        return {
            "state": "NOT_MATERIALIZED_FAIL_CLOSED",
            "agreement_outcome": region.get("agreement_outcome"),
            "evidence_region_id": evidence_region_id,
            "objects": [],
            "reason": "ONLY_AGREE_EVIDENCE_REGIONS_MAY_ENTER_THE_WORKBENCH_SCENE",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    return {
        "state": "READY_AGREED_DOCUMENT_GEOMETRY",
        "agreement_outcome": "AGREE",
        "evidence_region_id": evidence_region_id,
        "coordinate_mapping": region.get("coordinate_mapping"),
        "effective_match_ratio": region.get("effective_match_ratio"),
        "object_count": len(region["objects"]),
        "objects": region["objects"],
        "artifact_content_sha256": artifact["artifact_content_sha256"],
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
