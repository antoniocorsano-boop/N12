#!/usr/bin/env python3
"""Deterministic gate for the G4 prototype-led Object Workbench POC."""
from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient

import cew_oar_g4_assisted_workbench as assisted
import cew_oar_g4_atomic_store as atomic_store
import cew_oar_g4_prototype_search as prototype_search
import cew_oar_g4_region_binding as binding
import cew_oar_g4_region_workbench as oar
import cew_runtime_audit_store as audit_store

ROOT = Path(__file__).resolve().parents[1]
ADOPTION = ROOT / "automation/CEW_OAR_ASSISTED_LOCALIZATION_ADOPTION_v1.json"
MANIFEST = ROOT / "artifacts/cew_oar_g4_assisted/manifest.json"
SNAP = ROOT / "artifacts/cew_oar_g4_assisted/snap_candidates.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _first_support_for_family(family_id: str) -> str:
    contract = binding.load_contract()
    row = next(item for item in contract["objects"] if item["family_id"] == family_id)
    return str(row["support_id"])


def main() -> None:
    adoption = read_json(ADOPTION)
    assert adoption["schema"] == "CEW_OAR_ASSISTED_LOCALIZATION_ADOPTION_v1"
    assert adoption["status"] == "POC_NON_PROMOTING"
    components = adoption["adopted_components"]
    assert components["viewer"]["name"] == "OpenSeadragon"
    assert components["viewer"]["version"] == "6.1.0"
    assert components["viewer"]["license"] == "BSD-3-Clause"
    assert components["annotation"]["name"] == "@annotorious/openseadragon"
    assert components["annotation"]["version"] == "3.8.10"
    assert components["annotation"]["license"] == "BSD-3-Clause"
    assert components["deep_zoom"]["name"] == "sharp"
    assert components["deep_zoom"]["version"] == "0.35.4"
    assert components["deep_zoom"]["system_vips_cli_required"] is False
    assert components["snap_geometry"]["version"] == "4.12.0.88"
    assert components["snap_geometry"]["runtime_required"] is False

    interaction = adoption["interaction_contract"]
    assert interaction["primary_localization_mode"] == "DRAW_OR_ADJUST_EXAMPLE_THEN_FIND_SIMILAR"
    assert interaction["primary_actions"] == ["TEACH_THIS_IS", "FIND_SIMILAR", "REVIEW_SIMILAR_GROUP"]
    assert interaction["prototype_is_project_local_training_example"] is True
    assert interaction["prototype_is_not_oar_classification"] is True
    assert interaction["similar_search_auto_assigns_support_identity"] is False
    assert interaction["similar_search_auto_confirms_family"] is False
    assert interaction["snap_role"] == "FALLBACK_LOCAL_BOX_AID"
    assert interaction["snap_is_proposal_only"] is True
    assert interaction["manual_freehand_bbox_required"] is False
    assert interaction["family_prior_may_establish_classification"] is False
    prototype_contract = adoption["prototype_search_contract"]
    assert prototype_contract["domain_primitives_reused"] == [
        "ObjectPrototype", "ObjectFamily", "ObjectSignature", "EvidenceProvenance"
    ]
    assert prototype_contract["training_receipt_type"] == prototype_search.RECEIPT_TYPE
    assert prototype_contract["tap_distance_used"] is False
    assert prototype_contract["candidate_support_identity"] == "UNASSIGNED_UNTIL_SEPARATE_HUMAN_BINDING"
    assert prototype_contract["human_group_review_required"] is True
    assert adoption["authority"] == {
        "oar_human_confirmation": False,
        "oar_classification_confirmed": False,
        "f2_registry_written": False,
        "canonical_write_authorized": False,
        "structural_identity_authorized": False,
        "engineering_authority_effect": "NONE",
    }

    manifest = read_json(MANIFEST)
    assert manifest["schema"] == "CEW_OAR_G4_ASSISTED_ASSET_MANIFEST_v1"
    assert manifest["derived_asset_id"] == "CEW-N12-ASSET-TAV05S-P001-OAR-300DPI"
    assert manifest["derived_asset_sha256"] == "6344abae8d390ef799812c808427431e684a61cca6bb5792de331b2b9d2b6252"
    assert manifest["derived_asset_dimensions_px"] == [7016, 12530]
    assert manifest["deepzoom"]["builder"] == "sharp"
    assert manifest["deepzoom"]["builder_version"] == "0.35.4"
    assert manifest["deepzoom"]["system_vips_cli_required"] is False
    assert manifest["deepzoom"]["tile_count"] > 0
    assert manifest["snap"]["candidate_count"] > 0
    assert manifest["snap"]["runtime_opencv_required"] is False
    assert manifest["authority"]["canonical_write_authorized"] is False

    builder_source = (ROOT / "scripts/build_cew_oar_g4_assisted_assets.py").read_text(encoding="utf-8")
    worker_source = (ROOT / "scripts/cew_oar_g4_snap_worker.py").read_text(encoding="utf-8")
    deepzoom_worker = (ROOT / "scripts/cew_oar_g4_deepzoom_worker.cjs").read_text(encoding="utf-8")
    atomic_source = (ROOT / "scripts/cew_oar_g4_atomic_store.py").read_text(encoding="utf-8")
    region_source = (ROOT / "scripts/cew_oar_g4_region_workbench.py").read_text(encoding="utf-8")
    prototype_source = (ROOT / "scripts/cew_oar_g4_prototype_search.py").read_text(encoding="utf-8")
    assert 'SHARP_SPEC = "sharp@0.35.4"' in builder_source
    assert '"vips", "dzsave"' not in builder_source
    assert ".tile({ layout: 'dz', size: 256, overlap: 1" in deepzoom_worker
    assert "LONG_AXIS_SUPPRESSED" in worker_source
    assert "nested_raw_candidate_suppressed_count" in worker_source
    assert 'envelope.get("best_family_prior") != row.get("best_family_prior")' not in worker_source
    assert "ObjectPrototype" in prototype_source and "ObjectFamily" in prototype_source
    assert "PROJECT_LOCAL_HUMAN_PROTOTYPE_GEOMETRIC_SIMILARITY_V1" in prototype_source
    assert "search_uses_tap_distance\": False" in prototype_source
    assert "support_identity\": None" in prototype_source
    assert "pg_advisory_xact_lock" in atomic_source
    assert "CREATE TABLE" not in atomic_source
    assert "cew_oar_region_revision_heads" not in atomic_source
    assert "_public_receipt_reason" in region_source
    assert "reason_code" in region_source

    snap = read_json(SNAP)
    assert snap["schema"] == "CEW_OAR_G4_SNAP_CANDIDATES_v1"
    assert snap["source_dimensions_px"] == [7016, 12530]
    assert snap["coordinate_system"] == "NORMALIZED_0_1"
    assert snap["candidate_count"] == len(snap["candidates"]) > 0
    assert snap["axis_suppressed_candidate_count"] > 0
    assert snap["nested_raw_candidate_suppressed_count"] > 0
    assert snap["authority"]["snap_candidates_are_authority"] is False
    for candidate in snap["candidates"][:100]:
        bbox = binding.normalize_bbox(candidate["bbox"])
        assert bbox["x"] + bbox["w"] <= 1.0000001
        assert bbox["y"] + bbox["h"] <= 1.0000001

    # The mature primary path must prefer same-scale footprints over internal
    # sub-cells even when both have a plausible aspect ratio.
    prototype_bbox = {"x": 0.4, "y": 0.4, "w": 0.020, "h": 0.020}
    full = {
        "bbox": {"x": 0.1, "y": 0.1, "w": 0.0195, "h": 0.0205},
        "rectangularity": 0.85,
        "detector": "LONG_AXIS_SUPPRESSED",
    }
    nested = {
        "bbox": {"x": 0.2, "y": 0.2, "w": 0.0095, "h": 0.0120},
        "rectangularity": 0.92,
        "detector": "RAW_CONTOUR",
    }
    full_score = prototype_search._candidate_similarity(prototype_bbox, full)
    nested_score = prototype_search._candidate_similarity(prototype_bbox, nested)
    assert full_score["score"] > nested_score["score"]
    assert full_score["size"] > nested_score["size"]
    assert nested_score["size"] < 0.70

    # Keep fallback snap valid but explicitly non-primary and non-promoting.
    sample = next(
        row for row in snap["candidates"]
        if row.get("detector") == "LONG_AXIS_SUPPRESSED" and row.get("best_family_prior") == "COL-G4-40X40"
    )
    support_id = _first_support_for_family("COL-G4-40X40")
    ranked = assisted._rank_snap(support_id, sample["center"]["x"], sample["center"]["y"], radius=0.01)
    assert ranked["state"] == "SNAP_PROPOSALS_READY"
    assert ranked["candidates"]
    assert ranked["snap_role"] == "FALLBACK_LOCAL_BOX_AID"
    assert ranked["snap_is_proposal_only"] is True
    assert ranked["oar_classification_confirmed"] is False

    for bbox in ({"x": 0.1, "y": 0.2, "w": 0.03, "h": 0.04}, sample["bbox"]):
        px = {"x": bbox["x"] * 7016, "y": bbox["y"] * 12530, "w": bbox["w"] * 7016, "h": bbox["h"] * 12530}
        back = {"x": px["x"] / 7016, "y": px["y"] / 12530, "w": px["w"] / 7016, "h": px["h"] / 12530}
        assert all(math.isclose(back[key], bbox[key], rel_tol=0, abs_tol=1e-12) for key in bbox)

    source = (ROOT / "scripts/cew_oar_g4_assisted_workbench.py").read_text(encoding="utf-8")
    assert "cdn.jsdelivr" not in source and "unpkg.com" not in source
    assert "/workbench/oar/g4-assisted/vendor/openseadragon-6.1.0.min.js" in source
    assert "/workbench/oar/g4-assisted/vendor/annotorious-openseadragon-3.8.10.js" in source
    assert "AnnotoriousOSD.createOSDAnnotator" in source
    assert "setDrawingEnabled" in source and "setDrawingTool" in source
    assert "Insegna questo esempio" in source
    assert "Cerca simili nella tavola" in source
    assert "Snap fallback" in source
    assert "/api/workbench/oar/g4-assisted/teach-example" in source
    assert "/api/workbench/oar/g4-assisted/find-similar" in source
    assert "similarPreview" in source
    assert "canonical_write_authorized" in source and "False" in source

    assisted_router = assisted.build_router()
    paths = {route.path for route in assisted_router.routes}
    for path in (
        "/workbench/oar/g4-assisted",
        "/workbench/oar/g4-assisted/vendor/{filename}",
        "/workbench/oar/g4-assisted/deepzoom/{asset_path:path}",
        "/api/workbench/oar/g4-assisted/status",
        "/api/workbench/oar/g4-assisted/snap",
        "/api/workbench/oar/g4-assisted/teach-example",
        "/api/workbench/oar/g4-assisted/find-similar",
    ):
        assert path in paths, path

    original_region_store = oar._base.RUNTIME_STORE
    original_prototype_store = prototype_search.RUNTIME_STORE
    original_backend_status = audit_store.backend_status
    with tempfile.TemporaryDirectory(prefix="cew-oar-prototype-workbench-") as tmp:
        root = Path(tmp)
        oar._base.RUNTIME_STORE = root / "regions"
        prototype_search.RUNTIME_STORE = root / "prototypes"
        audit_store.backend_status = lambda: "FILESYSTEM_APPEND_ONLY"
        try:
            app = FastAPI()
            app.include_router(oar.build_router())
            app.include_router(assisted_router)
            client = TestClient(app)

            page = client.get("/workbench/oar/g4-assisted")
            assert page.status_code == 200
            assert "Object Workbench" in page.text
            assert "Insegna questo esempio" in page.text
            assert "Cerca simili nella tavola" in page.text
            assert page.headers["x-cew-canonical-write"] == "false"

            status = client.get("/api/workbench/oar/g4-assisted/status")
            assert status.status_code == 200
            status_body = status.json()
            assert status_body["primary_interaction"] == "TEACH_EXAMPLE_THEN_FIND_SIMILAR"
            assert status_body["snap_role"] == "FALLBACK_LOCAL_BOX_AID"
            assert status_body["prototype_search_auto_assigns_support_identity"] is False

            teach = client.post(
                "/api/workbench/oar/g4-assisted/teach-example",
                json={
                    "decision_id": "oar-g4-prototype-ci-teach-001",
                    "support_id": support_id,
                    "bbox": sample["bbox"],
                },
            )
            assert teach.status_code == 200, teach.text
            teach_body = teach.json()
            assert teach_body["state"] == "PROTOTYPE_TAUGHT"
            assert teach_body["prototype_id"].startswith("OPROT-G4-")
            assert teach_body["prototype_authority"] == "HUMAN_TRAINING_EXAMPLE_ONLY"
            assert teach_body["canonical_write_authorized"] is False
            prototype_id = teach_body["prototype_id"]

            stored_training = prototype_search.load_teach_receipts()
            assert stored_training["receipt_count"] == 1
            training_receipt = stored_training["receipts"][0]
            assert training_receipt["prototype"]["human_validated_training_example"] is True
            assert training_receipt["prototype"]["evidence_region_complete"] is False
            assert training_receipt["oar_classification_confirmed"] is False

            similar = client.get(
                "/api/workbench/oar/g4-assisted/find-similar",
                params={"prototype_id": prototype_id, "limit": 32},
            )
            assert similar.status_code == 200, similar.text
            similar_body = similar.json()
            assert similar_body["state"] == "SIMILAR_OBJECT_PROPOSALS_READY"
            assert similar_body["candidate_count"] > 0
            assert similar_body["search_uses_tap_distance"] is False
            assert similar_body["search_auto_assigns_support_identity"] is False
            assert similar_body["search_auto_confirms_family"] is False
            assert similar_body["human_group_review_required"] is True
            assert similar_body["canonical_write_authorized"] is False
            for candidate in similar_body["candidates"]:
                assert candidate["support_identity"] is None
                assert candidate["review_state"] == "SIMILARITY_PROPOSAL"

            # Preserve the existing governed single-object geometry boundary.
            snap_response = client.get(
                "/api/workbench/oar/g4-assisted/snap",
                params={"support_id": support_id, "x": sample["center"]["x"], "y": sample["center"]["y"], "radius": 0.01},
            )
            assert snap_response.status_code == 200
            proposal_bbox = snap_response.json()["candidates"][0]["bbox"]
            proposal = client.post(
                "/api/workbench/oar/g4-regions/receipt",
                json={
                    "decision_id": "oar-g4-assisted-ci-proposal-001",
                    "support_id": support_id,
                    "action": "PROPOSE_GEOMETRY",
                    "bbox": proposal_bbox,
                },
            )
            assert proposal.status_code == 200, proposal.text
            proposal_body = proposal.json()
            assert proposal_body["object_state"] == "PROPOSED"
            assert proposal_body["atomic_revision"] is True
            assert proposal_body["canonical_write_authorized"] is False

            rejected = client.post(
                "/api/workbench/oar/g4-regions/receipt",
                json={
                    "decision_id": "oar-g4-assisted-ci-invalid-001",
                    "support_id": support_id,
                    "action": "PROPOSE_GEOMETRY",
                    "bbox": {"x": -0.1, "y": 0.2, "w": 0.1, "h": 0.1},
                },
            )
            assert rejected.status_code == 422
            rejected_body = rejected.json()
            assert rejected_body["state"] == "OAR_REGION_BBOX_OUT_OF_RANGE"
            assert rejected_body["reason_code"] == "OAR_REGION_BBOX_OUT_OF_RANGE"
            assert "reason" not in rejected_body

            blocked = client.get("/workbench/oar/g4-assisted/deepzoom/../manifest.json")
            assert blocked.status_code in {404, 422}
        finally:
            oar._base.RUNTIME_STORE = original_region_store
            prototype_search.RUNTIME_STORE = original_prototype_store
            audit_store.backend_status = original_backend_status

    print("CEW_OAR_G4_ASSISTED_LOCALIZATION_PASS")
    print(f"deepzoom_tiles={manifest['deepzoom']['tile_count']} snap_candidates={snap['candidate_count']}")
    print(f"axis_suppressed={snap['axis_suppressed_candidate_count']} nested_raw_suppressed={snap['nested_raw_candidate_suppressed_count']}")
    print("primary_workflow=TEACH_THIS_IS->FIND_SIMILAR->REVIEW_SIMILAR_GROUP")
    print("prototype_receipt=PASS prototype_search=PASS support_identity_auto_assignment=false")
    print("prototype_search_tap_distance=false snap_role=FALLBACK_LOCAL_BOX_AID")
    print("snap_to_receipt_post=PASS atomic_filesystem_revision=PASS safe_reason_code=PASS")
    print("oar_classification_confirmed=false canonical_write_authorized=false structural_identity_authorized=false")


if __name__ == "__main__":
    main()
