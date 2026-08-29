#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# The smoke is local-only. A managed runtime must never use the test auth bypass.
os.environ.setdefault("CEW_AUTH_DISABLED_FOR_TEST", "1")
os.environ.setdefault("CEW_AUDIT_BACKEND_MODE", "LOCAL_TEST_ONLY")
os.environ.setdefault("RENDER_GIT_COMMIT", "0123456789abcdef0123456789abcdef01234567")
os.environ.setdefault("RENDER_EXTERNAL_URL", "https://cew-hva.example.invalid")

import app


def _walk_routes(routes: Iterable[object], seen: set[int] | None = None):
    """Traverse FastAPI/Starlette route containers without assuming a flat app.routes.

    FastAPI >=0.137 keeps included APIRouters behind _IncludedRouter wrappers.
    Depending on the Starlette/FastAPI version, child routes may live in .routes,
    .original_router.routes, or a mounted .app.routes. The validator deliberately
    understands all three shapes instead of forcing the application to flatten its
    router tree.
    """
    if seen is None:
        seen = set()
    for route in routes:
        identity = id(route)
        if identity in seen:
            continue
        seen.add(identity)
        yield route

        nested = getattr(route, "routes", None)
        if nested:
            yield from _walk_routes(nested, seen)

        original_router = getattr(route, "original_router", None)
        original_routes = getattr(original_router, "routes", None)
        if original_routes:
            yield from _walk_routes(original_routes, seen)

        mounted_app = getattr(route, "app", None)
        mounted_routes = getattr(mounted_app, "routes", None)
        if mounted_routes:
            yield from _walk_routes(mounted_routes, seen)


def _route_map() -> dict[str, object]:
    result: dict[str, object] = {}
    for route in _walk_routes(app.app.routes):
        path = getattr(route, "path", None)
        if isinstance(path, str):
            result[path] = route
    return result


def _body(response) -> dict:
    return json.loads(response.body)


def main() -> int:
    routes = _route_map()
    required = {
        "/acceptance/b1",
        "/evidence/dual-workspace",
        "/api/workbench/assets/status",
        "/api/workbench/document-geometry/status",
        "/workbench/assets/{asset_path:path}",
        "/api/workbench/scene",
        "/api/workbench/view/resolve",
        "/api/workbench/view/snapshot",
        "/api/workbench/working-edit/preview",
        "/api/workbench/reading-issue/preview",
    }
    missing = sorted(required - set(routes))
    if missing:
        raise AssertionError(f"WORKBENCH_ROUTE_TREE_MISSING:{missing}")

    response = app.b1_acceptance_lab()
    assert response.status_code == 200
    text = response.body.decode("utf-8")
    assert "Verifica del percorso documentale" in text
    assert "Svolgi il lavoro come faresti normalmente" in text
    assert "Ingrandisci il dettaglio e spostati" in text
    assert "AREA REVISIONE HVA" in text
    assert os.environ["RENDER_GIT_COMMIT"] in text
    assert "stored.runtime_revision!==RUNTIME_REVISION" in text
    assert "WRONG_SOURCE_OR_VERSION" in text
    assert "zoomed&&panned&&macro&&finalMicro" in text

    evidence = app.evidence_workspace("ERW-N12-001")
    evidence_text = evidence.body.decode("utf-8")
    assert 'id="evidenceViewport"' in evidence_text
    assert "＋ Ingrandisci" in evidence_text
    assert "Reset vista" in evidence_text

    dual = app.evidence_dual_workspace("ERW-N12-001")
    dual_text = dual.body.decode("utf-8")
    assert dual.status_code == 200
    assert "SOURCE PANEL" in dual_text
    assert "TECHNICAL REPRESENTATION PANEL" in dual_text
    assert "length=1040; quantity=UNREADABLE; diameter=UNREADABLE" in dual_text
    assert 'Geometria strutturale: <span class="open-state">OPEN/ND</span>' in dual_text
    assert "canonical_write:false" in dual_text

    scene_response = routes["/api/workbench/scene"].endpoint(task="ERW-N12-004")
    assert scene_response.status_code == 200
    scene = _body(scene_response)
    assert scene["authority"]["canonical_write_authorized"] is False
    assert scene["authority"]["engineering_authority_effect"] == "NONE"
    assert scene["registrations"][0]["state"] == "UNAVAILABLE"
    assert scene["capabilities"]["overlay_available"] is False
    assert scene["capabilities"]["managed_runtime_dynamic_pdf_rasterization"] is False
    assert scene["capabilities"]["runtime_docling_required"] is False
    assert scene["capabilities"]["managed_f3_assets"] == "UNAVAILABLE"
    assert scene["capabilities"]["source_multiresolution_assets"] == "UNAVAILABLE_FAIL_CLOSED"
    assert scene["capabilities"]["managed_document_geometry"] == "UNAVAILABLE"
    assert scene["source"]["managed_f3_dzi_url"] is None
    structural = [o for o in scene["objects"] if o["object_family"] == "GovernedStructuralObjectProjection"]
    assert len(structural) == 1
    assert structural[0]["governed_source_member_id"] == "G5-B017"
    assert structural[0]["binding_state"] == "UNBOUND"
    assert structural[0]["selection_authorized"] is False

    assets = _body(routes["/api/workbench/assets/status"].endpoint())
    assert assets["state"] == "UNAVAILABLE"
    assert assets["canonical_write_authorized"] is False
    assert assets["dynamic_pdf_rasterization"] is False

    geometry = _body(routes["/api/workbench/document-geometry/status"].endpoint())
    assert geometry["state"] == "UNAVAILABLE"
    assert geometry["runtime_docling_required"] is False
    assert geometry["canonical_write_authorized"] is False

    health = app.healthz()
    assert health["b1_acceptance_lab"] == "B18_IMPLEMENTED_CANDIDATE_HVA_PENDING"
    assert health["b18_dual_workspace"] == "IMPLEMENTED_CANDIDATE_HVA_PENDING"
    assert health["professional_workbench_kernel"] == "FOUNDATION_IMPLEMENTED_INTEGRATION_PENDING"
    assert health["professional_workbench_readiness"] == "REWORK_REQUIRED"
    assert health["professional_workbench_hva_authorized"] is False
    assert health["canonical_write_authorized"] is False

    print("CEW_PROFESSIONAL_WORKBENCH_RUNTIME_SMOKE = PASS")
    print("FASTAPI_INCLUDED_ROUTER_TREE = PASS")
    print("WORKBENCH_ROUTES = 8/8")
    print("ERW_N12_004_UNBOUND = PRESERVED")
    print("MANAGED_F3_WITHOUT_ASSET = FAIL_CLOSED")
    print("DOCUMENT_GEOMETRY_WITHOUT_ASSET = FAIL_CLOSED")
    print("RUNTIME_DOCLING_REQUIRED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
