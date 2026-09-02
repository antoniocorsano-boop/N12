#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import cew_source_evidence_workspace as source_workspace

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "TAV-05S"
EXPECTED_SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
EXPECTED_GIT_BLOB_SHA = "ec32cd621877e9037cb26ebc083164140a8e3e68"
EXPECTED_REMOTE_PATH = "archive/documentazione_originaria/tavola 5.pdf"
EXPECTED_PAGE_WIDTH_PT = 1683.72
EXPECTED_PAGE_HEIGHT_PT = 3007.08
REGISTERED_DERIVED_ASSET_ID = "CEW-N12-ASSET-TAV05S-P001-OAR-300DPI"
REGISTERED_RENDER_SHA256 = "6344abae8d390ef799812c808427431e684a61cca6bb5792de331b2b9d2b6252"
REGISTERED_RENDER_WIDTH_PX = 7016
REGISTERED_RENDER_HEIGHT_PX = 12530
RUNTIME_DPI = 300
BUILD_RASTER = ROOT / "artifacts" / "cew_oar_g4_runtime" / "TAV05S_OAR_300dpi.jpg"
RUNTIME_RASTER = Path("/tmp/cew-runtime/oar-g4-region-assets/TAV05S_OAR_300dpi.jpg")
REQUIRE_PREBUILT_ENV = "CEW_OAR_G4_REQUIRE_PREBUILT_RASTER"
JPEG_QUALITY = 92


def fetch_source() -> tuple[bytes, dict[str, Any]]:
    payload, source = source_workspace.fetch_verified_source(SOURCE_ID)
    if source.get("status") != "DOC_PRIMARY_IMMUTABLE":
        raise ValueError("OAR_G4_SOURCE_NOT_IMMUTABLE")
    if source.get("sha256", "").strip().lower() != EXPECTED_SOURCE_SHA256:
        raise ValueError("OAR_G4_SOURCE_REGISTRY_SHA256_MISMATCH")
    if source.get("git_blob_sha", "").strip() != EXPECTED_GIT_BLOB_SHA:
        raise ValueError("OAR_G4_SOURCE_REGISTRY_BLOB_MISMATCH")
    if source.get("remote_path", "").strip() != EXPECTED_REMOTE_PATH:
        raise ValueError("OAR_G4_SOURCE_REGISTRY_PATH_MISMATCH")
    return payload, source


def _verification_from_document(document: Any, source: dict[str, Any]) -> dict[str, Any]:
    """Validate an already-fetched immutable PDF without another remote read."""
    if document.page_count != 1:
        raise ValueError("OAR_G4_SOURCE_PAGE_COUNT_MISMATCH")
    page = document[0]
    width = float(page.rect.width)
    height = float(page.rect.height)
    if abs(width - EXPECTED_PAGE_WIDTH_PT) > 0.01 or abs(height - EXPECTED_PAGE_HEIGHT_PT) > 0.01:
        raise ValueError("OAR_G4_SOURCE_PAGE_DIMENSIONS_MISMATCH")
    return {
        "state": "READY",
        "source_id": SOURCE_ID,
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "git_blob_sha": EXPECTED_GIT_BLOB_SHA,
        "archive_commit": source_workspace.ARCHIVE_COMMIT,
        "remote_path": source["remote_path"],
        "page_width_pt": EXPECTED_PAGE_WIDTH_PT,
        "page_height_pt": EXPECTED_PAGE_HEIGHT_PT,
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "derived_asset_id": REGISTERED_DERIVED_ASSET_ID,
        "render_sha256": REGISTERED_RENDER_SHA256,
        "render_width_px": REGISTERED_RENDER_WIDTH_PX,
        "render_height_px": REGISTERED_RENDER_HEIGHT_PX,
        "render_dpi": RUNTIME_DPI,
        "source_resolution": "REMOTE_IMMUTABLE_ARCHIVE_SHA256_VERIFIED",
        "display_asset_authority": "DERIVED_REVIEW_AID_ONLY",
        "canonical_write_authorized": False,
    }


def verify_source() -> dict[str, Any]:
    payload, source = fetch_source()
    import fitz

    document = fitz.open(stream=payload, filetype="pdf")
    try:
        return _verification_from_document(document, source)
    finally:
        document.close()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_registered_raster(path: Path) -> None:
    if not path.is_file():
        raise ValueError("OAR_G4_REGISTERED_RENDER_NOT_MATERIALIZED")
    digest = _file_sha256(path)
    if digest != REGISTERED_RENDER_SHA256:
        raise ValueError(f"OAR_G4_REGISTERED_RENDER_SHA256_MISMATCH:{digest}")
    import fitz

    pixmap = fitz.Pixmap(str(path))
    if pixmap.width != REGISTERED_RENDER_WIDTH_PX or pixmap.height != REGISTERED_RENDER_HEIGHT_PX:
        raise ValueError("OAR_G4_REGISTERED_RENDER_DIMENSIONS_MISMATCH")


def _materialize_registered_raster(path: Path) -> Path:
    """Create the exact governed display asset from the immutable SourceVersion."""
    if path.is_file():
        verify_registered_raster(path)
        return path

    payload, source = fetch_source()
    import fitz

    document = fitz.open(stream=payload, filetype="pdf")
    try:
        _verification_from_document(document, source)
        path.parent.mkdir(parents=True, exist_ok=True)
        page = document[0]
        pixmap = page.get_pixmap(dpi=RUNTIME_DPI, alpha=False)
        if pixmap.width != REGISTERED_RENDER_WIDTH_PX or pixmap.height != REGISTERED_RENDER_HEIGHT_PX:
            raise ValueError("OAR_G4_REGISTERED_RENDER_DIMENSIONS_MISMATCH")
        pixmap.save(path, jpg_quality=JPEG_QUALITY)
        verify_registered_raster(path)
        return path
    finally:
        document.close()


def materialize_build_raster() -> Path:
    """Build-pipeline materialization; Render's build compute is isolated from the web worker."""
    return _materialize_registered_raster(BUILD_RASTER)


def _prebuilt_required() -> bool:
    return os.getenv(REQUIRE_PREBUILT_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def ensure_runtime_raster() -> Path:
    """Serve a build-materialized raster; never cold-render on governed Render runtime."""
    if BUILD_RASTER.is_file():
        verify_registered_raster(BUILD_RASTER)
        return BUILD_RASTER

    if _prebuilt_required():
        raise ValueError("OAR_G4_PREBUILT_RENDER_REQUIRED")

    # Local/test fallback only. Production Render sets REQUIRE_PREBUILT_ENV and
    # therefore cannot allocate the full 7016x12530 pixmap on a user request.
    return _materialize_registered_raster(RUNTIME_RASTER)
