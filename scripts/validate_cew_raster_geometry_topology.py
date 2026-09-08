#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_raster_geometry_topology"
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


def main() -> int:
    if not MANIFEST.is_file():
        raise AssertionError("R2T_MANIFEST_MISSING")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["diagnostic_contract"] == "CEW_PWB005_R2T_TOPOLOGY_COHERENCE_v1"
    assert data["build_revision"] == _revision()
    assert data["region_coverage"] == "4/4"
    assert data["touch_tolerance_norm"] == 0.004
    assert data["input_consolidated_candidate_total"] > 0
    assert data["r2_support_total"] == 230
    assert data["decision_state"] == "TOPOLOGY_DIAGNOSTIC_COMPLETE_REVIEW_REQUIRED"
    assert data["topology_authority"] == "NONE"
    assert data["structural_node_interpretation_authorized"] is False
    assert data["r2c_scene_adapter_authorized"] is False
    assert data["technical_identity_authorized"] is False
    assert data["structural_identity_authorized"] is False
    assert data["canonical_write_authorized"] is False
    assert data["engineering_authority_effect"] == "NONE"

    regions = data["regions"]
    assert {row["evidence_region_id"] for row in regions} == EXPECTED_REGIONS
    assert sum(row["consolidated_candidate_count"] for row in regions) == data["input_consolidated_candidate_total"]
    all_support_ids: list[str] = []

    for row in regions:
        result_path = ASSET_ROOT / row["result_filename"]
        assert result_path.is_file()
        stored = json.loads(result_path.read_text(encoding="utf-8"))
        assert stored["evidence_region_id"] == row["evidence_region_id"]
        assert stored["source_version_id"]
        assert len(stored["source_sha256"]) == 64
        assert stored["page_id"]
        assert stored["transform_id"]
        count = stored["consolidated_candidate_count"]
        assert count > 0
        assert stored["exact_intersection_pair_count"] >= 0
        assert stored["near_contact_pair_count"] >= 0
        assert stored["graph_edge_count"] == stored["exact_intersection_pair_count"] + stored["near_contact_pair_count"]
        assert 1 <= stored["connected_component_count"] <= count
        assert 1 <= stored["largest_component_size"] <= count
        assert 0.0 < stored["largest_component_fraction"] <= 1.0
        assert 0 <= stored["isolated_candidate_count"] <= count
        assert 0.0 <= stored["isolated_candidate_fraction"] <= 1.0
        assert stored["mean_graph_degree"] >= 0.0
        assert stored["max_graph_degree"] >= 0
        assert stored["residual_r2m_compatible_pair_count"] >= 0
        stability = stored["support_stability"]
        assert stability["support_count"] > 0
        for key in ("min", "p10", "median", "group_median_p10", "group_median_median"):
            assert 0.0 <= stability[key] <= 1.0
        support_ids = stored["support_candidate_ids"]
        assert len(support_ids) == stability["support_count"]
        assert len(support_ids) == len(set(support_ids))
        all_support_ids.extend(support_ids)
        assert stored["topology_role"] == "GEOMETRIC_DIAGNOSTIC_ONLY"
        assert stored["structural_node_interpretation_authorized"] is False
        assert stored["r2c_scene_adapter_authorized"] is False
        assert stored["technical_identity_authorized"] is False
        assert stored["structural_identity_authorized"] is False
        assert stored["canonical_write_authorized"] is False
        assert stored["engineering_authority_effect"] == "NONE"

    assert len(all_support_ids) == 230
    assert len(set(all_support_ids)) == 230

    print("CEW_PWB005_R2T_TOPOLOGY_COHERENCE = PASS")
    print("REGION_COVERAGE = 4/4")
    print("CONSOLIDATED_CANDIDATE_TOTAL = " + str(data["input_consolidated_candidate_total"]))
    print("R2_SUPPORT_TOTAL = 230")
    for row in sorted(regions, key=lambda item: item["evidence_region_id"]):
        print(
            "R2T_VALIDATED",
            row["evidence_region_id"],
            "lines=" + str(row["consolidated_candidate_count"]),
            "edges=" + str(row["graph_edge_count"]),
            "components=" + str(row["connected_component_count"]),
            "largest=" + str(row["largest_component_fraction"]),
            "isolated=" + str(row["isolated_candidate_fraction"]),
            "degree_mean=" + str(row["mean_graph_degree"]),
            "residual=" + str(row["residual_r2m_compatible_pair_count"]),
            "stability=" + str(row["support_stability"]["median"]),
        )
    print("GEOMETRIC_INTERSECTION_IS_STRUCTURAL_NODE = false")
    print("R2T_DIAGNOSTIC_AUTHORITY = NONE")
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
