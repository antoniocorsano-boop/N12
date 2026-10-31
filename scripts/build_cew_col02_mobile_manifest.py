#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any


def _as_float(value: Any, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc


def _bbox_pixels(box: dict[str, Any], width: int, height: int) -> tuple[int, int, int, int]:
    x = _as_float(box.get("x"), "bbox.x")
    y = _as_float(box.get("y"), "bbox.y")
    w = _as_float(box.get("width"), "bbox.width")
    h = _as_float(box.get("height"), "bbox.height")
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
        raise ValueError(f"invalid normalized bbox: {box}")
    left = max(0, min(width, int(round(x * width))))
    top = max(0, min(height, int(round(y * height))))
    right = max(left + 1, min(width, int(round((x + w) * width))))
    bottom = max(top + 1, min(height, int(round((y + h) * height))))
    return left, top, right, bottom


def _crop_bounds(box: dict[str, Any], width: int, height: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = _bbox_pixels(box, width, height)
    span = max(right - left, bottom - top, 70)
    margin = max(120, int(round(span * 1.8)))
    return max(0, left - margin), max(0, top - margin), min(width, right + margin), min(height, bottom + margin)


def select_residual_occurrences(search: dict, sweep: dict) -> list[dict[str, Any]]:
    """Select one explicit visual occurrence for every sibling not already reviewed as S01-S24 target.

    Candidate order follows first occurrence in the sweep. If the same residual is visible in
    multiple reviewed crops, the occurrence with the largest visible fraction is used; score and
    panel id are deterministic tie-breakers. No semantic or structural identity is inferred.
    """
    review_panels = search.get("review_panels")
    sweep_panels = sweep.get("panels")
    if not isinstance(review_panels, list) or not review_panels:
        raise ValueError("search.review_panels must be non-empty")
    if not isinstance(sweep_panels, list) or not sweep_panels:
        raise ValueError("sweep.panels must be non-empty")

    reviewed_targets = {str(panel.get("candidate_id") or "").strip() for panel in review_panels}
    reviewed_targets.discard("")
    search_panel_ids = {str(panel.get("panel_id") or "").strip() for panel in review_panels}

    first_order: dict[str, int] = {}
    best: dict[str, dict[str, Any]] = {}
    sequence = 0

    for panel in sweep_panels:
        panel_id = str(panel.get("panel_id") or "").strip()
        context_target_id = str(panel.get("target_candidate_id") or "").strip()
        if not panel_id or panel_id not in search_panel_ids:
            raise ValueError(f"sweep panel has no matching search review panel: {panel_id!r}")
        if not context_target_id:
            raise ValueError(f"missing target_candidate_id for sweep panel {panel_id}")
        siblings = panel.get("visible_sibling_candidates")
        if not isinstance(siblings, list):
            raise ValueError(f"visible_sibling_candidates must be a list for {panel_id}")

        for sibling in siblings:
            candidate_id = str(sibling.get("candidate_id") or "").strip()
            if not candidate_id or candidate_id in reviewed_targets:
                continue
            bbox = sibling.get("bbox")
            if not isinstance(bbox, dict):
                raise ValueError(f"missing bbox for residual {candidate_id}")
            visible_fraction = _as_float(sibling.get("visible_fraction_in_crop"), "visible_fraction_in_crop")
            score = _as_float(sibling.get("score", 0.0), "score")
            if not (0.0 < visible_fraction <= 1.0):
                raise ValueError(f"invalid visible fraction for {candidate_id}: {visible_fraction}")

            if candidate_id not in first_order:
                first_order[candidate_id] = sequence
                sequence += 1

            record = {
                "candidate_id": candidate_id,
                "source_panel_id": panel_id,
                "context_target_candidate_id": context_target_id,
                "target_bbox": dict(bbox),
                "score": score,
                "visible_fraction_in_crop": visible_fraction,
            }
            current = best.get(candidate_id)
            if current is None:
                best[candidate_id] = record
                continue
            current_key = (
                float(current["visible_fraction_in_crop"]),
                float(current["score"]),
                str(current["source_panel_id"]),
            )
            record_key = (visible_fraction, score, panel_id)
            if record_key > current_key:
                best[candidate_id] = record

    return [best[candidate_id] for candidate_id, _ in sorted(first_order.items(), key=lambda item: item[1])]


def _png_data_uri(image: Any) -> str:
    import cv2

    ok, encoded = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    if not ok:
        raise RuntimeError("cannot encode review image as PNG")
    return "data:image/png;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")


def _candidate_images(
    evidence_root: Path,
    search_panel: dict[str, Any],
    residual: dict[str, Any],
    width: int,
    height: int,
) -> tuple[str, str]:
    import cv2

    source_path = evidence_root / str(search_panel["source_only_crop"])
    source = cv2.imread(str(source_path), cv2.IMREAD_GRAYSCALE)
    if source is None:
        raise RuntimeError(f"cannot read source-only review crop: {source_path}")

    crop_left, crop_top, crop_right, crop_bottom = _crop_bounds(search_panel["bbox"], width, height)
    expected_width = crop_right - crop_left
    expected_height = crop_bottom - crop_top
    if source.shape[1] != expected_width or source.shape[0] != expected_height:
        raise RuntimeError(
            f"crop geometry mismatch for {search_panel['panel_id']}: "
            f"expected {expected_width}x{expected_height}, got {source.shape[1]}x{source.shape[0]}"
        )

    overlay = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)
    left, top, right, bottom = _bbox_pixels(residual["target_bbox"], width, height)
    x1 = max(0, min(source.shape[1] - 1, left - crop_left))
    y1 = max(0, min(source.shape[0] - 1, top - crop_top))
    x2 = max(x1 + 1, min(source.shape[1] - 1, right - crop_left))
    y2 = max(y1 + 1, min(source.shape[0] - 1, bottom - crop_top))
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 255), 4)
    label_y = max(20, y1 - 8)
    cv2.putText(
        overlay,
        f"TARGET {residual['candidate_id']}",
        (max(3, x1), label_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (0, 0, 255),
        1,
        cv2.LINE_AA,
    )
    return _png_data_uri(source), _png_data_uri(overlay)


def build_manifest(
    evidence_root: Path,
    *,
    producer_sha: str,
) -> dict[str, Any]:
    search_path = evidence_root / "col02-prototype-guided-search.json"
    sweep_path = evidence_root / "col02-occurrence-completeness-sweep.json"
    audit_path = evidence_root / "col02-audit.json"
    search = json.loads(search_path.read_text(encoding="utf-8"))
    sweep = json.loads(sweep_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    if sweep.get("source_search_replay_sha256") != search.get("replay_sha256"):
        raise ValueError("COL-02 search/sweep replay lineage mismatch")
    if sweep.get("status") != "VISIBLE_SIBLING_OCCURRENCES_READY_FOR_HUMAN_REVIEW":
        raise ValueError(f"unexpected COL-02 sweep status: {sweep.get('status')}")

    source = search.get("source")
    if not isinstance(source, dict):
        raise ValueError("COL-02 search source metadata missing")
    width = int(audit["source"]["raster_width_px"])
    height = int(audit["source"]["raster_height_px"])
    if width <= 0 or height <= 0:
        raise ValueError("invalid COL-02 audit raster dimensions")

    residuals = select_residual_occurrences(search, sweep)
    if not residuals:
        raise ValueError("COL-02 sweep contains no residual candidates")
    panels_by_id = {str(panel["panel_id"]): panel for panel in search["review_panels"]}

    candidates: list[dict[str, Any]] = []
    for residual in residuals:
        panel = panels_by_id[residual["source_panel_id"]]
        source_uri, overlay_uri = _candidate_images(evidence_root, panel, residual, width, height)
        candidate_id = residual["candidate_id"]
        candidates.append(
            {
                "candidate_id": candidate_id,
                "image_uri": source_uri,
                "overlay_image_uri": overlay_uri,
                "prompt": (
                    f"Valuta solo il riquadro rosso {candidate_id}. "
                    "La scelta riguarda la presenza grafica di un pilastro; non assegna numero, sezione o identità strutturale."
                ),
                "target": {
                    "candidate_id": candidate_id,
                    "bbox": residual["target_bbox"],
                    "source_panel_id": residual["source_panel_id"],
                    "context_target_candidate_id": residual["context_target_candidate_id"],
                    "visible_fraction_in_crop": residual["visible_fraction_in_crop"],
                    "similarity_score": residual["score"],
                },
            }
        )

    source_version_id = str(source.get("source_version_id") or source.get("path") or "TAV5").strip()
    return {
        "schema_version": "cew-mobile-candidate-review-v1",
        "review_id": "CEW-COL02-VISIBLE-SIBLING-RESIDUAL-MOBILE-v1",
        "source": {
            "source_id": f"CEW-COL02:{source_version_id}",
            "authority": "EXACT_SOURCE_DERIVED_HUMAN_GRAPHICAL_REVIEW_ONLY",
            "producer_exact_sha": producer_sha,
            "source_version_id": source.get("source_version_id"),
            "page_id": source.get("page_id"),
            "page_transform_id": source.get("page_transform_id"),
            "source_sha256": source.get("sha256"),
            "source_path": source.get("path"),
            "source_commit": source.get("commit"),
            "prototype_guided_replay_sha256": search.get("replay_sha256"),
            "occurrence_sweep_replay_sha256": sweep.get("replay_sha256"),
            "residual_candidate_count": len(candidates),
        },
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--producer-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    producer_sha = str(args.producer_sha).strip()
    if len(producer_sha) != 40 or any(ch not in "0123456789abcdef" for ch in producer_sha.lower()):
        raise ValueError("producer-sha must be a full 40-character Git SHA")

    manifest = build_manifest(args.evidence_root, producer_sha=producer_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "CEW_COL02_MOBILE_MANIFEST="
        + json.dumps(
            {
                "review_id": manifest["review_id"],
                "candidate_count": len(manifest["candidates"]),
                "candidate_ids": [item["candidate_id"] for item in manifest["candidates"]],
                "producer_exact_sha": producer_sha,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
