from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any, Mapping

from .records import CoordinateFrame, SourceIdentity


_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_FRAMES = {
    CoordinateFrame.PDF_POINT,
    CoordinateFrame.RASTER_PIXEL,
    CoordinateFrame.PAGE_MM,
}


class EvidenceValidationError(ValueError):
    """Raised when CEW-B01 geometric evidence violates its provenance contract."""


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceValidationError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise EvidenceValidationError(f"{name} must be finite")
    return result


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise EvidenceValidationError(f"{name} must be a positive integer")
    return value


def _canonical_sha256(mapping: Mapping[str, Any]) -> str:
    payload = json.dumps(
        mapping,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class AxisAlignedEvidenceRegion:
    frame: CoordinateFrame
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        if not isinstance(self.frame, CoordinateFrame) or self.frame not in _ALLOWED_FRAMES:
            raise EvidenceValidationError("evidence geometry requires a typed source/page coordinate frame")
        object.__setattr__(self, "x", _finite(self.x, "x"))
        object.__setattr__(self, "y", _finite(self.y, "y"))
        object.__setattr__(self, "width", _finite(self.width, "width"))
        object.__setattr__(self, "height", _finite(self.height, "height"))
        if self.width <= 0 or self.height <= 0:
            raise EvidenceValidationError("evidence region dimensions must be positive")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "frame": self.frame.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class Task3RasterBinding:
    source: SourceIdentity
    raster_width_px: int
    raster_height_px: int
    raster_sha256: str
    png_sha256: str
    renderer_tool_id: str
    renderer_tool_version: str
    frame: CoordinateFrame = CoordinateFrame.RASTER_PIXEL

    def __post_init__(self) -> None:
        if not isinstance(self.source, SourceIdentity):
            raise EvidenceValidationError("raster binding requires exact SourceIdentity")
        object.__setattr__(self, "raster_width_px", _positive_int(self.raster_width_px, "raster_width_px"))
        object.__setattr__(self, "raster_height_px", _positive_int(self.raster_height_px, "raster_height_px"))
        if not isinstance(self.raster_sha256, str) or not _HEX64.fullmatch(self.raster_sha256):
            raise EvidenceValidationError("raster_sha256 must be a 64-hex digest")
        if not isinstance(self.png_sha256, str) or not _HEX64.fullmatch(self.png_sha256):
            raise EvidenceValidationError("png_sha256 must be a 64-hex digest")
        if self.renderer_tool_id != "pypdfium2":
            raise EvidenceValidationError("Step 4 raster must come from the governed pypdfium2 renderer")
        if not isinstance(self.renderer_tool_version, str) or not self.renderer_tool_version:
            raise EvidenceValidationError("renderer tool version must be explicit")
        if self.frame != CoordinateFrame.RASTER_PIXEL:
            raise EvidenceValidationError("Step 4 raster binding must remain in RASTER_PIXEL")

    @classmethod
    def from_probe_mapping(cls, mapping: Mapping[str, Any]) -> "Task3RasterBinding":
        try:
            source_map = mapping["source"]
            raster_map = mapping["raster"]
            tool_results = mapping["tool_results"]
        except (KeyError, TypeError) as exc:
            raise EvidenceValidationError("invalid Step 3 probe mapping") from exc
        if not isinstance(source_map, Mapping) or not isinstance(raster_map, Mapping):
            raise EvidenceValidationError("invalid Step 3 source/raster mapping")
        source = SourceIdentity(
            repository=source_map["repository"],
            commit=source_map["commit"],
            path=source_map["path"],
            git_blob_sha=source_map["git_blob_sha"],
            sha256=source_map["sha256"],
            page_index=source_map["page_index"],
        )
        renderer: Mapping[str, Any] | None = None
        if isinstance(tool_results, list):
            for item in tool_results:
                if isinstance(item, Mapping) and item.get("tool_id") == "pypdfium2":
                    renderer = item
                    break
        if renderer is None or renderer.get("status") != "PASS":
            raise EvidenceValidationError("governed pypdfium2 PASS result is required")
        renderer_source = renderer.get("source")
        if not isinstance(renderer_source, Mapping) or renderer_source.get("sha256") != source.sha256:
            raise EvidenceValidationError("renderer result must bind the same exact source")
        metrics = renderer.get("metrics")
        if not isinstance(metrics, Mapping):
            raise EvidenceValidationError("renderer metrics are required")
        if metrics.get("png_role") != "EVIDENCE_RENDER_ONLY_NOT_STRUCTURAL_TRUTH":
            raise EvidenceValidationError("Step 3 render role is not governed for Evidence extraction")
        return cls(
            source=source,
            raster_width_px=raster_map["width_px"],
            raster_height_px=raster_map["height_px"],
            raster_sha256=raster_map["sha256"],
            png_sha256=metrics["png_sha256"],
            renderer_tool_id="pypdfium2",
            renderer_tool_version=renderer["tool_version"],
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "source": self.source.to_mapping(),
            "page_index": self.source.page_index,
            "frame": self.frame.value,
            "raster_width_px": self.raster_width_px,
            "raster_height_px": self.raster_height_px,
            "raster_sha256": self.raster_sha256,
            "png_sha256": self.png_sha256,
            "renderer": {
                "tool_id": self.renderer_tool_id,
                "tool_version": self.renderer_tool_version,
            },
        }


@dataclass(frozen=True)
class EvidenceRegionCandidate:
    candidate_id: str
    source: SourceIdentity
    page_index: int
    geometry: AxisAlignedEvidenceRegion
    geometry_digest: str
    method: str
    tool_id: str
    tool_version: str
    confidence: float
    status: str = "UNREVIEWED_GEOMETRIC_REGION"
    structural_identity_authorized: bool = False

    def __post_init__(self) -> None:
        if not self.candidate_id.startswith("CEW-B01-EV-"):
            raise EvidenceValidationError("candidate_id must use the CEW-B01 evidence namespace")
        if not isinstance(self.source, SourceIdentity):
            raise EvidenceValidationError("candidate requires exact SourceIdentity")
        if self.page_index != self.source.page_index:
            raise EvidenceValidationError("candidate page_index must match SourceIdentity")
        if not isinstance(self.geometry, AxisAlignedEvidenceRegion):
            raise EvidenceValidationError("candidate geometry must be typed")
        if not isinstance(self.geometry_digest, str) or not _HEX64.fullmatch(self.geometry_digest):
            raise EvidenceValidationError("geometry_digest must be a 64-hex digest")
        if not isinstance(self.method, str) or not self.method:
            raise EvidenceValidationError("method must be explicit")
        if not isinstance(self.tool_id, str) or not self.tool_id:
            raise EvidenceValidationError("tool_id must be explicit")
        if not isinstance(self.tool_version, str) or not self.tool_version:
            raise EvidenceValidationError("tool_version must be explicit")
        confidence = _finite(self.confidence, "confidence")
        if not 0.0 <= confidence <= 1.0:
            raise EvidenceValidationError("confidence must be within [0, 1]")
        object.__setattr__(self, "confidence", confidence)
        if self.status != "UNREVIEWED_GEOMETRIC_REGION":
            raise EvidenceValidationError("Step 4 evidence must remain unreviewed")
        if self.structural_identity_authorized is not False:
            raise EvidenceValidationError("Step 4 cannot authorize structural identity")

    @classmethod
    def create(
        cls,
        *,
        source: SourceIdentity,
        geometry: AxisAlignedEvidenceRegion,
        method: str,
        tool_id: str,
        tool_version: str,
        confidence: float,
    ) -> "EvidenceRegionCandidate":
        geometry_mapping = geometry.to_mapping()
        geometry_digest = _canonical_sha256(geometry_mapping)
        identity_payload = {
            "source_sha256": source.sha256,
            "page_index": source.page_index,
            "geometry_digest": geometry_digest,
            "method": method,
            "tool_id": tool_id,
            "tool_version": tool_version,
        }
        candidate_id = "CEW-B01-EV-" + _canonical_sha256(identity_payload)[:24]
        return cls(
            candidate_id=candidate_id,
            source=source,
            page_index=source.page_index,
            geometry=geometry,
            geometry_digest=geometry_digest,
            method=method,
            tool_id=tool_id,
            tool_version=tool_version,
            confidence=confidence,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "source": self.source.to_mapping(),
            "page_index": self.page_index,
            "geometry": self.geometry.to_mapping(),
            "geometry_digest": self.geometry_digest,
            "method": self.method,
            "tool": {"tool_id": self.tool_id, "tool_version": self.tool_version},
            "confidence": self.confidence,
            "status": self.status,
            "structural_identity_authorized": self.structural_identity_authorized,
        }
