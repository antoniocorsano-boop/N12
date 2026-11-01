from __future__ import annotations

from copy import deepcopy
from typing import Any


ALLOWED_KNOWLEDGE_PROVENANCE = {
    "PROJECT_LEARNED",
    "VERIFIED_REFERENCE",
    "METHOD_RULE",
    "HUMAN_TAUGHT_PROJECT_RULE",
}

GRAMMAR_INVARIANTS = {
    "RECTANGLE_DOES_NOT_IMPLY_COLUMN",
    "DIMENSION_REQUIRES_RELATION",
    "REBAR_CALLOUT_REQUIRES_TARGET_BINDING",
    "SECTION_SIZE_REQUIRES_CONTEXTUAL_BINDING",
    "TOPOLOGY_OUTRANKS_VISUAL_PROXIMITY_FOR_IDENTITY",
    "PROTOTYPE_DOES_NOT_IMPLY_TRUTH",
    "CROSS_VIEW_CONFLICT_FAILS_CLOSED",
    "OCR_CONFIDENCE_IS_NOT_ENGINEERING_CONFIDENCE",
    "SOURCE_REMAINS_EVIDENTIARY_AUTHORITY",
}

_REQUIRED_SOURCE_KEYS = {
    "source_version_id",
    "sha256",
    "evidence_region_id",
    "stable_id",
    "evidentiary_class",
}


def _closed_authority() -> dict[str, Any]:
    return {
        "grammar_output": "STRUCTURAL_HYPOTHESIS_CANDIDATE",
        "human_review_required": True,
        "primary_source_identity_bridge": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "family_assignment_authorized": False,
        "section_assignment_authorized": False,
        "m0g_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def _validate_source(source: Any) -> dict[str, Any]:
    if not isinstance(source, dict) or not _REQUIRED_SOURCE_KEYS.issubset(source):
        raise ValueError("SOURCE_BINDING_REQUIRED")
    digest = str(source.get("sha256") or "")
    if len(digest) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in digest):
        raise ValueError("SOURCE_BINDING_REQUIRED")
    if not all(str(source.get(key) or "").strip() for key in _REQUIRED_SOURCE_KEYS - {"sha256"}):
        raise ValueError("SOURCE_BINDING_REQUIRED")
    return deepcopy(source)


def _validate_provenance(value: Any) -> str:
    provenance = str(value or "")
    if provenance not in ALLOWED_KNOWLEDGE_PROVENANCE:
        raise ValueError("KNOWLEDGE_PROVENANCE_INVALID")
    return provenance


def interpret_observation(observation: dict[str, Any]) -> dict[str, Any]:
    """Translate a governed observation into a non-promoting technical relation.

    The adapter deliberately remains small. It carries forward the qualified N12
    engineering-drawing invariants and emits only review candidates. It never
    converts OCR, geometric similarity or historical DXF into structural truth.
    """

    if not isinstance(observation, dict):
        raise ValueError("OBSERVATION_OBJECT_REQUIRED")

    source = _validate_source(observation.get("source"))
    provenance = _validate_provenance(observation.get("knowledge_provenance"))
    payload = deepcopy(observation)
    payload.pop("source", None)
    payload.pop("knowledge_provenance", None)

    relation: dict[str, Any]
    hypothesis: dict[str, Any]

    if observation.get("cross_source_conflict") is True:
        relation = {
            "state": "CROSS_SOURCE_CONFLICT",
            "preferred_target_id": None,
        }
        hypothesis = {
            "state": "CROSS_SOURCE_CONFLICT_REVIEW_REQUIRED",
            "candidate_target_id": None,
        }
    elif observation.get("primitive") == "RECTANGULAR_ENVELOPE":
        relation = {
            "state": "UNBOUND_GRAPHIC_PRIMITIVE",
            "preferred_target_id": None,
        }
        hypothesis = {
            "state": "AMBIGUOUS_TECHNICAL_OBJECT_CANDIDATE",
            "structural_type": None,
        }
    elif observation.get("relation_type") == "IDENTITY_CANDIDATE":
        topology_target = observation.get("topology_target_id")
        visual_target = observation.get("visual_target_id")
        preferred_target = topology_target or visual_target
        relation = {
            "state": (
                "TOPOLOGY_PREFERRED_IDENTITY_RELATION"
                if topology_target is not None
                else "VISUAL_IDENTITY_RELATION_NEEDS_REVIEW"
            ),
            "preferred_target_id": preferred_target,
            "visual_target_id": visual_target,
            "topology_target_id": topology_target,
        }
        hypothesis = {
            "state": (
                "IDENTITY_HYPOTHESIS_TOPOLOGY_PREFERRED_REVIEW"
                if topology_target is not None
                else "IDENTITY_HYPOTHESIS_REVIEW_REQUIRED"
            ),
            "candidate_target_id": preferred_target,
        }
    else:
        token_type = observation.get("token_type")
        target_relation = observation.get("target_relation")
        if token_type == "DIMENSION" and target_relation is None:
            relation = {
                "state": "DIMENSION_NEEDS_TARGET_RELATION",
                "preferred_target_id": None,
            }
            hypothesis = {"state": "TECHNICAL_TOKEN_NEEDS_CONTEXT"}
        elif token_type is not None and target_relation is None:
            relation = {
                "state": "TECHNICAL_TOKEN_NEEDS_TARGET_RELATION",
                "preferred_target_id": None,
            }
            hypothesis = {"state": "TECHNICAL_TOKEN_NEEDS_CONTEXT"}
        elif token_type is not None and target_relation is not None:
            relation = {
                "state": "TECHNICAL_TOKEN_TARGET_RELATION_CANDIDATE",
                "target_relation": target_relation,
                "preferred_target_id": None,
            }
            hypothesis = {"state": "STRUCTURAL_HYPOTHESIS_CANDIDATE"}
        else:
            relation = {
                "state": "UNHANDLED_OBSERVATION_REVIEW_REQUIRED",
                "preferred_target_id": None,
            }
            hypothesis = {"state": "STRUCTURAL_HYPOTHESIS_REVIEW_REQUIRED"}

    return {
        "schema": "CEW_SPIRAL_GRAMMAR_ADAPTER_v1",
        "source": source,
        "observation": payload,
        "knowledge_provenance": provenance,
        "relation": relation,
        "hypothesis": hypothesis,
        "invariants_applied": sorted(GRAMMAR_INVARIANTS),
        "authority": _closed_authority(),
    }
