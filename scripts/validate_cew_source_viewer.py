#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_SOURCE_VIEWER_CONTRACT_v1.json"
BINDINGS = ROOT / "data" / "canonical" / "CEW_SOURCE_VIEWER_BINDINGS_v1.csv"
OA_BINDINGS = ROOT / "data" / "canonical" / "CEW_OA_SOURCE_VIEWER_BINDINGS_v1.csv"
REGIONS = ROOT / "data" / "canonical" / "CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
OBS = ROOT / "data" / "canonical" / "CEW_OBSERVATION_REGISTRY_v1.csv"
TRANSFORMS = ROOT / "data" / "canonical" / "CEW_PAGE_TRANSFORM_REGISTRY_v1.csv"
MILESTONES = ROOT / "data" / "canonical" / "CEW_SYSTEM_MILESTONES_v1.csv"
MANIFEST = ROOT / "knowledge" / "KNOWLEDGE_MANIFEST.json"
PATCH = "knowledge/ARTIFACT_REGISTRY_CEW_SOURCE_VIEWER_PATCH_v1.csv"
DEPS = {
    "knowledge/ARTIFACT_REGISTRY_CEW_FOUNDATION_PATCH_v1.csv",
    "knowledge/ARTIFACT_REGISTRY_CEW_SOURCE_FOUNDATION_PATCH_v1.csv",
    "knowledge/ARTIFACT_REGISTRY_CEW_EVIDENCE_FOUNDATION_PATCH_v1.csv",
    PATCH,
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--built-dir", required=True); args = ap.parse_args()
    built = Path(args.built_dir)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "CEW-SOURCE-VIEWER-v1": raise AssertionError("unexpected source viewer contract")
    if contract["authority_invariants"].get("viewer_may_write_canonical_data") is not False: raise AssertionError("viewer must remain read-only")
    if contract["coordinate_policy"].get("viewer_may_modify_evidence_geometry") is not False: raise AssertionError("F3 may not modify F2 evidence geometry")
    if contract["coordinate_policy"].get("viewer_input_space") != "NORMALIZED_0_1": raise AssertionError("viewer input coordinate space drift")

    frozen_tasks = set(contract.get("frozen_reference_tasks") or [])
    oa_extension_tasks = set(contract.get("oa_extension_tasks") or [])
    effective_declared_tasks = set(contract.get("reference_tasks") or [])
    if len(frozen_tasks) != 4: raise AssertionError("frozen F3 reference task set must remain exactly four")
    if frozen_tasks & oa_extension_tasks: raise AssertionError("F3 frozen tasks and OA extensions must be disjoint")
    if effective_declared_tasks != frozen_tasks | oa_extension_tasks: raise AssertionError("source viewer declared task union drift")

    milestone = {r["milestone_id"].strip(): r["status"].strip() for r in rows(MILESTONES)}
    if milestone.get("CEW-F2") != "COMPLETE" or milestone.get("CEW-F3") != "COMPLETE": raise AssertionError("F3 post-closure validation requires F2/F3 COMPLETE")
    knowledge = json.loads(MANIFEST.read_text(encoding="utf-8"))
    missing_patches = DEPS - set(knowledge.get("artifact_registry_patches", []))
    if missing_patches: raise AssertionError("CEW artifact patches are not effective in KNOWLEDGE_MANIFEST: " + ", ".join(sorted(missing_patches)))

    legacy_bindings = rows(BINDINGS)
    oa_bindings = rows(OA_BINDINGS) if OA_BINDINGS.exists() else []
    bindings = legacy_bindings + oa_bindings
    regions = {r["evidence_region_id"].strip(): r for r in rows(REGIONS)}
    transforms = {r["transform_id"].strip(): r for r in rows(TRANSFORMS)}
    observations = {r["reference_item"].strip(): r for r in rows(OBS)}
    legacy_task_set = {b["task_id"].strip() for b in legacy_bindings}
    oa_binding_task_set = {b["task_id"].strip() for b in oa_bindings}
    if legacy_task_set != frozen_tasks: raise AssertionError("frozen F3 reference task set changed")
    if oa_binding_task_set != oa_extension_tasks: raise AssertionError("OA viewer extension task/binding set mismatch")
    if len({b["task_id"].strip() for b in bindings}) != len(bindings): raise AssertionError("duplicate viewer task binding across domains")

    for b in bindings:
        rid = b["evidence_region_id"].strip(); tid = b["transform_id"].strip()
        region = regions.get(rid); transform = transforms.get(tid)
        if not region or not transform: raise AssertionError(f"missing F2 parent for viewer binding {b['task_id']}")
        if region["readiness_state"].strip() != "READY" or transform["readiness_state"].strip() != "READY": raise AssertionError(f"viewer binding parent not READY: {b['task_id']}")
        if region["transform_id"].strip() != tid: raise AssertionError(f"F3 binding transform differs from F2 region: {rid}")
        if transform["viewer_consumption_formula"].strip() != "viewer_x=x_n;viewer_y=y_n;viewer_w=w_n;viewer_h=h_n": raise AssertionError(f"F3 geometry reinterpretation detected: {tid}")
        if region["coordinate_space"].strip() != "NORMALIZED_0_1": raise AssertionError(f"F3 consumes non-certified coordinate space: {rid}")
        obs = observations.get(region["reference_item"].strip())
        if not obs or obs["reading_state"].strip() == "MIGRATED_NEEDS_REGION": raise AssertionError(f"non-finalized F2 observation: {rid}")

    required_files = ["index.html","app.js","styles.css","viewer_manifest.json","vendor/openseadragon/openseadragon.min.js"]
    for rel in required_files:
        if not (built / rel).is_file(): raise AssertionError(f"missing built viewer file: {rel}")

    vm = json.loads((built / "viewer_manifest.json").read_text(encoding="utf-8"))
    entries = vm.get("entries", [])
    manifest_tasks = {e["task_id"] for e in entries}
    effective_tasks = {b["task_id"].strip() for b in bindings}
    if manifest_tasks != effective_tasks: raise AssertionError("viewer manifest effective task set mismatch")
    if not frozen_tasks <= manifest_tasks: raise AssertionError("viewer manifest lost frozen F3 reference task")
    if not oa_extension_tasks <= manifest_tasks: raise AssertionError("viewer manifest lost declared OA extension task")

    effective_source_codes = {e["source_code"] for e in entries}
    for src in effective_source_codes:
        if not (built / "tiles" / f"{src}.dzi").is_file(): raise AssertionError(f"missing effective-task DZI descriptor: {src}")
        tile_dir = built / "tiles" / f"{src}_files"
        if not tile_dir.is_dir() or not any(tile_dir.rglob("*.jpg")): raise AssertionError(f"missing effective-task DZI tiles: {src}")

    for e in entries:
        region = regions[e["region_id"]]
        canonical_bbox = {k: float(region[k]) for k in ("x","y","width","height")}
        if e["bbox"] != canonical_bbox: raise AssertionError(f"viewer bbox differs from F2 canonical geometry: {e['region_id']}")
        if e["transform_id"] != region["transform_id"].strip(): raise AssertionError(f"viewer transform differs from F2 canonical transform: {e['region_id']}")
        if not (built / e["dzi"]).is_file(): raise AssertionError(f"manifest DZI missing: {e['dzi']}")

    for rel in ("index.html","app.js","styles.css"):
        text = (built / rel).read_text(encoding="utf-8")
        if re.search(r"https?://", text, flags=re.I): raise AssertionError(f"external runtime dependency found in {rel}")
    js = (built / "app.js").read_text(encoding="utf-8")
    for token in ("URLSearchParams","region","task","fitBounds","showNavigator"):
        if token not in js: raise AssertionError(f"viewer navigation behavior missing: {token}")

    print("SOURCE_VIEWER_PASS")
    print(f"FROZEN_REFERENCE_TASKS={len(frozen_tasks)}")
    print(f"OA_EXTENSION_TASKS={len(oa_extension_tasks)}")
    print(f"EFFECTIVE_VIEWER_TASKS={len(effective_tasks)}")
    print("F2_GEOMETRY_CONSUMPTION=IDENTITY_ONLY")
    print("F3_GEOMETRY_MUTATION=FORBIDDEN")
    print("POST_CLOSURE_STATE=F3_COMPLETE_PHASE_MONOTONIC")
    print("RUNTIME_DEPENDENCIES=SELF_CONTAINED")
    print("AUTHORITY=PRIMARY_PDF; VIEWER=TILES_DERIVED_REVIEW_AID_ONLY")
    return 0

if __name__ == "__main__": raise SystemExit(main())
