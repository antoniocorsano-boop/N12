#!/usr/bin/env python3
"""Deterministic gate for governed external graphic-reference acquisition."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pymupdf

import cew_external_graphic_reference_acquisition as acquire

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "knowledge/graphic_reference/CEW_EXTERNAL_REFERENCE_DISCOVERY_SEEDS_v1.json"


def _synthetic_reference_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 90), "CAD Standard Symbols", fontsize=14)
    page.insert_text((72, 120), "Section Mark Blocks", fontsize=11)
    page.draw_circle(pymupdf.Point(140, 200), 24, color=(0, 0, 0), width=1)
    page.draw_rect(pymupdf.Rect(220, 175, 275, 225), color=(0, 0, 0), width=1)
    payload = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return payload


def main() -> None:
    seeds = json.loads(SEEDS.read_text(encoding="utf-8"))
    assert seeds["schema"] == acquire.SEED_SCHEMA
    assert seeds["status"] == "DISCOVERED_PENDING_BINARY_ACQUISITION"
    assert len(seeds["sources"]) >= 3
    assert seeds["authority"]["library_entries_created"] is False
    assert seeds["authority"]["project_semantic_authority"] == "NONE"

    for source in seeds["sources"]:
        assert acquire._allowed_url(source["source_url"])
        assert source["discovery_authority"] == "REFERENCE_DISCOVERY_ONLY"
        assert source["evidence_queries"]
        assert source["usage_note"]

    assert acquire._allowed_url("https://www.wbdg.org/example.pdf")
    assert acquire._allowed_url("https://subdomain.nps.gov/example.pdf")
    assert not acquire._allowed_url("http://www.wbdg.org/example.pdf")
    assert not acquire._allowed_url("https://example.com/reference.pdf")

    payload = _synthetic_reference_pdf()
    expected_sha = hashlib.sha256(payload).hexdigest()
    original_fetch = acquire._fetch_exact_bytes
    acquire._fetch_exact_bytes = lambda url: (
        payload,
        {
            "requested_url": url,
            "final_url": url,
            "http_status": 200,
            "content_type": "application/pdf",
            "etag": None,
            "last_modified": None,
            "fetch_attempt": 1,
        },
    )
    try:
        test_manifest = {
            "schema": acquire.SEED_SCHEMA,
            "sources": [
                {
                    "source_id": "GREF-SRC-TEST-001",
                    "title": "Synthetic external reference",
                    "publisher": "CEW TEST",
                    "source_url": "https://www.wbdg.org/test-reference.pdf",
                    "reference_scope": ["CAD_STANDARD_SYMBOLS"],
                    "evidence_queries": ["CAD Standard Symbols", "Section Mark Blocks", "not present"],
                    "usage_note": "TEST ONLY",
                }
            ],
        }
        receipt = acquire.acquire_seed_manifest(test_manifest)
    finally:
        acquire._fetch_exact_bytes = original_fetch

    assert receipt["schema"] == acquire.RECEIPT_SCHEMA
    assert receipt["status"] == "PASS"
    assert receipt["acquired_source_count"] == 1
    assert receipt["failed_source_count"] == 0
    assert receipt["library_promotion_authorized"] is False
    assert receipt["authority"] == acquire.AUTHORITY
    assert receipt["next_gate"] == "REFERENCE_SOURCE_REVIEW_BEFORE_LIBRARY_PACK_BUILD"

    source = receipt["sources"][0]
    assert source["source_sha256"] == expected_sha
    assert source["byte_count"] == len(payload)
    assert source["page_count"] == 1
    assert source["source_bytes_redistributed"] is False
    assert source["matched_query_count"] == 2
    assert source["authority"] == acquire.AUTHORITY
    results = {row["query"]: row for row in source["evidence_query_results"]}
    assert results["CAD Standard Symbols"]["matched"] is True
    assert results["Section Mark Blocks"]["matched"] is True
    assert results["not present"]["matched"] is False
    for query in ("CAD Standard Symbols", "Section Mark Blocks"):
        match = results[query]["matches"][0]
        assert match["page_index"] == 0
        assert len(match["page_text_sha256"]) == 64
        assert len(match["page_feature_sha256"]) == 64
        assert "text" not in match

    print("CEW_EXTERNAL_GRAPHIC_REFERENCE_ACQUISITION_PASS")
    print("https_allowlist=PASS exact_byte_sha256=PASS page_query_fingerprints=PASS")
    print("source_bytes_redistributed=false library_entries_created=false")
    print("project_semantic_authority=NONE canonical_write_authorized=false")


if __name__ == "__main__":
    main()
