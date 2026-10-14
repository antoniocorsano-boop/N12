from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from typing import Any, Iterable

import cv2

from .evidence_schema import (
    AxisAlignedEvidenceRegion,
    EvidenceRegionCandidate,
    Task3RasterBinding,
)
from .records import CoordinateFrame


_METHOD_ID = "OPENCV_COMPOUND_RECTANGULAR_CELL_ENVELOPE_V2"
_TOOL_PACKAGE = "opencv-python-headless"
_CELL_VERTICAL_OVERLAP_RATIO = 0.70
_CELL_SIZE_RATIO_MAX = 1.50
_CELL_GAP_MIN_PX = -4
_CELL_GAP_TOLERANCE_RATIO = 0.75
_ROW_ALIGNMENT_RATIO = 0.25
_OUTER_FRAME_BAND_PX = 5
_OUTER_FRAME_SIDE_COVERAGE_MIN = 0.80


@dataclass(frozen=True)
class ExtractionConfig:
    threshold: int = 180
    min_width_px: int = 20
    min_height_px: int = 20
    max_width_px: int = 250
    max_height_px: int = 250
    min_rectangularity: float = 0.55
    max_aspect_ratio: float = 5.0
    duplicate_iou_threshold: float = 0.75
    approximation_epsilon_ratio: float = 0.02

    def __post_init__(self) -> None:
        if isinstance(self.threshold, bool) or not isinstance(self.threshold, int) or not 0 <= self.threshold <= 255:
            raise ValueError("threshold must be an integer within [0, 255]")
        for name in ("min_width_px", "min_height_px", "max_width_px", "max_height_px"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.min_width_px > self.max_width_px or self.min_height_px > self.max_height_px:
            raise ValueError("minimum extraction dimensions cannot exceed maximum dimensions")
        if not 0.0 < float(self.min_rectangularity) <= 1.0:
            raise ValueError("min_rectangularity must be within (0, 1]")
        if float(self.max_aspect_ratio) < 1.0:
            raise ValueError("max_aspect_ratio must be at least 1")
        if not 0.0 < float(self.duplicate_iou_threshold) <= 1.0:
            raise ValueError("duplicate_iou_threshold must be within (0, 1]")
        if not 0.0 < float(self.approximation_epsilon_ratio) < 1.0:
            raise ValueError("approximation_epsilon_ratio must be within (0, 1)")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "min_width_px": self.min_width_px,
            "min_height_px": self.min_height_px,
            "max_width_px": self.max_width_px,
            "max_height_px": self.max_height_px,
            "min_rectangularity": self.min_rectangularity,
            "max_aspect_ratio": self.max_aspect_ratio,
            "duplicate_iou_threshold": self.duplicate_iou_threshold,
            "approximation_epsilon_ratio": self.approximation_epsilon_ratio,
        }


def _intersection_over_union(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> float:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    left = max(ax, bx)
    top = max(ay, by)
    right = min(ax + aw, bx + bw)
    bottom = min(ay + ah, by + bh)
    if right <= left or bottom <= top:
        return 0.0
    intersection = float((right - left) * (bottom - top))
    union = float(aw * ah + bw * bh) - intersection
    return intersection / union if union > 0 else 0.0


def _deduplicate_rectangles(
    rectangles: Iterable[tuple[int, int, int, int, float]],
    threshold: float,
) -> list[tuple[int, int, int, int, float]]:
    ordered = sorted(
        rectangles,
        key=lambda item: (-(item[2] * item[3]), item[1], item[0], item[2], item[3]),
    )
    accepted: list[tuple[int, int, int, int, float]] = []
    for candidate in ordered:
        candidate_box = candidate[:4]
        if any(
            _intersection_over_union(candidate_box, existing[:4]) >= threshold
            for existing in accepted
        ):
            continue
        accepted.append(candidate)
    return sorted(accepted, key=lambda item: (item[1], item[0], item[2], item[3]))


def _interval_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> int:
    return max(0, min(end_a, end_b) - max(start_a, start_b))


def _cell_gap_tolerance(config: ExtractionConfig) -> int:
    return max(
        4,
        int(round(min(config.min_width_px, config.min_height_px) * _CELL_GAP_TOLERANCE_RATIO)),
    )


def _extract_rectangular_cells(
    binary: Any,
    config: ExtractionConfig,
) -> list[tuple[int, int, int, int, float]]:
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cells: list[tuple[int, int, int, int, float]] = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if not (
            config.min_width_px <= width <= config.max_width_px
            and config.min_height_px <= height <= config.max_height_px
        ):
            continue
        contour_area = abs(float(cv2.contourArea(contour)))
        rectangle_area = float(width * height)
        if contour_area <= 0 or rectangle_area <= 0:
            continue
        rectangularity = contour_area / rectangle_area
        if rectangularity < config.min_rectangularity:
            continue
        aspect_ratio = max(width / height, height / width)
        if aspect_ratio > config.max_aspect_ratio:
            continue
        cells.append((x, y, width, height, rectangularity))
    return sorted(cells, key=lambda item: (item[1], item[0], item[2], item[3], -item[4]))


def _horizontal_cell_pairs(
    cells: list[tuple[int, int, int, int, float]],
    config: ExtractionConfig,
) -> list[tuple[int, int, int, int, int, int]]:
    gap_tolerance = _cell_gap_tolerance(config)
    pairs: list[tuple[int, int, int, int, int, int]] = []
    for first_index, first in enumerate(cells):
        for second_index in range(first_index + 1, len(cells)):
            second = cells[second_index]
            left, right = (first, second) if first[0] <= second[0] else (second, first)
            lx, ly, lw, lh, _ = left
            rx, ry, rw, rh, _ = right
            vertical_overlap = _interval_overlap(ly, ly + lh, ry, ry + rh)
            if vertical_overlap < _CELL_VERTICAL_OVERLAP_RATIO * min(lh, rh):
                continue
            horizontal_gap = rx - (lx + lw)
            if not _CELL_GAP_MIN_PX <= horizontal_gap <= gap_tolerance:
                continue
            if max(lh, rh) / min(lh, rh) > _CELL_SIZE_RATIO_MAX:
                continue
            x1 = min(lx, rx)
            y1 = min(ly, ry)
            x2 = max(lx + lw, rx + rw)
            y2 = max(ly + lh, ry + rh)
            if x2 - x1 > config.max_width_px or y2 - y1 > config.max_height_px:
                continue
            pairs.append((first_index, second_index, x1, y1, x2 - x1, y2 - y1))
    return sorted(pairs, key=lambda item: (item[3], item[2], item[4], item[5], item[0], item[1]))


def _column_coverage(binary: Any, y1: int, y2: int, x1: int, x2: int) -> float:
    image_height, image_width = binary.shape[:2]
    top = max(0, min(image_height, y1))
    bottom = max(0, min(image_height, y2))
    left = max(0, min(image_width, x1))
    right = max(0, min(image_width, x2))
    if bottom <= top or right <= left:
        return 0.0
    region = binary[top:bottom, left:right]
    if not region.size:
        return 0.0
    return float((region > 0).any(axis=0).mean())


def _row_coverage(binary: Any, y1: int, y2: int, x1: int, x2: int) -> float:
    image_height, image_width = binary.shape[:2]
    top = max(0, min(image_height, y1))
    bottom = max(0, min(image_height, y2))
    left = max(0, min(image_width, x1))
    right = max(0, min(image_width, x2))
    if bottom <= top or right <= left:
        return 0.0
    region = binary[top:bottom, left:right]
    if not region.size:
        return 0.0
    return float((region > 0).any(axis=1).mean())


def _outer_frame_side_coverages(
    binary: Any,
    rectangle: tuple[int, int, int, int],
) -> tuple[float, float, float, float]:
    x, y, width, height = rectangle
    band = _OUTER_FRAME_BAND_PX
    top = _column_coverage(binary, y - band, y + band + 1, x, x + width)
    bottom = _column_coverage(
        binary,
        y + height - band,
        y + height + band + 1,
        x,
        x + width,
    )
    left = _row_coverage(binary, y, y + height, x - band, x + band + 1)
    right = _row_coverage(
        binary,
        y,
        y + height,
        x + width - band,
        x + width + band + 1,
    )
    return (top, bottom, left, right)


def _assemble_compound_envelopes(
    binary: Any,
    cells: list[tuple[int, int, int, int, float]],
    pairs: list[tuple[int, int, int, int, int, int]],
    config: ExtractionConfig,
) -> list[tuple[int, int, int, int, float]]:
    gap_tolerance = _cell_gap_tolerance(config)
    envelopes: list[tuple[int, int, int, int, float]] = []
    for first_pair_index, first_pair in enumerate(pairs):
        first_ids = {first_pair[0], first_pair[1]}
        for second_pair in pairs[first_pair_index + 1 :]:
            second_ids = {second_pair[0], second_pair[1]}
            if first_ids & second_ids:
                continue

            top_pair, bottom_pair = (
                (first_pair, second_pair)
                if first_pair[3] <= second_pair[3]
                else (second_pair, first_pair)
            )
            tx, ty, tw, th = top_pair[2:6]
            bx, by, bw, bh = bottom_pair[2:6]
            alignment_tolerance = max(
                gap_tolerance,
                int(round(max(tw, bw) * _ROW_ALIGNMENT_RATIO)),
            )
            if abs(tx - bx) > alignment_tolerance:
                continue
            if abs((tx + tw) - (bx + bw)) > alignment_tolerance:
                continue
            vertical_gap = by - (ty + th)
            if not _CELL_GAP_MIN_PX <= vertical_gap <= gap_tolerance:
                continue

            x1 = min(tx, bx)
            y1 = min(ty, by)
            x2 = max(tx + tw, bx + bw)
            y2 = max(ty + th, by + bh)
            width = x2 - x1
            height = y2 - y1
            if not (
                config.min_width_px <= width <= config.max_width_px
                and config.min_height_px <= height <= config.max_height_px
            ):
                continue
            aspect_ratio = max(width / height, height / width)
            if aspect_ratio > config.max_aspect_ratio:
                continue

            side_coverages = _outer_frame_side_coverages(binary, (x1, y1, width, height))
            minimum_side_coverage = min(side_coverages)
            if minimum_side_coverage < _OUTER_FRAME_SIDE_COVERAGE_MIN:
                continue

            member_ids = first_ids | second_ids
            mean_rectangularity = sum(cells[index][4] for index in member_ids) / len(member_ids)
            confidence = round(
                min(1.0, max(0.0, mean_rectangularity * minimum_side_coverage)),
                6,
            )
            envelopes.append((x1, y1, width, height, confidence))
    return _deduplicate_rectangles(envelopes, config.duplicate_iou_threshold)


def extract_g4_evidence_candidates(
    binding: Task3RasterBinding,
    raster_path: Path | str,
    config: ExtractionConfig = ExtractionConfig(),
) -> tuple[EvidenceRegionCandidate, ...]:
    path = Path(raster_path)
    if not path.is_file():
        raise ValueError("Step 3 raster does not exist")
    actual_png_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_png_sha256 != binding.png_sha256:
        raise ValueError("Step 3 raster PNG identity mismatch")

    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("Step 3 raster could not be decoded")
    height, width = image.shape[:2]
    if width != binding.raster_width_px or height != binding.raster_height_px:
        raise ValueError("Step 3 raster dimensions do not match governed probe output")

    _, binary = cv2.threshold(
        image,
        config.threshold,
        255,
        cv2.THRESH_BINARY_INV,
    )
    cells = _extract_rectangular_cells(binary, config)
    pairs = _horizontal_cell_pairs(cells, config)
    rectangles = _assemble_compound_envelopes(binary, cells, pairs, config)

    tool_version = version(_TOOL_PACKAGE)
    candidates = tuple(
        EvidenceRegionCandidate.create(
            source=binding.source,
            geometry=AxisAlignedEvidenceRegion(
                frame=CoordinateFrame.RASTER_PIXEL,
                x=float(x),
                y=float(y),
                width=float(region_width),
                height=float(region_height),
            ),
            method=_METHOD_ID,
            tool_id=_TOOL_PACKAGE,
            tool_version=tool_version,
            confidence=confidence,
        )
        for x, y, region_width, region_height, confidence in rectangles
    )
    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                item.geometry.y,
                item.geometry.x,
                item.geometry.width,
                item.geometry.height,
                item.candidate_id,
            ),
        )
    )


def evidence_bundle_mapping(
    binding: Task3RasterBinding,
    candidates: Iterable[EvidenceRegionCandidate],
    config: ExtractionConfig = ExtractionConfig(),
) -> dict[str, Any]:
    ordered = sorted(candidates, key=lambda item: item.candidate_id)
    body = {
        "schema_id": "CEW_B01_G4_EVIDENCE_CANDIDATES",
        "schema_version": 1,
        "source_binding": binding.to_mapping(),
        "extraction": {
            "method": _METHOD_ID,
            "tool_id": _TOOL_PACKAGE,
            "tool_version": version(_TOOL_PACKAGE),
            "config": config.to_mapping(),
            "semantic_identity_assigned": False,
            "structural_identity_authorized": False,
        },
        "candidate_count": len(ordered),
        "candidates": [candidate.to_mapping() for candidate in ordered],
    }
    digest_payload = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    body["bundle_sha256"] = hashlib.sha256(digest_payload).hexdigest()
    return body


def write_evidence_bundle(
    binding: Task3RasterBinding,
    candidates: Iterable[EvidenceRegionCandidate],
    destination: Path | str,
    config: ExtractionConfig = ExtractionConfig(),
) -> dict[str, Any]:
    mapping = evidence_bundle_mapping(binding, candidates, config=config)
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(mapping, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return mapping
