from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from experiments.cew_col02.exact_source_audit import (
    PAGE_ID,
    PAGE_TRANSFORM_ID,
    SOURCE_SHA256,
    SOURCE_VERSION_ID,
    _bbox_pixels,
    _bind_candidates,
    _normalized_text_observations,
    _tesseract_tsv,
    canonical_bytes,
)
from experiments.cew_col02.prototype_guided_search import rank_from_human_review


MAX_REVIEW_PANELS = 24
HUMAN_REVIEW_PATH = Path("governance/cew-col02/COLUMN_FOOTPRINT_HUMAN_REVIEW_v1.json")


def _authority() -> dict[str, bool]:
    return {
        "graphical_similarity_review_authorized": True,
        "support_identity_authorized": False,
        "text_identity_binding_authorized": False,
        "family_assignment_authorized": False,
        "section_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


def _crop_bounds(box: dict[str, float], width: int, height: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = _bbox_pixels(box, width, height)
    span = max(right - left, bottom - top, 70)
    margin = max(120, int(round(span * 1.8)))
    return max(0, left - margin), max(0, top - margin), min(width, right + margin), min(height, bottom + margin)


def _pad(panel: np.ndarray, width: int) -> np.ndarray:
    if panel.shape[1] >= width:
        return panel
    return cv2.copyMakeBorder(panel, 0, 0, 0, width - panel.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255))


def _export_search_review(
    image: np.ndarray,
    search_results: list[dict[str, Any]],
    records_by_id: dict[str, dict[str, Any]],
    out: Path,
) -> list[dict[str, Any]]:
    review_dir = out / "similarity-review"
    review_dir.mkdir(parents=True, exist_ok=True)
    height, width = image.shape[:2]
    manifest: list[dict[str, Any]] = []
    panels: list[np.ndarray] = []

    for index, result in enumerate(search_results[:MAX_REVIEW_PANELS], start=1):
        candidate_id = result["occurrence_candidate_id"]
        record = records_by_id[candidate_id]
        panel_id = f"S{index:02d}"
        left, top, right, bottom = _crop_bounds(record["bbox"], width, height)
        source_crop = image[top:bottom, left:right].copy()
        overlay = cv2.cvtColor(source_crop, cv2.COLOR_GRAY2BGR)

        fp_left, fp_top, fp_right, fp_bottom = _bbox_pixels(record["bbox"], width, height)
        cv2.rectangle(
            overlay,
            (fp_left - left, fp_top - top),
            (fp_right - left, fp_bottom - top),
            (0, 0, 255),
            3,
        )
        cv2.putText(
            overlay,
            candidate_id,
            (max(3, fp_left - left), max(18, fp_top - top - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )

        local_bindings: list[dict[str, Any]] = []
        for binding in record["text_binding"]["bindings"]:
            if binding["relation"] == "UNRELATED_OR_UNBOUND":
                continue
            tx1, ty1, tx2, ty2 = _bbox_pixels(binding["bbox"], width, height)
            if tx2 < left or tx1 > right or ty2 < top or ty1 > bottom:
                continue
            local_bindings.append(binding)
            colour = (0, 128, 0) if binding["relation"] == "INSIDE_FOOTPRINT" else (255, 0, 0)
            cv2.rectangle(overlay, (tx1 - left, ty1 - top), (tx2 - left, ty2 - top), colour, 2)
            cv2.putText(
                overlay,
                f"{binding['token_id']}:{binding.get('raw_text','')}:{binding['relation']}",
                (max(3, tx1 - left), min(overlay.shape[0] - 6, max(16, ty1 - top - 5))),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.34,
                colour,
                1,
                cv2.LINE_AA,
            )

        source_name = f"similarity-review/{panel_id.lower()}-source-only.png"
        overlay_name = f"similarity-review/{panel_id.lower()}-target-overlay.png"
        assert cv2.imwrite(str(out / source_name), source_crop)
        assert cv2.imwrite(str(out / overlay_name), overlay)

        manifest.append(
            {
                "panel_id": panel_id,
                "candidate_id": candidate_id,
                "bbox": record["bbox"],
                "score": result["score"],
                "best_prototype_candidate_id": result["best_prototype_candidate_id"],
                "matched_prototype_candidate_ids": result["matched_prototype_candidate_ids"],
                "prototype_count": result["prototype_count"],
                "size_similarity": result["size_similarity"],
                "ratio_similarity": result["ratio_similarity"],
                "rectangularity": result["rectangularity"],
                "detector": result["detector"],
                "axis_evidence_present": result["axis_evidence_present"],
                "text_bindings": local_bindings,
                "source_only_crop": source_name,
                "overlay_crop": overlay_name,
                "column_graphic_decision": "PENDING_HUMAN_REVIEW",
                "support_identity": None,
            }
        )

        source_bgr = cv2.cvtColor(source_crop, cv2.COLOR_GRAY2BGR)
        pair = cv2.hconcat([source_bgr, overlay])
        header = np.full((86, pair.shape[1], 3), 255, dtype=np.uint8)
        cv2.putText(
            header,
            f"{panel_id} | {candidate_id} | score={result['score']:.3f} | best={result['best_prototype_candidate_id']}",
            (12, 29),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            header,
            "LEFT=source only | RIGHT=similar footprint + OCR relations | decide only PILASTRO / NON PILASTRO / INCERTO",
            (12, 57),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.37,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        panels.append(cv2.vconcat([header, pair]))

    if panels:
        max_width = max(panel.shape[1] for panel in panels)
        atlas = cv2.vconcat([_pad(panel, max_width) for panel in panels])
    else:
        atlas = np.full((180, 1200, 3), 255, dtype=np.uint8)
        cv2.putText(atlas, "CEW-COL-02: no prototype-guided similarity proposals", (25, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    assert cv2.imwrite(str(out / "col02-prototype-guided-search-atlas.png"), atlas)
    return manifest


def main() -> None:
    from cew_b01.document_zoning import propose_document_zones
    from cew_b01.evidence_schema import Task3RasterBinding
    from cew_b01.pdf_probe import probe_pdf
    from cew_b01.primitive_census import _analysis_binary, _confirmed_analysis_mask
    from cew_b01.source_contract import load_source_contract, materialize_source
    from cew_b01.zone_review_package import confirmed_zones_from_receipt, zone_set_digest
    from experiments.cew_col02.footprint_proposals import extract_footprint_proposals

    runner_temp = Path(os.environ["RUNNER_TEMP"])
    out = Path("evidence/cew-col02/footprint-text-binding")
    out.mkdir(parents=True, exist_ok=True)

    review_receipt = json.loads(HUMAN_REVIEW_PATH.read_text(encoding="utf-8"))
    contract = load_source_contract("governance/cew-b01/N12_TAV5_SOURCE_v1.json")
    materialized = materialize_source(contract, ".", runner_temp / "tavola5-col02-search-source.pdf")
    assert materialized.sha256 == SOURCE_SHA256

    probe_dir = runner_temp / "cew-col02-search-probe"
    probe = probe_pdf(materialized, probe_dir)
    raster_binding = Task3RasterBinding.from_probe_mapping(probe.to_mapping())
    raster_path = probe_dir / "tav5-page0-300dpi.png"
    proposed_zones = propose_document_zones(raster_binding, raster_path)
    zone_receipt = json.loads(Path("governance/cew-b01/TAV5_DOCUMENT_ZONE_REVIEW_v1.json").read_text(encoding="utf-8"))
    zones = confirmed_zones_from_receipt(raster_binding, proposed_zones, zone_receipt)
    assert all(zone.human_confirmed for zone in zones)
    assert zone_set_digest(zones) == zone_receipt["zone_set_digest"]

    image = cv2.imread(str(raster_path), cv2.IMREAD_GRAYSCALE)
    assert image is not None
    mask = _confirmed_analysis_mask(raster_binding, zones)
    analysis, _binary = _analysis_binary(image, mask)
    analysis_path = runner_temp / "cew-col02-search-workarea.png"
    assert cv2.imwrite(str(analysis_path), analysis)

    proposals_a = extract_footprint_proposals(analysis, max_candidates=6000)
    proposals_b = extract_footprint_proposals(analysis, max_candidates=6000)
    assert canonical_bytes(proposals_a) == canonical_bytes(proposals_b)

    tsv_a, tesseract_version_a = _tesseract_tsv(analysis_path)
    tsv_b, tesseract_version_b = _tesseract_tsv(analysis_path)
    assert tesseract_version_a == tesseract_version_b
    text_a = _normalized_text_observations(tsv_a, image.shape[1], image.shape[0])
    text_b = _normalized_text_observations(tsv_b, image.shape[1], image.shape[0])
    assert canonical_bytes(text_a) == canonical_bytes(text_b)

    records_a = _bind_candidates(proposals_a["candidates"], text_a)
    records_b = _bind_candidates(proposals_b["candidates"], text_b)
    assert canonical_bytes(records_a) == canonical_bytes(records_b)

    search_a = rank_from_human_review(proposals_a["candidates"], review_receipt, limit=64)
    search_b = rank_from_human_review(proposals_b["candidates"], review_receipt, limit=64)
    assert canonical_bytes(search_a) == canonical_bytes(search_b)

    records_by_id = {record["candidate_id"]: record for record in records_a}
    review_manifest = _export_search_review(image, search_a, records_by_id, out)

    positive_ids = [
        item["candidate_id"]
        for item in review_receipt["panel_decisions"]
        if item.get("column_graphic_decision") == "COLUMN_FOOTPRINT_CONFIRMED" and item.get("prototype_eligible") is True
    ]
    negative_ids = [
        item["candidate_id"]
        for item in review_receipt["panel_decisions"]
        if item.get("column_graphic_decision") == "NOT_COLUMN"
    ]

    payload = {
        "schema_id": "CEW_COL02_PROTOTYPE_GUIDED_EXACT_SOURCE_SEARCH",
        "schema_version": 1,
        "status": "PROTOTYPE_GUIDED_SEARCH_READY_FOR_HUMAN_REVIEW",
        "source": {
            "source_version_id": SOURCE_VERSION_ID,
            "page_id": PAGE_ID,
            "page_transform_id": PAGE_TRANSFORM_ID,
            "sha256": materialized.sha256,
            "path": contract.path,
            "commit": contract.commit,
        },
        "human_review_input": {
            "receipt_path": str(HUMAN_REVIEW_PATH),
            "receipt_sha256": hashlib.sha256(canonical_bytes(review_receipt)).hexdigest(),
            "positive_prototype_candidate_ids": positive_ids,
            "reviewed_negative_candidate_ids": negative_ids,
            "positive_count": len(positive_ids),
            "negative_count": len(negative_ids),
        },
        "search_contract": {
            "historical_similarity_weights_reused": True,
            "negative_examples_train_similarity": False,
            "reviewed_negatives_excluded_from_output": True,
            "text_required": False,
            "axes_required": False,
            "historical_support_ids_used_to_generate_or_rank": False,
            "historical_family_ids_used_to_generate_or_rank": False,
        },
        "result": {
            "proposal_count": proposals_a["candidate_count"],
            "retrieved_similarity_candidate_count": len(search_a),
            "review_panel_count": len(review_manifest),
            "candidates_matching_both_positive_prototypes": sum(1 for item in search_a if item["prototype_count"] > 1),
            "top_score": search_a[0]["score"] if search_a else None,
        },
        "search_results": search_a,
        "review_panels": review_manifest,
        "next_required_human_action": "CLASSIFY_S01_TO_S24_AS_COLUMN_NOT_COLUMN_OR_UNCERTAIN",
        "authority": _authority(),
    }
    replay = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    payload["replay_sha256"] = replay
    (out / "col02-prototype-guided-search.json").write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = {
        "status": payload["status"],
        "positive_prototypes": positive_ids,
        "reviewed_negative_count": len(negative_ids),
        "proposal_count": proposals_a["candidate_count"],
        "retrieved_similarity_candidate_count": len(search_a),
        "review_panel_count": len(review_manifest),
        "both_prototypes_count": payload["result"]["candidates_matching_both_positive_prototypes"],
        "replay_sha256": replay,
    }
    print("CEW_COL02_PROTOTYPE_GUIDED_SEARCH=" + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
