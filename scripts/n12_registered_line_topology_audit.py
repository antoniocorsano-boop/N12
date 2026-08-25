#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from PIL import Image

from n12_registered_candidate_audit import (
    read_csv,
    registered_to_metric,
    review_to_registered_frame,
    select_registration,
)


def support_xy(path: Path, storey_id: str) -> dict[str, tuple[float, float]]:
    present_field = f"{storey_id.lower()}_present"
    out: dict[str, tuple[float, float]] = {}
    for row in read_csv(path):
        if row.get(present_field) != "PRESENT":
            continue
        out[row["support_id"]] = (float(row["x_global_m"]), float(row["y_global_m"]))
    if not out:
        raise ValueError(f"No {storey_id} supports found via {present_field}")
    return out


def straight_beams(path: Path, supports: dict[str, tuple[float, float]], storey_id: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in read_csv(path):
        if row.get("storey_id") != storey_id or row.get("direction_class") not in {"X", "Y"}:
            continue
        a_id, b_id = row["from_support_id"], row["to_support_id"]
        if a_id not in supports or b_id not in supports:
            continue
        out.append({"beam_id": row["beam_id"], "from": a_id, "to": b_id, "a": supports[a_id], "b": supports[b_id]})
    if not out:
        raise ValueError(f"No straight canonical beams found for {storey_id}")
    return out


def point_segment_distance(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    px, py = p; ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    den = dx * dx + dy * dy
    if den == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / den))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy)


def angle_difference_deg(a1: tuple[float, float], a2: tuple[float, float], b1: tuple[float, float], b2: tuple[float, float]) -> float:
    ux, uy = a2[0] - a1[0], a2[1] - a1[1]
    vx, vy = b2[0] - b1[0], b2[1] - b1[1]
    den = math.hypot(ux, uy) * math.hypot(vx, vy)
    if den == 0:
        return 90.0
    c = max(-1.0, min(1.0, abs((ux * vx + uy * vy) / den)))
    return math.degrees(math.acos(c))


def sample_segment(a: tuple[float, float], b: tuple[float, float], n: int = 81) -> list[tuple[float, float]]:
    return [(a[0] + (b[0] - a[0]) * i / (n - 1), a[1] + (b[1] - a[1]) * i / (n - 1)) for i in range(n)]


def line_metric_endpoints(row: dict[str, str], base: Image.Image, registration: dict[str, str]) -> tuple[tuple[float, float], tuple[float, float]]:
    fw, fh = float(registration["frame_width_px"]), float(registration["frame_height_px"])
    if row["orientation"] == "H":
        pts = [(float(row["start_px"]), float(row["coordinate_px"])), (float(row["end_px"]), float(row["coordinate_px"]))]
    else:
        pts = [(float(row["coordinate_px"]), float(row["start_px"])), (float(row["coordinate_px"]), float(row["end_px"]))]
    out = []
    for x, y in pts:
        u, v = review_to_registered_frame(x, y, base.width, base.height, fw, fh, registration["source_frame"])
        out.append(registered_to_metric(u, v, registration))
    return out[0], out[1]


def self_test() -> None:
    assert abs(point_segment_distance((0.5, 0.1), (0, 0), (1, 0)) - 0.1) < 1e-9
    assert angle_difference_deg((0, 0), (1, 0), (2, 0), (5, 0)) < 1e-9
    assert abs(angle_difference_deg((0, 0), (1, 0), (0, 0), (0, 1)) - 90.0) < 1e-9
    assert f"{'G2'.lower()}_present" == "g2_present"
    print("REGISTERED_LINE_TOPOLOGY_AUDIT_SELF_TEST_PASS")


def run(args: argparse.Namespace) -> int:
    root = Path(args.input_root) / args.source_id
    base = Image.open(root / "review_base.png")
    registration = select_registration(Path(args.registration_csv), args.source_id)
    if registration.get("level_id") != args.storey_id:
        raise ValueError(f"Registration {args.source_id} belongs to {registration.get('level_id')}, not {args.storey_id}")
    supports = support_xy(Path(args.supports_csv), args.storey_id)
    beams = straight_beams(Path(args.beams_csv), supports, args.storey_id)
    lines = read_csv(root / "consensus_lines.csv")

    rows: list[dict[str, object]] = []
    nearest_rows: list[dict[str, object]] = []
    for idx, line in enumerate(lines, start=1):
        p1, p2 = line_metric_endpoints(line, base, registration)
        samples = sample_segment(p1, p2)
        ranked = []
        for beam in beams:
            a, b = beam["a"], beam["b"]
            angle = angle_difference_deg(p1, p2, a, b)
            if angle > args.max_angle_deg:
                continue
            distances = [point_segment_distance(p, a, b) for p in samples]
            ranked.append((sum(distances) / len(distances), max(distances), min(distances), angle, beam))
        if not ranked:
            continue
        mean_d, max_d, min_d, angle, beam = min(ranked, key=lambda x: (x[0], x[1]))
        within = max_d <= args.max_distance_m
        diagnostic = {
            "line_id": f"L{idx:03d}",
            "orientation": line["orientation"],
            "detector_support_count": line["support_count"],
            "beam_id": beam["beam_id"],
            "from_support_id": beam["from"],
            "to_support_id": beam["to"],
            "angle_delta_deg": round(angle, 6),
            "min_distance_m": round(min_d, 6),
            "mean_distance_m": round(mean_d, 6),
            "max_distance_m": round(max_d, 6),
            "distance_gate_status": "WITHIN_REVIEW_GATE" if within else "OUTSIDE_REVIEW_GATE",
            "canonical_binding": "PROHIBITED",
            "epistemic_effect": "NONE",
        }
        nearest_rows.append(diagnostic)
        if not within:
            continue
        rows.append({**diagnostic, "review_status": "GEOMETRIC_REVIEW_CANDIDATE"})

    candidate_fields = ["line_id","orientation","detector_support_count","beam_id","from_support_id","to_support_id","angle_delta_deg","min_distance_m","mean_distance_m","max_distance_m","distance_gate_status","canonical_binding","epistemic_effect","review_status"]
    with (root / "registered_line_topology_candidates.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=candidate_fields); w.writeheader(); w.writerows(rows)

    nearest_fields = ["line_id","orientation","detector_support_count","beam_id","from_support_id","to_support_id","angle_delta_deg","min_distance_m","mean_distance_m","max_distance_m","distance_gate_status","canonical_binding","epistemic_effect"]
    with (root / "registered_line_topology_nearest.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=nearest_fields); w.writeheader(); w.writerows(nearest_rows)

    best_max = sorted(float(r["max_distance_m"]) for r in nearest_rows)
    best_mean = sorted(float(r["mean_distance_m"]) for r in nearest_rows)
    receipt = {
        "schema_version": "1.2",
        "experiment": "REGISTERED_CONSENSUS_LINE_TO_STOREY_TOPOLOGY_AUDIT",
        "source_id": args.source_id,
        "storey_id": args.storey_id,
        "registration_validation_state": registration["validation_state"],
        "straight_canonical_beams_compared": len(beams),
        "consensus_lines_compared": len(lines),
        "nearest_parallel_beam_diagnostics": len(nearest_rows),
        "geometric_review_candidates": len(rows),
        "best_parallel_distance_summary_m": {
            "minimum_mean": round(best_mean[0], 6) if best_mean else None,
            "minimum_max": round(best_max[0], 6) if best_max else None,
            "median_mean": round(best_mean[len(best_mean)//2], 6) if best_mean else None,
            "median_max": round(best_max[len(best_max)//2], 6) if best_max else None,
        },
        "parameters": {"max_angle_deg": args.max_angle_deg, "max_distance_m": args.max_distance_m},
        "gate": "LINE_TOPOLOGY_REVIEW_CANDIDATES_READY",
        "canonical_binding": "PROHIBITED",
        "epistemic_effect": "NONE",
        "promotion_prohibited": True,
    }
    (root / "registered_line_topology_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare registered consensus lines with existing straight storey beam topology for review only.")
    p.add_argument("--input-root", default="analysis/raster_line_concordance")
    p.add_argument("--source-id", default="TAV-06S")
    p.add_argument("--storey-id", default="G5")
    p.add_argument("--registration-csv", default="data/canonical/STOREY_SUPPORT_XY_REGISTRATION_v1.csv")
    p.add_argument("--supports-csv", default="data/canonical/VERTICAL_SUPPORT_LINES_CURRENT_v1.csv")
    p.add_argument("--beams-csv", default="data/canonical/STOREY_BEAMS_G5_v1.csv")
    p.add_argument("--max-angle-deg", type=float, default=2.0)
    p.add_argument("--max-distance-m", type=float, default=0.35)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    ns = parse_args()
    if ns.self_test:
        self_test(); raise SystemExit(0)
    raise SystemExit(run(ns))
