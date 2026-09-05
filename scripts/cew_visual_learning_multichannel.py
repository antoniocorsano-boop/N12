#!/usr/bin/env python3
"""Multi-channel similarity fusion for CEW prototype learning.

The module consumes the existing project-local PrototypeMemory and one or more
VisualEmbedding objects per candidate. Provider component scores remain visible.
Fusion is a normalized weighted mean over the available scored channels and is a
review aid only; it never assigns semantic meaning automatically.
"""
from __future__ import annotations

import math
from typing import Any, Iterable

import cew_visual_learning as learning

FUSION_SCHEMA = "CEW_MULTICHANNEL_SIMILARITY_RESULT_v1"
FUSION_POLICY = "NORMALIZED_WEIGHTED_MEAN_AVAILABLE_CHANNELS"
DEFAULT_PROVIDER_WEIGHTS = {
    learning.STRUCTURED_PROVIDER_ID: 1.0,
    learning.DINOV3_PROVIDER_ID: 1.0,
}


def _provider_weight(provider_id: str, weights: dict[str, float]) -> float:
    value = float(weights.get(provider_id, 1.0))
    if not math.isfinite(value) or value <= 0:
        raise ValueError("VISUAL_FUSION_PROVIDER_WEIGHT_INVALID")
    return value


def _score(memory: dict[str, Any], embedding: dict[str, Any]) -> dict[str, Any] | None:
    learning.validate_embedding(embedding)
    provider_id = str(embedding["provider_id"])
    centroid = (memory.get("centroids") or {}).get(provider_id)
    if not centroid or centroid.get("positive") is None:
        return None
    positive_similarity = learning.cosine_similarity(embedding["vector"], centroid["positive"])
    negative_similarity = None
    penalty = 0.0
    if centroid.get("negative") is not None:
        negative_similarity = learning.cosine_similarity(embedding["vector"], centroid["negative"])
        penalty = max(0.0, negative_similarity) * 0.35
    score = max(-1.0, min(1.0, positive_similarity - penalty))
    return {
        "provider_id": provider_id,
        "provider_version": embedding["provider_version"],
        "embedding_id": embedding["embedding_id"],
        "positive_similarity": round(positive_similarity, 6),
        "negative_similarity": None if negative_similarity is None else round(negative_similarity, 6),
        "negative_penalty": round(penalty, 6),
        "score": round(score, 6),
        "positive_count": int(centroid.get("positive_count", 0)),
        "negative_count": int(centroid.get("negative_count", 0)),
    }


def rank_multichannel_candidates(
    memory: dict[str, Any],
    embeddings: Iterable[dict[str, Any]],
    *,
    provider_weights: dict[str, float] | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    if memory.get("schema") != learning.MEMORY_SCHEMA:
        raise ValueError("VISUAL_FUSION_MEMORY_SCHEMA_INVALID")
    weights = dict(DEFAULT_PROVIDER_WEIGHTS)
    if provider_weights:
        weights.update({str(key): float(value) for key, value in provider_weights.items()})

    grouped: dict[str, list[dict[str, Any]]] = {}
    for embedding in embeddings:
        learning.validate_embedding(embedding)
        candidate_id = str(embedding.get("candidate_id") or "").strip()
        if not candidate_id:
            raise ValueError("VISUAL_FUSION_CANDIDATE_ID_REQUIRED")
        grouped.setdefault(candidate_id, []).append(embedding)

    results: list[dict[str, Any]] = []
    for candidate_id, rows in grouped.items():
        providers_seen: set[str] = set()
        source_versions = {str(row.get("source_version_id") or "") for row in rows}
        page_indices = {int(row.get("page_index")) for row in rows}
        if len(source_versions) != 1 or len(page_indices) != 1:
            raise ValueError("VISUAL_FUSION_CANDIDATE_BINDING_MISMATCH")

        components: list[dict[str, Any]] = []
        weighted_total = 0.0
        weight_total = 0.0
        for row in rows:
            provider_id = str(row["provider_id"])
            if provider_id in providers_seen:
                raise ValueError("VISUAL_FUSION_DUPLICATE_PROVIDER_FOR_CANDIDATE")
            providers_seen.add(provider_id)
            component = _score(memory, row)
            if component is None:
                continue
            weight = _provider_weight(provider_id, weights)
            component["configured_weight"] = weight
            components.append(component)
            weighted_total += weight * float(component["score"])
            weight_total += weight

        if not components:
            continue
        for component in components:
            component["effective_weight"] = round(float(component["configured_weight"]) / weight_total, 6)
        fused_score = weighted_total / weight_total
        results.append(
            {
                "candidate_id": candidate_id,
                "source_version_id": next(iter(source_versions)),
                "page_index": next(iter(page_indices)),
                "component_scores": sorted(components, key=lambda row: row["provider_id"]),
                "available_channel_count": len(components),
                "fused_score": round(max(-1.0, min(1.0, fused_score)), 6),
                "proposal_state": "SIMILARITY_PROPOSAL",
                "semantic_assignment": None,
                "human_project_validation_required": True,
                "authority": dict(learning.AUTHORITY),
            }
        )

    results.sort(key=lambda row: (-float(row["fused_score"]), row["candidate_id"]))
    requested_limit = max(1, int(limit))
    selected = results[:requested_limit]
    return {
        "schema": FUSION_SCHEMA,
        "project_id": memory["project_id"],
        "concept_id": memory["concept_id"],
        "meaning": memory["meaning"],
        "memory_fingerprint": memory.get("memory_fingerprint"),
        "fusion_policy": FUSION_POLICY,
        "provider_weights": weights,
        "candidate_count": len(selected),
        "candidates": selected,
        "automatic_classification": False,
        "semantic_assignment": None,
        "authority": dict(learning.AUTHORITY),
    }
