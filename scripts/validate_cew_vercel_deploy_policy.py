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

    deployment_rules = vercel.get("git", {}).get("deploymentEnabled")
    assert isinstance(deployment_rules, dict), "Vercel deploymentEnabled must be an explicit branch-rule map"
    assert deployment_rules.get("**") is False, "ordinary Git branches must not auto-deploy"
    assert deployment_rules.get("vercel-preview/**") is True, "only gated preview refs may trigger Vercel"

    assert policy["git_integration"] == "ENABLED_FOR_GATED_BRANCHES_ONLY"
    assert policy["preview_mode"] == "GATED_CANDIDATE_REF_ONLY"
    assert policy["candidate_ref_prefix"] == "vercel-preview/"
    assert len(policy["preview_required_workflows"]) >= 10
    assert len(policy["preview_required_workflows"]) == len(set(policy["preview_required_workflows"]))

    rules = policy["candidate_rules"]
    assert rules["immutable_sha_required"] is True
    assert rules["open_pull_request_head_required"] is True
    assert rules["all_required_workflows_success"] is True
    assert rules["preview_ref_must_point_to_exact_candidate_sha"] is True
    assert rules["automatic_first_generation"] == 1
    assert rules["manual_retry_may_increment_generation_without_changing_sha"] is True
    assert rules["deployment_does_not_imply_hva"] is True
    assert rules["deployment_does_not_imply_promotion"] is True

    credentials = policy["credentials"]
    assert credentials["vercel_token_required"] is False
    assert credentials["repository_secret_required"] is False
    assert credentials["github_token_source"] == "GITHUB_ACTIONS_BUILT_IN_TOKEN"

    prod = policy["production_rules"]
    assert prod["automatic_git_production_deploy"] is False
    assert prod["production_not_implemented_by_candidate_ref_policy"] is True
    assert prod["cew_promoted_baseline_required_before_any_future_production_deploy"] is True

    gov = governance["repository_governance"]
    assert gov["cew_vercel_deploy_policy"] == "automation/CEW_VERCEL_DEPLOY_POLICY_v1.json"
    assert governance["authority_boundaries"]["git_push_implies_vercel_preview"] is False

    required_markers = [
        "workflow_run:",
        "workflow_dispatch:",
        "check_cew_vercel_candidate_runs.py",
        "vercel-preview/",
        "git/refs",
        "CEW/Vercel Candidate Trigger",
        "open pull request",
        "retry_generation",
    ]
    for marker in required_markers:
        assert marker in workflow, f"candidate-ref workflow missing marker: {marker}"

    forbidden_markers = [
        "VERCEL_TOKEN",
        "vercel@latest deploy",
        "--prod",
        "CEW_PROMOTED_BASELINE_v1.json",
        "vcp_",
    ]
    for marker in forbidden_markers:
        assert marker not in workflow, f"candidate-ref workflow must not contain direct Vercel deploy/credential marker: {marker}"

    print("CEW_VERCEL_DEPLOY_POLICY_PASS")
    print("ORDINARY_GIT_AUTO_DEPLOY = false")
    print("GATED_PREVIEW_REF = vercel-preview/**")
    print(f"PREVIEW_REQUIRED_WORKFLOWS = {len(policy['preview_required_workflows'])}")
    print("VERCEL_TOKEN_REQUIRED = false")
    print("PRODUCTION_AUTO_DEPLOY = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
