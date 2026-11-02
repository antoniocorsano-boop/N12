from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable


ALLOWED_ANCHOR_CLASSES = {
    "STRUCTURAL_AXIS_INTERSECTION",
    "DIMENSION_CHAIN_ENDPOINT",
    "DOCUMENTED_REFERENCE_INTERSECTION",
    "SOURCE_NATIVE_METRIC_POINT",
}

FORBIDDEN_METRIC_SOURCE_KINDS = {
    "HISTORICAL_M0G",
    "HISTORICAL_AFFINE_REGISTRATION",
    "HISTORICAL_CEW_DERIVED_ANNOTATION",
}

FIT_ELIGIBLE_METRIC_SOURCE_POLICY = {
    "PRIMARY_TAV5_DOCUMENTED_RELATION": {"PRIMARY_VISUAL_VALIDATED"},
    "PRIMARY_TAV5_SOURCE_NATIVE_METRIC": {"SOURCE_NATIVE_VERIFIED"},
    "PRIMARY_MEASURED_CONTROL": {"MEASURED_CONTROL_VALIDATED"},
}

FIT_ELIGIBLE_METRIC_PROVENANCE = {"DOC", "MIS", "RIF"}

AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _canonical_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _anchor_identity_payload(
    *,
    anchor_class: str,
    source_version_sha256: str,
    source_page: int,
    source_point_px: list[float] | None,
    metric_xy_m: list[float] | None,
    metric_provenance: dict[str, str],
    evidence_refs: list[str],
    metric_source_kind: str,
    source_layer: str | None,
    metric_validation_state: str | None,
    metric_validation_ref: str | None,
) -> dict[str, Any]:
    return {
        "anchor_class": anchor_class,
        "source_version_sha256": source_version_sha256,
        "source_page": source_page,
        "source_point_px": source_point_px,
        "metric_xy_m": metric_xy_m,
        "metric_provenance": metric_provenance,
        "evidence_refs": evidence_refs,
        "metric_source_kind": metric_source_kind,
        "source_layer": source_layer,
        "metric_validation_state": metric_validation_state,
        "metric_validation_ref": metric_validation_ref,
    }


def make_anchor_candidate(
    *,
    anchor_class: str,
    source_version_sha256: str,
    source_page: int,
    source_point_px: list[float] | tuple[float, float] | None,
    metric_xy_m: list[float] | tuple[float, float] | None,
    metric_provenance: dict[str, str],
    evidence_refs: Iterable[str],
    metric_source_kind: str,
    source_layer: str | None = None,
    metric_validation_state: str | None = None,
    metric_validation_ref: str | None = None,
) -> dict[str, Any]:
    point = None if source_point_px is None else [float(source_point_px[0]), float(source_point_px[1])]
    metric = None if metric_xy_m is None else [float(metric_xy_m[0]), float(metric_xy_m[1])]
    refs = sorted(str(ref) for ref in evidence_refs)
    provenance = {"x": metric_provenance.get("x"), "y": metric_provenance.get("y")}
    validation_state = None if metric_validation_state is None else str(metric_validation_state).strip() or None
    validation_ref = None if metric_validation_ref is None else str(metric_validation_ref).strip() or None

    reasons: list[str] = []
    if anchor_class not in ALLOWED_ANCHOR_CLASSES:
        reasons.append("ANCHOR_CLASS_NOT_ALLOWED")
    if not source_version_sha256:
        reasons.append("SOURCE_VERSION_MISSING")
    if point is None:
        reasons.append("SOURCE_POINT_MISSING")
    if source_layer and source_layer.startswith("S-"):
        reasons.append("HISTORICAL_CEW_LAYER_NOT_PRIMARY")
    if metric_source_kind in FORBIDDEN_METRIC_SOURCE_KINDS:
        reasons.append("FORBIDDEN_METRIC_SOURCE")
    if metric_source_kind == "OCR_TEXT_ONLY":
        reasons.append("OCR_TEXT_WITHOUT_GEOMETRIC_BINDING")

    eligible_validation_states = FIT_ELIGIBLE_METRIC_SOURCE_POLICY.get(metric_source_kind)
    if eligible_validation_states is None:
        reasons.append("METRIC_SOURCE_KIND_NOT_FIT_ELIGIBLE")
    elif validation_state not in eligible_validation_states:
        reasons.append("METRIC_VALIDATION_STATE_NOT_ELIGIBLE")
    if not validation_ref:
        reasons.append("METRIC_VALIDATION_REFERENCE_MISSING")

    if metric is None:
        reasons.append("METRIC_COORDINATE_MISSING")
    if provenance["x"] not in FIT_ELIGIBLE_METRIC_PROVENANCE or provenance["y"] not in FIT_ELIGIBLE_METRIC_PROVENANCE:
        reasons.append("METRIC_PROVENANCE_NOT_FIT_ELIGIBLE")
    if not refs:
        reasons.append("EVIDENCE_REFERENCE_MISSING")

    identity = _anchor_identity_payload(
        anchor_class=anchor_class,
        source_version_sha256=source_version_sha256,
        source_page=int(source_page),
        source_point_px=point,
        metric_xy_m=metric,
        metric_provenance=provenance,
        evidence_refs=refs,
        metric_source_kind=metric_source_kind,
        source_layer=source_layer,
        metric_validation_state=validation_state,
        metric_validation_ref=validation_ref,
    )
    anchor_id = "CEW-CAL01-ANCHOR-" + hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:20]

    return {
        "anchor_id": anchor_id,
        **identity,
        "eligible_for_fit": not reasons,
        "rejection_reasons": reasons,
        "authority": dict(AUTHORITY_CLOSED),
    }


def build_primary_anchor_inventory(
    candidates: Iterable[dict[str, Any]],
    source_version_sha256: str,
) -> dict[str, Any]:
    anchors = sorted((dict(candidate) for candidate in candidates), key=lambda row: row["anchor_id"])
    for row in anchors:
        if row.get("source_version_sha256") != source_version_sha256:
            raise ValueError("anchor source_version_sha256 does not match inventory source")

    digest_payload = {
        "program": "CEW-CAL-01",
        "source_version_sha256": source_version_sha256,
        "anchors": anchors,
    }
    return {
        "program": "CEW-CAL-01",
        "artifact": "CEW_CAL01_PRIMARY_ANCHOR_INVENTORY_v1",
        "source_version_sha256": source_version_sha256,
        "anchor_count": len(anchors),
        "eligible_anchor_count": sum(1 for row in anchors if row["eligible_for_fit"]),
        "anchors": anchors,
        "inventory_digest": _canonical_digest(digest_payload),
        "authority": dict(AUTHORITY_CLOSED),
    }
