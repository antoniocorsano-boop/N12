#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

import fitz

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/canonical/CEW_SOURCE_IDENTITY_REGISTRY_v1.csv"
ASSET_ROOT = ROOT / ".cew_professional_workbench_assets"
MANIFEST = ASSET_ROOT / "managed_manifest.json"
REQUIRED_SOURCES = ("TAV-05A", "TAV-06A", "TAV-05S", "TAV-06S")
LOCATOR_RE = re.compile(r"^git\+github://antoniocorsano-boop/N12@([0-9a-f]{40})/(.+)$")
OSD_VERSION = "5.0.1"
DPI = 300
TILE_SIZE = 256
OVERLAP = 1
JPEG_QUALITY = 90
DZI_ENGINE = "PYMUPDF_BOUNDED_DZI"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_revision() -> str:
    env = (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
    )
    if env:
        return env.strip()
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def build_plan() -> dict[str, Any]:
    source_rows = rows(REGISTRY)
    plan_sources: list[dict[str, str]] = []
    archive_commits: set[str] = set()
    for code in REQUIRED_SOURCES:
        matches = [
            row for row in source_rows
            if row.get("logical_source_code", "").strip() == code
            and row.get("readiness_state", "").strip() == "READY"
            and row.get("authority", "").strip() == "PRIMARY"
        ]
        if len(matches) != 1:
            raise AssertionError(f"expected exactly one READY PRIMARY source for {code}, got {len(matches)}")
        row = matches[0]
        locator = row["storage_locator"].strip()
        match = LOCATOR_RE.match(locator)
        if not match:
            raise AssertionError(f"unsupported immutable source locator for {code}: {locator}")
        commit, repo_path = match.groups()
        archive_commits.add(commit)
        plan_sources.append(
            {
                "source_code": code,
                "source_id": row["source_id"].strip(),
                "source_version_id": row["source_version_id"].strip(),
                "sha256": row["sha256"].strip(),
                "archive_commit": commit,
                "archive_path": repo_path,
                "git_blob_sha": row["git_blob_sha"].strip(),
                "document_role": row["document_role"].strip(),
                "dzi": f"source-viewer/tiles/{code}.dzi",
            }
        )
    if len(archive_commits) != 1:
        raise AssertionError(f"managed F3 sources must share one frozen archive commit: {sorted(archive_commits)}")
    return {
        "schema_version": "1.0",
        "asset_contract": "CEW_MANAGED_F3_ASSETS_v1",
        "build_revision": build_revision(),
        "archive_commit": next(iter(archive_commits)),
        "render_dpi": DPI,
        "tile_size": TILE_SIZE,
        "tile_overlap": OVERLAP,
        "tile_format": "jpg",
        "jpeg_quality": JPEG_QUALITY,
        "dzi_engine": DZI_ENGINE,
        "openseadragon_version": OSD_VERSION,
        "sources": plan_sources,
        "authority": "READING_AID_ONLY",
        "canonical_write_authorized": False,
    }


def _run(command: list[str], *, cwd: Path = ROOT, stdout=None) -> None:
    subprocess.run(command, cwd=cwd, check=True, stdout=stdout)


def _ensure_archive_commit(commit: str) -> None:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return
    _run(["git", "fetch", "--no-tags", "--depth=1", "origin", commit])
    _run(["git", "cat-file", "-e", f"{commit}^{{commit}}"])


def _materialize_source(source: dict[str, str], target: Path) -> None:
    spec = f"{source['archive_commit']}:{source['archive_path']}"
    with target.open("wb") as handle:
        _run(["git", "show", spec], stdout=handle)
    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    if actual != source["sha256"]:
        raise AssertionError(
            f"immutable source digest mismatch for {source['source_code']}: expected={source['sha256']} actual={actual}"
        )
    blob = subprocess.check_output(["git", "rev-parse", spec], cwd=ROOT, text=True).strip()
    if source["git_blob_sha"] and blob != source["git_blob_sha"]:
        raise AssertionError(
            f"immutable Git blob mismatch for {source['source_code']}: expected={source['git_blob_sha']} actual={blob}"
        )


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise AssertionError(f"managed F3 build tool missing: {name}")
    return path


def _render_one(source: dict[str, str], pdf: Path, render_root: Path) -> Path:
    _run(
        [
            sys.executable,
            str(ROOT / "scripts/render_cew_viewer_sources.py"),
            "--dpi",
            str(DPI),
            "--out-dir",
            str(render_root),
            "--source",
            source["source_code"],
            str(pdf),
            source["sha256"],
        ]
    )
    png = render_root / source["source_code"] / f"{source['source_code']}_p001_{DPI}dpi.png"
    if not png.exists():
        raise AssertionError(f"managed F3 render output missing: {png}")
    return png


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise AssertionError(f"managed F3 PNG header invalid: {path}")
    width, height = struct.unpack(">II", header[16:24])
    if width <= 0 or height <= 0:
        raise AssertionError(f"managed F3 PNG dimensions invalid: {width}x{height}")
    return width, height


def _write_dzi_descriptor(path: Path, width: int, height: int) -> None:
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<Image TileSize="{TILE_SIZE}" Overlap="{OVERLAP}" Format="jpg" '
        'xmlns="http://schemas.microsoft.com/deepzoom/2008">\n'
        f'  <Size Width="{width}" Height="{height}"/>\n'
        '</Image>\n',
        encoding="utf-8",
    )


def _tile_one(source: dict[str, str], pdf: Path, png: Path, viewer_root: Path) -> None:
    full_width, full_height = _png_dimensions(png)
    max_level = int(math.ceil(math.log2(max(full_width, full_height)))) if max(full_width, full_height) > 1 else 0
    base = viewer_root / "tiles" / source["source_code"]
    files_root = base.parent / f"{base.name}_files"
    files_root.mkdir(parents=True, exist_ok=True)

    document = fitz.open(pdf)
    try:
        if document.page_count < 1:
            raise AssertionError(f"managed F3 source has no page: {source['source_code']}")
        page = document[0]
        page_rect = page.rect
        display_list = page.get_displaylist()

        for level in range(max_level + 1):
            divisor = 2 ** (max_level - level)
            level_width = max(1, int(math.ceil(full_width / divisor)))
            level_height = max(1, int(math.ceil(full_height / divisor)))
            sx = level_width / page_rect.width
            sy = level_height / page_rect.height
            columns = int(math.ceil(level_width / TILE_SIZE))
            rows_count = int(math.ceil(level_height / TILE_SIZE))
            level_dir = files_root / str(level)
            level_dir.mkdir(parents=True, exist_ok=True)

            for row_index in range(rows_count):
                y0 = row_index * TILE_SIZE
                y1 = min(level_height, (row_index + 1) * TILE_SIZE)
                stripe_y0 = max(0, y0 - (OVERLAP if row_index > 0 else 0))
                stripe_y1 = min(
                    level_height,
                    y1 + (OVERLAP if row_index < rows_count - 1 else 0),
                )
                clip = fitz.Rect(
                    page_rect.x0,
                    page_rect.y0 + stripe_y0 / sy,
                    page_rect.x1,
                    page_rect.y0 + stripe_y1 / sy,
                )
                stripe = display_list.get_pixmap(
                    matrix=fitz.Matrix(sx, sy),
                    colorspace=fitz.csRGB,
                    alpha=False,
                    clip=clip,
                )
                expected_height = stripe_y1 - stripe_y0
                if stripe.width != level_width or stripe.height != expected_height:
                    raise AssertionError(
                        "managed F3 bounded stripe mismatch "
                        f"source={source['source_code']} level={level} "
                        f"expected={level_width}x{expected_height} actual={stripe.width}x{stripe.height}"
                    )
                stripe.set_origin(0, 0)

                for column_index in range(columns):
                    x0 = column_index * TILE_SIZE
                    x1 = min(level_width, (column_index + 1) * TILE_SIZE)
                    tile_x0 = max(0, x0 - (OVERLAP if column_index > 0 else 0))
                    tile_x1 = min(
                        level_width,
                        x1 + (OVERLAP if column_index < columns - 1 else 0),
                    )
                    tile = fitz.Pixmap(
                        stripe,
                        stripe.width,
                        stripe.height,
                        fitz.IRect(tile_x0, 0, tile_x1, stripe.height),
                    )
                    expected_width = tile_x1 - tile_x0
                    if tile.width != expected_width or tile.height != expected_height:
                        raise AssertionError(
                            "managed F3 tile mismatch "
                            f"source={source['source_code']} level={level} x={column_index} y={row_index} "
                            f"expected={expected_width}x{expected_height} actual={tile.width}x{tile.height}"
                        )
                    tile_path = level_dir / f"{column_index}_{row_index}.jpg"
                    tile.save(tile_path, jpg_quality=JPEG_QUALITY)

        _write_dzi_descriptor(base.with_suffix(".dzi"), full_width, full_height)
    finally:
        document.close()

    if not base.with_suffix(".dzi").exists() or not files_root.is_dir():
        raise AssertionError(f"managed F3 DZI missing for {source['source_code']}")
    print(
        f"CEW_MANAGED_F3_DZI_READY source={source['source_code']} "
        f"engine={DZI_ENGINE} size={full_width}x{full_height} levels={max_level + 1}"
    )


def _install_osd(viewer_root: Path, temp_root: Path) -> dict[str, str]:
    package_dir = temp_root / "npm"
    package_dir.mkdir(parents=True, exist_ok=True)
    packed = subprocess.check_output(
        ["npm", "pack", f"openseadragon@{OSD_VERSION}", "--silent"],
        cwd=package_dir,
        text=True,
    ).strip().splitlines()[-1]
    tgz = package_dir / packed
    package_sha = hashlib.sha256(tgz.read_bytes()).hexdigest()
    with tarfile.open(tgz, "r:gz") as archive:
        archive.extractall(package_dir, filter="data")
    source = package_dir / "package/build/openseadragon"
    target = viewer_root / "vendor/openseadragon"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "openseadragon.min.js", target / "openseadragon.min.js")
    shutil.copytree(source / "images", target / "images", dirs_exist_ok=True)
    return {"npm_package": packed, "npm_package_sha256": package_sha}


def _file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _inventory(root: Path) -> tuple[int, int, str]:
    entries: list[tuple[str, int, str]] = []
    total_bytes = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path == MANIFEST:
            continue
        rel = path.relative_to(ASSET_ROOT).as_posix()
        size = path.stat().st_size
        digest = _file_digest(path)
        total_bytes += size
        entries.append((rel, size, digest))
    root_hash = hashlib.sha256(
        "\n".join(f"{rel}\t{size}\t{digest}" for rel, size, digest in entries).encode("utf-8")
    ).hexdigest()
    return len(entries), total_bytes, root_hash


def _validate_built_viewer(plan: dict[str, Any], viewer_root: Path) -> None:
    manifest_path = viewer_root / "viewer_manifest.json"
    if not manifest_path.exists():
        raise AssertionError("F3 viewer manifest missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    declared = {entry["source_code"] for entry in manifest["entries"]}
    declared.update(entry["source_code"] for entry in manifest["context_sources"])
    expected = set(REQUIRED_SOURCES)
    if declared != expected:
        raise AssertionError(f"F3 viewer source set mismatch: expected={sorted(expected)} actual={sorted(declared)}")
    for source in plan["sources"]:
        dzi = viewer_root / "tiles" / f"{source['source_code']}.dzi"
        tiles = viewer_root / "tiles" / f"{source['source_code']}_files"
        if not dzi.is_file() or not tiles.is_dir():
            raise AssertionError(f"F3 viewer assets incomplete for {source['source_code']}")
    for required in (
        viewer_root / "index.html",
        viewer_root / "app.js",
        viewer_root / "styles.css",
        viewer_root / "vendor/openseadragon/openseadragon.min.js",
    ):
        if not required.is_file():
            raise AssertionError(f"F3 viewer runtime asset missing: {required}")


def build_assets() -> dict[str, Any]:
    _require_tool("git")
    _require_tool("npm")
    plan = build_plan()
    _ensure_archive_commit(plan["archive_commit"])

    if ASSET_ROOT.exists():
        shutil.rmtree(ASSET_ROOT)
    viewer_root = ASSET_ROOT / "source-viewer"
    viewer_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cew-managed-f3-") as temp_name:
        temp_root = Path(temp_name)
        pdf_root = temp_root / "pdf"
        render_root = temp_root / "render"
        pdf_root.mkdir(parents=True, exist_ok=True)
        render_root.mkdir(parents=True, exist_ok=True)

        for source in plan["sources"]:
            pdf = pdf_root / f"{source['source_code']}.pdf"
            _materialize_source(source, pdf)
            png = _render_one(source, pdf, render_root)
            _tile_one(source, pdf, png, viewer_root)
            shutil.rmtree(render_root / source["source_code"], ignore_errors=True)
            pdf.unlink(missing_ok=True)

        _run(
            [
                sys.executable,
                str(ROOT / "scripts/build_cew_source_viewer.py"),
                "--out-dir",
                str(viewer_root),
            ]
        )
        osd = _install_osd(viewer_root, temp_root)

    _validate_built_viewer(plan, viewer_root)
    count, total_bytes, tree_sha = _inventory(ASSET_ROOT)
    manifest = {
        **plan,
        **osd,
        "asset_root": ASSET_ROOT.name,
        "viewer_entrypoint": "source-viewer/index.html",
        "file_count": count,
        "total_bytes": total_bytes,
        "asset_tree_sha256": tree_sha,
        "managed_runtime_dynamic_pdf_rasterization": False,
        "build_state": "READY",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("CEW_MANAGED_F3_ASSET_BUILD = PASS")
    print(f"BUILD_REVISION = {manifest['build_revision']}")
    print(f"SOURCES = {','.join(source['source_code'] for source in manifest['sources'])}")
    print(f"DZI_ENGINE = {manifest['dzi_engine']}")
    print(f"FILE_COUNT = {count}")
    print(f"TOTAL_BYTES = {total_bytes}")
    print(f"ASSET_TREE_SHA256 = {tree_sha}")
    print("DYNAMIC_RUNTIME_RASTERIZATION = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-plan-only", action="store_true")
    args = parser.parse_args()
    plan = build_plan()
    if args.validate_plan_only:
        print("CEW_MANAGED_F3_BUILD_PLAN = PASS")
        print(f"BUILD_REVISION = {plan['build_revision']}")
        print(f"ARCHIVE_COMMIT = {plan['archive_commit']}")
        print(f"SOURCES = {','.join(source['source_code'] for source in plan['sources'])}")
        print(f"DZI_ENGINE = {plan['dzi_engine']}")
        print("CANONICAL_WRITE_AUTHORIZED = false")
        return 0
    build_assets()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
