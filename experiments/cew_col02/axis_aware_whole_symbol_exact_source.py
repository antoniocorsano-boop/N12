from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from experiments.cew_col02.axis_aware_local_envelope import reconstruct_local_axis_envelope
from experiments.cew_col02.axis_aware_whole_symbol import (
    CLOSED_AUTHORITY_KEYS,
    EXPECTED_REJECTED_TASKS,
    EXPECTED_REPAIR_TASKS,
    reconstruct_axis_split_whole_symbol,
)
from experiments.cew_col02.exact_source_audit import SOURCE_SHA256, canonical_bytes


EVIDENCE_ROOT = Path("evidence/cew-col02/footprint-text-binding")
RECEIPT_PATH = Path("governance/cew-col02/COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW_v1.json")
OUTPUT_JSON = EVIDENCE_ROOT / "col02-axis-aware-whole-symbol-repair.json"
ASSET_DIR = EVIDENCE_ROOT / "axis-aware-whole-symbol-repair"
ATLAS_PATH = EVIDENCE_ROOT / "col02-axis-aware-whole-symbol-repair-atlas.png"
EXPECTED_PROPOSAL_COUNT = 611


def _validate_receipt_payload(receipt: dict[str, Any]) -> None:
    if receipt.get("schema_id") != "CEW_COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW" or receipt.get("schema_version") != 1:
        raise ValueError("unexpected repair receipt schema")
    authority = receipt.get("authority")
    if not isinstance(authority, dict) or authority.get("graphical_whole_symbol_repair_authorized") is not True:
        raise ValueError("repair receipt graphical authority is not explicit")
    for key in CLOSED_AUTHORITY_KEYS:
        if authority.get(key) is not False:
            raise ValueError(f"repair receipt authority drift: {key}")
    decisions = receipt.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("repair receipt decisions are missing")
    by_task = {str(row.get("review_task_id")): row for row in decisions}
    if set(by_task) != set(EXPECTED_REPAIR_TASKS) | set(EXPECTED_REJECTED_TASKS):
        raise ValueError("repair receipt task set drift")
    for task_id, candidate_id in EXPECTED_REPAIR_TASKS.items():
        row = by_task[task_id]
        if (
            row.get("candidate_id") != candidate_id
            or row.get("decision") != "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY"
            or row.get("repair_eligible") is not True
        ):
            raise ValueError(f"repair receipt fragmented-seed drift: {task_id}")
    for task_id, candidate_id in EXPECTED_REJECTED_TASKS.items():
        row = by_task[task_id]
        if (
            row.get("candidate_id") != candidate_id
            or row.get("decision") != "MISLOCALIZED_NOT_COLUMN"
            or row.get("repair_eligible") is not False
        ):
            raise ValueError(f"repair receipt rejected-seed drift: {task_id}")


def build_axis_aware_repair_manifest(
    *,
    receipt: dict[str, Any],
    proposals: list[dict[str, Any]],
    repair_results: dict[str, dict[str, Any] | None],
    source_replay_sha256: str,
) -> dict[str, Any]:
    _validate_receipt_payload(receipt)
    proposal_by_id: dict[str, dict[str, Any]] = {}
    for proposal in proposals:
        candidate_id = str(proposal.get("candidate_id", ""))
        if not candidate_id or candidate_id in proposal_by_id:
            raise ValueError("proposal IDs must be present and unique")
        proposal_by_id[candidate_id] = proposal

    repair_candidate_ids = list(EXPECTED_REPAIR_TASKS.values())
    rejected_candidate_ids = list(EXPECTED_REJECTED_TASKS.values())
    for candidate_id in repair_candidate_ids:
        if candidate_id not in proposal_by_id:
            raise ValueError(f"missing repair seed proposal: {candidate_id}")
    for candidate_id in rejected_candidate_ids:
        if candidate_id not in proposal_by_id:
            raise ValueError(f"missing rejected seed proposal: {candidate_id}")
    unexpected_results = set(repair_results) - set(repair_candidate_ids)
    if unexpected_results:
        raise ValueError(f"repair results contain unauthorized seeds: {sorted(unexpected_results)}")

    repairs: list[dict[str, Any]] = []
    for index, candidate_id in enumerate(repair_candidate_ids, start=1):
        result = repair_results.get(candidate_id)
        source_bbox = dict(proposal_by_id[candidate_id]["bbox"])
        record: dict[str, Any] = {
            "repair_id": f"COL02-WSR-{index:03d}",
            "source_candidate_id": candidate_id,
            "source_seed_bbox": source_bbox,
            "status": "READY_FOR_HUMAN_GRAPHICAL_REVIEW" if result is not None else "UNRESOLVED_GEOMETRY_REPAIR",
            "reconstructed_bbox": dict(result["bbox"]) if result is not None else None,
            "graphical_decision": "PENDING_HUMAN_REVIEW" if result is not None else "NOT_APPLICABLE_UNRESOLVED",
        }
        if result is not None:
            if int(result.get("boundary_side_count", 0)) != 4:
                raise ValueError(f"repair lacks four-side boundary evidence: {candidate_id}")
            record["axis_cross"] = dict(result["axis_cross"])
            record["axis_thickness_px"] = dict(result["axis_thickness_px"])
            record["boundary_side_count"] = 4
            record["boundary_coverage"] = dict(result.get("boundary_coverage", {}))
            record["detector"] = str(result.get("detector", "AXIS_AWARE_WHOLE_SYMBOL_REPAIR"))
        repairs.append(record)

    rejected = [
        {"candidate_id": candidate_id, "reason": "MISLOCALIZED_NOT_COLUMN"}
        for candidate_id in rejected_candidate_ids
    ]
    ready_count = sum(1 for row in repairs if row["status"] == "READY_FOR_HUMAN_GRAPHICAL_REVIEW")
    unresolved_count = len(repairs) - ready_count
    return {
        "schema": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR_MANIFEST_v1",
        "status": "AXIS_AWARE_WHOLE_SYMBOL_REPAIR_READY_FOR_HUMAN_REVIEW",
        "source_replay_sha256": str(source_replay_sha256),
        "proposal_count": len(proposals),
        "original_proposal_id_space_immutable": True,
        "repair_candidate_count": len(repairs),
        "ready_for_human_review_count": ready_count,
        "unresolved_repair_count": unresolved_count,
        "rejected_candidates": rejected,
        "repairs": repairs,
        "occurrence_coverage_complete": False,
        "authority": {
            "graphical_whole_symbol_repair_authorized": True,
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
        },
    }


def _regenerate_source_analysis_and_proposals() -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    from cew_b01.document_zoning import propose_document_zones
    from cew_b01.evidence_schema import Task3RasterBinding
    from cew_b01.pdf_probe import probe_pdf
    from cew_b01.primitive_census import _analysis_binary, _confirmed_analysis_mask
    from cew_b01.source_contract import load_source_contract, materialize_source
    from cew_b01.zone_review_package import confirmed_zones_from_receipt, zone_set_digest
    from experiments.cew_col02.footprint_proposals import extract_footprint_proposals

    runner_temp = Path(os.environ["RUNNER_TEMP"])
    contract = load_source_contract("governance/cew-b01/N12_TAV5_SOURCE_v1.json")
    materialized = materialize_source(contract, ".", runner_temp / "tavola5-col02-whole-symbol-source.pdf")
    if materialized.sha256 != SOURCE_SHA256:
        raise ValueError("exact-source SHA drift")

    probe_dir = runner_temp / "cew-col02-whole-symbol-probe"
    probe = probe_pdf(materialized, probe_dir)
    raster_binding = Task3RasterBinding.from_probe_mapping(probe.to_mapping())
    raster_path = probe_dir / "tav5-page0-300dpi.png"
    proposed_zones = propose_document_zones(raster_binding, raster_path)
    zone_receipt = json.loads(Path("governance/cew-b01/TAV5_DOCUMENT_ZONE_REVIEW_v1.json").read_text(encoding="utf-8"))
    zones = confirmed_zones_from_receipt(raster_binding, proposed_zones, zone_receipt)
    if not all(zone.human_confirmed for zone in zones):
        raise ValueError("document zones are not all human-confirmed")
    if zone_set_digest(zones) != zone_receipt["zone_set_digest"]:
        raise ValueError("document-zone digest drift")

    image = cv2.imread(str(raster_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"cannot read exact-source raster {raster_path}")
    mask = _confirmed_analysis_mask(raster_binding, zones)
    analysis, _binary = _analysis_binary(image, mask)
    proposals_a = extract_footprint_proposals(analysis, max_candidates=6000)
    proposals_b = extract_footprint_proposals(analysis, max_candidates=6000)
    if canonical_bytes(proposals_a) != canonical_bytes(proposals_b):
        raise ValueError("neutral proposal replay is not deterministic")
    if int(proposals_a["candidate_count"]) != EXPECTED_PROPOSAL_COUNT:
        raise ValueError(
            f"neutral proposal count drift: expected {EXPECTED_PROPOSAL_COUNT}, got {proposals_a['candidate_count']}"
        )
    return image, analysis, proposals_a


def _context_bbox(seed: dict[str, float], repaired: dict[str, float] | None) -> dict[str, float]:
    boxes = [seed] if repaired is None else [seed, repaired]
    left = min(float(box["x"]) for box in boxes)
    top = min(float(box["y"]) for box in boxes)
    right = max(float(box["x"]) + float(box["width"]) for box in boxes)
    bottom = max(float(box["y"]) + float(box["height"]) for box in boxes)
    span = max(right - left, bottom - top)
    margin = max(0.008, span * 1.5)
    x1 = max(0.0, left - margin)
    y1 = max(0.0, top - margin)
    x2 = min(1.0, right + margin)
    y2 = min(1.0, bottom + margin)
    return {"x": x1, "y": y1, "width": x2 - x1, "height": y2 - y1}


def _pixels(box: dict[str, float], width: int, height: int) -> tuple[int, int, int, int]:
    x1 = max(0, min(width - 1, int(round(float(box["x"]) * width))))
    y1 = max(0, min(height - 1, int(round(float(box["y"]) * height))))
    x2 = max(x1 + 1, min(width, int(round((float(box["x"]) + float(box["width"])) * width))))
    y2 = max(y1 + 1, min(height, int(round((float(box["y"]) + float(box["height"])) * height))))
    return x1, y1, x2, y2


def _render_repair(image: np.ndarray, row: dict[str, Any]) -> tuple[dict[str, Any], np.ndarray]:
    height, width = image.shape[:2]
    seed = row["source_seed_bbox"]
    repaired = row["reconstructed_bbox"]
    context = _context_bbox(seed, repaired)
    left, top, right, bottom = _pixels(context, width, height)
    source = image[top:bottom, left:right].copy()
    overlay = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)

    sx1, sy1, sx2, sy2 = _pixels(seed, width, height)
    cv2.rectangle(
        overlay,
        (max(0, sx1 - left), max(0, sy1 - top)),
        (min(overlay.shape[1] - 1, sx2 - left), min(overlay.shape[0] - 1, sy2 - top)),
        (0, 140, 255),
        3,
    )
    if repaired is not None:
        rx1, ry1, rx2, ry2 = _pixels(repaired, width, height)
        cv2.rectangle(
            overlay,
            (max(0, rx1 - left), max(0, ry1 - top)),
            (min(overlay.shape[1] - 1, rx2 - left), min(overlay.shape[0] - 1, ry2 - top)),
            (0, 0, 255),
            4,
        )
        label = f"REPAIRED {row['repair_id']}"
    else:
        label = f"UNRESOLVED {row['repair_id']}"
    cv2.putText(overlay, label, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 255), 1, cv2.LINE_AA)

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    source_rel = f"axis-aware-whole-symbol-repair/{row['repair_id'].lower()}-source-only.png"
    overlay_rel = f"axis-aware-whole-symbol-repair/{row['repair_id'].lower()}-repair-overlay.png"
    assert cv2.imwrite(str(EVIDENCE_ROOT / source_rel), source)
    assert cv2.imwrite(str(EVIDENCE_ROOT / overlay_rel), overlay)

    rendered = dict(row)
    rendered["source_only_crop"] = source_rel
    rendered["overlay_crop"] = overlay_rel
    rendered["context_bbox"] = context

    source_bgr = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)
    pair = cv2.hconcat([source_bgr, overlay])
    header = np.full((92, pair.shape[1], 3), 255, dtype=np.uint8)
    cv2.putText(
        header,
        f"{row['repair_id']} | seed={row['source_candidate_id']} | {row['status']}",
        (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0), 1, cv2.LINE_AA,
    )
    cv2.putText(
        header,
        "ORANGE=old fragment | RED=axis-aware whole-symbol repair | graphical review only",
        (12, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 0), 1, cv2.LINE_AA,
    )
    return rendered, cv2.vconcat([header, pair])


def _pad(panel: np.ndarray, width: int) -> np.ndarray:
    if panel.shape[1] >= width:
        return panel
    return cv2.copyMakeBorder(panel, 0, 0, 0, width - panel.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255))


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    _validate_receipt_payload(receipt)

    image, analysis, proposals_payload = _regenerate_source_analysis_and_proposals()
    proposals = list(proposals_payload["candidates"])
    proposal_by_id = {row["candidate_id"]: row for row in proposals}

    repair_results: dict[str, dict[str, Any] | None] = {}
    for candidate_id in EXPECTED_REPAIR_TASKS.values():
        proposal = proposal_by_id.get(candidate_id)
        if proposal is None:
            raise ValueError(f"missing repair seed proposal: {candidate_id}")
        result = reconstruct_axis_split_whole_symbol(analysis, proposal["bbox"])
        if result is None:
            result = reconstruct_local_axis_envelope(analysis, proposal["bbox"])
        repair_results[candidate_id] = result

    source_replay_sha256 = hashlib.sha256(canonical_bytes(proposals_payload)).hexdigest()
    manifest = build_axis_aware_repair_manifest(
        receipt=receipt,
        proposals=proposals,
        repair_results=repair_results,
        source_replay_sha256=source_replay_sha256,
    )

    panels: list[np.ndarray] = []
    rendered_repairs: list[dict[str, Any]] = []
    for row in manifest["repairs"]:
        rendered, panel = _render_repair(image, row)
        rendered_repairs.append(rendered)
        panels.append(panel)
    manifest["repairs"] = rendered_repairs

    if panels:
        max_width = max(panel.shape[1] for panel in panels)
        atlas = cv2.vconcat([_pad(panel, max_width) for panel in panels])
        assert cv2.imwrite(str(ATLAS_PATH), atlas)

    replay_payload = dict(manifest)
    manifest["replay_sha256"] = hashlib.sha256(canonical_bytes(replay_payload)).hexdigest()
    OUTPUT_JSON.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR="
        + json.dumps(
            {
                "status": manifest["status"],
                "proposal_count": manifest["proposal_count"],
                "repair_candidate_count": manifest["repair_candidate_count"],
                "ready_for_human_review_count": manifest["ready_for_human_review_count"],
                "unresolved_repair_count": manifest["unresolved_repair_count"],
                "rejected_candidate_count": len(manifest["rejected_candidates"]),
                "occurrence_coverage_complete": manifest["occurrence_coverage_complete"],
                "replay_sha256": manifest["replay_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()