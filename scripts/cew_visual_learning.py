#!/usr/bin/env python3
"""Governed incremental prototype learning for CEW.

The module learns review-oriented similarity from explicit human examples. The
learning memory is derived and replayable from append-only LearningReceipt
records. It grants no project semantic, CAD, structural or engineering authority.

v1 ships an explainable structured-graphic embedding. A DINOv3 frozen-feature
provider is implemented as an optional channel and is not simulated when absent.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import cew_runtime_audit_store as audit_store

CONTRACT_SCHEMA = "CEW_VISUAL_LEARNING_CONTRACT_v1"
MEMORY_SCHEMA = "CEW_PROTOTYPE_MEMORY_v1"
RECEIPT_SCHEMA = "CEW_VISUAL_LEARNING_RECEIPT_v1"
EMBEDDING_SCHEMA = "CEW_VISUAL_EMBEDDING_v1"
STRUCTURED_PROVIDER_ID = "CEW_STRUCTURED_GRAPHIC_DESCRIPTOR_V1"
STRUCTURED_PROVIDER_VERSION = "1.0.0"
DINOV3_PROVIDER_ID = "DINOV3_FROZEN_FEATURES"
DINOV3_PROVIDER_STATE = "IMPLEMENTED_NOT_PROVISIONED"
RUNTIME_STORE = Path(__file__).resolve().parents[1] / "runtime" / "visual_learning_receipts"

LEARNING_ROLES = {"POSITIVE", "NEGATIVE", "AMBIGUOUS"}
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

PRIMITIVE_FAMILIES = (
    "TEXT_BLOCK",
    "LINEAR_STROKE_GROUP",
    "RECTILINEAR_CLOSED_SHAPE",
    "CURVED_OR_ARC_SHAPE",
    "FILLED_OR_HATCHED_REGION",
    "RASTER_IMAGE_REGION",
    "COMPLEX_VECTOR_GROUP",
    "UNKNOWN_GRAPHIC_GROUP",
)
ASPECT_BUCKETS = ("VERY_TALL", "TALL", "SQUAREISH", "WIDE", "VERY_WIDE")
AREA_BUCKETS = ("TINY", "SMALL", "MEDIUM", "LARGE")
COMPLEXITY_BUCKETS = ("ONE", "FEW", "MEDIUM", "MANY")
STROKE_BUCKETS = ("NA", "THIN", "MEDIUM", "THICK")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical(value).encode("utf-8"))


def _required_text(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"VISUAL_LEARNING_{name.upper()}_REQUIRED")
    return text


def _one_hot(value: str, vocabulary: tuple[str, ...], field: str) -> list[float]:
    if value not in vocabulary:
        raise ValueError(f"VISUAL_LEARNING_{field.upper()}_INVALID")
    return [1.0 if item == value else 0.0 for item in vocabulary]


def _normalize(vector: Iterable[float]) -> list[float]:
    values = [float(v) for v in vector]
    norm = math.sqrt(sum(v * v for v in values))
    if norm <= 0:
        raise ValueError("VISUAL_LEARNING_ZERO_VECTOR")
    return [round(v / norm, 12) for v in values]


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    a = [float(v) for v in left]
    b = [float(v) for v in right]
    if len(a) != len(b) or not a:
        raise ValueError("VISUAL_LEARNING_EMBEDDING_DIMENSION_MISMATCH")
    an = math.sqrt(sum(v * v for v in a))
    bn = math.sqrt(sum(v * v for v in b))
    if an <= 0 or bn <= 0:
        raise ValueError("VISUAL_LEARNING_ZERO_VECTOR")
    score = sum(x * y for x, y in zip(a, b)) / (an * bn)
    return max(-1.0, min(1.0, score))


def provider_status() -> dict[str, Any]:
    return {
        "structured_graphic": {
            "provider_id": STRUCTURED_PROVIDER_ID,
            "provider_version": STRUCTURED_PROVIDER_VERSION,
            "state": "READY",
            "is_foundation_model": False,
        },
        "visual_foundation": {
            "provider_id": DINOV3_PROVIDER_ID,
            "state": DINOV3_PROVIDER_STATE,
            "required_for_v1": False,
            "simulated": False,
        },
        "authority": dict(AUTHORITY),
    }


def structured_embedding_from_signature(
    feature_signature: dict[str, Any],
    *,
    input_fingerprint: str,
    source_version_id: str,
    page_index: int,
    candidate_id: str,
) -> dict[str, Any]:
    """Create the explainable v1 embedding used before a visual model is configured."""
    primitive_family = _required_text(feature_signature.get("primitive_family"), "primitive_family")
    aspect_bucket = _required_text(feature_signature.get("aspect_bucket"), "aspect_bucket")
    area_bucket = _required_text(feature_signature.get("area_bucket"), "area_bucket")
    complexity_bucket = _required_text(feature_signature.get("complexity_bucket"), "complexity_bucket")
    stroke_width_bucket = str(feature_signature.get("stroke_width_bucket") or "NA")
    filled = bool(feature_signature.get("filled", False))

    vector: list[float] = []
    vector.extend(_one_hot(primitive_family, PRIMITIVE_FAMILIES, "primitive_family"))
    vector.extend(_one_hot(aspect_bucket, ASPECT_BUCKETS, "aspect_bucket"))
    vector.extend(_one_hot(area_bucket, AREA_BUCKETS, "area_bucket"))
    vector.extend(_one_hot(complexity_bucket, COMPLEXITY_BUCKETS, "complexity_bucket"))
    vector.extend(_one_hot(stroke_width_bucket, STROKE_BUCKETS, "stroke_width_bucket"))
    vector.extend([1.0 if filled else 0.0, 0.0 if filled else 1.0])
    normalized = _normalize(vector)

    identity = {
        "provider_id": STRUCTURED_PROVIDER_ID,
        "provider_version": STRUCTURED_PROVIDER_VERSION,
        "input_fingerprint": _required_text(input_fingerprint, "input_fingerprint"),
        "vector": normalized,
    }
    return {
        "schema": EMBEDDING_SCHEMA,
        "embedding_id": "VEMB-" + _sha256_json(identity)[:20],
        "provider_id": STRUCTURED_PROVIDER_ID,
        "provider_version": STRUCTURED_PROVIDER_VERSION,
        "channel": "STRUCTURED_GRAPHIC",
        "dimension": len(normalized),
        "vector": normalized,
        "input_fingerprint": input_fingerprint,
        "embedding_fingerprint": "sha256:" + _sha256_json(identity),
        "source_version_id": _required_text(source_version_id, "source_version_id"),
        "page_index": int(page_index),
        "candidate_id": _required_text(candidate_id, "candidate_id"),
        "semantic_authority": "NONE",
    }


def structured_embedding_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    signature = candidate.get("feature_signature")
    if not isinstance(signature, dict):
        raise ValueError("VISUAL_LEARNING_FEATURE_SIGNATURE_REQUIRED")
    candidate_id = _required_text(candidate.get("candidate_id"), "candidate_id")
    source_version_id = _required_text(candidate.get("source_version_id"), "source_version_id")
    page_index = int(candidate.get("page_index"))
    input_fingerprint = "sha256:" + _sha256_json(
        {
            "candidate_id": candidate_id,
            "source_version_id": source_version_id,
            "page_index": page_index,
            "bbox": candidate.get("bbox"),
            "feature_signature": signature,
        }
    )
    return structured_embedding_from_signature(
        signature,
        input_fingerprint=input_fingerprint,
        source_version_id=source_version_id,
        page_index=page_index,
        candidate_id=candidate_id,
    )


def validate_embedding(embedding: dict[str, Any]) -> None:
    if embedding.get("schema") != EMBEDDING_SCHEMA:
        raise ValueError("VISUAL_LEARNING_EMBEDDING_SCHEMA_INVALID")
    _required_text(embedding.get("embedding_id"), "embedding_id")
    _required_text(embedding.get("provider_id"), "provider_id")
    _required_text(embedding.get("provider_version"), "provider_version")
    _required_text(embedding.get("input_fingerprint"), "input_fingerprint")
    expected_fingerprint = str(embedding.get("embedding_fingerprint") or "")
    vector = embedding.get("vector")
    if not isinstance(vector, list) or not vector:
        raise ValueError("VISUAL_LEARNING_EMBEDDING_VECTOR_REQUIRED")
    if int(embedding.get("dimension", -1)) != len(vector):
        raise ValueError("VISUAL_LEARNING_EMBEDDING_DIMENSION_INVALID")
    identity = {
        "provider_id": embedding["provider_id"],
        "provider_version": embedding["provider_version"],
        "input_fingerprint": embedding["input_fingerprint"],
        "vector": [float(v) for v in vector],
    }
    if expected_fingerprint != "sha256:" + _sha256_json(identity):
        raise ValueError("VISUAL_LEARNING_EMBEDDING_FINGERPRINT_MISMATCH")


def new_memory(*, project_id: str, concept_id: str, meaning: str) -> dict[str, Any]:
    return {
        "schema": MEMORY_SCHEMA,
        "project_id": _required_text(project_id, "project_id"),
        "concept_id": _required_text(concept_id, "concept_id"),
        "meaning": _required_text(meaning, "meaning"),
        "scope": "PROJECT_LOCAL",
        "examples": [],
        "applied_receipt_ids": [],
        "centroids": {},
        "example_counts": {"POSITIVE": 0, "NEGATIVE": 0, "AMBIGUOUS": 0},
        "provider_states": provider_status(),
        "memory_fingerprint": None,
        "authority": dict(AUTHORITY),
    }


def _memory_fingerprint(memory: dict[str, Any]) -> str:
    payload = {
        "project_id": memory["project_id"],
        "concept_id": memory["concept_id"],
        "meaning": memory["meaning"],
        "examples": memory["examples"],
        "applied_receipt_ids": memory["applied_receipt_ids"],
        "centroids": memory["centroids"],
    }
    return "sha256:" + _sha256_json(payload)


def build_learning_receipt(
    *,
    decision_id: str,
    project_id: str,
    concept_id: str,
    meaning: str,
    reviewer: str,
    role: str,
    candidate_id: str,
    source_version_id: str,
    page_id: str,
    evidence_fingerprint: str,
    embedding: dict[str, Any],
    rationale: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    role = _required_text(role, "role").upper()
    if role not in LEARNING_ROLES:
        raise ValueError("VISUAL_LEARNING_ROLE_INVALID")
    validate_embedding(embedding)
    if embedding["candidate_id"] != candidate_id:
        raise ValueError("VISUAL_LEARNING_CANDIDATE_EMBEDDING_MISMATCH")
    if embedding["source_version_id"] != source_version_id:
        raise ValueError("VISUAL_LEARNING_SOURCE_EMBEDDING_MISMATCH")
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    receipt = {
        "receipt_type": RECEIPT_SCHEMA,
        "schema": RECEIPT_SCHEMA,
        "decision_id": _required_text(decision_id, "decision_id"),
        "task_id": _required_text(concept_id, "concept_id"),
        "residual_id": _required_text(candidate_id, "candidate_id"),
        "project_id": _required_text(project_id, "project_id"),
        "concept_id": concept_id,
        "meaning": _required_text(meaning, "meaning"),
        "reviewer": _required_text(reviewer, "reviewer"),
        "role": role,
        "rationale": _required_text(rationale, "rationale"),
        "timestamp": timestamp,
        "candidate_id": candidate_id,
        "source_version_id": source_version_id,
        "page_id": _required_text(page_id, "page_id"),
        "page_index": int(embedding["page_index"]),
        "evidence_fingerprint": _required_text(evidence_fingerprint, "evidence_fingerprint"),
        "embedding": deepcopy(embedding),
        "embedding_fingerprint": embedding["embedding_fingerprint"],
        "provider_id": embedding["provider_id"],
        "provider_version": embedding["provider_version"],
        "learning_effect": "DERIVED_PROTOTYPE_MEMORY_ONLY",
        "authority": dict(AUTHORITY),
    }
    receipt["receipt_fingerprint"] = "sha256:" + _sha256_json(
        {key: value for key, value in receipt.items() if key != "receipt_fingerprint"}
    )
    return receipt


def _validate_learning_receipt(receipt: dict[str, Any], memory: dict[str, Any]) -> None:
    if receipt.get("receipt_type") != RECEIPT_SCHEMA or receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("VISUAL_LEARNING_RECEIPT_SCHEMA_INVALID")
    if receipt.get("project_id") != memory.get("project_id"):
        raise ValueError("VISUAL_LEARNING_PROJECT_MISMATCH")
    if receipt.get("concept_id") != memory.get("concept_id"):
        raise ValueError("VISUAL_LEARNING_CONCEPT_MISMATCH")
    if receipt.get("meaning") != memory.get("meaning"):
        raise ValueError("VISUAL_LEARNING_MEANING_MISMATCH")
    if str(receipt.get("role") or "") not in LEARNING_ROLES:
        raise ValueError("VISUAL_LEARNING_ROLE_INVALID")
    decision_id = _required_text(receipt.get("decision_id"), "decision_id")
    if decision_id in set(memory.get("applied_receipt_ids") or []):
        raise ValueError("VISUAL_LEARNING_DUPLICATE_DECISION_ID")
    embedding = receipt.get("embedding")
    if not isinstance(embedding, dict):
        raise ValueError("VISUAL_LEARNING_EMBEDDING_REQUIRED")
    validate_embedding(embedding)
    if receipt.get("embedding_fingerprint") != embedding.get("embedding_fingerprint"):
        raise ValueError("VISUAL_LEARNING_STALE_EMBEDDING_FINGERPRINT")
    expected = str(receipt.get("receipt_fingerprint") or "")
    actual = "sha256:" + _sha256_json(
        {key: value for key, value in receipt.items() if key != "receipt_fingerprint"}
    )
    if expected != actual:
        raise ValueError("VISUAL_LEARNING_RECEIPT_FINGERPRINT_MISMATCH")
    authority = receipt.get("authority") or {}
    if authority.get("canonical_write_authorized") is not False:
        raise ValueError("VISUAL_LEARNING_AUTHORITY_DRIFT")
    if authority.get("structural_identity_authorized") is not False:
        raise ValueError("VISUAL_LEARNING_AUTHORITY_DRIFT")
    if authority.get("project_semantic_authority") != "NONE":
        raise ValueError("VISUAL_LEARNING_AUTHORITY_DRIFT")


def _mean_vector(vectors: list[list[float]]) -> list[float] | None:
    if not vectors:
        return None
    dimensions = {len(v) for v in vectors}
    if len(dimensions) != 1:
        raise ValueError("VISUAL_LEARNING_EMBEDDING_DIMENSION_MISMATCH")
    width = dimensions.pop()
    raw = [sum(float(v[i]) for v in vectors) / len(vectors) for i in range(width)]
    return _normalize(raw)


def _recompute_memory(memory: dict[str, Any]) -> None:
    counts = {role: 0 for role in LEARNING_ROLES}
    grouped: dict[str, dict[str, list[list[float]]]] = {}
    for example in memory["examples"]:
        role = example["role"]
        counts[role] += 1
        if role == "AMBIGUOUS":
            continue
        provider = example["provider_id"]
        grouped.setdefault(provider, {"POSITIVE": [], "NEGATIVE": []})[role].append(example["vector"])

    centroids: dict[str, Any] = {}
    for provider, roles in sorted(grouped.items()):
        positive = _mean_vector(roles["POSITIVE"])
        negative = _mean_vector(roles["NEGATIVE"])
        centroids[provider] = {
            "positive": positive,
            "negative": negative,
            "positive_count": len(roles["POSITIVE"]),
            "negative_count": len(roles["NEGATIVE"]),
        }
    memory["centroids"] = centroids
    memory["example_counts"] = counts
    memory["memory_fingerprint"] = _memory_fingerprint(memory)


def apply_learning_receipt(memory: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    if memory.get("schema") != MEMORY_SCHEMA:
        raise ValueError("VISUAL_LEARNING_MEMORY_SCHEMA_INVALID")
    _validate_learning_receipt(receipt, memory)
    next_memory = deepcopy(memory)
    embedding = receipt["embedding"]
    next_memory["examples"].append(
        {
            "decision_id": receipt["decision_id"],
            "role": receipt["role"],
            "candidate_id": receipt["candidate_id"],
            "source_version_id": receipt["source_version_id"],
            "page_id": receipt["page_id"],
            "page_index": receipt["page_index"],
            "evidence_fingerprint": receipt["evidence_fingerprint"],
            "provider_id": embedding["provider_id"],
            "provider_version": embedding["provider_version"],
            "embedding_id": embedding["embedding_id"],
            "embedding_fingerprint": embedding["embedding_fingerprint"],
            "vector": list(embedding["vector"]),
            "reviewer": receipt["reviewer"],
            "rationale": receipt["rationale"],
            "timestamp": receipt["timestamp"],
        }
    )
    next_memory["applied_receipt_ids"].append(receipt["decision_id"])
    _recompute_memory(next_memory)
    return next_memory


def replay_memory(
    *, project_id: str, concept_id: str, meaning: str, receipts: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    memory = new_memory(project_id=project_id, concept_id=concept_id, meaning=meaning)
    ordered = sorted(receipts, key=lambda r: (str(r.get("timestamp") or ""), str(r.get("decision_id") or "")))
    for receipt in ordered:
        memory = apply_learning_receipt(memory, receipt)
    return memory


def persist_learning_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    """Persist the immutable receipt; memory snapshots remain derived/replayable."""
    return audit_store.persist_runtime_receipt(receipt, RUNTIME_STORE)


def load_learning_receipts() -> dict[str, Any]:
    return audit_store.load_runtime_receipts(RECEIPT_SCHEMA, RUNTIME_STORE)


def _score_embedding(memory: dict[str, Any], embedding: dict[str, Any]) -> dict[str, Any]:
    validate_embedding(embedding)
    provider = embedding["provider_id"]
    centroid = (memory.get("centroids") or {}).get(provider)
    if not centroid or centroid.get("positive") is None:
        return {
            "provider_id": provider,
            "state": "NO_POSITIVE_PROTOTYPE_FOR_PROVIDER",
            "positive_similarity": None,
            "negative_similarity": None,
            "score": None,
        }
    positive_similarity = cosine_similarity(embedding["vector"], centroid["positive"])
    negative_similarity = None
    penalty = 0.0
    if centroid.get("negative") is not None:
        negative_similarity = cosine_similarity(embedding["vector"], centroid["negative"])
        penalty = max(0.0, negative_similarity) * 0.35
    score = max(-1.0, min(1.0, positive_similarity - penalty))
    return {
        "provider_id": provider,
        "state": "SIMILARITY_AVAILABLE",
        "positive_similarity": round(positive_similarity, 6),
        "negative_similarity": None if negative_similarity is None else round(negative_similarity, 6),
        "negative_penalty": round(penalty, 6),
        "score": round(score, 6),
        "positive_count": centroid["positive_count"],
        "negative_count": centroid["negative_count"],
    }


def rank_embeddings(
    memory: dict[str, Any], candidate_embeddings: Iterable[dict[str, Any]], *, limit: int = 50
) -> dict[str, Any]:
    if memory.get("schema") != MEMORY_SCHEMA:
        raise ValueError("VISUAL_LEARNING_MEMORY_SCHEMA_INVALID")
    results: list[dict[str, Any]] = []
    for embedding in candidate_embeddings:
        component = _score_embedding(memory, embedding)
        if component["score"] is None:
            continue
        results.append(
            {
                "candidate_id": embedding["candidate_id"],
                "source_version_id": embedding["source_version_id"],
                "page_index": embedding["page_index"],
                "embedding_id": embedding["embedding_id"],
                "component_scores": [component],
                "fused_score": component["score"],
                "proposal_state": "SIMILARITY_PROPOSAL",
                "semantic_assignment": None,
                "human_project_validation_required": True,
                "authority": dict(AUTHORITY),
            }
        )
    results.sort(key=lambda row: (-float(row["fused_score"]), row["candidate_id"]))
    return {
        "schema": "CEW_PROTOTYPE_SIMILARITY_RESULT_v1",
        "project_id": memory["project_id"],
        "concept_id": memory["concept_id"],
        "meaning": memory["meaning"],
        "memory_fingerprint": memory.get("memory_fingerprint"),
        "provider_states": memory.get("provider_states"),
        "candidate_count": min(len(results), max(1, int(limit))),
        "candidates": results[: max(1, int(limit))],
        "automatic_classification": False,
        "authority": dict(AUTHORITY),
    }


def rank_preacquisition_candidates(
    memory: dict[str, Any], primitive_candidates: Iterable[dict[str, Any]], *, limit: int = 50
) -> dict[str, Any]:
    embeddings = [structured_embedding_from_candidate(candidate) for candidate in primitive_candidates]
    return rank_embeddings(memory, embeddings, limit=limit)
