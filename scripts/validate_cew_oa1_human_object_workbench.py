#!/usr/bin/env python3
import json
from pathlib import Path

from cew_oa1_human_object_workbench import pilot_fixture, render_panel
from cew_oa1_workbench_runtime import OA1_RUNTIME_MARKER, augment

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_OA1_HUMAN_OBJECT_WORKBENCH_CONTRACT_v1.json"
QUEUE = ROOT / "automation" / "CEW_OBJECT_ACQUISITION_QUEUE_v1.json"
API = ROOT / "scripts" / "cew_professional_workbench_api.py"
CLIENT = ROOT / "scripts" / "cew_professional_workbench_client.py"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    state = pilot_fixture()
    html = render_panel(state)
    api = API.read_text(encoding="utf-8")
    client = CLIENT.read_text(encoding="utf-8")

    require(queue["items"][0]["state"] == "COMPLETE_PASS", "OA-0 must remain complete")
    oa1 = queue["items"][1]
    require(oa1["state"] == "COMPLETE_PASS", "OA-1 must remain COMPLETE_PASS after release")
    require(oa1.get("validated_head") == "1280c0f879bec50f4a4cfbec763b283f13ae4793", "OA-1 validated head drift")
    require(oa1.get("gate") == "OA1_HUMAN_OBJECT_WORKBENCH_PASS", "OA-1 completion gate drift")
    require(queue["current_item"] in {"OA-1", "OA-2", "OA-3", "OA-4", "OA-5", "OA-6"}, "invalid downstream current item")
    if queue["current_item"] == "OA-1":
        require(queue["items"][2]["state"] == "BLOCKED_BY_OA1", "OA-2 must remain blocked before release")
    else:
        require(queue["items"][2]["state"] in {"IN_PROGRESS", "COMPLETE_PASS"}, "OA-2 release state invalid")

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
        require(f'data-state="{state_name}"' in html, f"component UI missing state {state_name}")

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

    runtime_html = augment(client.replace("__TASK_LABEL__", "ERW-N12-001").replace("__TASK_JSON__", '"ERW-N12-001"'), "ERW-N12-001")
    require(OA1_RUNTIME_MARKER in runtime_html, "OA-1 runtime marker missing")
    require('id="oaPanel"' in runtime_html, "runtime acquisition panel missing")
    require('id="oaType"' in runtime_html, "runtime type-pass selector missing")
    require('id="oaBlockers"' in runtime_html, "runtime blocker panel missing")
    require("function explicitType(o)" in runtime_html, "runtime explicit type resolver missing")
    require("geometry" not in runtime_html[runtime_html.index("function explicitType(o)"):runtime_html.index("function explicitState(o)")], "type resolver must not infer from geometry")
    require("Nessun oggetto" in runtime_html and "non lo deduce dalla forma delle linee" in runtime_html, "fail-closed no-type explanation missing")
    require("THIS_IS_A" not in runtime_html and "FIND_SIMILAR" not in runtime_html, "OA-2/OA-3 actions leaked into OA-1 runtime")
    require("import cew_oa1_workbench_runtime as oa1_runtime" in api, "Professional Workbench API does not import OA-1 adapter")
    require("return oa1_runtime.augment(rendered, task)" in api, "Professional Workbench HTML is not augmented by OA-1")
    require('"X-CEW-OA1-Runtime": "CAD_FIRST_OBJECT_PASS_AVAILABLE_NON_PROMOTIVE"' in api, "OA-1 runtime authority header missing")

    print("OA1_HUMAN_OBJECT_WORKBENCH_COMPONENT_PASS")
    print("OA1_RUNTIME_INTEGRATION_PASS")
    print("OA1_HUMAN_OBJECT_WORKBENCH_PASS")


if __name__ == "__main__":
    main()
