#!/usr/bin/env python3
import json
from pathlib import Path

from cew_oa2_human_teaching import create_teaching_proposal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_OA2_HUMAN_TEACHING_CONTRACT_v1.json"
QUEUE = ROOT / "automation" / "CEW_OBJECT_ACQUISITION_QUEUE_v1.json"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))

    require(queue["current_item"] == "OA-2", "OA-2 must be current")
    require(queue["items"][1]["state"] == "COMPLETE_PASS", "OA-1 must remain complete")
    require(queue["items"][2]["state"] == "IN_PROGRESS", "OA-2 must be in progress")
    require(queue["items"][3]["state"] == "BLOCKED_BY_OA2", "OA-3 must remain blocked")

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

    print("OA2_HUMAN_TEACHING_CORE_PASS")
    print("OA2_RUNTIME_INTEGRATION_REQUIRED")


if __name__ == "__main__":
    main()
