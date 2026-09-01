#!/usr/bin/env python3
from __future__ import annotations

import inspect
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_ews3_spatial_candidate_review_runtime as ews3_runtime
import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

CONTRACT = ROOT / "automation/CEW_EWS3_SPATIAL_CANDIDATE_REVIEW_CONTRACT_v1.json"
PILOT = "OA-N12-G4-COLUMN-PILOT"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["contract"] == "CEW_EWS3_SPATIAL_CANDIDATE_REVIEW", "contract id drift")
    require(contract["status"] in {"IMPLEMENTED_PENDING_VALIDATION", "EWS3_COMPLETE_PASS"}, "invalid EWS-3 state")
    require(contract["authority_effect"] == "NONE", "spatial navigation cannot create authority")
    require(contract["canonical_write_authorized"] is False, "canonical write drift")
    require(contract["project_material_ready"] is False, "project material release drift")
    model = contract["locator_model"]
    require(model["state"] == "REGISTERED_DERIVED", "locator state drift")
    require(model["derivation"] == "INVERSE_CROSS_VALIDATED_AFFINE_FROM_COMMON_METRIC_XY", "locator derivation drift")
    require(model["registration_validation_state_required"] == "CROSS_VALIDATED", "registration requirement weakened")
    require(model["expected_locator_count"] == 34, "pilot locator coverage drift")
    require(model["canonical_document_geometry"] is False, "viewer locator cannot become canonical geometry")
    require(model["structural_identity_evidence"] is False, "viewer locator cannot become identity evidence")
    require(model["similarity_used_for_position"] is False, "similarity cannot locate source candidates")
    require(model["visual_proximity_used_for_position"] is False, "visual proximity cannot locate source candidates")

    locators, meta = ews3_runtime._load_locators()
    require(meta["registration_validation_state"] == "CROSS_VALIDATED", "live registration is not cross-validated")
    require(meta["source_sheet"] == "TAV-05S" and meta["level_id"] == "G4", "source scope drift")
    require(meta["frame_width_px"] == 12530 and meta["frame_height_px"] == 7016, "TAV-05S frame drift")
    require(meta["locator_count"] == 34 and len(locators) == 34, f"expected 34 G4 locators, got {len(locators)}")
    require(meta["inlier_count"] >= 8, "registration inlier evidence unexpectedly weak")
    expected = {str(i) for i in range(1, 34)} | {"22'"}
    require(set(locators) == expected, f"support locator identity coverage mismatch: {sorted(set(locators)^expected)}")
    for sid, loc in locators.items():
        u, v = float(loc["u_px"]), float(loc["v_px"])
        require(math.isfinite(u) and math.isfinite(v), f"non-finite source locator {sid}")
        require(0 <= u <= meta["frame_width_px"], f"support {sid} u outside source frame: {u}")
        require(0 <= v <= meta["frame_height_px"], f"support {sid} v outside source frame: {v}")
        require(loc["state"] == "REGISTERED_DERIVED", f"support {sid} locator state drift")
        require(loc["navigation_only"] is True, f"support {sid} navigation boundary lost")
        require(loc["structural_identity_authorized"] is False, f"support {sid} identity authority drift")
        require(loc["canonical_geometry_authorized"] is False, f"support {sid} canonical geometry drift")

    loader_source = inspect.getsource(ews3_runtime._load_locators)
    require("REGISTRATION_CSV" in loader_source and "SUPPORTS_CSV" in loader_source, "locator derivation must read governed registration and support coordinates")
    require("metric_x_from_u" in loader_source and "metric_y_from_v" in loader_source, "affine registration coefficients not used")
    require("x_global_m" in loader_source and "y_global_m" in loader_source, "common metric support coordinates not used")
    for forbidden_signal in ("score", "reason_codes", "cew-oa3", "latestSimilarity", "STRONG_SIMILAR", "POSSIBLE_SIMILAR"):
        require(forbidden_signal not in loader_source, f"source locator derivation improperly depends on similarity signal: {forbidden_signal}")

    runtime = (ROOT / "scripts/cew_ews3_spatial_candidate_review_runtime.py").read_text(encoding="utf-8")
    for marker in [
        "CEW_EWS3_SPATIAL_CANDIDATE_REVIEW",
        "REGISTERED_DERIVED",
        "imageToViewportRectangle",
        "imageToViewportCoordinates",
        "Mostra sulla tavola",
        "Posizione registrata sulla fonte",
        "navigation_only:true",
        "canonical_geometry_authorized:false",
        "structural_identity_authorized:false",
        "MutationObserver",
    ]:
        require(marker in runtime, f"runtime invariant missing: {marker}")

    resume = (ROOT / "scripts/cew_enterprise_governed_resume_runtime.py").read_text(encoding="utf-8")
    require("import cew_ews3_spatial_candidate_review_runtime as ews3_runtime" in resume, "EWS-3 compositor import missing")
    require("focused = ews2_guard_runtime.augment(ews2_runtime.augment(rendered, task), task)" in resume, "EWS-2 visibility guard composition missing")
    require("spatial = ews3_runtime.augment(focused, task)" in resume, "EWS-3 must compose after EWS-2 visibility guard")
    require(resume.find("focused = ews2_guard_runtime.augment") < resume.find("spatial = ews3_runtime.augment"), "EWS-3 presentation order drift")

    html = oa1_runtime.augment(client.build_client(PILOT), PILOT)
    require('data-ews3-runtime="CEW_EWS3_SPATIAL_CANDIDATE_REVIEW"' in html, "rendered pilot missing EWS-3")
    require("12530" in html and "7016" in html, "source frame metadata not embedded")
    require("\"locator_count\":34" in html, "locator coverage not embedded")
    require("#ews3SourceMarker" in html, "source marker UI missing")
    require("Mostra sulla tavola" in html, "manual source refocus action missing")
    require('data-canonical-write-authorized="false"' in html, "canonical write boundary lost")

    forbidden = set(contract["forbidden_shortcuts"])
    for item in {
        "SIMILARITY_SCORE_CREATES_POSITION",
        "VISUAL_PROXIMITY_CREATES_POSITION",
        "SOURCE_LOCATOR_CREATES_STRUCTURAL_IDENTITY",
        "SOURCE_LOCATOR_BECOMES_CANONICAL_GEOMETRY",
        "UNREGISTERED_CANDIDATE_AUTO_FOCUS",
        "AUTO_CONFIRM_ON_FOCUS",
        "OA6_RELEASE",
        "CANONICAL_WRITE_FROM_SPATIAL_REVIEW",
    }:
        require(item in forbidden, f"forbidden shortcut missing: {item}")

    print("CEW_EWS3_SPATIAL_CANDIDATE_REVIEW = PASS")
    print(f"SOURCE = {meta['source_sheet']} / {meta['level_id']}")
    print(f"SOURCE_FRAME = {meta['frame_width_px']}x{meta['frame_height_px']}")
    print(f"REGISTRATION = {meta['registration_validation_state']} / inliers={meta['inlier_count']}")
    print(f"LOCATOR_COVERAGE = {len(locators)}/34")
    print("LOCATOR_DERIVATION = REGISTERED_XY_ONLY_NO_SIMILARITY_SIGNAL")
    print("LOCATOR_ROLE = VIEWER_EVIDENCE_NAVIGATION_ONLY")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_GEOMETRY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
