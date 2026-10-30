from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import cv2

from cew_b01.document_zoning import propose_document_zones
from cew_b01.evidence_schema import Task3RasterBinding
from cew_b01.pdf_probe import probe_pdf
from cew_b01.primitive_census import (
    _analysis_binary,
    _confirmed_analysis_mask,
    extract_neutral_primitives,
)
from cew_b01.source_contract import load_source_contract, materialize_source
from cew_b01.zone_review_package import confirmed_zones_from_receipt, zone_set_digest
from experiments.cew_b01.beam_hosted_markers import build_line_tracks
from experiments.cew_b01.hosted_marker_occurrence_search import analyze_hosted_marker_occurrences
from experiments.cew_b01.marker_topology_repair import (
    describe_carrier_topology,
    refine_marker_grounding,
)
from experiments.cew_b01.marker_transverse_cross_axis import describe_transverse_band

SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
C5 = "CEW-B01-GP-90cefb124e0b97a63acd1d9c"
C7 = "CEW-B01-GP-f5bf9ee85705380152aae053"
A10 = "CEW-B01-GP-cf4860204d8bb1c826d35f40"
A17 = "CEW-B01-GP-8b7eae9c9f25bb1d73c6f504"
LEGACY_DOUBLE = "CEW-B01-GP-185b1f5d7a45a56581f5998b"
ALONE = "RECT_ALONE_ON_CARRIER"
DOUBLE = "RECT_PLUS_DOUBLE_TRANSVERSE_BAND"


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _build_records(
    primitives: list[dict[str, Any]], binary_bool: Any
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    parent = analyze_hosted_marker_occurrences(primitives, binary_bool)
    review = parent["review_eligible"]
    rejected = parent["annotation_dominated"]
    assert len(parent["all_bound"]) == 50
    assert len(review) == 46
    assert len(rejected) == 4

    tracks = build_line_tracks(primitives)
    assert len(tracks) == 158
    records: list[dict[str, Any]] = []
    for candidate in review:
        grounded = refine_marker_grounding(candidate, binary_bool)
        topology = describe_carrier_topology(grounded, tracks)
        band = describe_transverse_band(grounded, tracks, binary_bool)
        records.append(
            {
                "marker_primitive_id": candidate["marker_primitive_id"],
                "candidate_role": candidate["candidate_role"],
                "parent_graphical_state": candidate["graphical_state"],
                "carrier_id": candidate["carrier_id"],
                "carrier_orientation": candidate["carrier_orientation"],
                "carrier_track_ids": candidate["carrier_track_ids"],
                "source_marker_geometry": grounded["source_marker_geometry"],
                "review_marker_geometry": grounded["review_marker_geometry"],
                "marker_grounding": grounded["marker_grounding"],
                "carrier_topology": topology,
                "transverse_band": band,
                "semantic_meaning": None,
                "structural_identity_authorized": False,
                "canonical_write_authorized": False,
                "g2c_promotion_authorized": False,
                "g3_authorized": False,
                "merge_authorized": False,
            }
        )
    records.sort(key=lambda item: item["marker_primitive_id"])
    controls = sorted(
        [
            {
                "marker_primitive_id": item["marker_primitive_id"],
                "candidate_role": item["candidate_role"],
                "marker_geometry": item["marker_geometry"],
                "annotation_evidence": item["annotation_evidence"],
            }
            for item in rejected
        ],
        key=lambda item: item["marker_primitive_id"],
    )
    return {"records": records, "annotation_controls": controls}, tracks


def _track_map(tracks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(track["track_id"]): track for track in tracks}


def _draw_track(
    crop: Any,
    track: dict[str, Any],
    left: int,
    top: int,
    colour: tuple[int, int, int],
    thickness: int = 2,
) -> None:
    if track["orientation"] == "HORIZONTAL":
        y = int(round(float(track["centerline"]))) - top
        x0 = int(round(float(track["start"]))) - left
        x1 = int(round(float(track["end"]))) - left
        if 0 <= y < crop.shape[0]:
            cv2.line(
                crop,
                (max(0, x0), y),
                (min(crop.shape[1] - 1, x1), y),
                colour,
                thickness,
            )
    else:
        x = int(round(float(track["centerline"]))) - left
        y0 = int(round(float(track["start"]))) - top
        y1 = int(round(float(track["end"]))) - top
        if 0 <= x < crop.shape[1]:
            cv2.line(
                crop,
                (x, max(0, y0)),
                (x, min(crop.shape[0] - 1, y1)),
                colour,
                thickness,
            )


def _review_panel(
    image: Any,
    record: dict[str, Any],
    tracks: list[dict[str, Any]],
    index: int,
) -> Any:
    colour = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    review = record["review_marker_geometry"]
    cx = float(review["x"]) + float(review["width"]) / 2.0
    cy = float(review["y"]) + float(review["height"]) / 2.0
    margin_x, margin_y = 280, 240
    left = max(0, int(round(cx - margin_x)))
    right = min(colour.shape[1], int(round(cx + margin_x)))
    top = max(0, int(round(cy - margin_y)))
    bottom = min(colour.shape[0], int(round(cy + margin_y)))
    crop = colour[top:bottom, left:right].copy()

    x0 = int(round(float(review["x"]))) - left
    y0 = int(round(float(review["y"]))) - top
    x1 = int(round(float(review["x"]) + float(review["width"]))) - left
    y1 = int(round(float(review["y"]) + float(review["height"]))) - top
    cv2.rectangle(crop, (x0, y0), (x1, y1), (0, 0, 255), 3)

    by_track = _track_map(tracks)
    for track_id in record["carrier_track_ids"]:
        track = by_track.get(str(track_id))
        if track:
            _draw_track(crop, track, left, top, (0, 150, 0), 2)

    band = record["transverse_band"]
    primitive_ids = sorted(
        set(
            band["primitive_negative_track_ids"]
            + band["primitive_positive_track_ids"]
        )
    )
    for track_id in primitive_ids:
        track = by_track.get(str(track_id))
        if track:
            _draw_track(crop, track, left, top, (180, 0, 180), 2)

    carrier_tracks = [
        by_track[str(track_id)]
        for track_id in record["carrier_track_ids"]
        if str(track_id) in by_track
    ]
    centers = sorted(float(track["centerline"]) for track in carrier_tracks)
    if centers:
        cross_lo, cross_hi = centers[0], centers[-1]
        depth = float(band["cross_side_depth_px"])
        raster_strokes = [
            (stroke, "NEG") for stroke in band["raster_negative_strokes"]
        ] + [(stroke, "POS") for stroke in band["raster_positive_strokes"]]
        for stroke, side in raster_strokes:
            position = float(stroke["centerline"])
            if record["carrier_orientation"] == "HORIZONTAL":
                x = int(round(position)) - left
                ya, yb = (
                    (cross_lo - depth, cross_lo - 1.0)
                    if side == "NEG"
                    else (cross_hi + 1.0, cross_hi + depth)
                )
                if 0 <= x < crop.shape[1]:
                    cv2.line(
                        crop,
                        (x, max(0, int(round(ya)) - top)),
                        (x, min(crop.shape[0] - 1, int(round(yb)) - top)),
                        (255, 0, 0),
                        3,
                    )
            else:
                y = int(round(position)) - top
                xa, xb = (
                    (cross_lo - depth, cross_lo - 1.0)
                    if side == "NEG"
                    else (cross_hi + 1.0, cross_hi + depth)
                )
                if 0 <= y < crop.shape[0]:
                    cv2.line(
                        crop,
                        (max(0, int(round(xa)) - left), y),
                        (min(crop.shape[1] - 1, int(round(xb)) - left), y),
                        (255, 0, 0),
                        3,
                    )

    title = (
        f"M{index:02d} {record['carrier_topology']['topology_state']} "
        f"{band['graphical_state']} "
        f"{band['negative_side_label']}={band['negative_side_count']} "
        f"{band['positive_side_label']}={band['positive_side_count']} "
        f"matched={band['matched_cross_side_pair_count']} "
        f"{record['marker_primitive_id']}"
    )
    crop = cv2.copyMakeBorder(
        crop, 65, 0, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255)
    )
    cv2.putText(
        crop,
        title,
        (10, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.44,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )
    return crop


def main() -> None:
    runner_temp = Path(os.environ["RUNNER_TEMP"])
    out = Path("evidence/cew-b01/marker-cross-axis-repair")
    out.mkdir(parents=True, exist_ok=True)

    contract = load_source_contract("governance/cew-b01/N12_TAV5_SOURCE_v1.json")
    materialized = materialize_source(
        contract, ".", runner_temp / "tavola5-marker-cross-axis-source.pdf"
    )
    assert materialized.sha256 == SOURCE_SHA256

    probe_dir = runner_temp / "cew-b01-marker-cross-axis-probe"
    probe = probe_pdf(materialized, probe_dir)
    binding = Task3RasterBinding.from_probe_mapping(probe.to_mapping())
    raster_path = probe_dir / "tav5-page0-300dpi.png"

    proposed_zones = propose_document_zones(binding, raster_path)
    zone_receipt = json.loads(
        Path("governance/cew-b01/TAV5_DOCUMENT_ZONE_REVIEW_v1.json").read_text(
            encoding="utf-8"
        )
    )
    zones = confirmed_zones_from_receipt(binding, proposed_zones, zone_receipt)
    assert all(zone.human_confirmed for zone in zones)
    assert zone_set_digest(zones) == zone_receipt["zone_set_digest"]

    primitives_a = [
        item.to_mapping()
        for item in extract_neutral_primitives(binding, raster_path, zones)
    ]
    primitives_b = [
        item.to_mapping()
        for item in extract_neutral_primitives(binding, raster_path, zones)
    ]
    assert canonical_bytes(primitives_a) == canonical_bytes(primitives_b)
    assert len(primitives_a) == 5633
    axis_line_count = sum(
        item.get("family") == "LINE_SEGMENT"
        and item.get("feature_signature", {}).get("orientation")
        in {"HORIZONTAL", "VERTICAL"}
        for item in primitives_a
    )
    assert axis_line_count == 733

    image = cv2.imread(str(raster_path), cv2.IMREAD_GRAYSCALE)
    assert image is not None
    mask = _confirmed_analysis_mask(binding, zones)
    _analysis, binary = _analysis_binary(image, mask)
    binary_bool = binary > 0

    repaired_a, tracks_a = _build_records(primitives_a, binary_bool)
    repaired_b, _tracks_b = _build_records(primitives_b, binary_bool)
    assert canonical_bytes(repaired_a) == canonical_bytes(repaired_b)

    records = repaired_a["records"]
    by_id = {item["marker_primitive_id"]: item for item in records}
    assert C5 in by_id and C7 in by_id
    assert by_id[C5]["transverse_band"]["graphical_state"] == ALONE, by_id[C5]
    assert A10 not in by_id and A17 not in by_id

    for item in records:
        assert item["semantic_meaning"] is None
        assert item["structural_identity_authorized"] is False
        assert item["canonical_write_authorized"] is False
        assert item["g2c_promotion_authorized"] is False
        assert item["g3_authorized"] is False
        assert item["merge_authorized"] is False
        assert item["transverse_band"]["side_reference"] == "CARRIER_CROSS_AXIS"

    topology_counts = Counter(
        item["carrier_topology"]["topology_state"] for item in records
    )
    band_counts = Counter(item["transverse_band"]["graphical_state"] for item in records)
    grounding_counts = Counter(item["marker_grounding"]["method"] for item in records)

    selected_ids: list[str] = []

    def add(marker_id: str) -> None:
        if marker_id in by_id and marker_id not in selected_ids and len(selected_ids) < 10:
            selected_ids.append(marker_id)

    add(C5)
    add(C7)
    add(LEGACY_DOUBLE)
    for item in records:
        if item["transverse_band"]["graphical_state"] == DOUBLE:
            add(item["marker_primitive_id"])
    for item in sorted(
        records,
        key=lambda value: (
            -int(value["transverse_band"]["matched_cross_side_pair_count"]),
            value["marker_primitive_id"],
        ),
    ):
        add(item["marker_primitive_id"])

    payload = {
        "schema_id": "CEW_B01_MARKER_CROSS_AXIS_REPAIR_EXACT_SOURCE",
        "schema_version": 1,
        "status": (
            "GRAPHICAL_REPAIR_CANDIDATE_HUMAN_REVIEW_PENDING"
            if by_id[C7]["transverse_band"]["graphical_state"] == DOUBLE
            else "REWORK_C7_CROSS_AXIS_SIGNATURE"
        ),
        "source_sha256": materialized.sha256,
        "page_index": contract.page_index,
        "primitive_count": len(primitives_a),
        "axis_line_segment_count": axis_line_count,
        "review_eligible_input_count": len(records),
        "annotation_control_count": len(repaired_a["annotation_controls"]),
        "topology_counts": dict(sorted(topology_counts.items())),
        "transverse_band_counts": dict(sorted(band_counts.items())),
        "grounding_method_counts": dict(sorted(grounding_counts.items())),
        "selected_review_marker_ids": selected_ids,
        "c5": by_id[C5],
        "c7": by_id[C7],
        "legacy_double_marker": by_id.get(LEGACY_DOUBLE),
        "records": records,
        "annotation_controls": repaired_a["annotation_controls"],
        "authority": {
            "semantic_classification_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "g2c_promotion_authorized": False,
            "g3_authorized": False,
            "merge_authorized": False,
        },
    }
    digest = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    payload["replay_sha256"] = digest
    (out / "marker-cross-axis-repair.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    panels = [
        _review_panel(image, by_id[marker_id], tracks_a, index + 1)
        for index, marker_id in enumerate(selected_ids)
    ]
    max_width = max(panel.shape[1] for panel in panels)
    padded = [
        cv2.copyMakeBorder(
            panel,
            0,
            0,
            0,
            max_width - panel.shape[1],
            cv2.BORDER_CONSTANT,
            value=(255, 255, 255),
        )
        if panel.shape[1] < max_width
        else panel
        for panel in panels
    ]
    atlas = cv2.vconcat(padded)
    assert cv2.imwrite(str(out / "marker-cross-axis-repair-atlas.png"), atlas)

    c7_band = by_id[C7]["transverse_band"]
    legacy = by_id.get(LEGACY_DOUBLE)
    summary = {
        "status": payload["status"],
        "primitive_count": payload["primitive_count"],
        "review_eligible_input_count": payload["review_eligible_input_count"],
        "topology_counts": payload["topology_counts"],
        "transverse_band_counts": payload["transverse_band_counts"],
        "grounding_method_counts": payload["grounding_method_counts"],
        "c5_band_state": by_id[C5]["transverse_band"]["graphical_state"],
        "c7_band_state": c7_band["graphical_state"],
        "c7_side_labels": [
            c7_band["negative_side_label"],
            c7_band["positive_side_label"],
        ],
        "c7_side_counts": [
            c7_band["negative_side_count"],
            c7_band["positive_side_count"],
        ],
        "c7_matched_cross_side_pair_count": c7_band[
            "matched_cross_side_pair_count"
        ],
        "legacy_double_new_state": (
            None if legacy is None else legacy["transverse_band"]["graphical_state"]
        ),
        "replay_sha256": digest,
        "semantic_authority": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }
    print("MARKER_CROSS_AXIS_REPAIR=" + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
