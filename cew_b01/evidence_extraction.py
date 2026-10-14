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


_METHOD_ID = "OPENCV_LONG_AXIS_SUPPRESSED_CROSS_AXIS_ENVELOPE_V2"
_TOOL_PACKAGE = "opencv-python-headless"
_AXIS_KERNEL_EXTRA_PX = 5
_AXIS_CLOSE_ITERATIONS = 2
_AXIS_CONTEXT_EXTENSION_RATIO = 0.50
_AXIS_INNER_BAND_FRACTION = 0.20


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


def _axis_suppressed_envelope_mask(binary: Any, config: ExtractionConfig) -> tuple[Any, Any, Any]:
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, close_kernel, iterations=1)

    long_run = max(config.max_width_px, config.max_height_px) + _AXIS_KERNEL_EXTRA_PX
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (long_run, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, long_run))
    long_horizontal = cv2.morphologyEx(closed, cv2.MORPH_OPEN, horizontal_kernel)
    long_vertical = cv2.morphologyEx(closed, cv2.MORPH_OPEN, vertical_kernel)
    long_axes = cv2.bitwise_or(long_horizontal, long_vertical)

    axis_suppressed = cv2.subtract(closed, long_axes)
    axis_suppressed = cv2.morphologyEx(
        axis_suppressed,
        cv2.MORPH_CLOSE,
        close_kernel,
        iterations=_AXIS_CLOSE_ITERATIONS,
    )
    return axis_suppressed, long_horizontal, long_vertical


def _slice_has_ink(mask: Any, y1: int, y2: int, x1: int, x2: int) -> bool:
    height, width = mask.shape[:2]
    top = max(0, min(height, y1))
    bottom = max(0, min(height, y2))
    left = max(0, min(width, x1))
    right = max(0, min(width, x2))
    if bottom <= top or right <= left:
        return False
    region = mask[top:bottom, left:right]
    return bool(region.size and cv2.countNonZero(region) > 0)


def _has_bidirectional_cross_axis_context(
    long_horizontal: Any,
    long_vertical: Any,
    rectangle: tuple[int, int, int, int],
) -> bool:
    x, y, region_width, region_height = rectangle
    extension = max(
        5,
        int(round(min(region_width, region_height) * _AXIS_CONTEXT_EXTENSION_RATIO)),
    )
    inset_x = max(1, int(round(region_width * _AXIS_INNER_BAND_FRACTION)))
    inset_y = max(1, int(round(region_height * _AXIS_INNER_BAND_FRACTION)))

    center_x1 = x + inset_x
    center_x2 = x + region_width - inset_x
    center_y1 = y + inset_y
    center_y2 = y + region_height - inset_y
    if center_x2 <= center_x1 or center_y2 <= center_y1:
        return False

    horizontal_center = _slice_has_ink(
        long_horizontal,
        center_y1,
        center_y2,
        center_x1,
        center_x2,
    )
    horizontal_left = _slice_has_ink(
        long_horizontal,
        center_y1,
        center_y2,
        x - extension,
        x,
    )
    horizontal_right = _slice_has_ink(
        long_horizontal,
        center_y1,
        center_y2,
        x + region_width,
        x + region_width + extension,
    )

    vertical_center = _slice_has_ink(
        long_vertical,
        center_y1,
        center_y2,
        center_x1,
        center_x2,
    )
    vertical_top = _slice_has_ink(
        long_vertical,
        y - extension,
        y,
        center_x1,
        center_x2,
    )
    vertical_bottom = _slice_has_ink(
        long_vertical,
        y + region_height,
        y + region_height + extension,
        center_x1,
        center_x2,
    )

    return all(
        (
            horizontal_center,
            horizontal_left,
            horizontal_right,
            vertical_center,
            vertical_top,
            vertical_bottom,
        )
    )


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
    envelope_mask, long_horizontal, long_vertical = _axis_suppressed_envelope_mask(binary, config)
    contours, _ = cv2.findContours(envelope_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    rectangles: list[tuple[int, int, int, int, float]] = []
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue
        approximation = cv2.approxPolyDP(
            contour,
            config.approximation_epsilon_ratio * perimeter,
            True,
        )
        if len(approximation) != 4 or not cv2.isContourConvex(approximation):
            continue
        x, y, region_width, region_height = cv2.boundingRect(approximation)
        if not (
            config.min_width_px <= region_width <= config.max_width_px
            and config.min_height_px <= region_height <= config.max_height_px
        ):
            continue
        contour_area = float(cv2.contourArea(contour))
        rectangle_area = float(region_width * region_height)
        if contour_area <= 0 or rectangle_area <= 0:
            continue
        rectangularity = contour_area / rectangle_area
        if rectangularity < config.min_rectangularity:
            continue
        aspect_ratio = max(
            region_width / region_height,
            region_height / region_width,
        )
        if aspect_ratio > config.max_aspect_ratio:
            continue
        if not _has_bidirectional_cross_axis_context(
            long_horizontal,
            long_vertical,
            (x, y, region_width, region_height),
        ):
            continue
        confidence = round(min(1.0, max(0.0, rectangularity)), 6)
        rectangles.append((x, y, region_width, region_height, confidence))

    rectangles = _deduplicate_rectangles(rectangles, config.duplicate_iou_threshold)
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
