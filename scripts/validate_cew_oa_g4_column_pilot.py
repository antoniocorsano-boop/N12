#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

import build_cew_source_viewer as source_viewer
import cew_oa1_workbench_runtime as oa1_runtime
import cew_oa_source_workspace_adapter as oa_source_workspace_adapter
import cew_professional_workbench_client as workbench_client
import cew_professional_workbench_projection as projection

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/canonical"
TASK_ID = "OA-N12-G4-COLUMN-PILOT"
SOURCE_VERSION_ID = "CEW-N12-SRC-TAV05S-V2143DBCF"
PAGE_ID = "CEW-N12-PAGE-TAV05S-P001"
TRANSFORM_ID = "CEW-N12-XFORM-TAV05S-P001"
REGION_ID = "CEW-N12-REG-TAV05S-G4-COLUMN-PILOT"
SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def one(name: str, field: str, value: str) -> dict[str, str]:
    matches = [row for row in rows(name) if row.get(field, "").strip() == value]
    if len(matches) != 1:
        raise SystemExit(f"FAIL: {name} expected one {field}={value}, got {len(matches)}")
    return matches[0]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    source = one("CEW_SOURCE_IDENTITY_REGISTRY_v1.csv", "source_version_id", SOURCE_VERSION_ID)
    page = one("CEW_PAGE_REGISTRY_v1.csv", "page_id", PAGE_ID)
    transform = one("CEW_PAGE_TRANSFORM_REGISTRY_v1.csv", "transform_id", TRANSFORM_ID)
    region = one("CEW_EVIDENCE_REGION_REGISTRY_v1.csv", "evidence_region_id", REGION_ID)
    task = one("CEW_OA_TASK_REGISTRY_v1.csv", "task_id", TASK_ID)
    binding = one("CEW_OA_SOURCE_VIEWER_BINDINGS_v1.csv", "task_id", TASK_ID)
    observation = one("CEW_OBSERVATION_REGISTRY_v1.csv", "reference_item", "TAV05S-G4-COLUMN-PILOT")

    require(not any(r["task_id"] == TASK_ID for r in rows("CEW_ERW_RESOLUTION_TASKS_v1.csv")), "OA pilot leaked into ERW task registry")
    require(not any(r["task_id"] == TASK_ID for r in rows("CEW_SOURCE_VIEWER_BINDINGS_v1.csv")), "OA pilot leaked into ERW viewer binding registry")
    require(source["sha256"].lower() == SHA256, "TAV-05S source hash drift")
    require(source["authority"] == "PRIMARY" and source["readiness_state"] == "READY", "TAV-05S source authority/readiness drift")
    require(page["source_version_id"] == SOURCE_VERSION_ID and page["readiness_state"] == "READY", "TAV-05S Page parent/readiness drift")
    require(abs(float(page["source_width"]) - 1683.719971) < 1e-6, "TAV-05S page width drift")
    require(abs(float(page["source_height"]) - 3007.080078) < 1e-6, "TAV-05S page height drift")
    require(transform["page_id"] == PAGE_ID and transform["readiness_state"] == "READY", "TAV-05S transform drift")
    require("7016" in transform["normalized_to_derived_formula"] and "12530" in transform["normalized_to_derived_formula"], "TAV-05S derived dimensions drift")
    require(region["source_version_id"] == SOURCE_VERSION_ID and region["page_id"] == PAGE_ID and region["transform_id"] == TRANSFORM_ID, "pilot EvidenceRegion provenance chain drift")
    require(region["coordinate_space"] == "NORMALIZED_0_1", "pilot EvidenceRegion coordinate space drift")
    require([float(region[k]) for k in ("x", "y", "width", "height")] == [0.0, 0.0, 1.0, 1.0], "pilot must remain deterministic full-page evidence envelope")
    require(task["domain"] == "OBJECT_ACQUISITION", "pilot task domain drift")
    require(not task["model_entities"].strip(), "pilot task must not start from a model entity")
    require(binding["binding_state"] == "READY" and binding["evidence_region_id"] == REGION_ID, "pilot viewer binding drift")
    require(not observation["structural_binding"].strip(), "pilot observation must not assert structural binding")

    supports = [r for r in rows("STOREY_SUPPORT_SECTIONS_G4_v1.csv") if r["storey_id"] == "G4" and r["source_sheet"] == "TAV-05S"]
    require(len(supports) == 34, f"expected 34 G4 support identities, got {len(supports)}")
    require(all(r["primary_source_sha256"].lower() == SHA256 for r in supports), "support register source hash drift")
    require(all(r["validation_state"] == "DIRECT_REGISTERED" for r in supports), "support register validation drift")

    manifest = source_viewer.build_manifest()
    entries = [entry for entry in manifest["entries"] if entry["task_id"] == TASK_ID]
    require(len(entries) == 1, "pilot Source Viewer entry missing/non-unique")
    require(entries[0]["source_code"] == "TAV-05S" and entries[0]["region_id"] == REGION_ID, "pilot Source Viewer entry provenance drift")

    oa_workspace = oa_source_workspace_adapter.workspace
    ctx = oa_workspace.task_context(TASK_ID)
    require(ctx["task"]["domain"] == "OBJECT_ACQUISITION", "OA source workspace did not resolve dedicated task")
    require(ctx["binding"]["evidence_region_id"] == REGION_ID, "OA source workspace binding drift")
    scene = projection.build_scene(TASK_ID, oa_workspace)
    candidates = [o for o in scene["objects"] if o.get("object_family") == "TechnicalObjectCandidate"]
    require(len(candidates) == 34, f"pilot Workbench candidate count drift: {len(candidates)}")
    require(scene["capabilities"]["object_acquisition_candidate_count"] == 34, "pilot capability candidate count drift")
    require(scene["capabilities"]["object_acquisition_source_position_state"] == "UNREGISTERED", "pilot source-position authority drift")
    require(scene["capabilities"]["spatial_sync_available"] is False and scene["capabilities"]["overlay_available"] is False, "pilot accidentally enabled spatial authority")
    require(scene["authority"]["canonical_write_authorized"] is False and scene["authority"]["promotion_authorized"] is False, "pilot scene authority drift")
    for candidate in candidates:
        p = candidate["properties"]
        require(candidate["coordinate_space"] == "TECHNICAL_2D", "candidate coordinate space drift")
        require(candidate["geometry"]["semantic"] == "SECTION_SIGNATURE_VECTOR_NOT_SOURCE_POSITION", "candidate signature geometry drift")
        require(p["source_position_state"] == "UNREGISTERED", "candidate acquired fake source position")
        require(p["object_type"] is None and p["family_membership"] is None and p["structural_identity"] is None, "candidate was auto-classified/promoted")
        require(candidate["canonical_write_authorized"] is False, "candidate canonical write drift")

    html = oa1_runtime.augment(workbench_client.build_client(TASK_ID), TASK_ID)
    require('id="oaPilotTray"' in html, "human CAD object tray missing")
    require("Posizione sulla tavola" in html and "non registrata" in html.lower(), "human-readable source-position warning missing from pilot")
    require("Sincronizzazione spaziale non disponibile" in html, "human-readable spatial-sync warning missing from pilot")
    require("governed_receipt_id" in html, "governed OA-2/OA-3 chain marker missing")
    require("section_x_cm" in html and "section_y_cm" in html, "dimension-aware deterministic similarity missing")
    require("o.object_family==='TechnicalObjectCandidate'" in html, "pilot similarity universe is not restricted to object candidates")
    require("ACCEPT_STRUCTURAL_IDENTITY" in html, "OA-G5 explicit human review surface missing")

    app = (ROOT / "app.py").read_text(encoding="utf-8")
    require("professional_workbench_api.build_router(oa_workspace)" in app, "Workbench not mounted on OA read-only adapter")
    require("oa_governed_api.build_router(oa_workspace)" in app, "OA governed API not mounted on OA read-only adapter")

    queue = json.loads((ROOT / "automation/CEW_OBJECT_ACQUISITION_QUEUE_v1.json").read_text(encoding="utf-8"))
    items = {item["id"]: item for item in queue["items"]}
    require(items["OA-6"]["state"] == "BLOCKED_BY_OA5", "OA-6 released by pilot")
    require(queue["global_blocks"]["canonical_write_authorized"] is False, "pilot enabled canonical write")
    require(queue["global_blocks"]["project_material_ready"] is False, "pilot released project material")

    print("TAV05S_G4_F2_PROVENANCE_PASS")
    print("OA_G4_DOMAIN_ISOLATION_PASS")
    print("OA_G4_SUPPORT_REGISTER_34_PASS")
    print("OA_G4_OBJECT_TRAY_PASS")
    print("OA_G4_HUMAN_READABLE_SOURCE_STATE_PASS")
    print("OA_G4_DIMENSION_AWARE_SIMILARITY_PASS")
    print("OA_G4_NO_FAKE_SOURCE_POSITION_PASS")
    print("OA_G4_NO_AUTO_CLASSIFICATION_PASS")
    print("OA6_REMAINS_BLOCKED_PASS")


if __name__ == "__main__":
    main()
