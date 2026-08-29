#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_raster_support_continuity"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_distribution(value: dict) -> None:
    assert set(value) == {"min", "p10", "median", "p90", "max"}
    assert 0.0 <= value["min"] <= value["p10"] <= value["median"] <= value["p90"] <= value["max"] <= 1.0


def main() -> int:
    if not MANIFEST.is_file():
        raise AssertionError("R2S_MANIFEST_MISSING")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["diagnostic_contract"] == "CEW_PWB005_R2S_RASTER_SUPPORT_CONTINUITY_v1"
    assert data["build_revision"] == _revision()
    assert data["region_coverage"] == "4/4"
    assert data["line_total"] > 0
    assert data["decision_state"] == "RASTER_SUPPORT_DIAGNOSTIC_COMPLETE_REVIEW_REQUIRED"
    assert data["sampling"]["line_sample_step_px"] == 4.0
    assert data["sampling"]["min_line_samples"] == 16
    assert data["sampling"]["max_line_samples"] == 256
    assert data["sampling"]["gap_angle_tolerance_deg"] == 3.0
    assert data["sampling"]["gap_perpendicular_separation_norm"] == 0.008
    assert data["sampling"]["max_projected_gap_norm"] == 0.05
    assert data["sampling"]["threshold_method"] == "OTSU_PER_EXACT_RASTER_CROP"
    assert data["ocr_used"] is False
    assert data["raster_support_is_technical_identity"] is False
    assert data["gap_hypothesis_is_geometry"] is False
    assert data["r2c_scene_adapter_authorized"] is False
    assert data["technical_identity_authorized"] is False
    assert data["structural_identity_authorized"] is False
    assert data["canonical_write_authorized"] is False
    assert data["engineering_authority_effect"] == "NONE"

    regions = data["regions"]
    assert {row["evidence_region_id"] for row in regions} == EXPECTED_REGIONS
    assert sum(row["line_count"] for row in regions) == data["line_total"]
    assert sum(row["gap_hypothesis_count"] for row in regions) == data["gap_hypothesis_total"]

    seen_line_ids: set[str] = set()
    seen_gap_ids: set[str] = set()
    total_r2_support_ids: list[str] = []

    for row in regions:
        result_path = ASSET_ROOT / row["result_filename"]
        assert result_path.is_file()
        assert _sha256(result_path) == row["result_sha256"]
        result = json.loads(result_path.read_text(encoding="utf-8"))
        assert result["evidence_region_id"] == row["evidence_region_id"]
        assert result["source_version_id"]
        assert len(result["source_sha256"]) == 64
        assert result["page_id"]
        assert result["transform_id"]
        assert result["line_count"] == row["line_count"] == len(result["line_support"])
        assert result["gap_hypothesis_count"] == row["gap_hypothesis_count"] == len(result["gap_hypotheses"])

        for dpi in ("200", "300"):
            raster = result["raster_inputs"][dpi]
            assert raster["dpi"] == int(dpi)
            assert len(raster["sha256"]) == 64
            assert raster["width_px"] > 0 and raster["height_px"] > 0
            assert 0 <= raster["otsu_threshold"] <= 255

        for key in (
            "line_cross_scale_support_distribution",
            "line_cross_scale_longest_run_distribution",
        ):
            _validate_distribution(result[key])
        if result["gap_hypothesis_count"]:
            _validate_distribution(result["gap_cross_scale_support_distribution"])
            _validate_distribution(result["gap_cross_scale_longest_run_distribution"])
        else:
            assert all(value == 0.0 for value in result["gap_cross_scale_support_distribution"].values())
            assert all(value == 0.0 for value in result["gap_cross_scale_longest_run_distribution"].values())

        region_support_ids: list[str] = []
        for line in result["line_support"]:
            line_id = line["consolidated_candidate_id"]
            assert line_id not in seen_line_ids
            seen_line_ids.add(line_id)
            support_ids = line["support_candidate_ids"]
            assert support_ids
            assert support_ids == sorted(support_ids)
            assert len(support_ids) == line["support_count"] == len(set(support_ids))
            region_support_ids.extend(support_ids)
            for scale in ("scale_200", "scale_300"):
                measurement = line[scale]
                assert measurement["sample_count"] >= 16
                assert measurement["band_radius_px"] >= 1
                assert 0.0 <= measurement["support_fraction"] <= 1.0
                assert 0.0 <= measurement["longest_supported_run_fraction"] <= 1.0
                assert 0.0 <= measurement["mean_min_band_luma"] <= 255.0
            assert line["cross_scale_min_support_fraction"] == min(
                line["scale_200"]["support_fraction"], line["scale_300"]["support_fraction"]
            )
            assert line["cross_scale_min_longest_run_fraction"] == min(
                line["scale_200"]["longest_supported_run_fraction"],
                line["scale_300"]["longest_supported_run_fraction"],
            )
            assert line["diagnostic_only"] is True
            assert line["scene_materialization_authorized"] is False
        assert len(region_support_ids) == len(set(region_support_ids))
        total_r2_support_ids.extend(region_support_ids)

        for gap in result["gap_hypotheses"]:
            gap_id = gap["gap_hypothesis_id"]
            assert gap_id not in seen_gap_ids
            seen_gap_ids.add(gap_id)
            assert gap["candidate_ids"] == sorted(gap["candidate_ids"])
            assert len(gap["candidate_ids"]) == 2
            assert 0.0 < gap["projected_gap_norm"] <= 0.05
            assert gap["nearest_endpoint_distance_norm"] > 0.0
            assert len(gap["bridge_endpoints_normalized"]["a"]) == 2
            assert len(gap["bridge_endpoints_normalized"]["b"]) == 2
            for point in gap["bridge_endpoints_normalized"].values():
                assert 0.0 <= point[0] <= 1.0
                assert 0.0 <= point[1] <= 1.0
            for scale in ("scale_200", "scale_300"):
                measurement = gap[scale]
                assert measurement["sample_count"] >= 16
                assert 0.0 <= measurement["support_fraction"] <= 1.0
                assert 0.0 <= measurement["longest_supported_run_fraction"] <= 1.0
            assert gap["cross_scale_min_support_fraction"] == min(
                gap["scale_200"]["support_fraction"], gap["scale_300"]["support_fraction"]
            )
            assert gap["cross_scale_min_longest_run_fraction"] == min(
                gap["scale_200"]["longest_supported_run_fraction"],
                gap["scale_300"]["longest_supported_run_fraction"],
            )
            assert gap["hypothesis_only"] is True
            assert gap["geometry_materialization_authorized"] is False
            assert gap["technical_identity_authorized"] is False
            assert gap["structural_identity_authorized"] is False

        assert result["ocr_used"] is False
        assert result["raster_support_is_technical_identity"] is False
        assert result["gap_hypothesis_is_geometry"] is False
        assert result["r2c_scene_adapter_authorized"] is False
        assert result["technical_identity_authorized"] is False
        assert result["structural_identity_authorized"] is False
        assert result["canonical_write_authorized"] is False
        assert result["engineering_authority_effect"] == "NONE"

    assert len(total_r2_support_ids) == 230
    assert len(set(total_r2_support_ids)) == 230

    print("CEW_PWB005_R2S_RASTER_SUPPORT_CONTINUITY = PASS")
    print("REGION_COVERAGE = 4/4")
    print("LINE_TOTAL = " + str(data["line_total"]))
    print("R2_SUPPORT_RETENTION = 230/230")
    print("GAP_HYPOTHESIS_TOTAL = " + str(data["gap_hypothesis_total"]))
    for row in sorted(regions, key=lambda item: item["evidence_region_id"]):
        print(
            "R2S_VALIDATED",
            row["evidence_region_id"],
            "lines=" + str(row["line_count"]),
            "line_support_med=" + str(row["line_cross_scale_support_distribution"]["median"]),
            "line_run_med=" + str(row["line_cross_scale_longest_run_distribution"]["median"]),
            "gaps=" + str(row["gap_hypothesis_count"]),
            "gap_support_med=" + str(row["gap_cross_scale_support_distribution"]["median"]),
            "gap_run_med=" + str(row["gap_cross_scale_longest_run_distribution"]["median"]),
        )
    print("OCR_USED = false")
    print("RASTER_SUPPORT_IS_TECHNICAL_IDENTITY = false")
    print("GAP_HYPOTHESIS_IS_GEOMETRY = false")
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
