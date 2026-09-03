#!/usr/bin/env python3
"""Content-addressed cache for CEW visual embeddings.

Embeddings are derived artifacts. They are keyed by immutable provider and input
fingerprints and never carry project semantic, CAD, structural or engineering
authority. The cache supports a local filesystem backend and an explicit Neon
backend for persistent inference workers.
"""
from __future__ import annotations

from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import re
from typing import Any

CACHE_SCHEMA = "CEW_VISUAL_EMBEDDING_CACHE_ENTRY_v1"
EMBEDDING_SCHEMA = "CEW_VISUAL_EMBEDDING_v1"
DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "runtime" / "visual_embedding_cache"
SAFE_KEY = re.compile(r"^[a-z0-9-]{16,96}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")

AUTHORITY = {
    "project_semantic_authority": "NONE",
    "canonical_write_authorized": False,
    "structural_identity_authorized": False,
    "engineering_authority_effect": "NONE",
}

NEON_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS public.cew_visual_embedding_cache (
    cache_key text PRIMARY KEY,
    provider_id text NOT NULL,
    provider_version text NOT NULL,
    provider_revision_fingerprint text NOT NULL,
    input_fingerprint text NOT NULL,
    source_version_id text NOT NULL,
    source_sha256 text NOT NULL,
    page_id text NOT NULL,
    page_index integer NOT NULL,
    candidate_id text NOT NULL,
    region_image_sha256 text NOT NULL,
    embedding_fingerprint text NOT NULL,
    entry_sha256 text NOT NULL,
    entry_json jsonb NOT NULL,
    semantic_authority text NOT NULL DEFAULT 'NONE',
    canonical_write_authorized boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT cew_visual_embedding_cache_no_authority CHECK (
      semantic_authority = 'NONE' AND canonical_write_authorized = false
    )
);
CREATE UNIQUE INDEX IF NOT EXISTS cew_visual_embedding_cache_embedding_fingerprint_uq
ON public.cew_visual_embedding_cache (embedding_fingerprint);
""".strip()


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _required_text(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"VISUAL_CACHE_{name.upper()}_REQUIRED")
    return text


def _validate_sha256(value: Any, name: str) -> str:
    text = _required_text(value, name).lower()
    if text.startswith("sha256:"):
        text = text[7:]
    if not HEX64.fullmatch(text):
        raise ValueError(f"VISUAL_CACHE_{name.upper()}_INVALID")
    return text


def validate_embedding(embedding: dict[str, Any]) -> None:
    if not isinstance(embedding, dict) or embedding.get("schema") != EMBEDDING_SCHEMA:
        raise ValueError("VISUAL_CACHE_EMBEDDING_SCHEMA_INVALID")
    provider_id = _required_text(embedding.get("provider_id"), "provider_id")
    provider_version = _required_text(embedding.get("provider_version"), "provider_version")
    input_fingerprint = _required_text(embedding.get("input_fingerprint"), "input_fingerprint")
    if not input_fingerprint.startswith("sha256:") or not HEX64.fullmatch(input_fingerprint[7:]):
        raise ValueError("VISUAL_CACHE_INPUT_FINGERPRINT_INVALID")
    vector = embedding.get("vector")
    if not isinstance(vector, list) or not vector:
        raise ValueError("VISUAL_CACHE_VECTOR_REQUIRED")
    if int(embedding.get("dimension", -1)) != len(vector):
        raise ValueError("VISUAL_CACHE_DIMENSION_MISMATCH")
    identity = {
        "provider_id": provider_id,
        "provider_version": provider_version,
        "input_fingerprint": input_fingerprint,
        "vector": [float(value) for value in vector],
    }
    expected = "sha256:" + _sha256_json(identity)
    if embedding.get("embedding_fingerprint") != expected:
        raise ValueError("VISUAL_CACHE_EMBEDDING_FINGERPRINT_MISMATCH")
    authority = embedding.get("authority") or {}
    if embedding.get("semantic_authority") not in (None, "NONE"):
        raise ValueError("VISUAL_CACHE_AUTHORITY_DRIFT")
    if authority and authority.get("canonical_write_authorized") is not False:
        raise ValueError("VISUAL_CACHE_AUTHORITY_DRIFT")


def cache_key(embedding: dict[str, Any]) -> str:
    validate_embedding(embedding)
    provider_revision = _required_text(
        embedding.get("provider_revision_fingerprint"), "provider_revision_fingerprint"
    )
    if not provider_revision.startswith("sha256:") or not HEX64.fullmatch(provider_revision[7:]):
        raise ValueError("VISUAL_CACHE_PROVIDER_REVISION_FINGERPRINT_INVALID")
    source_sha = _validate_sha256(embedding.get("source_sha256"), "source_sha256")
    region_sha = _validate_sha256(embedding.get("region_image_sha256"), "region_image_sha256")
    payload = {
        "provider_revision_fingerprint": provider_revision,
        "provider_id": embedding["provider_id"],
        "provider_version": embedding["provider_version"],
        "input_fingerprint": embedding["input_fingerprint"],
        "source_version_id": _required_text(embedding.get("source_version_id"), "source_version_id"),
        "source_sha256": source_sha,
        "page_id": _required_text(embedding.get("page_id"), "page_id"),
        "page_index": int(embedding.get("page_index")),
        "coordinate_system": _required_text(embedding.get("coordinate_system"), "coordinate_system"),
        "bbox": embedding.get("bbox"),
        "region_image_sha256": region_sha,
        "candidate_id": _required_text(embedding.get("candidate_id"), "candidate_id"),
    }
    return "vemb-" + _sha256_json(payload)


def build_entry(embedding: dict[str, Any]) -> dict[str, Any]:
    key = cache_key(embedding)
    entry = {
        "schema": CACHE_SCHEMA,
        "cache_key": key,
        "provider_id": embedding["provider_id"],
        "provider_version": embedding["provider_version"],
        "provider_revision_fingerprint": embedding["provider_revision_fingerprint"],
        "input_fingerprint": embedding["input_fingerprint"],
        "source_version_id": embedding["source_version_id"],
        "source_sha256": _validate_sha256(embedding["source_sha256"], "source_sha256"),
        "page_id": embedding["page_id"],
        "page_index": int(embedding["page_index"]),
        "coordinate_system": embedding["coordinate_system"],
        "bbox": embedding["bbox"],
        "candidate_id": embedding["candidate_id"],
        "region_image_sha256": _validate_sha256(embedding["region_image_sha256"], "region_image_sha256"),
        "embedding_fingerprint": embedding["embedding_fingerprint"],
        "embedding": embedding,
        "authority": dict(AUTHORITY),
    }
    entry["entry_sha256"] = _sha256_json(entry)
    return entry


def validate_entry(entry: dict[str, Any]) -> None:
    if not isinstance(entry, dict) or entry.get("schema") != CACHE_SCHEMA:
        raise ValueError("VISUAL_CACHE_ENTRY_SCHEMA_INVALID")
    key = _required_text(entry.get("cache_key"), "cache_key")
    if not SAFE_KEY.fullmatch(key):
        raise ValueError("VISUAL_CACHE_KEY_INVALID")
    embedding = entry.get("embedding")
    if not isinstance(embedding, dict):
        raise ValueError("VISUAL_CACHE_EMBEDDING_REQUIRED")
    validate_embedding(embedding)
    if key != cache_key(embedding):
        raise ValueError("VISUAL_CACHE_KEY_MISMATCH")
    expected_sha = _required_text(entry.get("entry_sha256"), "entry_sha256")
    payload = {k: v for k, v in entry.items() if k != "entry_sha256"}
    if expected_sha != _sha256_json(payload):
        raise ValueError("VISUAL_CACHE_ENTRY_SHA256_MISMATCH")
    if (entry.get("authority") or {}).get("canonical_write_authorized") is not False:
        raise ValueError("VISUAL_CACHE_AUTHORITY_DRIFT")


def _filesystem_path(root: Path, key: str) -> Path:
    if not SAFE_KEY.fullmatch(key):
        raise ValueError("VISUAL_CACHE_KEY_INVALID")
    return root.resolve() / key[5:7] / f"{key}.json"


def put_filesystem(entry: dict[str, Any], root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    validate_entry(entry)
    target = _filesystem_path(root, entry["cache_key"])
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(entry, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    try:
        with target.open("x", encoding="utf-8") as stream:
            stream.write(text)
        state = "CACHE_WRITE"
    except FileExistsError:
        existing = json.loads(target.read_text(encoding="utf-8"))
        validate_entry(existing)
        if existing["entry_sha256"] != entry["entry_sha256"]:
            raise ValueError("VISUAL_CACHE_CONTENT_ADDRESS_COLLISION")
        state = "CACHE_HIT"
    return {
        "state": state,
        "backend": "FILESYSTEM_CONTENT_ADDRESSED",
        "cache_key": entry["cache_key"],
        "entry_sha256": entry["entry_sha256"],
        "canonical_write_authorized": False,
    }


def get_filesystem(key: str, root: Path = DEFAULT_ROOT) -> dict[str, Any] | None:
    target = _filesystem_path(root, key)
    if not target.is_file():
        return None
    entry = json.loads(target.read_text(encoding="utf-8"))
    validate_entry(entry)
    return entry


def _neon_url() -> str:
    return _required_text(os.getenv("CEW_VISUAL_EMBEDDING_NEON_DATABASE_URL"), "neon_database_url")


def init_neon_schema() -> None:
    try:
        import psycopg
    except Exception as exc:
        raise ValueError("VISUAL_CACHE_NEON_DRIVER_UNAVAILABLE") from exc
    with psycopg.connect(_neon_url(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute(NEON_SCHEMA_SQL)
        conn.commit()


def put_neon(entry: dict[str, Any]) -> dict[str, Any]:
    validate_entry(entry)
    try:
        import psycopg
    except Exception as exc:
        raise ValueError("VISUAL_CACHE_NEON_DRIVER_UNAVAILABLE") from exc
    sql = """
      INSERT INTO public.cew_visual_embedding_cache
        (cache_key, provider_id, provider_version, provider_revision_fingerprint,
         input_fingerprint, source_version_id, source_sha256, page_id, page_index,
         candidate_id, region_image_sha256, embedding_fingerprint, entry_sha256,
         entry_json, semantic_authority, canonical_write_authorized)
      VALUES
        (%(cache_key)s, %(provider_id)s, %(provider_version)s, %(provider_revision_fingerprint)s,
         %(input_fingerprint)s, %(source_version_id)s, %(source_sha256)s, %(page_id)s,
         %(page_index)s, %(candidate_id)s, %(region_image_sha256)s, %(embedding_fingerprint)s,
         %(entry_sha256)s, %(entry_json)s::jsonb, 'NONE', false)
      ON CONFLICT (cache_key) DO NOTHING
    """
    params = {
        "cache_key": entry["cache_key"],
        "provider_id": entry["provider_id"],
        "provider_version": entry["provider_version"],
        "provider_revision_fingerprint": entry["provider_revision_fingerprint"],
        "input_fingerprint": entry["input_fingerprint"],
        "source_version_id": entry["source_version_id"],
        "source_sha256": entry["source_sha256"],
        "page_id": entry["page_id"],
        "page_index": entry["page_index"],
        "candidate_id": entry["candidate_id"],
        "region_image_sha256": entry["region_image_sha256"],
        "embedding_fingerprint": entry["embedding_fingerprint"],
        "entry_sha256": entry["entry_sha256"],
        "entry_json": _canonical(entry),
    }
    with psycopg.connect(_neon_url(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            inserted = cur.rowcount == 1
            cur.execute(
                "SELECT entry_sha256, entry_json FROM public.cew_visual_embedding_cache WHERE cache_key = %s",
                (entry["cache_key"],),
            )
            row = cur.fetchone()
        conn.commit()
    if row is None:
        raise ValueError("VISUAL_CACHE_NEON_READBACK_MISSING")
    existing_sha, existing_json = row
    if str(existing_sha) != entry["entry_sha256"]:
        raise ValueError("VISUAL_CACHE_CONTENT_ADDRESS_COLLISION")
    existing = existing_json if isinstance(existing_json, dict) else json.loads(existing_json)
    validate_entry(existing)
    return {
        "state": "CACHE_WRITE" if inserted else "CACHE_HIT",
        "backend": "NEON_CONTENT_ADDRESSED",
        "cache_key": entry["cache_key"],
        "entry_sha256": entry["entry_sha256"],
        "canonical_write_authorized": False,
    }


def get_neon(key: str) -> dict[str, Any] | None:
    if not SAFE_KEY.fullmatch(key):
        raise ValueError("VISUAL_CACHE_KEY_INVALID")
    try:
        import psycopg
    except Exception as exc:
        raise ValueError("VISUAL_CACHE_NEON_DRIVER_UNAVAILABLE") from exc
    with psycopg.connect(_neon_url(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT entry_json FROM public.cew_visual_embedding_cache WHERE cache_key = %s",
                (key,),
            )
            row = cur.fetchone()
    if row is None:
        return None
    payload = row[0] if isinstance(row[0], dict) else json.loads(row[0])
    validate_entry(payload)
    return payload


def backend_name() -> str:
    value = str(os.getenv("CEW_VISUAL_EMBEDDING_CACHE_BACKEND", "FILESYSTEM")).strip().upper()
    if value not in {"FILESYSTEM", "NEON"}:
        raise ValueError("VISUAL_CACHE_BACKEND_INVALID")
    return value


def put_embedding(embedding: dict[str, Any], *, root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    entry = build_entry(embedding)
    return put_neon(entry) if backend_name() == "NEON" else put_filesystem(entry, root)


def get_embedding(key: str, *, root: Path = DEFAULT_ROOT) -> dict[str, Any] | None:
    entry = get_neon(key) if backend_name() == "NEON" else get_filesystem(key, root)
    return None if entry is None else entry["embedding"]


def main() -> None:
    parser = argparse.ArgumentParser(description="CEW content-addressed visual embedding cache")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-neon")
    put = subparsers.add_parser("put")
    put.add_argument("--embedding", type=Path, required=True)
    get = subparsers.add_parser("get")
    get.add_argument("--cache-key", required=True)
    get.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "init-neon":
        init_neon_schema()
        print("CEW_VISUAL_EMBEDDING_CACHE_NEON_SCHEMA_READY")
        return
    if args.command == "put":
        embedding = json.loads(args.embedding.read_text(encoding="utf-8"))
        print(json.dumps(put_embedding(embedding), indent=2, ensure_ascii=False))
        return
    embedding = get_embedding(args.cache_key)
    if embedding is None:
        raise SystemExit(2)
    text = json.dumps(embedding, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
