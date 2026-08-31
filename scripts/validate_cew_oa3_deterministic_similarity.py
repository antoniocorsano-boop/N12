#!/usr/bin/env python3
import json
from pathlib import Path

from cew_oa3_deterministic_similarity import WEIGHTS, STRONG_SIMILAR_MIN, POSSIBLE_SIMILAR_MIN, find_similar
from cew_oa3_workbench_runtime import OA3_RUNTIME_MARKER
import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_OA3_DETERMINISTIC_SIMILARITY_CONTRACT_v1.json"
QUEUE = ROOT / "automation" / "CEW_OBJECT_ACQUISITION_QUEUE_v1.json"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    items = {item["id"]: item for item in queue["items"]}

    require(items["OA-2"]["state"] == "COMPLETE_PASS", "OA-2 must remain complete")
    require(items["OA-3"]["state"] in {"IN_PROGRESS", "COMPLETE_PASS"}, "OA-3 state invalid")
    if queue["current_item"] == "OA-3":
        require(items["OA-4"]["state"] == "BLOCKED_BY_OA3", "OA-4 must remain blocked while OA-3 is current")
    else:
        require(items["OA-3"]["state"] == "COMPLETE_PASS", "OA-3 must be complete before downstream release")
        require(items["OA-3"].get("gate") == "OA3_DETERMINISTIC_SIMILARITY_PASS", "OA-3 completion gate missing")
        require(items["OA-3"].get("runtime_integration") == "WORKBENCH_FIND_SIMILAR_INTEGRATED", "OA-3 runtime integration record missing")

    require(contract["primary_action"] == "FIND_SIMILAR", "Find Similar action drift")
    require(contract["scoring"]["deterministic"] is True, "similarity must be deterministic")
    require(contract["input_contract"]["governed_prototype_receipt_required_in_runtime"] is True, "runtime governed prototype requirement missing")
    require(contract["governance"]["human_cluster_review_required_next"] is True, "human cluster review must remain required")
    require(contract["governance"]["similarity_creates_structural_identity"] is False, "similarity cannot create structural identity")
    require(contract["governance"]["source_position_may_be_inferred_from_similarity"] is False, "similarity cannot infer source position")
    require(contract["canonical_write_authorized"] is False, "OA-3 cannot authorize canonical writes")
    require(contract["scoring"]["default_weights"] == WEIGHTS, "core/contract weight drift")
    require(contract["scoring"]["thresholds"] == {"STRONG_SIMILAR_MIN": STRONG_SIMILAR_MIN, "POSSIBLE_SIMILAR_MIN": POSSIBLE_SIMILAR_MIN}, "core/contract threshold drift")

    source = {"source_version_id":"SV-1","page_id":"P-1","evidence_region_id":"ER-1","source_sha256":"a"*64}
    scene = {
        "source": source,
        "objects": [
            {"object_id":"ANCHOR","geometry":{"type":"LINE","a":[0,0],"b":[40,40]},"properties":{"section_x_cm":40,"section_y_cm":40,"orientation_class":"X40_Y40","topology_hint":"NODE_INTERSECTION","spatial_context":"FRAME_GRID","associated_text":"40x40 P"}},
            {"object_id":"SIM-1","geometry":{"type":"LINE","a":[100,5],"b":[140,45]},"properties":{"section_x_cm":40,"section_y_cm":40,"orientation_class":"X40_Y40","topology_hint":"NODE_INTERSECTION","spatial_context":"FRAME_GRID","associated_text":"40x40 P"}},
            {"object_id":"ROTATED-DIFF","geometry":{"type":"LINE","a":[200,5],"b":[230,50]},"properties":{"section_x_cm":30,"section_y_cm":45,"orientation_class":"X30_Y45","topology_hint":"NODE_INTERSECTION","spatial_context":"FRAME_GRID","associated_text":"30x45 P"}},
            {"object_id":"DIFF-1","geometry":{"type":"LINE","a":[0,0],"b":[25,70]},"properties":{"section_x_cm":25,"section_y_cm":70,"orientation_class":"X25_Y70","topology_hint":"SPAN","spatial_context":"BEAM_MIDSPAN","associated_text":"25x70 T"}},
        ],
    }
    prototype = {
        "state":"HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE",
        "prototype_id":"OAP-TEST",
        "object_type":"COLUMN",
        "family_id":"COLUMN_40X40",
        "anchor_object_id":"ANCHOR",
        "source_evidence":source,
    }
    result = find_similar(scene, prototype)
    require(result["state"] == "DETERMINISTIC_SIMILARITY_CANDIDATES", "wrong result state")
    require(result["candidates"][0]["candidate_object_id"] == "SIM-1", "expected identical section not ranked first")
    require(result["candidates"][0]["score"] > next(r["score"] for r in result["candidates"] if r["candidate_object_id"] == "ROTATED-DIFF"), "dimension/orientation signals do not discriminate")
    require("SECTION_X_RATIO_1.000" in result["candidates"][0]["reason_codes"], "section-x reason code missing")
    require("SECTION_Y_RATIO_1.000" in result["candidates"][0]["reason_codes"], "section-y reason code missing")
    require("ORIENTATION_CLASS_MATCH" in result["candidates"][0]["reason_codes"], "orientation-class reason code missing")
    require(result["candidates"][0]["human_confirmation_required"] is True, "human review bypassed")
    require(result["candidates"][0]["object_type_created"] is False, "similarity created object type")
    require(result["candidates"][0]["family_membership_created"] is False, "similarity created family membership")
    require(result["auto_confirm_cluster_authorized"] is False, "cluster auto-confirm enabled")
    require(result["structural_identity_created"] is False, "structural identity created")
    require(result["canonical_write_authorized"] is False, "canonical write enabled")
    require(all(row["reason_codes"] for row in result["candidates"]), "explainable reason codes missing")

    bad = dict(prototype)
    bad["source_evidence"] = dict(source, source_sha256="b"*64)
    try:
        find_similar(scene, bad)
    except ValueError as exc:
        require("OA3_SOURCE_REVISION_MISMATCH" in str(exc), "wrong mismatch failure")
    else:
        raise SystemExit("FAIL: source revision mismatch accepted")

    runtime_html = oa1_runtime.augment(client.build_client("ERW-N12-001"), "ERW-N12-001")
    require(OA3_RUNTIME_MARKER in runtime_html, "OA-3 runtime marker missing")
    require('id="oaSimilar"' in runtime_html, "Find Similar runtime surface missing")
    require('id="oaFindSimilar"' in runtime_html, "Find Similar action missing")
    require("Trova simili" in runtime_html, "Find Similar wording missing")
    require("WEIGHTS={GEOMETRY_KIND:.20,DIMENSION_RATIO:.30,ORIENTATION:.15,TOPOLOGY_HINT:.10,SPATIAL_CONTEXT:.10,ASSOCIATED_TEXT:.15}" in runtime_html, "runtime weight contract drift")
    require("section_x_cm" in runtime_html and "section_y_cm" in runtime_html, "runtime dimension-aware scoring missing")
    require("orientation_class" in runtime_html, "runtime orientation-class scoring missing")
    require("governed_receipt_id" in runtime_html, "runtime governed prototype requirement missing")
    require("Nessun candidato viene confermato automaticamente" in runtime_html, "auto-confirm prohibition missing")
    require("OA-4" in runtime_html, "next human cluster review boundary missing")
    require("AUTO_CONFIRM_CLUSTER" not in runtime_html, "automatic cluster confirmation leaked into runtime")
    require("CREATE_STRUCTURAL_IDENTITY" not in runtime_html, "structural identity action leaked into runtime")
    require("canonical_write_authorized:true" not in runtime_html, "canonical write leaked into runtime")

    print("OA3_DETERMINISTIC_SIMILARITY_CORE_PASS")
    print("OA3_DIMENSION_AWARE_SIGNATURE_PASS")
    print("OA3_RUNTIME_INTEGRATION_PASS")
    print("OA3_DETERMINISTIC_SIMILARITY_PASS")


if __name__ == "__main__":
    main()
