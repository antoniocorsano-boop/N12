#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data/canonical/CEW_SOURCE_IDENTITY_REGISTRY_v1.csv"
REGIONS = ROOT / "data/canonical/CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
ASSETS = ROOT / "data/canonical/CEW_DERIVED_ASSET_REGISTRY_v1.csv"
BINDINGS = ROOT / "data/canonical/CEW_SOURCE_VIEWER_BINDINGS_v1.csv"
TASKS = ROOT / "data/canonical/CEW_ERW_RESOLUTION_TASKS_v1.csv"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def index(path: Path, key: str) -> dict[str, dict[str, str]]:
    return {r[key].strip(): r for r in rows(path)}


def ceiling(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("DOC"):
        return "DOC"
    if raw.startswith("MIS"):
        return "MIS"
    if raw.startswith("RIF"):
        return "RIF"
    if raw.startswith("INF"):
        return "INF"
    return "ND"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    sources = index(SOURCES, "source_version_id")
    regions = index(REGIONS, "evidence_region_id")
    tasks = index(TASKS, "task_id")
    assets_by_page = {r["page_id"].strip(): r for r in rows(ASSETS)}
    bindings = rows(BINDINGS)

    packs = []
    for b in bindings:
        task_id = b["task_id"].strip()
        task = tasks[task_id]
        region = regions[b["evidence_region_id"].strip()]
        source = sources[b["source_version_id"].strip()]
        asset = assets_by_page[b["page_id"].strip()]
        if region["readiness_state"].strip() != "READY":
            raise AssertionError(f"region not READY: {region['evidence_region_id']}")
        if source["readiness_state"].strip() != "READY":
            raise AssertionError(f"source not READY: {source['source_version_id']}")
        pack = {
            "evidence_pack_id": f"CEW-PACK-{task_id}",
            "task_id": task_id,
            "source_version_id": source["source_version_id"].strip(),
            "source_sha256": source["sha256"].strip(),
            "page_id": b["page_id"].strip(),
            "evidence_region_id": region["evidence_region_id"].strip(),
            "derived_asset_id": asset["derived_asset_id"].strip(),
            "coordinate_space": region["coordinate_space"].strip(),
            "bbox": {k: float(region[k]) for k in ("x", "y", "width", "height")},
            "task_question": task["question"].strip(),
            "epistemic_ceiling": ceiling(task["epistemic_ceiling"]),
            "structural_binding_state": "UNBOUND" if task_id == "ERW-N12-004" else "NONE_ASSERTED",
            "authority_notice": "PRIMARY PDF SourceVersion is authority; derived render is inspection aid only; answer/history intentionally withheld from worker."
        }
        packs.append(pack)
        (out / f"{task_id}.json").write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")

    (out / "manifest.json").write_text(json.dumps({"schema_version":"1.0","packs":packs}, indent=2) + "\n", encoding="utf-8")
    print(f"EVIDENCE_PACKS_BUILT={len(packs)}")
    print("ANSWER_LEAKAGE=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
