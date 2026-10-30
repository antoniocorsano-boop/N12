from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
SOURCE_VERSION_ID = "CEW-N12-SRC-TAV05S-V2143DBCF"
PAGE_ID = "CEW-N12-PAGE-TAV05S-P001"
DERIVED_ASSET_ID = "CEW-N12-ASSET-TAV05S-P001-300DPI"
PAGE_TRANSFORM_ID = "CEW-N12-XFORM-TAV05S-P001"
MAX_REVIEW_PANELS = 18


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _tesseract_tsv(raster_path: Path) -> tuple[str, str]:
    version = subprocess.run(
        ["tesseract", "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0].strip()
    result = subprocess.run(
        ["tesseract", str(raster_path), "stdout", "--psm", "11", "tsv"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout, version


def _normalized_text_observations(tsv_text: str, width: int, height: int) -> list[dict[str, Any]]:
    from experiments.cew_col01.number_anchor import parse_support_like_tsv

    anchors = parse_support_like_tsv(tsv_text)
    observations: list[dict[str, Any]] = []
    for index, anchor in enumerate(anchors, start=1):
        box = anchor["bbox"]
        observations.append(
            {
                "token_id": f"TXT-{index:03d}",
                "raw_text": anchor["text"],
                "normalized_text": anchor["normalized_id"],
                "confidence": anchor["confidence"],
                "bbox": {
                    "x": box["x"] / width,
                    "y": box["y"] / height,
                    "width": box["width"] / width,
                    "height": box["height"] / height,
                },
                "bbox_px": dict(box),
            }
        )
    return observations


def _bind_candidates(
    candidates: list[dict[str, Any]],
    text_observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    from experiments.cew_col02.text_footprint_binding import bind_text_observations

    records: list[dict[str, Any]] = []
    binder_input = [
        {"token_id": item["token_id"], "raw_text": item["raw_text"], "bbox": item["bbox"]}
        for item in text_observations
    ]
    for candidate in candidates:
        binding = bind_text_observations(candidate["bbox"], binder_input)
        records.append(
            {
                "candidate_id": candidate["candidate_id"],
                "bbox": candidate["bbox"],
                "detector": candidate["detector"],
                "rectangularity": candidate["rectangularity"],
                "build_quality": candidate.get("build_quality", 0.0),
                "aspect_ratio": candidate.get("aspect_ratio"),
                "axis_evidence_present": bool(candidate.get("axis_evidence_present", False)),
                "text_binding": binding,
                "support_identity": None,
                "family_id": None,
            }
        )
    return records


def _review_priority(record: dict[str, Any]) -> tuple[int, float, float, str]:
    state = record["text_binding"]["binding_state"]
    if state == "ONE_INTERNAL_TEXT":
        group = 0
    elif state == "MULTIPLE_INTERNAL_TEXT_AMBIGUOUS":
        group = 1
    else:
        ratio = float(record.get("aspect_ratio") or 1.0)
        group = 2 if ratio <= 0.45 or ratio >= 2.2 else 3
    return (
        group,
        -float(record.get("build_quality", 0.0)),
        -float(record.get("rectangularity", 0.0)),
        str(record["candidate_id"]),
    )


def _select_neutral_review_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select neutral prototype-choice candidates without historical support IDs.

    Internal text raises review priority because the current human review found it
    useful on this source, but text is not required: elongated/high-quality
    geometry without OCR remains represented so OCR misses cannot exclude a
    potential prototype.
    """

    ordered = sorted(records, key=_review_priority)
    selected: list[dict[str, Any]] = []
    internal_seen = 0
    elongated_no_text_seen = 0
    general_seen = 0
    for record in ordered:
        state = record["text_binding"]["binding_state"]
        ratio = float(record.get("aspect_ratio") or 1.0)
        elongated = ratio <= 0.45 or ratio >= 2.2
        if state in {"ONE_INTERNAL_TEXT", "MULTIPLE_INTERNAL_TEXT_AMBIGUOUS"}:
            selected.append(record)
            internal_seen += 1
        elif elongated and elongated_no_text_seen < 7:
            selected.append(record)
            elongated_no_text_seen += 1
        elif general_seen < 5:
            selected.append(record)
            general_seen += 1
        if len(selected) >= MAX_REVIEW_PANELS:
            break
    return selected


def _bbox_pixels(box: dict[str, float], width: int, height: int) -> tuple[int, int, int, int]:
    left = max(0, min(width - 1, int(round(box["x"] * width))))
    top = max(0, min(height - 1, int(round(box["y"] * height))))
    right = max(left + 1, min(width, int(round((box["x"] + box["width"]) * width))))
    bottom = max(top + 1, min(height, int(round((box["y"] + box["height"]) * height))))
    return left, top, right, bottom


def _crop_bounds(record: dict[str, Any], width: int, height: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = _bbox_pixels(record["bbox"], width, height)
    fp_span = max(right - left, bottom - top, 70)
    margin = max(120, int(round(fp_span * 1.8)))
    return (
        max(0, left - margin),
        max(0, top - margin),
        min(width, right + margin),
        min(height, bottom + margin),
    )


def _export_review_package(
    image: Any,
    records: list[dict[str, Any]],
    source: dict[str, Any],
    out: Path,
) -> list[dict[str, Any]]:
    import cv2
    import numpy as np

    from experiments.cew_col02.review_export import build_review_manifest_entry

    selected = _select_neutral_review_records(records)
    review_dir = out / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    height, width = image.shape[:2]
    manifest: list[dict[str, Any]] = []
    atlas_panels: list[Any] = []

    for index, record in enumerate(selected, start=1):
        panel_id = f"P{index:02d}"
        left, top, right, bottom = _crop_bounds(record, width, height)
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
            record["candidate_id"],
            (max(3, fp_left - left), max(18, fp_top - top - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )

        local_bindings: list[dict[str, Any]] = []
        for binding in record["text_binding"]["bindings"]:
            if binding["relation"] == "UNRELATED_OR_UNBOUND":
                continue
            local_bindings.append(binding)
            tx1, ty1, tx2, ty2 = _bbox_pixels(binding["bbox"], width, height)
            colour = (0, 128, 0) if binding["relation"] == "INSIDE_FOOTPRINT" else (255, 0, 0)
            cv2.rectangle(
                overlay,
                (tx1 - left, ty1 - top),
                (tx2 - left, ty2 - top),
                colour,
                2,
            )
            cv2.putText(
                overlay,
                f"{binding['token_id']}:{binding.get('raw_text','')}:{binding['relation']}",
                (max(3, tx1 - left), min(overlay.shape[0] - 6, max(16, ty1 - top - 5))),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.36,
                colour,
                1,
                cv2.LINE_AA,
            )

        local_binding_payload = dict(record["text_binding"])
        local_binding_payload["bindings"] = local_bindings
        internal_ids = [
            item["token_id"] for item in local_bindings if item["relation"] == "INSIDE_FOOTPRINT"
        ]
        local_binding_payload["internal_token_ids"] = internal_ids
        if len(internal_ids) == 1:
            local_binding_payload["binding_state"] = "ONE_INTERNAL_TEXT"
            local_binding_payload["preferred_internal_token_id"] = internal_ids[0]
        elif len(internal_ids) > 1:
            local_binding_payload["binding_state"] = "MULTIPLE_INTERNAL_TEXT_AMBIGUOUS"
            local_binding_payload["preferred_internal_token_id"] = None
        else:
            local_binding_payload["binding_state"] = "NO_INTERNAL_TEXT"
            local_binding_payload["preferred_internal_token_id"] = None

        source_name = f"review/{panel_id.lower()}-source-only.png"
        overlay_name = f"review/{panel_id.lower()}-target-overlay.png"
        assert cv2.imwrite(str(out / source_name), source_crop)
        assert cv2.imwrite(str(out / overlay_name), overlay)

        candidate_for_manifest = {
            "candidate_id": record["candidate_id"],
            "bbox": record["bbox"],
            "detector": record["detector"],
            "score": None,
            "axis_evidence_present": record["axis_evidence_present"],
        }
        entry = build_review_manifest_entry(
            panel_id=panel_id,
            candidate=candidate_for_manifest,
            text_binding=local_binding_payload,
            source=source,
            source_only_crop=source_name,
            overlay_crop=overlay_name,
        )
        entry["crop_bounds_px"] = {"left": left, "top": top, "right": right, "bottom": bottom}
        entry["prototype_selection_decision"] = "PENDING_HUMAN_REVIEW"
        entry["prototype_selection_role"] = "NEUTRAL_CANDIDATE_FOR_HUMAN_TEACHING"
        manifest.append(entry)

        source_bgr = cv2.cvtColor(source_crop, cv2.COLOR_GRAY2BGR)
        header = np.full((74, source_bgr.shape[1] + overlay.shape[1], 3), 255, dtype=np.uint8)
        cv2.putText(
            header,
            f"{panel_id} | {record['candidate_id']} | {local_binding_payload['binding_state']}",
            (12, 29),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            header,
            "LEFT=source only | RIGHT=machine footprint + exact OCR targets | choose prototype only if whole footprint is correct",
            (12, 56),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        pair = cv2.hconcat([source_bgr, overlay])
        atlas_panels.append(cv2.vconcat([header, pair]))

    if atlas_panels:
        max_width = max(panel.shape[1] for panel in atlas_panels)
        padded = [
            cv2.copyMakeBorder(panel, 0, 0, 0, max_width - panel.shape[1], cv2.BORDER_CONSTANT, value=255)
            if panel.shape[1] < max_width else panel
            for panel in atlas_panels
        ]
        atlas = cv2.vconcat(padded)
    else:
        atlas = np.full((180, 1200, 3), 255, dtype=np.uint8)
        cv2.putText(
            atlas,
            "CEW-COL-02: no neutral footprint proposals available for prototype selection",
            (25, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )
    assert cv2.imwrite(str(out / "col02-prototype-selection-atlas.png"), atlas)
    return manifest


def _authority() -> dict[str, bool]:
    return {
        "support_identity_authorized": False,
        "family_assignment_authorized": False,
        "section_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "semantic_classification_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


def main() -> None:
    import cv2

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

    contract = load_source_contract("governance/cew-b01/N12_TAV5_SOURCE_v1.json")
    materialized = materialize_source(contract, ".", runner_temp / "tavola5-col02-source.pdf")
    assert materialized.sha256 == SOURCE_SHA256

    probe_dir = runner_temp / "cew-col02-probe"
    probe = probe_pdf(materialized, probe_dir)
    raster_binding = Task3RasterBinding.from_probe_mapping(probe.to_mapping())
    raster_path = probe_dir / "tav5-page0-300dpi.png"

    proposed_zones = propose_document_zones(raster_binding, raster_path)
    zone_receipt = json.loads(
        Path("governance/cew-b01/TAV5_DOCUMENT_ZONE_REVIEW_v1.json").read_text(encoding="utf-8")
    )
    zones = confirmed_zones_from_receipt(raster_binding, proposed_zones, zone_receipt)
    assert all(zone.human_confirmed for zone in zones)
    assert zone_set_digest(zones) == zone_receipt["zone_set_digest"]

    image = cv2.imread(str(raster_path), cv2.IMREAD_GRAYSCALE)
    assert image is not None
    mask = _confirmed_analysis_mask(raster_binding, zones)
    analysis, _binary = _analysis_binary(image, mask)
    analysis_path = runner_temp / "cew-col02-structural-workarea.png"
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

    binding_counts = dict(sorted(Counter(r["text_binding"]["binding_state"] for r in records_a).items()))
    relation_counts = Counter()
    for record in records_a:
        for item in record["text_binding"]["bindings"]:
            relation_counts[item["relation"]] += 1

    source = {
        "source_version_id": SOURCE_VERSION_ID,
        "page_id": PAGE_ID,
        "derived_asset_id": DERIVED_ASSET_ID,
        "page_transform_id": PAGE_TRANSFORM_ID,
        "repository": contract.repository,
        "commit": contract.commit,
        "path": contract.path,
        "git_blob_sha": contract.git_blob_sha,
        "sha256": materialized.sha256,
        "page_index": contract.page_index,
        "raster_width_px": raster_binding.raster_width_px,
        "raster_height_px": raster_binding.raster_height_px,
        "zone_set_digest": zone_receipt["zone_set_digest"],
    }
    review_source = {
        "source_version_id": SOURCE_VERSION_ID,
        "page_id": PAGE_ID,
        "page_transform_id": PAGE_TRANSFORM_ID,
        "sha256": materialized.sha256,
    }
    review_manifest = _export_review_package(image, records_a, review_source, out)

    payload = {
        "schema_id": "CEW_COL02_FOOTPRINT_TEXT_BINDING_EXACT_SOURCE",
        "schema_version": 1,
        "status": "HUMAN_PROTOTYPE_REQUIRED",
        "source": source,
        "toolchain": {"tesseract": tesseract_version_a, "opencv": cv2.__version__},
        "historical_reuse": {
            "pr136_prototype_search_core_reused": True,
            "pr136_axis_suppression_principle_reused": True,
            "durable_human_prototype_receipt_found": False,
            "historical_runtime_store_path": "runtime/oar_g4_prototype_receipts",
            "prototype_reconstructed_from_benchmark": False,
            "reason": "No concrete OPROT-G4 prototype receipt/bbox was found in the qualified PR #136 repository tree or review timeline.",
        },
        "candidate_generation": {
            "footprint_first": True,
            "text_required": False,
            "axes_required": False,
            "historical_support_ids_used_to_generate_candidates": False,
            "historical_family_ratios_used_to_generate_candidates": False,
            "proposal_count": proposals_a["candidate_count"],
            "axis_suppressed_candidate_count": proposals_a["axis_suppressed_candidate_count"],
            "nested_raw_candidate_suppressed_count": proposals_a["nested_raw_candidate_suppressed_count"],
        },
        "text_observations": {
            "numeric_token_count": len(text_a),
            "binding_state_counts": binding_counts,
            "relation_counts": dict(sorted(relation_counts.items())),
        },
        "review_role": "NEUTRAL_PROTOTYPE_SELECTION_BEFORE_SIMILARITY_SEARCH",
        "review_panels": review_manifest,
        "next_required_human_action": "SELECT_ONE_CORRECT_WHOLE_COLUMN_FOOTPRINT_AS_PROJECT_LOCAL_PROTOTYPE_OR_REJECT_ALL",
        "authority": _authority(),
    }
    digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    payload["replay_sha256"] = digest
    (out / "col02-audit.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    summary = {
        "status": payload["status"],
        "source_sha256": materialized.sha256,
        "proposal_count": proposals_a["candidate_count"],
        "axis_suppressed_candidate_count": proposals_a["axis_suppressed_candidate_count"],
        "nested_raw_candidate_suppressed_count": proposals_a["nested_raw_candidate_suppressed_count"],
        "numeric_token_count": len(text_a),
        "binding_state_counts": binding_counts,
        "review_panel_count": len(review_manifest),
        "replay_sha256": digest,
        "authority": _authority(),
    }
    print("CEW_COL02_EXACT_SOURCE_AUDIT=" + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
