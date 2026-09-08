#!/usr/bin/env python3
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile

import cew_dinov3_provider as provider
import cew_visual_embedding_cache as cache


def run(*args: str, cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout.strip()


def make_fake_repo(root: Path) -> tuple[Path, str]:
    repo = root / "dinov3"
    repo.mkdir()
    (repo / "hubconf.py").write_text("dependencies = ['torch', 'numpy']\n", encoding="utf-8")
    run("git", "init", cwd=repo)
    run("git", "config", "user.email", "ci@example.invalid", cwd=repo)
    run("git", "config", "user.name", "CEW CI", cwd=repo)
    run("git", "add", "hubconf.py", cwd=repo)
    run("git", "commit", "-m", "fake immutable dinov3 source", cwd=repo)
    commit = run("git", "rev-parse", "HEAD", cwd=repo)
    return repo, commit


def synthetic_embedding(revision: str, binding: dict, vector: list[float]) -> dict:
    input_fp = provider.input_fingerprint(binding)
    provider_version = "dinov3_vits16@test:weights:input256:cls-v1"
    identity = {
        "provider_id": provider.PROVIDER_ID,
        "provider_version": provider_version,
        "input_fingerprint": input_fp,
        "vector": vector,
    }
    embedding_fp = "sha256:" + sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema": provider.EMBEDDING_SCHEMA,
        "embedding_id": "VEMB-DINO3-TEST",
        "provider_id": provider.PROVIDER_ID,
        "provider_version": provider_version,
        "provider_revision_fingerprint": revision,
        "channel": "VISUAL_FOUNDATION",
        "dimension": len(vector),
        "vector": vector,
        "input_fingerprint": input_fp,
        "embedding_fingerprint": embedding_fp,
        "source_version_id": binding["source_version_id"],
        "source_sha256": binding["source_sha256"],
        "page_id": binding["page_id"],
        "page_index": binding["page_index"],
        "coordinate_system": binding["coordinate_system"],
        "bbox": binding["bbox"],
        "region_image_sha256": binding["region_image_sha256"],
        "candidate_id": binding["candidate_id"],
        "semantic_authority": "NONE",
        "authority": dict(provider.AUTHORITY),
    }


def main() -> None:
    original = {key: os.environ.get(key) for key in (
        "CEW_DINOV3_REPO_DIR",
        "CEW_DINOV3_REPO_COMMIT",
        "CEW_DINOV3_WEIGHTS_PATH",
        "CEW_DINOV3_WEIGHTS_SHA256",
        "CEW_VISUAL_EMBEDDING_CACHE_BACKEND",
    )}
    for key in list(original):
        os.environ.pop(key, None)
    try:
        status = provider.provider_environment_status()
        assert status["implementation_state"] == "IMPLEMENTED_NOT_PROVISIONED"
        assert len(status["missing_environment"]) == 4
        assert status["web_worker_dependency"] is False
        assert status["runtime_network_fetch_allowed"] is False

        with tempfile.TemporaryDirectory(prefix="cew-dino-provider-") as temp:
            root = Path(temp)
            repo, commit = make_fake_repo(root)
            weights = root / "weights.pth"
            weights.write_bytes(b"cew-fake-checkpoint-for-governance-test")
            weights_sha = sha256(weights.read_bytes()).hexdigest()
            config = provider.DinoV3Config(
                repo_dir=repo,
                repo_commit=commit,
                weights_path=weights,
                weights_sha256=weights_sha,
                model_name="dinov3_vits16",
                device="cpu",
                input_size=256,
            )
            verified = provider.verify_configuration(config)
            assert verified["implementation_state"] == "PROVISIONED_VERIFIED"
            assert verified["repo_commit"] == commit
            assert verified["weights_sha256"] == weights_sha
            assert verified["provider_revision_fingerprint"].startswith("sha256:")
            assert verified["authority"]["canonical_write_authorized"] is False

            try:
                provider.verify_configuration(provider.DinoV3Config(
                    repo_dir=repo,
                    repo_commit=commit,
                    weights_path=weights,
                    weights_sha256="0" * 64,
                ))
                raise AssertionError("wrong weights hash must fail")
            except ValueError as exc:
                assert "WEIGHTS_SHA256_MISMATCH" in str(exc)

            image_bytes = b"not-an-image-but-hash-bound-for-contract-test"
            image_sha = sha256(image_bytes).hexdigest()
            binding = {
                "source_version_id": "SRC-IMMUTABLE-001",
                "source_sha256": "1" * 64,
                "page_id": "PAGE-001",
                "page_index": 0,
                "coordinate_system": "NORMALIZED_0_1",
                "bbox": {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4},
                "region_image_sha256": image_sha,
                "candidate_id": "GPC-001",
                "derived_asset_id": "ASSET-001",
                "page_transform_id": "XFORM-001",
            }
            governed = provider.validate_region_binding(binding, image_bytes)
            assert governed["region_image_sha256"] == image_sha
            assert provider.input_fingerprint(governed).startswith("sha256:")
            try:
                bad = dict(binding)
                bad["region_image_sha256"] = "2" * 64
                provider.validate_region_binding(bad, image_bytes)
                raise AssertionError("stale image hash must fail")
            except ValueError as exc:
                assert "REGION_IMAGE_SHA256_MISMATCH" in str(exc)

            vector = [0.6, 0.8]
            embedding = synthetic_embedding(verified["provider_revision_fingerprint"], governed, vector)
            entry = cache.build_entry(embedding)
            cache.validate_entry(entry)
            assert entry["authority"]["canonical_write_authorized"] is False

            cache_root = root / "cache"
            os.environ["CEW_VISUAL_EMBEDDING_CACHE_BACKEND"] = "FILESYSTEM"
            first = cache.put_embedding(embedding, root=cache_root)
            second = cache.put_embedding(embedding, root=cache_root)
            assert first["state"] == "CACHE_WRITE"
            assert second["state"] == "CACHE_HIT"
            loaded = cache.get_embedding(first["cache_key"], root=cache_root)
            assert loaded is not None
            assert loaded["embedding_fingerprint"] == embedding["embedding_fingerprint"]

            target = cache._filesystem_path(cache_root, first["cache_key"])
            tampered = json.loads(target.read_text(encoding="utf-8"))
            tampered["embedding"]["vector"] = [1.0, 0.0]
            target.write_text(json.dumps(tampered), encoding="utf-8")
            try:
                cache.get_embedding(first["cache_key"], root=cache_root)
                raise AssertionError("tampered cache entry must fail")
            except ValueError as exc:
                assert "FINGERPRINT_MISMATCH" in str(exc) or "SHA256_MISMATCH" in str(exc)

        print("CEW_DINOV3_PROVIDER_CONTRACT_PASS")
        print("provider_state=IMPLEMENTED_NOT_PROVISIONED")
        print("immutable_repo_commit_verification=PASS")
        print("checkpoint_sha256_verification=PASS")
        print("source_region_binding=PASS")
        print("content_addressed_embedding_cache=PASS")
        print("cache_idempotence=PASS")
        print("cache_tamper_detection=PASS")
        print("actual_dinov3_inference=NOT_RUN_NO_OFFICIAL_WEIGHTS")
        print("canonical_write_authorized=false project_semantic_authority=NONE")
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    main()
