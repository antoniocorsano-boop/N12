from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from experiments.cew_col02.exact_source_audit import _bbox_pixels, canonical_bytes
from experiments.cew_col02.occurrence_sweep import visible_similarity_siblings


EVIDENCE_DIR = Path("evidence/cew-col02/footprint-text-binding")
SEARCH_PATH = EVIDENCE_DIR / "col02-prototype-guided-search.json"
AUDIT_PATH = EVIDENCE_DIR / "col02-audit.json"
HUMAN_REVIEW_PATH = Path("governance/cew-col02/COL02_PROTOTYPE_GUIDED_HUMAN_REVIEW_v1.json")


def _crop_bounds(box: dict[str, float], width: int, height: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = _bbox_pixels(box, width, height)
    span = max(right - left, bottom - top, 70)
    margin = max(120, int(round(span * 1.8)))
    return max(0, left - margin), max(0, top - margin), min(width, right + margin), min(height, bottom + margin)


def _normalized_crop(left: int, top: int, right: int, bottom: int, width: int, height: int) -> dict[str, float]:
    return {
        "x": left / width,
        "y": top / height,
        "width": (right - left) / width,
        "height": (bottom - top) / height,
    }


def _pad(panel: np.ndarray, width: int) -> np.ndarray:
    if panel.shape[1] >= width:
        return panel
    return cv2.copyMakeBorder(panel, 0, 0, 0, width - panel.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255))


def main() -> None:
    search = json.loads(SEARCH_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    human = json.loads(HUMAN_REVIEW_PATH.read_text(encoding="utf-8"))

    width = int(audit["source"]["raster_width_px"])
    height = int(audit["source"]["raster_height_px"])
    decisions = {item["panel_id"]: item for item in human["human_review"]["decisions"]}

    panels: list[np.ndarray] = []
    manifest: list[dict[str, Any]] = []
    sibling_ids: set[str] = set()

    for panel in search["review_panels"]:
        panel_id = panel["panel_id"]
        target_id = panel["candidate_id"]
        left, top, right, bottom = _crop_bounds(panel["bbox"], width, height)
        crop_bbox = _normalized_crop(left, top, right, bottom, width, height)
        siblings = visible_similarity_siblings(target_id, crop_bbox, search["search_results"])
        if not siblings:
            continue

        source_path = EVIDENCE_DIR / panel["source_only_crop"]
        source = cv2.imread(str(source_path), cv2.IMREAD_GRAYSCALE)
        if source is None:
            raise RuntimeError(f"cannot read source crop: {source_path}")
        overlay = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)

        tx1, ty1, tx2, ty2 = _bbox_pixels(panel["bbox"], width, height)
        cv2.rectangle(overlay, (tx1 - left, ty1 - top), (tx2 - left, ty2 - top), (0, 0, 255), 3)
        cv2.putText(overlay, f"TARGET {target_id}", (max(3, tx1 - left), max(18, ty1 - top - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1, cv2.LINE_AA)

        for sibling in siblings:
            sibling_id = sibling["occurrence_candidate_id"]
            sibling_ids.add(sibling_id)
            sx1, sy1, sx2, sy2 = _bbox_pixels(sibling["bbox"], width, height)
            cv2.rectangle(overlay, (sx1 - left, sy1 - top), (sx2 - left, sy2 - top), (0, 165, 255), 2)
            cv2.putText(overlay, sibling_id, (max(3, sx1 - left), max(16, sy1 - top - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (0, 120, 220), 1, cv2.LINE_AA)

        target_decision = decisions.get(panel_id, {}).get("graphical_decision", "UNKNOWN")
        source_bgr = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)
        pair = cv2.hconcat([source_bgr, overlay])
        header = np.full((92, pair.shape[1], 3), 255, dtype=np.uint8)
        cv2.putText(header, f"{panel_id} | target={target_id} | human={target_decision} | visible siblings={len(siblings)}", (12, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(header, "RED=already reviewed target | ORANGE=other similarity candidate visible in same crop; review orange candidates for missed columns", (12, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (0, 0, 0), 1, cv2.LINE_AA)
        panels.append(cv2.vconcat([header, pair]))

        manifest.append({
            "panel_id": panel_id,
            "target_candidate_id": target_id,
            "target_human_decision": target_decision,
            "visible_sibling_candidates": [
                {
                    "candidate_id": item["occurrence_candidate_id"],
                    "bbox": item["bbox"],
                    "score": item["score"],
                    "visible_fraction_in_crop": item["visible_fraction_in_crop"],
                    "column_graphic_decision": "PENDING_HUMAN_REVIEW"
                }
                for item in siblings
            ]
        })

    if panels:
        max_width = max(panel.shape[1] for panel in panels)
        atlas = cv2.vconcat([_pad(panel, max_width) for panel in panels])
    else:
        atlas = np.full((180, 1200, 3), 255, dtype=np.uint8)
        cv2.putText(atlas, "CEW-COL-02: no visible sibling similarity candidates in reviewed crops", (25, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2, cv2.LINE_AA)

    atlas_path = EVIDENCE_DIR / "col02-occurrence-completeness-sweep-atlas.png"
    assert cv2.imwrite(str(atlas_path), atlas)

    payload = {
        "schema_id": "CEW_COL02_OCCURRENCE_COMPLETENESS_SWEEP",
        "schema_version": 1,
        "status": "VISIBLE_SIBLING_OCCURRENCES_READY_FOR_HUMAN_REVIEW",
        "source_search_replay_sha256": search["replay_sha256"],
        "human_target_review_receipt": str(HUMAN_REVIEW_PATH),
        "human_target_review_status": human["status"],
        "panel_count_with_visible_siblings": len(manifest),
        "unique_visible_sibling_candidate_count": len(sibling_ids),
        "panels": manifest,
        "authority": {
            "sibling_graphical_review_authorized": True,
            "occurrence_coverage_complete": False,
            "support_identity_authorized": False,
            "text_identity_binding_authorized": False,
            "family_assignment_authorized": False,
            "section_assignment_authorized": False,
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "merge_authorized": False
        }
    }
    payload["replay_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    (EVIDENCE_DIR / "col02-occurrence-completeness-sweep.json").write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_COL02_OCCURRENCE_SWEEP=" + json.dumps({
        "status": payload["status"],
        "panel_count_with_visible_siblings": payload["panel_count_with_visible_siblings"],
        "unique_visible_sibling_candidate_count": payload["unique_visible_sibling_candidate_count"],
        "replay_sha256": payload["replay_sha256"]
    }, sort_keys=True))


if __name__ == "__main__":
    main()
