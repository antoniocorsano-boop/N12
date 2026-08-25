#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def line_endpoints(row: dict[str, str]) -> tuple[tuple[float, float], tuple[float, float]]:
    orientation = row["orientation"]
    c = float(row["coordinate_px"])
    start = float(row["start_px"])
    end = float(row["end_px"])
    if orientation == "H":
        return (start, c), (end, c)
    if orientation == "V":
        return (c, start), (c, end)
    raise ValueError(f"Unsupported orientation: {orientation}")


def write_review_register(path: Path, source_id: str, lines: list[dict[str, str]], intersections: list[dict[str, str]]) -> None:
    fields = ["source_id", "candidate_id", "candidate_type", "orientation", "x_px", "y_px", "start_px", "end_px", "support_count", "mean_detector_delta_px", "review_status", "canonical_match", "review_note"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for idx, row in enumerate(lines, start=1):
            orientation = row["orientation"]
            writer.writerow({
                "source_id": source_id,
                "candidate_id": f"L{idx:03d}",
                "candidate_type": "CONSENSUS_LINE",
                "orientation": orientation,
                "x_px": row["coordinate_px"] if orientation == "V" else "",
                "y_px": row["coordinate_px"] if orientation == "H" else "",
                "start_px": row["start_px"],
                "end_px": row["end_px"],
                "support_count": row["support_count"],
                "mean_detector_delta_px": row["mean_coordinate_delta_px"],
                "review_status": "UNREVIEWED",
                "canonical_match": "",
                "review_note": "",
            })
        for idx, row in enumerate(intersections, start=1):
            writer.writerow({
                "source_id": source_id,
                "candidate_id": f"I{idx:03d}",
                "candidate_type": "CONSENSUS_INTERSECTION",
                "orientation": "HV",
                "x_px": row["x_px"],
                "y_px": row["y_px"],
                "start_px": "",
                "end_px": "",
                "support_count": row["min_support_count"],
                "mean_detector_delta_px": row["mean_detector_delta_px"],
                "review_status": "UNREVIEWED",
                "canonical_match": "",
                "review_note": "",
            })


def render_overlay(source_dir: Path) -> dict:
    source_id = source_dir.name
    base = Image.open(source_dir / "review_base.png").convert("RGB")
    lines = read_csv(source_dir / "consensus_lines.csv")
    points = read_csv(source_dir / "consensus_intersections.csv")
    overlay = base.copy()
    draw = ImageDraw.Draw(overlay)
    line_width = max(2, round(max(base.size) / 700))
    radius = max(8, round(max(base.size) / 180))
    font = load_font(max(12, round(max(base.size) / 150)))

    for idx, row in enumerate(lines, start=1):
        p0, p1 = line_endpoints(row)
        draw.line([p0, p1], fill=(220, 20, 60), width=line_width)
        label = f"L{idx:03d}"
        x = min(p0[0], p1[0]) + 3
        y = min(p0[1], p1[1]) + 3
        draw.rectangle([x - 2, y - 2, x + 7 * len(label) + 3, y + 16], fill=(255, 255, 255))
        draw.text((x, y), label, fill=(0, 0, 0), font=font)

    for idx, row in enumerate(points, start=1):
        x = float(row["x_px"])
        y = float(row["y_px"])
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=(0, 70, 210), width=max(3, line_width))
        label = f"I{idx:03d}"
        draw.rectangle([x + radius + 2, y - 10, x + radius + 7 * len(label) + 10, y + 10], fill=(255, 255, 255))
        draw.text((x + radius + 4, y - 8), label, fill=(0, 0, 0), font=font)

    overlay.save(source_dir / "consensus_review_overlay.png")
    write_review_register(source_dir / "review_candidates.csv", source_id, lines, points)
    summary = {
        "source_id": source_id,
        "base_render": "review_base.png",
        "overlay": "consensus_review_overlay.png",
        "consensus_lines": len(lines),
        "consensus_intersections": len(points),
        "review_register": "review_candidates.csv",
        "review_status": "UNREVIEWED",
        "epistemic_effect": "NONE",
        "promotion_prohibited": True,
        "gate": "VISUAL_REVIEW_PACKAGE_READY",
    }
    (source_dir / "visual_review_receipt.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def self_test() -> None:
    row_h = {"orientation": "H", "coordinate_px": "50", "start_px": "10", "end_px": "90"}
    row_v = {"orientation": "V", "coordinate_px": "30", "start_px": "20", "end_px": "80"}
    assert line_endpoints(row_h) == ((10.0, 50.0), (90.0, 50.0))
    assert line_endpoints(row_v) == ((30.0, 20.0), (30.0, 80.0))
    print("CONSENSUS_REVIEW_OVERLAY_SELF_TEST_PASS")


def run(args: argparse.Namespace) -> int:
    root = Path(args.input_root)
    summaries = []
    for source_dir in sorted(x for x in root.iterdir() if x.is_dir()):
        required = [source_dir / "review_base.png", source_dir / "consensus_lines.csv", source_dir / "consensus_intersections.csv"]
        if not all(path.exists() for path in required):
            continue
        summaries.append(render_overlay(source_dir))
    batch = {
        "schema_version": "1.0",
        "gate": "VISUAL_REVIEW_PACKAGE_READY",
        "sources": summaries,
        "epistemic_effect": "NONE",
        "promotion_prohibited": True,
    }
    (root / "visual_review_batch_receipt.json").write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(batch, indent=2))
    return 0 if summaries else 2


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create non-canonical visual review overlays for consensus lines and intersections.")
    p.add_argument("--input-root", default="analysis/raster_line_concordance")
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    ns = parse_args()
    if ns.self_test:
        self_test()
        raise SystemExit(0)
    raise SystemExit(run(ns))