#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

CONTRACT = ROOT / "automation/CEW_PR1_ONE_SCROLL_OWNER_CONTRACT_v1.json"
PILOT = "OA-N12-G4-COLUMN-PILOT"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["contract"] == "CEW_PR1_ONE_SCROLL_OWNER_WORKSPACE", "contract id drift")
    require(contract["authority_effect"] == "NONE", "authority drift")
    require(contract["canonical_write_authorized"] is False, "canonical write drift")
    req = contract["required_behavior"]
    require(req["scroll_owner"] == "#ews2RailBody", "scroll owner drift")
    require(req["nested_vertical_scroll"] is False, "nested vertical scroll must be false")
    for k in ["workmode_header_outside_scroll_owner","primary_actions_sticky","source_canvas_stable","review_set_uses_parent_scroll","active_candidate_uses_parent_scroll","reason_list_uses_parent_scroll","catalog_uses_parent_scroll"]:
        require(req[k] is True, f"required behavior lost: {k}")

    runtime = (ROOT / "scripts/cew_pr1_one_scroll_owner_runtime.py").read_text(encoding="utf-8")
    for marker in [
        "CEW_PR1_ONE_SCROLL_OWNER_WORKSPACE",
        "#ews2RailBody",
        "overflow-y:auto!important",
        ".ews4-set",
        ".ews4-active",
        ".ews4-reasons",
        "#oaPilotTray",
        "overflow:visible!important",
        "position:sticky",
        "ONE_SCROLL_OWNER_ACTIVE",
    ]:
        require(marker in runtime, f"runtime invariant missing: {marker}")

    compositor = (ROOT / "scripts/cew_enterprise_governed_resume_runtime.py").read_text(encoding="utf-8")
    require("import cew_pr1_one_scroll_owner_runtime as pr1_runtime" in compositor, "PR-1 compositor import missing")
    require("return pr1_runtime.augment(persistent, task)" in compositor, "PR-1 must be final presentation layer")

    html = oa1_runtime.augment(client.build_client(PILOT), PILOT)
    require('data-pr1-runtime="CEW_PR1_ONE_SCROLL_OWNER_WORKSPACE"' in html, "rendered pilot missing PR-1")
    require("verticalScrollOwner='PRIMARY'" in html or "verticalScrollOwner=\'PRIMARY\'" in html, "primary scroll owner marker missing")
    require("nested_vertical_scroll:false" in html, "nested scroll state missing")
    require('data-canonical-write-authorized="false"' in html, "canonical write boundary lost")

    forbidden = set(contract["forbidden_shortcuts"])
    for item in ["NESTED_VERTICAL_SCROLL","SCROLL_OWNER_PER_SECTION","REVIEW_SET_INDEPENDENT_SCROLL","ACTIVE_CANDIDATE_INDEPENDENT_SCROLL","OA6_RELEASE"]:
        require(item in forbidden, f"forbidden shortcut missing: {item}")

    print("CEW_PR1_ONE_SCROLL_OWNER_WORKSPACE = PASS")
    print("VERTICAL_SCROLL_OWNER = #ews2RailBody")
    print("NESTED_VERTICAL_SCROLL = false")
    print("PRIMARY_ACTIONS = STICKY")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
