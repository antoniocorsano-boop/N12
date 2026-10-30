from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2

DOUBLE = "RECT_PLUS_DOUBLE_TRANSVERSE_BAND"


def _major_axis(geometry: dict[str, Any]) -> str:
    width = float(geometry["width"])
    height = float(geometry["height"])
    if width > height:
        return "HORIZONTAL"
    if height > width:
        return "VERTICAL"
    return "SQUARE_OR_UNRESOLVED"


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
        raise ValueError("BEAM_TYPE_APPROVAL_EMPTY_CROP")
    return crop


def export_double_candidates(result_path: Path, raster_path: Path, out_dir: Path) -> dict[str, Any]:
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    image = cv2.imread(str(raster_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("BEAM_TYPE_APPROVAL_RASTER_UNREADABLE")
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = [
        record
        for record in payload["records"]
        if record["transverse_band"]["graphical_state"] == DOUBLE
    ]
    candidates.sort(key=lambda item: item["marker_primitive_id"])
    if len(candidates) != int(payload["transverse_band_counts"][DOUBLE]):
        raise ValueError("BEAM_TYPE_APPROVAL_DOUBLE_COUNT_MISMATCH")

    manifest_candidates: list[dict[str, Any]] = []
    panels: list[Any] = []
    for index, record in enumerate(candidates, start=1):
        geometry = dict(record["review_marker_geometry"])
        marker_id = str(record["marker_primitive_id"])
        major_axis = _major_axis(geometry)
        filename = f"double-{index:02d}-{marker_id}.png"
        crop = _crop_source_only(image, geometry)
        if not cv2.imwrite(str(out_dir / filename), crop):
            raise ValueError("BEAM_TYPE_APPROVAL_CROP_WRITE_FAILED")

        header = 56
        panel = cv2.copyMakeBorder(
            crop,
            header,
            0,
            0,
            0,
            cv2.BORDER_CONSTANT,
            value=255,
        )
        cv2.putText(
            panel,
            f"D{index:02d} {marker_id} major={major_axis} carrier={record['carrier_orientation']}",
            (10, 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.46,
            0,
            1,
            cv2.LINE_AA,
        )
        panels.append(panel)

        band = record["transverse_band"]
        manifest_candidates.append(
            {
                "panel_id": f"D{index:02d}",
                "marker_primitive_id": marker_id,
                "source_crop": filename,
                "major_axis_orientation": major_axis,
                "carrier_orientation": record["carrier_orientation"],
                "source_marker_geometry": record["source_marker_geometry"],
                "review_marker_geometry": geometry,
                "carrier_id": record["carrier_id"],
                "carrier_track_ids": record["carrier_track_ids"],
                "topology_state": record["carrier_topology"]["topology_state"],
                "cross_axis_side_labels": [
                    band["negative_side_label"],
                    band["positive_side_label"],
                ],
                "cross_axis_side_counts": [
                    band["negative_side_count"],
                    band["positive_side_count"],
                ],
                "matched_cross_side_pair_count": band["matched_cross_side_pair_count"],
                "evidence_sources": band["evidence_sources"],
                "proposed_type": "PENDING_HUMAN_TYPE_REVIEW",
                "human_decision": "PENDING_HUMAN_REVIEW",
            }
        )

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
        for panel in panels
    ]
    atlas = cv2.vconcat(padded)
    if not cv2.imwrite(str(out_dir / "double-candidates-source-only-atlas.png"), atlas):
        raise ValueError("BEAM_TYPE_APPROVAL_ATLAS_WRITE_FAILED")

    manifest = {
        "schema_id": "CEW_B01_BEAM_TYPE_APPROVAL_SOURCE_ONLY_CANDIDATES",
        "schema_version": 1,
        "status": "HUMAN_TYPE_SELECTION_PENDING",
        "source_sha256": payload["source_sha256"],
        "page_index": payload["page_index"],
        "double_candidate_count": len(manifest_candidates),
        "candidates": manifest_candidates,
        "authority": {
            "graphical_type_approved": False,
            "semantic_classification_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "g2c_promotion_authorized": False,
            "g3_authorized": False,
            "merge_authorized": False,
        },
    }
    (out_dir / "double-candidates-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--raster", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = export_double_candidates(args.result, args.raster, args.out)
    print(
        "BEAM_TYPE_APPROVAL_EXPORT="
        + json.dumps(
            {
                "status": manifest["status"],
                "double_candidate_count": manifest["double_candidate_count"],
                "semantic_authority": False,
                "g3_authorized": False,
                "merge_authorized": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
