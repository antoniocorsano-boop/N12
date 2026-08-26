#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConsensusLine:
    orientation: str
    coordinate: float
    start: float
    end: float
    support_count: int
    mean_coordinate_delta_px: float
    mean_overlap_ratio: float

    @property
    def length(self) -> float:
        return self.end - self.start


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_consensus_candidates(root: Path) -> list[dict]:
    lsd = read_csv(root / "opencv_lsd_segments.csv")
    hough = read_csv(root / "skimage_hough_segments.csv")
    matches = read_csv(root / "matches.csv")
    out: list[dict] = []
    for row in matches:
        a = lsd[int(row["lsd_index"])]
        b = hough[int(row["hough_index"])]
        orientation = a["orientation"]
        if orientation != b["orientation"]:
            raise ValueError("Matched detector segments disagree on orientation")
        if orientation == "H":
            ca = (float(a["y1"]) + float(a["y2"])) / 2
            cb = (float(b["y1"]) + float(b["y2"])) / 2
            sa, ea = sorted((float(a["x1"]), float(a["x2"])))
            sb, eb = sorted((float(b["x1"]), float(b["x2"])))
        else:
            ca = (float(a["x1"]) + float(a["x2"])) / 2
            cb = (float(b["x1"]) + float(b["x2"])) / 2
            sa, ea = sorted((float(a["y1"]), float(a["y2"])))
            sb, eb = sorted((float(b["y1"]), float(b["y2"])))
        out.append({
            "orientation": orientation,
            "coordinate": (ca + cb) / 2,
            "start": max(sa, sb),
            "end": min(ea, eb),
            "coordinate_delta_px": float(row["coordinate_delta_px"]),
            "overlap_ratio": float(row["overlap_ratio"]),
        })
    return [x for x in out if x["end"] > x["start"]]


def overlap_or_gap(a0: float, a1: float, b0: float, b1: float) -> float:
    if min(a1, b1) >= max(a0, b0):
        return 0.0
    return max(a0, b0) - min(a1, b1)


def cluster_candidates(candidates: list[dict], coordinate_tolerance_px: float, join_gap_px: float) -> list[ConsensusLine]:
    groups: list[list[dict]] = []
    for cand in sorted(candidates, key=lambda x: (x["orientation"], x["coordinate"], x["start"])):
        placed = False
        for group in groups:
            if group[0]["orientation"] != cand["orientation"]:
                continue
            coord = sum(x["coordinate"] for x in group) / len(group)
            start = min(x["start"] for x in group)
            end = max(x["end"] for x in group)
            if abs(coord - cand["coordinate"]) <= coordinate_tolerance_px and overlap_or_gap(start, end, cand["start"], cand["end"]) <= join_gap_px:
                group.append(cand)
                placed = True
                break
        if not placed:
            groups.append([cand])

    out: list[ConsensusLine] = []
    for group in groups:
        weights = [max(1.0, x["end"] - x["start"]) for x in group]
        total = sum(weights)
        coord = sum(x["coordinate"] * w for x, w in zip(group, weights)) / total
        out.append(ConsensusLine(
            orientation=group[0]["orientation"],
            coordinate=coord,
            start=min(x["start"] for x in group),
            end=max(x["end"] for x in group),
            support_count=len(group),
            mean_coordinate_delta_px=sum(x["coordinate_delta_px"] for x in group) / len(group),
            mean_overlap_ratio=sum(x["overlap_ratio"] for x in group) / len(group),
        ))
    return sorted(out, key=lambda x: (x.orientation, x.coordinate, x.start))


def intersections(lines: list[ConsensusLine], endpoint_slack_px: float) -> list[dict]:
    hs = [(i, x) for i, x in enumerate(lines) if x.orientation == "H"]
    vs = [(i, x) for i, x in enumerate(lines) if x.orientation == "V"]
    out: list[dict] = []
    for hi, h in hs:
        for vi, v in vs:
            x, y = v.coordinate, h.coordinate
            if h.start - endpoint_slack_px <= x <= h.end + endpoint_slack_px and v.start - endpoint_slack_px <= y <= v.end + endpoint_slack_px:
                out.append({
                    "x_px": round(x, 4),
                    "y_px": round(y, 4),
                    "horizontal_line_index": hi,
                    "vertical_line_index": vi,
                    "horizontal_support_count": h.support_count,
                    "vertical_support_count": v.support_count,
                    "min_support_count": min(h.support_count, v.support_count),
                    "mean_detector_delta_px": round((h.mean_coordinate_delta_px + v.mean_coordinate_delta_px) / 2, 4),
                })
    return out


def write_lines(path: Path, lines: list[ConsensusLine]) -> None:
    fields = ["orientation", "coordinate_px", "start_px", "end_px", "length_px", "support_count", "mean_coordinate_delta_px", "mean_overlap_ratio"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for line in lines:
            writer.writerow({
                "orientation": line.orientation,
                "coordinate_px": round(line.coordinate, 4),
                "start_px": round(line.start, 4),
                "end_px": round(line.end, 4),
                "length_px": round(line.length, 4),
                "support_count": line.support_count,
                "mean_coordinate_delta_px": round(line.mean_coordinate_delta_px, 4),
                "mean_overlap_ratio": round(line.mean_overlap_ratio, 6),
            })


def write_intersections(path: Path, rows: list[dict]) -> None:
    fields = ["x_px", "y_px", "horizontal_line_index", "vertical_line_index", "horizontal_support_count", "vertical_support_count", "min_support_count", "mean_detector_delta_px"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def self_test() -> None:
    rows = [
        {"orientation": "H", "coordinate": 100.0, "start": 10.0, "end": 200.0, "coordinate_delta_px": 1.0, "overlap_ratio": 0.9},
        {"orientation": "H", "coordinate": 102.0, "start": 180.0, "end": 300.0, "coordinate_delta_px": 2.0, "overlap_ratio": 0.8},
        {"orientation": "V", "coordinate": 150.0, "start": 20.0, "end": 250.0, "coordinate_delta_px": 1.5, "overlap_ratio": 0.85},
    ]
    lines = cluster_candidates(rows, 4.0, 25.0)
    assert len(lines) == 2
    pts = intersections(lines, 2.0)
    assert len(pts) == 1
    assert math.isclose(pts[0]["x_px"], 150.0, abs_tol=0.01)
    print("CONSENSUS_INTERSECTION_SELF_TEST_PASS")


def run(args: argparse.Namespace) -> int:
    root = Path(args.input_root)
    summaries = []
    for source_dir in sorted(x for x in root.iterdir() if x.is_dir()):
        candidates = load_consensus_candidates(source_dir)
        lines = cluster_candidates(candidates, args.cluster_coordinate_tolerance_px, args.join_gap_px)
        points = intersections(lines, args.endpoint_slack_px)
        write_lines(source_dir / "consensus_lines.csv", lines)
        write_intersections(source_dir / "consensus_intersections.csv", points)
        summary = {
            "source_id": source_dir.name,
            "matched_detector_pairs": len(candidates),
            "consensus_lines": len(lines),
            "horizontal_lines": sum(x.orientation == "H" for x in lines),
            "vertical_lines": sum(x.orientation == "V" for x in lines),
            "candidate_intersections": len(points),
            "parameters": {
                "cluster_coordinate_tolerance_px": args.cluster_coordinate_tolerance_px,
                "join_gap_px": args.join_gap_px,
                "endpoint_slack_px": args.endpoint_slack_px,
            },
            "epistemic_effect": "NONE",
            "promotion_prohibited": True,
            "gate": "CONSENSUS_CANDIDATES_READY_FOR_REVIEW",
        }
        (source_dir / "consensus_receipt.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        summaries.append(summary)
    batch = {"schema_version": "1.0", "gate": "CONSENSUS_CANDIDATES_READY_FOR_REVIEW", "sources": summaries, "epistemic_effect": "NONE", "promotion_prohibited": True}
    (root / "consensus_batch_receipt.json").write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(batch, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Cluster only cross-detector matched raster lines and derive H/V intersection candidates.")
    p.add_argument("--input-root", default="analysis/raster_line_concordance")
    p.add_argument("--cluster-coordinate-tolerance-px", type=float, default=4.0)
    p.add_argument("--join-gap-px", type=float, default=24.0)
    p.add_argument("--endpoint-slack-px", type=float, default=6.0)
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.self_test:
        self_test()
        raise SystemExit(0)
    raise SystemExit(run(args))
