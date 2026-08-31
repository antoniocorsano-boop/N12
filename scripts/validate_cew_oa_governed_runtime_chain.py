#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OA2 = ROOT / "scripts/cew_oa2_workbench_runtime.py"
OA4 = ROOT / "scripts/cew_oa4_workbench_runtime.py"
OA5 = ROOT / "scripts/cew_oa5_workbench_runtime.py"
OAG5 = ROOT / "scripts/cew_oag5_workbench_runtime.py"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    oa2 = OA2.read_text(encoding="utf-8")
    oa4 = OA4.read_text(encoding="utf-8")
    oa5 = OA5.read_text(encoding="utf-8")
    oag5 = OAG5.read_text(encoding="utf-8")
    endpoint = "/api/workbench/object-acquisition/receipt"

    require(endpoint in oa2 and "stage:'OA2_PROTOTYPE'" in oa2, "OA2 is not governed-persistent")
    require("governed_receipt_id" in oa2, "OA2 governed receipt id not cached")
    require("sessionStorage è soltanto cache UI" in oa2, "OA2 session-state authority not demoted")
    require("La catena downstream resta bloccata" in oa2, "OA2 does not fail closed on persistence failure")

    require(endpoint in oa4 and "stage:'OA4_CLUSTER_REVIEW'" in oa4, "OA4 is not governed-persistent")
    require("parent_decision_id:parentId" in oa4, "OA4 does not link to OA2 parent receipt")
    require("p?.governed_receipt_id" in oa4, "OA4 does not require governed OA2 prototype")
    require("OA-5 resta bloccata" in oa4, "OA4 does not fail closed on persistence failure")

    require(endpoint in oa5 and "stage:'OA5_IDENTITY_CANDIDATE'" in oa5, "OA5 is not governed-persistent")
    require("parent_decision_id:review.governed_receipt_id" in oa5, "OA5 does not link to OA4 parent receipt")
    require("if(!review?.governed_receipt_id)" in oa5, "OA5 does not require governed OA4 review")
    require("OA-G5 resta bloccato" in oa5, "OA5 does not fail closed on persistence failure")
    require("accepted_structural_identity:false" in oa5, "OA5 auto-accept boundary missing")

    require(endpoint in oag5 and "stage:'OA_G5_IDENTITY_DECISION'" in oag5, "OAG5 is not governed-persistent")
    require("parent_decision_id:candidate.governed_receipt_id" in oag5, "OAG5 does not link to OA5 parent receipt")
    require("candidate.candidate_state!=='READY_FOR_EXPLICIT_IDENTITY_REVIEW'" in oag5, "OAG5 admits non-ready candidates")
    require("decision==='ACCEPT_STRUCTURAL_IDENTITY'&&!attested" in oag5, "OAG5 human attestation not enforced")
    require("canonical_write_authorized:false" in oag5, "OAG5 canonical write boundary missing")
    require("project_material_ready:false" in oag5, "OAG5 project material boundary missing")
    require("OA-6 resta un gate separato" in oag5, "OAG5/OA6 separation not visible")
    require("CEW_OA6_RUNTIME" not in oag5, "OA6 runtime leaked into OAG5")

    for text in (oa2, oa4, oa5, oag5):
        require("canonical_write_authorized:true" not in text, "canonical write authority leaked into OA runtime")
        require("project_material_ready:true" not in text, "project material readiness leaked into OA runtime")

    print("OA_GOVERNED_RUNTIME_CHAIN_PASS")
    print("OA2_OA4_OA5_OAG5_PARENT_LINK_PASS")
    print("SESSION_STORAGE_UI_CACHE_ONLY_PASS")
    print("OA6_RUNTIME_REMAINS_ABSENT_PASS")


if __name__ == "__main__":
    main()
