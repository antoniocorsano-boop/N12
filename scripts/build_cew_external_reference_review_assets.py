#!/usr/bin/env python3
"""Materialize exact-page reading aids for the CEW external-reference review queue.

The original external PDF remains the evidentiary authority. This build step
fetches only repository-governed sources, verifies exact source SHA-256 and page
text/feature fingerprints, renders only queue-listed pages, and writes Base64
encoded JPEG reading aids plus a manifest. The derived assets carry no project
semantic, CAD, structural, or engineering authority.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pymupdf

import cew_external_graphic_reference_acquisition as acquisition_tools

ROOT = Path(__file__).resolve().parents[1]
ACQUISITION_PATH = ROOT / "knowledge" / "graphic_reference" / "CEW_EXTERNAL_REFERENCE_ACQUISITION_RECEIPT_v1.json"
QUEUE_PATH = ROOT / "knowledge" / "graphic_reference" / "CEW_EXTERNAL_REFERENCE_REVIEW_QUEUE_v1.json"
OUTPUT_ROOT = ROOT / "knowledge" / "graphic_reference" / "derived_review_assets"
MANIFEST_PATH = OUTPUT_ROOT / "manifest.json"
SCHEMA = "CEW_EXTERNAL_REFERENCE_REVIEW_ASSET_MANIFEST_v1"
RENDER_SCALE = 1.65
JPEG_QUALITY = 88

AUTHORITY = {
    "reading_aid_only": True,
    "source_document_remains_authority": True,
    "semantic_meaning_assigned": False,
    "library_entries_created": False,
    "project_semantic_authority": "NONE",
    "canonical_write_authorized": False,
    "structural_identity_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("REFERENCE_REVIEW_ASSET_GOVERNED_JSON_INVALID")
    return data


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_index(acquisition: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in acquisition.get("acquired_sources") or []:
        source_id = str(row.get("source_id") or "")
        if not source_id or source_id in rows:
            raise ValueError("REFERENCE_REVIEW_ASSET_SOURCE_ID_INVALID")
        if row.get("acquisition_status") != "ACQUIRED_EXACT_BYTES":
            raise ValueError("REFERENCE_REVIEW_ASSET_SOURCE_NOT_ACQUIRED")
        rows[source_id] = row
    return rows


def _verify_page(item: dict[str, Any], source: dict[str, Any], doc: pymupdf.Document) -> pymupdf.Page:
    page_index = int(item["page_index"])
    if page_index < 0 or page_index >= doc.page_count:
        raise ValueError("REFERENCE_REVIEW_ASSET_PAGE_INDEX_INVALID")
    page = doc.load_page(page_index)
    page_text = acquisition_tools._normalize_text(page.get_text("text"))
    text_sha = _sha(page_text.encode("utf-8"))
    feature_sha, counts = acquisition_tools._page_feature_fingerprint(page)
    if text_sha != str(item["page_text_sha256"]):
        raise ValueError("REFERENCE_REVIEW_ASSET_PAGE_TEXT_SHA_MISMATCH")
    if feature_sha != str(item["page_feature_sha256"]):
        raise ValueError("REFERENCE_REVIEW_ASSET_PAGE_FEATURE_SHA_MISMATCH")
    expected_counts = {
        "drawing_count": int(item["drawing_count"]),
        "text_block_count": int(item["text_block_count"]),
        "image_count": int(item["image_count"]),
    }
    if counts != expected_counts:
        raise ValueError("REFERENCE_REVIEW_ASSET_PAGE_COUNTS_MISMATCH")
    return page


def build() -> dict[str, Any]:
    acquisition = _load(ACQUISITION_PATH)
    queue = _load(QUEUE_PATH)
    if acquisition.get("schema") != "CEW_EXTERNAL_REFERENCE_ACQUISITION_RECEIPT_v1":
        raise ValueError("REFERENCE_REVIEW_ASSET_ACQUISITION_SCHEMA_INVALID")
    if queue.get("schema") != "CEW_EXTERNAL_REFERENCE_REVIEW_QUEUE_v1":
        raise ValueError("REFERENCE_REVIEW_ASSET_QUEUE_SCHEMA_INVALID")
    receipt_fp = str(acquisition.get("artifact", {}).get("receipt_fingerprint") or "")
    if queue.get("acquisition_receipt_fingerprint") != receipt_fp:
        raise ValueError("REFERENCE_REVIEW_ASSET_RECEIPT_FINGERPRINT_MISMATCH")

    sources = _source_index(acquisition)
    items = list(queue.get("review_items") or [])
    if len(items) != 5:
        raise ValueError("REFERENCE_REVIEW_ASSET_EXPECTED_FIVE_REVIEW_ITEMS")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for old in OUTPUT_ROOT.glob("*.jpg.b64"):
        old.unlink()

    by_source: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_source.setdefault(str(item["source_id"]), []).append(item)

    assets: list[dict[str, Any]] = []
    for source_id, source_items in sorted(by_source.items()):
        source = sources.get(source_id)
        if source is None:
            raise ValueError("REFERENCE_REVIEW_ASSET_SOURCE_NOT_FOUND")
        payload, transport = acquisition_tools._fetch_exact_bytes(str(source["source_url"]))
        if _sha(payload) != str(source["source_sha256"]):
            raise ValueError("REFERENCE_REVIEW_ASSET_SOURCE_SHA_MISMATCH")
        if not payload.startswith(b"%PDF"):
            raise ValueError("REFERENCE_REVIEW_ASSET_SOURCE_NOT_PDF")
        with pymupdf.open(stream=payload, filetype="pdf") as doc:
            if int(doc.page_count) != int(source["page_count"]):
                raise ValueError("REFERENCE_REVIEW_ASSET_PAGE_COUNT_MISMATCH")
            for item in sorted(source_items, key=lambda row: str(row["review_item_id"])):
                page = _verify_page(item, source, doc)
                pix = page.get_pixmap(matrix=pymupdf.Matrix(RENDER_SCALE, RENDER_SCALE), alpha=False)
                image = pix.tobytes("jpeg", jpg_quality=JPEG_QUALITY)
                image_sha = _sha(image)
                filename = f"{item['review_item_id']}.jpg.b64"
                encoded = base64.b64encode(image).decode("ascii")
                (OUTPUT_ROOT / filename).write_text(encoded + "\n", encoding="ascii")
                assets.append({
                    "review_item_id": item["review_item_id"],
                    "source_id": source_id,
                    "source_sha256": source["source_sha256"],
                    "page_index": int(item["page_index"]),
                    "page_number_1_based": int(item["page_number_1_based"]),
                    "page_text_sha256": item["page_text_sha256"],
                    "page_feature_sha256": item["page_feature_sha256"],
                    "render_scale": RENDER_SCALE,
                    "jpeg_quality": JPEG_QUALITY,
                    "media_type": "image/jpeg",
                    "encoding": "BASE64_TEXT",
                    "asset_path": f"knowledge/graphic_reference/derived_review_assets/{filename}",
                    "image_sha256": image_sha,
                    "image_byte_count": len(image),
                    "source_transport_final_url": transport.get("final_url"),
                    "authority": dict(AUTHORITY),
                })

    manifest = {
        "schema": SCHEMA,
        "acquisition_receipt_fingerprint": receipt_fp,
        "review_queue_ref": "knowledge/graphic_reference/CEW_EXTERNAL_REFERENCE_REVIEW_QUEUE_v1.json",
        "asset_count": len(assets),
        "renderer": {"name": "PyMuPDF", "version": pymupdf.__version__},
        "assets": assets,
        "runtime_external_fetch_required": False,
        "source_bytes_committed_to_repo": False,
        "derived_page_assets_committed_to_repo": True,
        "authority": dict(AUTHORITY),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("CEW_EXTERNAL_REFERENCE_REVIEW_ASSET_BUILD_PASS")
    print(f"asset_count={len(assets)} runtime_external_fetch_required=false")
    return manifest


def main() -> None:
    build()


if __name__ == "__main__":
    main()
