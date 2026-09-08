#!/usr/bin/env python3
from __future__ import annotations

from hashlib import sha256
import json

import cew_visual_learning as learning
import cew_visual_learning_multichannel as fusion


def synthetic_embedding(
    *, candidate_id: str, provider_id: str, provider_version: str, vector: list[float], source: str = "SRC-001"
) -> dict:
    input_fingerprint = "sha256:" + sha256(
        json.dumps(
            {"candidate_id": candidate_id, "provider_id": provider_id, "vector": vector},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    identity = {
        "provider_id": provider_id,
        "provider_version": provider_version,
        "input_fingerprint": input_fingerprint,
        "vector": vector,
    }
    fingerprint = "sha256:" + sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema": learning.EMBEDDING_SCHEMA,
        "embedding_id": f"VEMB-{provider_id}-{candidate_id}",
        "provider_id": provider_id,
        "provider_version": provider_version,
        "channel": "VISUAL_FOUNDATION" if provider_id == learning.DINOV3_PROVIDER_ID else "STRUCTURED_GRAPHIC",
        "dimension": len(vector),
        "vector": vector,
        "input_fingerprint": input_fingerprint,
        "embedding_fingerprint": fingerprint,
        "source_version_id": source,
        "page_index": 0,
        "candidate_id": candidate_id,
        "semantic_authority": "NONE",
    }


def receipt(memory: dict, decision_id: str, role: str, embedding: dict) -> dict:
    return learning.build_learning_receipt(
        decision_id=decision_id,
        project_id=memory["project_id"],
        concept_id=memory["concept_id"],
        meaning=memory["meaning"],
        reviewer="HUMAN-REVIEWER",
        role=role,
        candidate_id=embedding["candidate_id"],
        source_version_id=embedding["source_version_id"],
        page_id="PAGE-001",
        evidence_fingerprint="sha256:" + "a" * 64,
        embedding=embedding,
        rationale=f"human {role.lower()} example",
        timestamp=f"2026-09-03T11:{len(decision_id):02d}:00+00:00",
    )


def main() -> None:
    memory = learning.new_memory(
        project_id="PROJECT-MULTI-001",
        concept_id="CONCEPT-COLUMNLIKE",
        meaning="HUMAN_TAUGHT_PROJECT_CONCEPT",
    )

    structured_positive = synthetic_embedding(
        candidate_id="TRAIN-S-POS",
        provider_id=learning.STRUCTURED_PROVIDER_ID,
        provider_version=learning.STRUCTURED_PROVIDER_VERSION,
        vector=[1.0, 0.0, 0.0],
    )
    dino_positive = synthetic_embedding(
        candidate_id="TRAIN-D-POS",
        provider_id=learning.DINOV3_PROVIDER_ID,
        provider_version="dinov3_vits16@test",
        vector=[1.0, 0.0, 0.0],
    )
    dino_negative = synthetic_embedding(
        candidate_id="TRAIN-D-NEG",
        provider_id=learning.DINOV3_PROVIDER_ID,
        provider_version="dinov3_vits16@test",
        vector=[0.0, 1.0, 0.0],
    )
    for row in (
        receipt(memory, "multi-structured-positive", "POSITIVE", structured_positive),
        receipt(memory, "multi-dino-positive", "POSITIVE", dino_positive),
        receipt(memory, "multi-dino-negative", "NEGATIVE", dino_negative),
    ):
        memory = learning.apply_learning_receipt(memory, row)

    good_structured = synthetic_embedding(
        candidate_id="GOOD",
        provider_id=learning.STRUCTURED_PROVIDER_ID,
        provider_version=learning.STRUCTURED_PROVIDER_VERSION,
        vector=[0.99, 0.05, 0.0],
    )
    good_dino = synthetic_embedding(
        candidate_id="GOOD",
        provider_id=learning.DINOV3_PROVIDER_ID,
        provider_version="dinov3_vits16@test",
        vector=[0.98, 0.05, 0.0],
    )
    deceptive_structured = synthetic_embedding(
        candidate_id="DECEPTIVE",
        provider_id=learning.STRUCTURED_PROVIDER_ID,
        provider_version=learning.STRUCTURED_PROVIDER_VERSION,
        vector=[1.0, 0.0, 0.0],
    )
    deceptive_dino = synthetic_embedding(
        candidate_id="DECEPTIVE",
        provider_id=learning.DINOV3_PROVIDER_ID,
        provider_version="dinov3_vits16@test",
        vector=[0.05, 0.99, 0.0],
    )
    structured_only = synthetic_embedding(
        candidate_id="STRUCTURED-ONLY",
        provider_id=learning.STRUCTURED_PROVIDER_ID,
        provider_version=learning.STRUCTURED_PROVIDER_VERSION,
        vector=[0.8, 0.2, 0.0],
    )

    ranked = fusion.rank_multichannel_candidates(
        memory,
        [deceptive_structured, deceptive_dino, structured_only, good_dino, good_structured],
        provider_weights={learning.STRUCTURED_PROVIDER_ID: 1.0, learning.DINOV3_PROVIDER_ID: 1.0},
    )
    ids = [row["candidate_id"] for row in ranked["candidates"]]
    assert ids[0] == "GOOD"
    assert ids.index("DECEPTIVE") > ids.index("GOOD")
    assert "STRUCTURED-ONLY" in ids

    good = next(row for row in ranked["candidates"] if row["candidate_id"] == "GOOD")
    deceptive = next(row for row in ranked["candidates"] if row["candidate_id"] == "DECEPTIVE")
    structured = next(row for row in ranked["candidates"] if row["candidate_id"] == "STRUCTURED-ONLY")
    assert good["available_channel_count"] == 2
    assert len(good["component_scores"]) == 2
    assert deceptive["fused_score"] < good["fused_score"]
    dino_component = next(c for c in deceptive["component_scores"] if c["provider_id"] == learning.DINOV3_PROVIDER_ID)
    assert dino_component["negative_penalty"] > 0
    assert structured["available_channel_count"] == 1
    assert ranked["automatic_classification"] is False
    assert ranked["semantic_assignment"] is None
    assert ranked["authority"]["project_semantic_authority"] == "NONE"
    assert ranked["authority"]["canonical_write_authorized"] is False

    try:
        fusion.rank_multichannel_candidates(memory, [good_structured, good_structured])
        raise AssertionError("duplicate provider must fail")
    except ValueError as exc:
        assert "DUPLICATE_PROVIDER" in str(exc)

    print("CEW_VISUAL_LEARNING_MULTICHANNEL_PASS")
    print("structured_plus_dinov3_fusion=PASS")
    print("visual_counterexample_penalty_visible=PASS")
    print("structured_only_fallback=PASS")
    print("automatic_classification=false project_semantic_authority=NONE")


if __name__ == "__main__":
    main()
