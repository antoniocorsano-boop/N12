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
ASSET_ROOT = ROOT / ".cew_raster_bridge_review"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}

SUPPORT_MIN = 0.70
RUN_MIN = 0.40
SUPPORT_CONTRAST_MIN = 0.70
RUN_CONTRAST_MIN = 0.40


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


def _tier(gap: dict[str, Any]) -> str:
    if gap.get("negative_control_state") != "NEGATIVE_CONTROL_COMPLETE":
        return "CONTROL_INCOMPLETE_REVIEW"
    values = (
        gap.get("r2s_cross_scale_min_support_fraction"),
        gap.get("r2s_cross_scale_min_longest_run_fraction"),
        gap.get("cross_scale_min_support_contrast"),
        gap.get("cross_scale_min_run_contrast"),
    )
    if any(value is None for value in values):
        return "CONTROL_INCOMPLETE_REVIEW"
    if (
        float(values[0]) >= SUPPORT_MIN
        and float(values[1]) >= RUN_MIN
        and float(values[2]) >= SUPPORT_CONTRAST_MIN
        and float(values[3]) >= RUN_CONTRAST_MIN
    ):
        return "HIGH_CONTRAST_REVIEW"
    return "STANDARD_REVIEW"


def build() -> dict[str, Any]:
    revision = _revision()
    r2sn = _load(R2SN_MANIFEST)
    if r2sn.get("build_revision") != revision:
        raise AssertionError("R2BR_R2SN_REVISION_MISMATCH")
    if r2sn.get("decision_state") != "NEGATIVE_CONTROL_DIAGNOSTIC_COMPLETE_REVIEW_REQUIRED":
        raise AssertionError("R2BR_REQUIRES_R2SN_COMPLETE")
    if r2sn.get("r2_bridge_candidate_authorized") is not False:
        raise AssertionError("R2BR_REQUIRES_BRIDGE_CANDIDATE_BLOCKED")
    if r2sn.get("r2c_scene_adapter_authorized") is not False:
        raise AssertionError("R2BR_REQUIRES_R2C_BLOCKED")

    entries = {row["evidence_region_id"]: row for row in r2sn["regions"]}
    if set(entries) != EXPECTED_REGIONS:
        raise AssertionError("R2BR_REGION_COVERAGE_MISMATCH")

    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    regions = []
    total = 0
    high_total = 0
    standard_total = 0
    incomplete_total = 0
    seen_ids: set[str] = set()

    for region_id in sorted(EXPECTED_REGIONS):
        source = _load(R2SN_ROOT / entries[region_id]["result_filename"])
        if source.get("evidence_region_id") != region_id:
            raise AssertionError(f"R2BR_REGION_ID_MISMATCH:{region_id}")
        if source.get("r2_bridge_candidate_authorized") is not False:
            raise AssertionError(f"R2BR_SOURCE_BRIDGE_AUTHORITY_DRIFT:{region_id}")

        review_rows = []
        for gap in sorted(source["negative_controls"], key=lambda row: row["gap_hypothesis_id"]):
            gap_id = gap["gap_hypothesis_id"]
            if gap_id in seen_ids:
                raise AssertionError(f"R2BR_DUPLICATE_GAP_ID:{gap_id}")
            seen_ids.add(gap_id)
            tier = _tier(gap)
            if tier == "HIGH_CONTRAST_REVIEW":
                high_total += 1
            elif tier == "STANDARD_REVIEW":
                standard_total += 1
            else:
                incomplete_total += 1

            review_rows.append({
                "gap_hypothesis_id": gap_id,
                "candidate_ids": gap["candidate_ids"],
                "bridge_endpoints_normalized": gap["bridge_endpoints_normalized"],
                "projected_gap_norm": gap["projected_gap_norm"],
                "nearest_endpoint_distance_norm": gap["nearest_endpoint_distance_norm"],
                "r2s_cross_scale_min_support_fraction": gap["r2s_cross_scale_min_support_fraction"],
                "r2s_cross_scale_min_longest_run_fraction": gap["r2s_cross_scale_min_longest_run_fraction"],
                "cross_scale_min_support_contrast": gap["cross_scale_min_support_contrast"],
                "cross_scale_min_run_contrast": gap["cross_scale_min_run_contrast"],
                "negative_control_state": gap["negative_control_state"],
                "review_tier": tier,
                "review_priority_only": True,
                "human_inspection_required": True,
                "bridge_candidate_authorized": False,
                "geometry_materialization_authorized": False,
                "technical_identity_authorized": False,
                "structural_identity_authorized": False,
                "canonical_write_authorized": False,
                "engineering_authority_effect": "NONE",
            })

        total += len(review_rows)
        payload = {
            "schema_version": "1.0",
            "review_contract": "CEW_PWB005_R2BR_BRIDGE_REVIEW_LAYER_v1",
            "build_revision": revision,
            "evidence_region_id": region_id,
            "source_code": source["source_code"],
            "source_version_id": source["source_version_id"],
            "source_sha256": source["source_sha256"],
            "page_id": source["page_id"],
            "transform_id": source["transform_id"],
            "review_cutoffs": {
                "support_min": SUPPORT_MIN,
                "run_min": RUN_MIN,
                "support_contrast_min": SUPPORT_CONTRAST_MIN,
                "run_contrast_min": RUN_CONTRAST_MIN,
                "purpose": "HUMAN_REVIEW_PRIORITY_ONLY",
                "correctness_threshold": False,
            },
            "review_rows": review_rows,
            "bridge_candidate_authorized": False,
            "geometry_materialization_authorized": False,
            "r2c_scene_adapter_authorized": False,
            "technical_identity_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
        path = ASSET_ROOT / f"{region_id}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        regions.append({
            "evidence_region_id": region_id,
            "result_filename": path.name,
            "gap_count": len(review_rows),
            "high_contrast_review_count": sum(1 for row in review_rows if row["review_tier"] == "HIGH_CONTRAST_REVIEW"),
            "standard_review_count": sum(1 for row in review_rows if row["review_tier"] == "STANDARD_REVIEW"),
            "control_incomplete_review_count": sum(1 for row in review_rows if row["review_tier"] == "CONTROL_INCOMPLETE_REVIEW"),
        })

    if total != int(r2sn["gap_hypothesis_total"]):
        raise AssertionError(f"R2BR_GAP_RETENTION_MISMATCH:{total}:{r2sn['gap_hypothesis_total']}")

    manifest = {
        "schema_version": "1.0",
        "review_contract": "CEW_PWB005_R2BR_BRIDGE_REVIEW_LAYER_v1",
        "build_revision": revision,
        "region_coverage": "4/4",
        "gap_hypothesis_total": total,
        "high_contrast_review_total": high_total,
        "standard_review_total": standard_total,
        "control_incomplete_review_total": incomplete_total,
        "review_cutoffs": {
            "support_min": SUPPORT_MIN,
            "run_min": RUN_MIN,
            "support_contrast_min": SUPPORT_CONTRAST_MIN,
            "run_contrast_min": RUN_CONTRAST_MIN,
            "purpose": "HUMAN_REVIEW_PRIORITY_ONLY",
            "correctness_threshold": False,
        },
        "regions": regions,
        "decision_state": "BRIDGE_REVIEW_LAYER_READY_HUMAN_INSPECTION_REQUIRED",
        "review_layer_authority": "NONE",
        "bridge_candidate_authorized": False,
        "geometry_materialization_authorized": False,
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R2BR_BRIDGE_REVIEW_LAYER_BUILD = PASS")
    print("REGION_COVERAGE = 4/4")
    print("GAP_HYPOTHESIS_TOTAL = " + str(total))
    print("HIGH_CONTRAST_REVIEW_TOTAL = " + str(high_total))
    print("STANDARD_REVIEW_TOTAL = " + str(standard_total))
    print("CONTROL_INCOMPLETE_REVIEW_TOTAL = " + str(incomplete_total))
    for region in regions:
        result = _load(ASSET_ROOT / region["result_filename"])
        for row in result["review_rows"]:
            print(
                "R2BR_GAP",
                region["evidence_region_id"],
                row["gap_hypothesis_id"],
                "tier=" + row["review_tier"],
                "support=" + str(row["r2s_cross_scale_min_support_fraction"]),
                "run=" + str(row["r2s_cross_scale_min_longest_run_fraction"]),
                "contrast=" + str(row["cross_scale_min_support_contrast"]),
                "run_contrast=" + str(row["cross_scale_min_run_contrast"]),
            )
    print("REVIEW_PRIORITY_IS_CORRECTNESS_THRESHOLD = false")
    print("R2_BRIDGE_CANDIDATE_AUTHORIZED = false")
    print("PWB005_R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


if __name__ == "__main__":
    build()
