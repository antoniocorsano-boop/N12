#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_raster_support_negative_controls"
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


def main() -> int:
    if not MANIFEST.is_file():
        raise AssertionError("R2SN_MANIFEST_MISSING")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["diagnostic_contract"] == "CEW_PWB005_R2SN_GAP_NEGATIVE_CONTROL_v1"
    assert data["build_revision"] == _revision()
    assert data["region_coverage"] == "4/4"
    assert data["gap_hypothesis_total"] == 10
    assert data["negative_control_complete_total"] + data["control_incomplete_total"] == 10
    assert data["control_offset_px"] == {"200": 12.0, "300": 18.0}
    assert data["control_baseline"] == "MAX_VALID_LATERAL_CONTROL_PER_SCALE"
    assert data["threshold_policy"] == "NOT_DEFINED_MEASURE_FIRST"
    assert data["decision_state"] == "NEGATIVE_CONTROL_DIAGNOSTIC_COMPLETE_REVIEW_REQUIRED"
    assert data["negative_control_authority"] == "NONE"
    assert data["gap_support_contrast_is_geometry"] is False
    assert data["r2_bridge_candidate_authorized"] is False
    assert data["r2c_scene_adapter_authorized"] is False
    assert data["technical_identity_authorized"] is False
    assert data["structural_identity_authorized"] is False
    assert data["canonical_write_authorized"] is False
    assert data["engineering_authority_effect"] == "NONE"

    regions = data["regions"]
    assert {row["evidence_region_id"] for row in regions} == EXPECTED_REGIONS
    assert sum(row["gap_count"] for row in regions) == 10
    assert sum(row["complete_control_count"] for row in regions) == data["negative_control_complete_total"]
    assert sum(row["incomplete_control_count"] for row in regions) == data["control_incomplete_total"]

    seen_gap_ids: set[str] = set()
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
        assert result["gap_count"] == row["gap_count"] == len(result["negative_controls"])
        assert result["control_offset_px"] == {"200": 12.0, "300": 18.0}
        assert result["threshold_policy"] == "NOT_DEFINED_MEASURE_FIRST"
        assert result["negative_control_authority"] == "NONE"
        assert result["gap_support_contrast_is_geometry"] is False
        assert result["r2_bridge_candidate_authorized"] is False
        assert result["r2c_scene_adapter_authorized"] is False
        assert result["technical_identity_authorized"] is False
        assert result["structural_identity_authorized"] is False
        assert result["canonical_write_authorized"] is False
        assert result["engineering_authority_effect"] == "NONE"

        for gap in result["negative_controls"]:
            gap_id = gap["gap_hypothesis_id"]
            assert gap_id not in seen_gap_ids
            seen_gap_ids.add(gap_id)
            assert gap["candidate_ids"] == sorted(gap["candidate_ids"])
            assert len(gap["candidate_ids"]) == 2
            assert 0.0 < gap["projected_gap_norm"] <= 0.05
            assert gap["nearest_endpoint_distance_norm"] > 0.0
            assert 0.0 <= gap["r2s_cross_scale_min_support_fraction"] <= 1.0
            assert 0.0 <= gap["r2s_cross_scale_min_longest_run_fraction"] <= 1.0
            assert gap["threshold_classification"] == "NOT_DEFINED"
            assert gap["bridge_candidate_authorized"] is False
            assert gap["geometry_materialization_authorized"] is False
            assert gap["technical_identity_authorized"] is False
            assert gap["structural_identity_authorized"] is False

            complete = gap["negative_control_state"] == "NEGATIVE_CONTROL_COMPLETE"
            if not complete:
                assert gap["negative_control_state"] == "CONTROL_INCOMPLETE"
                assert gap["cross_scale_min_support_contrast"] is None
                assert gap["cross_scale_min_run_contrast"] is None
            support_contrasts = []
            run_contrasts = []
            for dpi in (200, 300):
                scale = gap[f"scale_{dpi}"]
                assert scale["dpi"] == dpi
                assert scale["control_state"] in {"NEGATIVE_CONTROL_COMPLETE", "CONTROL_INCOMPLETE"}
                controls = scale["controls"]
                assert len(controls) == 2
                assert {control["side"] for control in controls} == {"PLUS", "MINUS"}
                for control in controls:
                    assert control["offset_px"] == (12.0 if dpi == 200 else 18.0)
                    if control["available"]:
                        assert 0.0 <= control["support_fraction"] <= 1.0
                        assert 0.0 <= control["longest_supported_run_fraction"] <= 1.0
                        for point in control["endpoints_normalized"].values():
                            assert 0.0 <= point[0] <= 1.0
                            assert 0.0 <= point[1] <= 1.0
                if scale["control_state"] == "NEGATIVE_CONTROL_COMPLETE":
                    available = [control for control in controls if control["available"]]
                    assert available
                    expected_support = max(control["support_fraction"] for control in available)
                    expected_run = max(control["longest_supported_run_fraction"] for control in available)
                    assert scale["control_support_fraction"] == expected_support
                    assert scale["control_longest_supported_run_fraction"] == expected_run
                    assert scale["support_contrast"] == round(
                        scale["actual_support_fraction"] - expected_support, 8
                    )
                    assert scale["run_contrast"] == round(
                        scale["actual_longest_supported_run_fraction"] - expected_run, 8
                    )
                    assert -1.0 <= scale["support_contrast"] <= 1.0
                    assert -1.0 <= scale["run_contrast"] <= 1.0
                    support_contrasts.append(scale["support_contrast"])
                    run_contrasts.append(scale["run_contrast"])
                else:
                    assert scale["control_support_fraction"] is None
                    assert scale["control_longest_supported_run_fraction"] is None
                    assert scale["support_contrast"] is None
                    assert scale["run_contrast"] is None
            if complete:
                assert len(support_contrasts) == 2 and len(run_contrasts) == 2
                assert gap["cross_scale_min_support_contrast"] == min(support_contrasts)
                assert gap["cross_scale_min_run_contrast"] == min(run_contrasts)
                assert -1.0 <= gap["cross_scale_min_support_contrast"] <= 1.0
                assert -1.0 <= gap["cross_scale_min_run_contrast"] <= 1.0

    assert len(seen_gap_ids) == 10

    print("CEW_PWB005_R2SN_GAP_NEGATIVE_CONTROL = PASS")
    print("REGION_COVERAGE = 4/4")
    print("GAP_HYPOTHESIS_TOTAL = 10")
    print("NEGATIVE_CONTROL_COMPLETE_TOTAL = " + str(data["negative_control_complete_total"]))
    print("CONTROL_INCOMPLETE_TOTAL = " + str(data["control_incomplete_total"]))
    for row in sorted(regions, key=lambda item: item["evidence_region_id"]):
        result = json.loads((ASSET_ROOT / row["result_filename"]).read_text(encoding="utf-8"))
        for gap in result["negative_controls"]:
            print(
                "R2SN_VALIDATED",
                row["evidence_region_id"],
                gap["gap_hypothesis_id"],
                "support=" + str(gap["r2s_cross_scale_min_support_fraction"]),
                "run=" + str(gap["r2s_cross_scale_min_longest_run_fraction"]),
                "contrast=" + str(gap["cross_scale_min_support_contrast"]),
                "run_contrast=" + str(gap["cross_scale_min_run_contrast"]),
                "state=" + gap["negative_control_state"],
            )
    print("THRESHOLD_POLICY = NOT_DEFINED_MEASURE_FIRST")
    print("NEGATIVE_CONTROL_AUTHORITY = NONE")
    print("GAP_SUPPORT_CONTRAST_IS_GEOMETRY = false")
    print("R2_BRIDGE_CANDIDATE_AUTHORIZED = false")
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
