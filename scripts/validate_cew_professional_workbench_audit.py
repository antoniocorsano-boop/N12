#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "automation/CEW_PROFESSIONAL_WORKBENCH_IMPLEMENTATION_MATRIX_v1.json"
AUDIT = ROOT / "docs/AUDIT/CEW_PROFESSIONAL_EVIDENCE_WORKBENCH_AUDIT_v1.md"
DUAL = ROOT / "scripts/cew_b1_dual_workspace.py"
VIEWER = ROOT / "scripts/cew_evidence_viewer_interaction.py"
HVA = ROOT / "automation/CEW_B18_DUAL_WORKSPACE_HVA_CONTRACT_v1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    audit = AUDIT.read_text(encoding="utf-8")
    dual = DUAL.read_text(encoding="utf-8")
    viewer = VIEWER.read_text(encoding="utf-8")
    hva = json.loads(HVA.read_text(encoding="utf-8"))

    require(matrix["schema_version"] == "1.0", "unexpected matrix schema")
    require(matrix["professional_workbench_readiness"] == "REWORK_REQUIRED", "workbench must remain REWORK_REQUIRED")
    require(matrix["hva_execution_authorized"] is False, "HVA must remain paused")
    require(matrix["b1_promotion_authorized"] is False, "B1 promotion must remain unauthorized")
    require(matrix["canonical_write_authorized"] is False, "canonical write must remain unauthorized")

    reqs = {item["id"]: item for item in matrix["requirements"]}
    blockers = matrix["blocking_requirement_ids"]
    require(blockers, "blocking requirements cannot be empty")
    for requirement_id in blockers:
        require(requirement_id in reqs, f"missing blocking requirement {requirement_id}")
        require(reqs[requirement_id]["status"] != "IMPLEMENTED", f"blocker {requirement_id} cannot be marked implemented without audit update")

    # Audit decision must be explicit and fail closed.
    for marker in (
        "AUDIT_COMPLETE — REWORK_REQUIRED_BEFORE_HVA",
        "PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED",
        "HVA_EXECUTION_AUTHORIZED = false",
        "B1_PROMOTION_AUTHORIZED = false",
        "CANONICAL_WRITE_AUTHORIZED = false",
        "document geometry != technical candidate != structural identity",
    ):
        require(marker in audit, f"audit marker missing: {marker}")

    # Verify strengths that the matrix marks as implemented/partial.
    require("canonical_write_authorized" in dual and "False" in dual, "dual workspace canonical-write boundary missing")
    require("sessionStorage" in dual, "session-only proposal boundary missing")
    require("geometry != identity" in dual, "geometry/identity warning missing")
    require("evidenceViewport" in viewer, "interactive evidence viewport missing")
    require("zoomBy" in viewer and "pointermove" in viewer and "keydown" in viewer, "zoom/pan/keyboard interaction markers missing")

    # Verify the current blocking architecture truthfully remains the POC audited above.
    require("<iframe" in dual, "matrix expects iframe-composed source panel; update matrix/audit if architecture changed")
    require("region-map" in dual and "region-box" in dual, "matrix expects documentary region placeholder; update matrix/audit if technical scene changed")
    require("<textarea id=\"proposalText\"" in dual, "matrix expects detached proposal textarea; update matrix/audit if object editing changed")
    require("html_text.replace" in viewer, "matrix expects string-replacement viewer enhancement; update matrix/audit if client architecture changed")

    # The current HVA still cannot claim the redesigned professional workflow is satisfied.
    require(hva["human_hva_state"] == "REQUIRED_NOT_SATISFIED", "human HVA must remain unsatisfied")
    require(hva["canonical_write_authorized"] is False, "HVA contract cannot authorize canonical writes")
    require(reqs["PWB-018"]["status"] == "PARTIAL", "professional HVA protocol must remain PARTIAL until redesigned")

    implemented = sorted(rid for rid, row in reqs.items() if row["status"] == "IMPLEMENTED")
    partial = sorted(rid for rid, row in reqs.items() if row["status"] == "PARTIAL")
    missing = sorted(rid for rid, row in reqs.items() if row["status"] == "NOT_IMPLEMENTED")

    print("CEW_PROFESSIONAL_WORKBENCH_AUDIT_CONSISTENCY = PASS")
    print("PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED")
    print(f"IMPLEMENTED = {','.join(implemented)}")
    print(f"PARTIAL = {','.join(partial)}")
    print(f"NOT_IMPLEMENTED = {','.join(missing)}")
    print(f"BLOCKERS = {','.join(blockers)}")
    print("HVA_EXECUTION_AUTHORIZED = false")
    print("B1_PROMOTION_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")


if __name__ == "__main__":
    main()
