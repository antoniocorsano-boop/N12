from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math
import re
from typing import Any, Mapping


class RecordValidationError(ValueError):
    """Raised when a CEW-B01 record violates its typed contract."""


class FrameTransformError(ValueError):
    """Raised when coordinates are transformed without a compatible frame."""


class CoordinateFrame(str, Enum):
    PDF_POINT = "PDF_POINT"
    RASTER_PIXEL = "RASTER_PIXEL"
    PAGE_MM = "PAGE_MM"


class ToolResultStatus(str, Enum):
    PASS = "PASS"
    LIMITED = "LIMITED"
    FAIL = "FAIL"
    NOT_TRIGGERED = "NOT_TRIGGERED"


_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RecordValidationError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise RecordValidationError(f"{name} must be finite")
    return result


@dataclass(frozen=True)
class Coordinate2D:
    frame: CoordinateFrame
    x: float
    y: float

    def __post_init__(self) -> None:
        if not isinstance(self.frame, CoordinateFrame):
            raise RecordValidationError("coordinate frame must be a CoordinateFrame")
        object.__setattr__(self, "x", _finite(self.x, "x"))
        object.__setattr__(self, "y", _finite(self.y, "y"))

    def __add__(self, other: object) -> "Coordinate2D":
        raise TypeError("coordinates cannot be combined without an explicit frame-aware operation")

    def __sub__(self, other: object) -> "Coordinate2D":
        raise TypeError("coordinates cannot be combined without an explicit frame-aware operation")

    def to_mapping(self) -> dict[str, Any]:
        return {"frame": self.frame.value, "x": self.x, "y": self.y}


@dataclass(frozen=True)
class FrameTransform:
    source_frame: CoordinateFrame
    target_frame: CoordinateFrame
    matrix: tuple[float, float, float, float, float, float, float, float, float]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.source_frame, CoordinateFrame) or not isinstance(
            self.target_frame, CoordinateFrame
        ):
            raise RecordValidationError("transform frames must be CoordinateFrame values")
        if len(self.matrix) != 9:
            raise RecordValidationError("transform matrix must contain exactly 9 values")
        matrix = tuple(_finite(value, "transform matrix value") for value in self.matrix)
        if matrix[6:] != (0.0, 0.0, 1.0):
            raise RecordValidationError("only explicit affine 2D transforms are supported")
        object.__setattr__(self, "matrix", matrix)
        object.__setattr__(self, "metadata", dict(self.metadata))

    def apply(self, point: Coordinate2D) -> Coordinate2D:
        if point.frame != self.source_frame:
            raise FrameTransformError(
                f"transform requires {self.source_frame.value}, got {point.frame.value}"
            )
        m = self.matrix
        x = m[0] * point.x + m[1] * point.y + m[2]
        y = m[3] * point.x + m[4] * point.y + m[5]
        return Coordinate2D(self.target_frame, x, y)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "source_frame": self.source_frame.value,
            "target_frame": self.target_frame.value,
            "matrix": list(self.matrix),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class SourceIdentity:
    repository: str
    commit: str
    path: str
    git_blob_sha: str
    sha256: str
    page_index: int

    def __post_init__(self) -> None:
        if not isinstance(self.repository, str) or self.repository.count("/") != 1:
            raise RecordValidationError("repository must be owner/repository")
        if not isinstance(self.commit, str) or not _HEX40.fullmatch(self.commit):
            raise RecordValidationError("commit must be an exact 40-hex SHA")
        if not isinstance(self.git_blob_sha, str) or not _HEX40.fullmatch(self.git_blob_sha):
            raise RecordValidationError("git_blob_sha must be an exact 40-hex SHA")
        if not isinstance(self.sha256, str) or not _HEX64.fullmatch(self.sha256):
            raise RecordValidationError("sha256 must be an exact 64-hex digest")
        if not isinstance(self.path, str) or not self.path:
            raise RecordValidationError("path must be non-empty")
        if isinstance(self.page_index, bool) or not isinstance(self.page_index, int) or self.page_index < 0:
            raise RecordValidationError("page_index must be a non-negative integer")

    @classmethod
    def from_materialized(cls, materialized: Any) -> "SourceIdentity":
        contract = materialized.contract
        return cls(
            repository=contract.repository,
            commit=contract.commit,
            path=contract.path,
            git_blob_sha=materialized.git_blob_sha,
            sha256=materialized.sha256,
            page_index=contract.page_index,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "commit": self.commit,
            "path": self.path,
            "git_blob_sha": self.git_blob_sha,
            "sha256": self.sha256,
            "page_index": self.page_index,
        }


@dataclass(frozen=True)
class OcrTriggerDecision:
    triggered: bool
    reason: str
    basis: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.triggered, bool):
            raise RecordValidationError("OCR trigger flag must be boolean")
        if not isinstance(self.reason, str) or not self.reason:
            raise RecordValidationError("OCR trigger reason must be non-empty")
        object.__setattr__(self, "basis", dict(self.basis))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "triggered": self.triggered,
            "reason": self.reason,
            "basis": dict(self.basis),
        }


@dataclass(frozen=True)
class ToolProbeResult:
    source: SourceIdentity
    tool_id: str
    tool_version: str
    status: ToolResultStatus
    metrics: Mapping[str, Any]
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source, SourceIdentity):
            raise RecordValidationError("tool result must bind an exact SourceIdentity")
        if not isinstance(self.tool_id, str) or not self.tool_id.strip():
            raise RecordValidationError("tool_id must be non-empty")
        if not isinstance(self.tool_version, str) or not self.tool_version.strip():
            raise RecordValidationError("tool_version must be non-empty")
        if not isinstance(self.status, ToolResultStatus):
            raise RecordValidationError("status must be a ToolResultStatus")
        if not isinstance(self.metrics, Mapping):
            raise RecordValidationError("metrics must be a mapping")
        if not all(isinstance(item, str) and item for item in self.limitations):
            raise RecordValidationError("limitations must contain non-empty strings")
        object.__setattr__(self, "metrics", dict(self.metrics))
        object.__setattr__(self, "limitations", tuple(self.limitations))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "source": self.source.to_mapping(),
            "tool_id": self.tool_id,
            "tool_version": self.tool_version,
            "status": self.status.value,
            "metrics": dict(self.metrics),
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class PdfProbeResult:
    source: SourceIdentity
    renderer_tool_id: str
    renderer_version: str
    render_dpi: int
    page_width_points: float
    page_height_points: float
    raster_width_px: int
    raster_height_px: int
    raster_sha256: str
    render_transform: FrameTransform
    ocr_trigger: OcrTriggerDecision
    tool_results: tuple[ToolProbeResult, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source, SourceIdentity):
            raise RecordValidationError("PDF probe must bind an exact SourceIdentity")
        if not isinstance(self.renderer_tool_id, str) or not self.renderer_tool_id:
            raise RecordValidationError("renderer_tool_id must be non-empty")
        if not isinstance(self.renderer_version, str) or not self.renderer_version:
            raise RecordValidationError("renderer_version must be non-empty")
        if isinstance(self.render_dpi, bool) or not isinstance(self.render_dpi, int) or self.render_dpi <= 0:
            raise RecordValidationError("render_dpi must be a positive integer")
        object.__setattr__(self, "page_width_points", _finite(self.page_width_points, "page_width_points"))
        object.__setattr__(self, "page_height_points", _finite(self.page_height_points, "page_height_points"))
        if self.page_width_points <= 0 or self.page_height_points <= 0:
            raise RecordValidationError("page dimensions must be positive")
        if isinstance(self.raster_width_px, bool) or not isinstance(self.raster_width_px, int) or self.raster_width_px <= 0:
            raise RecordValidationError("raster_width_px must be positive")
        if isinstance(self.raster_height_px, bool) or not isinstance(self.raster_height_px, int) or self.raster_height_px <= 0:
            raise RecordValidationError("raster_height_px must be positive")
        if not isinstance(self.raster_sha256, str) or not _HEX64.fullmatch(self.raster_sha256):
            raise RecordValidationError("raster_sha256 must be a 64-hex digest")
        if self.render_transform.source_frame != CoordinateFrame.PDF_POINT:
            raise RecordValidationError("render transform must start in PDF_POINT")
        if self.render_transform.target_frame != CoordinateFrame.RASTER_PIXEL:
            raise RecordValidationError("render transform must end in RASTER_PIXEL")
        for result in self.tool_results:
            if result.source != self.source:
                raise RecordValidationError("all tool results must bind the same exact source")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "source": self.source.to_mapping(),
            "renderer": {
                "tool_id": self.renderer_tool_id,
                "version": self.renderer_version,
                "dpi": self.render_dpi,
            },
            "page": {
                "width_points": self.page_width_points,
                "height_points": self.page_height_points,
            },
            "raster": {
                "width_px": self.raster_width_px,
                "height_px": self.raster_height_px,
                "sha256": self.raster_sha256,
            },
            "render_transform": self.render_transform.to_mapping(),
            "ocr_trigger": self.ocr_trigger.to_mapping(),
            "tool_results": [result.to_mapping() for result in self.tool_results],
        }

    def receipt_mapping(self) -> dict[str, Any]:
        mapping = self.to_mapping()
        for result in mapping["tool_results"]:
            metrics = result["metrics"]
            if metrics.get("output_role") == "OCR_DERIVATIVE_EVIDENCE_NOT_SOURCE_AUTHORITY":
                metrics.pop("output_sha256", None)
        return mapping

    def deterministic_receipt_sha256(self) -> str:
        payload = json.dumps(
            self.receipt_mapping(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
