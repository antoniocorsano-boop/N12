#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_professional_workbench_document_geometry as geometry
import cew_professional_workbench_projection as projection

FROZEN_TASKS = ("ERW-N12-001", "ERW-N12-002", "ERW-N12-003", "ERW-N12-004")
FROZEN_REGION_IDS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-T6A-G03",
}


def main() -> int:
    github_sha = os.getenv("GITHUB_SHA")
    if github_sha:
        os.environ["RENDER_GIT_COMMIT"] = github_sha

    manifest = geometry.validate_manifest()
    state = geometry.status()
    assert state["state"] == "READY", state
    assert state["source_coverage"] == "4/4", state
    assert state["governed_region_count"] >= 4, state
    assert state["comparison_scope"] == "GOVERNED_EVIDENCE_REGION_WHERE_AVAILABLE", state
    assert state["page_level_role"] == "DIAGNOSTIC_ONLY", state
    assert state["runtime_docling_required"] is False, state

    governed_region_ids: set[str] = set()
    comparable_regions = 0
    zero_vector_regions = 0
    for entry in manifest["entries"]:
        artifact = json.loads((geometry.ASSET_ROOT / entry["filename"]).read_text(encoding="utf-8"))
        for region in artifact["regions"]:
            governed_region_ids.add(region["evidence_region_id"])
            seg = region["segment_metrics"]
            ints = region["intersection_metrics"]
            reference_count = int(seg.get("reference_count") or 0)
            candidate_count = int(seg.get("candidate_count") or 0)
            if reference_count or candidate_count:
                comparable_regions += 1
            else:
                zero_vector_regions += 1
            print(
                "DOCUMENT_GEOMETRY_REGION_DIAGNOSTIC",
                region["evidence_region_id"],
                "outcome=" + region["agreement_outcome"],
                "mapping=" + str(region["coordinate_mapping"]),
                "reference=" + str(reference_count),
                "candidate=" + str(candidate_count),
                "matches=" + str(len(seg.get("matches") or [])),
                "segment_ratio=" + str(seg.get("match_ratio")),
                "intersection_reference=" + str(ints.get("reference_count")),
                "intersection_candidate=" + str(ints.get("candidate_count")),
                "intersection_matches=" + str(ints.get("matches")),
                "intersection_ratio=" + str(ints.get("match_ratio")),
            )

    assert FROZEN_REGION_IDS <= governed_region_ids, {
        "missing_frozen_regions": sorted(FROZEN_REGION_IDS - governed_region_ids),
        "governed_region_ids": sorted(governed_region_ids),
    }

    for task in FROZEN_TASKS:
        scene = projection.build_scene(task)
        assert scene["authority"]["canonical_write_authorized"] is False
        assert scene["source"]["pdf_page_no"] == scene["source"]["page_index"] + 1
        document_objects = [obj for obj in scene["objects"] if obj["object_family"] == "DocumentGraphicPrimitive"]
        for obj in document_objects:
            assert obj["coordinate_space"] == "SOURCE_PAGE_PT"
            assert obj["technical_identity_authorized"] is False
            assert obj["canonical_write_authorized"] is False
            assert obj["provenance"]["evidence_region_id"] == scene["source"]["evidence_region_id"]
        document_state = scene["capabilities"]["document_geometry"]["state"]
        assert document_state in {"READY_AGREED_DOCUMENT_GEOMETRY", "NOT_MATERIALIZED_FAIL_CLOSED"}, document_state

    print("CEW_DOCUMENT_GEOMETRY_SCENE_ADAPTER = PASS")
    print("FROZEN_GOVERNED_REGION_SUBSET = 4/4")
    print(f"GOVERNED_REGION_COUNT = {state['governed_region_count']}")
    print(f"AGREED_REGION_COUNT = {state['agreed_region_count']}")
    print(f"REGION_OBJECT_COUNT = {state['region_object_count']}")
    print(f"COMPARABLE_VECTOR_REGION_COUNT = {comparable_regions}")
    print(f"ZERO_VECTOR_REGION_COUNT = {zero_vector_regions}")
    print("PAGE_LEVEL_ROLE = DIAGNOSTIC_ONLY")
    print("RUNTIME_DOCLING_REQUIRED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
