#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "automation/CEW_PROFESSIONAL_WORKBENCH_SCENE_CONTRACT_v1.json"


def _contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_matrix3(matrix: Any) -> None:
    require(isinstance(matrix, list) and len(matrix) == 3, "REGISTRATION_MATRIX_3X3_REQUIRED")
    for row in matrix:
        require(isinstance(row, list) and len(row) == 3, "REGISTRATION_MATRIX_3X3_REQUIRED")
        require(all(_is_number(value) for value in row), "REGISTRATION_MATRIX_FINITE_NUMBERS_REQUIRED")


def validate_scene_object(obj: dict[str, Any]) -> None:
    c = _contract()
    require(isinstance(obj, dict), "SCENE_OBJECT_REQUIRED")
    require(bool(obj.get("object_id")), "SCENE_OBJECT_ID_REQUIRED")
    require(obj.get("object_family") in c["scene_object_families"], "SCENE_OBJECT_FAMILY_UNSUPPORTED")
    require(obj.get("coordinate_space") in c["coordinate_spaces"], "SCENE_OBJECT_COORDINATE_SPACE_UNSUPPORTED")
    require(obj.get("coordinate_space") != "VIEWPORT_PX", "VIEWPORT_COORDINATES_CANNOT_BE_SCENE_GEOMETRY")
    provenance = obj.get("provenance")
    require(isinstance(provenance, dict), "SCENE_OBJECT_PROVENANCE_REQUIRED")
    require(bool(provenance.get("source_version_id") or provenance.get("governed_object_id")), "SCENE_OBJECT_PROVENANCE_ID_REQUIRED")
    if obj["object_family"] == "GovernedStructuralObjectProjection":
        require(bool(obj.get("governed_object_id")), "GOVERNED_OBJECT_ID_REQUIRED")
        require(obj.get("authority_state") == "DERIVED_STRUCTURAL_PROJECTION_ONLY", "STRUCTURAL_PROJECTION_AUTHORITY_INVALID")
        require(obj.get("canonical_write_authorized") is False, "STRUCTURAL_PROJECTION_CANONICAL_WRITE_FORBIDDEN")


def validate_evidence_link(link: dict[str, Any], object_ids: set[str]) -> None:
    c = _contract()
    require(bool(link.get("evidence_link_id")), "EVIDENCE_LINK_ID_REQUIRED")
    require(link.get("link_type") in c["evidence_link_types"], "EVIDENCE_LINK_TYPE_UNSUPPORTED")
    require(link.get("target_object_id") in object_ids, "EVIDENCE_LINK_TARGET_UNKNOWN")
    require(bool(link.get("evidence_region_id") or link.get("source_version_id")), "EVIDENCE_LINK_SOURCE_EVIDENCE_REQUIRED")
    require(link.get("created_by") != "VISUAL_PROXIMITY", "VISUAL_PROXIMITY_LINK_FORBIDDEN")
    require(link.get("canonical_write_authorized") is False, "EVIDENCE_LINK_CANONICAL_WRITE_FORBIDDEN")


def validate_registration(
    registration: dict[str, Any],
    *,
    source_revision: str,
    scene_revision: str,
) -> None:
    c = _contract()
    require(bool(registration.get("registration_id")), "REGISTRATION_ID_REQUIRED")
    require(registration.get("state") in c["registration_states"], "REGISTRATION_STATE_UNSUPPORTED")
    require(registration.get("from_space") in c["coordinate_spaces"], "REGISTRATION_FROM_SPACE_UNSUPPORTED")
    require(registration.get("to_space") in c["coordinate_spaces"], "REGISTRATION_TO_SPACE_UNSUPPORTED")
    require(registration.get("from_space") != "VIEWPORT_PX" and registration.get("to_space") != "VIEWPORT_PX", "VIEWPORT_SPACE_REGISTRATION_FORBIDDEN")
    require(registration.get("canonical_write_authorized") is False, "REGISTRATION_CANONICAL_WRITE_FORBIDDEN")

    if registration["state"] != "VERIFIED":
        return

    require(registration.get("transform_type") in c["registration_types"], "VERIFIED_REGISTRATION_TYPE_REQUIRED")
    require(registration.get("source_revision") == source_revision, "VERIFIED_REGISTRATION_SOURCE_REVISION_MISMATCH")
    require(registration.get("scene_revision") == scene_revision, "VERIFIED_REGISTRATION_SCENE_REVISION_MISMATCH")
    require(bool(registration.get("verification_process")), "VERIFIED_REGISTRATION_PROCESS_REQUIRED")
    require(bool(registration.get("verification_actor_or_gate")), "VERIFIED_REGISTRATION_ACTOR_REQUIRED")
    require(isinstance(registration.get("residual_metrics"), dict), "VERIFIED_REGISTRATION_RESIDUAL_METRICS_REQUIRED")

    transform_type = registration["transform_type"]
    controls = registration.get("control_correspondences", [])
    require(isinstance(controls, list), "REGISTRATION_CONTROL_CORRESPONDENCES_REQUIRED")
    if transform_type == "IDENTITY_PAGE":
        require(registration["from_space"] == registration["to_space"], "IDENTITY_REGISTRATION_REQUIRES_SAME_SPACE")
    elif transform_type == "AFFINE_2D":
        require(len(controls) >= 3, "AFFINE_REGISTRATION_REQUIRES_AT_LEAST_3_CONTROLS")
        validate_matrix3(registration.get("matrix"))
    elif transform_type == "HOMOGRAPHY_2D":
        require(len(controls) >= 4, "HOMOGRAPHY_REGISTRATION_REQUIRES_AT_LEAST_4_CONTROLS")
        validate_matrix3(registration.get("matrix"))


def registration_allows_spatial(
    registration: dict[str, Any] | None,
    *,
    source_revision: str,
    scene_revision: str,
) -> bool:
    if not registration or registration.get("state") != "VERIFIED":
        return False
    try:
        validate_registration(registration, source_revision=source_revision, scene_revision=scene_revision)
    except ValueError:
        return False
    return True


def validate_scene(scene: dict[str, Any]) -> dict[str, Any]:
    c = _contract()
    for field in c["required_scene_envelope_fields"]:
        require(field in scene, f"SCENE_FIELD_REQUIRED:{field}")
    require(scene.get("schema_version") == c["scene_schema_version"], "SCENE_SCHEMA_UNSUPPORTED")
    require(bool(scene.get("scene_id")) and bool(scene.get("scene_revision")), "SCENE_IDENTITY_REQUIRED")
    require(bool(scene.get("task_id")), "SCENE_TASK_REQUIRED")

    authority = scene.get("authority")
    require(isinstance(authority, dict), "SCENE_AUTHORITY_REQUIRED")
    for key, expected in c["required_authority_flags"].items():
        require(authority.get(key) == expected, f"SCENE_AUTHORITY_DRIFT:{key}")

    source = scene.get("source")
    require(isinstance(source, dict), "SCENE_SOURCE_REQUIRED")
    require(bool(source.get("source_version_id")), "SCENE_SOURCE_VERSION_REQUIRED")
    require(bool(source.get("source_sha256")), "SCENE_SOURCE_SHA_REQUIRED")
    require(bool(source.get("page_id")), "SCENE_PAGE_REQUIRED")
    require(bool(source.get("source_revision")), "SCENE_SOURCE_REVISION_REQUIRED")

    objects = scene.get("objects")
    require(isinstance(objects, list), "SCENE_OBJECT_LIST_REQUIRED")
    object_ids: set[str] = set()
    for obj in objects:
        validate_scene_object(obj)
        require(obj["object_id"] not in object_ids, "SCENE_OBJECT_ID_DUPLICATE")
        object_ids.add(obj["object_id"])

    links = scene.get("evidence_links")
    require(isinstance(links, list), "SCENE_EVIDENCE_LINK_LIST_REQUIRED")
    link_ids: set[str] = set()
    for link in links:
        validate_evidence_link(link, object_ids)
        require(link["evidence_link_id"] not in link_ids, "EVIDENCE_LINK_ID_DUPLICATE")
        link_ids.add(link["evidence_link_id"])

    registrations = scene.get("registrations")
    require(isinstance(registrations, list), "SCENE_REGISTRATION_LIST_REQUIRED")
    reg_ids: set[str] = set()
    for registration in registrations:
        validate_registration(
            registration,
            source_revision=source["source_revision"],
            scene_revision=scene["scene_revision"],
        )
        require(registration["registration_id"] not in reg_ids, "REGISTRATION_ID_DUPLICATE")
        reg_ids.add(registration["registration_id"])

    return scene


def resolve_view_state(
    scene: dict[str, Any],
    *,
    requested_mode: str,
    requested_sync_mode: str,
    registration_id: str | None = None,
) -> dict[str, Any]:
    validate_scene(scene)
    c = _contract()
    require(requested_mode in c["display_modes"], "DISPLAY_MODE_UNSUPPORTED")
    require(requested_sync_mode in c["sync_modes"], "SYNC_MODE_UNSUPPORTED")

    registrations = {r["registration_id"]: r for r in scene["registrations"]}
    registration = registrations.get(registration_id) if registration_id else None
    source_revision = scene["source"]["source_revision"]
    scene_revision = scene["scene_revision"]
    spatial_ok = registration_allows_spatial(
        registration,
        source_revision=source_revision,
        scene_revision=scene_revision,
    )

    effective_mode = requested_mode
    effective_sync = requested_sync_mode
    blockers: list[str] = []

    if requested_mode == "OVERLAY" and not spatial_ok:
        effective_mode = "SPLIT" if scene["capabilities"].get("technical_scene_available") else "SOURCE"
        blockers.append("OVERLAY_REQUIRES_VERIFIED_REVISION_MATCHED_REGISTRATION")

    if requested_sync_mode == "SPATIAL_LOCKED" and not spatial_ok:
        effective_sync = "SEMANTIC" if scene["evidence_links"] else "OFF"
        blockers.append("SPATIAL_LOCK_REQUIRES_VERIFIED_REVISION_MATCHED_REGISTRATION")

    if effective_mode in {"TECHNICAL", "SPLIT"} and not scene["capabilities"].get("technical_scene_available"):
        effective_mode = "SOURCE"
        blockers.append("TECHNICAL_SCENE_UNAVAILABLE")

    return {
        "requested_mode": requested_mode,
        "requested_sync_mode": requested_sync_mode,
        "registration_id": registration_id,
        "effective_mode": effective_mode,
        "effective_sync_mode": effective_sync,
        "spatial_registration_usable": spatial_ok,
        "blocked_actions": blockers,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def validate_working_edit(scene: dict[str, Any], edit: dict[str, Any]) -> None:
    c = _contract()
    validate_scene(scene)
    require(edit.get("schema_version") == c["working_edit_schema_version"], "WORKING_EDIT_SCHEMA_UNSUPPORTED")
    require(edit.get("scene_revision") == scene["scene_revision"], "WORKING_EDIT_SCENE_REVISION_MISMATCH")
    require(edit.get("source_revision") == scene["source"]["source_revision"], "WORKING_EDIT_SOURCE_REVISION_MISMATCH")
    require(edit.get("state") in c["working_edit_states"], "WORKING_EDIT_STATE_UNSUPPORTED")
    require(edit.get("canonical_write") is False, "WORKING_EDIT_CANONICAL_WRITE_FORBIDDEN")
    require(edit.get("promotion_authorized") is False, "WORKING_EDIT_PROMOTION_FORBIDDEN")

    objects = {obj["object_id"]: obj for obj in scene["objects"]}
    target_id = edit.get("target_object_id")
    require(target_id in objects, "WORKING_EDIT_TARGET_UNKNOWN")
    target = objects[target_id]
    require(target["object_family"] in c["editable_object_families"], "WORKING_EDIT_TARGET_READ_ONLY")
    prop = edit.get("target_property")
    require(prop in target.get("properties", {}), "WORKING_EDIT_PROPERTY_UNKNOWN")
    require(edit.get("base_value") == target["properties"][prop], "WORKING_EDIT_BASE_VALUE_DRIFT")


def create_working_edit(
    scene: dict[str, Any],
    *,
    target_object_id: str,
    property_name: str,
    proposed_value: Any,
    author_session: str,
    state: str = "DRAFT",
) -> dict[str, Any]:
    validate_scene(scene)
    c = _contract()
    require(state in c["working_edit_states"], "WORKING_EDIT_STATE_UNSUPPORTED")
    require(bool(property_name), "WORKING_EDIT_PROPERTY_REQUIRED")
    require(bool(author_session), "WORKING_EDIT_AUTHOR_SESSION_REQUIRED")

    objects = {obj["object_id"]: obj for obj in scene["objects"]}
    require(target_object_id in objects, "WORKING_EDIT_TARGET_UNKNOWN")
    target = objects[target_object_id]
    require(target["object_family"] in c["editable_object_families"], "WORKING_EDIT_TARGET_READ_ONLY")

    properties = target.get("properties", {})
    require(property_name in properties, "WORKING_EDIT_PROPERTY_UNKNOWN")
    base_value = deepcopy(properties[property_name])

    edit = {
        "schema_version": c["working_edit_schema_version"],
        "working_edit_id": stable_id(
            "WE",
            scene["scene_revision"],
            target_object_id,
            property_name,
            canonical_json(base_value),
            canonical_json(proposed_value),
            author_session,
        ),
        "scene_revision": scene["scene_revision"],
        "source_revision": scene["source"]["source_revision"],
        "target_object_id": target_object_id,
        "target_property": property_name,
        "base_value": base_value,
        "proposed_value": deepcopy(proposed_value),
        "author_session": author_session,
        "state": state,
        "canonical_write": False,
        "promotion_authorized": False,
    }
    validate_working_edit(scene, edit)
    return edit


def validate_reading_issue(scene: dict[str, Any], issue: dict[str, Any]) -> None:
    c = _contract()
    validate_scene(scene)
    require(issue.get("schema_version") == c["reading_issue_schema_version"], "READING_ISSUE_SCHEMA_UNSUPPORTED")
    require(issue.get("scene_revision") == scene["scene_revision"], "READING_ISSUE_SCENE_REVISION_MISMATCH")
    require(issue.get("source_revision") == scene["source"]["source_revision"], "READING_ISSUE_SOURCE_REVISION_MISMATCH")
    require(issue.get("state") in c["reading_issue_states"], "READING_ISSUE_STATE_UNSUPPORTED")
    require(bool(str(issue.get("question", "")).strip()), "READING_ISSUE_QUESTION_REQUIRED")
    require(issue.get("canonical_write") is False, "READING_ISSUE_CANONICAL_WRITE_FORBIDDEN")
    require(issue.get("promotion_authorized") is False, "READING_ISSUE_PROMOTION_FORBIDDEN")

    object_ids = {obj["object_id"] for obj in scene["objects"]}
    link_ids = {link["evidence_link_id"] for link in scene["evidence_links"]}
    anchor_object_id = issue.get("anchor_object_id")
    anchor_geometry = issue.get("anchor_geometry")
    evidence_link_ids = list(issue.get("evidence_link_ids") or [])
    if anchor_object_id is not None:
        require(anchor_object_id in object_ids, "READING_ISSUE_ANCHOR_OBJECT_UNKNOWN")
    require(anchor_object_id is not None or anchor_geometry is not None or evidence_link_ids, "READING_ISSUE_GRAPHICAL_OR_EVIDENCE_ANCHOR_REQUIRED")
    require(all(link_id in link_ids for link_id in evidence_link_ids), "READING_ISSUE_EVIDENCE_LINK_UNKNOWN")
    if anchor_geometry is not None:
        require(anchor_geometry.get("coordinate_space") in c["coordinate_spaces"], "READING_ISSUE_COORDINATE_SPACE_UNSUPPORTED")
        require(anchor_geometry.get("coordinate_space") != "VIEWPORT_PX", "READING_ISSUE_VIEWPORT_ANCHOR_FORBIDDEN")


def create_reading_issue(
    scene: dict[str, Any],
    *,
    question: str,
    state: str = "OPEN",
    anchor_object_id: str | None = None,
    anchor_geometry: dict[str, Any] | None = None,
    evidence_link_ids: list[str] | None = None,
) -> dict[str, Any]:
    validate_scene(scene)
    c = _contract()
    evidence_link_ids = list(evidence_link_ids or [])
    issue = {
        "schema_version": c["reading_issue_schema_version"],
        "reading_issue_id": stable_id(
            "RI",
            scene["scene_revision"],
            question,
            anchor_object_id or "",
            canonical_json(anchor_geometry or {}),
            canonical_json(sorted(evidence_link_ids)),
        ),
        "scene_revision": scene["scene_revision"],
        "source_revision": scene["source"]["source_revision"],
        "question": question.strip(),
        "state": state,
        "anchor_object_id": anchor_object_id,
        "anchor_geometry": deepcopy(anchor_geometry),
        "evidence_link_ids": evidence_link_ids,
        "canonical_write": False,
        "promotion_authorized": False,
    }
    validate_reading_issue(scene, issue)
    return issue


def _validate_viewport_state(viewport: dict[str, Any], label: str) -> None:
    require(isinstance(viewport, dict), f"{label}_VIEWPORT_REQUIRED")
    centre = viewport.get("centre")
    require(isinstance(centre, list) and len(centre) == 2 and all(_is_number(v) for v in centre), f"{label}_VIEWPORT_CENTRE_REQUIRED")
    require(_is_number(viewport.get("zoom")) and float(viewport["zoom"]) > 0, f"{label}_VIEWPORT_ZOOM_INVALID")
    require(_is_number(viewport.get("rotation_deg")), f"{label}_VIEWPORT_ROTATION_INVALID")


def validate_view_snapshot(scene: dict[str, Any], view: dict[str, Any]) -> None:
    c = _contract()
    validate_scene(scene)
    for field in c["required_view_snapshot_fields"]:
        require(field in view, f"VIEW_FIELD_REQUIRED:{field}")
    require(view.get("schema_version") == c["view_schema_version"], "VIEW_SCHEMA_UNSUPPORTED")
    require(view.get("scene_revision") == scene["scene_revision"], "VIEW_SCENE_REVISION_MISMATCH")
    require(view.get("source_revision") == scene["source"]["source_revision"], "VIEW_SOURCE_REVISION_MISMATCH")
    require(view.get("display_mode") in c["display_modes"], "VIEW_DISPLAY_MODE_UNSUPPORTED")
    require(view.get("sync_mode") in c["sync_modes"], "VIEW_SYNC_MODE_UNSUPPORTED")
    require(view.get("canonical_write") is False, "VIEW_CANONICAL_WRITE_FORBIDDEN")
    layers = view.get("active_layers")
    require(isinstance(layers, list) and len(layers) == len(set(layers)), "VIEW_LAYERS_INVALID")
    require(all(layer in c["layer_ids"] for layer in layers), "VIEW_LAYER_UNSUPPORTED")
    _validate_viewport_state(view["source_viewport"], "SOURCE")
    _validate_viewport_state(view["technical_viewport"], "TECHNICAL")

    selected_object_id = view.get("selected_object_id")
    if selected_object_id is not None:
        require(selected_object_id in {obj["object_id"] for obj in scene["objects"]}, "VIEW_SELECTED_OBJECT_UNKNOWN")

    registration_id = view.get("registration_id")
    if view["display_mode"] == "OVERLAY" or view["sync_mode"] == "SPATIAL_LOCKED":
        registrations = {r["registration_id"]: r for r in scene["registrations"]}
        registration = registrations.get(registration_id)
        require(
            registration_allows_spatial(
                registration,
                source_revision=scene["source"]["source_revision"],
                scene_revision=scene["scene_revision"],
            ),
            "VIEW_SPATIAL_STATE_REQUIRES_VERIFIED_REGISTRATION",
        )


def create_view_snapshot(
    scene: dict[str, Any],
    *,
    requested_mode: str,
    requested_sync_mode: str,
    active_layers: list[str],
    source_viewport: dict[str, Any],
    technical_viewport: dict[str, Any],
    registration_id: str | None = None,
    selected_object_id: str | None = None,
    selected_evidence_region_id: str | None = None,
) -> dict[str, Any]:
    c = _contract()
    resolved = resolve_view_state(
        scene,
        requested_mode=requested_mode,
        requested_sync_mode=requested_sync_mode,
        registration_id=registration_id,
    )
    require(len(active_layers) == len(set(active_layers)), "VIEW_LAYERS_DUPLICATE")
    require(all(layer in c["layer_ids"] for layer in active_layers), "VIEW_LAYER_UNSUPPORTED")
    if selected_object_id is not None:
        require(selected_object_id in {obj["object_id"] for obj in scene["objects"]}, "VIEW_SELECTED_OBJECT_UNKNOWN")

    view = {
        "schema_version": c["view_schema_version"],
        "view_id": stable_id(
            "VIEW",
            scene["scene_revision"],
            resolved["effective_mode"],
            resolved["effective_sync_mode"],
            canonical_json(active_layers),
            canonical_json(source_viewport),
            canonical_json(technical_viewport),
            selected_object_id or "",
            selected_evidence_region_id or "",
        ),
        "scene_revision": scene["scene_revision"],
        "source_revision": scene["source"]["source_revision"],
        "display_mode": resolved["effective_mode"],
        "sync_mode": resolved["effective_sync_mode"],
        "registration_id": registration_id if resolved["spatial_registration_usable"] else None,
        "active_layers": list(active_layers),
        "source_viewport": deepcopy(source_viewport),
        "technical_viewport": deepcopy(technical_viewport),
        "selected_object_id": selected_object_id,
        "selected_evidence_region_id": selected_evidence_region_id,
        "blocked_actions_at_save": list(resolved["blocked_actions"]),
        "canonical_write": False,
        "engineering_authority_effect": "NONE",
    }
    validate_view_snapshot(scene, view)
    return view


def build_working_session_patch(
    scene: dict[str, Any],
    *,
    edits: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    view: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_scene(scene)
    for edit in edits:
        validate_working_edit(scene, edit)
    for issue in issues:
        validate_reading_issue(scene, issue)
    if view is not None:
        validate_view_snapshot(scene, view)

    patch = {
        "schema_version": "1.0",
        "working_session_patch_id": stable_id(
            "WSP",
            scene["scene_revision"],
            canonical_json([e["working_edit_id"] for e in edits]),
            canonical_json([i["reading_issue_id"] for i in issues]),
            view["view_id"] if view else "",
        ),
        "scene_revision": scene["scene_revision"],
        "source_revision": scene["source"]["source_revision"],
        "working_edits": deepcopy(edits),
        "reading_issues": deepcopy(issues),
        "view": deepcopy(view),
        "canonical_write": False,
        "promotion_authorized": False,
        "authority_effect": "NONE",
    }
    return patch


def scene_digest(scene_without_revision: dict[str, Any]) -> str:
    payload = deepcopy(scene_without_revision)
    payload.pop("scene_revision", None)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
