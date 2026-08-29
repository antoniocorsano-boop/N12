#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy

import cew_professional_workbench_core as core
import cew_professional_workbench_projection as projection

TASKS = [f"ERW-N12-00{i}" for i in range(1, 5)]


def expect_value_error(fn, code: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if code not in str(exc):
            raise AssertionError(f"expected {code}, got {exc}") from exc
        return
    raise AssertionError(f"expected ValueError containing {code}")


def main() -> None:
    scenes = {task: projection.build_scene(task) for task in TASKS}
    for task, scene in scenes.items():
        core.validate_scene(scene)
        assert scene["task_id"] == task
        assert scene["authority"]["canonical_write_authorized"] is False
        assert scene["authority"]["engineering_authority_effect"] == "NONE"
        assert scene["authority"]["promotion_authorized"] is False
        assert scene["source"]["authority"] == "VERIFIED_IMMUTABLE_PRIMARY_SOURCE"
        assert scene["capabilities"]["source_viewer"] == "F3_DZI_MANIFEST_REUSED"
        assert scene["capabilities"]["dual_vector_agreement"].startswith("UPSTREAM_AVAILABLE")
        assert scene["registrations"][0]["state"] == "UNAVAILABLE"
        assert scene["capabilities"]["overlay_available"] is False
        assert scene["capabilities"]["spatial_sync_available"] is False

    # F6's rejected candidate-comparison context is preserved without inventing a binding.
    t4 = scenes["ERW-N12-004"]
    assert len(t4["objects"]) == 1
    obj = t4["objects"][0]
    assert obj["object_family"] == "GovernedStructuralObjectProjection"
    assert obj["governed_source_member_id"] == "G5-B017"
    assert obj["binding_state"] == "UNBOUND"
    assert obj["selection_authorized"] is False
    assert t4["evidence_links"][0]["link_type"] == "CANDIDATE_CORRESPONDENCE"
    assert t4["evidence_links"][0]["binding_state"] == "UNBOUND"

    # Overlay and spatial lock fail closed when there is no VERIFIED registration.
    state = core.resolve_view_state(
        t4,
        requested_mode="OVERLAY",
        requested_sync_mode="SPATIAL_LOCKED",
        registration_id=t4["registrations"][0]["registration_id"],
    )
    assert state["effective_mode"] == "SPLIT"
    assert state["effective_sync_mode"] == "SEMANTIC"
    assert state["spatial_registration_usable"] is False
    assert "OVERLAY_REQUIRES_VERIFIED_REVISION_MATCHED_REGISTRATION" in state["blocked_actions"]
    assert "SPATIAL_LOCK_REQUIRES_VERIFIED_REVISION_MATCHED_REGISTRATION" in state["blocked_actions"]
    assert state["canonical_write_authorized"] is False

    # Source-only tasks remain usable even when the technical scene is unavailable.
    t1 = scenes["ERW-N12-001"]
    source_only = core.resolve_view_state(
        t1,
        requested_mode="TECHNICAL",
        requested_sync_mode="OFF",
    )
    assert source_only["effective_mode"] == "SOURCE"
    assert "TECHNICAL_SCENE_UNAVAILABLE" in source_only["blocked_actions"]

    # A revision-matched verified affine registration is accepted as a mechanism,
    # without inventing one for the real project.
    synthetic = deepcopy(t4)
    synthetic["scene_revision"] = "SYNTHETIC_TEST_SCENE_REVISION"
    reg = synthetic["registrations"][0]
    reg.update(
        {
            "state": "VERIFIED",
            "transform_type": "AFFINE_2D",
            "source_revision": synthetic["source"]["source_revision"],
            "scene_revision": synthetic["scene_revision"],
            "control_correspondences": [
                {"source": [0.0, 0.0], "technical": [0.0, 0.0]},
                {"source": [1.0, 0.0], "technical": [1.0, 0.0]},
                {"source": [0.0, 1.0], "technical": [0.0, 1.0]},
            ],
            "matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            "residual_metrics": {"method": "SYNTHETIC_TEST_ONLY", "measured": True},
            "verification_process": "UNIT_CONTRACT_TEST",
            "verification_actor_or_gate": "AUTOMATED_SYNTHETIC_TEST",
        }
    )
    core.validate_scene(synthetic)
    spatial = core.resolve_view_state(
        synthetic,
        requested_mode="OVERLAY",
        requested_sync_mode="SPATIAL_LOCKED",
        registration_id=reg["registration_id"],
    )
    assert spatial["effective_mode"] == "OVERLAY"
    assert spatial["effective_sync_mode"] == "SPATIAL_LOCKED"
    assert spatial["spatial_registration_usable"] is True

    stale = deepcopy(reg)
    stale["source_revision"] = "WRONG_SOURCE_REVISION"
    expect_value_error(
        lambda: core.validate_registration(
            stale,
            source_revision=synthetic["source"]["source_revision"],
            scene_revision=synthetic["scene_revision"],
        ),
        "VERIFIED_REGISTRATION_SOURCE_REVISION_MISMATCH",
    )

    # WorkingEdit is object-bound, preserves the base value, and cannot edit governed objects.
    editable_scene = deepcopy(t1)
    text_obj = {
        "object_id": "RT-SYNTHETIC-TEST",
        "object_family": "RecognizedText",
        "coordinate_space": "SOURCE_NORMALIZED_0_1",
        "authority_state": "DERIVED_RECOGNITION_ONLY",
        "geometry": {"type": "BBOX", "x": 0.1, "y": 0.1, "width": 0.2, "height": 0.05},
        "properties": {"literal_text": "2 Φ12", "normalized_candidate": "2 Φ12"},
        "provenance": {
            "source_version_id": editable_scene["source"]["source_version_id"],
            "page_id": editable_scene["source"]["page_id"],
            "origin": "SYNTHETIC_TEST_ONLY",
        },
        "canonical_write_authorized": False,
    }
    editable_scene["objects"].append(text_obj)
    editable_scene["scene_revision"] = "SYNTHETIC_EDITABLE_SCENE_REVISION"
    core.validate_scene(editable_scene)
    edit = core.create_working_edit(
        editable_scene,
        target_object_id=text_obj["object_id"],
        property_name="literal_text",
        proposed_value="2 Φ14",
        author_session="SYNTHETIC_SESSION",
    )
    assert edit["base_value"] == "2 Φ12"
    assert edit["proposed_value"] == "2 Φ14"
    assert text_obj["properties"]["literal_text"] == "2 Φ12"
    assert edit["canonical_write"] is False
    assert edit["promotion_authorized"] is False

    expect_value_error(
        lambda: core.create_working_edit(
            t4,
            target_object_id=obj["object_id"],
            property_name="section_cm",
            proposed_value="40x50",
            author_session="SYNTHETIC_SESSION",
        ),
        "WORKING_EDIT_TARGET_READ_ONLY",
    )

    # ReadingIssue must remain graphically/evidence anchored.
    issue = core.create_reading_issue(
        t4,
        question="Verificare la corrispondenza candidata senza creare binding.",
        anchor_object_id=obj["object_id"],
        evidence_link_ids=[t4["evidence_links"][0]["evidence_link_id"]],
    )
    assert issue["anchor_object_id"] == obj["object_id"]
    assert issue["canonical_write"] is False
    expect_value_error(
        lambda: core.create_reading_issue(t1, question="Issue senza ancora"),
        "READING_ISSUE_GRAPHICAL_OR_EVIDENCE_ANCHOR_REQUIRED",
    )

    # Viewport pixels can never become persisted technical geometry.
    bad_scene = deepcopy(t1)
    bad_scene["objects"].append(
        {
            "object_id": "BAD-VIEWPORT-OBJECT",
            "object_family": "DocumentGraphicPrimitive",
            "coordinate_space": "VIEWPORT_PX",
            "authority_state": "DERIVED_DOCUMENT_GEOMETRY",
            "geometry": {"type": "LINE", "a": [1, 1], "b": [2, 2]},
            "properties": {},
            "provenance": {"source_version_id": bad_scene["source"]["source_version_id"]},
        }
    )
    expect_value_error(lambda: core.validate_scene(bad_scene), "VIEWPORT_COORDINATES_CANNOT_BE_SCENE_GEOMETRY")

    print("CEW_PROFESSIONAL_WORKBENCH_CORE = PASS")
    print("SCENES = 4/4")
    print("F3_MANIFEST_REUSE = PASS")
    print("F6_UNBOUND_CANDIDATE_CONTEXT = PRESERVED")
    print("DUAL_VECTOR_AUTHORITY_BOUNDARY = PRESERVED_UPSTREAM")
    print("OVERLAY_WITHOUT_VERIFIED_REGISTRATION = FAIL_CLOSED")
    print("SPATIAL_LOCK_WITHOUT_VERIFIED_REGISTRATION = FAIL_CLOSED")
    print("WORKING_EDIT_BASE_VALUE_IMMUTABLE = PASS")
    print("GOVERNED_STRUCTURAL_EDIT = FORBIDDEN")
    print("READING_ISSUE_ANCHOR = REQUIRED")
    print("VIEWPORT_GEOMETRY_PERSISTENCE = FORBIDDEN")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("HVA_EXECUTION_AUTHORIZED = false")


if __name__ == "__main__":
    main()
