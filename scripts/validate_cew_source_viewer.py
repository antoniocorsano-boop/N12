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
REGIONS = ROOT / "data" / "canonical" / "CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
OBS = ROOT / "data" / "canonical" / "CEW_OBSERVATION_REGISTRY_v1.csv"
TASKS = ROOT / "data" / "canonical" / "CEW_ERW_RESOLUTION_TASKS_v1.csv"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--built-dir", required=True); args = ap.parse_args()
    built = Path(args.built_dir)

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "CEW-SOURCE-VIEWER-v1":
        raise AssertionError("unexpected source viewer contract")
    if contract["viewer_engine"]["name"] != "OpenSeadragon" or contract["viewer_engine"]["version"] != "5.0.1":
        raise AssertionError("viewer engine/version drift")
    if int(contract["pdf_renderer"]["minimum_dpi"]) < 300:
        raise AssertionError("source viewer technical render below 300 dpi")
    if contract["authority_invariants"].get("viewer_may_write_canonical_data") is not False:
        raise AssertionError("viewer must remain read-only")
    modes = contract.get("view_modes", {})
    if modes.get("ORIGINAL", {}).get("state") != "ENABLED":
        raise AssertionError("ORIGINAL view mode must be explicitly enabled")
    if modes.get("ENHANCED", {}).get("state") != "DISABLED_UNTIL_REGISTERED_DERIVATIVE_EXISTS":
        raise AssertionError("ENHANCED view must remain separately disabled until a registered derivative exists")
    if contract["authority_invariants"].get("enhancement_may_replace_original") is not False:
        raise AssertionError("enhancement may not replace original")

    expected_tasks = set(contract["reference_tasks"])
    bindings = rows(BINDINGS)
    if {r["task_id"].strip() for r in bindings} != expected_tasks:
        raise AssertionError("source viewer binding set mismatch")
    task_ids = {r["task_id"].strip() for r in rows(TASKS)}
    regions = {r["evidence_region_id"].strip(): r for r in rows(REGIONS)}
    obs = {r["reference_item"].strip(): r for r in rows(OBS)}
    for b in bindings:
        if b["binding_state"].strip() != "READY":
            raise AssertionError(f"viewer binding not READY: {b['task_id']}")
        if b["task_id"].strip() not in task_ids:
            raise AssertionError(f"unknown viewer task: {b['task_id']}")
        region = regions.get(b["evidence_region_id"].strip())
        if not region or region["readiness_state"].strip() != "READY":
            raise AssertionError(f"viewer binding lacks READY region: {b['task_id']}")
        observation = obs.get(region["reference_item"].strip())
        if not observation or observation["reading_state"].strip() == "MIGRATED_NEEDS_REGION":
            raise AssertionError(f"viewer binding lacks finalized observation: {b['task_id']}")

    required_files = ["index.html", "app.js", "styles.css", "viewer_manifest.json", "vendor/openseadragon/openseadragon.min.js", "tiles/TAV-05A.dzi", "tiles/TAV-06A.dzi"]
    for rel in required_files:
        if not (built / rel).is_file(): raise AssertionError(f"missing built viewer file: {rel}")
    for src in ("TAV-05A", "TAV-06A"):
        tile_dir = built / "tiles" / f"{src}_files"
        if not tile_dir.is_dir() or not any(tile_dir.rglob("*.jpg")):
            raise AssertionError(f"missing DZI tiles: {src}")

    manifest = json.loads((built / "viewer_manifest.json").read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    if len(entries) != 4 or {e["task_id"] for e in entries} != expected_tasks:
        raise AssertionError("viewer manifest reference set mismatch")
    if manifest.get("view_modes", {}).get("ORIGINAL", {}).get("state") != "ENABLED":
        raise AssertionError("viewer manifest lacks explicit ORIGINAL mode")
    if manifest.get("view_modes", {}).get("ENHANCED", {}).get("state") != "DISABLED_UNTIL_REGISTERED_DERIVATIVE_EXISTS":
        raise AssertionError("viewer manifest does not preserve enhanced-mode separation")
    if len({e["region_id"] for e in entries}) != 4:
        raise AssertionError("viewer region deep links are not unique")
    for e in entries:
        b = e["bbox"]
        if not (0 <= b["x"] <= 1 and 0 <= b["y"] <= 1 and 0 < b["width"] <= 1 and 0 < b["height"] <= 1):
            raise AssertionError(f"invalid viewer bbox: {e['task_id']}")
        if not (built / e["dzi"]).is_file(): raise AssertionError(f"manifest DZI missing: {e['dzi']}")

    for rel in ("index.html", "app.js", "styles.css"):
        text = (built / rel).read_text(encoding="utf-8")
        if re.search(r"https?://", text, flags=re.I): raise AssertionError(f"external runtime dependency found in {rel}")
    html = (built / "index.html").read_text(encoding="utf-8")
    js = (built / "app.js").read_text(encoding="utf-8")
    for token in ("openseadragon.min.js", "task-select", "viewer", "original-mode", "enhanced-mode", "Enhanced — unavailable"):
        if token not in html: raise AssertionError(f"viewer HTML missing token: {token}")
    for token in ("URLSearchParams", "region", "task", "fitBounds", "showNavigator"):
        if token not in js: raise AssertionError(f"viewer deep-link/navigation behavior missing: {token}")

    print("SOURCE_VIEWER_PASS")
    print("REFERENCE_TASKS=4")
    print("VIEW_MODES=ORIGINAL_ENABLED;ENHANCED_SEPARATE_DISABLED")
    print("RUNTIME_DEPENDENCIES=SELF_CONTAINED")
    print("AUTHORITY=PRIMARY_PDF; VIEWER=TILES_DERIVED_REVIEW_AID_ONLY")
    return 0


if __name__ == "__main__": raise SystemExit(main())
