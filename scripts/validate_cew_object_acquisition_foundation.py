#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_OBJECT_ACQUISITION_CONTRACT_v1.json"
QUEUE = ROOT / "automation" / "CEW_OBJECT_ACQUISITION_QUEUE_v1.json"
DOC = ROOT / "docs" / "PROGRAM" / "CEW_OBJECT_ACQUISITION_DEVELOPMENT_LOGIC_v1.md"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    doc = DOC.read_text(encoding="utf-8")

    require(contract["slice"] == "OA-0", "contract must govern OA-0")
    require(contract["priority_invariant"] == "ACQUISITION_BEFORE_MODELING", "acquisition priority missing")
    require(contract["canonical_write_authorized"] is False, "OA-0 must not authorize canonical writes")
    require(contract["engineering_authority_effect"] == "NONE", "OA-0 must not create engineering authority")
    require(contract["source_authority"]["primary_authority"] == "IMMUTABLE_SOURCE_DOCUMENT", "source authority drift")
    require(contract["source_authority"]["crop_role"] == "EVIDENCE_ONLY_NOT_PRIMARY_WORK_SURFACE", "crop cannot become primary work object")

    expected_chain = [
        "SOURCE_ACQUISITION",
        "DOCUMENT_REGISTRATION",
        "OBJECT_TYPE_PASS",
        "OBJECT_PROTOTYPE",
        "FIND_SIMILAR",
        "HUMAN_CLUSTER_REVIEW",
        "CANONICAL_CAD_OBJECT_PROPOSAL",
        "STRUCTURAL_IDENTITY_REVIEW",
        "PROJECT_MATERIAL_READY",
    ]
    require(contract["process_chain"] == expected_chain, "process chain order changed")

    forbidden = set(contract["forbidden_shortcuts"])
    require("VISUAL_SIMILARITY_CREATES_STRUCTURAL_IDENTITY" in forbidden, "similarity identity shortcut not forbidden")
    require("M0_G_M0_S_M0_A_USED_TO_REPAIR_UPSTREAM_GAPS" in forbidden, "downstream repair shortcut not forbidden")

    gate_names = [g["name"] for g in contract["promotion_gates"]]
    require(gate_names == ["SOURCE_READY", "OBJECT_ACQUIRED", "OBJECT_CLASSIFIED", "HUMAN_VERIFIED", "STRUCTURAL_IDENTITY"], "OA gate chain drift")
    require(contract["project_material_gate"]["state"] == "BLOCKED", "project material must start blocked")
    require(contract["human_workbench"]["primary_surface"] == "CANONICAL_CAD_VIEW", "Workbench must remain CAD-first")
    require(contract["human_workbench"]["must_show_blockers"] is True, "Workbench must show blockers")
    require(contract["similarity_model"]["v1"] == "DETERMINISTIC_FIRST", "OA-3 must start deterministic")
    require(contract["similarity_model"]["confidence_is_authority"] is False, "similarity confidence cannot be authority")
    require(contract["integration"]["extends_existing_professional_workbench"] is True, "OA must extend existing Workbench")
    require(contract["integration"]["second_parallel_product_forbidden"] is True, "parallel OA product forbidden")
    require(contract["integration"]["current_hva_authorized"] is False, "OA-0 must preserve HVA hold")

    require(queue["current_item"] == "OA-0", "OA-0 must remain current until validation")
    ids = [i["id"] for i in queue["items"]]
    require(ids == ["OA-0", "OA-1", "OA-2", "OA-3", "OA-4", "OA-5", "OA-6"], "OA development order drift")
    require(queue["items"][1]["state"] == "BLOCKED_BY_OA0", "OA-1 must be blocked by OA-0")
    require(queue["pilot"]["object_type"] == "COLUMN", "first pilot must remain COLUMN")
    require(queue["global_blocks"]["project_material_ready"] is False, "project material cannot start ready")

    for phrase in [
        "The unit of document understanding is an **object**, not a line and not a crop.",
        "OA extends the existing Professional Workbench at `/workbench`; it must not create a parallel product.",
        "M0-G, M0-S, M0-A, EdiLus, FEM, assessment and intervention design are downstream consumers.",
    ]:
        require(phrase in doc, f"missing governing statement: {phrase}")

    print("CEW_OBJECT_ACQUISITION_FOUNDATION_PASS")


if __name__ == "__main__":
    main()
