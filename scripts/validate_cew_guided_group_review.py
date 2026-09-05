#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import cew_guided_group_review as group
import cew_guided_group_review_workbench as workbench
import cew_visual_learning as learning


def candidate(candidate_id: str, score: float, page_index: int) -> dict:
    signature = {
        "primitive_family": "RECTILINEAR_CLOSED_SHAPE",
        "aspect_bucket": "TALL",
        "area_bucket": "SMALL",
        "complexity_bucket": "FEW",
        "stroke_width_bucket": "THIN",
        "filled": False,
    }
    embedding = learning.structured_embedding_from_signature(
        signature,
        input_fingerprint=f"sha256:{candidate_id:0<64}"[:71],
        source_version_id="SRC-V1",
        page_index=page_index,
        candidate_id=candidate_id,
    )
    return {
        "candidate_id": candidate_id,
        "source_version_id": "SRC-V1",
        "page_id": f"PAGE-{page_index}",
        "page_index": page_index,
        "bbox": {"x": 0.1, "y": 0.2, "w": 0.1, "h": 0.2},
        "primitive_family": "RECTILINEAR_CLOSED_SHAPE",
        "evidence_fingerprint": f"sha256:{candidate_id:0<64}"[:71],
        "embedding": embedding,
        "fused_score": score,
        "is_training_example": False,
    }


def main() -> None:
    snapshot = group.build_snapshot(
        project_id="N12",
        concept_id="COLUMN",
        meaning="pilastro",
        memory_fingerprint="sha256:" + "a" * 64,
        candidates=[candidate("C1", 0.96, 0), candidate("C2", 0.77, 0), candidate("C3", 0.35, 1)],
    )
    assert snapshot["band_counts"] == {
        "HIGH_SIMILARITY_PROPOSAL": 1,
        "REVIEW_PROPOSAL": 1,
        "LOW_SIMILARITY_PROPOSAL": 1,
    }
    assert snapshot["default_selected_candidate_ids"] == ["C1"]
    receipt = group.build_receipt(
        snapshot,
        action="CONFIRM_SELECTED",
        selected_candidate_ids=["C1"],
        reviewer="human-reviewer",
        rationale="Source-visible geometry is coherent with the taught prototype.",
        timestamp="2026-09-05T06:00:00+00:00",
    )
    group.validate_receipt(receipt)
    assert receipt["selected_count"] == 1
    assert receipt["derived_learning_receipts"][0]["role"] == "POSITIVE"
    assert receipt["authority"]["canonical_write_authorized"] is False
    assert receipt["authority"]["structural_identity_authorized"] is False

    tampered = deepcopy(receipt)
    tampered["selected_candidate_ids"] = ["C2"]
    try:
        group.validate_receipt(tampered)
    except ValueError as exc:
        assert "FINGERPRINT" in str(exc)
    else:
        raise AssertionError("tampered group receipt must fail closed")

    duplicate_training = deepcopy(snapshot)
    duplicate_training["members"][0]["is_training_example"] = True
    try:
        group.build_receipt(
            duplicate_training,
            action="CONFIRM_SELECTED",
            selected_candidate_ids=["C1"],
            reviewer="human-reviewer",
            rationale="must reject reselection",
        )
    except ValueError as exc:
        assert "RESELECTION" in str(exc)
    else:
        raise AssertionError("training example reselection must be rejected")

    page = workbench._patched_document_discovery_page()
    assert "analyze-preview-async" in page
    assert "/workbench/guided-group-review?session=" in page
    assert "Trova simili" in page

    root = Path(__file__).resolve().parents[1]
    professional = (root / "scripts" / "cew_professional_workbench_api.py").read_text(encoding="utf-8")
    guided = (root / "scripts" / "cew_guided_group_review_workbench.py").read_text(encoding="utf-8")
    assert "import cew_guided_group_review_workbench as _guided_group_review" in professional
    guided_mount = professional.index("router.include_router(_guided_group_review.build_router())")
    async_mount = professional.index("router.include_router(_document_discovery_async_preview.build_router())")
    base_mount = professional.index("router.include_router(_document_discovery.build_router(source_workspace))")
    assert guided_mount < async_mount < base_mount
    assert "discovery.memory = integrated_memory" in guided
    assert "DOCUMENT_DISCOVERY_GROUP_SNAPSHOT_STALE" in guided
    assert "X-CEW-Group-Review\": \"GUIDED_V1" in guided

    print("GUIDED_GROUP_REVIEW_PASS")


if __name__ == "__main__":
    main()
