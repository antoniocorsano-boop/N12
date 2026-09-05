#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".cew_evidence_region_mapping_root_cause/manifest.json"
TARGET_IDS = {"CEW-N12-REG-G01-R06", "CEW-N12-REG-G07-R07"}
ALLOWED = {
    "PAGE_REGISTRY_ROW_MISSING",
    "SOURCE_VERSION_MISMATCH",
    "PAGE_INDEX_OUT_OF_RANGE",
    "PAGE_DIMENSION_MISMATCH",
    "NORMALIZED_REGION_OUT_OF_BOUNDS",
    "FLOATING_POINT_CONTAINMENT_TOLERANCE",
    "SOURCE_REGION_OUTSIDE_PAGE",
    "NO_MAPPING_ERROR_REPRODUCED",
}


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or ""
    ).strip()


def main() -> int:
    if not MANIFEST.is_file():
        raise AssertionError("PWB005_R1A_MANIFEST_MISSING")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["diagnostic_contract"] == "CEW_PWB005_R1A_REGION_MAPPING_ROOT_CAUSE_v1"
    assert set(data["target_region_ids"]) == TARGET_IDS
    assert set(data["allowed_root_causes"]) == ALLOWED
    assert data["canonical_write_authorized"] is False
    assert data["engineering_authority_effect"] == "NONE"
    assert data["hva_execution_authorized"] is False

    revision = _revision()
    if revision:
        assert data["build_revision"] == revision, (data["build_revision"], revision)

    rows = data["results"]
    assert len(rows) == 2
    assert {row["evidence_region_id"] for row in rows} == TARGET_IDS
    for row in rows:
        assert row["root_cause"] in ALLOWED
        assert row["canonical_write_authorized"] is False
        assert row["engineering_authority_effect"] == "NONE"
        predicates = row["predicates"]
        for key in (
            "page_registry_present",
            "source_version_match",
            "page_index_in_range",
            "page_dimensions_match",
            "normalized_bbox_valid",
            "source_rect_nonempty",
            "strict_r1_containment",
            "edge_tolerant_containment",
        ):
            assert isinstance(predicates[key], bool), (row["evidence_region_id"], key)
        assert row["region"]["source_area_pt2"] >= 0
        assert row["region"]["intersection_area_pt2"] >= 0
        assert row["region"]["intersection_area_deficit_pt2"] >= 0
        assert set(row["region"]["edge_overhang_pt"]) == {"left", "top", "right", "bottom"}
        assert all(value >= 0 for value in row["region"]["edge_overhang_pt"].values())
        if row["root_cause"] == "FLOATING_POINT_CONTAINMENT_TOLERANCE":
            assert predicates["strict_r1_containment"] is False
            assert predicates["edge_tolerant_containment"] is True
            assert all(value <= data["edge_tolerance_pt"] for value in row["region"]["edge_overhang_pt"].values())
        if row["root_cause"] == "NO_MAPPING_ERROR_REPRODUCED":
            assert predicates["strict_r1_containment"] is True

    print("CEW_PWB005_R1A_MAPPING_ROOT_CAUSE = PASS")
    print("TARGET_REGION_COVERAGE = 2/2")
    for row in rows:
        print(
            "R1A_RESULT",
            row["evidence_region_id"],
            row["root_cause"],
            "strict=" + str(row["predicates"]["strict_r1_containment"]),
            "tolerant=" + str(row["predicates"]["edge_tolerant_containment"]),
            "area_deficit=" + str(row["region"]["intersection_area_deficit_pt2"]),
        )
    print("PROVENANCE_REPAIR_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("HVA_EXECUTION_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
