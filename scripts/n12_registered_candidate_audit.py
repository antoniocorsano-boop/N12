#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from PIL import Image


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def select_registration(path: Path, sheet_id: str) -> dict[str, str]:
    rows = [r for r in read_csv(path) if r.get("sheet_id") == sheet_id]
    if len(rows) != 1:
        raise ValueError(f"Expected one registration row for {sheet_id}, found {len(rows)}")
    row = rows[0]
    if row.get("validation_state") != "CROSS_VALIDATED":
        raise ValueError(f"Registration for {sheet_id} is not CROSS_VALIDATED")
    return row


def review_to_registered_frame(
    x_px: float,
    y_px: float,
    review_width: int,
    review_height: int,
    frame_width: float,
    frame_height: float,
    source_frame: str,
) -> tuple[float, float]:
    if source_frame != "ROT90_CCW_300DPI":
        raise ValueError(f"Unsupported registered source frame: {source_frame}")
    # Continuous image-coordinate convention: review render is the same source in
    # portrait orientation; canonical registration uses the 90° CCW frame.
    # After CCW rotation: u'=y, v'=W-x. Scale normalized coordinates to the
    # registered 300 dpi frame. No metric information is introduced here.
    u = (y_px / review_height) * frame_width
    v = ((review_width - x_px) / review_width) * frame_height
    return u, v


def registered_to_metric(u: float, v: float, r: dict[str, str]) -> tuple[float, float]:
    x = float(r["metric_x_from_u"]) * u + float(r["metric_x_from_v"]) * v + float(r["metric_x_offset"])
    y = float(r["metric_y_from_u"]) * u + float(r["metric_y_from_v"]) * v + float(r["metric_y_offset"])
    return x, y


def g5_supports(path: Path) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in read_csv(path):
        if row.get("level_id") != "G5" or row.get("node_role") != "SUPPORT_CORE" or not row.get("support_id"):
            continue
        out.append({
            "support_id": row["support_id"],
            "x_m": float(row["x_m"]),
            "y_m": float(row["y_m"]),
            "coordinate_evidence_state": row.get("coordinate_evidence_state", ""),
            "xy_input_provenance": row.get("xy_input_provenance", ""),
        })
    if not out:
        raise ValueError("No G5 SUPPORT_CORE rows found")
    return out


def self_test() -> None:
    u, v = review_to_registered_frame(25.0, 50.0, 100, 200, 1000.0, 500.0, "ROT90_CCW_300DPI")
    assert abs(u - 250.0) < 1e-9
    assert abs(v - 375.0) < 1e-9
    r = {
        "metric_x_from_u": "1", "metric_x_from_v": "0", "metric_x_offset": "2",
        "metric_y_from_u": "0", "metric_y_from_v": "1", "metric_y_offset": "3",
    }
    x, y = registered_to_metric(u, v, r)
    assert (x, y) == (252.0, 378.0)
    print("REGISTERED_CANDIDATE_AUDIT_SELF_TEST_PASS")


def run(args: argparse.Namespace) -> int:
    root = Path(args.input_root)
    source_dir = root / args.source_id
    intersections = read_csv(source_dir / "consensus_intersections.csv")
    candidate_index = int(args.candidate_id.removeprefix("I")) - 1
    if candidate_index < 0 or candidate_index >= len(intersections):
        raise ValueError(f"Candidate {args.candidate_id} not found for {args.source_id}")
    candidate = intersections[candidate_index]

    base = Image.open(source_dir / "review_base.png")
    registration = select_registration(Path(args.registration_csv), args.source_id)
    frame_width = float(registration["frame_width_px"])
    frame_height = float(registration["frame_height_px"])
    x_review = float(candidate["x_px"])
    y_review = float(candidate["y_px"])
    u, v = review_to_registered_frame(
        x_review, y_review, base.width, base.height,
        frame_width, frame_height, registration["source_frame"],
    )
    x_m, y_m = registered_to_metric(u, v, registration)

    supports = g5_supports(Path(args.nodes_csv))
    ranked = sorted(
        (
            math.hypot(x_m - float(s["x_m"]), y_m - float(s["y_m"])),
            s,
        )
        for s in supports
    )
    nearest_distance, nearest = ranked[0]

    audit = {
        "schema_version": "1.0",
        "experiment": "REGISTERED_RASTER_CANDIDATE_TO_CANONICAL_XY_AUDIT",
        "source_id": args.source_id,
        "candidate_id": args.candidate_id,
        "candidate_kind": "CONSENSUS_INTERSECTION_VISUALLY_PLAUSIBLE_MAIN_PLAN",
        "review_frame": {
            "width_px": base.width,
            "height_px": base.height,
            "x_px": round(x_review, 4),
            "y_px": round(y_review, 4),
        },
        "registered_frame": {
            "source_frame": registration["source_frame"],
            "width_px": frame_width,
            "height_px": frame_height,
            "u_px": round(u, 4),
            "v_px": round(v, 4),
            "registration_method": registration["registration_method"],
            "registration_validation_state": registration["validation_state"],
            "registration_evidence_state": registration["evidence_state"],
        },
        "metric_projection": {
            "x_m": round(x_m, 6),
            "y_m": round(y_m, 6),
            "state": "EXPERIMENTAL_PROJECTION_FROM_CROSS_VALIDATED_REGISTRATION",
            "canonical_write_prohibited": True,
        },
        "nearest_g5_support": {
            "support_id": nearest["support_id"],
            "x_m": nearest["x_m"],
            "y_m": nearest["y_m"],
            "distance_m": round(nearest_distance, 6),
            "coordinate_evidence_state": nearest["coordinate_evidence_state"],
            "xy_input_provenance": nearest["xy_input_provenance"],
        },
        "binding_status": "NO_AUTOMATIC_SUPPORT_BINDING",
        "binding_reason": "Candidate is an image-line intersection, not a support observation. Nearest-support distance is reported only as audit information; no capture radius or snapping threshold is introduced.",
        "gate": "REGISTERED_POSITION_AUDITED_NO_SUPPORT_BINDING",
        "epistemic_effect": "NONE",
        "promotion_prohibited": True,
    }
    (source_dir / "registered_candidate_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    with (source_dir / "registered_candidate_audit.csv").open("w", newline="", encoding="utf-8") as fh:
        fields = ["source_id", "candidate_id", "review_x_px", "review_y_px", "registered_u_px", "registered_v_px", "projected_x_m", "projected_y_m", "nearest_support_id", "nearest_support_distance_m", "binding_status", "epistemic_effect"]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "source_id": args.source_id,
            "candidate_id": args.candidate_id,
            "review_x_px": round(x_review, 4),
            "review_y_px": round(y_review, 4),
            "registered_u_px": round(u, 4),
            "registered_v_px": round(v, 4),
            "projected_x_m": round(x_m, 6),
            "projected_y_m": round(y_m, 6),
            "nearest_support_id": nearest["support_id"],
            "nearest_support_distance_m": round(nearest_distance, 6),
            "binding_status": audit["binding_status"],
            "epistemic_effect": "NONE",
        })
    print(json.dumps(audit, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Audit a visually retained TAV-06S raster candidate against the existing cross-validated common XY registration.")
    p.add_argument("--input-root", default="analysis/raster_line_concordance")
    p.add_argument("--source-id", default="TAV-06S")
    p.add_argument("--candidate-id", default="I001")
    p.add_argument("--registration-csv", default="data/canonical/STOREY_SUPPORT_XY_REGISTRATION_v1.csv")
    p.add_argument("--nodes-csv", default="data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv")
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    ns = parse_args()
    if ns.self_test:
        self_test()
        raise SystemExit(0)
    raise SystemExit(run(ns))
