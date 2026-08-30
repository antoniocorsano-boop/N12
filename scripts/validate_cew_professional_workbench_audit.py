#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "automation/CEW_PROFESSIONAL_WORKBENCH_IMPLEMENTATION_MATRIX_v1.json"
AUDIT = ROOT / "docs/AUDIT/CEW_PROFESSIONAL_EVIDENCE_WORKBENCH_AUDIT_v1.md"
R1_FINDINGS = ROOT / "docs/AUDIT/CEW_PROFESSIONAL_WORKBENCH_PWB005_R1_FINDINGS_v1.md"
R1A_FINDINGS = ROOT / "docs/AUDIT/CEW_PROFESSIONAL_WORKBENCH_PWB005_R1A_FINDINGS_v1.md"
R1_PLAN = ROOT / "docs/PLAN/CEW_PWB005_R1_EVIDENCE_REGION_CONTENT_DIAGNOSTIC_PLAN_v1.md"
R1A_PLAN = ROOT / "docs/PLAN/CEW_PWB005_R1A_REGION_MAPPING_ROOT_CAUSE_PLAN_v1.md"
REUSE = ROOT / "docs/AUDIT/CEW_PROFESSIONAL_WORKBENCH_REUSE_MAP_v1.md"
SCENE = ROOT / "automation/CEW_PROFESSIONAL_WORKBENCH_SCENE_CONTRACT_v1.json"
HVA = ROOT / "automation/CEW_B18_DUAL_WORKSPACE_HVA_CONTRACT_v1.json"
CORE = ROOT / "scripts/cew_professional_workbench_core.py"
CORE_VALIDATOR = ROOT / "scripts/validate_cew_professional_workbench_core.py"
PROJECTION = ROOT / "scripts/cew_professional_workbench_projection.py"
API = ROOT / "scripts/cew_professional_workbench_api.py"
CLIENT = ROOT / "scripts/cew_professional_workbench_client.py"
CLIENT_VALIDATOR = ROOT / "scripts/validate_cew_professional_workbench_client.py"
CLIENT_WORKFLOW = ROOT / ".github/workflows/validate-cew-professional-workbench-client.yml"
PROJECT_HOME = ROOT / "scripts/cew_project_home.py"
SOURCE_VIEWER = ROOT / "scripts/build_cew_source_viewer.py"
ERW = ROOT / "scripts/build_cew_erw_synced_workspace.py"
DUAL_VECTOR = ROOT / "scripts/cew_dual_vector_agreement.py"
GEOMETRY_BUILDER = ROOT / "scripts/build_cew_document_geometry_artifacts.py"
GEOMETRY_VALIDATOR = ROOT / "scripts/validate_cew_document_geometry_artifacts.py"
GEOMETRY_ADAPTER = ROOT / "scripts/validate_cew_document_geometry_scene_adapter.py"
R1_BUILDER = ROOT / "scripts/build_cew_evidence_region_content_diagnostic.py"
R1_VALIDATOR = ROOT / "scripts/validate_cew_evidence_region_content_diagnostic.py"
R1A_BUILDER = ROOT / "scripts/build_cew_evidence_region_mapping_root_cause.py"
R1A_VALIDATOR = ROOT / "scripts/validate_cew_evidence_region_mapping_root_cause.py"
F3_BUILDER = ROOT / "scripts/build_cew_managed_f3_assets.py"
F3_RUNTIME = ROOT / "scripts/cew_managed_f3_assets.py"
RUNTIME_SMOKE = ROOT / "scripts/validate_cew_professional_workbench_runtime_smoke.py"
RENDER = ROOT / "render.yaml"
RENDER_BUILD = ROOT / "scripts/render_build_candidate.sh"
REQUIREMENTS = ROOT / "requirements.txt"
CLIENT_VERIFIED_CANDIDATE = "9296d82a02ce1d4e2e171f64c937e828094cca2d"


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def text(path: Path) -> str:
    require(path.is_file(), f"missing evidence: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def load(path: Path) -> dict:
    return json.loads(text(path))


def main() -> int:
    matrix = load(MATRIX)
    reqs = {row["id"]: row for row in matrix["requirements"]}
    blockers = matrix["blocking_requirement_ids"]

    require(matrix["schema_version"] == "1.6", "matrix must be schema 1.6")
    require(matrix["status"] == "CLIENT_INTEGRATION_VERIFIED_PWB005_BLOCKED", "matrix status drift")
    require(matrix["client_integration_verified_candidate"] == CLIENT_VERIFIED_CANDIDATE, "client integration verified candidate drift")
    require(matrix["professional_workbench_readiness"] == "REWORK_REQUIRED", "workbench must remain REWORK_REQUIRED")
    require(matrix["hva_execution_authorized"] is False, "HVA must remain blocked")
    require(matrix["b1_promotion_authorized"] is False, "B1 promotion must remain blocked")
    require(matrix["canonical_write_authorized"] is False, "canonical write must remain blocked")
    require(set(reqs) == {f"PWB-{i:03d}" for i in range(1, 19)}, "PWB requirement inventory drift")

    for rid in blockers:
        require(rid in reqs, f"unknown blocker {rid}")
        require(reqs[rid]["status"] != "IMPLEMENTED", f"blocker {rid} cannot be IMPLEMENTED")

    require(reqs["PWB-001"]["status"] == "IMPLEMENTED", "PWB-001 regression")
    require(reqs["PWB-002"]["status"] == "IMPLEMENTED", "PWB-002 regression")
    require(reqs["PWB-004"]["status"] == "IMPLEMENTED", "PWB-004 client integration regression")
    require(reqs["PWB-006"]["status"] == "IMPLEMENTED", "PWB-006 client integration regression")
    require("PWB-006" not in blockers, "PWB-006 must leave blocker list after selectable-object integration")
    require(reqs["PWB-013"]["status"] == "IMPLEMENTED", "PWB-013 progressive-disclosure regression")
    require(reqs["PWB-005"]["status"] == "PARTIAL", "PWB-005 must remain PARTIAL")
    require("PWB-005" in blockers, "PWB-005 must remain a blocker")
    for rid in ("PWB-003", "PWB-005", "PWB-007", "PWB-008", "PWB-009", "PWB-010", "PWB-011", "PWB-012", "PWB-014", "PWB-015", "PWB-016", "PWB-017", "PWB-018"):
        require(reqs[rid]["status"] == "PARTIAL", f"{rid} must remain PARTIAL")

    finding = reqs["PWB-005"]["finding"]
    expected_regions = {
        "CEW-N12-REG-G01-R06",
        "CEW-N12-REG-G05-R04",
        "CEW-N12-REG-G07-R07",
        "CEW-N12-REG-T6A-G03",
    }
    require(finding["governed_regions"] == 4, "R1 governed-region count drift")
    require(finding["dual_vector_comparable_regions"] == 0, "R1 vector-comparable count drift")
    require(finding["published_document_primitives"] == 0, "R1 cannot claim document primitives")
    require(set(finding["raster_regions"]) == expected_regions, "R1.1 raster set must be 4/4")
    require(finding["region_mapping_error_regions"] == [], "R1A must clear false diagnostic mapping errors")
    require(finding["r1a_root_cause"] == "FLOATING_POINT_CONTAINMENT_TOLERANCE", "R1A root cause drift")
    require(finding["canonical_provenance_repair_required"] is False, "R1A must not require canonical repair")
    require(finding["containment_method"] == "SOURCE_PAGE_EDGE_TOLERANCE", "R1.1 containment method drift")
    require(finding["containment_tolerance_pt"] == 0.01, "R1.1 containment tolerance drift")

    audit = text(AUDIT)
    for marker in (
        "AUDIT_COMPLETE — REWORK_REQUIRED_BEFORE_HVA",
        "PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED",
        "HVA_EXECUTION_AUTHORIZED = false",
        "CANONICAL_WRITE_AUTHORIZED = false",
        "document geometry != technical candidate != structural identity",
    ):
        require(marker in audit, f"base audit invariant missing: {marker}")

    r1 = text(R1_FINDINGS)
    for marker in (
        "R1_COMPLETE_VERIFIED_RASTER_4_OF_4",
        "RASTER = 4",
        "REGION_MAPPING_ERROR = 0",
        "VECTOR = 0",
        "R1_RASTER_REGION_COVERAGE = 4/4",
        "PWB-005 = PARTIAL_BLOCKED",
        "HVA_EXECUTION_AUTHORIZED = false",
        "CANONICAL_WRITE_AUTHORIZED = false",
    ):
        require(marker in r1, f"R1 final finding marker missing: {marker}")

    r1a = text(R1A_FINDINGS)
    for marker in (
        "R1A_COMPLETE_DIAGNOSTIC_DEFECT_ISOLATED",
        "FLOATING_POINT_CONTAINMENT_TOLERANCE",
        "0.0155378622",
        "0.398352060467",
        "PROVENANCE_REPAIR_AUTHORIZED = false",
        "CANONICAL_WRITE_AUTHORIZED = false",
    ):
        require(marker in r1a, f"R1A finding marker missing: {marker}")

    for marker in ("VECTOR", "RASTER", "TEXT", "MIXED", "REGION_MAPPING_ERROR", "EMPTY", "No OCR is used in R1"):
        require(marker in text(R1_PLAN), f"R1 plan marker missing: {marker}")
    for marker in ("FLOATING_POINT_CONTAINMENT_TOLERANCE", "0.01 pt", "DIAGNOSTIC != PROVENANCE_REPAIR"):
        require(marker in text(R1A_PLAN), f"R1A plan marker missing: {marker}")

    scene = load(SCENE)
    require(scene["canonical_write_authorized"] is False, "scene authority drift")
    require("document geometry != technical candidate != structural identity" in scene["invariants"], "scene geometry/identity invariant missing")
    require("OVERLAY" in scene["display_modes"] and "SPATIAL_LOCKED" in scene["sync_modes"], "scene mode vocabulary incomplete")

    core = text(CORE)
    for marker in ("validate_registration", "create_working_edit", "create_reading_issue", "create_view_snapshot", "VIEWPORT_COORDINATES_CANNOT_BE_SCENE_GEOMETRY"):
        require(marker in core, f"kernel marker missing: {marker}")
    for marker in ("OVERLAY_WITHOUT_VERIFIED_REGISTRATION = FAIL_CLOSED", "STALE_VIEW_REATTACHMENT = FORBIDDEN", "GOVERNED_STRUCTURAL_EDIT = FORBIDDEN"):
        require(marker in text(CORE_VALIDATOR), f"kernel negative test missing: {marker}")

    projection = text(PROJECTION)
    require("F3_DZI_MANIFEST_REUSED" in projection, "F3 projection reuse missing")
    require("F6_ERW_M0G_FROZEN_LEDGER_ADAPTER" in projection, "F6 projection reuse missing")
    require("NO_VERIFIED_SOURCE_TO_TECHNICAL_REGISTRATION_IN_CURRENT_CEW_RECORDS" in projection, "registration fail-closed marker missing")

    client = text(CLIENT)
    for marker in (
        "F3_DZI_OPENSEADRAGON_REUSED",
        "WORKBENCH_SCENE_OBJECTS_RENDERED_AS_SVG",
        "EXPLICIT_EVIDENCE_LINK_ONLY",
        "OVERLAY_DISABLED_WITHOUT_VERIFIED_REGISTRATION",
        "OBJECT_ANCHORED_NON_CANONICAL_WORKING_EDIT",
        "GRAPHICALLY_ANCHORED_NON_CANONICAL_READING_ISSUE",
        "WORK_EVIDENCE_PROVENANCE",
        "/api/workbench/scene?task=",
    ):
        require(marker in client, f"professional client integration marker missing: {marker}")
    client_validator = text(CLIENT_VALIDATOR)
    for marker in (
        "CEW_PROFESSIONAL_WORKBENCH_CLIENT_INTEGRATION = PASS",
        "PRIMARY_CHROME_INTERNAL_IDS_HIDDEN = PASS",
        "HVA_EXECUTION_AUTHORIZED = false",
        "CANONICAL_WRITE_AUTHORIZED = false",
    ):
        require(marker in client_validator, f"client validator marker missing: {marker}")
    require("Validate CEW Professional Workbench Client" in text(CLIENT_WORKFLOW), "client CI gate missing")
    require('/workbench?task={quote(task.get(\'task_id\',\'\'))}' in text(PROJECT_HOME), "Project Home does not enter professional Workbench")
    require('@router.get("/workbench", response_class=HTMLResponse)' in text(API), "professional Workbench route missing")
    require("Progetto N12 › Evidenza › Revisione tecnica" in text(API), "primary Workbench chrome must hide internal task id")

    require("openseadragon" in text(SOURCE_VIEWER).lower(), "OpenSeadragon foundation missing")
    require("svg" in text(ERW).lower(), "F6 SVG foundation missing")
    require(all(state in text(DUAL_VECTOR) for state in ("AGREE", "PARTIAL", "DISAGREE")), "dual-vector vocabulary missing")

    require("GOVERNED_EVIDENCE_REGION_WHERE_AVAILABLE" in text(GEOMETRY_BUILDER), "claim-scoped geometry build missing")
    require("UNMATCHED_GEOMETRY_PUBLICATION = FORBIDDEN" in text(GEOMETRY_VALIDATOR), "unmatched geometry guard missing")
    require("COMPARABLE_VECTOR_REGION_COUNT" in text(GEOMETRY_ADAPTER), "real-source vector diagnostic missing")
    require("REGION_EDGE_TOLERANCE_PT = 0.01" in text(R1_BUILDER), "R1.1 containment remediation missing")
    require("SOURCE_PAGE_EDGE_TOLERANCE" in text(R1_BUILDER), "R1.1 containment method missing")
    require("R1A_REMEDIATION = PASS" in text(R1_VALIDATOR), "R1.1 remediation validator missing")
    require("FLOATING_POINT_CONTAINMENT_TOLERANCE" in text(R1A_BUILDER), "R1A diagnostic root-cause vocabulary missing")
    require("PROVENANCE_REPAIR_AUTHORIZED = false" in text(R1A_VALIDATOR), "R1A provenance-repair guard missing")

    f3 = text(F3_BUILDER)
    for marker in ("DPI = 300", "TILE_SIZE = 256", "OVERLAP = 1", "JPEG_QUALITY = 90", 'OSD_VERSION = "5.0.1"'):
        require(marker in f3, f"managed F3 marker missing: {marker}")
    require("MANAGED_F3_RUNTIME_REVISION_MISMATCH" in text(F3_RUNTIME), "F3 revision guard missing")
    require("/workbench/assets/{asset_path:path}" in text(API), "authenticated asset route missing")
    require("FASTAPI_INCLUDED_ROUTER_TREE = PASS" in text(RUNTIME_SMOKE), "runtime route-tree smoke missing")

    render = text(RENDER)
    render_build = text(RENDER_BUILD)
    require("buildCommand: bash scripts/render_build_candidate.sh" in render, "Render candidate build delegation missing")
    require('key: CEW_R2HR_STRICT_RUNTIME' in render and 'value: "1"' in render, "Render strict R2HR runtime guard missing")
    for marker in (
        "build_cew_managed_f3_assets.py",
        "build_cew_human_gap_review_receipts.py",
        "validate_cew_human_gap_review_receipts.py",
        "validate_cew_b18_hva_hardening.py",
        "CEW_RENDER_R2HR_RUNTIME_ARTIFACT = READY",
        "CEW_RENDER_R2HR_REGION_COVERAGE = 4/4",
        "CEW_RENDER_R2HR_GAP_TOTAL = 10",
    ):
        require(marker in render_build, f"Render delegated build missing marker: {marker}")

    require("PyMuPDF==1.26.4" in text(REQUIREMENTS), "runtime PyMuPDF pin drift")

    hva = load(HVA)
    require(hva["human_hva_state"] == "REQUIRED_NOT_SATISFIED", "human HVA unexpectedly satisfied")
    require(hva["canonical_write_authorized"] is False, "HVA cannot authorize canonical writes")

    reuse = text(REUSE)
    for marker in ("F3 Source Viewer", "Dual Vector Agreement", "F6 ERW Synchronized Workspace"):
        require(marker in reuse, f"reuse map marker missing: {marker}")

    implemented = sorted(rid for rid, row in reqs.items() if row["status"] == "IMPLEMENTED")
    partial = sorted(rid for rid, row in reqs.items() if row["status"] == "PARTIAL")
    available = sorted(rid for rid, row in reqs.items() if row["status"] == "AVAILABLE_NOT_INTEGRATED")
    missing = sorted(rid for rid, row in reqs.items() if row["status"] == "NOT_IMPLEMENTED")

    print("CEW_PROFESSIONAL_WORKBENCH_AUDIT_CONSISTENCY = PASS")
    print("CEW_PROFESSIONAL_WORKBENCH_CLIENT_RECONCILIATION = PASS")
    print("CLIENT_INTEGRATION_VERIFIED_CANDIDATE = " + CLIENT_VERIFIED_CANDIDATE)
    print("PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED")
    print("PWB005 = PARTIAL_BLOCKED")
    print("PWB005_VECTOR_COMPARABLE_REGIONS = 0/4")
    print("PWB005_RASTER_REGIONS = 4/4")
    print("PWB005_REGION_MAPPING_ERRORS = 0")
    print("R1A_PROVENANCE_REPAIR_REQUIRED = false")
    print("IMPLEMENTED = " + ",".join(implemented))
    print("PARTIAL = " + ",".join(partial))
    print("AVAILABLE_NOT_INTEGRATED = " + ",".join(available))
    print("NOT_IMPLEMENTED = " + ",".join(missing))
    print("BLOCKERS = " + ",".join(blockers))
    print("HVA_EXECUTION_AUTHORIZED = false")
    print("B1_PROMOTION_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
