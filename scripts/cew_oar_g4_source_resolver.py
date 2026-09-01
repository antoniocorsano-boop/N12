#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import cew_source_evidence_workspace as source_workspace

SOURCE_ID = "TAV-05S"
EXPECTED_SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
EXPECTED_GIT_BLOB_SHA = "ec32cd621877e9037cb26ebc083164140a8e3e68"
EXPECTED_REMOTE_PATH = "archive/documentazione_originaria/tavola 5.pdf"
EXPECTED_PAGE_WIDTH_PT = 1683.72
EXPECTED_PAGE_HEIGHT_PT = 3007.08
RUNTIME_DPI = 150
RUNTIME_RASTER = Path("/tmp/cew-runtime/oar-g4-region-assets/TAV05S_150dpi.png")


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


def verify_source() -> dict[str, Any]:
    payload, source = fetch_source()
    import fitz
    document = fitz.open(stream=payload, filetype="pdf")
    try:
        if document.page_count != 1:
            raise ValueError("OAR_G4_SOURCE_PAGE_COUNT_MISMATCH")
        page = document[0]
        width = float(page.rect.width)
        height = float(page.rect.height)
        if abs(width - EXPECTED_PAGE_WIDTH_PT) > 0.01 or abs(height - EXPECTED_PAGE_HEIGHT_PT) > 0.01:
            raise ValueError("OAR_G4_SOURCE_PAGE_DIMENSIONS_MISMATCH")
    finally:
        document.close()
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
        "source_resolution": "REMOTE_IMMUTABLE_ARCHIVE_SHA256_VERIFIED",
        "canonical_write_authorized": False,
    }


def ensure_runtime_raster() -> Path:
    payload, _ = fetch_source()
    verify_source()
    RUNTIME_RASTER.parent.mkdir(parents=True, exist_ok=True)
    if RUNTIME_RASTER.is_file():
        return RUNTIME_RASTER
    import fitz
    document = fitz.open(stream=payload, filetype="pdf")
    try:
        page = document[0]
        pixmap = page.get_pixmap(dpi=RUNTIME_DPI, alpha=False)
        pixmap.save(RUNTIME_RASTER)
    finally:
        document.close()
    return RUNTIME_RASTER
