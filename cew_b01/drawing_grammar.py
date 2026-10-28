from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class DrawingGrammarConfig:
    min_width_px: int = 20
    min_height_px: int = 20
    max_width_px: int = 250
    max_height_px: int = 250
    max_aspect_ratio: float = 3.0
    min_frame_coverage: float = 0.60
    min_internal_ink_ratio: float = 0.008
    min_internal_components: int = 1
    border_margin_ratio: float = 0.12
    context_band_ratio: float = 0.55
    duplicate_iou_threshold: float = 0.72

    def __post_init__(self) -> None:
        for name in ("min_width_px", "min_height_px", "max_width_px", "max_height_px", "min_internal_components"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.min_width_px > self.max_width_px or self.min_height_px > self.max_height_px:
            raise ValueError("minimum grammar dimensions cannot exceed maximum dimensions")
        if float(self.max_aspect_ratio) < 1.0:
            raise ValueError("max_aspect_ratio must be at least 1")
        for name in (
            "min_frame_coverage",
            "min_internal_ink_ratio",
            "border_margin_ratio",
            "context_band_ratio",
            "duplicate_iou_threshold",
        ):
            value = float(getattr(self, name))
            if not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must be within (0, 1]")


@dataclass(frozen=True)
class DrawingMotif:
    motif_id: str
    x: int
    y: int
    width: int
    height: int
    frame_coverage: float
    internal_ink_ratio: float
    internal_component_count: int
    single_full_span_divider: bool
    context_signature: tuple[float, float, float, float]
    semantic_identity: None = None

    @property
    def rectangle(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height


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


def _line_coverage(region: Any, *, axis: int) -> float:
    if region.size == 0:
        return 0.0
    occupied = (region > 0).any(axis=axis)
    return float(occupied.mean()) if occupied.size else 0.0


def _frame_coverage(binary: Any, rectangle: tuple[int, int, int, int]) -> float:
    x, y, width, height = rectangle
    band = max(2, int(round(min(width, height) * 0.08)))
    image_height, image_width = binary.shape[:2]

    def crop(x1: int, y1: int, x2: int, y2: int) -> Any:
        return binary[
            max(0, y1):min(image_height, y2),
            max(0, x1):min(image_width, x2),
        ]

    top = _line_coverage(crop(x, y - band, x + width, y + band + 1), axis=0)
    bottom = _line_coverage(
        crop(x, y + height - band, x + width, y + height + band + 1), axis=0
    )
    left = _line_coverage(crop(x - band, y, x + band + 1, y + height), axis=1)
    right = _line_coverage(
        crop(x + width - band, y, x + width + band + 1, y + height), axis=1
    )
    return min(top, bottom, left, right)


def _interior_metrics(
    binary: Any,
    rectangle: tuple[int, int, int, int],
    config: DrawingGrammarConfig,
) -> tuple[float, int, bool]:
    x, y, width, height = rectangle
    margin = max(3, int(round(min(width, height) * config.border_margin_ratio)))
    x1, y1 = x + margin, y + margin
    x2, y2 = x + width - margin, y + height - margin
    if x2 <= x1 or y2 <= y1:
        return (0.0, 0, False)
    interior = (binary[y1:y2, x1:x2] > 0).astype(np.uint8)
    if not interior.size:
        return (0.0, 0, False)
    ink_ratio = float(interior.mean())
    count, _, stats, _ = cv2.connectedComponentsWithStats(interior, connectivity=8)
    components = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= 3:
            components.append(stats[label])

    inner_height, inner_width = interior.shape[:2]
    single_full_span_divider = False
    if len(components) == 1:
        component = components[0]
        comp_width = int(component[cv2.CC_STAT_WIDTH])
        comp_height = int(component[cv2.CC_STAT_HEIGHT])
        single_full_span_divider = (
            comp_width >= int(round(inner_width * 0.80))
            and comp_height <= max(5, int(round(inner_height * 0.22)))
        ) or (
            comp_height >= int(round(inner_height * 0.80))
            and comp_width <= max(5, int(round(inner_width * 0.22)))
        )
    return (ink_ratio, len(components), single_full_span_divider)


def _context_signature(
    binary: Any,
    rectangle: tuple[int, int, int, int],
    config: DrawingGrammarConfig,
) -> tuple[float, float, float, float]:
    x, y, width, height = rectangle
    image_height, image_width = binary.shape[:2]
    reach = max(8, int(round(min(width, height) * config.context_band_ratio)))
    side_half = max(2, int(round(min(width, height) * 0.12)))
    # Candidate contours can follow the inner edge of the closed frame. Leave a
    # dead zone before measuring external context so the frame itself is not
    # misread as a structural line on every side.
    frame_dead_zone = max(4, int(round(min(width, height) * 0.10)))
    cx = x + width // 2
    cy = y + height // 2

    def density(x1: int, y1: int, x2: int, y2: int) -> float:
        region = binary[
            max(0, y1):min(image_height, y2),
            max(0, x1):min(image_width, x2),
        ]
        return float((region > 0).mean()) if region.size else 0.0

    left = density(
        x - reach,
        cy - side_half,
        x - frame_dead_zone,
        cy + side_half + 1,
    )
    right = density(
        x + width + frame_dead_zone,
        cy - side_half,
        x + width + reach,
        cy + side_half + 1,
    )
    top = density(
        cx - side_half,
        y - reach,
        cx + side_half + 1,
        y - frame_dead_zone,
    )
    bottom = density(
        cx - side_half,
        y + height + frame_dead_zone,
        cx + side_half + 1,
        y + height + reach,
    )
    return tuple(round(value, 6) for value in (left, right, top, bottom))


def _motif_id(
    rectangle: tuple[int, int, int, int],
    frame_coverage: float,
    internal_ink_ratio: float,
    internal_component_count: int,
    single_full_span_divider: bool,
    context_signature: tuple[float, float, float, float],
) -> str:
    payload = json.dumps(
        {
            "rectangle": rectangle,
            "frame_coverage": round(frame_coverage, 6),
            "internal_ink_ratio": round(internal_ink_ratio, 6),
            "internal_component_count": internal_component_count,
            "single_full_span_divider": single_full_span_divider,
            "context_signature": context_signature,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "CEW-DGM-" + hashlib.sha256(payload).hexdigest()[:24]


def _candidate_rectangles(binary: Any, config: DrawingGrammarConfig) -> list[tuple[int, int, int, int]]:
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    rectangles: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        if not (
            config.min_width_px <= width <= config.max_width_px
            and config.min_height_px <= height <= config.max_height_px
        ):
            continue
        aspect = max(width / height, height / width)
        if aspect > config.max_aspect_ratio:
            continue
        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue
        approximation = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
        if len(approximation) < 4 or len(approximation) > 8:
            continue
        coverage = _frame_coverage(binary, (x, y, width, height))
        if coverage < config.min_frame_coverage:
            continue
        rectangles.append((x, y, width, height))

    ordered = sorted(rectangles, key=lambda item: (-(item[2] * item[3]), item[1], item[0]))
    deduplicated: list[tuple[int, int, int, int]] = []
    for rectangle in ordered:
        if any(
            _intersection_over_union(rectangle, existing) >= config.duplicate_iou_threshold
            for existing in deduplicated
        ):
            continue
        deduplicated.append(rectangle)
    return sorted(deduplicated, key=lambda item: (item[1], item[0], item[2], item[3]))


def extract_drawing_motifs(
    binary: Any,
    config: DrawingGrammarConfig = DrawingGrammarConfig(),
) -> tuple[DrawingMotif, ...]:
    if binary is None or getattr(binary, "ndim", None) != 2:
        raise ValueError("drawing grammar requires a single-channel binary raster")
    motifs: list[DrawingMotif] = []
    for rectangle in _candidate_rectangles(binary, config):
        frame_coverage = _frame_coverage(binary, rectangle)
        ink_ratio, component_count, divider = _interior_metrics(binary, rectangle, config)
        if ink_ratio < config.min_internal_ink_ratio:
            continue
        if component_count < config.min_internal_components:
            continue
        if divider:
            continue
        context = _context_signature(binary, rectangle, config)
        motifs.append(
            DrawingMotif(
                motif_id=_motif_id(
                    rectangle,
                    frame_coverage,
                    ink_ratio,
                    component_count,
                    divider,
                    context,
                ),
                x=rectangle[0],
                y=rectangle[1],
                width=rectangle[2],
                height=rectangle[3],
                frame_coverage=round(frame_coverage, 6),
                internal_ink_ratio=round(ink_ratio, 6),
                internal_component_count=component_count,
                single_full_span_divider=divider,
                context_signature=context,
            )
        )
    return tuple(sorted(motifs, key=lambda item: (item.y, item.x, item.width, item.height, item.motif_id)))


def _ratio_similarity(first: float, second: float) -> float:
    high = max(abs(first), abs(second))
    if high == 0:
        return 1.0
    return max(0.0, 1.0 - abs(first - second) / high)


def _context_similarity(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    first_active = {index for index, value in enumerate(first) if value >= 0.03}
    second_active = {index for index, value in enumerate(second) if value >= 0.03}
    union = first_active | second_active
    if not union:
        return 1.0
    return len(first_active & second_active) / len(union)


def motif_similarity(left: DrawingMotif, right: DrawingMotif) -> float:
    aspect_score = _ratio_similarity(left.aspect_ratio, right.aspect_ratio)
    ink_score = _ratio_similarity(left.internal_ink_ratio, right.internal_ink_ratio)
    component_score = _ratio_similarity(
        float(left.internal_component_count),
        float(right.internal_component_count),
    )
    context_score = _context_similarity(left.context_signature, right.context_signature)
    score = (
        0.30 * aspect_score
        + 0.20 * ink_score
        + 0.20 * component_score
        + 0.30 * context_score
    )
    return round(max(0.0, min(1.0, score)), 6)
