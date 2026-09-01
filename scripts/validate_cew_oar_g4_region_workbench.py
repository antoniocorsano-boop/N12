#!/usr/bin/env python3
"""Static/deterministic validation of G4 OAR Workbench wiring."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> None:
    wrapper = text("scripts/cew_professional_workbench_api.py")
    base = text("scripts/cew_professional_workbench_api_base.py")
    oar_wrapper = text("scripts/cew_oar_g4_region_workbench.py")
    oar_base = text("scripts/cew_oar_g4_region_workbench_base.py")
    resolver = text("scripts/cew_oar_g4_source_resolver.py")
    source_workspace = text("scripts/cew_source_evidence_workspace.py")
    app = text("app.py")

    # The professional router remains behind the global authentication guard.
    assert "import cew_professional_workbench_api_base as _base" in wrapper
    assert "import cew_oar_g4_region_workbench as _oar_g4" in wrapper
    assert "router = _base.build_router(source_workspace)" in wrapper
    assert "router.include_router(_oar_g4.build_router())" in wrapper
    assert "def build_router(source_workspace)" in base
    assert '@app.middleware("http")' in app
    assert "async def access_guard" in app
    assert "app.include_router(professional_workbench_api.build_router(source_workspace))" in app
    assert app.index('@app.middleware("http")') < app.index("app.include_router(professional_workbench_api.build_router(source_workspace))")

    # OAR UI/API implementation is preserved in a base module; the public OAR
    # module replaces only source resolution with the governed resolver.
    assert "import cew_oar_g4_region_workbench_base as _base" in oar_wrapper
    assert "import cew_oar_g4_source_resolver as _resolver" in oar_wrapper
    assert "_base.verify_source = verify_source" in oar_wrapper
    assert "_base.ensure_runtime_raster = ensure_runtime_raster" in oar_wrapper
    for route in (
        "/workbench/oar/g4-regions",
        "/workbench/oar/g4-regions/source.png",
        "/api/workbench/oar/g4-regions/status",
        "/api/workbench/oar/g4-regions/receipt",
    ):
        assert route in oar_base, route

    # Source resolution must reuse CEW's immutable archive reader rather than
    # assuming that the source PDF exists in the deployment checkout.
    assert 'SOURCE_ID = "TAV-05S"' in resolver
    assert "source_workspace.fetch_verified_source(SOURCE_ID)" in resolver
    assert 'EXPECTED_GIT_BLOB_SHA = "ec32cd621877e9037cb26ebc083164140a8e3e68"' in resolver
    assert 'EXPECTED_SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"' in resolver
    assert 'EXPECTED_REMOTE_PATH = "archive/documentazione_originaria/tavola 5.pdf"' in resolver
    assert "EXPECTED_PAGE_WIDTH_PT = 1683.72" in resolver
    assert "EXPECTED_PAGE_HEIGHT_PT = 3007.08" in resolver
    assert "fitz.open(stream=payload, filetype=\"pdf\")" in resolver
    assert "page.get_pixmap(dpi=RUNTIME_DPI" in resolver
    assert 'ARCHIVE_COMMIT = "78c20a52db4f391ce0d13b9705b9f04737e218c9"' in source_workspace
    assert "verify_source_bytes(source, payload)" in source_workspace

    # Confirmation remains server-bound to the current proposal; no authority
    # escalation or canonical EvidenceRegion write is introduced.
    assert "_latest_proposal_bbox(current, support_id)" in oar_base
    assert "OAR_REGION_CONFIRMATION_BBOX_MISMATCH" in oar_base
    assert '"oar_human_confirmation": False' in oar_base
    assert '"canonical_write_authorized": False' in oar_base
    assert '"engineering_authority_effect": "NONE"' in oar_base
    assert "audit_store.persist_runtime_receipt" in oar_base
    assert "CEW_EVIDENCE_REGION_REGISTRY" not in oar_base
    assert '"DERIVED_INTERACTION_AID_ONLY"' in oar_base

    for path in (
        "scripts/cew_professional_workbench_api.py",
        "scripts/cew_professional_workbench_api_base.py",
        "scripts/cew_oar_g4_region_workbench.py",
        "scripts/cew_oar_g4_region_workbench_base.py",
        "scripts/cew_oar_g4_source_resolver.py",
    ):
        ast.parse(text(path), filename=path)

    print("CEW_OAR_G4_REGION_WORKBENCH_PASS")
    print("authenticated_composition=true governed_remote_source=true full_page_overlay=true")
    print("runtime_audit_only=true oar_human_confirmation=false canonical_write_authorized=false")


if __name__ == "__main__":
    main()
