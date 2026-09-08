#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_raster_geometry_consolidation"
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


def _stable_id(parts: list[str]) -> str:
    raw = "|".join(parts)
    return "RGM-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def main() -> int:
    if not MANIFEST.is_file():
        raise AssertionError("R2M_MANIFEST_MISSING")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    revision = _revision()

    assert data["schema_version"] == "1.0"
    assert data["artifact_contract"] == "CEW_PWB005_R2M_RASTER_GEOMETRY_CONSOLIDATION_v1"
    assert data["build_revision"] == revision
    assert data["r2_build_revision"] == revision
    assert data["r2q_build_revision"] == revision
    assert data["region_coverage"] == "4/4"
    assert data["input_candidate_total"] == 230
    assert 0 < data["consolidated_candidate_total"] <= data["input_candidate_total"]
    assert data["support_id_total"] == data["input_candidate_total"]
    assert data["support_retention"] == "100%"
    assert data["one_r2_candidate_to_one_r2m_group"] is True
    assert data["decision_state"] == "CONSOLIDATION_COMPLETE_REVIEW_REQUIRED"
    assert data["r2c_scene_adapter_authorized"] is False
    assert data["technical_identity_authorized"] is False
    assert data["structural_identity_authorized"] is False
    assert data["canonical_write_authorized"] is False
    assert data["engineering_authority_effect"] == "NONE"

    regions = data["regions"]
    assert {row["evidence_region_id"] for row in regions} == EXPECTED_REGIONS
    all_support_ids: list[str] = []
    output_total = 0

    for row in regions:
        result_path = ASSET_ROOT / row["result_filename"]
        preview_path = ASSET_ROOT / row["preview_filename"]
        assert result_path.is_file()
        assert preview_path.is_file()
        assert _sha256(result_path) == row["result_sha256"]
        assert _sha256(preview_path) == row["preview_sha256"]
        result = json.loads(result_path.read_text(encoding="utf-8"))

        assert result["evidence_region_id"] == row["evidence_region_id"]
        assert result["source_version_id"]
        assert len(result["source_sha256"]) == 64
        assert result["page_id"]
        assert result["transform_id"]
        assert result["r2_artifact_contract"] == "CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES_v1"
        assert result["consolidation_rule"]["angle_tolerance_deg"] == 2.0
        assert result["consolidation_rule"]["perpendicular_separation_norm"] == 0.006
        assert result["consolidation_rule"]["projected_gap_norm"] == 0.012
        assert result["consolidation_rule"]["grouping"] == "DETERMINISTIC_COMPLETE_LINK"
        assert result["support_retention"] == "100%"
        assert result["r2c_scene_adapter_authorized"] is False
        assert result["technical_identity_authorized"] is False
        assert result["structural_identity_authorized"] is False
        assert result["canonical_write_authorized"] is False
        assert result["engineering_authority_effect"] == "NONE"

        candidates = result["consolidated_candidates"]
        diagnostics = result["diagnostics"]
        assert len(candidates) == diagnostics["consolidated_candidate_count"] == row["consolidated_candidate_count"]
        assert diagnostics["input_candidate_count"] == row["input_candidate_count"]
        assert diagnostics["support_id_count"] == diagnostics["input_candidate_count"]
        assert diagnostics["multi_support_group_count"] + diagnostics["singleton_count"] == len(candidates)
        assert diagnostics["max_support_count"] >= 1
        assert 0.0 <= diagnostics["reduction_ratio"] < 1.0
        assert 0.0 <= diagnostics["endpoint_connectivity"]["connected_endpoint_fraction"] <= 1.0
        assert (
            diagnostics["orientation"]["horizontal_count"]
            + diagnostics["orientation"]["vertical_count"]
            + diagnostics["orientation"]["oblique_count"]
            == len(candidates)
        )

        region_support_ids: list[str] = []
        consolidated_ids: set[str] = set()
        for candidate in candidates:
            assert candidate["object_family"] == "RasterGeometryConsolidatedCandidate"
            assert candidate["geometry_type"] == "LINE"
            assert candidate["coordinate_space"] == "EVIDENCE_REGION_NORMALIZED_0_1"
            support_ids = candidate["support_candidate_ids"]
            assert support_ids
            assert support_ids == sorted(support_ids)
            assert len(support_ids) == len(set(support_ids)) == candidate["support_count"]
            assert candidate["consolidated_candidate_id"] == _stable_id(support_ids)
            assert candidate["consolidated_candidate_id"] not in consolidated_ids
            consolidated_ids.add(candidate["consolidated_candidate_id"])
            region_support_ids.extend(support_ids)
            for key in ("a", "b"):
                normalized = candidate["geometry_normalized"][key]
                assert len(normalized) == 2
                assert 0.0 <= normalized[0] <= 1.0
                assert 0.0 <= normalized[1] <= 1.0
                source_point = candidate["geometry_source_page_pt"][key]
                assert len(source_point) == 2
            assert candidate["semantic_classification"] == "UNASSIGNED"
            assert candidate["technical_identity_authorized"] is False
            assert candidate["structural_identity_authorized"] is False
            assert candidate["scene_materialization_authorized"] is False
            assert candidate["canonical_write_authorized"] is False
            assert candidate["engineering_authority_effect"] == "NONE"

        assert len(region_support_ids) == diagnostics["input_candidate_count"]
        assert len(region_support_ids) == len(set(region_support_ids))
        all_support_ids.extend(region_support_ids)
        output_total += len(candidates)

    assert len(all_support_ids) == data["input_candidate_total"]
    assert len(all_support_ids) == len(set(all_support_ids))
    assert output_total == data["consolidated_candidate_total"]
    expected_reduction = round(1.0 - output_total / data["input_candidate_total"], 8)
    assert data["global_reduction_ratio"] == expected_reduction

    print("CEW_PWB005_R2M_RASTER_GEOMETRY_CONSOLIDATION = PASS")
    print("REGION_COVERAGE = 4/4")
    print("INPUT_CANDIDATE_TOTAL = " + str(data["input_candidate_total"]))
    print("CONSOLIDATED_CANDIDATE_TOTAL = " + str(data["consolidated_candidate_total"]))
    print("GLOBAL_REDUCTION_RATIO = " + str(data["global_reduction_ratio"]))
    print("SUPPORT_RETENTION = 100%")
    print("ONE_R2_CANDIDATE_TO_ONE_R2M_GROUP = true")
    for row in sorted(regions, key=lambda item: item["evidence_region_id"]):
        print(
            "R2M_VALIDATED",
            row["evidence_region_id"],
            "input=" + str(row["input_candidate_count"]),
            "output=" + str(row["consolidated_candidate_count"]),
            "reduction=" + str(row["reduction_ratio"]),
            "multi=" + str(row["multi_support_group_count"]),
            "max_support=" + str(row["max_support_count"]),
            "connected=" + str(row["endpoint_connectivity"]["connected_endpoint_fraction"]),
        )
    print("R2M_AUTHORITY = NONE")
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
