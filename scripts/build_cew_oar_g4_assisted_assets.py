#!/usr/bin/env python3
"""Build self-hosted Deep Zoom, viewer assets and raster snap candidates for G4.

Everything produced here is a derived interaction aid. The immutable PDF and the
registered 300-DPI OAR raster remain the provenance anchors named by receipts.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv

import cew_oar_g4_source_resolver as source

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "cew_oar_g4_assisted"
DZI_BASE = OUT / "deepzoom" / "TAV05S_OAR_300dpi"
VENDOR = OUT / "vendor"
SNAP_JSON = OUT / "snap_candidates.json"
MANIFEST = OUT / "manifest.json"
SNAP_WORKER = ROOT / "scripts" / "cew_oar_g4_snap_worker.py"
OPENCV_PIN = "opencv-python-headless==4.12.0.88"
OSD_SPEC = "openseadragon@6.1.0"
ANNOTORIOUS_SPEC = "@annotorious/openseadragon@3.8.10"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("GITHUB_SHA")
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ).strip()


def _tool_version(command: list[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()


def _npm_pack(spec: str, target: Path) -> Path:
    result = subprocess.check_output(
        ["npm", "pack", "--silent", "--pack-destination", str(target), spec],
        cwd=ROOT,
        text=True,
    ).strip().splitlines()
    if not result:
        raise AssertionError(f"OAR_ASSISTED_NPM_PACK_EMPTY:{spec}")
    archive = target / result[-1].strip()
    if not archive.is_file():
        raise AssertionError(f"OAR_ASSISTED_NPM_PACK_MISSING:{spec}:{archive.name}")
    return archive


def _extract_package(archive: Path, target: Path) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as handle:
        handle.extractall(target, filter="data")
    package = target / "package"
    if not package.is_dir():
        raise AssertionError(f"OAR_ASSISTED_NPM_PACKAGE_DIR_MISSING:{archive.name}")
    return package


def _materialize_vendor() -> dict:
    if shutil.which("npm") is None:
        raise AssertionError("OAR_ASSISTED_NPM_REQUIRED")
    VENDOR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cew-oar-ui-npm-") as tmp:
        tmp_root = Path(tmp)
        osd_archive = _npm_pack(OSD_SPEC, tmp_root)
        ann_archive = _npm_pack(ANNOTORIOUS_SPEC, tmp_root)
        osd_pkg = _extract_package(osd_archive, tmp_root / "osd")
        ann_pkg = _extract_package(ann_archive, tmp_root / "anno")

        osd_meta = json.loads((osd_pkg / "package.json").read_text(encoding="utf-8"))
        ann_meta = json.loads((ann_pkg / "package.json").read_text(encoding="utf-8"))
        if osd_meta.get("version") != "6.1.0" or ann_meta.get("version") != "3.8.10":
            raise AssertionError("OAR_ASSISTED_VENDOR_VERSION_DRIFT")
        if osd_meta.get("license") != "BSD-3-Clause" or ann_meta.get("license") != "BSD-3-Clause":
            raise AssertionError("OAR_ASSISTED_VENDOR_LICENSE_DRIFT")

        mapping = {
            osd_pkg / "build/openseadragon/openseadragon.min.js": VENDOR / "openseadragon-6.1.0.min.js",
            ann_pkg / "dist/annotorious-openseadragon.js": VENDOR / "annotorious-openseadragon-3.8.10.js",
            ann_pkg / "dist/annotorious-openseadragon.css": VENDOR / "annotorious-openseadragon-3.8.10.css",
        }
        for source_path, dest in mapping.items():
            if not source_path.is_file():
                raise AssertionError(f"OAR_ASSISTED_VENDOR_FILE_MISSING:{source_path}")
            shutil.copy2(source_path, dest)

    return {
        "npm_version": _tool_version(["npm", "--version"]),
        "openseadragon": {
            "version": "6.1.0",
            "license": "BSD-3-Clause",
            "filename": "openseadragon-6.1.0.min.js",
            "sha256": _sha256(VENDOR / "openseadragon-6.1.0.min.js"),
        },
        "annotorious_openseadragon": {
            "version": "3.8.10",
            "license": "BSD-3-Clause",
            "js_filename": "annotorious-openseadragon-3.8.10.js",
            "js_sha256": _sha256(VENDOR / "annotorious-openseadragon-3.8.10.js"),
            "css_filename": "annotorious-openseadragon-3.8.10.css",
            "css_sha256": _sha256(VENDOR / "annotorious-openseadragon-3.8.10.css"),
        },
    }


def _build_deepzoom(raster: Path) -> dict:
    if shutil.which("vips") is None:
        raise AssertionError("OAR_ASSISTED_LIBVIPS_REQUIRED")
    DZI_BASE.parent.mkdir(parents=True, exist_ok=True)
    descriptor = DZI_BASE.with_suffix(".dzi")
    tile_root = DZI_BASE.parent / f"{DZI_BASE.name}_files"
    descriptor.unlink(missing_ok=True)
    if tile_root.exists():
        shutil.rmtree(tile_root)

    subprocess.run(
        [
            "vips", "dzsave", str(raster), str(DZI_BASE),
            "--layout", "dz",
            "--tile-size", "256",
            "--overlap", "1",
            "--suffix", ".jpg[Q=88,strip]",
        ],
        check=True,
        cwd=ROOT,
    )
    if not descriptor.is_file() or not tile_root.is_dir():
        raise AssertionError("OAR_ASSISTED_DZI_MATERIALIZATION_FAILED")
    descriptor_text = descriptor.read_text(encoding="utf-8")
    if 'Width="7016"' not in descriptor_text or 'Height="12530"' not in descriptor_text:
        raise AssertionError("OAR_ASSISTED_DZI_DIMENSION_DRIFT")
    if 'TileSize="256"' not in descriptor_text or 'Overlap="1"' not in descriptor_text:
        raise AssertionError("OAR_ASSISTED_DZI_TILE_CONTRACT_DRIFT")
    tiles = sorted(tile_root.rglob("*.jpg"))
    if not tiles:
        raise AssertionError("OAR_ASSISTED_DZI_TILES_MISSING")
    return {
        "vips_version": _tool_version(["vips", "--version"]),
        "descriptor": str(descriptor.relative_to(OUT)),
        "descriptor_sha256": _sha256(descriptor),
        "tile_root": str(tile_root.relative_to(OUT)),
        "tile_count": len(tiles),
        "tile_size": 256,
        "overlap": 1,
        "tile_format": "JPEG",
        "tile_quality": 88,
    }


def _venv_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _build_snap_candidates(raster: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cew-oar-g4-snap-env-") as temp:
        env = Path(temp)
        venv.EnvBuilder(with_pip=True, clear=True).create(env)
        python = _venv_python(env)
        subprocess.run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", OPENCV_PIN],
            check=True,
            cwd=ROOT,
        )
        subprocess.run([str(python), str(SNAP_WORKER), str(raster), str(SNAP_JSON)], check=True, cwd=ROOT)
    payload = json.loads(SNAP_JSON.read_text(encoding="utf-8"))
    if payload.get("candidate_count", 0) <= 0:
        raise AssertionError("OAR_ASSISTED_SNAP_CANDIDATES_EMPTY")
    if payload.get("source_dimensions_px") != [7016, 12530]:
        raise AssertionError("OAR_ASSISTED_SNAP_SOURCE_DIMENSION_DRIFT")
    if payload.get("authority", {}).get("canonical_write_authorized") is not False:
        raise AssertionError("OAR_ASSISTED_SNAP_AUTHORITY_DRIFT")
    return {
        "worker_dependency": OPENCV_PIN,
        "runtime_opencv_required": False,
        "candidate_count": payload["candidate_count"],
        "filename": SNAP_JSON.name,
        "sha256": _sha256(SNAP_JSON),
    }


def build() -> dict:
    raster = source.materialize_build_raster()
    source.verify_registered_raster(raster)
    if _sha256(raster) != source.REGISTERED_RENDER_SHA256:
        raise AssertionError("OAR_ASSISTED_REGISTERED_RASTER_SHA_DRIFT")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    # materialize_build_raster writes inside OUT's sibling tree; OUT reset does
    # not delete the governed raster itself.
    vendor = _materialize_vendor()
    deepzoom = _build_deepzoom(raster)
    snap = _build_snap_candidates(raster)
    manifest = {
        "schema": "CEW_OAR_G4_ASSISTED_ASSET_MANIFEST_v1",
        "build_revision": _revision(),
        "pilot_id": "OAR-PILOT-G4-COLUMNS",
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "derived_asset_id": source.REGISTERED_DERIVED_ASSET_ID,
        "derived_asset_sha256": source.REGISTERED_RENDER_SHA256,
        "derived_asset_dimensions_px": [source.REGISTERED_RENDER_WIDTH_PX, source.REGISTERED_RENDER_HEIGHT_PX],
        "vendor": vendor,
        "deepzoom": deepzoom,
        "snap": snap,
        "authority": {
            "deep_zoom_tiles_are_authority": False,
            "snap_candidates_are_authority": False,
            "oar_classification_confirmed": False,
            "f2_registry_written": False,
            "canonical_write_authorized": False,
            "structural_identity_authorized": False,
            "engineering_authority_effect": "NONE",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("CEW_OAR_G4_ASSISTED_ASSETS_PASS")
    print(f"deepzoom_tiles={deepzoom['tile_count']} snap_candidates={snap['candidate_count']}")
    print("vendor_delivery=SELF_HOSTED build_only_opencv=true canonical_write_authorized=false")
    return manifest


if __name__ == "__main__":
    build()
