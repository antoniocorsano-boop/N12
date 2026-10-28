from __future__ import annotations

"""CEW-B01 adapter into existing CEW discovery/similarity contracts.

This module creates no semantic truth. It preserves exact B01 source identity,
derives nonauthoritative compatibility IDs for reused contracts, and maps B01
closed-frame observations into the structured descriptor vocabulary from PR #137
and the deterministic OA-3 signal vocabulary from PR #116.
"""

import hashlib
import json
from typing import Any, Iterable

from .drawing_grammar import DrawingMotif
from .evidence_schema import Task3RasterBinding
from .reused_oa3_similarity import OA3_CAPABILITY_ID, OA3_SOURCE_REF

PR137_DESCRIPTOR_CAPABILITY_ID = "CEW-CAP-ZERO-PRIOR-GRAPHIC-DISCOVERY-V1"
PR137_VISUAL_LEARNING_CAPABILITY_ID = "CEW-CAP-VISUAL-PROTOTYPE-LEARNING-V1"
PR137_SOURCE_REF = "320755e66a7263f1842f73dc14fb9a0ea8ccd7f8"
PR143_GRAMMAR_CAPABILITY_ID = "CEW-CAP-ENG-DRAWING-GRAMMAR-V1"
PR143_SOURCE_REF = "098f98d2724c0a16b9293adc366a585f356bc9fc"
STRUCTURED_PROVIDER_ID = "CEW_STRUCTURED_GRAPHIC_DESCRIPTOR_V1"
STRUCTURED_PROVIDER_VERSION = "1.0.0"
ADAPTER_VERSION = "CEW_B01_REUSE_ADAPTER_v1"

_AUTHORITY = {
    "semantic_authority": "NONE",
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "engineering_authority_effect": "NONE",
    "human_review_required": True,
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _stable_id(prefix: str, payload: Any, length: int = 24) -> str:
    digest = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
    return prefix + digest[:length]


def _derived_source_identity(binding: Task3RasterBinding) -> dict[str, Any]:
    original = binding.source.to_mapping()
    source_version_id = _stable_id(
        "CEW-B01-DERIVED-SV-",
        {"source": original, "role": "SOURCE_VERSION_COMPATIBILITY_ID"},
    )
    page_id = _stable_id(
        "CEW-B01-DERIVED-PAGE-",
        {
            "source_version_id": source_version_id,
            "page_index": binding.source.page_index,
            "role": "PAGE_COMPATIBILITY_ID",
        },
    )
    evidence_region_id = _stable_id(
        "CEW-B01-DERIVED-PAGE-REGION-",
        {
            "page_id": page_id,
            "raster_width_px": binding.raster_width_px,
            "raster_height_px": binding.raster_height_px,
            "role": "WHOLE_PAGE_REUSE_SCENE",
        },
    )
    return {
        "source_version_id": source_version_id,
        "page_id": page_id,
        "evidence_region_id": evidence_region_id,
        "source_sha256": binding.source.sha256,
        "page_index": binding.source.page_index,
        "original_source": original,
        "derived_identity_authority": "NONE_COMPATIBILITY_ONLY",
    }


def _aspect_bucket(width: float, height: float) -> str:
    ratio = width / max(height, 1e-12)
    if ratio < 0.35:
        return "VERY_TALL"
    if ratio < 0.75:
        return "TALL"
    if ratio <= 1.35:
        return "SQUAREISH"
    if ratio <= 2.85:
        return "WIDE"
    return "VERY_WIDE"


def _area_bucket(normalized_width: float, normalized_height: float) -> str:
    area = normalized_width * normalized_height
    if area < 0.0001:
        return "TINY"
    if area < 0.001:
        return "SMALL"
    if area < 0.01:
        return "MEDIUM"
    return "LARGE"


def _complexity_bucket(component_count: int) -> str:
    if component_count <= 1:
        return "ONE"
    if component_count <= 4:
        return "FEW"
    if component_count <= 12:
        return "MEDIUM"
    return "MANY"


def _context_code(signature: tuple[float, float, float, float]) -> str:
    active = tuple(value >= 0.03 for value in signature)
    return "_".join(
        f"{name}{1 if state else 0}"
        for name, state in zip(("L", "R", "T", "B"), active)
    )


def _structured_descriptor(
    binding: Task3RasterBinding,
    motif: DrawingMotif,
) -> dict[str, Any]:
    normalized_width = motif.width / binding.raster_width_px
    normalized_height = motif.height / binding.raster_height_px
    signature = {
        "primitive_family": "RECTILINEAR_CLOSED_SHAPE",
        "aspect_bucket": _aspect_bucket(float(motif.width), float(motif.height)),
        "area_bucket": _area_bucket(normalized_width, normalized_height),
        "complexity_bucket": _complexity_bucket(motif.internal_component_count),
        "filled": False,
        "stroke_width_bucket": "NA",
    }
    return {
        "provider_id": STRUCTURED_PROVIDER_ID,
        "provider_version": STRUCTURED_PROVIDER_VERSION,
        "source_capability_id": PR137_DESCRIPTOR_CAPABILITY_ID,
        "source_ref": PR137_SOURCE_REF,
        "feature_signature": signature,
        "semantic_authority": "NONE",
    }


def _object_from_motif(binding: Task3RasterBinding, motif: DrawingMotif) -> dict[str, Any]:
    if motif.semantic_identity is not None:
        raise ValueError("B01_REUSE_ADAPTER_SEMANTIC_MOTIF_NOT_ALLOWED")
    context_code = _context_code(motif.context_signature)
    return {
        "object_id": motif.motif_id,
        "geometry": {
            "type": "RECTANGLE",
            "coordinate_frame": "RASTER_PIXEL",
            "x": motif.x,
            "y": motif.y,
            "width": motif.width,
            "height": motif.height,
        },
        "properties": {
            "aspect_ratio": round(motif.aspect_ratio, 9),
            "orientation": "AXIS_ALIGNED",
            "topology_hint": context_code,
            "spatial_context": context_code,
            "associated_text": None,
            "frame_coverage": motif.frame_coverage,
            "internal_ink_ratio": motif.internal_ink_ratio,
            "internal_component_count": motif.internal_component_count,
        },
        "structured_descriptor": _structured_descriptor(binding, motif),
        "authority": dict(_AUTHORITY),
    }


def build_oa3_scene(
    binding: Task3RasterBinding,
    motifs: Iterable[DrawingMotif],
) -> dict[str, Any]:
    if not isinstance(binding, Task3RasterBinding):
        raise ValueError("B01_REUSE_ADAPTER_TASK3_BINDING_REQUIRED")
    objects = tuple(
        sorted(
            (_object_from_motif(binding, motif) for motif in motifs),
            key=lambda item: str(item["object_id"]),
        )
    )
    object_ids = [str(item["object_id"]) for item in objects]
    if len(object_ids) != len(set(object_ids)):
        raise ValueError("B01_REUSE_ADAPTER_DUPLICATE_OBJECT_ID")
    return {
        "schema": "CEW_B01_OA3_REUSE_SCENE_v1",
        "adapter_version": ADAPTER_VERSION,
        "source": _derived_source_identity(binding),
        "objects": list(objects),
        "reuse": {
            "oa3_capability_id": OA3_CAPABILITY_ID,
            "oa3_source_ref": OA3_SOURCE_REF,
            "structured_descriptor_capability_id": PR137_DESCRIPTOR_CAPABILITY_ID,
            "structured_descriptor_source_ref": PR137_SOURCE_REF,
            "visual_learning_capability_id": PR137_VISUAL_LEARNING_CAPABILITY_ID,
            "engineering_grammar_capability_id": PR143_GRAMMAR_CAPABILITY_ID,
            "engineering_grammar_source_ref": PR143_SOURCE_REF,
        },
        "authority": dict(_AUTHORITY),
    }


def build_human_taught_oa3_prototype(
    scene: dict[str, Any],
    *,
    anchor_object_id: str,
    human_decision_id: str,
    prototype_id: str,
    object_type: str,
    family_id: str,
) -> dict[str, Any]:
    decision = str(human_decision_id or "").strip()
    if not decision:
        raise ValueError("B01_REUSE_ADAPTER_HUMAN_DECISION_REQUIRED")
    anchor = str(anchor_object_id or "").strip()
    if not anchor:
        raise ValueError("B01_REUSE_ADAPTER_ANCHOR_REQUIRED")
    if not any(item.get("object_id") == anchor for item in scene.get("objects", [])):
        raise ValueError("B01_REUSE_ADAPTER_ANCHOR_NOT_IN_SCENE")
    prototype = str(prototype_id or "").strip()
    proposed_type = str(object_type or "").strip()
    proposed_family = str(family_id or "").strip()
    if not prototype or not proposed_type or not proposed_family:
        raise ValueError("B01_REUSE_ADAPTER_PROTOTYPE_FIELDS_REQUIRED")
    source = scene.get("source")
    if not isinstance(source, dict):
        raise ValueError("B01_REUSE_ADAPTER_SOURCE_REQUIRED")
    return {
        "state": "HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE",
        "prototype_id": prototype,
        "anchor_object_id": anchor,
        "human_decision_id": decision,
        "object_type": proposed_type,
        "family_id": proposed_family,
        "source_evidence": dict(source),
        "prototype_scope": "PROJECT_LOCAL_NON_CANONICAL",
        "human_confirmation_required": True,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
