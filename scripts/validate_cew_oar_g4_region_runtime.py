#!/usr/bin/env python3
"""Runtime smoke for the authenticated G4/TAV-05S localization surface."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient
import fitz

import cew_oar_g4_region_binding as binding
import cew_oar_g4_region_workbench as workbench
import cew_oar_g4_source_resolver as resolver
import cew_runtime_audit_store as audit_store

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROUTES = {
    "/workbench/oar/g4-regions",
    "/workbench/oar/g4-regions/source.jpg",
    "/api/workbench/oar/g4-regions/status",
    "/api/workbench/oar/g4-regions/receipt",
}
LEGACY_IMAGE_ROUTE = "/workbench/oar/g4-regions/source.png"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_prebuilt_runtime_boundary(raster: Path) -> None:
    original_build = resolver.BUILD_RASTER
    original_runtime = resolver.RUNTIME_RASTER
    original_fetch = resolver.fetch_source
    original_required = os.environ.get(resolver.REQUIRE_PREBUILT_ENV)
    try:
        with tempfile.TemporaryDirectory(prefix="cew-oar-g4-prebuilt-") as tmp:
            root = Path(tmp)
            prebuilt = root / "TAV05S_OAR_300dpi.jpg"
            shutil.copyfile(raster, prebuilt)
            resolver.BUILD_RASTER = prebuilt
            resolver.RUNTIME_RASTER = root / "must-not-be-created.jpg"
            os.environ[resolver.REQUIRE_PREBUILT_ENV] = "1"

            def forbidden_fetch():
                raise AssertionError("governed Render request must not fetch/rasterize source when prebuilt asset exists")

            resolver.fetch_source = forbidden_fetch
            served = resolver.ensure_runtime_raster()
            assert served == prebuilt
            assert _sha256(served) == resolver.REGISTERED_RENDER_SHA256
            assert not resolver.RUNTIME_RASTER.exists()

            prebuilt.unlink()
            try:
                resolver.ensure_runtime_raster()
            except ValueError as exc:
                assert str(exc) == "OAR_G4_PREBUILT_RENDER_REQUIRED"
            else:
                raise AssertionError("missing prebuilt Render asset must fail closed")
            assert not resolver.RUNTIME_RASTER.exists()
    finally:
        resolver.BUILD_RASTER = original_build
        resolver.RUNTIME_RASTER = original_runtime
        resolver.fetch_source = original_fetch
        if original_required is None:
            os.environ.pop(resolver.REQUIRE_PREBUILT_ENV, None)
        else:
            os.environ[resolver.REQUIRE_PREBUILT_ENV] = original_required


def main() -> None:
    source = workbench.verify_source()
    assert source["state"] == "READY"
    assert source["source_sha256"] == workbench.EXPECTED_SOURCE_SHA256
    assert source["page_width_pt"] == workbench.EXPECTED_PAGE_WIDTH_PT
    assert source["page_height_pt"] == workbench.EXPECTED_PAGE_HEIGHT_PT
    assert source["source_resolution"] == "REMOTE_IMMUTABLE_ARCHIVE_SHA256_VERIFIED"
    assert source["derived_asset_id"] == workbench.REGISTERED_DERIVED_ASSET_ID
    assert source["render_sha256"] == workbench.REGISTERED_RENDER_SHA256
    assert source["render_width_px"] == workbench.REGISTERED_RENDER_WIDTH_PX
    assert source["render_height_px"] == workbench.REGISTERED_RENDER_HEIGHT_PX
    assert source["render_dpi"] == 300
    assert source["canonical_write_authorized"] is False

    raster = workbench.ensure_runtime_raster()
    assert raster.is_file()
    assert raster.name == "TAV05S_OAR_300dpi.jpg"
    assert _sha256(raster) == workbench.REGISTERED_RENDER_SHA256
    pix = fitz.Pixmap(str(raster))
    assert pix.width == workbench.REGISTERED_RENDER_WIDTH_PX == 7016, pix.width
    assert pix.height == workbench.REGISTERED_RENDER_HEIGHT_PX == 12530, pix.height
    _assert_prebuilt_runtime_boundary(raster)

    router = workbench.build_router()
    route_paths = {route.path for route in router.routes}
    assert EXPECTED_ROUTES.issubset(route_paths)
    assert LEGACY_IMAGE_ROUTE not in route_paths

    isolated = FastAPI()
    isolated.include_router(router)
    client = TestClient(isolated)
    page = client.get("/workbench/oar/g4-regions")
    assert page.status_code == 200
    assert "Localizzazione documentale — Pilastri G4" in page.text
    assert "/workbench/oar/g4-regions/source.jpg" in page.text
    assert LEGACY_IMAGE_ROUTE not in page.text
    assert page.headers["x-cew-oar-human-confirmation"] == "false"
    assert page.headers["x-cew-canonical-write"] == "false"

    image = client.get("/workbench/oar/g4-regions/source.jpg")
    assert image.status_code == 200
    assert image.headers["content-type"].startswith("image/jpeg")
    assert image.headers["x-cew-derived-authority"] == "DERIVED_REVIEW_AID_ONLY"
    assert image.headers["x-cew-derived-asset-id"] == workbench.REGISTERED_DERIVED_ASSET_ID
    assert image.headers["x-cew-render-sha256"] == workbench.REGISTERED_RENDER_SHA256
    assert image.headers["x-cew-source-sha256"] == workbench.EXPECTED_SOURCE_SHA256
    assert hashlib.sha256(image.content).hexdigest() == workbench.REGISTERED_RENDER_SHA256

    original_backend_status = audit_store.backend_status
    original_store = workbench.RUNTIME_STORE
    original_base_store = workbench._base.RUNTIME_STORE
    try:
        audit_store.backend_status = lambda: "FILESYSTEM_APPEND_ONLY"
        with tempfile.TemporaryDirectory(prefix="cew-oar-g4-runtime-") as tmp:
            isolated_store = Path(tmp)
            workbench.RUNTIME_STORE = isolated_store
            workbench._base.RUNTIME_STORE = isolated_store
            status = client.get("/api/workbench/oar/g4-regions/status")
            assert status.status_code == 200
            state = status.json()
            assert state["summary"]["UNBOUND"] == 34
            assert state["summary"]["GEOMETRY_CONFIRMED"] == 0
            assert state["runtime_raster"]["derived_asset_id"] == workbench.REGISTERED_DERIVED_ASSET_ID
            assert state["runtime_raster"]["render_sha256"] == workbench.REGISTERED_RENDER_SHA256
            assert state["runtime_raster"]["shown_to_operator"] is True
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
            frozen_body = frozen.json()
            assert frozen_body["state"] == "OAR_REGION_GEOMETRY_ALREADY_CONFIRMED"
            assert frozen_body["reason_code"] == "OAR_REGION_GEOMETRY_ALREADY_CONFIRMED"
            assert "reason" not in frozen_body
    finally:
        audit_store.backend_status = original_backend_status
        workbench.RUNTIME_STORE = original_store
        workbench._base.RUNTIME_STORE = original_base_store

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
    print("source_resolution=remote_immutable_archive_sha256_verified")
    print(f"display_asset={workbench.REGISTERED_DERIVED_ASSET_ID} raster=7016x12530 dpi=300 sha256_verified=true")
    print("render_runtime_prebuilt_required=true first_request_rasterization=false missing_prebuilt_fail_closed=true")
    print("proposal_persisted=true confirmation_persisted=true post_confirmation_mutation_rejected=true safe_reason_code=true")
    print("global_auth_guard=true canonical_write_authorized=false oar_human_confirmation=false")


if __name__ == "__main__":
    main()
