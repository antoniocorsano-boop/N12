#!/usr/bin/env python3
import json
from pathlib import Path

from cew_oa5_structural_resolver import resolve_identity_candidate
from cew_oa5_workbench_runtime import OA5_RUNTIME_MARKER
import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_OA5_STRUCTURAL_RESOLVER_CONTRACT_v1.json"
QUEUE = ROOT / "automation" / "CEW_OBJECT_ACQUISITION_QUEUE_v1.json"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    items = {item["id"]: item for item in queue["items"]}

    require(queue["current_item"] == "OA-5", "OA-5 must be current")
    require(items["OA-4"]["state"] == "COMPLETE_PASS", "OA-4 must remain complete")
    require(items["OA-5"]["state"] == "IN_PROGRESS", "OA-5 must be in progress")
    require(items["OA-6"]["state"] == "BLOCKED_BY_OA5", "OA-6 must remain blocked")
    require(contract["minimum_identity_rule"]["proximity_only_forbidden"] is True, "proximity identity shortcut must be forbidden")
    require(contract["minimum_identity_rule"]["similarity_only_forbidden"] is True, "similarity identity shortcut must be forbidden")
    require(contract["minimum_identity_rule"]["family_membership_only_forbidden"] is True, "family identity shortcut must be forbidden")
    require(contract["output"]["accepted_structural_identity"] is False, "OA-5 cannot auto-accept identity")
    require(contract["canonical_write_authorized"] is False, "OA-5 cannot authorize canonical writes")

    evidence = {"source_version_id":"SV-1","page_id":"P-1","evidence_region_id":"ER-1","source_sha256":"a"*64}
    family_decision = {
        "candidate_object_id":"C1",
        "decision":"CONFIRM_AS_FAMILY_CANDIDATE",
        "proposed_family_id":"COLUMN_40X40",
        "family_membership_proposal_created":True,
        "source_evidence":evidence,
    }

    insufficient = resolve_identity_candidate(family_decision, [], "REV-1")
    require(insufficient["candidate_state"] == "INSUFFICIENT_RELATIONSHIP_EVIDENCE", "missing relationship evidence incorrectly accepted")
    require(insufficient["accepted_structural_identity"] is False, "insufficient candidate accepted")

    ready = resolve_identity_candidate(
        family_decision,
        [
            {"relationship_type":"VERTICAL_CONTINUITY","target_id":"G3-P27","evidence_ref":"ER-G3-P27","revision":"REV-1","support":"SUPPORTS"},
            {"relationship_type":"FRAME_MEMBERSHIP","target_id":"FRAME-5","evidence_ref":"FRAME5-NODES","revision":"REV-1","support":"SUPPORTS"},
        ],
        "REV-1",
    )
    require(ready["candidate_state"] == "READY_FOR_EXPLICIT_IDENTITY_REVIEW", "supported candidate not review-ready")
    require(ready["supporting_relationship_count"] == 2, "relationship evidence count wrong")
    require(ready["proximity_used_as_identity_evidence"] is False, "proximity used as identity")
    require(ready["similarity_used_as_identity_authority"] is False, "similarity used as identity authority")
    require(ready["family_membership_used_as_identity_authority"] is False, "family membership used as identity authority")
    require(ready["accepted_structural_identity"] is False, "candidate auto-accepted")
    require(ready["canonical_write_authorized"] is False, "candidate authorized canonical write")
    require(ready["project_material_ready"] is False, "candidate released project material")

    conflict = resolve_identity_candidate(
        family_decision,
        [
            {"relationship_type":"VERTICAL_CONTINUITY","target_id":"G3-P27","evidence_ref":"ER-G3-P27","revision":"REV-1","support":"SUPPORTS"},
            {"relationship_type":"SECTION_CONTINUITY","target_id":"COLUMN_40X50","evidence_ref":"SECTION-CONFLICT","revision":"REV-1","support":"CONFLICTS"},
        ],
        "REV-1",
    )
    require(conflict["candidate_state"] == "IDENTITY_CONFLICT", "relationship conflict not blocking")

    for bad_decision in [
        dict(family_decision, decision="MARK_AMBIGUOUS", family_membership_proposal_created=False),
        dict(family_decision, decision="REJECT", family_membership_proposal_created=False),
    ]:
        try:
            resolve_identity_candidate(bad_decision, [], "REV-1")
        except ValueError:
            pass
        else:
            raise SystemExit("FAIL: non-confirmed family candidate accepted by OA-5")

    try:
        resolve_identity_candidate(
            family_decision,
            [{"relationship_type":"VERTICAL_CONTINUITY","target_id":"G3-P27","evidence_ref":"ER-G3-P27","revision":"OTHER","support":"SUPPORTS"}],
            "REV-1",
        )
    except ValueError as exc:
        require("OA5_RELATIONSHIP_REVISION_MISMATCH" in str(exc), "wrong revision mismatch failure")
    else:
        raise SystemExit("FAIL: stale relationship evidence accepted")

    runtime_html = oa1_runtime.augment(client.build_client("ERW-N12-001"), "ERW-N12-001")
    require(OA5_RUNTIME_MARKER in runtime_html, "OA-5 runtime marker missing")
    require('id="oaStructuralResolver"' in runtime_html, "structural resolver surface missing")
    require('id="oa5Candidate"' in runtime_html, "family candidate selector missing")
    require('id="oa5RelationType"' in runtime_html, "relationship type selector missing")
    require('id="oa5EvidenceRef"' in runtime_html, "relationship evidence reference missing")
    require('id="oa5Resolve"' in runtime_html, "identity candidate construction action missing")
    require("Una famiglia confermata non è ancora identità strutturale" in runtime_html, "family/identity boundary unclear")
    require("proximity_used_as_identity_evidence:false" in runtime_html, "runtime uses proximity as identity")
    require("similarity_used_as_identity_authority:false" in runtime_html, "runtime uses similarity as identity authority")
    require("family_membership_used_as_identity_authority:false" in runtime_html, "runtime uses family membership as identity authority")
    require("accepted_structural_identity:false" in runtime_html, "runtime auto-accepts structural identity")
    require("explicit_identity_review_required:true" in runtime_html, "explicit identity review requirement missing")
    require("canonical_write_authorized:false" in runtime_html, "runtime enabled canonical write")
    require("project_material_ready:false" in runtime_html, "runtime released project material")
    require("OA-G5_EXPLICIT_STRUCTURAL_IDENTITY_REVIEW" in runtime_html, "OA-G5 boundary missing")

    print("OA5_STRUCTURAL_RESOLVER_CORE_PASS")
    print("OA5_WORKBENCH_INTEGRATION_PASS")
    print("OA5_STRUCTURAL_RESOLVER_PASS")


if __name__ == "__main__":
    main()
