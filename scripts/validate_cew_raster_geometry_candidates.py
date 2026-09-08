#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_raster_geometry_candidates"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}
EXPECTED_PIN = "opencv-python-headless==4.12.0.88"


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
        or ""
    ).strip()


def _within(value: float, low: float, high: float, tolerance: float = 1e-6) -> bool:
    return low - tolerance <= value <= high + tolerance


def main() -> int:
    if not MANIFEST.is_file():
        raise AssertionError("R2_MANIFEST_MISSING")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "1.0"
    assert manifest["artifact_contract"] == "CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES_v1"
    assert manifest["r1_raster_region_count"] == 4
    assert set(manifest["target_region_ids"]) == EXPECTED_REGIONS
    assert manifest["crop_dpis"] == [200, 300]
    assert manifest["worker_dependency_pin"] == EXPECTED_PIN
    assert manifest["worker_environment"] == "EPHEMERAL_BUILD_ONLY"
    assert manifest["quality_gate_state"] == "CANDIDATE_REVIEW_REQUIRED"
    assert manifest["r2c_scene_adapter_authorized"] is False
    assert manifest["runtime_opencv_required"] is False
    assert manifest["scene_materialization_authorized"] is False
    assert manifest["technical_identity_authorized"] is False
    assert manifest["structural_identity_authorized"] is False
    assert manifest["canonical_write_authorized"] is False
    assert manifest["engineering_authority_effect"] == "NONE"
    assert str(manifest["opencv_version"]).startswith("4.12.0")

    revision = _revision()
    if revision:
        assert manifest["build_revision"] == revision, (manifest["build_revision"], revision)
        assert manifest["r1_build_revision"] == revision, (manifest["r1_build_revision"], revision)

    entries = manifest["region_entries"]
    assert len(entries) == 4
    assert {row["evidence_region_id"] for row in entries} == EXPECTED_REGIONS
    assert sum(int(row["stable_candidate_count"]) for row in entries) == manifest["stable_candidate_total"]

    all_candidate_ids: set[str] = set()
    total_raw_200 = 0
    total_raw_300 = 0
    truncated_regions: list[str] = []

    for entry in entries:
        for key in ("result_filename", "preview_filename", "crop_200_filename", "crop_300_filename"):
            path = ASSET_ROOT / entry[key]
            assert path.is_file(), (entry["evidence_region_id"], key, path)
        assert _sha256(ASSET_ROOT / entry["result_filename"]) == entry["result_sha256"]
        assert _sha256(ASSET_ROOT / entry["preview_filename"]) == entry["preview_sha256"]
        assert _sha256(ASSET_ROOT / entry["crop_200_filename"]) == entry["crop_200_sha256"]
        assert _sha256(ASSET_ROOT / entry["crop_300_filename"]) == entry["crop_300_sha256"]

        result = json.loads((ASSET_ROOT / entry["result_filename"]).read_text(encoding="utf-8"))
        assert result["evidence_region_id"] == entry["evidence_region_id"]
        assert result["source_version_id"] == entry["source_version_id"]
        assert result["source_sha256"] == entry["source_sha256"]
        assert result["page_id"] == entry["page_id"]
        assert result["transform_id"] == entry["transform_id"]
        assert result["r1_classification"] == "RASTER"
        assert result["quality_state"] in {"STABLE_CANDIDATES_PRESENT", "NO_STABLE_CANDIDATES"}
        assert result["technical_identity_authorized"] is False
        assert result["structural_identity_authorized"] is False
        assert result["scene_materialization_authorized"] is False
        assert result["canonical_write_authorized"] is False
        assert result["engineering_authority_effect"] == "NONE"
        assert result["detector"]["algorithm"] == "CANNY_PLUS_PROBABILISTIC_HOUGH_MULTI_SCALE"
        assert str(result["detector"]["opencv_version"]).startswith("4.12.0")
        assert result["detector"]["angle_tolerance_deg"] == 2.0
        assert result["detector"]["endpoint_tolerance_norm"] == 0.01
        assert result["detector"]["relative_length_tolerance"] == 0.08
        assert result["stable_candidate_count"] == len(result["stable_candidates"])
        assert result["stable_candidate_count"] == entry["stable_candidate_count"]

        total_raw_200 += int(result["scale_200"]["raw_line_count"])
        total_raw_300 += int(result["scale_300"]["raw_line_count"])
        if result["scale_200"]["matching_truncated"] or result["scale_300"]["matching_truncated"]:
            truncated_regions.append(entry["evidence_region_id"])

        assert result["crops"]["200"]["dpi"] == 200
        assert result["crops"]["300"]["dpi"] == 300
        source_rect = [float(value) for value in result["source_rect_pt"]]
        x0, y0, x1, y1 = source_rect
        assert x1 > x0 and y1 > y0

        for candidate in result["stable_candidates"]:
            candidate_id = candidate["candidate_id"]
            assert candidate_id not in all_candidate_ids, candidate_id
            all_candidate_ids.add(candidate_id)
            assert candidate["object_family"] == "RasterGeometryCandidate"
            assert candidate["geometry_type"] == "LINE"
            assert candidate["coordinate_space"] == "EVIDENCE_REGION_NORMALIZED_0_1"
            assert candidate["semantic_classification"] == "UNASSIGNED"
            assert candidate["candidate_state"] == "STABLE_ACROSS_200_300_DPI"
            assert candidate["technical_identity_authorized"] is False
            assert candidate["structural_identity_authorized"] is False
            assert candidate["scene_materialization_authorized"] is False
            assert candidate["canonical_write_authorized"] is False
            assert candidate["support"]["line_200_id"].startswith("L200-")
            assert candidate["support"]["line_300_id"].startswith("L300-")
            assert candidate["support"]["endpoint_error_norm"] <= 0.01 + 1e-9
            assert candidate["support"]["angle_error_deg"] <= 2.0 + 1e-9
            assert candidate["support"]["relative_length_error"] <= 0.08 + 1e-9
            assert 0.0 <= candidate["support"]["stability_score"] <= 1.0

            for point in (candidate["geometry_normalized"]["a"], candidate["geometry_normalized"]["b"]):
                assert _within(float(point[0]), 0.0, 1.0)
                assert _within(float(point[1]), 0.0, 1.0)
            for point in (candidate["geometry_source_page_pt"]["a"], candidate["geometry_source_page_pt"]["b"]):
                assert _within(float(point[0]), x0, x1)
                assert _within(float(point[1]), y0, y1)

    print("CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES = PASS")
    print("REGION_COVERAGE = 4/4")
    print("SCALE_CROP_COVERAGE = 8/8")
    print("R1_RASTER_INPUTS = 4/4")
    print("WORKER_DEPENDENCY_PIN = " + EXPECTED_PIN)
    print("RAW_LINE_TOTAL_200 = " + str(total_raw_200))
    print("RAW_LINE_TOTAL_300 = " + str(total_raw_300))
    print("STABLE_CANDIDATE_TOTAL = " + str(manifest["stable_candidate_total"]))
    print("MATCHING_TRUNCATED_REGIONS = " + (",".join(sorted(truncated_regions)) if truncated_regions else "NONE"))
    for entry in entries:
        print(
            "R2_REGION_VALIDATED",
            entry["evidence_region_id"],
            "stable=" + str(entry["stable_candidate_count"]),
            "quality=" + entry["quality_state"],
        )
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("RUNTIME_OPENCV_REQUIRED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
