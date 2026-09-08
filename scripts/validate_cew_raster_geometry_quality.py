#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".cew_raster_geometry_quality/manifest.json"
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


def main() -> int:
    if not MANIFEST.is_file():
        raise AssertionError("R2Q_MANIFEST_MISSING")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["diagnostic_contract"] == "CEW_PWB005_R2Q_RASTER_GEOMETRY_QUALITY_v1"
    assert data["build_revision"] == _revision()
    assert data["r2_build_revision"] == _revision()
    assert data["r2_artifact_contract"] == "CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES_v1"
    assert data["region_coverage"] == "4/4"
    assert data["decision_state"] == "QUALITY_DIAGNOSTIC_COMPLETE"
    assert data["r2c_scene_adapter_authorized"] is False
    assert data["technical_identity_authorized"] is False
    assert data["structural_identity_authorized"] is False
    assert data["canonical_write_authorized"] is False
    assert data["engineering_authority_effect"] == "NONE"

    regions = data["regions"]
    assert {row["evidence_region_id"] for row in regions} == EXPECTED_REGIONS
    assert sum(row["stable_candidate_count"] for row in regions) == data["stable_candidate_total"]
    assert data["stable_candidate_total"] > 0

    for row in regions:
        assert row["source_version_id"]
        assert len(row["source_sha256"]) == 64
        assert row["page_id"]
        assert row["transform_id"]
        assert row["stable_candidate_count"] > 0
        assert 0.0 <= row["stable_to_raw_200_ratio"] <= 1.0
        assert 0.0 <= row["stable_to_raw_300_ratio"] <= 1.0
        assert 0.0 <= row["orientation"]["horizontal_fraction"] <= 1.0
        assert 0.0 <= row["orientation"]["vertical_fraction"] <= 1.0
        assert 0.0 <= row["orientation"]["oblique_fraction"] <= 1.0
        assert (
            row["orientation"]["horizontal_count"]
            + row["orientation"]["vertical_count"]
            + row["orientation"]["oblique_count"]
            == row["stable_candidate_count"]
        )
        assert row["length_norm"]["min"] <= row["length_norm"]["median"] <= row["length_norm"]["max"]
        assert row["length_norm"]["median"] <= row["length_norm"]["p90"] <= row["length_norm"]["max"]
        assert 0.0 <= row["stability_score"]["min"] <= 1.0
        assert 0.0 <= row["stability_score"]["p10"] <= 1.0
        assert 0.0 <= row["stability_score"]["median"] <= 1.0
        assert 0.0 <= row["near_duplicates"]["member_fraction"] <= 1.0
        assert 0.0 <= row["endpoint_connectivity"]["connected_endpoint_fraction"] <= 1.0
        assert row["quality_state"] == "QUALITY_DIAGNOSTIC_COMPLETE"
        assert row["r2c_scene_adapter_authorized"] is False
        assert row["technical_identity_authorized"] is False
        assert row["structural_identity_authorized"] is False
        assert row["canonical_write_authorized"] is False
        assert row["engineering_authority_effect"] == "NONE"

    print("CEW_PWB005_R2Q_RASTER_GEOMETRY_QUALITY = PASS")
    print("REGION_COVERAGE = 4/4")
    print("STABLE_CANDIDATE_TOTAL = " + str(data["stable_candidate_total"]))
    for row in sorted(regions, key=lambda item: item["evidence_region_id"]):
        print(
            "R2Q_VALIDATED",
            row["evidence_region_id"],
            "stable=" + str(row["stable_candidate_count"]),
            "raw_ratio_200=" + str(row["stable_to_raw_200_ratio"]),
            "raw_ratio_300=" + str(row["stable_to_raw_300_ratio"]),
            "median_len=" + str(row["length_norm"]["median"]),
            "p90_len=" + str(row["length_norm"]["p90"]),
            "horizontal=" + str(row["orientation"]["horizontal_fraction"]),
            "vertical=" + str(row["orientation"]["vertical_fraction"]),
            "oblique=" + str(row["orientation"]["oblique_fraction"]),
            "dup_fraction=" + str(row["near_duplicates"]["member_fraction"]),
            "connected=" + str(row["endpoint_connectivity"]["connected_endpoint_fraction"]),
            "stability_p10=" + str(row["stability_score"]["p10"]),
            "stability_median=" + str(row["stability_score"]["median"]),
        )
    print("R2Q_DIAGNOSTIC_AUTHORITY = NONE")
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
