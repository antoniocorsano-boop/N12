#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
R2SN_ROOT = ROOT / ".cew_raster_support_negative_controls"
R2SN_MANIFEST = R2SN_ROOT / "manifest.json"
R2BR_ROOT = ROOT / ".cew_raster_bridge_review"
R2BR_MANIFEST = R2BR_ROOT / "manifest.json"
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


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"R2BR_REQUIRED_ARTIFACT_MISSING:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_tier(row: dict[str, Any], cutoffs: dict[str, Any]) -> str:
    if row.get("negative_control_state") != "NEGATIVE_CONTROL_COMPLETE":
        return "CONTROL_INCOMPLETE_REVIEW"
    values = (
        row.get("r2s_cross_scale_min_support_fraction"),
        row.get("r2s_cross_scale_min_longest_run_fraction"),
        row.get("cross_scale_min_support_contrast"),
        row.get("cross_scale_min_run_contrast"),
    )
    if any(value is None for value in values):
        return "CONTROL_INCOMPLETE_REVIEW"
    if (
        float(values[0]) >= float(cutoffs["support_min"])
        and float(values[1]) >= float(cutoffs["run_min"])
        and float(values[2]) >= float(cutoffs["support_contrast_min"])
        and float(values[3]) >= float(cutoffs["run_contrast_min"])
    ):
        return "HIGH_CONTRAST_REVIEW"
    return "STANDARD_REVIEW"


def validate() -> None:
    revision = _revision()
    r2sn = _load(R2SN_MANIFEST)
    r2br = _load(R2BR_MANIFEST)

    assert r2sn["build_revision"] == revision, "R2BR_R2SN_REVISION_MISMATCH"
    assert r2br["build_revision"] == revision, "R2BR_REVISION_MISMATCH"
    assert r2br["review_contract"] == "CEW_PWB005_R2BR_BRIDGE_REVIEW_LAYER_v1"
    assert r2br["region_coverage"] == "4/4"
    assert int(r2br["gap_hypothesis_total"]) == int(r2sn["gap_hypothesis_total"]) == 10
    assert r2br["decision_state"] == "BRIDGE_REVIEW_LAYER_READY_HUMAN_INSPECTION_REQUIRED"
    assert r2br["review_layer_authority"] == "NONE"
    assert r2br["bridge_candidate_authorized"] is False
    assert r2br["geometry_materialization_authorized"] is False
    assert r2br["r2c_scene_adapter_authorized"] is False
    assert r2br["technical_identity_authorized"] is False
    assert r2br["structural_identity_authorized"] is False
    assert r2br["canonical_write_authorized"] is False
    assert r2br["engineering_authority_effect"] == "NONE"
    cutoffs = r2br["review_cutoffs"]
    assert cutoffs["purpose"] == "HUMAN_REVIEW_PRIORITY_ONLY"
    assert cutoffs["correctness_threshold"] is False

    r2sn_entries = {row["evidence_region_id"]: row for row in r2sn["regions"]}
    r2br_entries = {row["evidence_region_id"]: row for row in r2br["regions"]}
    assert set(r2sn_entries) == EXPECTED_REGIONS
    assert set(r2br_entries) == EXPECTED_REGIONS

    seen: set[str] = set()
    high = standard = incomplete = 0

    for region_id in sorted(EXPECTED_REGIONS):
        source = _load(R2SN_ROOT / r2sn_entries[region_id]["result_filename"])
        review = _load(R2BR_ROOT / r2br_entries[region_id]["result_filename"])
        assert review["evidence_region_id"] == region_id
        assert review["build_revision"] == revision
        assert review["source_code"] == source["source_code"]
        assert review["source_version_id"] == source["source_version_id"]
        assert review["source_sha256"] == source["source_sha256"]
        assert review["page_id"] == source["page_id"]
        assert review["transform_id"] == source["transform_id"]
        assert review["bridge_candidate_authorized"] is False
        assert review["geometry_materialization_authorized"] is False
        assert review["r2c_scene_adapter_authorized"] is False
        assert review["canonical_write_authorized"] is False

        source_rows = {row["gap_hypothesis_id"]: row for row in source["negative_controls"]}
        review_rows = {row["gap_hypothesis_id"]: row for row in review["review_rows"]}
        assert set(source_rows) == set(review_rows), f"R2BR_GAP_RETENTION_FAILURE:{region_id}"

        for gap_id in sorted(source_rows):
            assert gap_id not in seen, f"R2BR_DUPLICATE_GAP:{gap_id}"
            seen.add(gap_id)
            src = source_rows[gap_id]
            row = review_rows[gap_id]
            assert row["candidate_ids"] == src["candidate_ids"]
            assert row["bridge_endpoints_normalized"] == src["bridge_endpoints_normalized"]
            assert row["projected_gap_norm"] == src["projected_gap_norm"]
            assert row["nearest_endpoint_distance_norm"] == src["nearest_endpoint_distance_norm"]
            for key in (
                "r2s_cross_scale_min_support_fraction",
                "r2s_cross_scale_min_longest_run_fraction",
                "cross_scale_min_support_contrast",
                "cross_scale_min_run_contrast",
                "negative_control_state",
            ):
                assert row[key] == src[key], f"R2BR_MEASUREMENT_DRIFT:{gap_id}:{key}"
            assert row["review_tier"] == _expected_tier(row, cutoffs), f"R2BR_TIER_MISMATCH:{gap_id}"
            assert row["review_priority_only"] is True
            assert row["human_inspection_required"] is True
            assert row["bridge_candidate_authorized"] is False
            assert row["geometry_materialization_authorized"] is False
            assert row["technical_identity_authorized"] is False
            assert row["structural_identity_authorized"] is False
            assert row["canonical_write_authorized"] is False
            assert row["engineering_authority_effect"] == "NONE"
            if row["review_tier"] == "HIGH_CONTRAST_REVIEW":
                high += 1
            elif row["review_tier"] == "STANDARD_REVIEW":
                standard += 1
            else:
                incomplete += 1

    assert len(seen) == 10
    assert high == int(r2br["high_contrast_review_total"])
    assert standard == int(r2br["standard_review_total"])
    assert incomplete == int(r2br["control_incomplete_review_total"])
    assert high + standard + incomplete == 10

    print("CEW_PWB005_R2BR_BRIDGE_REVIEW_LAYER = PASS")
    print("REGION_COVERAGE = 4/4")
    print("GAP_RETENTION = 10/10")
    print("HIGH_CONTRAST_REVIEW_TOTAL = " + str(high))
    print("STANDARD_REVIEW_TOTAL = " + str(standard))
    print("CONTROL_INCOMPLETE_REVIEW_TOTAL = " + str(incomplete))
    print("REVIEW_PRIORITY_IS_CORRECTNESS_THRESHOLD = false")
    print("HUMAN_INSPECTION_REQUIRED = true")
    print("R2_BRIDGE_CANDIDATE_AUTHORIZED = false")
    print("PWB005_R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")


if __name__ == "__main__":
    validate()
