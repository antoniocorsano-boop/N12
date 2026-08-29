#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "automation/CEW_PROFESSIONAL_WORKBENCH_IMPLEMENTATION_MATRIX_v1.json"
AUDIT = ROOT / "docs/AUDIT/CEW_PROFESSIONAL_EVIDENCE_WORKBENCH_AUDIT_v1.md"
REUSE = ROOT / "docs/AUDIT/CEW_PROFESSIONAL_WORKBENCH_REUSE_MAP_v1.md"
DUAL = ROOT / "scripts/cew_b1_dual_workspace.py"
VIEWER = ROOT / "scripts/cew_evidence_viewer_interaction.py"
HVA = ROOT / "automation/CEW_B18_DUAL_WORKSPACE_HVA_CONTRACT_v1.json"
SOURCE_VIEWER = ROOT / "scripts/build_cew_source_viewer.py"
SOURCE_VIEWER_CONTRACT = ROOT / "automation/CEW_SOURCE_VIEWER_CONTRACT_v1.json"
DUAL_VECTOR = ROOT / "scripts/cew_dual_vector_agreement.py"
DUAL_VECTOR_CONTRACT = ROOT / "automation/CEW_DUAL_VECTOR_AGREEMENT_CONTRACT_v1.json"
ERW = ROOT / "scripts/build_cew_erw_synced_workspace.py"
ERW_CONTRACT = ROOT / "automation/CEW_ERW_CONTRACT_v1.json"
ERW_VALIDATOR = ROOT / "scripts/validate_cew_erw_synced_workspace.py"
WORKBENCH_CONTRACT = ROOT / "automation/CEW_PROFESSIONAL_WORKBENCH_SCENE_CONTRACT_v1.json"
WORKBENCH_CORE = ROOT / "scripts/cew_professional_workbench_core.py"
WORKBENCH_PROJECTION = ROOT / "scripts/cew_professional_workbench_projection.py"
WORKBENCH_VALIDATOR = ROOT / "scripts/validate_cew_professional_workbench_core.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def text(path: Path) -> str:
    require(path.exists(), f"required audit/reuse evidence missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    matrix = json.loads(text(MATRIX))
    audit = text(AUDIT)
    reuse = text(REUSE)
    dual = text(DUAL)
    viewer = text(VIEWER)
    hva = json.loads(text(HVA))
    workbench_contract = json.loads(text(WORKBENCH_CONTRACT))
    workbench_core = text(WORKBENCH_CORE)
    workbench_projection = text(WORKBENCH_PROJECTION)
    workbench_validator = text(WORKBENCH_VALIDATOR)

    require(matrix["schema_version"] == "1.2", "unexpected matrix schema")
    require(matrix["professional_workbench_readiness"] == "REWORK_REQUIRED", "workbench must remain REWORK_REQUIRED")
    require(matrix["hva_execution_authorized"] is False, "HVA must remain paused")
    require(matrix["b1_promotion_authorized"] is False, "B1 promotion must remain unauthorized")
    require(matrix["canonical_write_authorized"] is False, "canonical write must remain unauthorized")
    require("AVAILABLE_NOT_INTEGRATED" in matrix["status_vocabulary"], "reuse-aware status vocabulary missing")

    reqs = {item["id"]: item for item in matrix["requirements"]}
    blockers = matrix["blocking_requirement_ids"]
    require(blockers, "blocking requirements cannot be empty")
    for requirement_id in blockers:
        require(requirement_id in reqs, f"missing blocking requirement {requirement_id}")
        require(reqs[requirement_id]["status"] != "IMPLEMENTED", f"blocker {requirement_id} cannot be marked implemented without audit update")

    for marker in (
        "AUDIT_COMPLETE — REWORK_REQUIRED_BEFORE_HVA",
        "PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED",
        "HVA_EXECUTION_AUTHORIZED = false",
        "B1_PROMOTION_AUTHORIZED = false",
        "CANONICAL_WRITE_AUTHORIZED = false",
        "document geometry != technical candidate != structural identity",
    ):
        require(marker in audit, f"audit marker missing: {marker}")

    # The audited B1.8 surface remains the historical POC and must not be silently
    # reclassified as the final client merely because a new kernel exists.
    require("canonical_write_authorized" in dual and "False" in dual, "dual workspace canonical-write boundary missing")
    require("sessionStorage" in dual, "session-only proposal boundary missing")
    require("geometry != identity" in dual, "geometry/identity warning missing")
    require("evidenceViewport" in viewer, "interactive evidence viewport missing")
    require("zoomBy" in viewer and "pointermove" in viewer and "keydown" in viewer, "zoom/pan/keyboard interaction markers missing")
    require("<iframe" in dual, "audited B1.8 iframe composition unexpectedly changed; update audit if client changed")
    require("region-map" in dual and "region-box" in dual, "audited documentary region placeholder unexpectedly changed")
    require("<textarea id=\"proposalText\"" in dual, "audited detached proposal textarea unexpectedly changed")
    require("html_text.replace" in viewer, "audited string-replacement viewer enhancement unexpectedly changed")

    # Reusable upstream CEW foundations.
    source_viewer = text(SOURCE_VIEWER)
    source_contract = text(SOURCE_VIEWER_CONTRACT)
    dual_vector = text(DUAL_VECTOR)
    dual_vector_contract = text(DUAL_VECTOR_CONTRACT)
    erw = text(ERW)
    erw_contract = text(ERW_CONTRACT)
    erw_validator = text(ERW_VALIDATOR)

    require("OpenSeadragon" in source_viewer or "openseadragon" in source_viewer.lower(), "F3 OpenSeadragon source-viewer capability missing")
    require("dzi" in source_viewer.lower(), "F3 DZI source-viewer capability missing")
    require("300" in source_contract, "F3 300 dpi source-viewer contract marker missing")
    require("canonical" in source_contract.lower() and "false" in source_contract.lower(), "F3 read-only/canonical-write boundary missing")

    require(all(state in dual_vector for state in ("AGREE", "PARTIAL", "DISAGREE")), "dual-vector AGREE/PARTIAL/DISAGREE states missing")
    require("pymupdf" in dual_vector_contract.lower() and "docling" in dual_vector_contract.lower(), "dual-vector two-extractor contract missing")
    require("canonical_mutation" in dual_vector and "False" in dual_vector, "dual-vector non-canonical evidence boundary missing")

    require("svg" in erw.lower(), "F6 ERW SVG structural scene missing")
    require("member" in erw.lower() and "node" in erw.lower(), "F6 ERW member/node scene markers missing")
    require("sync" in erw.lower(), "F6 ERW synchronization markers missing")
    require("M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv" in text(ROOT / ".github/workflows/validate-cew-erw-synced-workspace.yml"), "F6 frozen member-ledger workflow binding missing")
    require("canonical" in erw_contract.lower() or "read" in erw_contract.lower(), "F6 ERW read-only contract marker missing")
    for marker in (
        "forbidden authority action enabled",
        "support topology drift",
        "candidate coordinates differ from canonical analytical nodes",
        "section state differs from frozen connectivity ledger",
        "CANONICAL_WRITE=FORBIDDEN",
        "M0G_REOPEN=FORBIDDEN",
    ):
        require(marker in erw_validator, f"F6 frozen-ledger/authority validator marker missing: {marker}")

    # New deterministic workbench foundation: model/guards exist, but this is not
    # permission to claim the visual client or real spatial registration complete.
    require(workbench_contract["canonical_write_authorized"] is False, "workbench scene contract canonical-write drift")
    require("document geometry != technical candidate != structural identity" in workbench_contract["invariants"], "workbench geometry/identity invariant missing")
    require("VIEWPORT_PX" in workbench_contract["coordinate_spaces"], "viewport coordinate space must be explicit")
    require("SPATIAL_LOCKED" in workbench_contract["sync_modes"] and "OVERLAY" in workbench_contract["display_modes"], "workbench mode contract incomplete")
    for marker in (
        "validate_registration",
        "registration_allows_spatial",
        "resolve_view_state",
        "create_working_edit",
        "create_reading_issue",
        "VIEWPORT_COORDINATES_CANNOT_BE_SCENE_GEOMETRY",
        "WORKING_EDIT_TARGET_READ_ONLY",
        "READING_ISSUE_GRAPHICAL_OR_EVIDENCE_ANCHOR_REQUIRED",
    ):
        require(marker in workbench_core, f"workbench fail-closed kernel marker missing: {marker}")
    for marker in (
        "F3_DZI_MANIFEST_REUSED",
        "F6_ERW_M0G_FROZEN_LEDGER_ADAPTER",
        "UNBOUND_CANDIDATE_COMPARISON_CONTEXT_ONLY",
        "NO_VERIFIED_SOURCE_TO_TECHNICAL_REGISTRATION_IN_CURRENT_CEW_RECORDS",
        "canonical_write_authorized",
    ):
        require(marker in workbench_projection, f"workbench reuse projection marker missing: {marker}")
    for marker in (
        "OVERLAY_WITHOUT_VERIFIED_REGISTRATION = FAIL_CLOSED",
        "SPATIAL_LOCK_WITHOUT_VERIFIED_REGISTRATION = FAIL_CLOSED",
        "GOVERNED_STRUCTURAL_EDIT = FORBIDDEN",
        "READING_ISSUE_ANCHOR = REQUIRED",
        "VIEWPORT_GEOMETRY_PERSISTENCE = FORBIDDEN",
    ):
        require(marker in workbench_validator, f"workbench negative-test marker missing: {marker}")

    require(reqs["PWB-005"]["status"] == "AVAILABLE_NOT_INTEGRATED", "PWB-005 reuse classification mismatch")
    require(reqs["PWB-006"]["status"] == "AVAILABLE_NOT_INTEGRATED", "PWB-006 reuse classification mismatch")
    require(reqs["PWB-014"]["status"] == "AVAILABLE_NOT_INTEGRATED", "PWB-014 reuse classification mismatch")
    for requirement_id in ("PWB-007", "PWB-008", "PWB-009", "PWB-012", "PWB-015", "PWB-018"):
        require(reqs[requirement_id]["status"] == "PARTIAL", f"{requirement_id} kernel/design classification mismatch")
    require(reqs["PWB-010"]["status"] == "NOT_IMPLEMENTED", "overlay must remain unimplemented until a verified registered renderer exists")
    require(reqs["PWB-004"]["status"] == "NOT_IMPLEMENTED", "drawing-first client must not be claimed before UI integration")
    require(reqs["PWB-013"]["status"] == "NOT_IMPLEMENTED", "progressive disclosure must not be claimed before UI integration")

    for marker in (
        "F3 Source Viewer",
        "Dual Vector Agreement",
        "F6 ERW Synchronized Workspace",
        "AVAILABLE_NOT_INTEGRATED",
        "PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED",
    ):
        require(marker in reuse, f"reuse-map marker missing: {marker}")

    require(hva["human_hva_state"] == "REQUIRED_NOT_SATISFIED", "human HVA must remain unsatisfied")
    require(hva["canonical_write_authorized"] is False, "HVA contract cannot authorize canonical writes")

    implemented = sorted(rid for rid, row in reqs.items() if row["status"] == "IMPLEMENTED")
    partial = sorted(rid for rid, row in reqs.items() if row["status"] == "PARTIAL")
    available = sorted(rid for rid, row in reqs.items() if row["status"] == "AVAILABLE_NOT_INTEGRATED")
    missing = sorted(rid for rid, row in reqs.items() if row["status"] == "NOT_IMPLEMENTED")

    print("CEW_PROFESSIONAL_WORKBENCH_AUDIT_CONSISTENCY = PASS")
    print("CEW_PROFESSIONAL_WORKBENCH_REUSE_VERIFICATION = PASS")
    print("CEW_PROFESSIONAL_WORKBENCH_KERNEL_FOUNDATION = VERIFIED_PRESENT")
    print("PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED")
    print(f"IMPLEMENTED = {','.join(implemented)}")
    print(f"PARTIAL = {','.join(partial)}")
    print(f"AVAILABLE_NOT_INTEGRATED = {','.join(available)}")
    print(f"NOT_IMPLEMENTED = {','.join(missing)}")
    print(f"BLOCKERS = {','.join(blockers)}")
    print("HVA_EXECUTION_AUTHORIZED = false")
    print("B1_PROMOTION_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")


if __name__ == "__main__":
    main()
