"""
Task 1: Document Engine Data Model
Defines the Python dataclasses for the eTwin document chain.

Architecture: Page → SemanticRegion → Tile → EvidenceCrop → Claim → Entity/Candidate → Verification
Every geometric object carries bboxNative + bboxNormalized + pixelCoords + dxfCoords.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from pathlib import Path


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SemanticRegionType(str, Enum):
    PLAN = "PLAN"
    TITLE_BLOCK = "TITLE_BLOCK"
    SCHEDULE = "SCHEDULE"
    DETAIL = "DETAIL"
    ELEVATION = "ELEVATION"
    SECTION = "SECTION"
    NOTES = "NOTES"


class EvidenceStatus(str, Enum):
    DOC = "DOC"
    MIS = "MIS"
    RIF = "RIF"
    INF = "INF"
    INC = "INC"
    ND = "ND"


class VerificationCriterion(str, Enum):
    EVIDENCE_EXISTS = "EVIDENCE_EXISTS"
    SPATIAL_ALIGNMENT = "SPATIAL_ALIGNMENT"
    IDENTITY_MATCH = "IDENTITY_MATCH"
    PROPERTY_SUPPORT = "PROPERTY_SUPPORT"
    SOURCE_CONSISTENCY = "SOURCE_CONSISTENCY"


class VerificationStatus(str, Enum):
    MATCH = "MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    MISSING_IN_TWIN = "MISSING_IN_TWIN"
    MISSING_IN_DOCUMENT = "MISSING_IN_DOCUMENT"
    GEOMETRY_MISMATCH = "GEOMETRY_MISMATCH"
    CONFLICT = "CONFLICT"
    UNRESOLVED = "UNRESOLVED"


class ClaimStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    CONFLICTED = "CONFLICTED"
    REJECTED = "REJECTED"


class EntityIdentityStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANDIDATE = "CANDIDATE"
    UNRESOLVED = "UNRESOLVED"


class TileReadStatus(str, Enum):
    NOT_READ = "NOT_READ"
    PARTIAL = "PARTIAL"
    READ = "READ"
    NEEDS_REVIEW = "NEEDS_REVIEW"


# ---------------------------------------------------------------------------
# Coordinate Types
# ---------------------------------------------------------------------------

@dataclass
class BBoxNative:
    """Coordinates in original PDF coordinate space (points, origin bottom-left)."""
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def to_dict(self) -> dict:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}


@dataclass
class BBoxNormalized:
    """Coordinates as fractions [0..1] of page dimensions."""
    x0: float
    y0: float
    x1: float
    y1: float

    def to_dict(self) -> dict:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}


@dataclass
class PixelCoords:
    """Pixel coordinates at specific DPI."""
    x: int
    y: int
    width: int
    height: int
    dpi: int

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "width": self.width,
                "height": self.height, "dpi": self.dpi}


@dataclass
class DXFCoords:
    """DXF coordinate mapping when available."""
    x_mm: Optional[float] = None
    y_mm: Optional[float] = None
    dxf_handle: Optional[str] = None
    dxf_layer: Optional[str] = None

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class GeometricCoords:
    """Complete coordinate set for any geometric observation."""
    bbox_native: BBoxNative
    bbox_normalized: BBoxNormalized
    pixel_coords: Optional[PixelCoords] = None
    dxf_coords: Optional[DXFCoords] = None

    def to_dict(self) -> dict:
        d = {
            "bbox_native": self.bbox_native.to_dict(),
            "bbox_normalized": self.bbox_normalized.to_dict(),
        }
        if self.pixel_coords:
            d["pixel_coords"] = self.pixel_coords.to_dict()
        if self.dxf_coords:
            d["dxf_coords"] = self.dxf_coords.to_dict()
        return d


# ---------------------------------------------------------------------------
# Document Layer
# ---------------------------------------------------------------------------

@dataclass
class OriginalDocument:
    """Immutable source document with integrity hash."""
    document_id: str
    file_path: str
    sha256: str
    drawing_id: str
    discipline: str
    drawing_type: str
    page_count: int
    page_width_pts: float
    page_height_pts: float
    page_width_mm: float
    page_height_mm: float
    file_size_bytes: int
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> OriginalDocument:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class SemanticRegion:
    """Semantic area on a PDF page (not just spatial)."""
    region_id: str
    document_id: str
    page_number: int
    region_type: SemanticRegionType
    label: str
    coords: GeometricCoords
    evidence_status: EvidenceStatus = EvidenceStatus.ND
    source_text: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["region_type"] = self.region_type.value
        d["evidence_status"] = self.evidence_status.value
        return d


@dataclass
class Tile:
    """Adaptive spatial window for reading a region."""
    tile_id: str
    region_id: str
    document_id: str
    page_number: int
    coords: GeometricCoords
    overlap_fraction: float = 0.1
    read_status: TileReadStatus = TileReadStatus.NOT_READ
    generation_method: str = "adaptive_grid"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["read_status"] = self.read_status.value
        return d


# ---------------------------------------------------------------------------
# Evidence Layer
# ---------------------------------------------------------------------------

@dataclass
class EvidenceCrop:
    """Proof of a claim, linked to source document."""
    evidence_id: str
    document_id: str
    page_number: int
    crop_path: str
    coords: GeometricCoords
    method: str = "pdfium_render"
    status: EvidenceStatus = EvidenceStatus.ND
    confidence: float = 0.0
    raw_reading: str = ""
    normalized_reading: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class Claim:
    """What is asserted about a structural element."""
    claim_id: str
    entity_id: str
    property_name: str
    property_value: str
    evidence_refs: list[str] = field(default_factory=list)
    source_document_id: str = ""
    status: ClaimStatus = ClaimStatus.ACTIVE
    confidence: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


# ---------------------------------------------------------------------------
# Entity Layer
# ---------------------------------------------------------------------------

@dataclass
class StructuralEntity:
    """Confirmed structural identity."""
    entity_id: str
    entity_type: str  # Column, Beam, Slab, etc.
    identity_status: EntityIdentityStatus = EntityIdentityStatus.CONFIRMED
    position_x_mm: Optional[float] = None
    position_y_mm: Optional[float] = None
    vertical_start: Optional[str] = None
    vertical_end: Optional[str] = None
    termination_reason: Optional[str] = None
    claim_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["identity_status"] = self.identity_status.value
        return d


@dataclass
class DocumentEntityCandidate:
    """Unresolved structural identity — not yet promoted to StructuralEntity."""
    candidate_id: str
    entity_type: str
    identity_status: EntityIdentityStatus = EntityIdentityStatus.CANDIDATE
    possible_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    resolution_notes: str = ""
    blocking_residual: str = ""  # e.g., "R-R1-01"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["identity_status"] = self.identity_status.value
        return d


# ---------------------------------------------------------------------------
# Resolution Layer
# ---------------------------------------------------------------------------

@dataclass
class PropertyResolution:
    """Links entity/candidate → property → claim → evidence → crop → PDF."""
    resolution_id: str
    entity_id: str
    property_name: str
    claim_id: str
    evidence_id: str
    crop_path: str
    document_id: str
    page_number: int
    status: str = "RESOLVED"  # RESOLVED | CANDIDATES | CONFLICT | ND

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Verification Layer
# ---------------------------------------------------------------------------

@dataclass
class VerificationCheck:
    """Single criterion check result."""
    criterion: VerificationCriterion
    passed: bool
    details: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["criterion"] = self.criterion.value
        return d


@dataclass
class VerificationResult:
    """Multi-criteria verification of eTwin entity against source."""
    result_id: str
    entity_id: str
    property_name: str
    status: VerificationStatus
    checks: list[VerificationCheck] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["checks"] = [c.to_dict() for c in self.checks]
        return d


# ---------------------------------------------------------------------------
# Document Map (top-level container)
# ---------------------------------------------------------------------------

@dataclass
class DocumentMap:
    """Persistent map of a PDF document's semantic structure."""
    map_id: str
    document_id: str
    version: int = 1
    regions: list[SemanticRegion] = field(default_factory=list)
    tiles: list[Tile] = field(default_factory=list)
    created_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "map_id": self.map_id,
            "document_id": self.document_id,
            "version": self.version,
            "regions": [r.to_dict() for r in self.regions],
            "tiles": [t.to_dict() for t in self.tiles],
            "created_at": self.created_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DocumentMap:
        regions = [SemanticRegion(
            region_id=r["region_id"],
            document_id=r["document_id"],
            page_number=r["page_number"],
            region_type=SemanticRegionType(r["region_type"]),
            label=r["label"],
            coords=GeometricCoords(
                bbox_native=BBoxNative(**r["coords"]["bbox_native"]),
                bbox_normalized=BBoxNormalized(**r["coords"]["bbox_normalized"]),
            ),
            evidence_status=EvidenceStatus(r.get("evidence_status", "ND")),
            source_text=r.get("source_text", ""),
        ) for r in d.get("regions", [])]

        tiles = [Tile(
            tile_id=t["tile_id"],
            region_id=t["region_id"],
            document_id=t["document_id"],
            page_number=t["page_number"],
            coords=GeometricCoords(
                bbox_native=BBoxNative(**t["coords"]["bbox_native"]),
                bbox_normalized=BBoxNormalized(**t["coords"]["bbox_normalized"]),
            ),
            overlap_fraction=t.get("overlap_fraction", 0.1),
            read_status=TileReadStatus(t.get("read_status", "NOT_READ")),
        ) for t in d.get("tiles", [])]

        return cls(
            map_id=d["map_id"],
            document_id=d["document_id"],
            version=d.get("version", 1),
            regions=regions,
            tiles=tiles,
            created_at=d.get("created_at", ""),
            notes=d.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def save_json(data, path: Path):
    """Save any dataclass or dict to JSON."""
    if hasattr(data, 'to_dict'):
        d = data.to_dict()
    elif isinstance(data, list):
        d = [item.to_dict() if hasattr(item, 'to_dict') else item for item in data]
    else:
        d = data
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def load_json(path: Path):
    """Load JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
