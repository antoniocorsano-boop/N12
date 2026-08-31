#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import cew_oa_governed_audit as governed

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
API = ROOT / "scripts" / "cew_oa_governed_api.py"
QUEUE = ROOT / "automation" / "CEW_OBJECT_ACQUISITION_QUEUE_v1.json"
OAG5 = ROOT / "automation" / "CEW_OAG5_EXPLICIT_STRUCTURAL_IDENTITY_REVIEW_CONTRACT_v1.json"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def payload(source, **extra):
    return {
        "source_evidence": dict(source),
        "canonical_write_authorized": False,
        "project_material_ready": False,
        **extra,
    }


def main():
    source = {
        "source_version_id": "SV-TEST",
        "page_id": "PAGE-TEST",
        "evidence_region_id": "ER-TEST",
        "source_sha256": "a" * 64,
    }

    oa2 = governed.build_receipt(
        task_id="ERW-N12-001",
        stage="OA2_PROTOTYPE",
        payload=payload(source, state="HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE", prototype_id="OAP-1"),
        expected_source=source,
        revision="REV-1",
        reviewer="HUMAN-A",
        parent=None,
        timestamp="2026-08-31T00:00:00+00:00",
    )
    oa4 = governed.build_receipt(
        task_id="ERW-N12-001",
        stage="OA4_CLUSTER_REVIEW",
        payload=payload(source, state="HUMAN_REVIEWED_FAMILY_CANDIDATES", similarity_run_fingerprint="sim-1"),
        expected_source=source,
        revision="REV-1",
        reviewer="HUMAN-A",
        parent=oa2,
        timestamp="2026-08-31T00:01:00+00:00",
    )
    oa5 = governed.build_receipt(
        task_id="ERW-N12-001",
        stage="OA5_IDENTITY_CANDIDATE",
        payload=payload(source, candidate_state="READY_FOR_EXPLICIT_IDENTITY_REVIEW", accepted_structural_identity=False),
        expected_source=source,
        revision="REV-1",
        reviewer="HUMAN-A",
        parent=oa4,
        timestamp="2026-08-31T00:02:00+00:00",
    )
    oag5 = governed.build_receipt(
        task_id="ERW-N12-001",
        stage="OA_G5_IDENTITY_DECISION",
        payload=payload(
            source,
            decision="ACCEPT_STRUCTURAL_IDENTITY",
            human_attestation=True,
            accepted_structural_identity=True,
            identity_candidate_receipt_fingerprint=oa5["receipt_fingerprint"],
        ),
        expected_source=source,
        revision="REV-1",
        reviewer="HUMAN-A",
        parent=oa5,
        timestamp="2026-08-31T00:03:00+00:00",
    )

    require(oa4["parent_decision_id"] == oa2["decision_id"], "OA4 parent chain missing")
    require(oa5["parent_decision_id"] == oa4["decision_id"], "OA5 parent chain missing")
    require(oag5["parent_decision_id"] == oa5["decision_id"], "OAG5 parent chain missing")
    require(oag5["canonical_write_authorized"] is False, "OAG5 authorized canonical write")
    require(oag5["project_material_ready"] is False, "OAG5 released project material")
    require(oag5["engineering_authority_effect"] == "IDENTITY_REVIEW_ONLY", "OAG5 authority boundary drift")

    for child, expected_stage in [(oa4, "OA2_PROTOTYPE"), (oa5, "OA4_CLUSTER_REVIEW"), (oag5, "OA5_IDENTITY_CANDIDATE")]:
        require(child["parent_receipt_fingerprint"], f"{expected_stage} fingerprint link missing")

    try:
        governed.build_receipt(
            task_id="ERW-N12-001",
            stage="OA5_IDENTITY_CANDIDATE",
            payload=payload(source, candidate_state="READY_FOR_EXPLICIT_IDENTITY_REVIEW"),
            expected_source=source,
            revision="REV-1",
            reviewer="H",
            parent=oa2,
        )
    except ValueError as exc:
        require("PARENT_STAGE_MISMATCH" in str(exc), "wrong parent stage was not rejected correctly")
    else:
        raise SystemExit("FAIL: OA5 accepted OA2 as direct parent")

    stale = dict(source, source_sha256="b" * 64)
    try:
        governed.build_receipt(
            task_id="ERW-N12-001",
            stage="OA4_CLUSTER_REVIEW",
            payload=payload(stale, state="HUMAN_REVIEWED_FAMILY_CANDIDATES"),
            expected_source=source,
            revision="REV-1",
            reviewer="H",
            parent=oa2,
        )
    except ValueError as exc:
        require("SOURCE_MISMATCH" in str(exc), "stale source mismatch not rejected")
    else:
        raise SystemExit("FAIL: stale source accepted")

    try:
        governed.build_receipt(
            task_id="ERW-N12-001",
            stage="OA_G5_IDENTITY_DECISION",
            payload=payload(
                source,
                decision="ACCEPT_STRUCTURAL_IDENTITY",
                human_attestation=False,
                accepted_structural_identity=True,
                identity_candidate_receipt_fingerprint=oa5["receipt_fingerprint"],
            ),
            expected_source=source,
            revision="REV-1",
            reviewer="H",
            parent=oa5,
        )
    except ValueError as exc:
        require("HUMAN_ATTESTATION_REQUIRED" in str(exc), "OAG5 acceptance without attestation not rejected")
    else:
        raise SystemExit("FAIL: synthetic/unattested identity acceptance accepted")

    try:
        governed.build_receipt(
            task_id="ERW-N12-001",
            stage="OA_G5_IDENTITY_DECISION",
            payload=payload(
                source,
                decision="ACCEPT_STRUCTURAL_IDENTITY",
                human_attestation=True,
                accepted_structural_identity=True,
                identity_candidate_receipt_fingerprint="deadbeef",
            ),
            expected_source=source,
            revision="REV-1",
            reviewer="H",
            parent=oa5,
        )
    except ValueError as exc:
        require("CANDIDATE_FINGERPRINT_MISMATCH" in str(exc), "wrong OA5 candidate fingerprint not rejected")
    else:
        raise SystemExit("FAIL: wrong OA5 candidate fingerprint accepted")

    try:
        governed.build_receipt(
            task_id="ERW-N12-001",
            stage="OA_G5_IDENTITY_DECISION",
            payload=payload(
                source,
                decision="REJECT_STRUCTURAL_IDENTITY",
                human_attestation=False,
                accepted_structural_identity=True,
                identity_candidate_receipt_fingerprint=oa5["receipt_fingerprint"],
            ),
            expected_source=source,
            revision="REV-1",
            reviewer="H",
            parent=oa5,
        )
    except ValueError as exc:
        require("NON_ACCEPT_DECISION_CANNOT_ACCEPT_IDENTITY" in str(exc), "reject/accepted inconsistency not rejected")
    else:
        raise SystemExit("FAIL: reject decision accepted structural identity")

    app = APP.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    require("import cew_oa_governed_api as oa_governed_api" in app, "OA governed API not imported by app")
    require("app.include_router(oa_governed_api.build_router(source_workspace))" in app, "OA governed API not mounted")
    require("audit_store.persist_runtime_receipt" in api, "OA API does not persist to common audit store")
    require("audit_store.load_runtime_receipts" in api, "OA API cannot read governed append-only lineage")
    require('"session_storage_role": "UI_CACHE_ONLY"' in api, "session storage role not demoted to cache")
    require("/api/workbench/object-acquisition/receipt" in api, "OA persistence endpoint missing")
    require("/api/workbench/object-acquisition/status" in api, "OA status endpoint missing")

    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    items = {item["id"]: item for item in queue["items"]}
    require(items["OA-6"]["state"] == "BLOCKED_BY_OA5", "OA6 must remain blocked while OA5/OAG5 are not completed")
    require(queue["global_blocks"]["project_material_ready"] is False, "project material became ready prematurely")
    require(queue["global_blocks"]["canonical_write_authorized"] is False, "canonical write became authorized")

    contract = json.loads(OAG5.read_text(encoding="utf-8"))
    require(contract["canonical_write_authorized"] is False, "OAG5 contract canonical write drift")
    require(set(contract["decisions"]) == governed.OAG5_DECISIONS, "OAG5 governed decisions drift from canonical contract")
    require(contract["acceptance_effect"]["canonical_write_authorized"] is False, "OAG5 acceptance enabled canonical write")
    require(contract["acceptance_effect"]["project_material_ready"] is False, "OAG5 acceptance released project material")
    require(contract["non_acceptance_effect"]["canonical_write_authorized"] is False, "OAG5 non-acceptance canonical write drift")
    require(contract["non_acceptance_effect"]["project_material_ready"] is False, "OAG5 non-acceptance project material drift")
    require(contract["automation_may_create_acceptance"] is False, "automation may create OAG5 acceptance")
    require(contract["synthetic_test_receipt_is_project_evidence"] is False, "synthetic receipt treated as project evidence")

    print("OA_GOVERNED_APPEND_ONLY_LINEAGE_PASS")
    print("OA_GOVERNED_WORKBENCH_API_MOUNT_PASS")
    print("OA_G5_REMAINS_HUMAN_EXPLICIT_PASS")
    print("OA6_REMAINS_BLOCKED_PASS")


if __name__ == "__main__":
    main()
