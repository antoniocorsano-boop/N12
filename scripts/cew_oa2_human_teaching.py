#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from typing import Any

ALLOWED_TYPES = {
    "COLUMN", "BEAM", "BEAM_SECTION_SYMBOL", "SLAB", "FOUNDATION_BEAM",
    "LONGITUDINAL_REBAR", "STIRRUP", "GRID_AXIS", "DIMENSION", "CALLOUT",
    "NODE", "TECHNICAL_TEXT",
}


def _slug(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.strip().upper())
    return "_".join(part for part in cleaned.split("_") if part)[:64]


def create_teaching_proposal(scene: dict[str, Any], payload: dict[str, Any], revision: str) -> dict[str, Any]:
    anchor_id = str(payload.get("anchor_object_id", "")).strip()
    object_type = str(payload.get("object_type", "")).strip().upper()
    family_label = str(payload.get("family_label", "")).strip()
    reviewer = str(payload.get("reviewer", "")).strip()

    if not anchor_id:
        raise ValueError("OA2_ANCHOR_OBJECT_REQUIRED")
    if object_type not in ALLOWED_TYPES:
        raise ValueError("OA2_EXPLICIT_OBJECT_TYPE_REQUIRED")
    if not family_label:
        raise ValueError("OA2_FAMILY_LABEL_REQUIRED")
    if not reviewer:
        raise ValueError("OA2_HUMAN_REVIEWER_REQUIRED")

    objects = scene.get("objects") or []
    anchor = next((o for o in objects if o.get("object_id") == anchor_id), None)
    if anchor is None:
        raise ValueError("OA2_ANCHOR_OBJECT_NOT_IN_SCENE")

    source = scene.get("source") or {}
    evidence = {
        "source_version_id": source.get("source_version_id"),
        "page_id": source.get("page_id"),
        "evidence_region_id": source.get("evidence_region_id"),
        "source_sha256": source.get("source_sha256"),
    }
    if not all(evidence.values()):
        raise ValueError("OA2_SOURCE_EVIDENCE_INCOMPLETE")

    family_id = f"{object_type}_{_slug(family_label)}"
    seed = json.dumps(
        {
            "anchor": anchor_id,
            "type": object_type,
            "family": family_id,
            "source": evidence,
            "revision": revision,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    prototype_id = "OAP-" + hashlib.sha256(seed).hexdigest()[:16].upper()

    return {
        "state": "HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE",
        "prototype_id": prototype_id,
        "object_type": object_type,
        "family_id": family_id,
        "family_label": family_label,
        "anchor_object_id": anchor_id,
        "source_evidence": evidence,
        "human_decision": {
            "decision": "THIS_IS_A",
            "reviewer": reviewer,
            "explicit_object_type": object_type,
            "family_label": family_label,
        },
        "revision": revision,
        "geometry_used_to_infer_type": False,
        "find_similar_authorized": False,
        "structural_identity_created": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "next_gate": "OA2_REVIEW_AND_RUNTIME_INTEGRATION",
    }


def demo() -> dict[str, Any]:
    scene = {
        "source": {
            "source_version_id": "SV-DEMO",
            "page_id": "PAGE-DEMO",
            "evidence_region_id": "ER-DEMO",
            "source_sha256": "a" * 64,
        },
        "objects": [{"object_id": "OBJ-1", "geometry": {"type": "LINE"}}],
    }
    return create_teaching_proposal(
        scene,
        {"anchor_object_id": "OBJ-1", "object_type": "COLUMN", "family_label": "40x40", "reviewer": "HUMAN-DEMO"},
        "REV-DEMO",
    )


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2, ensure_ascii=False))
