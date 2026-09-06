#!/usr/bin/env python3
"""Runtime hardening: serve only pre-materialized verified review-page assets.

This removes live Internet access from the external-reference human review path.
The original PDF remains the evidentiary authority; committed JPEGs are reading
 aids only and are accepted only when their manifest provenance matches the
current governed acquisition receipt and review queue exactly.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "knowledge" / "graphic_reference" / "derived_review_assets"
MANIFEST_PATH = ASSET_ROOT / "manifest.json"
SCHEMA = "CEW_EXTERNAL_REFERENCE_REVIEW_ASSET_MANIFEST_v1"


def _manifest(review) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:  # noqa: ANN001
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA:
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_MANIFEST_SCHEMA_INVALID")
    if manifest.get("asset_count") != 5 or len(manifest.get("assets") or []) != 5:
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_COUNT_INVALID")
    if manifest.get("runtime_external_fetch_required") is not False:
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_NETWORK_DRIFT")
    authority = manifest.get("authority", {})
    if authority.get("reading_aid_only") is not True:
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_AUTHORITY_INVALID")
    if authority.get("project_semantic_authority") != "NONE":
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_SEMANTIC_AUTHORITY_DRIFT")

    acquisition, queue = review._governed()
    receipt_fp = str(acquisition.get("artifact", {}).get("receipt_fingerprint") or "")
    if manifest.get("acquisition_receipt_fingerprint") != receipt_fp:
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_RECEIPT_FINGERPRINT_MISMATCH")
    if queue.get("acquisition_receipt_fingerprint") != receipt_fp:
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_QUEUE_FINGERPRINT_MISMATCH")

    rows: dict[str, dict[str, Any]] = {}
    for row in manifest["assets"]:
        item_id = str(row.get("review_item_id") or "")
        if not item_id or item_id in rows:
            raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_ID_INVALID_OR_DUPLICATE")
        if row.get("authority", {}).get("reading_aid_only") is not True:
            raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_ROW_AUTHORITY_INVALID")
        if row.get("authority", {}).get("project_semantic_authority") != "NONE":
            raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_ROW_SEMANTIC_AUTHORITY_DRIFT")
        rows[item_id] = row
    return manifest, rows


def _safe_asset_path(relative: str) -> Path:
    target = (ROOT / relative).resolve()
    try:
        target.relative_to(ASSET_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_PATH_ESCAPE") from exc
    if target.suffix.lower() != ".b64" or not target.is_file():
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_FILE_MISSING")
    return target


def _render_local(review, review_item_id: str, *, scale: float = 1.5) -> bytes:  # noqa: ANN001
    # scale is intentionally ignored: the governed reading aid has a fixed
    # materialized render scale recorded in its manifest.
    _ = float(scale)
    _acquisition, queue = review._governed()
    item = review._queue_index(queue).get(str(review_item_id))
    if item is None:
        raise ValueError("REFERENCE_REVIEW_ITEM_UNKNOWN")
    _manifest_doc, rows = _manifest(review)
    row = rows.get(str(review_item_id))
    if row is None:
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_NOT_MATERIALIZED")

    for field in (
        "source_id",
        "source_sha256",
        "page_index",
        "page_number_1_based",
        "page_text_sha256",
        "page_feature_sha256",
    ):
        expected = item[field]
        actual = row.get(field)
        if field in {"page_index", "page_number_1_based"}:
            expected = int(expected)
            actual = int(actual)
        if actual != expected:
            raise ValueError(f"REFERENCE_REVIEW_LOCAL_ASSET_{field.upper()}_MISMATCH")

    if row.get("encoding") != "BASE64_TEXT" or row.get("media_type") != "image/jpeg":
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_ENCODING_INVALID")
    path = _safe_asset_path(str(row["asset_path"]))
    try:
        raw = base64.b64decode(path.read_text(encoding="ascii").strip(), validate=True)
    except Exception as exc:
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_BASE64_INVALID") from exc
    if hashlib.sha256(raw).hexdigest() != str(row["image_sha256"]):
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_IMAGE_SHA_MISMATCH")
    if len(raw) != int(row["image_byte_count"]):
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_IMAGE_SIZE_MISMATCH")
    if not raw.startswith(b"\xff\xd8"):
        raise ValueError("REFERENCE_REVIEW_LOCAL_ASSET_JPEG_INVALID")
    return raw


def install(review) -> None:  # noqa: ANN001
    def render_review_page(review_item_id: str, *, scale: float = 1.5) -> bytes:
        return _render_local(review, review_item_id, scale=scale)

    review.render_review_page = render_review_page
