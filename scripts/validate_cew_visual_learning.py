#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tempfile

import cew_runtime_audit_store as audit_store
import cew_visual_learning as learning


def candidate(candidate_id: str, family: str, aspect: str, area: str, complexity: str, filled: bool, stroke: str):
    return {
        "candidate_id": candidate_id,
        "source_version_id": "SRC-NEW-001",
        "page_index": 0,
        "bbox": {"x": 0.1, "y": 0.1, "w": 0.05, "h": 0.05},
        "feature_signature": {
            "primitive_family": family,
            "aspect_bucket": aspect,
            "area_bucket": area,
            "complexity_bucket": complexity,
            "filled": filled,
            "stroke_width_bucket": stroke,
        },
    }


def receipt(decision_id: str, role: str, item: dict, meaning: str = "PROJECT_CONCEPT_A"):
    emb = learning.structured_embedding_from_candidate(item)
    return learning.build_learning_receipt(
        decision_id=decision_id,
        project_id="PROJECT-NEW-001",
        concept_id="CONCEPT-A",
        meaning=meaning,
        reviewer="HUMAN-REVIEWER",
        role=role,
        candidate_id=item["candidate_id"],
        source_version_id=item["source_version_id"],
        page_id="PAGE-001",
        evidence_fingerprint=f"sha256:evidence-{item['candidate_id']}",
        embedding=emb,
        rationale=f"human {role.lower()} example",
        timestamp=f"2026-09-03T10:0{len(decision_id)}:00+00:00",
    )


def main() -> None:
    contract = learning.provider_status()
    assert contract["structured_graphic"]["state"] == "READY"
    assert contract["structured_graphic"]["is_foundation_model"] is False
    assert contract["visual_foundation"]["provider_id"] == "DINOV3_FROZEN_FEATURES"
    assert contract["visual_foundation"]["state"] == "DINOV3_PROVIDER_NOT_CONFIGURED"
    assert contract["visual_foundation"]["simulated"] is False

    p1 = candidate("P1", "RECTILINEAR_CLOSED_SHAPE", "SQUAREISH", "SMALL", "FEW", False, "MEDIUM")
    p2 = candidate("P2", "RECTILINEAR_CLOSED_SHAPE", "SQUAREISH", "SMALL", "FEW", False, "THIN")
    n1 = candidate("N1", "RECTILINEAR_CLOSED_SHAPE", "VERY_WIDE", "SMALL", "FEW", False, "MEDIUM")
    a1 = candidate("A1", "RECTILINEAR_CLOSED_SHAPE", "WIDE", "MEDIUM", "MEDIUM", False, "THIN")
    good = candidate("GOOD", "RECTILINEAR_CLOSED_SHAPE", "SQUAREISH", "SMALL", "FEW", False, "MEDIUM")
    bad = candidate("BAD", "RECTILINEAR_CLOSED_SHAPE", "VERY_WIDE", "SMALL", "FEW", False, "MEDIUM")

    memory = learning.new_memory(project_id="PROJECT-NEW-001", concept_id="CONCEPT-A", meaning="PROJECT_CONCEPT_A")
    r1 = receipt("learn-positive-1", "POSITIVE", p1)
    r2 = receipt("learn-positive-2", "POSITIVE", p2)
    rn = receipt("learn-negative-1", "NEGATIVE", n1)
    ra = receipt("learn-ambiguous-1", "AMBIGUOUS", a1)

    for row in (r1, r2, rn, ra):
        memory = learning.apply_learning_receipt(memory, row)

    assert memory["example_counts"] == {"POSITIVE": 2, "NEGATIVE": 1, "AMBIGUOUS": 1}
    provider = memory["centroids"][learning.STRUCTURED_PROVIDER_ID]
    assert provider["positive_count"] == 2
    assert provider["negative_count"] == 1
    assert provider["positive"] is not None
    assert provider["negative"] is not None

    ranked = learning.rank_preacquisition_candidates(memory, [bad, good], limit=10)
    assert ranked["automatic_classification"] is False
    assert ranked["authority"]["canonical_write_authorized"] is False
    assert ranked["authority"]["project_semantic_authority"] == "NONE"
    assert [row["candidate_id"] for row in ranked["candidates"]] == ["GOOD", "BAD"]
    good_score = ranked["candidates"][0]["fused_score"]
    bad_score = ranked["candidates"][1]["fused_score"]
    assert good_score > bad_score
    bad_component = ranked["candidates"][1]["component_scores"][0]
    assert bad_component["negative_similarity"] is not None
    assert bad_component["negative_penalty"] > 0

    replayed = learning.replay_memory(
        project_id="PROJECT-NEW-001",
        concept_id="CONCEPT-A",
        meaning="PROJECT_CONCEPT_A",
        receipts=[ra, rn, r2, r1],
    )
    assert replayed["memory_fingerprint"] == memory["memory_fingerprint"]
    assert replayed["centroids"] == memory["centroids"]

    try:
        learning.apply_learning_receipt(memory, r1)
        raise AssertionError("duplicate receipt should fail")
    except ValueError as exc:
        assert "DUPLICATE_DECISION_ID" in str(exc)

    stale = dict(r1)
    stale["embedding_fingerprint"] = "sha256:stale"
    stale["decision_id"] = "learn-stale-1"
    stale["receipt_fingerprint"] = "sha256:invalid"
    try:
        learning.apply_learning_receipt(learning.new_memory(project_id="PROJECT-NEW-001", concept_id="CONCEPT-A", meaning="PROJECT_CONCEPT_A"), stale)
        raise AssertionError("stale embedding should fail")
    except ValueError as exc:
        assert "STALE_EMBEDDING_FINGERPRINT" in str(exc) or "RECEIPT_FINGERPRINT_MISMATCH" in str(exc)

    original_store = learning.RUNTIME_STORE
    original_backend = audit_store.backend_status
    with tempfile.TemporaryDirectory(prefix="cew-learning-") as tmp:
        learning.RUNTIME_STORE = Path(tmp)
        audit_store.backend_status = lambda: "FILESYSTEM_APPEND_ONLY"
        try:
            stored = learning.persist_learning_receipt(r1)
            assert stored["canonical_write"] is False
            loaded = learning.load_learning_receipts()
            assert loaded["receipt_count"] == 1
            assert loaded["receipts"][0]["decision_id"] == r1["decision_id"]
            try:
                learning.persist_learning_receipt(r1)
                raise AssertionError("append-only duplicate should fail")
            except ValueError as exc:
                assert "duplicate decision_id" in str(exc)
        finally:
            learning.RUNTIME_STORE = original_store
            audit_store.backend_status = original_backend

    print("CEW_VISUAL_LEARNING_PASS")
    print("structured_embedding=PASS")
    print("positive_negative_ambiguous_memory=PASS")
    print("counterexample_penalty=PASS")
    print("receipt_replay=DETERMINISTIC")
    print("append_only_learning_receipt=PASS")
    print("dinov3_provider_state=DINOV3_PROVIDER_NOT_CONFIGURED")
    print("project_semantic_authority=NONE canonical_write_authorized=false")


if __name__ == "__main__":
    main()
