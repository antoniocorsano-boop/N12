#!/usr/bin/env python3
"""Cache-first CEW DINOv3 embedding worker.

The worker computes the content-addressed cache key from the verified provider
revision and immutable region binding before invoking DINOv3. A cache hit avoids
model loading entirely. A miss invokes the governed provider and writes the
result to the configured cache backend.
"""
from __future__ import annotations

from hashlib import sha256
import argparse
import json
from pathlib import Path
from typing import Any

import cew_dinov3_provider as provider
import cew_visual_embedding_cache as cache


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def provider_version(config: provider.DinoV3Config, verified: dict[str, Any]) -> str:
    return (
        f"{config.model_name}@{verified['repo_commit']}:"
        f"{verified['weights_sha256']}:input{config.input_size}:cls-v1"
    )


def expected_cache_key(
    config: provider.DinoV3Config,
    verified: dict[str, Any],
    governed_binding: dict[str, Any],
) -> str:
    input_fp = provider.input_fingerprint(governed_binding)
    payload = {
        "provider_revision_fingerprint": verified["provider_revision_fingerprint"],
        "provider_id": provider.PROVIDER_ID,
        "provider_version": provider_version(config, verified),
        "input_fingerprint": input_fp,
        "source_version_id": governed_binding["source_version_id"],
        "source_sha256": governed_binding["source_sha256"],
        "page_id": governed_binding["page_id"],
        "page_index": governed_binding["page_index"],
        "coordinate_system": governed_binding["coordinate_system"],
        "bbox": governed_binding["bbox"],
        "region_image_sha256": governed_binding["region_image_sha256"],
        "candidate_id": governed_binding["candidate_id"],
    }
    return "vemb-" + _sha256_json(payload)


def get_or_extract(
    image_bytes: bytes,
    binding: dict[str, Any],
    *,
    config: provider.DinoV3Config | None = None,
    cache_root: Path = cache.DEFAULT_ROOT,
) -> dict[str, Any]:
    config = config or provider.DinoV3Config.from_env()
    verified = provider.verify_configuration(config)
    governed_binding = provider.validate_region_binding(binding, image_bytes)
    key = expected_cache_key(config, verified, governed_binding)
    cached = cache.get_embedding(key, root=cache_root)
    if cached is not None:
        return {
            "state": "CACHE_HIT",
            "cache_key": key,
            "embedding": cached,
            "provider_revision_fingerprint": verified["provider_revision_fingerprint"],
            "inference_executed": False,
            "authority": dict(provider.AUTHORITY),
        }

    embedding = provider.extract_embedding(image_bytes, governed_binding, config=config)
    actual_key = cache.cache_key(embedding)
    if actual_key != key:
        raise ValueError("DINOV3_WORKER_CACHE_KEY_DRIFT")
    stored = cache.put_embedding(embedding, root=cache_root)
    return {
        "state": "CACHE_MISS_INFERRED",
        "cache_key": key,
        "embedding": embedding,
        "cache_write": stored,
        "provider_revision_fingerprint": verified["provider_revision_fingerprint"],
        "inference_executed": True,
        "authority": dict(provider.AUTHORITY),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CEW cache-first DINOv3 embedding worker")
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = get_or_extract(
        args.image.read_bytes(),
        json.loads(args.binding.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
