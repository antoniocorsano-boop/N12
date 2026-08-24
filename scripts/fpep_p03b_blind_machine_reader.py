#!/usr/bin/env python3
"""Deterministic blind Reader B for FPEP P03B.

The program is intentionally conservative. It reads only the P01 source
identity, the P02 HiRes evidence manifest and raster files referenced by that
manifest. OCR tokens are observations with epistemic state INC. Raster line
primitives are MIS. Nothing is promoted to DOC and no structural topology is
constructed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

PIPELINE_ID = "N12_FPEP_FOUNDATION_PRIMARY_EVIDENCE_PIPELINE"
WORK_ITEM_ID = "FPEP-P03B-BLIND-READ-B"
AGENT_ROLE = "FOUNDATION_CARPENTRY_READER_B"
DEFAULT_TARGET = "analysis/fpep/FPEP_READER_B_OBSERVATIONS_v1.csv"
DEFAULT_RESULT = "automation/inbox/N12_FOUNDATION_AGENT_RESULT.json"

DECIMAL_RE = re.compile(r"^\d{1,3}[\.,]\d{1,3}$")
INTEGER_RE = re.compile(r"^\d{1,2}$")
LETTER_RE = re.compile(r"^[A-Za-z]$")
ALNUM_RE = re.compile(r"^[0-9A-Za-z]{1,4}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_token(text: str) -> str:
    value = text.strip()
    if DECIMAL_RE.fullmatch(value):
        return value.replace(",", ".")
    return value


def semantic_class(text: str) -> str | None:
    if DECIMAL_RE.fullmatch(text):
        return "DIMENSION_TEXT_CANDIDATE"
    if INTEGER_RE.fullmatch(text):
        return "INTEGER_LABEL_CANDIDATE"
    if LETTER_RE.fullmatch(text):
        return "LETTER_LABEL_CANDIDATE"
    if ALNUM_RE.fullmatch(text) and any(char.isdigit() for char in text):
        return "ALPHANUMERIC_LABEL_CANDIDATE"
    return None


def bbox_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    width, height = max(0, ix1 - ix0), max(0, iy1 - iy0)
    intersection = width * height
    if intersection <= 0:
        return 0.0
    area_a = max(1, (ax1 - ax0) * (ay1 - ay0))
    area_b = max(1, (bx1 - bx0) * (by1 - by0))
    return intersection / (area_a + area_b - intersection)


def tesseract_tsv(image_path: Path, psm: int) -> list[dict]:
    proc = subprocess.run(
        ["tesseract", str(image_path), "stdout", "--psm", str(psm), "-l", "eng", "tsv"],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"tesseract psm={psm} failed: {proc.stderr[:500]}")

    observations: list[dict] = []
    reader = csv.DictReader(proc.stdout.splitlines(), delimiter="\t")
    for row in reader:
        raw = (row.get("text") or "").strip()
        if not raw:
            continue
        try:
            confidence = float(row.get("conf", "-1"))
            left = int(row["left"])
            top = int(row["top"])
            width = int(row["width"])
            height = int(row["height"])
        except (ValueError, KeyError):
            continue
        if confidence < 35:
            continue
        value = normalize_token(raw)
        klass = semantic_class(value)
        if klass is None:
            continue
        observations.append(
            {
                "raw": value,
                "class": klass,
                "confidence": confidence,
                "bbox": (left, top, left + width, top + height),
                "psm": psm,
            }
        )
    return observations


def consensus_tokens(first: list[dict], second: list[dict]) -> list[dict]:
    matched_second: set[int] = set()
    output: list[dict] = []

    for item in first:
        best_index = None
        best_overlap = 0.0
        for index, candidate in enumerate(second):
            if index in matched_second or item["raw"] != candidate["raw"]:
                continue
            overlap = bbox_iou(item["bbox"], candidate["bbox"])
            if overlap > best_overlap:
                best_overlap = overlap
                best_index = index
        if best_index is not None and best_overlap >= 0.35:
            candidate = second[best_index]
            matched_second.add(best_index)
            bbox = tuple(round((a + b) / 2) for a, b in zip(item["bbox"], candidate["bbox"]))
            output.append(
                {
                    "raw": item["raw"],
                    "class": item["class"],
                    "bbox": bbox,
                    "confidence": round((item["confidence"] + candidate["confidence"]) / 2, 3),
                    "agreement": "PSM11_PSM12_MATCH",
                    "readability": "MACHINE_CONSENSUS_CANDIDATE",
                }
            )
        elif item["confidence"] >= 80:
            output.append(
                {
                    "raw": item["raw"],
                    "class": item["class"],
                    "bbox": item["bbox"],
                    "confidence": round(item["confidence"], 3),
                    "agreement": "PSM11_ONLY",
                    "readability": "HIGH_CONFIDENCE_SINGLE_PASS_CANDIDATE",
                }
            )

    for index, item in enumerate(second):
        if index not in matched_second and item["confidence"] >= 85:
            output.append(
                {
                    "raw": item["raw"],
                    "class": item["class"],
                    "bbox": item["bbox"],
                    "confidence": round(item["confidence"], 3),
                    "agreement": "PSM12_ONLY",
                    "readability": "HIGH_CONFIDENCE_SINGLE_PASS_CANDIDATE",
                }
            )

    deduplicated: list[dict] = []
    for item in sorted(output, key=lambda value: (value["bbox"][1], value["bbox"][0], value["raw"])):
        duplicate = any(
            item["raw"] == existing["raw"] and bbox_iou(item["bbox"], existing["bbox"]) >= 0.5
            for existing in deduplicated
        )
        if not duplicate:
            deduplicated.append(item)
    return deduplicated


def reconstruct_page(page: dict, root: Path, scale: float = 0.5):
    width = int(page["evidence_dpi_pixel_size"]["width"])
    height = int(page["evidence_dpi_pixel_size"]["height"])
    scaled_width = int(round(width * scale))
    scaled_height = int(round(height * scale))
    canvas = np.full((scaled_height, scaled_width), 255, dtype=np.uint8)

    for region in page["regions"]:
        path = root / region["path"]
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise RuntimeError(f"cannot read P02 region {path}")
        rectangle = region["source_rect_px"]
        x0, y0, x1, y1 = [int(rectangle[key]) for key in ("x0", "y0", "x1", "y1")]
        sx0, sy0, sx1, sy1 = [int(round(value * scale)) for value in (x0, y0, x1, y1)]
        resized = cv2.resize(image, (sx1 - sx0, sy1 - sy0), interpolation=cv2.INTER_AREA)
        canvas[sy0:sy1, sx0:sx1] = resized

    rotated = cv2.rotate(canvas, cv2.ROTATE_90_COUNTERCLOCKWISE)
    _, binary = cv2.threshold(rotated, 210, 255, cv2.THRESH_BINARY)
    return binary, scaled_width


def rotated_center_to_source(bbox: tuple[int, int, int, int], scale: float, scaled_width: int):
    x0, y0, x1, y1 = bbox
    rotated_x = (x0 + x1) / 2.0
    rotated_y = (y0 + y1) / 2.0
    source_y_scaled = rotated_x
    source_x_scaled = (scaled_width - 1) - rotated_y
    return source_x_scaled / scale, source_y_scaled / scale


def containing_tile(page: dict, source_x: float, source_y: float) -> str:
    candidates: list[tuple[int, str]] = []
    for tile in page["tiles"]:
        rectangle = tile["source_rect_px"]
        if (
            rectangle["x0"] <= source_x <= rectangle["x1"]
            and rectangle["y0"] <= source_y <= rectangle["y1"]
        ):
            area = (rectangle["x1"] - rectangle["x0"]) * (rectangle["y1"] - rectangle["y0"])
            candidates.append((area, tile["evidence_id"]))
    return min(candidates)[1] if candidates else "P001-OVERVIEW"


def line_primitives(gray: np.ndarray) -> list[tuple]:
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
    minimum_length = max(120, int(min(gray.shape[:2]) * 0.04))
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=100,
        minLineLength=minimum_length,
        maxLineGap=18,
    )
    if lines is None:
        return []

    candidates: list[tuple] = []
    for line in lines[:, 0, :]:
        x1, y1, x2, y2 = [int(value) for value in line]
        length = math.hypot(x2 - x1, y2 - y1)
        if length < minimum_length:
            continue
        angle = (math.degrees(math.atan2(y2 - y1, x2 - x1)) + 180) % 180
        horizontal_distance = min(abs(angle), abs(180 - angle))
        vertical_distance = abs(angle - 90)
        if min(horizontal_distance, vertical_distance) > 4.0:
            continue
        orientation = "H" if horizontal_distance <= vertical_distance else "V"
        candidates.append((length, orientation, x1, y1, x2, y2, angle))

    kept: list[tuple] = []
    for item in sorted(candidates, reverse=True):
        _, orientation, x1, y1, x2, y2, _ = item
        midpoint_x, midpoint_y = (x1 + x2) / 2, (y1 + y2) / 2
        duplicate = any(
            previous[1] == orientation
            and abs((previous[2] + previous[4]) / 2 - midpoint_x) < 20
            and abs((previous[3] + previous[5]) / 2 - midpoint_y) < 20
            for previous in kept
        )
        if duplicate:
            continue
        kept.append(item)
        if len(kept) >= 24:
            break
    return kept


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--identity", default="analysis/fpep/FPEP_SOURCE_IDENTITY_v1.json")
    parser.add_argument("--manifest", default="analysis/fpep/FPEP_HIRES_EVIDENCE_MANIFEST_v1.json")
    parser.add_argument("--output", default=DEFAULT_TARGET)
    parser.add_argument("--result", default=DEFAULT_RESULT)
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    identity_path = root / args.identity
    manifest_path = root / args.manifest
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if identity.get("source_identity", {}).get("source_id") != "TAV-01S":
        raise SystemExit("P03B requires P01 identity for TAV-01S")
    if manifest.get("work_item_id") != "FPEP-P02-HIRES-EVIDENCE":
        raise SystemExit("P03B requires the P02 HiRes evidence manifest")
    if len(manifest.get("pages", [])) != 1:
        raise SystemExit("P03B v1 expects exactly one P02 evidence page")

    page = manifest["pages"][0]
    accessed_paths = [args.identity, args.manifest]
    tile_hash_audit: list[dict] = []

    for tile in page["tiles"]:
        tile_path = root / tile["path"]
        actual = sha256_file(tile_path)
        if actual != tile["sha256"]:
            raise SystemExit(f"tile hash mismatch: {tile['evidence_id']}")
        accessed_paths.append(tile["path"])
        tile_hash_audit.append({"evidence_id": tile["evidence_id"], "sha256": actual})

    for region in page["regions"]:
        region_path = root / region["path"]
        actual = sha256_file(region_path)
        if actual != region["sha256"]:
            raise SystemExit(f"region hash mismatch: {region['evidence_id']}")
        accessed_paths.append(region["path"])

    scale = 0.5
    page_image, scaled_width = reconstruct_page(page, root, scale=scale)
    observations: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="fpep-p03b-") as temporary_directory:
        temporary_path = Path(temporary_directory) / "reader-b-page.png"
        if not cv2.imwrite(str(temporary_path), page_image):
            raise RuntimeError("failed to materialize temporary Reader B raster")
        first = tesseract_tsv(temporary_path, 11)
        second = tesseract_tsv(temporary_path, 12)
        for index, token in enumerate(consensus_tokens(first, second), start=1):
            source_x, source_y = rotated_center_to_source(token["bbox"], scale, scaled_width)
            anchor = containing_tile(page, source_x, source_y)
            x0, y0, x1, y1 = token["bbox"]
            observations.append(
                {
                    "obs_id": f"P03B-TXT-{index:03d}",
                    "source_id": "TAV-01S",
                    "evidence_anchor": anchor,
                    "semantic_class": token["class"],
                    "raw_value": token["raw"],
                    "unit": "ND",
                    "evidence_state": "INC",
                    "readability": token["readability"],
                    "method": "BLIND_MACHINE_OCR_TESSERACT_PSM11_PSM12",
                    "bbox_local_px": f"{x0},{y0},{x1},{y1}",
                    "confidence": f"{token['confidence']:.3f}",
                    "agreement": token["agreement"],
                    "note": "OCR candidate only; no structural relation or authority upgrade asserted.",
                }
            )

    line_index = 0
    for tile in page["tiles"]:
        image = cv2.imread(str(root / tile["path"]), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise RuntimeError(f"cannot read tile {tile['path']}")
        rotated = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        for length, orientation, x1, y1, x2, y2, angle in line_primitives(rotated):
            line_index += 1
            observations.append(
                {
                    "obs_id": f"P03B-LINE-{line_index:03d}",
                    "source_id": "TAV-01S",
                    "evidence_anchor": tile["evidence_id"],
                    "semantic_class": "GRAPHIC_LINE_PRIMITIVE",
                    "raw_value": f"{x1},{y1}->{x2},{y2};orientation={orientation};angle={angle:.2f};length={length:.1f}",
                    "unit": "px",
                    "evidence_state": "MIS",
                    "readability": "DETECTED_RASTER_PRIMITIVE",
                    "method": "CANNY_HOUGH_LINES_P",
                    "bbox_local_px": f"{min(x1,x2)},{min(y1,y2)},{max(x1,x2)},{max(y1,y2)}",
                    "confidence": "ND",
                    "agreement": "NA",
                    "note": "Raster primitive only; not classified as beam, axis, quote, boundary or reinforcement.",
                }
            )

    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "obs_id",
        "source_id",
        "evidence_anchor",
        "semantic_class",
        "raw_value",
        "unit",
        "evidence_state",
        "readability",
        "method",
        "bbox_local_px",
        "confidence",
        "agreement",
        "note",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(observations)

    state_counts: dict[str, int] = {}
    class_counts: dict[str, int] = {}
    for observation in observations:
        state_counts[observation["evidence_state"]] = state_counts.get(observation["evidence_state"], 0) + 1
        class_counts[observation["semantic_class"]] = class_counts.get(observation["semantic_class"], 0) + 1

    run_id = "FPEP-P03B-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    source_identity = identity["source_identity"]
    result = {
        "schema_version": "1.0",
        "pipeline_id": PIPELINE_ID,
        "run_id": run_id,
        "work_item_id": WORK_ITEM_ID,
        "stage_id": "P03B",
        "agent_role": AGENT_ROLE,
        "decision": "PASS_WITH_WATCH",
        "semantic_gate": "WATCH",
        "input_artifacts": [
            {
                "path": args.identity,
                "sha256": sha256_file(identity_path),
                "authority": "SOURCE_IDENTITY",
                "status": "CURRENT",
            },
            {
                "path": args.manifest,
                "sha256": sha256_file(manifest_path),
                "authority": "DERIVED_EVIDENCE_MANIFEST",
                "status": "CURRENT",
            },
        ],
        "primary_sources": [
            {
                "source_id": "TAV-01S",
                "path": source_identity["archive_branch"] + ":" + source_identity["remote_path"],
                "git_blob_sha": source_identity["git_blob_sha"],
                "sha256": source_identity["sha256"],
                "evidence_anchor": "P02 HiRes manifest plus its hash-verified tiles/regions",
            }
        ],
        "target_outputs": [args.output],
        "provenance_summary": {
            "DOC": 0,
            "MIS": state_counts.get("MIS", 0),
            "RIF": 0,
            "INF": 0,
            "INC": state_counts.get("INC", 0),
            "ND": 0,
            "observation_count": len(observations),
            "class_counts": class_counts,
        },
        "residuals": [
            {
                "residual_id": "P03B-R001",
                "claim_id": "P03B-MACHINE-TEXT-CANDIDATES",
                "blocking": False,
                "reason": "Machine OCR candidates are deliberately retained as INC and may contain transcription errors; no candidate is promoted to DOC by Reader B.",
                "required_evidence": "P04 claim-level comparison against the independently closed Reader A observations and P06 local reread for conflicts.",
            }
        ],
        "audit_paths": [args.output, args.manifest, args.identity],
        "information_barrier_attestation": {
            "forbidden_context_not_used": True,
            "legacy_target_counts_not_used_before_primary_gate": True,
            "downstream_model_not_used_as_primary_evidence": True,
            "majority_vote_not_used_for_authority": True,
        },
        "blind_read_audit": {
            "accessed_paths": sorted(accessed_paths),
            "tile_hashes_verified": tile_hash_audit,
            "reader_a_output_available_to_process": False,
            "topology_constructed": False,
            "ocr_promoted_to_DOC": False,
            "raster_primitives_promoted_above_MIS": False,
        },
    }

    result_path = root / args.result
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": run_id, "decision": result["decision"], "observations": len(observations)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
