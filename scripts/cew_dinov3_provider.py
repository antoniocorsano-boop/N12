#!/usr/bin/env python3
"""Governed DINOv3 frozen-feature provider for CEW.

This module is intentionally optional. It is not imported by the normal CEW web
runtime and lazily imports PyTorch only when actual visual inference is requested.
The DINOv3 repository and checkpoint must already exist locally and are verified
against immutable identifiers before model loading. Runtime network acquisition
of code or weights is forbidden.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
from typing import Any

PROVIDER_ID = "DINOV3_FROZEN_FEATURES"
EMBEDDING_SCHEMA = "CEW_VISUAL_EMBEDDING_v1"
PROVIDER_CONTRACT_SCHEMA = "CEW_DINOV3_PROVIDER_CONTRACT_v1"
ALLOWED_MODELS = {"dinov3_vits16"}
DEFAULT_MODEL = "dinov3_vits16"
DEFAULT_DEVICE = "cpu"
DEFAULT_INPUT_SIZE = 256
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")

AUTHORITY = {
    "project_semantic_authority": "NONE",
    "oar_human_confirmation": False,
    "oar_classification_confirmed": False,
    "f2_registry_written": False,
    "canonical_write_authorized": False,
    "structural_identity_authorized": False,
    "engineering_authority_effect": "NONE",
    "human_project_validation_required": True,
}

_MODEL_CACHE: dict[str, tuple[Any, Any, Any]] = {}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical(value).encode("utf-8"))


def _required_text(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"DINOV3_{name.upper()}_REQUIRED")
    return text


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _git(repo_dir: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


@dataclass(frozen=True)
class DinoV3Config:
    repo_dir: Path
    repo_commit: str
    weights_path: Path
    weights_sha256: str
    model_name: str = DEFAULT_MODEL
    device: str = DEFAULT_DEVICE
    input_size: int = DEFAULT_INPUT_SIZE

    @classmethod
    def from_env(cls) -> "DinoV3Config":
        return cls(
            repo_dir=Path(_required_text(os.getenv("CEW_DINOV3_REPO_DIR"), "repo_dir")),
            repo_commit=_required_text(os.getenv("CEW_DINOV3_REPO_COMMIT"), "repo_commit").lower(),
            weights_path=Path(_required_text(os.getenv("CEW_DINOV3_WEIGHTS_PATH"), "weights_path")),
            weights_sha256=_required_text(os.getenv("CEW_DINOV3_WEIGHTS_SHA256"), "weights_sha256").lower(),
            model_name=str(os.getenv("CEW_DINOV3_MODEL_NAME", DEFAULT_MODEL)).strip() or DEFAULT_MODEL,
            device=str(os.getenv("CEW_DINOV3_DEVICE", DEFAULT_DEVICE)).strip() or DEFAULT_DEVICE,
            input_size=int(os.getenv("CEW_DINOV3_INPUT_SIZE", str(DEFAULT_INPUT_SIZE))),
        )


def provider_environment_status() -> dict[str, Any]:
    required = {
        "CEW_DINOV3_REPO_DIR": os.getenv("CEW_DINOV3_REPO_DIR"),
        "CEW_DINOV3_REPO_COMMIT": os.getenv("CEW_DINOV3_REPO_COMMIT"),
        "CEW_DINOV3_WEIGHTS_PATH": os.getenv("CEW_DINOV3_WEIGHTS_PATH"),
        "CEW_DINOV3_WEIGHTS_SHA256": os.getenv("CEW_DINOV3_WEIGHTS_SHA256"),
    }
    missing = sorted(key for key, value in required.items() if not str(value or "").strip())
    return {
        "provider_id": PROVIDER_ID,
        "implementation_state": "IMPLEMENTED_NOT_PROVISIONED" if missing else "CONFIGURATION_PRESENT_UNVERIFIED",
        "missing_environment": missing,
        "runtime_network_fetch_allowed": False,
        "web_worker_dependency": False,
        "authority": dict(AUTHORITY),
    }


def verify_configuration(config: DinoV3Config) -> dict[str, Any]:
    repo_dir = config.repo_dir.expanduser().resolve()
    weights_path = config.weights_path.expanduser().resolve()
    if config.model_name not in ALLOWED_MODELS:
        raise ValueError("DINOV3_MODEL_NOT_ALLOWED")
    if config.input_size <= 0 or config.input_size > 2048:
        raise ValueError("DINOV3_INPUT_SIZE_INVALID")
    if not HEX40.fullmatch(config.repo_commit):
        raise ValueError("DINOV3_REPO_COMMIT_INVALID")
    if not HEX64.fullmatch(config.weights_sha256):
        raise ValueError("DINOV3_WEIGHTS_SHA256_INVALID")
    if not repo_dir.is_dir() or not (repo_dir / "hubconf.py").is_file():
        raise ValueError("DINOV3_REPO_DIR_INVALID")
    actual_commit = _git(repo_dir, "rev-parse", "HEAD").lower()
    if actual_commit != config.repo_commit:
        raise ValueError("DINOV3_REPO_COMMIT_MISMATCH")
    if _git(repo_dir, "status", "--porcelain"):
        raise ValueError("DINOV3_REPO_DIRTY")
    if not weights_path.is_file():
        raise ValueError("DINOV3_WEIGHTS_MISSING")
    actual_weights_sha = _file_sha256(weights_path)
    if actual_weights_sha != config.weights_sha256:
        raise ValueError("DINOV3_WEIGHTS_SHA256_MISMATCH")

    revision_payload = {
        "provider_id": PROVIDER_ID,
        "model_name": config.model_name,
        "repo_commit": actual_commit,
        "weights_sha256": actual_weights_sha,
        "feature_output": "x_norm_clstoken",
        "preprocessing": {
            "input_size": config.input_size,
            "color_mode": "RGB",
            "mean": list(IMAGENET_MEAN),
            "std": list(IMAGENET_STD),
            "antialias": True,
        },
    }
    revision_fingerprint = "sha256:" + _sha256_json(revision_payload)
    return {
        "provider_id": PROVIDER_ID,
        "implementation_state": "PROVISIONED_VERIFIED",
        "model_name": config.model_name,
        "repo_dir": str(repo_dir),
        "repo_commit": actual_commit,
        "weights_path": str(weights_path),
        "weights_sha256": actual_weights_sha,
        "device_requested": config.device,
        "input_size": config.input_size,
        "feature_output": "x_norm_clstoken",
        "provider_revision_fingerprint": revision_fingerprint,
        "runtime_network_fetch_allowed": False,
        "authority": dict(AUTHORITY),
    }


def validate_region_binding(binding: dict[str, Any], image_bytes: bytes) -> dict[str, Any]:
    if not isinstance(binding, dict):
        raise ValueError("DINOV3_REGION_BINDING_REQUIRED")
    source_version_id = _required_text(binding.get("source_version_id"), "source_version_id")
    source_sha256 = _required_text(binding.get("source_sha256"), "source_sha256").lower()
    page_id = _required_text(binding.get("page_id"), "page_id")
    candidate_id = _required_text(binding.get("candidate_id"), "candidate_id")
    coordinate_system = _required_text(binding.get("coordinate_system"), "coordinate_system")
    if not HEX64.fullmatch(source_sha256):
        raise ValueError("DINOV3_SOURCE_SHA256_INVALID")
    try:
        page_index = int(binding.get("page_index"))
    except (TypeError, ValueError) as exc:
        raise ValueError("DINOV3_PAGE_INDEX_INVALID") from exc
    if page_index < 0:
        raise ValueError("DINOV3_PAGE_INDEX_INVALID")
    bbox = binding.get("bbox")
    if not isinstance(bbox, dict):
        raise ValueError("DINOV3_BBOX_REQUIRED")
    normalized_bbox: dict[str, float] = {}
    for key in ("x", "y", "w", "h"):
        try:
            value = float(bbox[key])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("DINOV3_BBOX_INVALID") from exc
        normalized_bbox[key] = round(value, 12)
    if normalized_bbox["w"] <= 0 or normalized_bbox["h"] <= 0:
        raise ValueError("DINOV3_BBOX_INVALID")
    if coordinate_system == "NORMALIZED_0_1":
        if any(normalized_bbox[key] < 0 or normalized_bbox[key] > 1 for key in ("x", "y", "w", "h")):
            raise ValueError("DINOV3_BBOX_OUT_OF_RANGE")
        if normalized_bbox["x"] + normalized_bbox["w"] > 1.000000000001:
            raise ValueError("DINOV3_BBOX_OUT_OF_RANGE")
        if normalized_bbox["y"] + normalized_bbox["h"] > 1.000000000001:
            raise ValueError("DINOV3_BBOX_OUT_OF_RANGE")
    region_image_sha256 = _required_text(binding.get("region_image_sha256"), "region_image_sha256").lower()
    if not HEX64.fullmatch(region_image_sha256):
        raise ValueError("DINOV3_REGION_IMAGE_SHA256_INVALID")
    actual_image_sha = _sha256_bytes(image_bytes)
    if actual_image_sha != region_image_sha256:
        raise ValueError("DINOV3_REGION_IMAGE_SHA256_MISMATCH")
    return {
        "source_version_id": source_version_id,
        "source_sha256": source_sha256,
        "page_id": page_id,
        "page_index": page_index,
        "coordinate_system": coordinate_system,
        "bbox": normalized_bbox,
        "region_image_sha256": actual_image_sha,
        "candidate_id": candidate_id,
        "derived_asset_id": str(binding.get("derived_asset_id") or "").strip() or None,
        "page_transform_id": str(binding.get("page_transform_id") or "").strip() or None,
    }


def input_fingerprint(binding: dict[str, Any]) -> str:
    governed = {
        "source_version_id": binding["source_version_id"],
        "source_sha256": binding["source_sha256"],
        "page_id": binding["page_id"],
        "page_index": binding["page_index"],
        "coordinate_system": binding["coordinate_system"],
        "bbox": binding["bbox"],
        "region_image_sha256": binding["region_image_sha256"],
        "candidate_id": binding["candidate_id"],
        "derived_asset_id": binding.get("derived_asset_id"),
        "page_transform_id": binding.get("page_transform_id"),
    }
    return "sha256:" + _sha256_json(governed)


def _normalize_vector(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(float(value) * float(value) for value in values))
    if norm <= 0:
        raise ValueError("DINOV3_ZERO_EMBEDDING")
    return [round(float(value) / norm, 12) for value in values]


def _load_model(config: DinoV3Config, verified: dict[str, Any]):
    cache_key = verified["provider_revision_fingerprint"] + ":" + config.device
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    try:
        import torch
        from PIL import Image
        from torchvision.transforms import v2
    except Exception as exc:
        raise ValueError("DINOV3_OPTIONAL_DEPENDENCIES_UNAVAILABLE") from exc

    if config.device.startswith("cuda") and not torch.cuda.is_available():
        raise ValueError("DINOV3_CUDA_REQUESTED_BUT_UNAVAILABLE")
    model = torch.hub.load(
        verified["repo_dir"],
        config.model_name,
        source="local",
        weights=verified["weights_path"],
    )
    model = model.eval().to(config.device)
    model.requires_grad_(False)
    transform = v2.Compose(
        [
            v2.ToImage(),
            v2.Resize((config.input_size, config.input_size), antialias=True),
            v2.ToDtype(torch.float32, scale=True),
            v2.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )
    _MODEL_CACHE[cache_key] = (torch, Image, (model, transform))
    return _MODEL_CACHE[cache_key]


def extract_embedding(image_bytes: bytes, binding: dict[str, Any], *, config: DinoV3Config | None = None) -> dict[str, Any]:
    if not image_bytes:
        raise ValueError("DINOV3_IMAGE_BYTES_REQUIRED")
    config = config or DinoV3Config.from_env()
    verified = verify_configuration(config)
    governed_binding = validate_region_binding(binding, image_bytes)
    torch, Image, model_bundle = _load_model(config, verified)
    model, transform = model_bundle
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError("DINOV3_REGION_IMAGE_INVALID") from exc
    batch = transform(image)[None].to(config.device)
    with torch.inference_mode():
        features = model.forward_features(batch)
    if not isinstance(features, dict) or "x_norm_clstoken" not in features:
        raise ValueError("DINOV3_FEATURE_OUTPUT_MISSING")
    token = features["x_norm_clstoken"]
    if getattr(token, "ndim", None) != 2 or int(token.shape[0]) != 1:
        raise ValueError("DINOV3_FEATURE_OUTPUT_SHAPE_INVALID")
    raw_vector = token[0].detach().float().cpu().tolist()
    vector = _normalize_vector([float(value) for value in raw_vector])
    governed_input_fingerprint = input_fingerprint(governed_binding)
    provider_version = (
        f"{config.model_name}@{verified['repo_commit']}:"
        f"{verified['weights_sha256']}:input{config.input_size}:cls-v1"
    )
    identity = {
        "provider_id": PROVIDER_ID,
        "provider_version": provider_version,
        "input_fingerprint": governed_input_fingerprint,
        "vector": vector,
    }
    embedding_fingerprint = "sha256:" + _sha256_json(identity)
    return {
        "schema": EMBEDDING_SCHEMA,
        "embedding_id": "VEMB-DINO3-" + _sha256_json(identity)[:20],
        "provider_id": PROVIDER_ID,
        "provider_version": provider_version,
        "provider_revision_fingerprint": verified["provider_revision_fingerprint"],
        "channel": "VISUAL_FOUNDATION",
        "dimension": len(vector),
        "vector": vector,
        "input_fingerprint": governed_input_fingerprint,
        "embedding_fingerprint": embedding_fingerprint,
        "source_version_id": governed_binding["source_version_id"],
        "source_sha256": governed_binding["source_sha256"],
        "page_id": governed_binding["page_id"],
        "page_index": governed_binding["page_index"],
        "coordinate_system": governed_binding["coordinate_system"],
        "bbox": governed_binding["bbox"],
        "region_image_sha256": governed_binding["region_image_sha256"],
        "candidate_id": governed_binding["candidate_id"],
        "derived_asset_id": governed_binding.get("derived_asset_id"),
        "page_transform_id": governed_binding.get("page_transform_id"),
        "feature_output": "x_norm_clstoken",
        "semantic_authority": "NONE",
        "authority": dict(AUTHORITY),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CEW governed DINOv3 frozen-feature provider")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--output", type=Path)
    extract = subparsers.add_parser("extract")
    extract.add_argument("--image", type=Path, required=True)
    extract.add_argument("--binding", type=Path, required=True)
    extract.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "status":
        payload = provider_environment_status()
    elif args.command == "verify":
        payload = verify_configuration(DinoV3Config.from_env())
    else:
        image_bytes = args.image.read_bytes()
        binding = json.loads(args.binding.read_text(encoding="utf-8"))
        payload = extract_embedding(image_bytes, binding)

    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if getattr(args, "output", None):
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
