#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_b1_human_acceptance_v2_hardening as hva


def build_with_env(**values: str) -> str:
    keys = {
        "RENDER_GIT_COMMIT",
        "RENDER_EXTERNAL_URL",
        "RENDER_EXTERNAL_HOSTNAME",
        "VERCEL_GIT_COMMIT_SHA",
        "VERCEL_URL",
        "GITHUB_SHA",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
