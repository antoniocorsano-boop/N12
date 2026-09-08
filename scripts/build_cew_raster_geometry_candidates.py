#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any

import pymupdf

import build_cew_evidence_region_content_diagnostic as r1_builder
import build_cew_managed_f3_assets as managed_f3_builder

ROOT = Path(__file__).resolve().parents[1]
R1_ROOT = ROOT / ".cew_evidence_region_content_diagnostic"
R1_MANIFEST = R1_ROOT / "manifest.json"
ASSET_ROOT = ROOT / ".cew_raster_geometry_candidates"
MANIFEST = ASSET_ROOT / "manifest.json"
WORKER = ROOT / "scripts/cew_raster_geometry_candidate_worker.py"
OPENCV_PIN = "opencv-python-headless==4.12.0.88"
CROP_DPIS = (200, 300)
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ).strip()


def _load_r1() -> dict[str, Any]:
    if not R1_MANIFEST.is_file():
        raise AssertionError("R2_REQUIRES_R1_MANIFEST_ON_SAME_BUILD")
    data = json.loads(R1_MANIFEST.read_text(encoding="utf-8"))
    if data.get("build_revision") != _revision():
        raise AssertionError(f"R2_R1_REVISION_MISMATCH:{data.get('build_revision')}:{_revision()}")
    results = data.get("region_results") or []
    if {row.get("evidence_region_id") for row in results} != EXPECTED_REGIONS:
        raise AssertionError("R2_R1_REGION_COVERAGE_MISMATCH")
    for row in results:
        if row.get("classification") != "RASTER":
            raise AssertionError(f"R2_REQUIRES_RASTER_REGION:{row.get('evidence_region_id')}:{row.get('classification')}")
        if row.get("mapping_error_reason") is not None:
            raise AssertionError(f"R2_MAPPING_ERROR_NOT_ALLOWED:{row.get('evidence_region_id')}")
        if row.get("canonical_write_authorized") is not False:
            raise AssertionError("R1_AUTHORITY_DRIFT")
    return data


def _source_plan() -> dict[str, dict[str, Any]]:
    plan = managed_f3_builder.build_plan()
    return {row["source_code"]: row for row in plan["sources"]}


def _render_region_crop(pdf: Path, page_index: int, normalized: dict[str, float], dpi: int, target: Path) -> dict[str, Any]:
    doc = pymupdf.open(pdf)
    try:
        if page_index < 0 or page_index >= doc.page_count:
            raise AssertionError(f"R2_PAGE_INDEX_OUT_OF_RANGE:{page_index}")
        page = doc[page_index]
        page_rect = pymupdf.Rect(page.rect)
        width = float(page_rect.width)
        height = float(page_rect.height)
        x = float(normalized["x"])
        y = float(normalized["y"])
        w = float(normalized["width"])
        h = float(normalized["height"])
        clip = pymupdf.Rect(
            page_rect.x0 + x * width,
            page_rect.y0 + y * height,
            page_rect.x0 + (x + w) * width,
            page_rect.y0 + (y + h) * height,
        ) & page_rect
        if clip.is_empty or clip.width <= 0 or clip.height <= 0:
            raise AssertionError("R2_EMPTY_SOURCE_CLIP")
        matrix = pymupdf.Matrix(dpi / 72.0, dpi / 72.0)
        pix = page.get_pixmap(matrix=matrix, clip=clip, colorspace=pymupdf.csGRAY, alpha=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(target))
        return {
            "dpi": dpi,
            "filename": target.name,
            "sha256": _sha256(target),
            "width_px": int(pix.width),
            "height_px": int(pix.height),
            "source_rect_pt": [
                round(float(clip.x0), 6),
                round(float(clip.y0), 6),
                round(float(clip.x1), 6),
                round(float(clip.y1), 6),
            ],
        }
    finally:
        doc.close()


def _venv_python(root: Path) -> Path:
    if os.name == "nt":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python"


def _install_worker_environment(env_root: Path) -> Path:
    venv.EnvBuilder(with_pip=True, clear=True).create(env_root)
    python = _venv_python(env_root)
    subprocess.run(
        [str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", OPENCV_PIN],
        check=True,
        cwd=ROOT,
    )
    return python


def build_plan() -> dict[str, Any]:
    r1 = _load_r1()
    return {
        "schema_version": "1.0",
        "artifact_contract": "CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES_v1",
        "build_revision": _revision(),
        "r1_build_revision": r1["build_revision"],
        "r1_contract": r1["diagnostic_contract"],
        "r1_raster_region_count": sum(1 for row in r1["region_results"] if row["classification"] == "RASTER"),
        "target_region_ids": sorted(EXPECTED_REGIONS),
        "crop_dpis": list(CROP_DPIS),
        "worker_dependency_pin": OPENCV_PIN,
        "worker_environment": "EPHEMERAL_BUILD_ONLY",
        "runtime_opencv_required": False,
        "scene_materialization_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def build() -> dict[str, Any]:
    r1 = _load_r1()
    plan = build_plan()
    source_plan = _source_plan()
    managed_f3_builder._ensure_archive_commit(r1["archive_commit"])

    if ASSET_ROOT.exists():
        shutil.rmtree(ASSET_ROOT)
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    crop_root = ASSET_ROOT / "crops"
    worker_root = ASSET_ROOT / "worker"

    source_pdfs: dict[str, Path] = {}
    regions_for_worker: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="cew-pwb005-r2-src-") as source_temp:
        source_temp_root = Path(source_temp)
        for result in sorted(r1["region_results"], key=lambda row: row["evidence_region_id"]):
            source_code = result["source_code"]
            source = source_plan.get(source_code)
            if source is None:
                raise AssertionError(f"R2_SOURCE_NOT_IN_MANAGED_F3_PLAN:{source_code}")
            if source["source_version_id"] != result["source_version_id"] or source["sha256"] != result["source_sha256"]:
                raise AssertionError(f"R2_SOURCE_IDENTITY_MISMATCH:{source_code}")
            pdf = source_pdfs.get(source_code)
            if pdf is None:
                pdf = source_temp_root / f"{source_code}.pdf"
                managed_f3_builder._materialize_source(source, pdf)
                source_pdfs[source_code] = pdf

            region_id = result["evidence_region_id"]
            region_crop_dir = crop_root / region_id
            crops: dict[str, Any] = {}
            source_rect: list[float] | None = None
            for dpi in CROP_DPIS:
                target = region_crop_dir / f"crop_{dpi}.png"
                crop = _render_region_crop(pdf, int(result["page_index"]), result["region"]["bbox_normalized"], dpi, target)
                crops[str(dpi)] = crop
                if source_rect is None:
                    source_rect = crop["source_rect_pt"]
                elif source_rect != crop["source_rect_pt"]:
                    raise AssertionError(f"R2_SOURCE_RECT_DRIFT_ACROSS_SCALES:{region_id}")

            regions_for_worker.append({
                "evidence_region_id": region_id,
                "source_code": source_code,
                "source_id": result["source_id"],
                "source_version_id": result["source_version_id"],
                "source_sha256": result["source_sha256"],
                "page_id": result["page_id"],
                "transform_id": result["transform_id"],
                "source_rect_pt": source_rect,
                "r1_classification": result["classification"],
                "crop_200_path": str((region_crop_dir / "crop_200.png").resolve()),
                "crop_300_path": str((region_crop_dir / "crop_300.png").resolve()),
                "crop_200": crops["200"],
                "crop_300": crops["300"],
            })

        job_path = ASSET_ROOT / "worker_job.json"
        job_path.write_text(json.dumps({"regions": regions_for_worker}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        with tempfile.TemporaryDirectory(prefix="cew-pwb005-r2-env-") as env_temp:
            python = _install_worker_environment(Path(env_temp))
            subprocess.run([str(python), str(WORKER), str(job_path), str(worker_root)], check=True, cwd=ROOT)

    worker_output_path = worker_root / "worker_output.json"
    if not worker_output_path.is_file():
        raise AssertionError("R2_WORKER_OUTPUT_MISSING")
    worker_output = json.loads(worker_output_path.read_text(encoding="utf-8"))
    rows = worker_output["regions"]
    if {row["evidence_region_id"] for row in rows} != EXPECTED_REGIONS:
        raise AssertionError("R2_WORKER_REGION_COVERAGE_MISMATCH")

    region_entries: list[dict[str, Any]] = []
    stable_total = 0
    for row in rows:
        result_path = worker_root / row["result_filename"]
        preview_path = worker_root / row["preview_filename"]
        if not result_path.is_file() or not preview_path.is_file():
            raise AssertionError(f"R2_REGION_ARTIFACT_MISSING:{row['evidence_region_id']}")
        stable_total += int(row["stable_candidate_count"])
        region_entries.append({
            "evidence_region_id": row["evidence_region_id"],
            "source_code": row["source_code"],
            "source_version_id": row["source_version_id"],
            "source_sha256": row["source_sha256"],
            "page_id": row["page_id"],
            "transform_id": row["transform_id"],
            "quality_state": row["quality_state"],
            "raw_line_count_200": row["scale_200"]["raw_line_count"],
            "raw_line_count_300": row["scale_300"]["raw_line_count"],
            "stable_candidate_count": row["stable_candidate_count"],
            "result_filename": str(result_path.relative_to(ASSET_ROOT)),
            "result_sha256": _sha256(result_path),
            "preview_filename": str(preview_path.relative_to(ASSET_ROOT)),
            "preview_sha256": _sha256(preview_path),
            "crop_200_filename": str((crop_root / row["evidence_region_id"] / "crop_200.png").relative_to(ASSET_ROOT)),
            "crop_200_sha256": row["crops"]["200"]["sha256"],
            "crop_300_filename": str((crop_root / row["evidence_region_id"] / "crop_300.png").relative_to(ASSET_ROOT)),
            "crop_300_sha256": row["crops"]["300"]["sha256"],
        })

    manifest = {
        **plan,
        "opencv_version": worker_output["opencv_version"],
        "numpy_version": worker_output["numpy_version"],
        "region_entries": sorted(region_entries, key=lambda row: row["evidence_region_id"]),
        "stable_candidate_total": stable_total,
        "quality_gate_state": "CANDIDATE_REVIEW_REQUIRED",
        "r2c_scene_adapter_authorized": False,
        "runtime_opencv_required": False,
        "scene_materialization_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R2_RASTER_GEOMETRY_BUILD = PASS")
    print("REGION_COVERAGE = 4/4")
    print("SCALE_CROP_COVERAGE = 8/8")
    print("WORKER_DEPENDENCY_PIN = " + OPENCV_PIN)
    print("OPENCV_VERSION = " + str(manifest["opencv_version"]))
    for row in manifest["region_entries"]:
        print(
            "R2_RESULT",
            row["evidence_region_id"],
            "raw200=" + str(row["raw_line_count_200"]),
            "raw300=" + str(row["raw_line_count_300"]),
            "stable=" + str(row["stable_candidate_count"]),
            "quality=" + row["quality_state"],
        )
    print("STABLE_CANDIDATE_TOTAL = " + str(stable_total))
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("RUNTIME_OPENCV_REQUIRED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
