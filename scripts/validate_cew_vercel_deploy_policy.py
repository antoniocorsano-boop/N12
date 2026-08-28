#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERCEL = ROOT / "vercel.json"
POLICY = ROOT / "automation/CEW_VERCEL_DEPLOY_POLICY_v1.json"
WORKFLOW = ROOT / ".github/workflows/deploy-cew-vercel-candidate.yml"
CHECKER = ROOT / "scripts/check_cew_vercel_candidate_runs.py"
GOVERNANCE = ROOT / "automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json"
DOC = ROOT / "docs/GOVERNANCE/CEW_VERCEL_CANDIDATE_DEPLOY_POLICY_v1.md"


def main() -> int:
    required = [VERCEL, POLICY, WORKFLOW, CHECKER, GOVERNANCE, DOC]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"missing deployment-governance artifacts: {missing}")

    vercel = json.loads(VERCEL.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    governance = json.loads(GOVERNANCE.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert vercel.get("git", {}).get("deploymentEnabled") is False, (
        "Vercel Git auto-deploy must remain disabled; candidate deployment is controlled by GitHub Actions"
    )
    assert policy["git_auto_deploy"] is False
    assert policy["preview_mode"] == "GATED_CANDIDATE_ONLY"
    assert policy["production_mode"] == "MANUAL_AFTER_CEW_PROMOTION_ONLY"
    assert len(policy["preview_required_workflows"]) >= 10
    assert len(policy["preview_required_workflows"]) == len(set(policy["preview_required_workflows"]))

    rules = policy["candidate_rules"]
    assert rules["immutable_sha_required"] is True
    assert rules["open_pull_request_head_required"] is True
    assert rules["all_required_workflows_success"] is True
    assert rules["duplicate_preview_for_same_sha_forbidden"] is True
    assert rules["deployment_does_not_imply_hva"] is True
    assert rules["deployment_does_not_imply_promotion"] is True

    prod = policy["production_rules"]
    assert prod["automatic_git_production_deploy"] is False
    assert prod["cew_promoted_baseline_required"] is True
    assert prod["same_sha_as_promoted_baseline_required"] is True
    assert prod["manual_dispatch_required"] is True

    assert policy["authentication"]["github_secret_required"] == "VERCEL_TOKEN"
    assert policy["authentication"]["repository_must_not_store_token"] is True

    gov = governance["repository_governance"]
    assert gov["cew_vercel_deploy_policy"] == "automation/CEW_VERCEL_DEPLOY_POLICY_v1.json"
    assert governance["authority_boundaries"]["git_push_implies_vercel_preview"] is False

    required_markers = [
        "workflow_run:",
        "workflow_dispatch:",
        "check_cew_vercel_candidate_runs.py",
        "CEW/Vercel Candidate Preview",
        "VERCEL_TOKEN",
        "automation/CEW_PROMOTED_BASELINE_v1.json",
        "vercel@latest deploy",
        "open pull request",
    ]
    for marker in required_markers:
        assert marker in workflow, f"deployment workflow missing marker: {marker}"

    # Secrets must only be referenced symbolically, never embedded as token values.
    forbidden_literals = ["vcp_", "VERCEL_TOKEN="]
    for literal in forbidden_literals:
        assert literal not in workflow, f"possible credential literal in workflow: {literal}"

    print("CEW_VERCEL_DEPLOY_POLICY_PASS")
    print("GIT_AUTO_DEPLOY = false")
    print(f"PREVIEW_REQUIRED_WORKFLOWS = {len(policy['preview_required_workflows'])}")
    print("PREVIEW = GATED_CANDIDATE_ONLY")
    print("PRODUCTION = PROMOTED_BASELINE_REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
