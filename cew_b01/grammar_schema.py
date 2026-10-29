from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from typing import Any, Mapping

from .records import CoordinateFrame, SourceIdentity


class GrammarValidationError(ValueError):
    """Raised when grammar-foundation evidence violates the G0-G2 contract."""


class DocumentRegionKind(str, Enum):
    STRUCTURAL_WORKAREA = "STRUCTURAL_WORKAREA"
    TITLE_BLOCK = "TITLE_BLOCK"
    LOCATION_DIAGRAM = "LOCATION_DIAGRAM"
    APPROVAL_STAMP_SIGNATURE = "APPROVAL_STAMP_SIGNATURE"
    NOTE_OR_LEGEND_REGION = "NOTE_OR_LEGEND_REGION"
    MARGIN_VOID = "MARGIN_VOID"
    SCAN_ARTIFACT = "SCAN_ARTIFACT"
    UNKNOWN_DOCUMENT_REGION = "UNKNOWN_DOCUMENT_REGION"


class PrimitiveFamily(str, Enum):
    LINE_SEGMENT = "LINE_SEGMENT"
    PARALLEL_LINE_PAIR = "PARALLEL_LINE_PAIR"
    INTERSECTION = "INTERSECTION"
    T_JUNCTION = "T_JUNCTION"
    LINE_ENDPOINT = "LINE_ENDPOINT"
    RECTILINEAR_CLOSED_SHAPE = "RECTILINEAR_CLOSED_SHAPE"
    RECTILINEAR_OPEN_SHAPE = "RECTILINEAR_OPEN_SHAPE"
    L_SHAPED_MOTIF = "L_SHAPED_MOTIF"
    T_SHAPED_MOTIF = "T_SHAPED_MOTIF"
    CROSS_MOTIF = "CROSS_MOTIF"
    FILLED_OR_HATCHED_REGION = "FILLED_OR_HATCHED_REGION"
    TEXT_BLOCK = "TEXT_BLOCK"
    DIMENSION_LINE_OR_TICK_CANDIDATE = "DIMENSION_LINE_OR_TICK_CANDIDATE"
    LEADER_OR_CALLOUT_CANDIDATE = "LEADER_OR_CALLOUT_CANDIDATE"
    COMPLEX_GRAPHIC_GROUP = "COMPLEX_GRAPHIC_GROUP"
    UNKNOWN_GRAPHIC_GROUP = "UNKNOWN_GRAPHIC_GROUP"


class MotifClassificationState(str, Enum):
    UNCLASSIFIED = "UNCLASSIFIED"
    FUNCTIONALLY_CLASSIFIED = "FUNCTIONALLY_CLASSIFIED"
    NON_STRUCTURAL = "NON_STRUCTURAL"
    ARTIFACT = "ARTIFACT"
    UNKNOWN_EXCEPTION = "UNKNOWN_EXCEPTION"


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GrammarValidationError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise GrammarValidationError(f"{name} must be finite")
    return result


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise GrammarValidationError(f"{name} must be a positive integer")
    return value


def _validate_geometry(
    *,
    frame: CoordinateFrame,
    raster_width: int,
    raster_height: int,
    x: Any,
    y: Any,
    width: Any,
    height: Any,
) -> tuple[float, float, float, float]:
    if frame != CoordinateFrame.RASTER_PIXEL:
        raise GrammarValidationError("G0-G2 raster geometry requires CoordinateFrame.RASTER_PIXEL")
    rw = _positive_int(raster_width, "raster_width")
    rh = _positive_int(raster_height, "raster_height")
    gx = _finite(x, "x")
    gy = _finite(y, "y")
    gw = _finite(width, "width")
    gh = _finite(height, "height")
    if gx < 0 or gy < 0 or gw <= 0 or gh <= 0:
        raise GrammarValidationError("geometry must be positive and inside the raster frame")
    if gx + gw > rw or gy + gh > rh:
        raise GrammarValidationError("geometry exceeds the raster frame")
    return gx, gy, gw, gh


@dataclass(frozen=True)
class DocumentRegionMask:
    region_id: str
    source: SourceIdentity
    page_index: int
    frame: CoordinateFrame
    raster_width: int
    raster_height: int
    x: float
    y: float
    width: float
    height: float
    kind: DocumentRegionKind
    method: str
    human_confirmed: bool
    geometry_digest: str
    structural_identity_authorized: bool = False
    canonical_write_authorized: bool = False

    @classmethod
    def create(
        cls,
        *,
        source: SourceIdentity,
        frame: CoordinateFrame,
        raster_width: int,
        raster_height: int,
        x: float,
        y: float,
        width: float,
        height: float,
        kind: DocumentRegionKind,
        method: str,
        human_confirmed: bool,
    ) -> "DocumentRegionMask":
        if not isinstance(source, SourceIdentity):
            raise GrammarValidationError("DocumentRegionMask requires SourceIdentity")
        if not isinstance(kind, DocumentRegionKind):
            raise GrammarValidationError("kind must be DocumentRegionKind")
        if not isinstance(human_confirmed, bool):
            raise GrammarValidationError("human_confirmed must be boolean")
        if not isinstance(method, str) or not method:
            raise GrammarValidationError("method must be explicit")
        gx, gy, gw, gh = _validate_geometry(
            frame=frame,
            raster_width=raster_width,
            raster_height=raster_height,
            x=x,
            y=y,
            width=width,
            height=height,
        )
        geometry = {
            "frame": frame.value,
            "x": gx,
            "y": gy,
            "width": gw,
            "height": gh,
        }
        geometry_digest = _canonical_hash(geometry)
        identity = {
            "source_sha256": source.sha256,
            "page_index": source.page_index,
            "geometry_digest": geometry_digest,
            "kind": kind.value,
            "method": method,
        }
        return cls(
            region_id="CEW-B01-ZONE-" + _canonical_hash(identity)[:24],
            source=source,
            page_index=source.page_index,
            frame=frame,
            raster_width=raster_width,
            raster_height=raster_height,
            x=gx,
            y=gy,
            width=gw,
            height=gh,
            kind=kind,
            method=method,
            human_confirmed=human_confirmed,
            geometry_digest=geometry_digest,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "source": self.source.to_mapping(),
            "page_index": self.page_index,
            "frame": self.frame.value,
            "raster": {"width": self.raster_width, "height": self.raster_height},
            "geometry": {"x": self.x, "y": self.y, "width": self.width, "height": self.height},
            "kind": self.kind.value,
            "method": self.method,
            "human_confirmed": self.human_confirmed,
            "geometry_digest": self.geometry_digest,
            "structural_identity_authorized": self.structural_identity_authorized,
            "canonical_write_authorized": self.canonical_write_authorized,
        }


@dataclass(frozen=True)
class GraphicPrimitiveObservation:
    primitive_id: str
    source: SourceIdentity
    page_index: int
    frame: CoordinateFrame
    raster_width: int
    raster_height: int
    x: float
    y: float
    width: float
    height: float
    family: PrimitiveFamily
    detector: str
    feature_signature: Mapping[str, Any]
    geometry_digest: str
    semantic_meaning: None = None
    structural_identity_authorized: bool = False
    canonical_write_authorized: bool = False

    @classmethod
    def create(
        cls,
        *,
        source: SourceIdentity,
        frame: CoordinateFrame,
        raster_width: int,
        raster_height: int,
        x: float,
        y: float,
        width: float,
        height: float,
        family: PrimitiveFamily,
        detector: str,
        feature_signature: Mapping[str, Any],
    ) -> "GraphicPrimitiveObservation":
        if not isinstance(source, SourceIdentity):
            raise GrammarValidationError("GraphicPrimitiveObservation requires SourceIdentity")
        if not isinstance(family, PrimitiveFamily):
            raise GrammarValidationError("family must be PrimitiveFamily")
        if not isinstance(detector, str) or not detector:
            raise GrammarValidationError("detector must be explicit")
        gx, gy, gw, gh = _validate_geometry(
            frame=frame,
            raster_width=raster_width,
            raster_height=raster_height,
            x=x,
            y=y,
            width=width,
            height=height,
        )
        geometry = {"frame": frame.value, "x": gx, "y": gy, "width": gw, "height": gh}
        geometry_digest = _canonical_hash(geometry)
        signature = dict(feature_signature)
        identity = {
            "source_sha256": source.sha256,
            "page_index": source.page_index,
            "geometry_digest": geometry_digest,
            "family": family.value,
            "detector": detector,
            "feature_signature": signature,
        }
        return cls(
            primitive_id="CEW-B01-GP-" + _canonical_hash(identity)[:24],
            source=source,
            page_index=source.page_index,
            frame=frame,
            raster_width=raster_width,
            raster_height=raster_height,
            x=gx,
            y=gy,
            width=gw,
            height=gh,
            family=family,
            detector=detector,
            feature_signature=signature,
            geometry_digest=geometry_digest,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "primitive_id": self.primitive_id,
            "source": self.source.to_mapping(),
            "page_index": self.page_index,
            "frame": self.frame.value,
            "raster": {"width": self.raster_width, "height": self.raster_height},
            "geometry": {"x": self.x, "y": self.y, "width": self.width, "height": self.height},
            "family": self.family.value,
            "detector": self.detector,
            "feature_signature": dict(self.feature_signature),
            "geometry_digest": self.geometry_digest,
            "semantic_meaning": self.semantic_meaning,
            "structural_identity_authorized": self.structural_identity_authorized,
            "canonical_write_authorized": self.canonical_write_authorized,
        }


@dataclass(frozen=True)
class RecurringMotif:
    motif_id: str
    source: SourceIdentity
    page_index: int
    member_primitive_ids: tuple[str, ...]
    representative_primitive_id: str
    neutral_descriptor: Mapping[str, Any]
    occurrence_count: int
    classification_state: MotifClassificationState = MotifClassificationState.UNCLASSIFIED
    semantic_meaning: None = None
    structural_identity_authorized: bool = False
    canonical_write_authorized: bool = False

    @classmethod
    def create(
        cls,
        *,
        source: SourceIdentity,
        member_primitive_ids: tuple[str, ...],
        representative_primitive_id: str,
        neutral_descriptor: Mapping[str, Any],
    ) -> "RecurringMotif":
        if not isinstance(source, SourceIdentity):
            raise GrammarValidationError("RecurringMotif requires SourceIdentity")
        members = tuple(sorted(set(member_primitive_ids)))
        if not members:
            raise GrammarValidationError("RecurringMotif requires at least one primitive")
        if representative_primitive_id not in members:
            raise GrammarValidationError("representative primitive must be a motif member")
        descriptor = dict(neutral_descriptor)
        identity = {
            "source_sha256": source.sha256,
            "page_index": source.page_index,
            "member_primitive_ids": members,
            "representative_primitive_id": representative_primitive_id,
            "neutral_descriptor": descriptor,
        }
        return cls(
            motif_id="CEW-B01-MOTIF-" + _canonical_hash(identity)[:24],
            source=source,
            page_index=source.page_index,
            member_primitive_ids=members,
            representative_primitive_id=representative_primitive_id,
            neutral_descriptor=descriptor,
            occurrence_count=len(members),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "motif_id": self.motif_id,
            "source": self.source.to_mapping(),
            "page_index": self.page_index,
            "member_primitive_ids": list(self.member_primitive_ids),
            "representative_primitive_id": self.representative_primitive_id,
            "neutral_descriptor": dict(self.neutral_descriptor),
            "occurrence_count": self.occurrence_count,
            "classification_state": self.classification_state.value,
            "semantic_meaning": self.semantic_meaning,
            "structural_identity_authorized": self.structural_identity_authorized,
            "canonical_write_authorized": self.canonical_write_authorized,
        }
