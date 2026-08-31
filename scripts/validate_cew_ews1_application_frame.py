#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

EWS0 = ROOT / "automation/CEW_ENTERPRISE_PROFESSIONAL_WORKSPACE_CONTRACT_v1.json"
EWS1 = ROOT / "automation/CEW_EWS1_APPLICATION_FRAME_CONTRACT_v1.json"
RUNTIME = ROOT / "scripts/cew_ews1_application_frame_runtime.py"
OA1 = ROOT / "scripts/cew_oa1_workbench_runtime.py"
PILOT = "OA-N12-G4-COLUMN-PILOT"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    ews0 = json.loads(EWS0.read_text(encoding="utf-8"))
    ews1 = json.loads(EWS1.read_text(encoding="utf-8"))
    runtime = RUNTIME.read_text(encoding="utf-8")
    oa1 = OA1.read_text(encoding="utf-8")

    require(ews0["status"] == "EWS0_COMPLETE_PASS", "EWS-0 is not frozen")
    require(ews1["contract"] == "CEW_EWS1_APPLICATION_FRAME", "EWS-1 contract id drift")
    require(ews1["status"] == "EWS1_COMPLETE_PASS", "EWS-1 is not frozen COMPLETE_PASS")
    require(ews1["interaction_revision"] == "EWS1.1_RESIZABLE_PROFESSIONAL_FRAME", "EWS-1.1 revision missing")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", ews1["validated_runtime_sha"])), "validated runtime SHA invalid")
    require(ews1["authority_effect"] == "NONE", "layout cannot create authority")
    require(ews1["canonical_write_authorized"] is False, "canonical write drift")
    require(ews1["project_material_ready"] is False, "project material release drift")

    desktop = ews1["desktop"]
    require(desktop["application_frame"] == "VIEWPORT_BOUND", "frame must be viewport bound")
    require(desktop["workspace_page_growth"] == "FORBIDDEN", "page growth guard missing")
    require(desktop["context_rail_overflow"] == "INDEPENDENT_VERTICAL_SCROLL", "rail scroll guard missing")
    require(desktop["context_rail_resizable"] is True, "context rail must be resizable")
    require(desktop["context_rail_width_px"] == {"default": 400, "minimum": 280, "maximum": 640}, "rail width limits drift")
    require(desktop["minimum_canvas_ratio"] >= 0.55, "canvas minimum ratio weakened")
    require(desktop["resize_preference_storage"] == "LOCAL_UI_PREFERENCE_ONLY", "resize preference must remain UI-only")
    require(desktop["resize_preference_authority"] == "NONE", "resize preference gained authority")
    require(desktop["utility_popover_layer"] == "FLOAT_ABOVE_CONTEXT_RAIL", "utility layering drift")
    require(desktop["layers_panel_reachability"] == "ALWAYS_AVAILABLE", "levels panel reachability weakened")
    require(ews1["oa_unregistered_source_position"]["topology"] == "SOURCE_PRIMARY_WITH_CONTEXT_RAIL", "OA topology drift")
    require(ews1["oa_unregistered_source_position"]["source_canvas_min_target_percent"] >= 55, "canvas target weakened")
    require(ews1["runtime"]["domain_logic_modified"] is False, "EWS-1 may not alter domain logic")
    require(ews1["runtime"]["receipt_logic_modified"] is False, "EWS-1 may not alter receipt logic")
    require(ews1["runtime"]["similarity_logic_modified"] is False, "EWS-1 may not alter similarity logic")

    for marker in [
        "CEW_EWS1_VIEWPORT_BOUND_APPLICATION_FRAME",
        "CEW_EWS11_RESIZABLE_PROFESSIONAL_FRAME",
        "height:100dvh",
        "overflow:hidden",
        "context_rail_independent_scroll:true",
        "context_rail_resizable:TASK_ID",
        "--ews-context-rail-width",
        "grid-template-columns:minmax(0,1fr) var(--ews-context-rail-width)",
        "#ews1RailSplitter",
        "cursor:col-resize",
        "MIN_RAIL=280",
        "MAX_RAIL=640",
        "MIN_CANVAS_RATIO=.55",
        "localStorage.setItem(PREF_KEY",
        "ui_preference_authority:'NONE'",
        "#layerPop",
        "position:fixed!important",
        "right:calc(var(--ews-context-rail-width) + 18px)!important",
        "z-index:240!important",
        "utility_popovers_above_context_rail:true",
        "#oaPanel",
        "overflow-y:auto",
        "#sourceViewport",
        "position:absolute",
        "page_growth_from_context_rail:false",
        "canonical_write_authorized:false",
    ]:
        require(marker in runtime, f"runtime invariant missing: {marker}")

    require("import cew_ews1_application_frame_runtime as ews1_runtime" in oa1, "EWS-1 compositor import missing")
    require("ews1_runtime.augment(oa2_runtime.augment(rendered, task), task)" in oa1, "EWS-1 must compose after OA runtime")

    html = oa1_runtime.augment(client.build_client(PILOT), PILOT)
    require("CEW_EWS1_VIEWPORT_BOUND_APPLICATION_FRAME" in html, "rendered pilot missing EWS-1 marker")
    require("CEW_EWS11_RESIZABLE_PROFESSIONAL_FRAME" in html, "rendered pilot missing EWS-1.1 marker")
    require('data-ews1-runtime="CEW_EWS1_VIEWPORT_BOUND_APPLICATION_FRAME"' in html, "runtime marker not emitted")
    require('data-ews11-runtime="CEW_EWS11_RESIZABLE_PROFESSIONAL_FRAME"' in html, "resizable runtime marker not emitted")
    require("body.ews1-frame.oa-human-first" in html, "OA-specific enterprise frame missing")
    require("var(--ews-context-rail-width)" in html, "resizable rail width missing")
    require("max-height:100%!important" in html, "context rail height containment missing")
    require("overflow-y:auto!important" in html, "context rail independent scroll missing")
    require("position:absolute!important" in html and "inset:0!important" in html, "source viewport full-fill missing")
    require("Ridimensiona pannello laterale" in html, "accessible splitter label missing")
    require("Doppio clic: larghezza standard" in html, "splitter reset affordance missing")
    require("FLOAT_ABOVE_FRAME" in html, "utility layer marker missing")
    require("data-canonical-write-authorized=\"false\"" in html, "canonical write boundary lost")

    forbidden = set(ews1["forbidden_shortcuts"])
    for name in {
        "PAGE_HEIGHT_DRIVEN_BY_CONTEXT_RAIL",
        "SOURCE_CANVAS_HEIGHT_DRIVEN_BY_RESULT_COUNT",
        "BODY_SCROLL_AS_PRIMARY_WORKSPACE_NAVIGATION",
        "PERSISTENT_UI_OVER_SOURCE_CONTENT",
        "FIXED_CONTEXT_RAIL_WITHOUT_USER_RESIZE",
        "UTILITY_POPOVER_HIDDEN_BEHIND_CONTEXT_RAIL",
        "UI_WIDTH_AS_GOVERNED_STATE",
        "CANVAS_COLLAPSE_BELOW_MINIMUM_RATIO",
        "OA_G5_RELEASE",
        "OA_6_RELEASE",
        "CANONICAL_WRITE_FROM_LAYOUT",
    }:
        require(name in forbidden, f"forbidden shortcut missing: {name}")

    print("CEW_EWS1_APPLICATION_FRAME = PASS")
    print("STATUS = EWS1_COMPLETE_PASS")
    print("INTERACTION_REVISION = EWS1.1_RESIZABLE_PROFESSIONAL_FRAME")
    print("APPLICATION_FRAME = VIEWPORT_BOUND")
    print("CONTEXT_RAIL_RESIZABLE = true")
    print("CONTEXT_RAIL_RANGE_PX = 280..640")
    print("MINIMUM_CANVAS_RATIO = 0.55")
    print("LAYERS_PANEL_REACHABILITY = ALWAYS_AVAILABLE")
    print("UI_PREFERENCE_AUTHORITY = NONE")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("PROJECT_MATERIAL_READY = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
