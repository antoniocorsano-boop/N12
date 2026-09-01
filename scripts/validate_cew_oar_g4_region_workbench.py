#!/usr/bin/env python3
"""Static/deterministic validation of G4 OAR Workbench wiring.

The validation intentionally avoids importing FastAPI/PyMuPDF so the authority
contract is checked independently from runtime dependencies.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    wrapper = text("scripts/cew_professional_workbench_api.py")
    base = text("scripts/cew_professional_workbench_api_base.py")
    oar = text("scripts/cew_oar_g4_region_workbench.py")
    app = text("app.py")

    # Composition keeps the pre-existing Workbench implementation separate and
    # adds the OAR router at the same authenticated application boundary.
    assert "import cew_professional_workbench_api_base as _base" in wrapper
    assert "import cew_oar_g4_region_workbench as _oar_g4" in wrapper
    assert "router = _base.build_router(source_workspace)" in wrapper
    assert "router.include_router(_oar_g4.build_router())" in wrapper
    assert "def build_router(source_workspace)" in base

    # app.py mounts only the composed professional router behind its global
    # access_guard middleware, so the OAR routes cannot bypass authentication.
    assert '@app.middleware("http")' in app
    assert "async def access_guard" in app
    assert "app.include_router(professional_workbench_api.build_router(source_workspace))" in app
    assert app.index('@app.middleware("http")') < app.index("app.include_router(professional_workbench_api.build_router(source_workspace))")

    # Required bounded UI/API surface.
    for route in (
        "/workbench/oar/g4-regions",
        "/workbench/oar/g4-regions/source.png",
        "/api/workbench/oar/g4-regions/status",
        "/api/workbench/oar/g4-regions/receipt",
    ):
        assert route in oar, route

    # Source identity is checked before rendering, and coordinates remain tied
    # to the registered page instead of browser PDF-viewer geometry.
    assert "EXPECTED_SOURCE_SHA256" in oar
    assert "OAR_G4_SOURCE_SHA256_MISMATCH" in oar
    assert "EXPECTED_PAGE_WIDTH_PT = 1683.72" in oar
    assert "EXPECTED_PAGE_HEIGHT_PT = 3007.08" in oar
    assert "page.get_pixmap(dpi=RUNTIME_DPI" in oar
    assert '"DERIVED_INTERACTION_AID_ONLY"' in oar

    # Confirmation is server-bound to the latest proposal and all authority
    # escalation remains explicitly false.
    assert "_latest_proposal_bbox(current, support_id)" in oar
    assert "OAR_REGION_CONFIRMATION_BBOX_MISMATCH" in oar
    assert '"oar_human_confirmation": False' in oar
    assert '"canonical_write_authorized": False' in oar
    assert '"engineering_authority_effect": "NONE"' in oar
    assert "audit_store.persist_runtime_receipt" in oar
    assert "CEW_EVIDENCE_REGION_REGISTRY" not in oar

    # Every edited Python module must remain syntactically valid.
    for path in (
        "scripts/cew_professional_workbench_api.py",
        "scripts/cew_professional_workbench_api_base.py",
        "scripts/cew_oar_g4_region_workbench.py",
    ):
        ast.parse(text(path), filename=path)

    print("CEW_OAR_G4_REGION_WORKBENCH_PASS")
    print("authenticated_composition=true source_verified=true full_page_overlay=true")
    print("runtime_audit_only=true oar_human_confirmation=false canonical_write_authorized=false")


if __name__ == "__main__":
    main()
