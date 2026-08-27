#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json"
QUEUE = ROOT / "automation/CEW_PRODUCT_TRANSFORMATION_QUEUE_v1.json"
RECON = ROOT / "automation/CEW_PRODUCT_STATE_RECONCILIATION_v1.json"
ENGINEERING_STATE = ROOT / "knowledge/CURRENT_STATE.json"
ENGINEERING_QUEUE = ROOT / "automation/N12_WORK_QUEUE_v1.json"
DEPLOY_RUNTIME = ROOT / "deploy/cew_user_runtime.py"
AUDIT_STORE = ROOT / "scripts/cew_runtime_audit_store.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def selected_item(queue: dict) -> dict | None:
    by_id = {i["id"]: i for i in queue.get("items", [])}
    active = {"IN_PROGRESS", "RESIDUAL", "CONFLICT", "HUMAN_AUTHORITY_REQUIRED"}
    ordered = sorted(queue.get("items", []), key=lambda i: (int(i.get("priority", 999999)), i.get("id", "")))
    for item in ordered:
        if item.get("state") in active:
            return item
    for item in ordered:
        if item.get("state") not in {"READY", "WAITING"}:
            continue
        if all(by_id[d].get("state") == "COMPLETE" for d in item.get("dependencies", [])):
            return item
    return None


def main() -> int:
    errors: list[str] = []
    for path in [STATE, QUEUE, RECON, ENGINEERING_STATE, ENGINEERING_QUEUE, DEPLOY_RUNTIME, AUDIT_STORE]:
        if not path.exists():
            errors.append(f"missing required artifact: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    state = load(STATE)
    queue = load(QUEUE)
    recon = load(RECON)

    if str(state.get("schema_version")) != "2.0":
        errors.append("CEW product state schema_version must be 2.0")
    if state.get("state_role") != "CEW_PRODUCT_RUNTIME_STATE":
        errors.append("CEW state_role must be CEW_PRODUCT_RUNTIME_STATE")
    if state.get("product") != "CEW" or state.get("vertical") != "CEW-EX":
        errors.append("CEW product identity mismatch")
    if state.get("program", {}).get("goal") != "CEW-GOAL-01":
        errors.append("product state must bind CEW-GOAL-01")
    if state.get("program", {}).get("queue") != "automation/CEW_PRODUCT_TRANSFORMATION_QUEUE_v1.json":
        errors.append("product queue path mismatch")
    if state.get("program", {}).get("orchestrator") != "scripts/cew_product_orchestrator.py":
        errors.append("product orchestrator path mismatch")

    engineering = state.get("engineering_state", {})
    if engineering.get("authority_path") != "knowledge/CURRENT_STATE.json":
        errors.append("N12 engineering authority must remain knowledge/CURRENT_STATE.json")
    if engineering.get("queue_path") != "automation/N12_WORK_QUEUE_v1.json":
        errors.append("N12 engineering queue path mismatch")
    if engineering.get("calculation_model_ready") is not False:
        errors.append("reference project may not be marked calculation-ready by product reconciliation")
    forbidden_detail_keys = {
        "analytical_nodes", "rigid_joint_links", "ordinary_members", "physical_supports",
        "foundation_members", "current_calculation_blockers", "support_count"
    }
    if forbidden_detail_keys.intersection(engineering):
        errors.append("CEW product state duplicates detailed N12 engineering facts")

    phase_projection = engineering.get("phase_projection", [])
    phase_ids = [row.get("phase_id") for row in phase_projection]
    expected = [f"P{i}" for i in range(17)]
    if phase_ids != expected:
        errors.append(f"phase projection must be exactly P0-P16, got {phase_ids}")
    for row in phase_projection:
        if row.get("authority_path") != "knowledge/CURRENT_STATE.json":
            errors.append(f"{row.get('phase_id')}: engineering phase projection must point to N12 authority")
        if set(row) - {"phase_id", "title", "authority_path", "workspace_status"}:
            errors.append(f"{row.get('phase_id')}: phase projection embeds fields beyond allowed product projection")

    runtime = state.get("runtime", {}).get("production", {})
    expected_runtime = {
        "platform": "VERCEL_FASTAPI",
        "url": "https://cew-pilot.vercel.app",
        "service": "CEW_USER_RUNTIME",
        "audit_backend": "NEON_APPEND_ONLY",
        "production_receipt_submit_ready": True,
        "canonical_write_authorized": False,
    }
    for key, expected_value in expected_runtime.items():
        if runtime.get(key) != expected_value:
            errors.append(f"runtime production {key} mismatch: {runtime.get(key)!r}")
    if runtime.get("auth_configured") is not True:
        errors.append("production auth must be recorded configured")

    smoke_status = str(runtime.get("smoke_status") or "")
    valid_smoke_prefixes = (
        "PASS_HUMAN_OBSERVED_",
        "B1_PRODUCTION_DEPLOY_PASS_",
        "B1_PRODUCTION_SMOKE_PASS",
    )
    if not any(smoke_status.startswith(prefix) for prefix in valid_smoke_prefixes):
        errors.append("production smoke/deploy state missing or malformed")

    latest_home = runtime.get("latest_project_home_v2_deployed")
    latest_b1 = runtime.get("latest_b1_source_evidence_deployed")
    for name, value in (
        ("latest_project_home_v2_deployed", latest_home),
        ("latest_b1_source_evidence_deployed", latest_b1),
    ):
        if value is not None and not isinstance(value, bool):
            errors.append(f"{name} must be boolean when present")

    current = state.get("current_product_work_item", {})
    if current.get("id") == "CEW-B1-SOURCE-EVIDENCE-JOURNEY":
        if current.get("state") == "RESIDUAL":
            if "PENDING" not in smoke_status:
                errors.append("B1 RESIDUAL must retain an explicit pending production-smoke state")
            if latest_b1 is not True:
                errors.append("B1 production residual after deployment must record latest_b1_source_evidence_deployed=true")
            if not runtime.get("production_source_commit"):
                errors.append("B1 production residual after deployment must record production_source_commit")
        elif current.get("state") == "COMPLETE" and not smoke_status.startswith("B1_PRODUCTION_SMOKE_PASS"):
            errors.append("B1 COMPLETE requires B1_PRODUCTION_SMOKE_PASS")

    lowered = STATE.read_text(encoding="utf-8").lower()
    stale_fragments = ["netlify", "pending_vercel", "vercel_preview_pending", "created_pending_first_code_deploy"]
    for fragment in stale_fragments:
        if fragment in lowered:
            errors.append(f"stale runtime fragment remains in CEW CURRENT state: {fragment}")

    deploy_text = DEPLOY_RUNTIME.read_text(encoding="utf-8")
    audit_text = AUDIT_STORE.read_text(encoding="utf-8")
    for marker in ["CEW_USER_RUNTIME", "NEON_APPEND_ONLY", "canonical_write_authorized"]:
        if marker not in deploy_text:
            errors.append(f"production deploy runtime missing marker {marker}")
    for marker in ["CEW_AUDIT_NEON_DATABASE_URL", "NEON_APPEND_ONLY", '"canonical_write": False']:
        if marker not in audit_text:
            errors.append(f"audit adapter missing marker {marker}")

    if recon.get("program_goal") != "CEW-GOAL-01":
        errors.append("reconciliation contract goal mismatch")
    authority_split = recon.get("authority_split", {})
    if authority_split.get("n12_engineering_state", {}).get("authority_path") != "knowledge/CURRENT_STATE.json":
        errors.append("reconciliation contract changed N12 authority")

    selected = selected_item(queue)
    if not selected:
        errors.append("product queue has no selected work item")
    elif current.get("id") != selected.get("id") or current.get("agent_role") != selected.get("agent_role"):
        errors.append(
            f"CURRENT product work item {current.get('id')}/{current.get('agent_role')} does not match queue selection "
            f"{selected.get('id')}/{selected.get('agent_role')}"
        )

    if errors:
        print("CEW_PRODUCT_STATE_RECONCILIATION = FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("CEW_PRODUCT_STATE_RECONCILIATION = PASS")
    print(f"CURRENT_PRODUCT_WORK_ITEM = {current.get('id')}")
    print("N12_ENGINEERING_AUTHORITY = knowledge/CURRENT_STATE.json")
    print("PRODUCTION_RUNTIME = VERCEL_FASTAPI + NEON_APPEND_ONLY")
    print(f"PRODUCTION_SMOKE_STATE = {smoke_status}")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
