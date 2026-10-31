from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from experiments.cew_col02.exact_source_audit import (
    SOURCE_SHA256,
    _bbox_pixels,
    canonical_bytes,
)
from experiments.cew_col02.residual_occurrence_reconciliation import (
    HUMAN_REVIEW_BUNDLE_SHA256,
    _expanded_context_bbox,
    build_reconciliation_manifest,
)


EVIDENCE_ROOT = Path("evidence/cew-col02/footprint-text-binding")
REVIEW_PATH = Path("governance/cew-col02/COL02_RESIDUAL_MOBILE_HUMAN_REVIEW_v1.json")
OUTPUT_JSON = EVIDENCE_ROOT / "col02-residual-occurrence-reconciliation.json"
ASSET_DIR = EVIDENCE_ROOT / "residual-occurrence-reconciliation"
ATLAS_PATH = EVIDENCE_ROOT / "col02-residual-occurrence-reconciliation-atlas.png"
EXPECTED_PROPOSAL_COUNT = 611


def _context_pixels(box: dict[str, float], width: int, height: int) -> tuple[int, int, int, int]:
    left = max(0, min(width - 1, int(round(box["x"] * width))))
    top = max(0, min(height - 1, int(round(box["y"] * height))))
    right = max(left + 1, min(width, int(round((box["x"] + box["width"]) * width))))
    bottom = max(top + 1, min(height, int(round((box["y"] + box["height"]) * height))))
    return left, top, right, bottom


def _point_context(point: dict[str, float], width: int, height: int) -> dict[str, float]:
    radius_px = 360
    cx = int(round(point["x"] * width))
    cy = int(round(point["y"] * height))
    left = max(0, cx - radius_px)
    top = max(0, cy - radius_px)
    right = min(width, cx + radius_px)
    bottom = min(height, cy + radius_px)
    return {
        "x": left / width,
        "y": top / height,
        "width": max(1, right - left) / width,
        "height": max(1, bottom - top) / height,
    }


def _pad(panel: np.ndarray, width: int) -> np.ndarray:
    if panel.shape[1] >= width:
        return panel
    return cv2.copyMakeBorder(
        panel,
        0,
        0,
        0,
        width - panel.shape[1],
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )


def _render_task(
    image: np.ndarray,
    task: dict[str, Any],
    index: int,
) -> tuple[dict[str, Any], np.ndarray]:
    height, width = image.shape[:2]
    task_type = str(task["task_type"])

    target_bbox: dict[str, float] | None = None
    source_point: dict[str, float] | None = None
    if task_type == "REFRAME_CONFIRMATION":
        target_bbox = task["target_bbox"]
        context_bbox = task["context_bbox"]
        label = str(task["candidate_id"])
    elif task_type == "ADDITIONAL_OCCURRENCE_CONFIRMATION":
        target_bbox = task["proposal_bbox"]
        context_bbox = _expanded_context_bbox(
            target_bbox,
            source_width=width,
            source_height=height,
        )
        label = str(task["proposal_candidate_id"])
    elif task_type == "HUMAN_POINT_UNBOUND":
        source_point = task["source_point"]
        context_bbox = _point_context(source_point, width, height)
        label = str(task["event_id"])
    else:
        raise ValueError(f"unsupported review task type: {task_type}")

    left, top, right, bottom = _context_pixels(context_bbox, width, height)
    source_crop = image[top:bottom, left:right].copy()
    overlay = cv2.cvtColor(source_crop, cv2.COLOR_GRAY2BGR)

    if target_bbox is not None:
        x1, y1, x2, y2 = _bbox_pixels(target_bbox, width, height)
        cv2.rectangle(
            overlay,
            (max(0, x1 - left), max(0, y1 - top)),
            (min(overlay.shape[1] - 1, x2 - left), min(overlay.shape[0] - 1, y2 - top)),
            (0, 0, 255),
            4,
        )
        cv2.putText(
            overlay,
            f"TARGET {label}",
            (max(3, x1 - left), max(20, y1 - top - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )
    else:
        assert source_point is not None
        px = int(round(source_point["x"] * width)) - left
        py = int(round(source_point["y"] * height)) - top
        cv2.circle(overlay, (px, py), 18, (0, 140, 255), 3)
        cv2.line(overlay, (px - 28, py), (px + 28, py), (0, 140, 255), 2)
        cv2.line(overlay, (px, py - 28), (px, py + 28), (0, 140, 255), 2)
        cv2.putText(
            overlay,
            f"HUMAN POINT {label}",
            (max(3, px + 20), max(20, py - 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.44,
            (0, 140, 255),
            1,
            cv2.LINE_AA,
        )

    task_id = f"R{index:02d}"
    source_name = f"residual-occurrence-reconciliation/{task_id.lower()}-source-only.png"
    overlay_name = f"residual-occurrence-reconciliation/{task_id.lower()}-target-overlay.png"
    assert cv2.imwrite(str(EVIDENCE_ROOT / source_name), source_crop)
    assert cv2.imwrite(str(EVIDENCE_ROOT / overlay_name), overlay)

    rendered = dict(task)
    rendered.update(
        {
            "review_task_id": task_id,
            "source_only_crop": source_name,
            "overlay_crop": overlay_name,
            "context_bbox": context_bbox,
            "graphical_decision": "PENDING_HUMAN_REVIEW",
        }
    )

    source_bgr = cv2.cvtColor(source_crop, cv2.COLOR_GRAY2BGR)
    pair = cv2.hconcat([source_bgr, overlay])
    header = np.full((88, pair.shape[1], 3), 255, dtype=np.uint8)
    cv2.putText(
        header,
        f"{task_id} | {task_type} | {label}",
        (12, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        header,
        "LEFT=source only | RIGHT=target explicit | graphical occurrence review only",
        (12, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.38,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )
    return rendered, cv2.vconcat([header, pair])


def _regenerate_source_and_proposals() -> tuple[np.ndarray, list[dict[str, Any]]]:
    from cew_b01.document_zoning import propose_document_zones
    from cew_b01.evidence_schema import Task3RasterBinding
    from cew_b01.pdf_probe import probe_pdf
    from cew_b01.primitive_census import _analysis_binary, _confirmed_analysis_mask
    from cew_b01.source_contract import load_source_contract, materialize_source
    from cew_b01.zone_review_package import confirmed_zones_from_receipt, zone_set_digest
    from experiments.cew_col02.footprint_proposals import extract_footprint_proposals

    runner_temp = Path(os.environ["RUNNER_TEMP"])
    contract = load_source_contract("governance/cew-b01/N12_TAV5_SOURCE_v1.json")
    materialized = materialize_source(contract, ".", runner_temp / "tavola5-col02-reconciliation-source.pdf")
    if materialized.sha256 != SOURCE_SHA256:
        raise ValueError("exact-source SHA drift")

    probe_dir = runner_temp / "cew-col02-reconciliation-probe"
    probe = probe_pdf(materialized, probe_dir)
    raster_binding = Task3RasterBinding.from_probe_mapping(probe.to_mapping())
    raster_path = probe_dir / "tav5-page0-300dpi.png"
    proposed_zones = propose_document_zones(raster_binding, raster_path)
    zone_receipt = json.loads(
        Path("governance/cew-b01/TAV5_DOCUMENT_ZONE_REVIEW_v1.json").read_text(encoding="utf-8")
    )
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
    return image, list(proposals_a["candidates"])


def main() -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    review_bytes = REVIEW_PATH.read_bytes()
    review_sha = hashlib.sha256(review_bytes).hexdigest()
    if review_sha != HUMAN_REVIEW_BUNDLE_SHA256:
        raise ValueError(
            f"human review bundle digest drift: expected {HUMAN_REVIEW_BUNDLE_SHA256}, got {review_sha}"
        )
    review_bundle = json.loads(review_bytes.decode("utf-8"))

    audit = json.loads((EVIDENCE_ROOT / "col02-audit.json").read_text(encoding="utf-8"))
    search = json.loads((EVIDENCE_ROOT / "col02-prototype-guided-search.json").read_text(encoding="utf-8"))
    sweep = json.loads((EVIDENCE_ROOT / "col02-occurrence-completeness-sweep.json").read_text(encoding="utf-8"))

    image, proposals = _regenerate_source_and_proposals()
    manifest = build_reconciliation_manifest(
        review_bundle,
        search=search,
        sweep=sweep,
        audit=audit,
        proposals=proposals,
        human_review_bundle_sha256=review_sha,
    )

    rendered_tasks: list[dict[str, Any]] = []
    panels: list[np.ndarray] = []
    for index, task in enumerate(manifest["review_tasks"], start=1):
        rendered, panel = _render_task(image, task, index)
        rendered_tasks.append(rendered)
        panels.append(panel)
    manifest["review_tasks"] = rendered_tasks

    if panels:
        max_width = max(panel.shape[1] for panel in panels)
        atlas = cv2.vconcat([_pad(panel, max_width) for panel in panels])
    else:
        atlas = np.full((180, 1200, 3), 255, dtype=np.uint8)
        cv2.putText(
            atlas,
            "CEW-COL-02 residual occurrence reconciliation: no unresolved review tasks",
            (25, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )
    assert cv2.imwrite(str(ATLAS_PATH), atlas)

    replay_payload = dict(manifest)
    manifest["replay_sha256"] = hashlib.sha256(canonical_bytes(replay_payload)).hexdigest()
    OUTPUT_JSON.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    status_counts: dict[str, int] = {}
    for record in manifest["point_reconciliation"]:
        status = str(record["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
    print(
        "CEW_COL02_RESIDUAL_RECONCILIATION="
        + json.dumps(
            {
                "status": manifest["status"],
                "review_task_count": len(manifest["review_tasks"]),
                "reframe_task_count": len(manifest["reframe_tasks"]),
                "point_status_counts": status_counts,
                "proposal_count": len(proposals),
                "replay_sha256": manifest["replay_sha256"],
                "occurrence_coverage_complete": manifest["occurrence_coverage_complete"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
