#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation/CEW_OA_HUMAN_FIRST_UX_CONTRACT_v1.json"
OA2 = ROOT / "scripts/cew_oa2_workbench_runtime.py"
OA3 = ROOT / "scripts/cew_oa3_workbench_runtime.py"
QUEUE = ROOT / "automation/CEW_OBJECT_ACQUISITION_QUEUE_v1.json"
PILOT = "OA-N12-G4-COLUMN-PILOT"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    oa2 = OA2.read_text(encoding="utf-8")
    oa3 = OA3.read_text(encoding="utf-8")
    rendered = client.build_client(PILOT)
    runtime = oa1_runtime.augment(rendered, PILOT)

    require(contract["scope"] == PILOT, "human-first scope drift")
    require(contract["interaction_principle"] == "HUMAN_FIRST_STATE_DEPENDENT_VIEW", "interaction principle drift")
    require(contract["source_content_obstruction_forbidden"] is True, "source obstruction must be forbidden")
    policy = contract["unregistered_source_position_policy"]
    require(policy["layout"] == "SOURCE_PRIMARY_WITH_OPERATIONAL_SIDEBAR", "source-primary layout required")
    require(policy["default_mode"] == "SOURCE", "SOURCE must be default for unregistered pilot")
    require(policy["split_mode_default_forbidden"] is True, "split default must be forbidden")
    require(policy["source_status_badges"] == "OUTSIDE_SOURCE_VIEWPORT", "badges must be outside source")
    require(policy["object_catalog"] == "PRIMARY_OPERATIONAL_ENTRY", "catalog must be primary operational entry")

    require('body.oa-human-first .source-pane .pane-head' in runtime, "source badge suppression missing")
    require('display:none!important' in runtime[runtime.index('body.oa-human-first .source-pane .pane-head'):], "source badge must be suppressed")
    require('grid-template-columns:minmax(0,1fr) minmax(340px,400px)!important' in runtime, "source/sidebar layout missing")
    require("workspace.appendChild(panel)" in runtime, "OA panel is not moved into persistent workspace sidebar")
    require("requestMode('SOURCE')" in runtime, "human-first pilot does not request SOURCE default")
    require("OA_HUMAN_FIRST_MARKER='CEW_OA_HUMAN_FIRST_SOURCE_PRIMARY'" in runtime, "human-first runtime marker missing")

    for label in [
        "Leggi la fonte",
        "Scegli un oggetto",
        "Questo è un…",
        "Famiglia",
        "Trova simili",
        "Rivedi candidati",
    ]:
        require(label in runtime, f"human sequence label missing: {label}")
    require('id="oaHumanSelected"' in runtime, "selected-object card missing")
    require("Catalogo supporti G4" in runtime, "catalog-first pilot copy missing")
    require("Posizione dei supporti sulla tavola non ancora registrata" in runtime, "human-readable position blocker missing")
    require("Puoi insegnare tipo e famiglia e cercare simili" in runtime, "blocker does not explain allowed work")
    require("Non puoi sincronizzare spazialmente né accettare identità strutturali" in runtime, "blocker does not explain forbidden work")
    require("Sincronizzazione spaziale non disponibile" in runtime, "human-readable spatial sync state missing")
    require("posizione sulla tavola non registrata" in runtime.lower(), "human-readable registration state missing")

    # Human-first must survive the first real interaction, not only initial boot.
    selection_marker = "if(typeof selectObject==='function')selectObject(obj);else selected=obj;if(typeof requestMode==='function')requestMode('SOURCE')"
    require(selection_marker in oa2, "pilot object selection can leave SOURCE-primary mode")
    require(oa2.count("requestMode('SOURCE')") >= 2, "SOURCE must be asserted at boot and after pilot selection")

    require('id="oaTeachCreate" class="primary oa-primary-action"' in runtime, "THIS_IS_A is not visually primary")
    require('id="oaFindSimilar" class="primary" type="button" disabled' in runtime, "Find Similar must start disabled")
    require("governed_receipt_id" in oa3 and "prototypeReadiness" in oa3, "Find Similar governance readiness missing")
    require("source_version_id','page_id','evidence_region_id','source_sha256" in oa3, "same-source gate missing")
    require("window.addEventListener('cew:oa2-prototype-persisted',refreshOA3Availability)" in oa3, "Find Similar does not react to persisted prototype")
    require("window.dispatchEvent(new CustomEvent('cew:oa2-prototype-persisted'" in oa2, "OA2 does not announce governed persistence")
    require("auto_confirm_cluster_authorized:false" in oa3, "auto cluster confirmation must remain forbidden")
    require("body.oa-human-first #oaClusterReview{display:none}" in runtime, "OA4 must be progressively hidden before similarity run")
    require("review.classList.add('oa4-ready')" in oa3, "OA4 is not revealed after similarity run")

    require(contract["canonical_write_authorized"] is False, "canonical write authority drift")
    require(contract["structural_identity_acceptance_authorized"] is False, "structural identity acceptance drift")
    require(contract["project_material_ready"] is False, "project material must remain blocked")
    require("canonical_write_authorized:false" in runtime, "runtime authority guard missing")
    require(queue.get("project_material_ready") is not True, "queue cannot assert project material ready")

    print("CEW_OA_HUMAN_FIRST_UX = PASS")
    print("SOURCE_VIEWPORT_UNOBSTRUCTED = true")
    print("SOURCE_PRIMARY_WITH_OPERATIONAL_SIDEBAR = true")
    print("SOURCE_PRIMARY_AFTER_OBJECT_SELECTION = true")
    print("FIND_SIMILAR_GOVERNED_PROTOTYPE_GATE = PASS")
    print("AUTO_CLUSTER_CONFIRMATION = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("PROJECT_MATERIAL_READY = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
