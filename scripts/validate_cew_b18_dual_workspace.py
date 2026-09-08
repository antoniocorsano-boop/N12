#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_b1_dual_workspace as dual
import cew_source_evidence_workspace as source_workspace

CONTRACT = ROOT / "automation/CEW_B18_DUAL_WORKSPACE_HVA_CONTRACT_v1.json"
REGIONS = ROOT / "data/canonical/CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
OBSERVATIONS = ROOT / "data/canonical/CEW_OBSERVATION_REGISTRY_v1.csv"
BINDINGS = ROOT / "data/canonical/CEW_SOURCE_VIEWER_BINDINGS_v1.csv"
DOCUMENT_MAPS = ROOT / "data/canonical/CEW_DOCUMENT_MAP_REGISTRY_v1.json"
APP = ROOT / "app.py"
DOC = ROOT / "docs/ACCEPTANCE/CEW_B18_DUAL_WORKSPACE_CONTRACT_v1.md"


def rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    required = [CONTRACT, REGIONS, OBSERVATIONS, BINDINGS, DOCUMENT_MAPS, APP, DOC, ROOT / "scripts/cew_b1_dual_workspace.py"]
    for path in required:
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print("ERROR:", error)
        return 1

    contract = load(CONTRACT)
    chain = contract["required_real_data_chain"]
    if contract.get("status") != "IMPLEMENTED_CANDIDATE_HVA_PENDING":
        errors.append("dual workspace must remain HVA pending")
    if contract.get("human_hva_state") != "REQUIRED_NOT_SATISFIED":
        errors.append("human HVA cannot be auto-satisfied")
    if contract.get("canonical_write_authorized") is not False:
        errors.append("canonical write must remain false")
    if contract.get("engineering_authority_effect") != "NONE":
        errors.append("engineering authority effect must remain NONE")
    if chain.get("structural_geometry_state") != "OPEN/ND":
        errors.append("structural geometry must remain OPEN/ND until a traceable geometry binding exists")

    bindings = {r["task_id"]: r for r in rows(BINDINGS)}
    regions = {r["evidence_region_id"]: r for r in rows(REGIONS)}
    observations = {r["observation_id"]: r for r in rows(OBSERVATIONS)}
    binding = bindings.get(chain["task_id"])
    region = regions.get(chain["evidence_region_id"])
    observation = observations.get(chain["observation_id"])
    if not binding:
        errors.append("required task binding missing")
    else:
        for key in ["source_version_id", "page_id", "transform_id", "evidence_region_id"]:
            if binding.get(key) != chain.get(key):
                errors.append(f"required chain mismatch: {key}")
        if binding.get("binding_state") != "READY":
            errors.append("viewer binding must be READY")
    if not region:
        errors.append("required EvidenceRegion missing")
    else:
        if region.get("readiness_state") != "READY":
            errors.append("required EvidenceRegion must be READY")
        if region.get("coordinate_space") != "NORMALIZED_0_1":
            errors.append("dual page projection expects canonical NORMALIZED_0_1 geometry")
    if not observation:
        errors.append("required Observation missing")
    else:
        if observation.get("evidence_region_id") != chain["evidence_region_id"]:
            errors.append("Observation/EvidenceRegion mismatch")
        if observation.get("literal_or_value") != chain["documented_literal"]:
            errors.append("documented literal drift")
        if observation.get("epistemic_ceiling") != "DOC":
            errors.append("first dual-workspace Observation must preserve DOC ceiling")
        if observation.get("structural_binding"):
            errors.append("first dual-workspace Observation must not invent a structural binding")

    maps = load(DOCUMENT_MAPS).get("maps", [])
    docmap = next((m for m in maps if m.get("source_id") == chain["source_id"] and m.get("page_id") == chain["page_id"]), None)
    if not docmap:
        errors.append("document map for first dual-workspace source missing")
    else:
        if chain["evidence_region_id"] not in docmap.get("evidence_region_ids", []):
            errors.append("EvidenceRegion not declared by DocumentMap")
        if docmap.get("canonical_engineering_promotion") is not False:
            errors.append("DocumentMap must not authorize engineering promotion")

    p = dual.projection(chain["task_id"], source_workspace)
    if p["canonical_write_authorized"] is not False:
        errors.append("projection authorized canonical write")
    if p["engineering_authority_effect"] != "NONE":
        errors.append("projection changed engineering authority")
    if p["structural_geometry_state"] != "OPEN/ND":
        errors.append("projection invented structural geometry")

    rendered = dual.build_workspace(chain["task_id"], source_workspace)
    for marker in [
        "SOURCE PANEL",
        "TECHNICAL REPRESENTATION PANEL",
        "OPEN/ND",
        "geometry != identity",
        chain["source_version_id"],
        chain["page_id"],
        chain["transform_id"],
        chain["evidence_region_id"],
        chain["observation_id"],
        chain["documented_literal"],
        "Nessuna scrittura canonica eseguita",
        "proposal_only:true",
        "canonical_write:false",
        "sessionStorage",
        "non geometria del modello",
    ]:
        if marker not in rendered:
            errors.append(f"dual workspace missing marker: {marker}")

    forbidden = [
        "canonical_write:true",
        "engineering_authority_effect:'LEVEL_C'",
        "AUTO_BIND_NEAREST_MEMBER",
        "INFER_MISSING_REINFORCEMENT",
    ]
    for marker in forbidden:
        if marker in rendered:
            errors.append(f"forbidden dual-workspace behavior present: {marker}")

    app_text = APP.read_text(encoding="utf-8")
    for marker in [
        "import cew_b1_dual_workspace as dual_workspace",
        '@app.get("/evidence/dual-workspace"',
        '"b18_dual_workspace": "IMPLEMENTED_CANDIDATE_HVA_PENDING"',
    ]:
        if marker not in app_text:
            errors.append(f"runtime wiring missing: {marker}")

    if errors:
        print("CEW_B18_DUAL_WORKSPACE = FAIL")
        for error in errors:
            print("ERROR:", error)
        return 1

    print("CEW_B18_DUAL_WORKSPACE = PASS")
    print("REAL_DATA_CHAIN = PASS")
    print("SOURCE_TECHNICAL_AUTHORITY_BOUNDARY = PASS")
    print("STRUCTURAL_GEOMETRY_STATE = OPEN/ND")
    print("PROPOSAL_CANONICAL_WRITE = false")
    print("HUMAN_HVA = REQUIRED_NOT_SATISFIED")
    print("ACCESSIBILITY_GATE = REQUIRED_NOT_SATISFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
