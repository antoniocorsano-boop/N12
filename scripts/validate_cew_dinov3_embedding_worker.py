#!/usr/bin/env python3
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile

import cew_dinov3_embedding_worker as worker
import cew_dinov3_provider as provider
import cew_visual_embedding_cache as cache


def run(*args: str, cwd: Path) -> str:
    return subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()


def fake_repo(root: Path) -> tuple[Path, str, Path, str]:
    repo = root / "dinov3"
    repo.mkdir()
    (repo / "hubconf.py").write_text("dependencies = ['torch', 'numpy']\n", encoding="utf-8")
    run("git", "init", cwd=repo)
    run("git", "config", "user.email", "ci@example.invalid", cwd=repo)
    run("git", "config", "user.name", "CEW CI", cwd=repo)
    run("git", "add", "hubconf.py", cwd=repo)
    run("git", "commit", "-m", "fake dinov3", cwd=repo)
    commit = run("git", "rev-parse", "HEAD", cwd=repo)
    weights = root / "weights.pth"
    weights.write_bytes(b"fake-weights")
    return repo, commit, weights, sha256(weights.read_bytes()).hexdigest()


def make_embedding(config: provider.DinoV3Config, verified: dict, governed: dict, vector: list[float]) -> dict:
    provider_version = worker.provider_version(config, verified)
    input_fp = provider.input_fingerprint(governed)
    identity = {
        "provider_id": provider.PROVIDER_ID,
        "provider_version": provider_version,
        "input_fingerprint": input_fp,
        "vector": vector,
    }
    fingerprint = "sha256:" + sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema": provider.EMBEDDING_SCHEMA,
        "embedding_id": "VEMB-DINO3-WORKER-TEST",
        "provider_id": provider.PROVIDER_ID,
        "provider_version": provider_version,
        "provider_revision_fingerprint": verified["provider_revision_fingerprint"],
        "channel": "VISUAL_FOUNDATION",
        "dimension": len(vector),
        "vector": vector,
        "input_fingerprint": input_fp,
        "embedding_fingerprint": fingerprint,
        "source_version_id": governed["source_version_id"],
        "source_sha256": governed["source_sha256"],
        "page_id": governed["page_id"],
        "page_index": governed["page_index"],
        "coordinate_system": governed["coordinate_system"],
        "bbox": governed["bbox"],
        "region_image_sha256": governed["region_image_sha256"],
        "candidate_id": governed["candidate_id"],
        "semantic_authority": "NONE",
        "authority": dict(provider.AUTHORITY),
    }


def main() -> None:
    old_backend = os.environ.get("CEW_VISUAL_EMBEDDING_CACHE_BACKEND")
    original_extract = provider.extract_embedding
    try:
        os.environ["CEW_VISUAL_EMBEDDING_CACHE_BACKEND"] = "FILESYSTEM"
        with tempfile.TemporaryDirectory(prefix="cew-dino-worker-") as temp:
            root = Path(temp)
            repo, commit, weights, weights_sha = fake_repo(root)
            config = provider.DinoV3Config(
                repo_dir=repo,
                repo_commit=commit,
                weights_path=weights,
                weights_sha256=weights_sha,
            )
            verified = provider.verify_configuration(config)
            image = b"immutable-region-image-bytes"
            binding = {
                "source_version_id": "SRC-001",
                "source_sha256": "1" * 64,
                "page_id": "PAGE-001",
                "page_index": 0,
                "coordinate_system": "NORMALIZED_0_1",
                "bbox": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2},
                "region_image_sha256": sha256(image).hexdigest(),
                "candidate_id": "CAND-001",
            }
            governed = provider.validate_region_binding(binding, image)
            embedding = make_embedding(config, verified, governed, [0.6, 0.8])
            expected = worker.expected_cache_key(config, verified, governed)
            assert cache.cache_key(embedding) == expected
            cache_root = root / "cache"
            cache.put_embedding(embedding, root=cache_root)

            provider.extract_embedding = lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("DINO inference must not run on cache hit")
            )
            hit = worker.get_or_extract(image, binding, config=config, cache_root=cache_root)
            assert hit["state"] == "CACHE_HIT"
            assert hit["inference_executed"] is False
            assert hit["cache_key"] == expected

            miss_binding = dict(binding)
            miss_binding["candidate_id"] = "CAND-002"
            miss_governed = provider.validate_region_binding(miss_binding, image)
            miss_embedding = make_embedding(config, verified, miss_governed, [0.8, 0.6])
            calls = {"count": 0}

            def fake_extract(*args, **kwargs):
                calls["count"] += 1
                return miss_embedding

            provider.extract_embedding = fake_extract
            miss = worker.get_or_extract(image, miss_binding, config=config, cache_root=cache_root)
            assert miss["state"] == "CACHE_MISS_INFERRED"
            assert miss["inference_executed"] is True
            assert calls["count"] == 1
            again = worker.get_or_extract(image, miss_binding, config=config, cache_root=cache_root)
            assert again["state"] == "CACHE_HIT"
            assert again["inference_executed"] is False
            assert calls["count"] == 1

        print("CEW_DINOV3_CACHE_FIRST_WORKER_PASS")
        print("cache_hit_skips_inference=PASS")
        print("cache_miss_infers_once=PASS")
        print("immutable_request_key_matches_embedding_key=PASS")
    finally:
        provider.extract_embedding = original_extract
        if old_backend is None:
            os.environ.pop("CEW_VISUAL_EMBEDDING_CACHE_BACKEND", None)
        else:
            os.environ["CEW_VISUAL_EMBEDDING_CACHE_BACKEND"] = old_backend


if __name__ == "__main__":
    main()
