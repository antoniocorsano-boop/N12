from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import cv2
import numpy as np

from .evidence_schema import Task3RasterBinding
from .grammar_schema import DocumentRegionKind, DocumentRegionMask
from .records import CoordinateFrame


_CONFIRMATION_DECISION = "CONFIRMED_FOR_G0_DOCUMENT_FUNCTION_ONLY"


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _ordered_zones(zones: Sequence[DocumentRegionMask]) -> tuple[DocumentRegionMask, ...]:
    result = tuple(zones)
    if not result or not all(isinstance(item, DocumentRegionMask) for item in result):
        raise ValueError("G0_ZONE_REVIEW_REQUIRES_TYPED_ZONES")
    return tuple(
        sorted(
            result,
            key=lambda item: (item.kind.value, item.y, item.x, item.width, item.height, item.region_id),
        )
    )


def zone_set_digest(zones: Sequence[DocumentRegionMask]) -> str:
    ordered = _ordered_zones(zones)
    payload = [
        {
            "region_id": zone.region_id,
            "source_sha256": zone.source.sha256,
            "page_index": zone.page_index,
            "kind": zone.kind.value,
            "geometry_digest": zone.geometry_digest,
            "method": zone.method,
        }
        for zone in ordered
    ]
    return _canonical_hash(payload)


def build_zone_confirmation_receipt(
    *,
    binding: Task3RasterBinding,
    zones: Sequence[DocumentRegionMask],
    reviewer_decision_id: str,
) -> dict[str, Any]:
    if not isinstance(binding, Task3RasterBinding):
        raise ValueError("G0_RECEIPT_REQUIRES_TASK3_RASTER_BINDING")
    if not isinstance(reviewer_decision_id, str) or not reviewer_decision_id.strip():
        raise ValueError("G0_RECEIPT_REQUIRES_REVIEWER_DECISION_ID")
    ordered = _ordered_zones(zones)
    return {
        "schema": "TAV5_DOCUMENT_ZONE_REVIEW_RECEIPT_v1",
        "decision": _CONFIRMATION_DECISION,
        "reviewer_decision_id": reviewer_decision_id,
        "source_sha256": binding.source.sha256,
        "page_index": binding.source.page_index,
        "raster_sha256": binding.raster_sha256,
        "raster_png_sha256": binding.png_sha256,
        "zone_set_digest": zone_set_digest(ordered),
        "confirmed_region_ids": [zone.region_id for zone in ordered],
        "authority_effect": "DOCUMENT_FUNCTION_CLASSIFICATION_ONLY",
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }


def _validate_receipt(
    binding: Task3RasterBinding,
    zones: Sequence[DocumentRegionMask],
    receipt: Mapping[str, Any],
) -> None:
    ordered = _ordered_zones(zones)
    expected = {
        "schema": "TAV5_DOCUMENT_ZONE_REVIEW_RECEIPT_v1",
        "decision": _CONFIRMATION_DECISION,
        "source_sha256": binding.source.sha256,
        "page_index": binding.source.page_index,
        "raster_sha256": binding.raster_sha256,
        "raster_png_sha256": binding.png_sha256,
        "zone_set_digest": zone_set_digest(ordered),
        "confirmed_region_ids": [zone.region_id for zone in ordered],
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError("ZONE_CONFIRMATION_RECEIPT_MISMATCH")
    if not isinstance(receipt.get("reviewer_decision_id"), str) or not receipt["reviewer_decision_id"].strip():
        raise ValueError("ZONE_CONFIRMATION_RECEIPT_MISMATCH")


def confirmed_zones_from_receipt(
    binding: Task3RasterBinding,
    zones: Sequence[DocumentRegionMask],
    receipt: Mapping[str, Any],
) -> tuple[DocumentRegionMask, ...]:
    _validate_receipt(binding, zones, receipt)
    confirmed: list[DocumentRegionMask] = []
    for zone in _ordered_zones(zones):
        confirmed.append(
            DocumentRegionMask.create(
                source=zone.source,
                frame=zone.frame,
                raster_width=zone.raster_width,
                raster_height=zone.raster_height,
                x=zone.x,
                y=zone.y,
                width=zone.width,
                height=zone.height,
                kind=zone.kind,
                method=zone.method,
                human_confirmed=True,
            )
        )
    return tuple(confirmed)


def _zone_color(kind: DocumentRegionKind) -> tuple[int, int, int]:
    if kind == DocumentRegionKind.STRUCTURAL_WORKAREA:
        return (0, 160, 0)
    if kind == DocumentRegionKind.TITLE_BLOCK:
        return (0, 0, 220)
    if kind == DocumentRegionKind.UNKNOWN_DOCUMENT_REGION:
        return (0, 140, 255)
    return (180, 80, 0)


def _draw_zone(image: np.ndarray, zone: DocumentRegionMask, index: int) -> None:
    x0 = int(round(zone.x))
    y0 = int(round(zone.y))
    x1 = int(round(zone.x + zone.width))
    y1 = int(round(zone.y + zone.height))
    color = _zone_color(zone.kind)
    thickness = max(2, round(max(image.shape[:2]) / 1800))
    cv2.rectangle(image, (x0, y0), (x1, y1), color, thickness)
    label = f"{index:02d} {zone.kind.value}"
    cv2.putText(
        image,
        label,
        (max(2, x0 + 4), max(18, y0 + 18)),
        cv2.FONT_HERSHEY_SIMPLEX,
        max(0.45, min(1.1, max(image.shape[:2]) / 4000)),
        color,
        max(1, thickness),
        cv2.LINE_AA,
    )


def _fit_inside(image: np.ndarray, width: int = 1800, height: int = 2200) -> np.ndarray:
    source_height, source_width = image.shape[:2]
    scale = min(width / source_width, height / source_height, 1.0)
    if scale >= 1.0:
        return image
    return cv2.resize(
        image,
        (max(1, int(round(source_width * scale))), max(1, int(round(source_height * scale)))),
        interpolation=cv2.INTER_AREA,
    )


def render_zone_review_package(
    binding: Task3RasterBinding,
    raster_path: Path | str,
    zones: Sequence[DocumentRegionMask],
    output_dir: Path | str,
    *,
    confirmation_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(binding, Task3RasterBinding):
        raise ValueError("G0_REVIEW_REQUIRES_TASK3_RASTER_BINDING")
    source_path = Path(raster_path)
    image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("G0_REVIEW_RASTER_DECODE_FAILED")
    height, width = image.shape[:2]
    if width != binding.raster_width_px or height != binding.raster_height_px:
        raise ValueError("G0_REVIEW_RASTER_BINDING_DIMENSION_MISMATCH")

    ordered = _ordered_zones(zones)
    for zone in ordered:
        if zone.source != binding.source or zone.page_index != binding.source.page_index:
            raise ValueError("G0_REVIEW_ZONE_SOURCE_MISMATCH")
        if zone.frame != CoordinateFrame.RASTER_PIXEL:
            raise ValueError("G0_REVIEW_ZONE_FRAME_MISMATCH")

    if confirmation_receipt is None:
        review_state = "PENDING_HUMAN_ZONE_REVIEW"
        g0_pass = False
    else:
        _validate_receipt(binding, ordered, confirmation_receipt)
        review_state = "G0_DOCUMENT_ZONING_PASS"
        g0_pass = True

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    overview = image.copy()
    zone_entries: list[dict[str, Any]] = []
    crop_paths: list[str] = []

    for index, zone in enumerate(ordered, start=1):
        _draw_zone(overview, zone, index)
        x0 = int(round(zone.x))
        y0 = int(round(zone.y))
        x1 = int(round(zone.x + zone.width))
        y1 = int(round(zone.y + zone.height))
        crop = image[y0:y1, x0:x1].copy()
        crop_path = destination / f"zone-{index:02d}-{zone.kind.value.lower()}.png"
        if not cv2.imwrite(str(crop_path), crop):
            raise ValueError("G0_REVIEW_ZONE_CROP_WRITE_FAILED")
        crop_paths.append(str(crop_path))
        zone_entries.append(
            {
                "review_index": index,
                "region_id": zone.region_id,
                "kind": zone.kind.value,
                "geometry_digest": zone.geometry_digest,
                "geometry": {"x": zone.x, "y": zone.y, "width": zone.width, "height": zone.height},
                "method": zone.method,
                "proposal_human_confirmed": zone.human_confirmed,
                "crop": crop_path.name,
            }
        )

    overview_path = destination / "zone-overview.png"
    if not cv2.imwrite(str(overview_path), _fit_inside(overview)):
        raise ValueError("G0_REVIEW_OVERVIEW_WRITE_FAILED")

    proposal_path = destination / "proposed-zones.json"
    proposal_payload = {
        "schema": "TAV5_DOCUMENT_ZONE_PROPOSALS_v1",
        "source": binding.source.to_mapping(),
        "raster": binding.to_mapping(),
        "zone_set_digest": zone_set_digest(ordered),
        "zones": [zone.to_mapping() for zone in ordered],
    }
    proposal_path.write_text(json.dumps(proposal_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "schema": "TAV5_DOCUMENT_ZONE_REVIEW_PACKAGE_v1",
        "source": binding.source.to_mapping(),
        "raster": {
            "raster_sha256": binding.raster_sha256,
            "png_sha256": binding.png_sha256,
            "width_px": binding.raster_width_px,
            "height_px": binding.raster_height_px,
            "renderer_tool_id": binding.renderer_tool_id,
            "renderer_tool_version": binding.renderer_tool_version,
        },
        "zone_set_digest": zone_set_digest(ordered),
        "zone_count": len(ordered),
        "review_state": review_state,
        "g0_document_zoning_pass": g0_pass,
        "authority": {
            "authority_effect": "DOCUMENT_FUNCTION_CLASSIFICATION_ONLY" if g0_pass else "NONE",
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
        },
        "zones": zone_entries,
    }
    if confirmation_receipt is not None:
        manifest["confirmation_receipt"] = dict(confirmation_receipt)

    manifest_path = destination / "zone-review-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "overview_path": str(overview_path),
        "zone_crop_paths": crop_paths,
        "proposals_path": str(proposal_path),
        "manifest_path": str(manifest_path),
    }
