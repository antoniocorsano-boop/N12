#!/usr/bin/env python3
import json
from pathlib import Path

from cew_oa4_human_cluster_review import review_candidates
from cew_oa4_workbench_runtime import OA4_RUNTIME_MARKER
import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_OA4_HUMAN_CLUSTER_REVIEW_CONTRACT_v1.json"
QUEUE = ROOT / "automation" / "CEW_OBJECT_ACQUISITION_QUEUE_v1.json"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    items = {item["id"]: item for item in queue["items"]}

    require(items["OA-3"]["state"] == "COMPLETE_PASS", "OA-3 must remain complete")
    require(items["OA-4"]["state"] in {"IN_PROGRESS", "COMPLETE_PASS"}, "OA-4 state invalid")
    if queue["current_item"] == "OA-4":
        require(items["OA-5"]["state"] == "BLOCKED_BY_OA4", "OA-5 must remain blocked while OA-4 is current")
    else:
        require(items["OA-4"]["state"] == "COMPLETE_PASS", "OA-4 must be complete before downstream release")
        require(items["OA-4"].get("gate") == "OA4_HUMAN_CLUSTER_REVIEW_PASS", "OA-4 completion gate missing")
        require(items["OA-4"].get("runtime_integration") == "WORKBENCH_EXPLICIT_CLUSTER_REVIEW_INTEGRATED", "OA-4 runtime integration record missing")

    require(contract["canonical_write_authorized"] is False, "OA-4 cannot authorize canonical write")
    require(contract["batch_review"]["explicit_candidate_selection_required"] is True, "explicit candidate set required")
    require(contract["batch_review"]["implicit_whole_cluster_confirmation_forbidden"] is True, "implicit cluster acceptance must be forbidden")
    require(contract["output"]["creates_structural_identity"] is False, "OA-4 cannot create structural identity")

    evidence = {"source_version_id":"SV-1","page_id":"P-1","evidence_region_id":"ER-1","source_sha256":"a"*64}
    similarity = {
        "state":"DETERMINISTIC_SIMILARITY_CANDIDATES",
        "prototype_id":"OAP-1",
        "family_id":"COLUMN_40X40",
        "weights":{"GEOMETRY_KIND":.3,"DIMENSION_RATIO":.2,"ORIENTATION":.15,"TOPOLOGY_HINT":.15,"SPATIAL_CONTEXT":.1,"ASSOCIATED_TEXT":.1},
        "candidates":[
            {"candidate_object_id":"C1","score":.91,"state":"STRONG_SIMILAR","reason_codes":["GEOMETRY_KIND_MATCH"]},
            {"candidate_object_id":"C2","score":.78,"state":"STRONG_SIMILAR","reason_codes":["ORIENTATION_DELTA_0.0"]},
            {"candidate_object_id":"C3","score":.55,"state":"POSSIBLE_SIMILAR","reason_codes":["TOPOLOGY_DIFFERENT"]}
        ]
    }

    partial = review_candidates(similarity,[{"candidate_object_id":"C1","decision":"CONFIRM_AS_FAMILY_CANDIDATE"}],"HUMAN-TEST","REV-1",evidence)
    require(partial["state"] == "REVIEW_PARTIAL", "partial review state wrong")
    require(partial["family_membership_proposals_created"] == 1, "family proposal missing")
    require(partial["structural_identity_created"] is False, "partial review created structural identity")

    complete = review_candidates(similarity,[
        {"candidate_object_id":"C1","decision":"CONFIRM_AS_FAMILY_CANDIDATE"},
        {"candidate_object_id":"C2","decision":"REJECT"},
        {"candidate_object_id":"C3","decision":"MARK_AMBIGUOUS"},
    ],"HUMAN-TEST","REV-1",evidence)
    require(complete["state"] == "REVIEW_COMPLETE_WITH_AMBIGUITIES", "ambiguity state wrong")
    require(complete["clean_completion"] is False, "ambiguity incorrectly clean")
    require(complete["ambiguous_count"] == 1, "ambiguity not counted")
    require(all(row["canonical_write_authorized"] is False for row in complete["candidate_decisions"]), "candidate decision authorized canonical write")
    require(all(row["structural_identity_created"] is False for row in complete["candidate_decisions"]), "candidate decision created structural identity")

    clean = review_candidates(similarity,[
        {"candidate_object_id":"C1","decision":"CONFIRM_AS_FAMILY_CANDIDATE"},
        {"candidate_object_id":"C2","decision":"MOVE_TO_OTHER_FAMILY","target_family_id":"COLUMN_40X50"},
        {"candidate_object_id":"C3","decision":"REJECT"},
    ],"HUMAN-TEST","REV-1",evidence)
    require(clean["state"] == "REVIEW_COMPLETE", "clean review state wrong")
    require(clean["clean_completion"] is True, "clean completion not recognized")
    require(clean["project_material_promotion_authorized"] is False, "OA-4 promoted project material")

    for bad in [
        [{"candidate_object_id":"UNKNOWN","decision":"REJECT"}],
        [{"candidate_object_id":"C1","decision":"MOVE_TO_OTHER_FAMILY"}],
        [{"candidate_object_id":"C1","decision":"CONFIRM_AS_FAMILY_CANDIDATE"},{"candidate_object_id":"C1","decision":"REJECT"}],
    ]:
        try:
            review_candidates(similarity, bad, "H", "REV", evidence)
        except ValueError:
            pass
        else:
            raise SystemExit("FAIL: invalid OA-4 review accepted")

    runtime_html = oa1_runtime.augment(client.build_client("ERW-N12-001"), "ERW-N12-001")
    require(OA4_RUNTIME_MARKER in runtime_html, "OA-4 runtime marker missing")
    require('id="oaClusterReview"' in runtime_html, "cluster review surface missing")
    require('id="oaLoadReview"' in runtime_html, "load similarity run action missing")
    require('id="oaSaveReview"' in runtime_html, "save selected decisions action missing")
    require("Seleziona esplicitamente i candidati" in runtime_html, "explicit selection wording missing")
    require("Nessun candidato viene incluso automaticamente" in runtime_html, "implicit cluster acceptance prohibition missing")
    require("explicit_candidate_selection:true" in runtime_html, "runtime explicit selection receipt missing")
    require("implicit_cluster_acceptance:false" in runtime_html, "runtime implicit acceptance flag missing")
    require("structural_identity_created:false" in runtime_html, "runtime created structural identity")
    require("project_material_promotion_authorized:false" in runtime_html, "runtime promoted project material")
    require("canonical_write_authorized:false" in runtime_html, "runtime enabled canonical write")
    require("OA-5_STRUCTURAL_RESOLVER" in runtime_html, "next structural resolver boundary missing")
    if queue["current_item"] == "OA-4":
        require("CEW_OA5_RUNTIME" not in runtime_html, "OA-5 runtime leaked before release")

    print("OA4_HUMAN_CLUSTER_REVIEW_CORE_PASS")
    print("OA4_RUNTIME_INTEGRATION_PASS")
    print("OA4_HUMAN_CLUSTER_REVIEW_PASS")


if __name__ == "__main__":
    main()
