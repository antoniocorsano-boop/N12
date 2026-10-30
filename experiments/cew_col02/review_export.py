from __future__ import annotations

from copy import deepcopy
from typing import Any


_REQUIRED_SOURCE_FIELDS = {"source_version_id", "page_id", "page_transform_id", "sha256"}


def _require_bbox(raw: Any, *, name: str) -> dict[str, float]:
    if not isinstance(raw, dict):
        raise ValueError(f"{name} requires bbox")
    try:
        box = {
            "x": float(raw["x"]),
            "y": float(raw["y"]),
            "width": float(raw["width"]),
            "height": float(raw["height"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} bbox must contain numeric x/y/width/height") from exc
    if box["width"] <= 0 or box["height"] <= 0:
        raise ValueError(f"{name} bbox width/height must be positive")
    return box


def _authority() -> dict[str, bool]:
    return {
        "support_identity_authorized": False,
        "family_assignment_authorized": False,
        "section_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


def build_review_manifest_entry(
    *,
    panel_id: str,
    candidate: dict[str, Any],
    text_binding: dict[str, Any],
    source: dict[str, Any],
    source_only_crop: str,
    overlay_crop: str,
) -> dict[str, Any]:
    """Build one target-explicit Human Review manifest row.

    The graphical column decision and the text-binding decision are deliberately
    independent. A future reviewer may confirm either without implicitly
    confirming the other, and neither decision grants structural identity.
    """

    panel = str(panel_id).strip()
    candidate_id = str(candidate.get("occurrence_candidate_id") or candidate.get("candidate_id") or "").strip()
    if not panel or not candidate_id:
        raise ValueError("panel_id and candidate_id are required")
    footprint_bbox = _require_bbox(candidate.get("bbox"), name="candidate")

    if not isinstance(source, dict) or not _REQUIRED_SOURCE_FIELDS.issubset(source):
        raise ValueError("source provenance is incomplete")
    if not source_only_crop or not overlay_crop:
        raise ValueError("source-only and overlay crop paths are required")
    if not isinstance(text_binding, dict) or not isinstance(text_binding.get("bindings"), list):
        raise ValueError("text binding payload is incomplete")

    bindings: list[dict[str, Any]] = []
    for item in text_binding["bindings"]:
        if not isinstance(item, dict):
            raise ValueError("text binding item must be an object")
        token_id = str(item.get("token_id", "")).strip()
        if not token_id:
            raise ValueError("text binding item requires token_id")
        copied = deepcopy(item)
        copied["bbox"] = _require_bbox(item.get("bbox"), name=f"text token {token_id}")
        bindings.append(copied)

    return {
        "panel_id": panel,
        "candidate_id": candidate_id,
        "footprint_bbox": footprint_bbox,
        "footprint_detector": candidate.get("detector"),
        "footprint_similarity": candidate.get("score"),
        "axis_evidence_present": bool(candidate.get("axis_evidence_present", False)),
        "binding_state": text_binding.get("binding_state"),
        "internal_token_ids": list(text_binding.get("internal_token_ids", [])),
        "preferred_internal_token_id": text_binding.get("preferred_internal_token_id"),
        "text_bindings": bindings,
        "source": deepcopy(source),
        "source_only_crop": str(source_only_crop),
        "overlay_crop": str(overlay_crop),
        "column_graphic_decision": "PENDING_HUMAN_REVIEW",
        "text_binding_decision": "PENDING_HUMAN_REVIEW",
        "authority": _authority(),
    }
