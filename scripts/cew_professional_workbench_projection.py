#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import build_cew_erw_synced_workspace as f6_erw
import build_cew_source_viewer as f3_source_viewer
import cew_professional_workbench_core as core
import cew_professional_workbench_document_geometry as document_geometry

ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = ROOT / "data/canonical/CEW_OBSERVATION_REGISTRY_v1.csv"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _observations_for_region(region_id: str) -> list[dict[str, str]]:
    return [row for row in rows(OBSERVATIONS) if row.get("evidence_region_id", "").strip() == region_id]


def _single_structural_binding(observations: list[dict[str, str]]) -> str | None:
    bindings = {
        row.get("structural_binding", "").strip()
        for row in observations
        if row.get("structural_binding", "").strip()
    }
    if len(bindings) > 1:
        raise ValueError("MULTIPLE_STRUCTURAL_BINDINGS_FOR_EVIDENCE_REGION")
    return next(iter(bindings), None)


def _f3_entry(task_id: str) -> dict[str, Any]:
    manifest = f3_source_viewer.build_manifest()
    entries = [entry for entry in manifest["entries"] if entry["task_id"] == task_id]
    if len(entries) != 1:
        raise ValueError(f"F3_VIEWER_ENTRY_NOT_UNIQUE:{task_id}")
    return entries[0]


def _structural_projection(
    *,
    context: dict[str, Any],
    task_id: str,
    source_version_id: str,
    evidence_region_id: str,
    binding_state: str,
    link_type: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    object_id = core.stable_id(
        "GSO",
        context["member_id"],
        context["node_i"]["node_id"],
        context["node_j"]["node_id"],
        context["frozen_geometric_length_m"],
    )
    obj = {
        "object_id": object_id,
        "object_family": "GovernedStructuralObjectProjection",
        "coordinate_space": "STRUCTURAL_MODEL_XY",
        "authority_state": "DERIVED_STRUCTURAL_PROJECTION_ONLY",
        "governed_object_id": context["member_id"],
        "governed_source_member_id": context["source_member_id"],
        "binding_state": binding_state,
        "selection_authorized": binding_state == "BOUND",
        "geometry": {
            "type": "LINE",
            "a": [context["node_i"]["x_m"], context["node_i"]["y_m"]],
            "b": [context["node_j"]["x_m"], context["node_j"]["y_m"]],
            "z_a_m": context["node_i"]["z_m"],
            "z_b_m": context["node_j"]["z_m"],
        },
        "properties": {
            "source_member_id": context["source_member_id"],
            "support_i": context["support_i"],
            "support_j": context["support_j"],
            "frozen_geometric_length_m": context["frozen_geometric_length_m"],
            "section_cm": context["section_cm"],
            "coordinate_evidence_i": context["node_i"]["coordinate_evidence_state"],
            "coordinate_evidence_j": context["node_j"]["coordinate_evidence_state"],
        },
        "provenance": {
            "governed_object_id": context["member_id"],
            "source_member_id": context["source_member_id"],
            "source_version_id": source_version_id,
            "evidence_region_id": evidence_region_id,
            "task_id": task_id,
            "projection_origin": "F6_ERW_M0G_FROZEN_LEDGER_ADAPTER",
        },
        "canonical_write_authorized": False,
    }
    link = {
        "evidence_link_id": core.stable_id(
            "EL",
            task_id,
            evidence_region_id,
            object_id,
            link_type,
        ),
        "link_type": link_type,
        "evidence_region_id": evidence_region_id,
        "source_version_id": source_version_id,
        "target_object_id": object_id,
        "created_by": "EXPLICIT_CEW_F6_RELATION",
        "binding_state": binding_state,
        "canonical_write_authorized": False,
    }
    return obj, link


def _document_geometry_projection(
    *,
    source_version_id: str,
    source_sha256: str,
    page_index: int,
    evidence_region_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    state = document_geometry.status()
    if state["state"] != "READY":
        return [], {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": state.get("reason", "DOCUMENT_GEOMETRY_UNAVAILABLE"),
            "agreement_outcome": None,
            "canonical_write_authorized": False,
        }
    pdf_page_no = page_index + 1
    try:
        result = document_geometry.scene_objects(
            source_version_id=source_version_id,
            source_sha256=source_sha256,
            page=pdf_page_no,
            evidence_region_id=evidence_region_id,
        )
    except ValueError as exc:
        return [], {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": str(exc),
            "agreement_outcome": None,
            "canonical_write_authorized": False,
        }
    return list(result.get("objects") or []), {
        "state": result["state"],
        "agreement_outcome": result.get("agreement_outcome"),
        "evidence_region_id": evidence_region_id,
        "pdf_page_no": pdf_page_no,
        "object_count": len(result.get("objects") or []),
        "effective_match_ratio": result.get("effective_match_ratio"),
        "artifact_content_sha256": result.get("artifact_content_sha256"),
        "canonical_write_authorized": False,
    }


def build_scene(task_id: str, source_workspace=None) -> dict[str, Any]:
    if source_workspace is None:
        import cew_source_evidence_workspace as source_workspace

    ctx = source_workspace.task_context(task_id)
    task = ctx["task"]
    binding = ctx["binding"]
    region = ctx["region"]
    page = ctx["page"]
    source = ctx["source"]
    f3 = _f3_entry(task_id)

    source_version_id = binding["source_version_id"].strip()
    source_sha256 = source["sha256"].strip()
    page_id = page["page_id"].strip()
    page_index = int(page["page_index"])
    evidence_region_id = region["evidence_region_id"].strip()
    source_revision = core.stable_id(
        "SRCREV",
        source_version_id,
        source_sha256,
        page_id,
        ctx["transform"]["transform_id"].strip(),
    )

    document_objects, document_geometry_state = _document_geometry_projection(
        source_version_id=source_version_id,
        source_sha256=source_sha256,
        page_index=page_index,
        evidence_region_id=evidence_region_id,
    )
    objects: list[dict[str, Any]] = list(document_objects)
    evidence_links: list[dict[str, Any]] = []
    observations = _observations_for_region(evidence_region_id)
    structural_binding = _single_structural_binding(observations)
    member_rows = f6_erw.rows(f6_erw.MEMBERS)
    node_rows = f6_erw.rows(f6_erw.NODES)

    structural_state = "NO_STRUCTURAL_OBJECT_FOR_TASK"
    if structural_binding:
        context = f6_erw.member_context(member_rows, node_rows, structural_binding)
        obj, link = _structural_projection(
            context=context,
            task_id=task_id,
            source_version_id=source_version_id,
            evidence_region_id=evidence_region_id,
            binding_state="BOUND",
            link_type="GOVERNED_BINDING",
        )
        objects.append(obj)
        evidence_links.append(link)
        structural_state = "GOVERNED_BINDING_PROJECTED_READ_ONLY"
    elif task_id == "ERW-N12-004":
        context = f6_erw.member_context(member_rows, node_rows, "G5-B017")
        obj, link = _structural_projection(
            context=context,
            task_id=task_id,
            source_version_id=source_version_id,
            evidence_region_id=evidence_region_id,
            binding_state="UNBOUND",
            link_type="CANDIDATE_CORRESPONDENCE",
        )
        objects.append(obj)
        evidence_links.append(link)
        structural_state = "UNBOUND_CANDIDATE_COMPARISON_CONTEXT_ONLY"

    scene: dict[str, Any] = {
        "schema_version": "1.0",
        "scene_id": core.stable_id("SCENE", task_id, source_version_id, page_id, evidence_region_id),
        "scene_revision": "PENDING_DIGEST",
        "task_id": task_id,
        "source": {
            "source_id": task["source_id"].strip(),
            "source_version_id": source_version_id,
            "source_sha256": source_sha256,
            "source_revision": source_revision,
            "page_id": page_id,
            "page_index": page_index,
            "pdf_page_no": page_index + 1,
            "page_width_pt": float(page["source_width"]),
            "page_height_pt": float(page["source_height"]),
            "evidence_region_id": evidence_region_id,
            "evidence_bbox_normalized": {
                "x": float(region["x"]),
                "y": float(region["y"]),
                "width": float(region["width"]),
                "height": float(region["height"]),
            },
            "page_transform_id": ctx["transform"]["transform_id"].strip(),
            "f3_dzi_reference": f3["dzi"],
            "f3_initial_view_policy": f3["initial_view_policy"],
            "authority": "VERIFIED_IMMUTABLE_PRIMARY_SOURCE",
        },
        "objects": objects,
        "evidence_links": evidence_links,
        "registrations": [
            {
                "registration_id": core.stable_id("REG", task_id, source_revision, "SOURCE_TO_TECHNICAL"),
                "from_space": "SOURCE_PAGE_PT",
                "to_space": "TECHNICAL_2D",
                "transform_type": None,
                "state": "UNAVAILABLE",
                "reason": "NO_VERIFIED_SOURCE_TO_TECHNICAL_REGISTRATION_IN_CURRENT_CEW_RECORDS",
                "control_correspondences": [],
                "matrix": None,
                "residual_metrics": {},
                "canonical_write_authorized": False,
            }
        ],
        "capabilities": {
            "source_viewer": "F3_DZI_MANIFEST_REUSED",
            "source_multiresolution_assets": "AVAILABLE_NOT_YET_WIRED_TO_MANAGED_RUNTIME",
            "dual_vector_agreement": document_geometry_state["state"],
            "document_geometry": document_geometry_state,
            "document_linework_object_count": len(document_objects),
            "structural_projection": structural_state,
            "technical_scene_available": bool(objects),
            "semantic_sync_available": bool(evidence_links),
            "spatial_sync_available": False,
            "overlay_available": False,
            "working_edit_model": "KERNEL_AVAILABLE",
            "reading_issue_model": "KERNEL_AVAILABLE",
        },
        "authority": {
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
            "promotion_authorized": False,
            "source_authority_preserved": True,
        },
    }
    scene["scene_revision"] = core.scene_digest(scene)
    core.validate_scene(scene)
    return scene
