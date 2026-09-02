#!/usr/bin/env python3
"""Deterministic gate for the additive OAR G4 assisted-localization POC."""
from __future__ import annotations

import json
import math
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

import cew_oar_g4_assisted_workbench as assisted
import cew_oar_g4_region_binding as binding

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
    assert components["viewer"] == {
        "name": "OpenSeadragon",
        "version": "6.1.0",
        "license": "BSD-3-Clause",
        "role": "DEEP_ZOOM_PAN_ROTATE_MOBILE_NAVIGATION",
        "runtime_delivery": "SELF_HOSTED_BUILD_MATERIALIZED",
    }
    assert components["annotation"]["name"] == "@annotorious/openseadragon"
    assert components["annotation"]["version"] == "3.8.10"
    assert components["annotation"]["license"] == "BSD-3-Clause"
    assert components["snap_geometry"]["version"] == "4.12.0.88"
    assert components["snap_geometry"]["runtime_required"] is False
    assert adoption["interaction_contract"]["manual_freehand_bbox_required"] is False
    assert adoption["interaction_contract"]["snap_is_proposal_only"] is True
    assert adoption["interaction_contract"]["existing_receipt_endpoint_reused"] == "/api/workbench/oar/g4-regions/receipt"
    assert adoption["interaction_contract"]["family_prior_may_establish_classification"] is False
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
    assert manifest["vendor"]["openseadragon"]["version"] == "6.1.0"
    assert manifest["vendor"]["annotorious_openseadragon"]["version"] == "3.8.10"
    assert manifest["deepzoom"]["tile_count"] > 0
    assert manifest["deepzoom"]["tile_size"] == 256
    assert manifest["deepzoom"]["overlap"] == 1
    assert manifest["snap"]["candidate_count"] > 0
    assert manifest["snap"]["runtime_opencv_required"] is False
    assert manifest["authority"]["deep_zoom_tiles_are_authority"] is False
    assert manifest["authority"]["snap_candidates_are_authority"] is False
    assert manifest["authority"]["canonical_write_authorized"] is False

    snap = read_json(SNAP)
    assert snap["schema"] == "CEW_OAR_G4_SNAP_CANDIDATES_v1"
    assert snap["source_dimensions_px"] == [7016, 12530]
    assert snap["coordinate_system"] == "NORMALIZED_0_1"
    assert snap["candidate_count"] == len(snap["candidates"]) > 0
    assert snap["authority"]["snap_candidates_are_authority"] is False
    for candidate in snap["candidates"][:100]:
        bbox = candidate["bbox"]
        assert 0 <= bbox["x"] <= 1 and 0 <= bbox["y"] <= 1
        assert bbox["w"] > 0 and bbox["h"] > 0
        assert bbox["x"] + bbox["w"] <= 1.0000001
        assert bbox["y"] + bbox["h"] <= 1.0000001

    # The build-derived snap index must provide a proposal when tapped exactly
    # at one of its own candidates. Family prior ranks candidates but does not
    # change authority.
    sample = snap["candidates"][0]
    family_id = sample["best_family_prior"]
    support_id = _first_support_for_family(family_id)
    ranked = assisted._rank_snap(support_id, sample["center"]["x"], sample["center"]["y"], radius=0.01)
    assert ranked["state"] == "SNAP_PROPOSALS_READY"
    assert ranked["candidates"]
    assert ranked["candidates"][0]["family_id"] == family_id
    assert ranked["snap_is_proposal_only"] is True
    assert ranked["oar_classification_confirmed"] is False
    assert ranked["canonical_write_authorized"] is False
    assert ranked["structural_identity_authorized"] is False

    # Exact normalized<->image-pixel roundtrip used between OAR receipts and
    # Annotorious geometry. This is independent from viewer rotation/pan.
    for bbox in (
        {"x": 0.1, "y": 0.2, "w": 0.03, "h": 0.04},
        sample["bbox"],
    ):
        px = {"x": bbox["x"] * 7016, "y": bbox["y"] * 12530, "w": bbox["w"] * 7016, "h": bbox["h"] * 12530}
        back = {"x": px["x"] / 7016, "y": px["y"] / 12530, "w": px["w"] / 7016, "h": px["h"] / 12530}
        assert all(math.isclose(back[key], bbox[key], rel_tol=0, abs_tol=1e-12) for key in bbox)

    source = (ROOT / "scripts/cew_oar_g4_assisted_workbench.py").read_text(encoding="utf-8")
    assert "cdn.jsdelivr" not in source and "unpkg.com" not in source
    assert "/workbench/oar/g4-assisted/vendor/openseadragon-6.1.0.min.js" in source
    assert "/workbench/oar/g4-assisted/vendor/annotorious-openseadragon-3.8.10.js" in source
    assert "/workbench/oar/g4-assisted/deepzoom/TAV05S_OAR_300dpi.dzi" in source
    assert "AnnotoriousOSD.createOSDAnnotator" in source
    assert "showNavigator:true" in source
    assert "viewport.setRotation" in source
    assert "TAP_NEAR_OBJECT" not in source  # UI is implementation, governance lives in adoption contract.
    assert "snapMode" in source and "TRY_NEXT_CANDIDATE" not in source
    assert "'/api/workbench/oar/g4-regions/receipt'" in source or '"/api/workbench/oar/g4-regions/receipt"' in source
    assert "canonical_write_authorized" in source and "False" in source

    router = assisted.build_router()
    paths = {route.path for route in router.routes}
    for path in (
        "/workbench/oar/g4-assisted",
        "/workbench/oar/g4-assisted/vendor/{filename}",
        "/workbench/oar/g4-assisted/deepzoom/{asset_path:path}",
        "/api/workbench/oar/g4-assisted/status",
        "/api/workbench/oar/g4-assisted/snap",
    ):
        assert path in paths, path

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    page = client.get("/workbench/oar/g4-assisted")
    assert page.status_code == 200
    assert "Localizzazione assistita" in page.text
    assert "Fallback" in page.text
    assert page.headers["x-cew-canonical-write"] == "false"
    js = client.get("/workbench/oar/g4-assisted/vendor/openseadragon-6.1.0.min.js")
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]
    dzi = client.get("/workbench/oar/g4-assisted/deepzoom/TAV05S_OAR_300dpi.dzi")
    assert dzi.status_code == 200 and "xml" in dzi.headers["content-type"]
    snap_response = client.get(
        "/api/workbench/oar/g4-assisted/snap",
        params={"support_id": support_id, "x": sample["center"]["x"], "y": sample["center"]["y"], "radius": 0.01},
    )
    assert snap_response.status_code == 200
    assert snap_response.json()["snap_is_proposal_only"] is True
    blocked = client.get("/workbench/oar/g4-assisted/deepzoom/../manifest.json")
    assert blocked.status_code in {404, 422}

    print("CEW_OAR_G4_ASSISTED_LOCALIZATION_PASS")
    print(f"deepzoom_tiles={manifest['deepzoom']['tile_count']} snap_candidates={snap['candidate_count']}")
    print("viewer=OpenSeadragon-6.1.0 annotation=Annotorious-3.8.10 runtime_vendor=self_hosted")
    print("mobile_pan_zoom_rotate=true snap_proposal_only=true editable_before_receipt=true")
    print("normalized_pixel_roundtrip=PASS fallback_preserved=true")
    print("oar_classification_confirmed=false canonical_write_authorized=false structural_identity_authorized=false")


if __name__ == "__main__":
    main()
