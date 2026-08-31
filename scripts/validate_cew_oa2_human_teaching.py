#!/usr/bin/env python3
import json
from pathlib import Path

from cew_oa2_human_teaching import create_teaching_proposal
from cew_oa2_workbench_runtime import OA2_RUNTIME_MARKER
import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_OA2_HUMAN_TEACHING_CONTRACT_v1.json"
QUEUE = ROOT / "automation" / "CEW_OBJECT_ACQUISITION_QUEUE_v1.json"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))

    items = {item["id"]: item for item in queue["items"]}
    require(items["OA-1"]["state"] == "COMPLETE_PASS", "OA-1 must remain complete")
    require(items["OA-2"]["state"] in {"IN_PROGRESS", "COMPLETE_PASS"}, "OA-2 state invalid")
    if queue["current_item"] == "OA-2":
        require(items["OA-3"]["state"] == "BLOCKED_BY_OA2", "OA-3 must remain blocked while OA-2 is current")
    else:
        require(items["OA-2"]["state"] == "COMPLETE_PASS", "OA-2 must be complete before downstream release")
        require(items["OA-2"].get("gate") == "OA2_HUMAN_TEACHING_PASS", "OA-2 completion gate missing")
        require(items["OA-2"].get("runtime_integration") == "WORKBENCH_INTEGRATED_SESSION_STATE", "OA-2 runtime integration record missing")

    require(contract["primary_action"] == "THIS_IS_A", "primary teaching action drift")
    require(contract["canonical_write_authorized"] is False, "OA-2 cannot authorize canonical write")
    require("FIND_SIMILAR" in contract["forbidden_actions"], "Find Similar must remain forbidden in OA-2")
    require(contract["teaching_input"]["geometry_inference_for_type_forbidden"] is True, "geometry inference must remain forbidden")

    scene = {
        "source": {
            "source_version_id": "SV-1",
            "page_id": "PAGE-1",
            "evidence_region_id": "ER-1",
            "source_sha256": "b" * 64,
        },
        "objects": [
            {"object_id": "OBJ-CANDIDATE", "geometry": {"type": "LINE", "a": [0, 0], "b": [1, 1]}}
        ],
    }
    proposal = create_teaching_proposal(
        scene,
        {
            "anchor_object_id": "OBJ-CANDIDATE",
            "object_type": "COLUMN",
            "family_label": "40x40",
            "reviewer": "HUMAN-TEST",
        },
        "REV-TEST",
    )

    require(proposal["state"] == "HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE", "wrong proposal state")
    require(proposal["object_type"] == "COLUMN", "explicit type not preserved")
    require(proposal["family_id"] == "COLUMN_40X40", "family proposal mismatch")
    require(proposal["geometry_used_to_infer_type"] is False, "type inferred from geometry")
    require(proposal["find_similar_authorized"] is False, "Find Similar enabled prematurely")
    require(proposal["structural_identity_created"] is False, "structural identity created prematurely")
    require(proposal["canonical_write_authorized"] is False, "canonical write created")

    for bad in [
        {"anchor_object_id": "OBJ-CANDIDATE", "family_label": "40x40", "reviewer": "H"},
        {"anchor_object_id": "MISSING", "object_type": "COLUMN", "family_label": "40x40", "reviewer": "H"},
        {"anchor_object_id": "OBJ-CANDIDATE", "object_type": "COLUMN", "family_label": "", "reviewer": "H"},
    ]:
        try:
            create_teaching_proposal(scene, bad, "REV-TEST")
        except ValueError:
            pass
        else:
            raise SystemExit("FAIL: invalid teaching input accepted")

    runtime_html = oa1_runtime.augment(client.build_client("ERW-N12-001"), "ERW-N12-001")
    require(OA2_RUNTIME_MARKER in runtime_html, "OA-2 runtime marker missing")
    require('id="oaTeach"' in runtime_html, "human teaching surface missing")
    require('id="oaTeachType"' in runtime_html, "explicit type control missing")
    require('id="oaTeachFamily"' in runtime_html, "project family control missing")
    require('id="oaTeachCreate"' in runtime_html, "This is a action missing")
    require("Questo è un…" in runtime_html, "human teaching wording missing")
    require("geometry_used_to_infer_type:false" in runtime_html, "runtime must record no geometry type inference")
    require("find_similar_authorized:false" in runtime_html, "runtime must keep Find Similar unauthorized")
    require("structural_identity_created:false" in runtime_html, "runtime must keep structural identity false")
    require("canonical_write_authorized:false" in runtime_html, "runtime must keep canonical write false")
    require("source_version_id" in runtime_html and "evidence_region_id" in runtime_html and "source_sha256" in runtime_html, "runtime source provenance incomplete")
    require("sessionStorage.setItem" in runtime_html, "OA-2 proposal must remain work/session state in this tranche")
    require("FIND_SIMILAR" not in runtime_html, "OA-3 action leaked into OA-2 runtime")

    print("OA2_HUMAN_TEACHING_CORE_PASS")
    print("OA2_RUNTIME_INTEGRATION_PASS")
    print("OA2_HUMAN_TEACHING_PASS")


if __name__ == "__main__":
    main()
