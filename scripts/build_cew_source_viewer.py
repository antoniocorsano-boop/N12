#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_SOURCE_VIEWER_CONTRACT_v1.json"
BINDINGS = ROOT / "data" / "canonical" / "CEW_SOURCE_VIEWER_BINDINGS_v1.csv"
REGIONS = ROOT / "data" / "canonical" / "CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
OBS = ROOT / "data" / "canonical" / "CEW_OBSERVATION_REGISTRY_v1.csv"
TASKS = ROOT / "data" / "canonical" / "CEW_ERW_RESOLUTION_TASKS_v1.csv"
SOURCES = ROOT / "data" / "canonical" / "CEW_SOURCE_IDENTITY_REGISTRY_v1.csv"
PAGES = ROOT / "data" / "canonical" / "CEW_PAGE_REGISTRY_v1.csv"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def idx(path: Path, key: str) -> dict[str, dict[str, str]]:
    return {r[key].strip(): r for r in rows(path)}


def build_manifest() -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    bindings = rows(BINDINGS)
    regions = idx(REGIONS, "evidence_region_id")
    observations = {r["reference_item"].strip(): r for r in rows(OBS)}
    tasks = idx(TASKS, "task_id")
    sources = idx(SOURCES, "source_version_id")
    pages = idx(PAGES, "page_id")

    expected = set(contract["reference_tasks"])
    actual = {r["task_id"].strip() for r in bindings}
    if actual != expected:
        raise AssertionError(f"viewer binding task set mismatch: expected={sorted(expected)} actual={sorted(actual)}")

    source_to_dzi = {"TAV-05A": "tiles/TAV-05A.dzi", "TAV-06A": "tiles/TAV-06A.dzi"}
    entries: list[dict] = []
    for b in bindings:
        task_id = b["task_id"].strip()
        region_id = b["evidence_region_id"].strip()
        if b["binding_state"].strip() != "READY":
            raise AssertionError(f"viewer binding not READY: {task_id}")
        if task_id not in tasks or region_id not in regions:
            raise AssertionError(f"viewer binding parent missing: {task_id}")
        region = regions[region_id]
        if region["readiness_state"].strip() != "READY":
            raise AssertionError(f"viewer region not READY: {region_id}")
        ref = region["reference_item"].strip()
        obs = observations.get(ref)
        if not obs or obs["reading_state"].strip() == "MIGRATED_NEEDS_REGION":
            raise AssertionError(f"viewer observation not finalized: {ref}")
        source_version = sources[b["source_version_id"].strip()]
        page = pages[b["page_id"].strip()]
        source_code = page["logical_source_code"].strip()
        if source_code not in source_to_dzi:
            raise AssertionError(f"no DZI target declared for source: {source_code}")
        bbox = {k: float(region[k]) for k in ("x", "y", "width", "height")}
        task = tasks[task_id]
        entries.append({
            "task_id": task_id,
            "residual_id": b["residual_id"].strip(),
            "region_id": region_id,
            "reference_item": ref,
            "source_code": source_code,
            "source_version_id": b["source_version_id"].strip(),
            "source_sha256": source_version["sha256"].strip(),
            "page_id": b["page_id"].strip(),
            "page_index": int(page["page_index"]),
            "page_width_pt": float(page["source_width"]),
            "page_height_pt": float(page["source_height"]),
            "dzi": source_to_dzi[source_code],
            "bbox": bbox,
            "initial_view_policy": b["initial_view_policy"].strip(),
            "question": task["question"].strip(),
            "known_claims": task["known_claims"].strip(),
            "unknown_claims": task["unknown_claims"].strip(),
            "conflicts": task["conflicts"].strip(),
            "suggested_actions": task["suggested_actions"].strip(),
            "observation": obs["literal_or_value"].strip(),
            "reading_state": obs["reading_state"].strip(),
            "epistemic_ceiling": obs["epistemic_ceiling"].strip(),
            "authority_note": b["authority_note"].strip(),
        })

    return {
        "contract_id": contract["contract_id"],
        "milestone": contract["milestone"],
        "authority_banner": "PRIMARY PDF IS AUTHORITY — VIEWER RENDER/TILES ARE DERIVED REVIEW AIDS ONLY",
        "view_modes": contract["view_modes"],
        "entries": entries,
    }


HTML = """<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>CEW Source Viewer</title><link rel=\"stylesheet\" href=\"styles.css\">
<script src=\"vendor/openseadragon/openseadragon.min.js\"></script>
</head>
<body>
<header><div><strong>CEW Source Viewer</strong><span id=\"task-label\"></span></div><div class=\"authority\" id=\"authority\"></div></header>
<main>
<section class=\"viewer-shell\"><div id=\"viewer\"></div></section>
<aside>
<label for=\"task-select\">Resolution task</label><select id=\"task-select\"></select>
<div class=\"mode-panel\"><strong>View</strong><div><button id=\"original-mode\" aria-pressed=\"true\">Original</button><button id=\"enhanced-mode\" disabled title=\"No registered enhanced derivative exists\">Enhanced — unavailable</button></div><small id=\"mode-note\">Original technical render reproduced from the immutable source. Derived review aid only.</small></div>
<div class=\"actions\"><button id=\"fit\">Fit evidence</button><button id=\"home\">Whole sheet</button><button id=\"copy\">Copy permalink</button></div>
<dl id=\"details\"></dl>
</aside>
</main><script src=\"app.js\"></script>
</body></html>
"""

CSS = """html,body{margin:0;height:100%;font-family:system-ui,sans-serif;background:#f4f5f7;color:#15171a}body{display:flex;flex-direction:column}header{display:flex;justify-content:space-between;gap:1rem;padding:.65rem 1rem;background:#fff;border-bottom:1px solid #d9dde3;font-size:.92rem}header strong{margin-right:.75rem}.authority{font-size:.72rem;font-weight:700;letter-spacing:.02em}main{display:grid;grid-template-columns:minmax(0,1fr) 360px;min-height:0;flex:1}.viewer-shell{min-width:0;min-height:0;padding:.5rem}#viewer{width:100%;height:100%;background:#202328;border-radius:8px}.evidence-box{border:2px solid currentColor;box-sizing:border-box;pointer-events:none}aside{background:#fff;border-left:1px solid #d9dde3;padding:1rem;overflow:auto}select,button{font:inherit}select{width:100%;padding:.55rem;margin:.35rem 0 1rem}.actions,.mode-panel div{display:flex;flex-wrap:wrap;gap:.4rem}.actions{margin:1rem 0}.mode-panel{padding:.75rem;border:1px solid #d9dde3;border-radius:6px}.mode-panel small{display:block;margin-top:.55rem;line-height:1.35}button{padding:.45rem .65rem}button[disabled]{opacity:.55;cursor:not-allowed}dl{display:grid;grid-template-columns:110px 1fr;gap:.55rem .75rem;font-size:.86rem}dt{font-weight:700}dd{margin:0;overflow-wrap:anywhere}@media(max-width:850px){main{grid-template-columns:1fr;grid-template-rows:minmax(420px,65vh) auto}aside{border-left:0;border-top:1px solid #d9dde3}}"""

JS = r"""let manifest, viewer, current, overlayEl;
const $=id=>document.getElementById(id);
function byQuery(){const q=new URLSearchParams(location.search);const task=q.get('task');const region=q.get('region');return manifest.entries.find(e=>e.task_id===task)||manifest.entries.find(e=>e.region_id===region)||manifest.entries[0]}
function setUrl(entry){const u=new URL(location.href);u.search='';u.searchParams.set('task',entry.task_id);history.replaceState(null,'',u)}
function detail(entry){const items=[['Residual',entry.residual_id],['Source',entry.source_code],['Source hash',entry.source_sha256],['Region',entry.region_id],['Reading',entry.reading_state],['Observation',entry.observation],['Known',entry.known_claims],['Unknown',entry.unknown_claims],['Conflict',entry.conflicts||'—'],['Next action',entry.suggested_actions],['Epistemic ceiling',entry.epistemic_ceiling],['Authority',entry.authority_note]];$('details').innerHTML=items.map(([k,v])=>`<dt>${k}</dt><dd>${v||'—'}</dd>`).join('')}
function regionRect(entry){const item=viewer.world.getItemAt(0),s=item.getContentSize(),b=entry.bbox;return item.imageToViewportRectangle(b.x*s.x,b.y*s.y,b.width*s.x,b.height*s.y)}
function fit(){if(!viewer||!viewer.world.getItemCount())return;const r=regionRect(current);viewer.viewport.fitBounds(r,true);if(overlayEl)viewer.removeOverlay(overlayEl);overlayEl=document.createElement('div');overlayEl.className='evidence-box';viewer.addOverlay({element:overlayEl,location:r})}
function openEntry(entry){current=entry;setUrl(entry);$('task-select').value=entry.task_id;$('task-label').textContent=` · ${entry.task_id} · ${entry.reference_item}`;detail(entry);if(viewer)viewer.destroy();viewer=OpenSeadragon({id:'viewer',prefixUrl:'vendor/openseadragon/images/',tileSources:entry.dzi,showNavigator:true,navigatorAutoFade:false,showRotationControl:true,gestureSettingsMouse:{clickToZoom:false},maxZoomPixelRatio:4});viewer.addOnceHandler('open',fit)}
async function boot(){manifest=await (await fetch('viewer_manifest.json',{cache:'no-store'})).json();$('authority').textContent=manifest.authority_banner;for(const e of manifest.entries){const o=document.createElement('option');o.value=e.task_id;o.textContent=`${e.task_id} — ${e.reference_item}`;$('task-select').appendChild(o)}$('task-select').onchange=()=>openEntry(manifest.entries.find(e=>e.task_id===$('task-select').value));$('fit').onclick=fit;$('home').onclick=()=>viewer.viewport.goHome(true);$('copy').onclick=async()=>navigator.clipboard.writeText(location.href);$('original-mode').onclick=()=>{};openEntry(byQuery())}boot();
"""


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--out-dir", required=True); args = ap.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    (out / "viewer_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "index.html").write_text(HTML, encoding="utf-8")
    (out / "styles.css").write_text(CSS, encoding="utf-8")
    (out / "app.js").write_text(JS, encoding="utf-8")
    print(f"SOURCE_VIEWER_MANIFEST_ENTRIES={len(manifest['entries'])}")
    for e in manifest["entries"]: print(f"VIEWER_BINDING={e['task_id']}->{e['region_id']}->{e['dzi']}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
