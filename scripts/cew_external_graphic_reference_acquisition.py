#!/usr/bin/env python3
"""Governed acquisition of external graphic-reference sources.

The source list is repository-governed. This command downloads exact bytes from
an HTTPS allowlist, fingerprints them, locates evidence-query pages and emits an
acquisition receipt. It deliberately does NOT create Graphic Reference Library
entries and grants no project semantic authority.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import socket
from typing import Any
from urllib import error, parse, request

import pymupdf

SEED_SCHEMA = "CEW_EXTERNAL_REFERENCE_DISCOVERY_SEEDS_v1"
RECEIPT_SCHEMA = "CEW_EXTERNAL_GRAPHIC_REFERENCE_ACQUISITION_RECEIPT_v1"
ACQUIRER_VERSION = "CEW_EXTERNAL_GRAPHIC_REFERENCE_ACQUIRER_v1"
MAX_SOURCE_BYTES = 100 * 1024 * 1024
TIMEOUT_SECONDS = 45
FETCH_ATTEMPTS = 3
ALLOWED_HOST_SUFFIXES = (
    "wbdg.org",
    "nps.gov",
    "publications.usace.army.mil",
    "erdc-library.erdc.dren.mil",
    "sifacilities.si.edu",
)

AUTHORITY = {
    "reference_acquisition_only": True,
    "library_entries_created": False,
    "project_semantic_authority": "NONE",
    "canonical_write_authorized": False,
    "structural_identity_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_text(text: str) -> str:
    return " ".join(str(text).casefold().split())


def _allowed_url(url: str) -> bool:
    parsed = parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower().rstrip(".")
    return any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_HOST_SUFFIXES)


class _StrictRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        if not _allowed_url(newurl):
            raise ValueError("EXTERNAL_REFERENCE_REDIRECT_HOST_NOT_ALLOWED")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch_exact_bytes(url: str) -> tuple[bytes, dict[str, Any]]:
    if not _allowed_url(url):
        raise ValueError("EXTERNAL_REFERENCE_URL_NOT_ALLOWED")
    opener = request.build_opener(_StrictRedirect())
    last_error: Exception | None = None
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        req = request.Request(
            url,
            method="GET",
            headers={
                "User-Agent": "CEW-External-Reference-Acquirer/1.0",
                "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.1",
            },
        )
        try:
            with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
                final_url = response.geturl()
                if not _allowed_url(final_url):
                    raise ValueError("EXTERNAL_REFERENCE_FINAL_HOST_NOT_ALLOWED")
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_SOURCE_BYTES:
                    raise ValueError("EXTERNAL_REFERENCE_SOURCE_TOO_LARGE")
                chunks: list[bytes] = []
                total = 0
                while True:
                    chunk = response.read(min(1024 * 1024, MAX_SOURCE_BYTES + 1 - total))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                    if total > MAX_SOURCE_BYTES:
                        raise ValueError("EXTERNAL_REFERENCE_SOURCE_TOO_LARGE")
                data = b"".join(chunks)
                return data, {
                    "requested_url": url,
                    "final_url": final_url,
                    "http_status": int(getattr(response, "status", 200)),
                    "content_type": str(response.headers.get("Content-Type") or ""),
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "fetch_attempt": attempt,
                }
        except (TimeoutError, socket.timeout, error.URLError, error.HTTPError) as exc:
            last_error = exc
            if attempt >= FETCH_ATTEMPTS:
                break
    raise ValueError("EXTERNAL_REFERENCE_FETCH_FAILED") from last_error


def _page_feature_fingerprint(page: pymupdf.Page) -> tuple[str, dict[str, Any]]:
    drawings = page.get_drawings()
    blocks = page.get_text("blocks")
    images = page.get_images(full=True)
    vector_signature: list[dict[str, Any]] = []
    for drawing in drawings:
        rect = drawing.get("rect")
        if rect is None:
            continue
        r = pymupdf.Rect(rect)
        ops = [str(item[0]) for item in (drawing.get("items") or []) if item]
        vector_signature.append(
            {
                "bbox_pt": [round(float(r.x0), 3), round(float(r.y0), 3), round(float(r.x1), 3), round(float(r.y1), 3)],
                "ops": ops,
                "filled": drawing.get("fill") is not None,
                "width": round(float(drawing.get("width") or 0.0), 3),
            }
        )
    payload = {
        "width_pt": round(float(page.rect.width), 3),
        "height_pt": round(float(page.rect.height), 3),
        "rotation": int(page.rotation),
        "drawing_count": len(drawings),
        "text_block_count": len(blocks),
        "image_count": len(images),
        "vector_signature": vector_signature,
    }
    return _sha256(_canonical(payload).encode("utf-8")), {
        "drawing_count": len(drawings),
        "text_block_count": len(blocks),
        "image_count": len(images),
    }


def _locate_queries(doc: pymupdf.Document, queries: list[str]) -> list[dict[str, Any]]:
    normalized_queries = [(query, _normalize_text(query)) for query in queries if str(query).strip()]
    matches: dict[str, list[dict[str, Any]]] = {query: [] for query, _ in normalized_queries}
    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        page_text = _normalize_text(page.get_text("text"))
        if not page_text:
            continue
        for query, normalized in normalized_queries:
            if normalized and normalized in page_text:
                feature_sha, counts = _page_feature_fingerprint(page)
                matches[query].append(
                    {
                        "page_index": page_index,
                        "page_number_1_based": page_index + 1,
                        "page_text_sha256": _sha256(page_text.encode("utf-8")),
                        "page_feature_sha256": feature_sha,
                        **counts,
                    }
                )
    return [
        {
            "query": query,
            "matched": bool(rows),
            "matches": rows,
        }
        for query, rows in matches.items()
    ]


def acquire_source(seed: dict[str, Any]) -> dict[str, Any]:
    source_id = str(seed.get("source_id") or "").strip()
    url = str(seed.get("source_url") or "").strip()
    if not re.fullmatch(r"GREF-SRC-[A-Z0-9-]+", source_id):
        raise ValueError("EXTERNAL_REFERENCE_SOURCE_ID_INVALID")
    data, transport = _fetch_exact_bytes(url)
    if not data.startswith(b"%PDF"):
        raise ValueError("EXTERNAL_REFERENCE_NOT_PDF")
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        queries = _locate_queries(doc, list(seed.get("evidence_queries") or []))
        page_count = int(doc.page_count)
    return {
        "source_id": source_id,
        "title": seed.get("title"),
        "publisher": seed.get("publisher"),
        "source_url": url,
        "reference_scope": list(seed.get("reference_scope") or []),
        "usage_note": seed.get("usage_note"),
        "acquisition_status": "ACQUIRED_EXACT_BYTES",
        "source_sha256": _sha256(data),
        "byte_count": len(data),
        "page_count": page_count,
        "transport": transport,
        "evidence_query_results": queries,
        "matched_query_count": sum(1 for item in queries if item["matched"]),
        "source_bytes_redistributed": False,
        "authority": dict(AUTHORITY),
    }


def acquire_seed_manifest(seed_manifest: dict[str, Any]) -> dict[str, Any]:
    if seed_manifest.get("schema") != SEED_SCHEMA:
        raise ValueError("EXTERNAL_REFERENCE_SEED_SCHEMA_INVALID")
    sources = seed_manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("EXTERNAL_REFERENCE_SEEDS_EMPTY")
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for seed in sources:
        try:
            results.append(acquire_source(seed))
        except Exception as exc:
            failures.append(
                {
                    "source_id": str(seed.get("source_id") or "UNKNOWN"),
                    "error_code": str(exc) if isinstance(exc, ValueError) else "EXTERNAL_REFERENCE_ACQUISITION_ERROR",
                }
            )
    status = "PASS" if len(results) == len(sources) else ("PARTIAL" if results else "FAILED")
    identity = {
        "acquirer_version": ACQUIRER_VERSION,
        "sources": [
            {"source_id": row["source_id"], "source_sha256": row["source_sha256"]}
            for row in sorted(results, key=lambda x: x["source_id"])
        ],
        "failures": sorted(failures, key=lambda x: x["source_id"]),
    }
    return {
        "schema": RECEIPT_SCHEMA,
        "status": status,
        "acquired_at": datetime.now(timezone.utc).isoformat(),
        "acquirer_version": ACQUIRER_VERSION,
        "seed_schema": SEED_SCHEMA,
        "seed_source_count": len(sources),
        "acquired_source_count": len(results),
        "failed_source_count": len(failures),
        "receipt_fingerprint": "sha256:" + _sha256(_canonical(identity).encode("utf-8")),
        "sources": sorted(results, key=lambda x: x["source_id"]),
        "failures": sorted(failures, key=lambda x: x["source_id"]),
        "library_promotion_authorized": False,
        "authority": dict(AUTHORITY),
        "next_gate": "REFERENCE_SOURCE_REVIEW_BEFORE_LIBRARY_PACK_BUILD",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire governed external graphic references")
    parser.add_argument("--seeds", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-all", action="store_true")
    args = parser.parse_args()
    seeds = json.loads(args.seeds.read_text(encoding="utf-8"))
    receipt = acquire_seed_manifest(seeds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"CEW_EXTERNAL_GRAPHIC_REFERENCE_ACQUISITION status={receipt['status']} acquired={receipt['acquired_source_count']} failed={receipt['failed_source_count']}")
    for row in receipt["sources"]:
        print(f"source={row['source_id']} sha256={row['source_sha256']} pages={row['page_count']} matched_queries={row['matched_query_count']}")
    for row in receipt["failures"]:
        print(f"failed_source={row['source_id']} error={row['error_code']}")
    if args.require_all and receipt["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
