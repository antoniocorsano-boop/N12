from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from experiments.cew_b01.prototype_guided_occurrence_search import (
    shortlist_prototype_guided_occurrences,
)

EXPECTED_SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
EXPECTED_FROZEN_PRIORITY_COUNTS = {"A": 6, "B": 2, "C": 3}
ALLOWED_HUMAN_DECISIONS = ["SIMILAR_TO_T1", "SIMILAR_TO_T2", "NEITHER", "UNCERTAIN"]


def _prototype_references(prototype_registry: dict[str, Any]) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    for prototype in prototype_registry.get("prototypes", []):
        references.append(
            {
                "prototype_id": str(prototype["prototype_id"]),
                "marker_primitive_id": str(prototype["marker_primitive_id"]),
                "human_reference_label": str(prototype["human_reference_label"]),
                "source_crop": str(prototype["source_crop"]),
            }
        )
    references.sort(key=lambda item: item["prototype_id"])
    return references


def build_expansion_manifest(
    shortlisted: list[dict[str, Any]],
    prototype_registry: dict[str, Any],
    *,
    source_sha256: str,
    page_index: int,
) -> dict[str, Any]:
    priority_counts = Counter(str(item["review_priority"]) for item in shortlisted)
    candidates: list[dict[str, Any]] = []
    for index, item in enumerate(shortlisted, start=1):
        marker_id = str(item["marker_primitive_id"])
        candidates.append(
            {
                **item,
                "panel_id": f"E{index:02d}",
                "source_crop": f"occurrence-{index:02d}-{marker_id}.png",
                "human_decision": "PENDING_HUMAN_REVIEW",
            }
        )

    return {
        "schema_id": "CEW_B01_PROTOTYPE_GUIDED_OCCURRENCE_EXPANSION",
        "schema_version": 1,
        "status": "PROTOTYPE_GUIDED_OCCURRENCE_HUMAN_REVIEW_PENDING",
        "source_sha256": source_sha256,
        "page_index": int(page_index),
        "selection_scope": "EXISTING_EXACT_SOURCE_REVIEW_ELIGIBLE_RECORDS_ONLY",
        "candidate_count": len(candidates),
        "priority_counts": {
            key: int(priority_counts.get(key, 0)) for key in ("A", "B", "C")
        },
        "prototype_references": _prototype_references(prototype_registry),
        "allowed_human_decisions": list(ALLOWED_HUMAN_DECISIONS),
        "candidates": candidates,
        "authority": {
            "semantic_classification_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "g2c_promotion_authorized": False,
            "g3_authorized": False,
            "merge_authorized": False,
        },
    }


def _negative_control_ids(receipt: dict[str, Any]) -> set[str]:
    return {
        str(panel["marker_primitive_id"])
        for panel in receipt.get("panels", [])
        if panel.get("role") == "NEGATIVE_CONTROL"
    }


def _crop_source_only(image: Any, geometry: dict[str, Any]) -> Any:
    cx = float(geometry["x"]) + float(geometry["width"]) / 2.0
    cy = float(geometry["y"]) + float(geometry["height"]) / 2.0
    margin_x = max(320, int(round(float(geometry["width"]) * 2.2)))
    margin_y = max(280, int(round(float(geometry["height"]) * 2.2)))
    left = max(0, int(round(cx - margin_x)))
    right = min(image.shape[1], int(round(cx + margin_x)))
    top = max(0, int(round(cy - margin_y)))
    bottom = min(image.shape[0], int(round(cy + margin_y)))
    crop = image[top:bottom, left:right].copy()
    if crop.size == 0:
        raise ValueError("PROTOTYPE_GUIDED_OCCURRENCE_EMPTY_CROP")
    return crop


def _label_panel(cv2: Any, crop: Any, text: str) -> Any:
    panel = cv2.copyMakeBorder(
        crop, 58, 0, 0, 0, cv2.BORDER_CONSTANT, value=255
    )
    cv2.putText(
        panel,
        text,
        (10, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.46,
        0,
        1,
        cv2.LINE_AA,
    )
    return panel


def _vertical_atlas(cv2: Any, panels: list[Any]) -> Any:
    if not panels:
        raise ValueError("PROTOTYPE_GUIDED_OCCURRENCE_NO_PANELS")
    max_width = max(panel.shape[1] for panel in panels)
    padded = [
        cv2.copyMakeBorder(
            panel,
            0,
            0,
            0,
            max_width - panel.shape[1],
            cv2.BORDER_CONSTANT,
            value=255,
        )
        if panel.shape[1] < max_width
        else panel
        for panel in panels
    ]
    return cv2.vconcat(padded)


def export_prototype_guided_occurrences(
    *,
    result_path: Path,
    raster_path: Path,
    prototype_registry_path: Path,
    negative_control_receipt_path: Path,
    beam_type_dir: Path,
    out_dir: Path,
) -> dict[str, Any]:
    import cv2

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    prototype_registry = json.loads(prototype_registry_path.read_text(encoding="utf-8"))
    negative_receipt = json.loads(
        negative_control_receipt_path.read_text(encoding="utf-8")
    )

    excluded_ids = _negative_control_ids(negative_receipt)
    shortlisted = shortlist_prototype_guided_occurrences(
        payload["records"], excluded_ids=excluded_ids
    )
    manifest = build_expansion_manifest(
        shortlisted,
        prototype_registry,
        source_sha256=str(payload["source_sha256"]),
        page_index=int(payload["page_index"]),
    )

    if manifest["source_sha256"] == EXPECTED_SOURCE_SHA256:
        if manifest["candidate_count"] != 11:
            raise ValueError("PROTOTYPE_GUIDED_OCCURRENCE_FROZEN_COUNT_MISMATCH")
        if manifest["priority_counts"] != EXPECTED_FROZEN_PRIORITY_COUNTS:
            raise ValueError("PROTOTYPE_GUIDED_OCCURRENCE_FROZEN_PRIORITY_MISMATCH")

    image = cv2.imread(str(raster_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("PROTOTYPE_GUIDED_OCCURRENCE_RASTER_UNREADABLE")
    out_dir.mkdir(parents=True, exist_ok=True)

    panels: list[Any] = []
    for reference in manifest["prototype_references"]:
        source_name = Path(reference["source_crop"]).name
        source_path = beam_type_dir / source_name
        reference_crop = cv2.imread(str(source_path), cv2.IMREAD_GRAYSCALE)
        if reference_crop is None:
            raise ValueError("PROTOTYPE_GUIDED_OCCURRENCE_REFERENCE_CROP_MISSING")
        panels.append(
            _label_panel(
                cv2,
                reference_crop,
                f"REFERENCE {reference['prototype_id']} {reference['human_reference_label']}",
            )
        )

    by_id = {str(record["marker_primitive_id"]): record for record in payload["records"]}
    for item in manifest["candidates"]:
        marker_id = str(item["marker_primitive_id"])
        source_record = by_id[marker_id]
        crop = _crop_source_only(image, source_record["review_marker_geometry"])
        if not cv2.imwrite(str(out_dir / item["source_crop"]), crop):
            raise ValueError("PROTOTYPE_GUIDED_OCCURRENCE_CROP_WRITE_FAILED")
        panels.append(
            _label_panel(
                cv2,
                crop,
                f"{item['panel_id']} priority={item['review_priority']} pending {marker_id}",
            )
        )

    atlas = _vertical_atlas(cv2, panels)
    atlas_path = out_dir / "prototype-guided-occurrence-review-atlas.png"
    if not cv2.imwrite(str(atlas_path), atlas):
        raise ValueError("PROTOTYPE_GUIDED_OCCURRENCE_ATLAS_WRITE_FAILED")

    manifest_path = out_dir / "prototype-guided-occurrence-candidates.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--raster", type=Path, required=True)
    parser.add_argument("--prototype-registry", type=Path, required=True)
    parser.add_argument("--negative-control-receipt", type=Path, required=True)
    parser.add_argument("--beam-type-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest = export_prototype_guided_occurrences(
        result_path=args.result,
        raster_path=args.raster,
        prototype_registry_path=args.prototype_registry,
        negative_control_receipt_path=args.negative_control_receipt,
        beam_type_dir=args.beam_type_dir,
        out_dir=args.out,
    )
    print(
        "PROTOTYPE_GUIDED_OCCURRENCE_EXPANSION="
        + json.dumps(
            {
                "status": manifest["status"],
                "candidate_count": manifest["candidate_count"],
                "priority_counts": manifest["priority_counts"],
                "semantic_authority": False,
                "g3_authorized": False,
                "merge_authorized": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
