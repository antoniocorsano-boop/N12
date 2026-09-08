#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any

import build_cew_raster_support_continuity as r2s

ROOT = Path(__file__).resolve().parents[1]
R2_ROOT = ROOT / ".cew_raster_geometry_candidates"
R2_MANIFEST = R2_ROOT / "manifest.json"
R2S_ROOT = ROOT / ".cew_raster_support_continuity"
R2S_MANIFEST = R2S_ROOT / "manifest.json"
ASSET_ROOT = ROOT / ".cew_raster_support_negative_controls"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}
CONTROL_OFFSET_PX = {200: 12.0, 300: 18.0}


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ).strip()


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"R2SN_REQUIRED_ARTIFACT_MISSING:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _shifted_control(
    a_norm: list[float],
    b_norm: list[float],
    width: int,
    height: int,
    offset_px: float,
    sign: float,
) -> tuple[list[float], list[float]] | None:
    ax = float(a_norm[0]) * (width - 1)
    ay = float(a_norm[1]) * (height - 1)
    bx = float(b_norm[0]) * (width - 1)
    by = float(b_norm[1]) * (height - 1)
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        return None
    nx, ny = -dy / length, dx / length
    sx, sy = sign * offset_px * nx, sign * offset_px * ny
    points_px = ((ax + sx, ay + sy), (bx + sx, by + sy))
    if any(x < 0 or y < 0 or x > width - 1 or y > height - 1 for x, y in points_px):
        return None
    return (
        [round(points_px[0][0] / (width - 1), 8), round(points_px[0][1] / (height - 1), 8)],
        [round(points_px[1][0] / (width - 1), 8), round(points_px[1][1] / (height - 1), 8)],
    )


def _control_measurements(
    gap: dict[str, Any],
    image: dict[str, Any],
    dpi: int,
) -> dict[str, Any]:
    a_norm = gap["bridge_endpoints_normalized"]["a"]
    b_norm = gap["bridge_endpoints_normalized"]["b"]
    controls = []
    for label, sign in (("PLUS", 1.0), ("MINUS", -1.0)):
        shifted = _shifted_control(
            a_norm,
            b_norm,
            image["width_px"],
            image["height_px"],
            CONTROL_OFFSET_PX[dpi],
            sign,
        )
        if shifted is None:
            controls.append({
                "side": label,
                "available": False,
                "offset_px": CONTROL_OFFSET_PX[dpi],
            })
            continue
        measurement = r2s._sample_support(
            shifted[0],
            shifted[1],
            image["width_px"],
            image["height_px"],
            image["gray"],
            image["otsu_threshold"],
            dpi,
        )
        controls.append({
            "side": label,
            "available": True,
            "offset_px": CONTROL_OFFSET_PX[dpi],
            "endpoints_normalized": {"a": shifted[0], "b": shifted[1]},
            **measurement,
        })

    available = [row for row in controls if row["available"]]
    if not available:
        return {
            "dpi": dpi,
            "control_state": "CONTROL_INCOMPLETE",
            "controls": controls,
            "control_support_fraction": None,
            "control_longest_supported_run_fraction": None,
        }
    return {
        "dpi": dpi,
        "control_state": "NEGATIVE_CONTROL_COMPLETE",
        "controls": controls,
        "control_support_fraction": round(max(row["support_fraction"] for row in available), 8),
        "control_longest_supported_run_fraction": round(
            max(row["longest_supported_run_fraction"] for row in available), 8
        ),
    }


def _raster_for_region(r2_entry: dict[str, Any], r2_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return r2s._region_raster_inputs(r2_entry, r2_result)


def build() -> dict[str, Any]:
    revision = _revision()
    r2 = _load(R2_MANIFEST)
    r2s_manifest = _load(R2S_MANIFEST)
    if r2.get("build_revision") != revision or r2s_manifest.get("build_revision") != revision:
        raise AssertionError("R2SN_INPUT_REVISION_MISMATCH")
    if r2s_manifest.get("decision_state") != "RASTER_SUPPORT_DIAGNOSTIC_COMPLETE_REVIEW_REQUIRED":
        raise AssertionError("R2SN_REQUIRES_R2S_COMPLETE")
    if r2s_manifest.get("r2c_scene_adapter_authorized") is not False:
        raise AssertionError("R2SN_REQUIRES_R2C_BLOCKED")

    r2_entries = {row["evidence_region_id"]: row for row in r2["region_entries"]}
    r2s_entries = {row["evidence_region_id"]: row for row in r2s_manifest["regions"]}
    if set(r2_entries) != EXPECTED_REGIONS or set(r2s_entries) != EXPECTED_REGIONS:
        raise AssertionError("R2SN_REGION_COVERAGE_MISMATCH")

    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    regions = []
    gap_total = 0
    complete_total = 0
    incomplete_total = 0

    for region_id in sorted(EXPECTED_REGIONS):
        r2_entry = r2_entries[region_id]
        r2_result = _load(R2_ROOT / r2_entry["result_filename"])
        r2s_result = _load(R2S_ROOT / r2s_entries[region_id]["result_filename"])
        raster = _raster_for_region(r2_entry, r2_result)
        gap_rows = []

        for gap in sorted(r2s_result["gap_hypotheses"], key=lambda row: row["gap_hypothesis_id"]):
            scale_rows = {}
            complete = True
            support_contrasts = []
            run_contrasts = []
            for dpi in (200, 300):
                control = _control_measurements(gap, raster[str(dpi)], dpi)
                actual = gap[f"scale_{dpi}"]
                if control["control_state"] != "NEGATIVE_CONTROL_COMPLETE":
                    complete = False
                    scale_rows[str(dpi)] = {
                        "actual_support_fraction": actual["support_fraction"],
                        "actual_longest_supported_run_fraction": actual["longest_supported_run_fraction"],
                        **control,
                        "support_contrast": None,
                        "run_contrast": None,
                    }
                    continue
                support_contrast = round(
                    actual["support_fraction"] - control["control_support_fraction"], 8
                )
                run_contrast = round(
                    actual["longest_supported_run_fraction"]
                    - control["control_longest_supported_run_fraction"],
                    8,
                )
                support_contrasts.append(support_contrast)
                run_contrasts.append(run_contrast)
                scale_rows[str(dpi)] = {
                    "actual_support_fraction": actual["support_fraction"],
                    "actual_longest_supported_run_fraction": actual["longest_supported_run_fraction"],
                    **control,
                    "support_contrast": support_contrast,
                    "run_contrast": run_contrast,
                }

            state = "NEGATIVE_CONTROL_COMPLETE" if complete else "CONTROL_INCOMPLETE"
            if complete:
                complete_total += 1
                cross_support_contrast = round(min(support_contrasts), 8)
                cross_run_contrast = round(min(run_contrasts), 8)
            else:
                incomplete_total += 1
                cross_support_contrast = None
                cross_run_contrast = None

            gap_rows.append({
                "gap_hypothesis_id": gap["gap_hypothesis_id"],
                "candidate_ids": gap["candidate_ids"],
                "projected_gap_norm": gap["projected_gap_norm"],
                "nearest_endpoint_distance_norm": gap["nearest_endpoint_distance_norm"],
                "bridge_endpoints_normalized": gap["bridge_endpoints_normalized"],
                "r2s_cross_scale_min_support_fraction": gap["cross_scale_min_support_fraction"],
                "r2s_cross_scale_min_longest_run_fraction": gap["cross_scale_min_longest_run_fraction"],
                "scale_200": scale_rows["200"],
                "scale_300": scale_rows["300"],
                "negative_control_state": state,
                "cross_scale_min_support_contrast": cross_support_contrast,
                "cross_scale_min_run_contrast": cross_run_contrast,
                "threshold_classification": "NOT_DEFINED",
                "bridge_candidate_authorized": False,
                "geometry_materialization_authorized": False,
                "technical_identity_authorized": False,
                "structural_identity_authorized": False,
            })

        region_payload = {
            "schema_version": "1.0",
            "evidence_region_id": region_id,
            "source_code": r2s_result["source_code"],
            "source_version_id": r2s_result["source_version_id"],
            "source_sha256": r2s_result["source_sha256"],
            "page_id": r2s_result["page_id"],
            "transform_id": r2s_result["transform_id"],
            "gap_count": len(gap_rows),
            "negative_controls": gap_rows,
            "control_offset_px": {"200": CONTROL_OFFSET_PX[200], "300": CONTROL_OFFSET_PX[300]},
            "threshold_policy": "NOT_DEFINED_MEASURE_FIRST",
            "negative_control_authority": "NONE",
            "gap_support_contrast_is_geometry": False,
            "r2_bridge_candidate_authorized": False,
            "r2c_scene_adapter_authorized": False,
            "technical_identity_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
        region_path = ASSET_ROOT / f"{region_id}.json"
        region_path.write_text(json.dumps(region_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        regions.append({
            "evidence_region_id": region_id,
            "result_filename": region_path.name,
            "result_sha256": r2s._sha256(region_path),
            "gap_count": len(gap_rows),
            "complete_control_count": sum(
                1 for row in gap_rows if row["negative_control_state"] == "NEGATIVE_CONTROL_COMPLETE"
            ),
            "incomplete_control_count": sum(
                1 for row in gap_rows if row["negative_control_state"] == "CONTROL_INCOMPLETE"
            ),
        })
        gap_total += len(gap_rows)

    if gap_total != int(r2s_manifest["gap_hypothesis_total"]):
        raise AssertionError(f"R2SN_GAP_INVENTORY_MISMATCH:{gap_total}:{r2s_manifest['gap_hypothesis_total']}")

    manifest = {
        "schema_version": "1.0",
        "diagnostic_contract": "CEW_PWB005_R2SN_GAP_NEGATIVE_CONTROL_v1",
        "build_revision": revision,
        "region_coverage": "4/4",
        "gap_hypothesis_total": gap_total,
        "negative_control_complete_total": complete_total,
        "control_incomplete_total": incomplete_total,
        "control_offset_px": {"200": CONTROL_OFFSET_PX[200], "300": CONTROL_OFFSET_PX[300]},
        "control_baseline": "MAX_VALID_LATERAL_CONTROL_PER_SCALE",
        "threshold_policy": "NOT_DEFINED_MEASURE_FIRST",
        "regions": regions,
        "decision_state": "NEGATIVE_CONTROL_DIAGNOSTIC_COMPLETE_REVIEW_REQUIRED",
        "negative_control_authority": "NONE",
        "gap_support_contrast_is_geometry": False,
        "r2_bridge_candidate_authorized": False,
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R2SN_GAP_NEGATIVE_CONTROL_BUILD = PASS")
    print("REGION_COVERAGE = 4/4")
    print("GAP_HYPOTHESIS_TOTAL = " + str(gap_total))
    print("NEGATIVE_CONTROL_COMPLETE_TOTAL = " + str(complete_total))
    print("CONTROL_INCOMPLETE_TOTAL = " + str(incomplete_total))
    for region in regions:
        result = _load(ASSET_ROOT / region["result_filename"])
        for gap in result["negative_controls"]:
            print(
                "R2SN_GAP",
                region["evidence_region_id"],
                gap["gap_hypothesis_id"],
                "r2s_support=" + str(gap["r2s_cross_scale_min_support_fraction"]),
                "r2s_run=" + str(gap["r2s_cross_scale_min_longest_run_fraction"]),
                "contrast=" + str(gap["cross_scale_min_support_contrast"]),
                "run_contrast=" + str(gap["cross_scale_min_run_contrast"]),
                "gap=" + str(gap["projected_gap_norm"]),
                "distance=" + str(gap["nearest_endpoint_distance_norm"]),
                "state=" + gap["negative_control_state"],
            )
    print("THRESHOLD_POLICY = NOT_DEFINED_MEASURE_FIRST")
    print("GAP_SUPPORT_CONTRAST_IS_GEOMETRY = false")
    print("R2_BRIDGE_CANDIDATE_AUTHORIZED = false")
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


if __name__ == "__main__":
    build()
