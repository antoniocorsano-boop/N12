#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation/CEW_PROFESSIONAL_REVIEW_PRECISION_CONTRACT_v1.json"
BASELINE = ROOT / "docs/DESIGN/CEW_PROFESSIONAL_REVIEW_PRECISION_BASELINE_v1.md"
GCP = ROOT / "data/canonical/STRUCTURAL_GCP_REGISTER_v1.csv"
OUT_CSV = ROOT / "artifacts/cew_precision_registration/TAV05S_G4_GLOBAL_PREDICTIONS_v1.csv"
OUT_JSON = ROOT / "artifacts/cew_precision_registration/TAV05S_G4_PRECISION_DIAGNOSTICS_v1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["contract"] == "CEW_PROFESSIONAL_REVIEW_PRECISION", "contract id drift")
    require(contract["authority_effect"] == "NONE", "authority drift")
    require(contract["canonical_write_authorized"] is False, "canonical write drift")
    require(contract["project_material_ready"] is False, "project material drift")
    require(contract["ux_gate"]["single_vertical_scroll_owner"] is True, "single scroll owner must be frozen")
    require(contract["ux_gate"]["nested_vertical_scroll_forbidden"] is True, "nested scroll prohibition missing")
    require(contract["spatial_precision_gate"]["global_registration_is_verified_locator"] is False, "global registration cannot equal verified locator")
    require(contract["spatial_precision_gate"]["residual_threshold_frozen"] is False, "threshold cannot be frozen before residual measurement")
    require(contract["spatial_precision_gate"]["sift_inlier_is_structural_gcp"] is False, "SIFT feature cannot become structural GCP")

    baseline = BASELINE.read_text(encoding="utf-8")
    for marker in [
        "UX_GATE",
        "SPATIAL_PRECISION_GATE",
        "STRUCTURAL_GCP",
        "LOCAL RESIDUAL MODEL",
        "DOCUMENT SNAP",
        "VERIFIED_LOCATOR",
        "global registration != verified locator",
        "PR-0",
    ]:
        require(marker in baseline, f"baseline marker missing: {marker}")

    with GCP.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fields = fh.readline if False else None
    require(rows == [], "PR-0 must not invent structural GCP rows")
    header = GCP.read_text(encoding="utf-8").splitlines()[0].split(",")
    for field in ["gcp_id", "feature_type", "support_id", "native_x_px", "native_y_px", "common_x_m", "common_y_m", "selection_method", "validation_state", "reviewer", "receipt_id"]:
        require(field in header, f"STRUCTURAL_GCP field missing: {field}")

    subprocess.run([sys.executable, str(ROOT / "scripts/build_cew_precision_diagnostics.py")], check=True, cwd=ROOT)
    require(OUT_CSV.is_file(), "global prediction register not built")
    require(OUT_JSON.is_file(), "precision diagnostics summary not built")

    with OUT_CSV.open(newline="", encoding="utf-8") as fh:
        predictions = list(csv.DictReader(fh))
    require(len(predictions) == 34, f"expected 34 predictions, got {len(predictions)}")
    expected = {str(i) for i in range(1, 34)} | {"22'"}
    require({r["support_id"] for r in predictions} == expected, "support identity coverage drift")
    for row in predictions:
        require(row["locator_state"] == "REGISTERED_GLOBAL_NEEDS_LOCAL_QA", f"premature locator state for support {row['support_id']}")
        require(row["snapped_native_x_px"] == "" and row["snapped_native_y_px"] == "", "PR-0 must not invent snapped coordinates")
        require(row["residual_norm_px"] == "", "PR-0 must not invent residuals")
        require(row["navigation_only"] == "true", "navigation boundary drift")
        require(row["structural_identity_authorized"] == "false", "identity authority drift")
        require(row["canonical_geometry_authorized"] == "false", "canonical geometry drift")

    summary = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    require(summary["support_count"] == 34, "summary support count drift")
    require(summary["structural_gcp_count"] == 0, "structural GCP count must remain zero until captured")
    require(summary["snapped_locator_count"] == 0, "snapped locator count must remain zero")
    require(summary["human_verified_locator_count"] == 0, "verified locator count must remain zero")
    require(summary["residual_distribution_available"] is False, "residual distribution cannot exist before GCP/snap")
    require(summary["residual_threshold_frozen"] is False, "threshold cannot be frozen")
    require(summary["current_locator_state"] == "REGISTERED_GLOBAL_NEEDS_LOCAL_QA", "diagnostic state drift")

    forbidden = set(contract["forbidden_shortcuts"])
    for item in [
        "MARKER_LOOKS_CLOSE_THEREFORE_VERIFIED",
        "GLOBAL_AFFINE_EQUALS_PRECISE_OBJECT_BINDING",
        "SIFT_FEATURE_EQUALS_STRUCTURAL_GCP",
        "NESTED_VERTICAL_SCROLL",
        "OA6_RELEASE",
    ]:
        require(item in forbidden, f"forbidden shortcut missing: {item}")

    print("CEW_PROFESSIONAL_REVIEW_PRECISION_BASELINE = PASS")
    print("UX_GATE_MODEL = ONE_SCROLL_OWNER")
    print("GLOBAL_PREDICTIONS = 34/34")
    print("STRUCTURAL_GCP = 0")
    print("RESIDUAL_DISTRIBUTION = NOT_AVAILABLE")
    print("RESIDUAL_THRESHOLD = NOT_FROZEN")
    print("LOCATOR_STATE = REGISTERED_GLOBAL_NEEDS_LOCAL_QA")
    print("NEXT = STRUCTURAL_GCP_CAPTURE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
