#!/usr/bin/env python3
"""Static/deterministic validation of G4 OAR Workbench wiring."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
import tempfile
import types

import cew_oar_g4_source_resolver as resolver_runtime

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _validate_single_source_fetch() -> None:
    """Prove registered-asset verification+rendering consumes one immutable fetch."""
    calls = {"fetch": 0, "open": 0, "save": 0, "close": 0, "verify_raster": 0}

    class Rect:
        width = resolver_runtime.EXPECTED_PAGE_WIDTH_PT
        height = resolver_runtime.EXPECTED_PAGE_HEIGHT_PT

    class Pixmap:
        width = resolver_runtime.REGISTERED_RENDER_WIDTH_PX
        height = resolver_runtime.REGISTERED_RENDER_HEIGHT_PX

        def save(self, path, *, jpg_quality):
            calls["save"] += 1
            assert jpg_quality == resolver_runtime.JPEG_QUALITY
            Path(path).write_bytes(b"JPEG")

    class Page:
        rect = Rect()

        def get_pixmap(self, *, dpi, alpha):
            assert dpi == resolver_runtime.RUNTIME_DPI == 300
            assert alpha is False
            return Pixmap()

    class Document:
        page_count = 1

        def __getitem__(self, index):
            assert index == 0
            return Page()

        def close(self):
            calls["close"] += 1

    fake_fitz = types.ModuleType("fitz")

    def fake_open(*, stream, filetype):
        calls["open"] += 1
        assert stream == b"verified-pdf"
        assert filetype == "pdf"
        return Document()

    fake_fitz.open = fake_open

    original_fetch = resolver_runtime.fetch_source
    original_raster = resolver_runtime.RUNTIME_RASTER
    original_verify_raster = resolver_runtime._verify_registered_raster
    original_fitz = sys.modules.get("fitz")
    try:
        def fake_fetch():
            calls["fetch"] += 1
            return b"verified-pdf", {"remote_path": resolver_runtime.EXPECTED_REMOTE_PATH}

        def fake_verify_raster(path):
            calls["verify_raster"] += 1
            assert Path(path).is_file()

        resolver_runtime.fetch_source = fake_fetch
        resolver_runtime._verify_registered_raster = fake_verify_raster
        sys.modules["fitz"] = fake_fitz
        with tempfile.TemporaryDirectory() as td:
            resolver_runtime.RUNTIME_RASTER = Path(td) / "TAV05S_300dpi.jpg"
            result = resolver_runtime.ensure_runtime_raster()
            assert result == resolver_runtime.RUNTIME_RASTER
            assert result.read_bytes() == b"JPEG"
            assert calls == {"fetch": 1, "open": 1, "save": 1, "close": 1, "verify_raster": 1}, calls

            # Cache reuse still verifies the immutable source and the exact
            # registered raster, but performs neither a second fetch nor render
            # inside the same request.
            result = resolver_runtime.ensure_runtime_raster()
            assert result == resolver_runtime.RUNTIME_RASTER
            assert calls == {"fetch": 2, "open": 2, "save": 1, "close": 2, "verify_raster": 2}, calls
    finally:
        resolver_runtime.fetch_source = original_fetch
        resolver_runtime.RUNTIME_RASTER = original_raster
        resolver_runtime._verify_registered_raster = original_verify_raster
        if original_fitz is None:
            sys.modules.pop("fitz", None)
        else:
            sys.modules["fitz"] = original_fitz


def main() -> None:
    wrapper = text("scripts/cew_professional_workbench_api.py")
    base = text("scripts/cew_professional_workbench_api_base.py")
    oar_wrapper = text("scripts/cew_oar_g4_region_workbench.py")
    oar_base = text("scripts/cew_oar_g4_region_workbench_base.py")
    resolver = text("scripts/cew_oar_g4_source_resolver.py")
    source_workspace = text("scripts/cew_source_evidence_workspace.py")
    app = text("app.py")
    binding_contract = json.loads(text("automation/CEW_OAR_G4_COLUMN_REGION_BINDING_v1.json"))

    assert "import cew_professional_workbench_api_base as _base" in wrapper
    assert "import cew_oar_g4_region_workbench as _oar_g4" in wrapper
    assert "router = _base.build_router(source_workspace)" in wrapper
    assert "router.include_router(_oar_g4.build_router())" in wrapper
    assert "def build_router(source_workspace)" in base
    assert '@app.middleware("http")' in app
    assert "async def access_guard" in app
    assert "app.include_router(professional_workbench_api.build_router(source_workspace))" in app
    assert app.index('@app.middleware("http")') < app.index("app.include_router(professional_workbench_api.build_router(source_workspace))")

    assert "import cew_oar_g4_region_workbench_base as _base" in oar_wrapper
    assert "import cew_oar_g4_source_resolver as _resolver" in oar_wrapper
    assert "_base.verify_source = verify_source" in oar_wrapper
    assert "_base.ensure_runtime_raster = ensure_runtime_raster" in oar_wrapper
    assert "draftDirty=true;confirmBtn.disabled=true" in oar_wrapper
    assert "action==='PROPOSE_GEOMETRY'||action==='CONFIRM_GEOMETRY'" in oar_wrapper
    assert "Registra prima la geometria modificata." in oar_wrapper
    assert "_base.build_page = build_page" in oar_wrapper
    assert '"/workbench/oar/g4-regions/source.png"' in oar_wrapper
    assert '"/workbench/oar/g4-regions/source.jpg"' in oar_wrapper
    assert 'media_type="image/jpeg"' in oar_wrapper
    assert '"X-CEW-Derived-Asset-ID": REGISTERED_DERIVED_ASSET_ID' in oar_wrapper
    assert '"X-CEW-Render-SHA256": REGISTERED_RENDER_SHA256' in oar_wrapper

    for route in (
        "/workbench/oar/g4-regions",
        "/api/workbench/oar/g4-regions/status",
        "/api/workbench/oar/g4-regions/receipt",
    ):
        assert route in oar_base, route

    assert 'SOURCE_ID = "TAV-05S"' in resolver
    assert "source_workspace.fetch_verified_source(SOURCE_ID)" in resolver
    assert 'EXPECTED_GIT_BLOB_SHA = "ec32cd621877e9037cb26ebc083164140a8e3e68"' in resolver
    assert 'EXPECTED_SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"' in resolver
    assert 'EXPECTED_REMOTE_PATH = "archive/documentazione_originaria/tavola 5.pdf"' in resolver
    assert 'REGISTERED_DERIVED_ASSET_ID = "CEW-N12-ASSET-TAV05S-P001-300DPI"' in resolver
    assert 'REGISTERED_RENDER_SHA256 = "32dfa5976b3d6a6482f73159da1778de6483e5d90c671ae771793374781f58b7"' in resolver
    assert "REGISTERED_RENDER_WIDTH_PX = 7016" in resolver
    assert "REGISTERED_RENDER_HEIGHT_PX = 12530" in resolver
    assert "RUNTIME_DPI = 300" in resolver
    assert "JPEG_QUALITY = 92" in resolver
    assert "pixmap.save(RUNTIME_RASTER, jpg_quality=JPEG_QUALITY)" in resolver
    assert "_verify_registered_raster(RUNTIME_RASTER)" in resolver
    assert "verify_source()" not in resolver[resolver.index("def ensure_runtime_raster"):]
    assert "fitz.open(stream=payload, filetype=\"pdf\")" in resolver
    assert 'ARCHIVE_COMMIT = "78c20a52db4f391ce0d13b9705b9f04737e218c9"' in source_workspace
    assert "verify_source_bytes(source, payload)" in source_workspace

    document = binding_contract["document"]
    assert document["derived_asset_id"] == resolver_runtime.REGISTERED_DERIVED_ASSET_ID
    assert document["render_width_px"] == resolver_runtime.REGISTERED_RENDER_WIDTH_PX
    assert document["render_height_px"] == resolver_runtime.REGISTERED_RENDER_HEIGHT_PX
    assert document["render_sha256"] == resolver_runtime.REGISTERED_RENDER_SHA256
    _validate_single_source_fetch()

    assert "_latest_proposal_bbox(current, support_id)" in oar_base
    assert "OAR_REGION_CONFIRMATION_BBOX_MISMATCH" in oar_base
    assert '"oar_human_confirmation": False' in oar_base
    assert '"canonical_write_authorized": False' in oar_base
    assert '"engineering_authority_effect": "NONE"' in oar_base
    assert "audit_store.persist_runtime_receipt" in oar_base
    assert "CEW_EVIDENCE_REGION_REGISTRY" not in oar_base

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
    print("display_asset=CEW-N12-ASSET-TAV05S-P001-300DPI dpi=300 sha256_bound=true")
    print("immutable_source_fetch_per_raster_request=1 registered_asset_verified_before_serve=true")
    print("edited_bbox_requires_reproposal=true confirmation_bbox_server_checked=true")
    print("runtime_audit_only=true oar_human_confirmation=false canonical_write_authorized=false")


if __name__ == "__main__":
    main()
