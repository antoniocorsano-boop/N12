#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_precision_gcp_audit as precision
import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

CONTRACT = ROOT / "automation/CEW_PR2_STRUCTURAL_GCP_CAPTURE_CONTRACT_v1.json"
PILOT = "OA-N12-G4-COLUMN-PILOT"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["contract"] == "CEW_PR2_STRUCTURAL_GCP_CAPTURE", "contract id drift")
    require(contract["receipt_type"] == precision.RECEIPT_TYPE, "receipt type drift")
    require(contract["authority_effect"] == "NONE", "authority drift")
    require(contract["canonical_write_authorized"] is False, "canonical write drift")
    req = contract["required_behavior"]
    for key in [
        "receipt_type_separate_from_oa", "source_evidence_required", "human_attestation_required",
        "predicted_native_xy_required", "snapped_native_xy_required", "server_computes_residual",
        "preview_before_persist", "explicit_confirm_before_persist", "idempotent_replay",
    ]:
        require(req[key] is True, f"required behavior lost: {key}")
    for key in ["locator_promotion_authorized", "structural_identity_authorized", "canonical_geometry_authorized", "canonical_write_authorized"]:
        require(req[key] is False, f"forbidden authority enabled: {key}")

    expected_source = {
        "source_version_id": "SRC-V1", "page_id": "PAGE-1",
        "evidence_region_id": "REG-1", "source_sha256": "a" * 64,
    }
    payload = {
        "source_evidence": dict(expected_source), "support_id": "16", "feature_type": "COLUMN_CENTER",
        "predicted_native_x_px": 100.0, "predicted_native_y_px": 200.0,
        "snapped_native_x_px": 106.0, "snapped_native_y_px": 208.0,
        "common_x_m": 12.5, "common_y_m": 9.75,
        "selection_method": "HUMAN_EXPLICIT_POINT", "human_attestation": True,
        "navigation_only": True, "canonical_write_authorized": False,
        "canonical_geometry_authorized": False, "structural_identity_authorized": False,
    }
    receipt = precision.build_receipt(
        task_id=PILOT, revision="TEST-REV", reviewer="HUMAN_OPERATOR",
        payload=payload, expected_source=expected_source,
        timestamp="2026-09-01T00:00:00+00:00",
    )
    rp = receipt["payload"]
    require(receipt["receipt_type"] == "CEW_PRECISION_GCP_RECEIPT_V1", "wrong receipt type")
    require(receipt["stage"] == "PR2_STRUCTURAL_GCP_CAPTURE", "wrong precision stage")
    require(receipt["engineering_authority_effect"] == "NONE", "GCP cannot create engineering authority")
    require(receipt["canonical_write_authorized"] is False, "GCP canonical write drift")
    require(abs(rp["residual_dx_px"] - 6.0) < 1e-9, "server residual dx incorrect")
    require(abs(rp["residual_dy_px"] - 8.0) < 1e-9, "server residual dy incorrect")
    require(abs(rp["residual_norm_px"] - 10.0) < 1e-9, "server residual norm incorrect")
    require(rp["gcp_state"] == "HUMAN_VERIFIED_STRUCTURAL_GCP", "GCP state drift")
    require(rp["locator_promotion_authorized"] is False, "single GCP cannot promote locator")

    audit_src = (ROOT / "scripts/cew_precision_gcp_audit.py").read_text(encoding="utf-8")
    require("snapped_x - predicted_x" in audit_src and "math.hypot" in audit_src, "server must compute residual")
    api_src = (ROOT / "scripts/cew_precision_gcp_api.py").read_text(encoding="utf-8")
    require('/api/workbench/precision/gcp' in api_src, "precision API missing")
    require("PRECISION_GCP_ALREADY_PERSISTED" in api_src, "idempotent replay missing")
    oa_api = (ROOT / "scripts/cew_oa_governed_api.py").read_text(encoding="utf-8")
    require("precision_gcp_api.build_router(source_workspace)" in oa_api, "precision router not mounted")
    require("STAGE_ORDER" not in api_src, "precision API must not enter OA stage order")

    runtime = (ROOT / "scripts/cew_pr2_structural_gcp_capture_runtime.py").read_text(encoding="utf-8")
    for marker in [
        "CEW_PR2_STRUCTURAL_GCP_CAPTURE", "Verifica posizione", "canvas-click", "Residuo:",
        "Conferma GCP", "HUMAN_EXPLICIT_POINT", "human_attestation:true",
        "locator_promotion_authorized:false",
    ]:
        require(marker in runtime, f"runtime invariant missing: {marker}")

    # Semantic interaction order: a canvas click may only create a pending preview.
    # Persistence is reachable only through the explicit Confirm GCP handler.
    click_start = runtime.index("function onCanvasClick")
    persist_start = runtime.index("async function persistPending")
    click_src = runtime[click_start:persist_start]
    persist_src = runtime[persist_start:]
    require("pending={{support:s,predicted:p,snapped:snap,dx,dy,norm}}" in click_src, "canvas click must create pending measurement")
    require("Conferma GCP" in click_src, "preview must expose explicit GCP confirmation")
    require(".onclick=persistPending" in click_src, "confirmation must delegate to persistence function")
    require("/api/workbench/precision/gcp" not in click_src, "canvas click must not persist a GCP")
    require("fetch('/api/workbench/precision/gcp'" in persist_src, "precision POST must exist only in persistence phase")
    require("method:'POST'" in persist_src, "precision persistence must be explicit POST")

    compositor = (ROOT / "scripts/cew_enterprise_governed_resume_runtime.py").read_text(encoding="utf-8")
    require("import cew_pr2_structural_gcp_capture_runtime as pr2_runtime" in compositor, "PR-2 compositor import missing")
    require("return pr2_runtime.augment(one_scroll, task)" in compositor, "PR-2 must compose after PR-1")

    html = oa1_runtime.augment(client.build_client(PILOT), PILOT)
    require('data-pr2-runtime="CEW_PR2_STRUCTURAL_GCP_CAPTURE"' in html, "rendered pilot missing PR-2")
    require("Verifica posizione" in html, "GCP capture action missing")
    require('data-canonical-write-authorized="false"' in html, "canonical write boundary lost")

    forbidden = set(contract["forbidden_shortcuts"])
    for item in [
        "CLICK_AUTOMATICALLY_PROMOTES_LOCATOR", "CLIENT_SUPPLIED_RESIDUAL_TRUSTED",
        "PRECISION_GCP_ADVANCES_OA_STAGE", "SINGLE_GCP_VERIFIES_ALL_LOCATORS", "OA6_RELEASE",
    ]:
        require(item in forbidden, f"forbidden shortcut missing: {item}")

    print("CEW_PR2_STRUCTURAL_GCP_CAPTURE = PASS")
    print("RECEIPT_TYPE = CEW_PRECISION_GCP_RECEIPT_V1")
    print("RESIDUAL_COMPUTATION = SERVER_SIDE")
    print("PERSISTENCE = EXPLICIT_CONFIRM_APPEND_ONLY")
    print("LOCATOR_PROMOTION_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
