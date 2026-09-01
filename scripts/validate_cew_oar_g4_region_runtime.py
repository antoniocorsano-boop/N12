#!/usr/bin/env python3
"""Runtime smoke for the authenticated G4/TAV-05S localization surface."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient
import fitz

import cew_oar_g4_region_binding as binding
import cew_oar_g4_region_workbench as workbench
import cew_runtime_audit_store as audit_store

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROUTES = {
    "/workbench/oar/g4-regions",
    "/workbench/oar/g4-regions/source.png",
    "/api/workbench/oar/g4-regions/status",
    "/api/workbench/oar/g4-regions/receipt",
}


def main() -> None:
    source = workbench.verify_source()
    assert source["state"] == "READY"
    assert source["source_sha256"] == workbench.EXPECTED_SOURCE_SHA256
    assert source["page_width_pt"] == workbench.EXPECTED_PAGE_WIDTH_PT
    assert source["page_height_pt"] == workbench.EXPECTED_PAGE_HEIGHT_PT
    assert source["canonical_write_authorized"] is False

    raster = workbench.ensure_runtime_raster()
    assert raster.is_file()
    pix = fitz.Pixmap(str(raster))
    assert pix.width == 3508, pix.width
    assert pix.height == 6265, pix.height

    router = workbench.build_router()
    route_paths = {route.path for route in router.routes}
    assert EXPECTED_ROUTES.issubset(route_paths)

    isolated = FastAPI()
    isolated.include_router(router)
    client = TestClient(isolated)
    page = client.get("/workbench/oar/g4-regions")
    assert page.status_code == 200
    assert "Localizzazione documentale — Pilastri G4" in page.text
    assert page.headers["x-cew-oar-human-confirmation"] == "false"
    assert page.headers["x-cew-canonical-write"] == "false"

    image = client.get("/workbench/oar/g4-regions/source.png")
    assert image.status_code == 200
    assert image.headers["x-cew-derived-authority"] == "DERIVED_INTERACTION_AID_ONLY"
    assert image.headers["x-cew-source-sha256"] == workbench.EXPECTED_SOURCE_SHA256

    original_backend_status = audit_store.backend_status
    original_store = workbench.RUNTIME_STORE
    try:
        audit_store.backend_status = lambda: "FILESYSTEM_APPEND_ONLY"
        with tempfile.TemporaryDirectory(prefix="cew-oar-g4-runtime-") as tmp:
            workbench.RUNTIME_STORE = Path(tmp)
            status = client.get("/api/workbench/oar/g4-regions/status")
            assert status.status_code == 200
            state = status.json()
            assert state["summary"]["UNBOUND"] == 34
            assert state["summary"]["GEOMETRY_CONFIRMED"] == 0
            assert state["canonical_write_authorized"] is False

            bbox = {"x": 0.10, "y": 0.20, "w": 0.02, "h": 0.03}
            proposal = client.post(
                "/api/workbench/oar/g4-regions/receipt",
                json={
                    "decision_id": "runtime-g4-1-proposal",
                    "support_id": "1",
                    "action": binding.PROPOSAL_ACTION,
                    "bbox": bbox,
                },
            )
            assert proposal.status_code == 200, proposal.text
            assert proposal.json()["object_state"] == "PROPOSED"
            assert proposal.json()["canonical_write_authorized"] is False

            confirmation = client.post(
                "/api/workbench/oar/g4-regions/receipt",
                json={
                    "decision_id": "runtime-g4-1-confirm",
                    "support_id": "1",
                    "action": binding.CONFIRM_ACTION,
                },
            )
            assert confirmation.status_code == 200, confirmation.text
            confirmed_body = confirmation.json()
            assert confirmed_body["object_state"] == "GEOMETRY_CONFIRMED"
            assert confirmed_body["oar_human_confirmation"] is False
            assert confirmed_body["canonical_write_authorized"] is False

            frozen = client.post(
                "/api/workbench/oar/g4-regions/receipt",
                json={
                    "decision_id": "runtime-g4-1-reproposal",
                    "support_id": "1",
                    "action": binding.PROPOSAL_ACTION,
                    "bbox": {"x": 0.11, "y": 0.20, "w": 0.02, "h": 0.03},
                },
            )
            assert frozen.status_code == 422
            assert "OAR_REGION_GEOMETRY_ALREADY_CONFIRMED" in frozen.json()["reason"]
    finally:
        audit_store.backend_status = original_backend_status
        workbench.RUNTIME_STORE = original_store

    # The real application must still place the composed router behind its
    # global access middleware. The smoke runs from scripts/, so explicitly add
    # the repository root before importing the production application module.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    os.environ["CEW_AUTH_DISABLED_FOR_TEST"] = "1"
    import app as runtime_app
    runtime_client = TestClient(runtime_app.app)
    response = runtime_client.get("/workbench/oar/g4-regions")
    assert response.status_code == 200
    assert "Localizzazione documentale — Pilastri G4" in response.text
    os.environ.pop("CEW_AUTH_DISABLED_FOR_TEST", None)
    unauthorized = runtime_client.get("/workbench/oar/g4-regions", follow_redirects=False)
    assert unauthorized.status_code == 303
    assert unauthorized.headers["location"] == "/login"

    print("CEW_OAR_G4_REGION_RUNTIME_PASS")
    print("source_sha_verified=true raster_150dpi=3508x6265 routes=4")
    print("proposal_persisted=true confirmation_persisted=true post_confirmation_mutation_rejected=true")
    print("global_auth_guard=true canonical_write_authorized=false oar_human_confirmation=false")


if __name__ == "__main__":
    main()
