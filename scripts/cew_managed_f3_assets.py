#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_professional_workbench_assets"
MANIFEST = ASSET_ROOT / "managed_manifest.json"
REQUIRED_SOURCES = {"TAV-05A", "TAV-06A", "TAV-05S", "TAV-06S"}


def runtime_revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("CEW_RUNTIME_REVISION")
        or "LOCAL"
    ).strip()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_manifest() -> dict[str, Any]:
    _require(MANIFEST.is_file(), "MANAGED_F3_MANIFEST_MISSING")
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("MANAGED_F3_MANIFEST_INVALID") from exc
    _require(isinstance(manifest, dict), "MANAGED_F3_MANIFEST_INVALID")
    return manifest


def validate_manifest(*, expected_revision: str | None = None) -> dict[str, Any]:
    manifest = load_manifest()
    expected = (expected_revision or runtime_revision()).strip()
    _require(manifest.get("schema_version") == "1.0", "MANAGED_F3_MANIFEST_SCHEMA_UNSUPPORTED")
    _require(manifest.get("asset_contract") == "CEW_MANAGED_F3_ASSETS_v1", "MANAGED_F3_CONTRACT_MISMATCH")
    _require(manifest.get("build_state") == "READY", "MANAGED_F3_NOT_READY")
    _require(manifest.get("authority") == "READING_AID_ONLY", "MANAGED_F3_AUTHORITY_DRIFT")
    _require(manifest.get("canonical_write_authorized") is False, "MANAGED_F3_CANONICAL_WRITE_FORBIDDEN")
    _require(manifest.get("managed_runtime_dynamic_pdf_rasterization") is False, "MANAGED_F3_DYNAMIC_RASTERIZATION_FORBIDDEN")
    _require(manifest.get("build_revision") == expected, "MANAGED_F3_RUNTIME_REVISION_MISMATCH")

    sources = manifest.get("sources")
    _require(isinstance(sources, list), "MANAGED_F3_SOURCE_LIST_MISSING")
    codes = {source.get("source_code") for source in sources if isinstance(source, dict)}
    _require(codes == REQUIRED_SOURCES, "MANAGED_F3_SOURCE_COVERAGE_MISMATCH")

    viewer = ASSET_ROOT / "source-viewer"
    required = [
        viewer / "index.html",
        viewer / "app.js",
        viewer / "styles.css",
        viewer / "viewer_manifest.json",
        viewer / "vendor/openseadragon/openseadragon.min.js",
    ]
    for code in sorted(REQUIRED_SOURCES):
        required.extend(
            [
                viewer / "tiles" / f"{code}.dzi",
                viewer / "tiles" / f"{code}_files",
            ]
        )
    for path in required:
        _require(path.exists(), f"MANAGED_F3_REQUIRED_ASSET_MISSING:{path.relative_to(ASSET_ROOT).as_posix()}")

    _require(isinstance(manifest.get("file_count"), int) and manifest["file_count"] > 0, "MANAGED_F3_FILE_COUNT_INVALID")
    _require(isinstance(manifest.get("total_bytes"), int) and manifest["total_bytes"] > 0, "MANAGED_F3_TOTAL_BYTES_INVALID")
    tree_hash = manifest.get("asset_tree_sha256", "")
    _require(isinstance(tree_hash, str) and len(tree_hash) == 64, "MANAGED_F3_TREE_HASH_INVALID")
    return manifest


def status(*, expected_revision: str | None = None) -> dict[str, Any]:
    try:
        manifest = validate_manifest(expected_revision=expected_revision)
    except ValueError as exc:
        return {
            "state": "UNAVAILABLE",
            "reason": str(exc),
            "runtime_revision": (expected_revision or runtime_revision()).strip(),
            "canonical_write_authorized": False,
            "dynamic_pdf_rasterization": False,
        }
    return {
        "state": "READY",
        "build_revision": manifest["build_revision"],
        "source_count": len(manifest["sources"]),
        "asset_tree_sha256": manifest["asset_tree_sha256"],
        "viewer_entrypoint": "/workbench/assets/source-viewer/index.html",
        "canonical_write_authorized": False,
        "dynamic_pdf_rasterization": False,
    }
