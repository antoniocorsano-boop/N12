#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image

from n12_registered_candidate_audit import read_csv, select_registration
from n12_registered_line_topology_audit import (
    angle_difference_deg,
    line_metric_endpoints,
    point_segment_distance,
    sample_segment,
    straight_beams,
    support_xy,
)


def self_test() -> None:
    beams = [
        {"beam_id": "B1", "from": "1", "to": "2", "a": (0.0, 0.0), "b": (1.0, 0.0)},
        {"beam_id": "B2", "from": "2", "to": "3", "a": (1.0, 0.0), "b": (2.0, 0.0)},
    ]
    p1, p2 = (0.1, 0.05), (1.9, 0.05)
    samples = sample_segment(p1, p2, 21)
    eligible = [b for b in beams if angle_difference_deg(p1, p2, b["a"], b["b"]) <= 2.0]
    nearest = [min(point_segment_distance(p, b["a"], b["b"]) for b in eligible) for p in samples]
    assert max(nearest) < 0.051
    print("REGISTERED_LINE_NETWORK_AUDIT_SELF_TEST_PASS")


def run(args: argparse.Namespace) -> int:
    root = Path(args.input_root) / args.source_id
    base = Image.open(root / "review_base.png")
    registration = select_registration(Path(args.registration_csv), args.source_id)
    if registration.get("level_id") != args.storey_id:
        raise ValueError(f"Registration {args.source_id} belongs to {registration.get('level_id')}, not {args.storey_id}")
    supports = support_xy(Path(args.supports_csv), args.storey_id)
    beams = straight_beams(Path(args.beams_csv), supports, args.storey_id)
    lines = read_csv(root / "consensus_lines.csv")

    diagnostics: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    for idx, line in enumerate(lines, start=1):
        p1, p2 = line_metric_endpoints(line, base, registration)
        eligible = [b for b in beams if angle_difference_deg(p1, p2, b["a"], b["b"]) <= args.max_angle_deg]
        if not eligible:
            continue
        samples = sample_segment(p1, p2)
        nearest_distances: list[float] = []
        nearest_beam_ids: list[str] = []
        for p in samples:
            ranked = sorted((point_segment_distance(p, b["a"], b["b"]), b) for b in eligible)
            d, b = ranked[0]
            nearest_distances.append(d)
            nearest_beam_ids.append(str(b["beam_id"]))
        min_d = min(nearest_distances)
        mean_d = sum(nearest_distances) / len(nearest_distances)
        max_d = max(nearest_distances)
        within = max_d <= args.max_distance_m
        supporting_beams = []
        for bid in nearest_beam_ids:
            if bid not in supporting_beams:
                supporting_beams.append(bid)
        row = {
            "line_id": f"L{idx:03d}",
            "orientation": line["orientation"],
            "detector_support_count": line["support_count"],
            "supporting_beam_count": len(supporting_beams),
            "supporting_beam_ids": ";".join(supporting_beams),
            "min_network_distance_m": round(min_d, 6),
            "mean_network_distance_m": round(mean_d, 6),
            "max_network_distance_m": round(max_d, 6),
            "network_gate_status": "WITHIN_REVIEW_GATE" if within else "OUTSIDE_REVIEW_GATE",
            "canonical_binding": "PROHIBITED",
            "epistemic_effect": "NONE",
        }
        diagnostics.append(row)
        if within:
            candidates.append({**row, "review_status": "NETWORK_GEOMETRIC_REVIEW_CANDIDATE"})

    diagnostic_fields = ["line_id","orientation","detector_support_count","supporting_beam_count","supporting_beam_ids","min_network_distance_m","mean_network_distance_m","max_network_distance_m","network_gate_status","canonical_binding","epistemic_effect"]
    with (root / "registered_line_network_diagnostics.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=diagnostic_fields); w.writeheader(); w.writerows(diagnostics)

    candidate_fields = diagnostic_fields + ["review_status"]
    with (root / "registered_line_network_candidates.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=candidate_fields); w.writeheader(); w.writerows(candidates)

    max_values = sorted(float(r["max_network_distance_m"]) for r in diagnostics)
    mean_values = sorted(float(r["mean_network_distance_m"]) for r in diagnostics)
    receipt = {
        "schema_version": "1.0",
        "experiment": "REGISTERED_CONSENSUS_LINE_TO_STOREY_BEAM_NETWORK_AUDIT",
        "source_id": args.source_id,
        "storey_id": args.storey_id,
        "registration_validation_state": registration["validation_state"],
        "straight_canonical_beams_in_network": len(beams),
        "consensus_lines_compared": len(lines),
        "network_diagnostics": len(diagnostics),
        "network_review_candidates": len(candidates),
        "best_network_distance_summary_m": {
            "minimum_mean": round(mean_values[0], 6) if mean_values else None,
            "minimum_max": round(max_values[0], 6) if max_values else None,
            "median_mean": round(mean_values[len(mean_values)//2], 6) if mean_values else None,
            "median_max": round(max_values[len(max_values)//2], 6) if max_values else None,
        },
        "parameters": {"max_angle_deg": args.max_angle_deg, "max_distance_m": args.max_distance_m},
        "gate": "LINE_NETWORK_REVIEW_CANDIDATES_READY",
        "canonical_binding": "PROHIBITED",
        "epistemic_effect": "NONE",
        "promotion_prohibited": True,
    }
    (root / "registered_line_network_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare registered consensus lines against the union of parallel canonical beam spans for review only.")
    p.add_argument("--input-root", default="analysis/raster_line_concordance")
    p.add_argument("--source-id", required=True)
    p.add_argument("--storey-id", required=True)
    p.add_argument("--registration-csv", default="data/canonical/STOREY_SUPPORT_XY_REGISTRATION_v1.csv")
    p.add_argument("--supports-csv", default="data/canonical/VERTICAL_SUPPORT_LINES_CURRENT_v1.csv")
    p.add_argument("--beams-csv", required=True)
    p.add_argument("--max-angle-deg", type=float, default=2.0)
    p.add_argument("--max-distance-m", type=float, default=0.35)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    ns = parse_args()
    if ns.self_test:
        self_test(); raise SystemExit(0)
    raise SystemExit(run(ns))
