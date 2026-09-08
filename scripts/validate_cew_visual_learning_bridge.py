#!/usr/bin/env python3
from __future__ import annotations

import cew_visual_learning as learning
import cew_visual_learning_bridge as bridge


def cand(cid: str, aspect: str):
    return {
        "candidate_id": cid,
        "source_version_id": "SRC-UNKNOWN-001",
        "source_sha256": "0" * 64,
        "page_index": 0,
        "coordinate_system": "NORMALIZED_0_1",
        "bbox": {"x": 0.1, "y": 0.1, "w": 0.02, "h": 0.02},
        "primitive_family": "RECTILINEAR_CLOSED_SHAPE",
        "feature_signature": {
            "primitive_family": "RECTILINEAR_CLOSED_SHAPE",
            "aspect_bucket": aspect,
            "area_bucket": "SMALL",
            "complexity_bucket": "FEW",
            "filled": False,
            "stroke_width_bucket": "MEDIUM",
        },
        "semantic_meaning": None,
        "semantic_authority": "NONE",
    }


def report():
    a = cand("GPC-A", "SQUAREISH")
    b = cand("GPC-B", "VERY_WIDE")
    return {
        "schema": bridge.PREACQUISITION_SCHEMA,
        "mode": "NEW_PROJECT_ZERO_SEMANTIC_PRIOR",
        "source_version_id": "SRC-UNKNOWN-001",
        "source_sha256": "0" * 64,
        "report_fingerprint": "sha256:" + "1" * 64,
        "primitive_candidates": [a, b],
        "graphic_clusters": [
            {"cluster_id": "GC-A", "member_candidate_ids": ["GPC-A"]},
            {"cluster_id": "GC-B", "member_candidate_ids": ["GPC-B"]},
        ],
        "human_triage_queue": [
            {"cluster_id": "GC-A", "semantic_authority_before_action": "NONE"},
            {"cluster_id": "GC-B", "semantic_authority_before_action": "NONE"},
        ],
        "semantic_labels_assigned_automatically": False,
        "authority": {
            "semantic_authority": "NONE_UNTIL_PROJECT_HUMAN_VALIDATION",
            "canonical_write_authorized": False,
            "structural_identity_authorized": False,
            "engineering_authority_effect": "NONE",
        },
    }


def main() -> None:
    source = report()
    taught = bridge.build_learning_receipt_from_candidate(
        source,
        candidate_id="GPC-A",
        project_id="PROJECT-X",
        concept_id="CONCEPT-COLUMN-LIKE",
        meaning="COLUMN_LIKE_GRAPHIC_FAMILY",
        reviewer="HUMAN",
        role="POSITIVE",
        page_id="PAGE-001",
        rationale="human teaches one example",
        decision_id="learning-bridge-positive-1",
        timestamp="2026-09-03T11:00:00+00:00",
    )
    negative = bridge.build_learning_receipt_from_candidate(
        source,
        candidate_id="GPC-B",
        project_id="PROJECT-X",
        concept_id="CONCEPT-COLUMN-LIKE",
        meaning="COLUMN_LIKE_GRAPHIC_FAMILY",
        reviewer="HUMAN",
        role="NEGATIVE",
        page_id="PAGE-001",
        rationale="human rejects a false positive",
        decision_id="learning-bridge-negative-1",
        timestamp="2026-09-03T11:01:00+00:00",
    )

    memory = learning.new_memory(
        project_id="PROJECT-X",
        concept_id="CONCEPT-COLUMN-LIKE",
        meaning="COLUMN_LIKE_GRAPHIC_FAMILY",
    )
    memory = learning.apply_learning_receipt(memory, taught)
    memory = learning.apply_learning_receipt(memory, negative)

    overlay = bridge.build_learning_overlay(source, project_id="PROJECT-X", memories=[memory])
    assert overlay["schema"] == bridge.OVERLAY_SCHEMA
    assert overlay["automatic_semantic_assignment"] is False
    assert overlay["authority"]["project_semantic_authority"] == "NONE"
    assert overlay["authority"]["canonical_write_authorized"] is False
    rows = {row["cluster_id"]: row for row in overlay["triage_overlay"]}
    suggestion = rows["GC-A"]["learned_prototype_suggestions"][0]
    assert suggestion["concept_id"] == "CONCEPT-COLUMN-LIKE"
    assert suggestion["semantic_assignment"] is None
    assert suggestion["human_project_validation_required"] is True
    assert rows["GC-A"]["semantic_authority_before_human_action"] == "NONE"
    assert set(rows["GC-A"]["allowed_learning_actions"]) == {
        "TEACH_THIS_IS", "CONFIRM_POSITIVE", "MARK_NEGATIVE", "MARK_AMBIGUOUS"
    }

    bad_memory = dict(memory)
    bad_memory["project_id"] = "OTHER-PROJECT"
    try:
        bridge.build_learning_overlay(source, project_id="PROJECT-X", memories=[bad_memory])
        raise AssertionError("cross-project memory should fail")
    except ValueError as exc:
        assert "PROJECT_MISMATCH" in str(exc)

    external = dict(memory)
    external["scope"] = "EXTERNAL_REFERENCE"
    try:
        bridge.build_learning_overlay(source, project_id="PROJECT-X", memories=[external])
        raise AssertionError("external reference should not enter project-local memory overlay")
    except ValueError as exc:
        assert "NON_PROJECT_LOCAL_MEMORY_NOT_ALLOWED" in str(exc)

    print("CEW_VISUAL_LEARNING_BRIDGE_PASS")
    print("zero_prior_to_learning_receipt=PASS")
    print("project_local_memory_overlay=PASS")
    print("counterexample_memory=PASS")
    print("automatic_semantic_assignment=false")
    print("cross_project_leakage=BLOCKED")
    print("external_reference_as_project_memory=BLOCKED")


if __name__ == "__main__":
    main()
