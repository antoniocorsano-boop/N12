#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation/CEW_ENTERPRISE_PROFESSIONAL_WORKSPACE_CONTRACT_v1.json"
MODEL = ROOT / "docs/DESIGN/CEW_ENTERPRISE_PROFESSIONAL_WORKSPACE_MODEL_v1.md"
RESEARCH = ROOT / "docs/RESEARCH/CEW_ENTERPRISE_AEC_SYSTEM_PATTERN_DECODING_v1.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    model = MODEL.read_text(encoding="utf-8")
    research = RESEARCH.read_text(encoding="utf-8")

    require(contract["contract"] == "CEW_ENTERPRISE_PROFESSIONAL_WORKSPACE", "contract id drift")
    require(contract["product_thesis"] == "PROFESSIONAL_WORK_OPERATING_SYSTEM_EVIDENCE_FIRST", "product thesis drift")
    require(contract["authority_effect"] == "NONE", "design baseline cannot create authority")
    require(contract["canonical_write_authorized"] is False, "canonical write authority drift")
    require(contract["project_material_ready"] is False, "project material cannot be released by UX design")

    interaction_objects = set(contract["interaction_objects"])
    for required in {"WorkItem", "WorkContext", "ViewState", "EvidenceObject", "TechnicalObject", "IssueTopic", "DecisionReceipt"}:
        require(required in interaction_objects, f"interaction object missing: {required}")

    workspace = contract["workspace"]
    require(workspace["application_frame"] == "VIEWPORT_BOUND", "workspace must be viewport-bound")
    require(workspace["page_growth_from_context_rail_forbidden"] is True, "page-growth regression is not blocked")
    require(workspace["context_rail_independent_scroll"] is True, "context rail must scroll independently")
    require(workspace["source_content_obstruction_forbidden"] is True, "source obstruction guard missing")
    require(workspace["single_context_rail_canvas_target_min_percent"] >= 65, "canvas dominance weakened")

    topology = contract["view_topology"]
    require(topology["unregistered_source_position_default"] == "SOURCE_PRIMARY_WITH_CONTEXT_RAIL", "unregistered source topology drift")
    require(topology["universal_split_default_forbidden"] is True, "universal split default must be forbidden")
    require("EXPLICIT_ONLY" in topology["verified_spatial_registration"], "split/overlay eligibility must remain explicit")

    modes = set(contract["work_modes"])
    for required in {"NAVIGATE", "ACQUIRE", "REVIEW_SET", "COMPARE", "RESOLVE_ISSUE", "EDIT_WORKING", "VALIDATE", "PROVENANCE_AUDIT"}:
        require(required in modes, f"work mode missing: {required}")

    review = contract["review_set"]
    require(review["levels"] == ["SUMMARY", "REVIEW_SET", "ACTIVE_CANDIDATE"], "review hierarchy drift")
    require(review["full_expanded_result_stack_forbidden"] is True, "full expanded result stack must remain forbidden")
    require(review["virtualization_or_progressive_paging_required"] is True, "large result containment missing")
    require(review["single_primary_candidate"] is True, "active candidate model weakened")
    require(review["implicit_whole_cluster_confirmation_forbidden"] is True, "implicit cluster confirmation must remain forbidden")
    require(review["score_is_not_authority"] is True, "detector/check score authority drift")

    continuity = contract["context_continuity"]
    for field in ["Project", "WorkItem", "SourceVersion", "Page", "EvidenceRegion", "SelectedObjects", "ViewState", "Revision"]:
        require(field in continuity["restore_fields"], f"context restore field missing: {field}")
    require(continuity["snapshot_is_convenience_not_authority"] is True, "snapshot authority drift")

    authority = contract["authority_separation"]
    require(all(authority.values()), "authority-separation invariant weakened")

    performance = contract["performance"]
    require(performance["canvas_render_isolated_from_rail"] is True, "canvas/rail rendering isolation missing")
    require(performance["long_lists_virtualized"] is True, "long-list virtualization missing")
    require(performance["evidence_provenance_lazy"] is True, "progressive evidence loading missing")

    shortcuts = set(contract["forbidden_shortcuts"])
    for required in {
        "PAGE_HEIGHT_DRIVEN_BY_RESULT_LIST",
        "UNIVERSAL_SPLIT_DEFAULT",
        "SOURCE_OVERLAID_BY_PERSISTENT_UI",
        "FULL_EXPANDED_CLUSTER_AS_PRIMARY_REVIEW_UI",
        "DETECTOR_SCORE_AS_ENGINEERING_AUTHORITY",
        "VISUAL_PROXIMITY_CREATES_IDENTITY",
        "SCREENSHOT_REPLACES_IMMUTABLE_SOURCE",
        "OA6_RELEASE_BEFORE_ENTERPRISE_UX_GATE",
    }:
        require(required in shortcuts, f"forbidden shortcut missing: {required}")

    require("EWS-1 — Application frame" in model, "EWS-1 program missing")
    require("EWS-4 — Result Review Controller" in model, "EWS-4 program missing")
    require("The current long right-hand result stack is not accepted as enterprise UX" in model, "OA pilot rework decision missing")
    require("primary canvas and context rail have independent overflow behavior" in model, "independent-scroll model missing")
    require("WorkItem" in model and "ViewState" in model and "IssueTopic" in model, "enterprise interaction model incomplete")

    for source_name in ["Bluebeam Revu", "AutoCAD Smart Blocks", "Revizto", "Dalux", "Procore", "Navisworks", "BIMcollab", "Trimble Connect", "Solibri"]:
        require(source_name in research, f"research system missing: {source_name}")
    require("Canvas dominance" in research, "research synthesis missing canvas dominance")
    require("Summary before detail" in research, "research synthesis missing summary-before-detail")

    print("CEW_ENTERPRISE_PROFESSIONAL_WORKSPACE = PASS")
    print("APPLICATION_FRAME = VIEWPORT_BOUND")
    print("CONTEXT_RAIL_INDEPENDENT_SCROLL = true")
    print("UNIVERSAL_SPLIT_DEFAULT = forbidden")
    print("REVIEW_SET_MODEL = SUMMARY_TO_SET_TO_ACTIVE_CANDIDATE")
    print("IMPLICIT_CLUSTER_CONFIRMATION = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("PROJECT_MATERIAL_READY = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
