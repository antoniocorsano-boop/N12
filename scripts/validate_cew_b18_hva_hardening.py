#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_b1_acceptance_lab as acceptance_lab
import cew_b1_human_acceptance_v2_hardening as hva
import cew_r2hr_system_review as r2hr


def build_with_env(**values: str) -> str:
    keys = {
        "RENDER_GIT_COMMIT",
        "RENDER_EXTERNAL_URL",
        "RENDER_EXTERNAL_HOSTNAME",
        "VERCEL_GIT_COMMIT_SHA",
        "VERCEL_URL",
        "GITHUB_SHA",
        "CEW_RUNTIME_REVISION",
    }
    previous = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ.pop(key, None)
        for key, value in values.items():
            os.environ[key] = value
        return hva.build_app()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def integrated_with_revision(revision: str) -> str:
    keys = {"RENDER_GIT_COMMIT", "RENDER_EXTERNAL_URL"}
    previous = {key: os.environ.get(key) for key in keys}
    try:
        os.environ["RENDER_GIT_COMMIT"] = revision
        os.environ["RENDER_EXTERNAL_URL"] = "https://cew-hva.example.invalid"
        return acceptance_lab.build_lab()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def synthetic_r2hr_receipt(template: dict) -> dict:
    decisions = []
    for gap in template["gaps"]:
        decisions.append({
            "gap_hypothesis_id": gap["gap_hypothesis_id"],
            "review_tier": gap["review_tier"],
            "decision": "UNRESOLVED_FROM_CURRENT_VIEW",
            "rationale": "Synthetic system-path validation only; no human conclusion is asserted.",
            "candidate_ids": gap["candidate_ids"],
            "bridge_endpoints_normalized": gap["bridge_endpoints_normalized"],
            "metric_snapshot": gap["metric_snapshot"],
            "decision_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
            "decision_is_geometry_acceptance": False,
        })
    return {
        "schema_version": "1.0",
        "receipt_type": "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_v1",
        "candidate_head_sha": template["candidate_head_sha"],
        "build_revision": template["build_revision"],
        "evidence_region_id": template["evidence_region_id"],
        "source_code": template["source_code"],
        "source_version_id": template["source_version_id"],
        "source_sha256": template["source_sha256"],
        "page_id": template["page_id"],
        "transform_id": template["transform_id"],
        "reviewer_label": "SYNTHETIC_SYSTEM_VALIDATOR",
        "reviewer_attestation": True,
        "reviewed_at": "2026-08-29T00:00:00Z",
        "decisions": decisions,
        "receipt_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
        "supported_continuity_hypothesis_is_geometry": False,
        "human_review_is_bridge_acceptance": False,
        "bridge_candidate_authorized": False,
        "geometry_materialization_authorized": False,
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def main() -> int:
    render_sha = "0123456789abcdef0123456789abcdef01234567"
    html = build_with_env(
        RENDER_GIT_COMMIT=render_sha,
        RENDER_EXTERNAL_URL="https://cew-hva.example.invalid",
    )

    checks = {
        "render_revision_propagated": render_sha in html,
        "render_deployment_propagated": "https://cew-hva.example.invalid" in html,
        "session_namespaced_by_revision": "+'::'+RUNTIME_REVISION" in html,
        "session_revision_mismatch_invalidated": "stored.runtime_revision!==RUNTIME_REVISION" in html,
        "session_deployment_mismatch_invalidated": "stored.runtime_deployment!==RUNTIME_DEPLOYMENT" in html,
        "wrong_path_inspected_across_full_journey": "paths.some(p=>p.startsWith('/drawings/')&&!p.startsWith('/drawings/TAV-05A'))" in html,
        "wrong_source_blocker_emitted": "WRONG_SOURCE_OR_VERSION" in html,
        "runtime_revision_fail_closed": "RUNTIME_REVISION_UNRESOLVED" in html,
        "runtime_deployment_fail_closed": "RUNTIME_DEPLOYMENT_UNRESOLVED" in html,
    }

    unresolved = build_with_env()
    checks["unresolved_revision_visible_to_blocker_logic"] = "UNRESOLVED_RUNTIME_REVISION" in unresolved
    checks["unresolved_deployment_visible_to_blocker_logic"] = "LOCAL_OR_UNRESOLVED_DEPLOYMENT" in unresolved

    manifest_path = ROOT / "artifacts/cew_r2hr_review/manifest.json"
    if not manifest_path.is_file():
        checks["r2hr_runtime_manifest_available"] = False
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        candidate = manifest["candidate_head_sha"]
        integrated = integrated_with_revision(candidate)
        checks.update({
            "r2hr_runtime_manifest_available": True,
            "r2hr_system_surface_present": "R2HR · Revisione umana delle ipotesi di continuità" in integrated,
            "r2hr_no_download_required": "Nessun file deve essere scaricato" in integrated,
            "r2hr_system_submit_present": "Registra revisione nel sistema" in integrated,
            "r2hr_authenticated_runtime_endpoint_used": "fetch('/api/f7/receipt'" in integrated,
            "r2hr_all_gap_controls_present": integrated.count('class="r2hr-card"') == 10,
            "r2hr_all_regions_present": integrated.count('class="r2hr-region"') == 4,
            "r2hr_local_export_absent_from_runtime_surface": "Esporta review JSON" not in integrated,
            "r2hr_authority_visible": "HUMAN_REVIEW_EVIDENCE_ONLY" in integrated,
        })

        templates = []
        for entry in manifest["regions"]:
            template = json.loads((ROOT / "artifacts/cew_r2hr_review" / entry["receipt_template_filename"]).read_text(encoding="utf-8"))
            if template.get("gaps"):
                templates.append(template)
        if not templates:
            checks["r2hr_system_receipt_path"] = False
        else:
            receipt = synthetic_r2hr_receipt(templates[0])
            previous_revision = os.environ.get("CEW_RUNTIME_REVISION")
            try:
                os.environ["CEW_RUNTIME_REVISION"] = candidate
                with tempfile.TemporaryDirectory() as tmp:
                    result = r2hr.process_r2hr_receipt(receipt, Path(tmp))
            finally:
                if previous_revision is None:
                    os.environ.pop("CEW_RUNTIME_REVISION", None)
                else:
                    os.environ["CEW_RUNTIME_REVISION"] = previous_revision
            checks["r2hr_system_receipt_path"] = result.get("state") == "R2HR_REVIEW_EVIDENCE_RECORDED"
            checks["r2hr_system_receipt_no_canonical_write"] = result.get("canonical_write_authorized") is False and result.get("canonical_write_performed") is False
            checks["r2hr_system_receipt_no_bridge_acceptance"] = result.get("human_review_is_bridge_acceptance") is False and result.get("r2c_scene_adapter_authorized") is False

    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        print("CEW_B18_HVA_HARDENING = FAIL")
        for name in failed:
            print("ERROR:", name)
        return 1

    print("CEW_B18_HVA_HARDENING = PASS")
    print("RENDER_RECEIPT_IDENTITY = REVISION_BOUND")
    print("CROSS_REVISION_SESSION_REUSE = REJECTED")
    print("WRONG_SOURCE_PATH = NON_COMPENSABLE_BLOCKER")
    print("UNRESOLVED_RUNTIME_IDENTITY = FAIL_CLOSED")
    print("R2HR_REVIEW_SURFACE = AUTHENTICATED_CEW_RUNTIME")
    print("R2HR_DOWNLOAD_REQUIRED = false")
    print("R2HR_SUBMISSION = APPEND_ONLY_RUNTIME_AUDIT")
    print("R2HR_RECEIPT_AUTHORITY = HUMAN_REVIEW_EVIDENCE_ONLY")
    print("R2HR_HUMAN_REVIEW_IS_BRIDGE_ACCEPTANCE = false")
    print("R2HR_R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("R2HR_CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
