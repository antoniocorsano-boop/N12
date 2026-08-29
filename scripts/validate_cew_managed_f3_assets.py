#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import fitz

import build_cew_managed_f3_assets as builder
import cew_managed_f3_assets as runtime_assets


def expect_value_error(fn, code: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if code not in str(exc):
            raise AssertionError(f"expected {code}, got {exc}") from exc
        return
    raise AssertionError(f"expected ValueError containing {code}")


def main() -> None:
    plan = builder.build_plan()
    assert plan["schema_version"] == "1.0"
    assert plan["asset_contract"] == "CEW_MANAGED_F3_ASSETS_v1"
    assert plan["render_dpi"] == 300
    assert plan["tile_size"] == 256
    assert plan["tile_overlap"] == 1
    assert plan["tile_format"] == "jpg"
    assert plan["jpeg_quality"] == 90
    assert plan["dzi_engine"] == "PYMUPDF_BOUNDED_DZI"
    assert plan["openseadragon_version"] == "5.0.1"
    assert plan["canonical_write_authorized"] is False
    assert {source["source_code"] for source in plan["sources"]} == {
        "TAV-05A",
        "TAV-06A",
        "TAV-05S",
        "TAV-06S",
    }
    assert len({source["archive_commit"] for source in plan["sources"]}) == 1
    assert all(len(source["sha256"]) == 64 for source in plan["sources"])
    assert all(len(source["git_blob_sha"]) == 40 for source in plan["sources"])
    assert all(source["dzi"].endswith(f"/{source['source_code']}.dzi") for source in plan["sources"])

    builder_text = (builder.ROOT / "scripts/build_cew_managed_f3_assets.py").read_text(encoding="utf-8")
    requirements_text = (builder.ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "render_cew_viewer_sources.py" in builder_text
    assert "import fitz" in builder_text
    assert "display_list.get_pixmap" in builder_text
    assert "fitz.Pixmap(" in builder_text
    assert "jpg_quality=JPEG_QUALITY" in builder_text
    assert "pyvips" not in builder_text.lower()
    assert "dzsave" not in builder_text.lower()
    assert '_require_tool("vips")' not in builder_text
    assert "pyvips" not in requirements_text.lower()
    assert "PyMuPDF==1.26.4" in requirements_text
    assert "build_cew_source_viewer.py" in builder_text
    assert "npm" in builder_text and "openseadragon@" in builder_text
    assert "shutil.rmtree(render_root / source[\"source_code\"]" in builder_text

    # Prove the bounded PyMuPDF DZI engine itself with a real multi-level pyramid.
    with tempfile.TemporaryDirectory(prefix="cew-pymupdf-dzi-") as probe_temp:
        probe_root = Path(probe_temp)
        probe_pdf = probe_root / "probe.pdf"
        probe_png = probe_root / "probe.png"
        viewer = probe_root / "viewer"
        (viewer / "tiles").mkdir(parents=True)

        document = fitz.open()
        page = document.new_page(width=144, height=288)
        page.draw_rect(fitz.Rect(10, 10, 134, 278), color=(0, 0, 0), width=1)
        page.insert_text((20, 40), "CEW DZI PROBE", fontsize=12)
        document.save(probe_pdf)
        document.close()

        document = fitz.open(probe_pdf)
        pix = document[0].get_pixmap(
            matrix=fitz.Matrix(2, 2),
            colorspace=fitz.csRGB,
            alpha=False,
        )
        pix.save(probe_png)
        document.close()

        builder._tile_one({"source_code": "PROBE"}, probe_pdf, probe_png, viewer)
        descriptor = viewer / "tiles/PROBE.dzi"
        tile_root = viewer / "tiles/PROBE_files"
        assert descriptor.is_file()
        descriptor_text = descriptor.read_text(encoding="utf-8")
        assert 'TileSize="256"' in descriptor_text
        assert 'Overlap="1"' in descriptor_text
        assert 'Format="jpg"' in descriptor_text
        assert 'Width="288"' in descriptor_text
        assert 'Height="576"' in descriptor_text
        assert tile_root.is_dir()
        levels = sorted(path for path in tile_root.iterdir() if path.is_dir())
        assert len(levels) >= 2
        assert any(path.suffix == ".jpg" for path in tile_root.rglob("*.jpg"))

    with tempfile.TemporaryDirectory(prefix="cew-f3-guard-test-") as temp_name:
        root = Path(temp_name) / ".cew_professional_workbench_assets"
        viewer = root / "source-viewer"
        (viewer / "vendor/openseadragon").mkdir(parents=True)
        (viewer / "tiles").mkdir(parents=True)
        for name in ("index.html", "app.js", "styles.css", "viewer_manifest.json"):
            (viewer / name).write_text("test", encoding="utf-8")
        (viewer / "vendor/openseadragon/openseadragon.min.js").write_text("test", encoding="utf-8")
        for code in sorted(runtime_assets.REQUIRED_SOURCES):
            (viewer / "tiles" / f"{code}.dzi").write_text("<Image/>", encoding="utf-8")
            (viewer / "tiles" / f"{code}_files").mkdir()
            (viewer / "tiles" / f"{code}_files/0").mkdir()
            (viewer / "tiles" / f"{code}_files/0/0_0.jpg").write_bytes(b"fake")

        manifest = {
            **plan,
            "build_revision": "TEST_REVISION",
            "file_count": 20,
            "total_bytes": 100,
            "asset_tree_sha256": "a" * 64,
            "managed_runtime_dynamic_pdf_rasterization": False,
            "build_state": "READY",
            "viewer_entrypoint": "source-viewer/index.html",
        }
        manifest_path = root / "managed_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        old_root, old_manifest = runtime_assets.ASSET_ROOT, runtime_assets.MANIFEST
        runtime_assets.ASSET_ROOT = root
        runtime_assets.MANIFEST = manifest_path
        try:
            validated = runtime_assets.validate_manifest(expected_revision="TEST_REVISION")
            assert validated["build_revision"] == "TEST_REVISION"
            status = runtime_assets.status(expected_revision="TEST_REVISION")
            assert status["state"] == "READY"
            assert status["source_count"] == 4
            assert status["canonical_write_authorized"] is False
            assert status["dynamic_pdf_rasterization"] is False

            expect_value_error(
                lambda: runtime_assets.validate_manifest(expected_revision="OTHER_REVISION"),
                "MANAGED_F3_RUNTIME_REVISION_MISMATCH",
            )

            missing = viewer / "tiles/TAV-06S.dzi"
            missing.unlink()
            expect_value_error(
                lambda: runtime_assets.validate_manifest(expected_revision="TEST_REVISION"),
                "MANAGED_F3_REQUIRED_ASSET_MISSING",
            )
        finally:
            runtime_assets.ASSET_ROOT = old_root
            runtime_assets.MANIFEST = old_manifest

    print("CEW_MANAGED_F3_ASSETS = PASS")
    print("SOURCE_COVERAGE = 4/4")
    print("SOURCE_IDENTITY = IMMUTABLE_COMMIT_PLUS_SHA256_PLUS_GIT_BLOB")
    print("RENDER_DPI = 300")
    print("DZI_TILE_SIZE = 256")
    print("DZI_OVERLAP = 1")
    print("DZI_JPEG_QUALITY = 90")
    print("DZI_ENGINE = PYMUPDF_BOUNDED_DZI")
    print("PYMUPDF_BOUNDED_DZI_CAPABILITY = PASS")
    print("OPENSEADRAGON = 5.0.1")
    print("STALE_ASSET_REVISION = REJECTED")
    print("DYNAMIC_RUNTIME_RASTERIZATION = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")


if __name__ == "__main__":
    main()
