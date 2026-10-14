from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np

from .evidence_schema import EvidenceRegionCandidate
from .records import CoordinateFrame


def _ordered_candidates(candidates: Iterable[EvidenceRegionCandidate]) -> tuple[EvidenceRegionCandidate, ...]:
    result = tuple(candidates)
    if not all(isinstance(item, EvidenceRegionCandidate) for item in result):
        raise ValueError("review package requires EvidenceRegionCandidate records")
    if any(item.geometry.frame is not CoordinateFrame.RASTER_PIXEL for item in result):
        raise ValueError("review package requires RASTER_PIXEL evidence geometry")
    return tuple(
        sorted(
            result,
            key=lambda item: (
                item.geometry.y,
                item.geometry.x,
                item.geometry.width,
                item.geometry.height,
                item.candidate_id,
            ),
        )
    )


def _candidate_box(candidate: EvidenceRegionCandidate) -> tuple[int, int, int, int]:
    geometry = candidate.geometry
    return (
        int(round(geometry.x)),
        int(round(geometry.y)),
        int(round(geometry.width)),
        int(round(geometry.height)),
    )


def _draw_candidate(image: np.ndarray, candidate: EvidenceRegionCandidate, label: str) -> None:
    x, y, width, height = _candidate_box(candidate)
    x2 = x + width
    y2 = y + height
    thickness = max(2, round(max(image.shape[:2]) / 1800))
    cv2.rectangle(image, (x, y), (x2, y2), (0, 0, 255), thickness)
    font_scale = max(0.45, min(1.3, max(image.shape[:2]) / 3500))
    text_thickness = max(1, thickness)
    (text_width, text_height), baseline = cv2.getTextSize(
        label,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        text_thickness,
    )
    text_x = max(0, min(x, image.shape[1] - text_width - 4))
    text_y = max(text_height + baseline + 4, y - 4)
    cv2.rectangle(
        image,
        (text_x - 2, text_y - text_height - baseline - 2),
        (text_x + text_width + 2, text_y + baseline + 2),
        (255, 255, 255),
        -1,
    )
    cv2.putText(
        image,
        label,
        (text_x, text_y - baseline),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        (0, 0, 0),
        text_thickness,
        cv2.LINE_AA,
    )


def _fit_inside(image: np.ndarray, width: int, height: int) -> np.ndarray:
    source_height, source_width = image.shape[:2]
    if source_width <= 0 or source_height <= 0:
        raise ValueError("invalid image dimensions")
    scale = min(width / source_width, height / source_height)
    target_width = max(1, int(round(source_width * scale)))
    target_height = max(1, int(round(source_height * scale)))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    return cv2.resize(image, (target_width, target_height), interpolation=interpolation)


def _context_crop(image: np.ndarray, candidate: EvidenceRegionCandidate) -> np.ndarray:
    x, y, width, height = _candidate_box(candidate)
    margin = max(120, int(round(max(width, height) * 3.5)))
    left = max(0, x - margin)
    top = max(0, y - margin)
    right = min(image.shape[1], x + width + margin)
    bottom = min(image.shape[0], y + height + margin)
    crop = image[top:bottom, left:right].copy()
    local_candidate = _LocalCandidate(
        x=x - left,
        y=y - top,
        width=width,
        height=height,
    )
    cv2.rectangle(
        crop,
        (local_candidate.x, local_candidate.y),
        (local_candidate.x + local_candidate.width, local_candidate.y + local_candidate.height),
        (0, 0, 255),
        max(2, round(max(crop.shape[:2]) / 400)),
    )
    return crop


class _LocalCandidate:
    def __init__(self, *, x: int, y: int, width: int, height: int) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height


def render_review_package(
    raster_path: Path | str,
    candidates: Iterable[EvidenceRegionCandidate],
    output_dir: Path | str,
    *,
    sheet_rows: int = 4,
    sheet_columns: int = 3,
    tile_width: int = 560,
    tile_height: int = 420,
) -> dict[str, Any]:
    if sheet_rows <= 0 or sheet_columns <= 0 or tile_width <= 0 or tile_height <= 0:
        raise ValueError("review package layout values must be positive")
    source_path = Path(raster_path)
    image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("review raster could not be decoded")
    ordered = _ordered_candidates(candidates)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    overview = image.copy()
    for index, candidate in enumerate(ordered, start=1):
        _draw_candidate(overview, candidate, f"{index:02d}")
    overview_preview = _fit_inside(overview, 1800, 2200)
    overview_path = destination / "overview.png"
    if not cv2.imwrite(str(overview_path), overview_preview):
        raise ValueError("could not write review overview")

    per_sheet = sheet_rows * sheet_columns
    contact_sheet_paths: list[str] = []
    manifest_candidates: list[dict[str, Any]] = []
    for sheet_start in range(0, len(ordered), per_sheet):
        sheet_items = ordered[sheet_start : sheet_start + per_sheet]
        sheet_index = sheet_start // per_sheet + 1
        sheet = np.full(
            (sheet_rows * tile_height, sheet_columns * tile_width, 3),
            255,
            dtype=np.uint8,
        )
        for offset, candidate in enumerate(sheet_items):
            review_index = sheet_start + offset + 1
            row = offset // sheet_columns
            column = offset % sheet_columns
            crop = _context_crop(image, candidate)
            header_height = 48
            fitted = _fit_inside(crop, tile_width - 16, tile_height - header_height - 16)
            y0 = row * tile_height
            x0 = column * tile_width
            paste_x = x0 + (tile_width - fitted.shape[1]) // 2
            paste_y = y0 + header_height + (tile_height - header_height - fitted.shape[0]) // 2
            sheet[paste_y : paste_y + fitted.shape[0], paste_x : paste_x + fitted.shape[1]] = fitted
            label = f"{review_index:02d}  {candidate.candidate_id}"
            cv2.putText(
                sheet,
                label,
                (x0 + 8, y0 + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.46,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )
            manifest_candidates.append(
                {
                    "review_index": review_index,
                    "candidate_id": candidate.candidate_id,
                    "geometry_digest": candidate.geometry_digest,
                    "confidence": candidate.confidence,
                    "sheet_index": sheet_index,
                    "sheet_slot": offset + 1,
                }
            )
        sheet_path = destination / f"contact-sheet-{sheet_index:02d}.png"
        if not cv2.imwrite(str(sheet_path), sheet):
            raise ValueError("could not write review contact sheet")
        contact_sheet_paths.append(str(sheet_path))

    manifest = {
        "schema_id": "CEW_B01_G4_HUMAN_REVIEW_PACKAGE",
        "schema_version": 1,
        "source_raster": str(source_path.name),
        "candidate_count": len(ordered),
        "review_state": "PENDING_HUMAN",
        "candidates": manifest_candidates,
    }
    manifest_path = destination / "review-index.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {
        "overview_path": str(overview_path),
        "contact_sheet_paths": contact_sheet_paths,
        "manifest_path": str(manifest_path),
    }
