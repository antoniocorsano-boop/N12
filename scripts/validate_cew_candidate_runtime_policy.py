#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDER = ROOT / "render.yaml"
POLICY = ROOT / "automation/CEW_CANDIDATE_RUNTIME_POLICY_v1.json"
STATE = ROOT / "automation/CEW_CANDIDATE_RUNTIME_STATE_v1.json"
APP = ROOT / "app.py"
AUDIT = ROOT / "scripts/cew_runtime_audit_store.py"
GOVERNANCE = ROOT / "automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json"
DOC = ROOT / "docs/GOVERNANCE/CEW_CANDIDATE_RUNTIME_POLICY_v1.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_text(path: Path, markers: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        assert marker in text, f"{path.relative_to(ROOT)} missing marker: {marker}"


def main() -> int:
    required = [RENDER, POLICY, STATE, APP, AUDIT, GOVERNANCE, DOC]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    assert not missing, f"missing candidate-runtime artifacts: {missing}"

    policy = load(POLICY)
    state = load(STATE)
    governance = load(GOVERNANCE)

    primary = policy["primary_provider"]
    assert primary["provider"] == "RENDER"
    assert primary["service_role"] == "CANDIDATE_HVA"
    assert primary["plan"] == "free"
    assert primary["region"] == "frankfurt"
    assert primary["auto_deploy"] is False
    assert primary["deploy_mode"] == "SPECIFIC_IMMUTABLE_COMMIT"
    assert primary["health_path"] == "/readyz"
    assert primary["production_authority"] is False

    fallback = policy["fallback_provider"]
    assert fallback["provider"] == "VERCEL"
    assert fallback["role"] == "CONTROLLED_PREVIEW_FALLBACK"
    assert fallback["automatic_working_commit_deploy"] is False

    candidate = policy["candidate_rules"]
    assert candidate["full_sha_required"] is True
    assert candidate["same_sha_as_automated_gate_candidate"] is True
    assert candidate["manual_specific_commit_deploy_required"] is True
    assert candidate["auto_deploy_for_working_commits_forbidden"] is True
    assert candidate["provider_change_does_not_change_candidate_identity"] is True
    assert candidate["deployment_does_not_imply_hva"] is True
    assert candidate["deployment_does_not_imply_promotion"] is True
    assert candidate["deployment_does_not_imply_engineering_authority"] is True

    readiness = policy["readiness_contract"]
    assert readiness["endpoint"] == "/readyz"
    assert readiness["required_http_status"] == 200
    assert readiness["required_runtime_provider"] == "RENDER"
    assert readiness["required_runtime_role"] == "CANDIDATE_HVA"
    assert readiness["runtime_revision_must_equal_candidate_sha"] is True
    assert readiness["persistent_audit_backend_required"] is True
    assert readiness["canonical_write_authorized"] is False
    assert "NEON_APPEND_ONLY" in readiness["allowed_audit_backends"]

    assert state["primary_provider"] == "RENDER"
    assert state["primary_auto_deploy"] is False
    assert state["external_binding_required"] is True
    assert state["production_authorized"] is False
    assert state["canonical_write_authorized"] is False
    assert state["engineering_authority_effect"] == "NONE"

    require_text(
        RENDER,
        [
            "name: cew-hva-candidate",
            "runtime: python",
            "plan: free",
            "region: frankfurt",
            "autoDeployTrigger: off",
            "healthCheckPath: /readyz",
            "uvicorn app:app --host 0.0.0.0 --port $PORT",
            "key: CEW_RUNTIME_ROLE",
            "value: CANDIDATE_HVA",
            "key: CEW_AUTH_DISABLED_FOR_TEST",
            'value: "0"',
            "key: CEW_ACCESS_PASSWORD",
            "sync: false",
            "key: CEW_SESSION_SECRET",
            "generateValue: true",
            "key: CEW_AUDIT_NEON_DATABASE_URL",
        ],
    )

    require_text(
        APP,
        [
            "def _managed_runtime() -> bool:",
            'os.getenv("VERCEL") or os.getenv("RENDER")',
            'return "RENDER"',
            'os.getenv("RENDER_GIT_COMMIT")',
            '@app.get("/readyz")',
            '"runtime_revision": _runtime_revision()',
            '"canonical_write_authorized": False',
            "secure=_managed_runtime() or request.url.scheme == \"https\"",
        ],
    )

    require_text(
        AUDIT,
        [
            'if os.getenv("VERCEL") or os.getenv("RENDER"):',
            'return "UNCONFIGURED_PRODUCTION"',
            'raise ValueError("production audit backend is not configured")',
        ],
    )

    gov = governance["repository_governance"]
    assert gov["cew_candidate_runtime_policy"] == "automation/CEW_CANDIDATE_RUNTIME_POLICY_v1.json"
    assert gov["cew_candidate_runtime_state"] == "automation/CEW_CANDIDATE_RUNTIME_STATE_v1.json"
    assert gov["cew_candidate_runtime_policy_doc"] == "docs/GOVERNANCE/CEW_CANDIDATE_RUNTIME_POLICY_v1.md"
    boundaries = governance["authority_boundaries"]
    assert boundaries["candidate_runtime_deployment_implies_hva"] is False
    assert boundaries["candidate_runtime_deployment_implies_promotion"] is False
    assert boundaries["candidate_runtime_provider_is_engineering_authority"] is False

    print("CEW_CANDIDATE_RUNTIME_POLICY_PASS")
    print("PRIMARY_PROVIDER = RENDER")
    print("PRIMARY_AUTO_DEPLOY = false")
    print("READINESS = /readyz")
    print("FALLBACK_PROVIDER = VERCEL")
    print("PRODUCTION_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
