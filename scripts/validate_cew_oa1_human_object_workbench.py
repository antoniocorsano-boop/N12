#!/usr/bin/env python3
import json
from pathlib import Path

from cew_oa1_human_object_workbench import pilot_fixture, render_panel

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_OA1_HUMAN_OBJECT_WORKBENCH_CONTRACT_v1.json"
QUEUE = ROOT / "automation" / "CEW_OBJECT_ACQUISITION_QUEUE_v1.json"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    state = pilot_fixture()
    html = render_panel(state)

    require(queue["current_item"] == "OA-1", "OA-1 must be current")
    require(queue["items"][0]["state"] == "COMPLETE_PASS", "OA-0 must remain complete")
    require(queue["items"][1]["state"] == "IN_PROGRESS", "OA-1 must remain in progress until runtime integration")
    require(queue["items"][2]["state"] == "BLOCKED_BY_OA1", "OA-2 must remain blocked")

    require(contract["extends_route"] == "/workbench", "OA-1 must extend existing Workbench")
    require(contract["parallel_product_forbidden"] is True, "parallel product forbidden")
    require(contract["primary_view"] == "CAD_FIRST_TECHNICAL_SCENE", "CAD-first view required")
    require(contract["source_view"] == "ON_DEMAND_PROVENANCE", "source must be on-demand")
    require(contract["canonical_write_authorized"] is False, "canonical write must remain disabled")
    require(contract["type_pass"]["initial_type"] == "COLUMN", "pilot type must remain COLUMN")

    expected_regions = {
        "TYPE_PASS_CONTROL",
        "TECHNICAL_CAD_VIEW",
        "FAMILY_PANEL",
        "OBJECT_INSPECTOR",
        "BLOCKER_PANEL",
        "SOURCE_PROVENANCE_DISCLOSURE",
    }
    require(expected_regions.issubset(set(contract["regions"])), "required Workbench regions missing")

    for state_name in ["VERIFIED", "PROPOSED", "AMBIGUOUS", "BLOCKING", "NOT_ANALYZED"]:
        require(state_name in contract["visible_object_states"], f"missing visible state {state_name}")
        require(f'data-state="{state_name}"' in html, f"UI missing state {state_name}")

    require(state["object_type_pass"] == "COLUMN", "fixture must be type-specific")
    require(all(o["object_type"] == "COLUMN" for o in state["objects"]), "type pass leaked other object types")
    require(state["gate"]["can_close_type_pass"] is False, "pilot must visibly remain blocked")
    require(state["gate"]["blocking_count"] == 1, "pilot must expose one blocker")
    require(state["authority"]["canonical_write_authorized"] is False, "state cannot authorize canonical write")
    require(state["authority"]["structural_identity_created"] is False, "OA-1 cannot create structural identity")

    require('data-primary-view="CAD_FIRST_TECHNICAL_SCENE"' in html, "CAD host missing")
    require('aria-label="Cosa blocca"' in html, "blocker panel missing")
    require('data-action="VIEW_SOURCE"' in html, "source disclosure missing")
    require("Fonte disponibile su richiesta; il CAD resta la vista operativa primaria." in html, "source/CAD hierarchy unclear")

    enabled = set(state["actions"]["enabled"])
    require("VIEW_SOURCE" in enabled and "FILTER_TYPE" in enabled, "OA-1 actions incomplete")
    require("THIS_IS_A" not in enabled and "FIND_SIMILAR" not in enabled, "future actions enabled prematurely")

    print("OA1_HUMAN_OBJECT_WORKBENCH_COMPONENT_PASS")
    print("OA1_RUNTIME_INTEGRATION_REQUIRED")


if __name__ == "__main__":
    main()
