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
WORKBENCH_API = ROOT / "scripts/cew_professional_workbench_api.py"
BUILD_MANAGED_F3 = ROOT / "scripts/build_cew_managed_f3_assets.py"
MANAGED_F3 = ROOT / "scripts/cew_managed_f3_assets.py"
MANAGED_F3_VALIDATOR = ROOT / "scripts/validate_cew_managed_f3_assets.py"
RENDER = ROOT / "render.yaml"
REQUIREMENTS = ROOT / "requirements.txt"


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
    workbench_api = text(WORKBENCH_API)
    build_managed_f3 = text(BUILD_MANAGED_F3)
    managed_f3 = text(MANAGED_F3)
    managed_f3_validator = text(MANAGED_F3_VALIDATOR)
    render = text(RENDER)
    requirements = text(REQUIREMENTS)

    require(matrix["schema_version"] == "1.3", "unexpected matrix schema")
    require(matrix["status"] == "VERIFIED_GAP_MATRIX_WITH_KERNEL_AND_MANAGED_F3_FOUNDATIONS", "matrix state drift")
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

    # Historical B1.8 remains the audited POC. New foundations must not silently
    # reclassify its monolithic UI as the final professional client.
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

    # Deterministic Workbench kernel and non-authoritative working state.
    require(workbench_contract["schema_version"] == "1.1", "workbench contract schema drift")
    require(workbench_contract["scene_schema_version"] == "1.0", "scene payload schema drift")
    require(workbench_contract["view_schema_version"] == "1.0", "view payload schema drift")
    require(workbench_contract["canonical_write_authorized"] is False, "workbench scene contract canonical-write drift")
    require("document geometry != technical candidate != structural identity" in workbench_contract["invariants"], "workbench geometry/identity invariant missing")
    require("VIEWPORT_PX" in workbench_contract["coordinate_spaces"], "viewport coordinate space must be explicit")
    require("SPATIAL_LOCKED" in workbench_contract["sync_modes"] and "OVERLAY" in workbench_contract["display_modes"], "workbench mode contract incomplete")
    require("WORKING_EDITS" in workbench_contract["layer_ids"] and "ISSUES" in workbench_contract["layer_ids"], "workbench layer vocabulary incomplete")

    for marker in (
        "validate_registration",
        "registration_allows_spatial",
        "resolve_view_state",
        "create_working_edit",
        "validate_working_edit",
        "create_reading_issue",
        "validate_reading_issue",
        "create_view_snapshot",
        "validate_view_snapshot",
        "build_working_session_patch",
        "VIEWPORT_COORDINATES_CANNOT_BE_SCENE_GEOMETRY",
        "WORKING_EDIT_TARGET_READ_ONLY",
        "READING_ISSUE_GRAPHICAL_OR_EVIDENCE_ANCHOR_REQUIRED",
        "VIEW_SCENE_REVISION_MISMATCH",
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
        "REVISION_BOUND_VIEW_SNAPSHOT = PASS",
        "STALE_VIEW_REATTACHMENT = FORBIDDEN",
        "GOVERNED_STRUCTURAL_EDIT = FORBIDDEN",
        "READING_ISSUE_ANCHOR = REQUIRED",
        "WORKING_SESSION_PATCH_AUTHORITY = NONE",
        "VIEWPORT_GEOMETRY_PERSISTENCE = FORBIDDEN",
    ):
        require(marker in workbench_validator, f"workbench negative-test marker missing: {marker}")

    # Managed F3 must be a build-time, exact-revision, complete 4-source asset set.
    for code in ("TAV-05A", "TAV-06A", "TAV-05S", "TAV-06S"):
        require(code in build_managed_f3, f"managed F3 required source missing from builder: {code}")
    for marker in (
        "DPI = 300",
        "TILE_SIZE = 256",
        "OVERLAP = 1",
        "JPEG_QUALITY = 90",
        'OSD_VERSION = "5.0.1"',
        "render_cew_viewer_sources.py",
        "build_cew_source_viewer.py",
        '"vips"',
        '"dzsave"',
        "managed_runtime_dynamic_pdf_rasterization",
        "CEW_MANAGED_F3_ASSET_BUILD = PASS",
    ):
        require(marker in build_managed_f3, f"managed F3 builder marker missing: {marker}")
    require("MANAGED_F3_RUNTIME_REVISION_MISMATCH" in managed_f3, "managed F3 exact-revision guard missing")
    require("MANAGED_F3_REQUIRED_ASSET_MISSING" in managed_f3, "managed F3 completeness guard missing")
    require("managed_runtime_dynamic_pdf_rasterization" in managed_f3, "managed F3 dynamic-raster prohibition missing")
    for marker in (
        "SOURCE_COVERAGE = 4/4",
        "STALE_ASSET_REVISION = REJECTED",
        "DYNAMIC_RUNTIME_RASTERIZATION = false",
        "CANONICAL_WRITE_AUTHORIZED = false",
    ):
        require(marker in managed_f3_validator, f"managed F3 validator marker missing: {marker}")
    require("/workbench/assets/{asset_path:path}" in workbench_api, "managed F3 authenticated asset route missing")
    require("_safe_asset_path" in workbench_api and "relative_to(root)" in workbench_api, "managed F3 path traversal guard missing")
    require("validate_manifest()" in workbench_api, "managed F3 exact-revision serving guard missing")
    require("build_cew_managed_f3_assets.py" in render, "Render build does not produce managed F3 assets")
    require("PyMuPDF==1.26.4" in requirements, "runtime renderer version is not aligned to governed F3 pipeline")

    # Status truth: foundations may advance to PARTIAL, but no blocker is cleared by
    # model/API/build scaffolding alone.
    require(reqs["PWB-005"]["status"] == "AVAILABLE_NOT_INTEGRATED", "PWB-005 reuse classification mismatch")
    require(reqs["PWB-006"]["status"] == "AVAILABLE_NOT_INTEGRATED", "PWB-006 reuse classification mismatch")
    for requirement_id in ("PWB-003", "PWB-007", "PWB-008", "PWB-009", "PWB-011", "PWB-012", "PWB-014", "PWB-015", "PWB-016", "PWB-017", "PWB-018"):
        require(reqs[requirement_id]["status"] == "PARTIAL", f"{requirement_id} foundation classification mismatch")
    for requirement_id in ("PWB-004", "PWB-010", "PWB-013"):
        require(reqs[requirement_id]["status"] == "NOT_IMPLEMENTED", f"{requirement_id} must remain NOT_IMPLEMENTED")

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
    print("CEW_MANAGED_F3_FOUNDATION = VERIFIED_PRESENT")
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
