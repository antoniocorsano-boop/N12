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
TRANSFORMS = ROOT / "data" / "canonical" / "CEW_PAGE_TRANSFORM_REGISTRY_v1.csv"


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
    transforms = idx(TRANSFORMS, "transform_id")

    expected = set(contract["reference_tasks"])
    actual = {r["task_id"].strip() for r in bindings}
    if actual != expected:
        raise AssertionError(f"viewer binding task set mismatch: expected={sorted(expected)} actual={sorted(actual)}")

    source_to_dzi = {"TAV-05A": "tiles/TAV-05A.dzi", "TAV-06A": "tiles/TAV-06A.dzi"}
    entries: list[dict] = []
    for b in bindings:
        task_id = b["task_id"].strip()
        region_id = b["evidence_region_id"].strip()
        transform_id = b["transform_id"].strip()
        if b["binding_state"].strip() != "READY":
            raise AssertionError(f"viewer binding not READY: {task_id}")
        if task_id not in tasks or region_id not in regions or transform_id not in transforms:
            raise AssertionError(f"viewer binding parent missing: {task_id}")

        region = regions[region_id]
        transform = transforms[transform_id]
        if region["readiness_state"].strip() != "READY":
            raise AssertionError(f"viewer region not READY: {region_id}")
        if region["coordinate_space"].strip() != "NORMALIZED_0_1":
            raise AssertionError(f"viewer only consumes certified NORMALIZED_0_1 regions: {region_id}")
        if region["transform_id"].strip() != transform_id:
            raise AssertionError(f"viewer transform differs from F2 region transform: {region_id}")
        if transform["readiness_state"].strip() != "READY":
            raise AssertionError(f"viewer transform not READY: {transform_id}")
        expected_formula = "viewer_x=x_n;viewer_y=y_n;viewer_w=w_n;viewer_h=h_n"
        if transform["viewer_consumption_formula"].strip() != expected_formula:
            raise AssertionError(f"viewer would reinterpret F2 geometry: {transform_id}")

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
            "transform_id": transform_id,
            "viewer_consumption_formula": transform["viewer_consumption_formula"].strip(),
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
        "geometry_banner": "F2 EVIDENCE GEOMETRY IS READ-ONLY — F3 DOES NOT RELOCALIZE OR CORRECT REGIONS",
        "view_modes": contract["view_modes"],
        "entries": entries,
    }


HTML = """<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>CEW Source Viewer</title><link rel=\"stylesheet\" href=\"styles.css\"><script src=\"vendor/openseadragon/openseadragon.min.js\"></script></head>
<body><header><strong>CEW Source Viewer</strong><span id=\"task-label\"></span><div id=\"authority\"></div><div id=\"geometry\"></div></header><main><section><div id=\"viewer\"></div></section><aside><label>Resolution task</label><select id=\"task-select\"></select><div><button id=\"fit\">Fit evidence</button><button id=\"home\">Whole sheet</button></div><p><button id=\"original-mode\" aria-pressed=\"true\">Original</button> <button id=\"enhanced-mode\" disabled>Enhanced — unavailable</button></p><dl id=\"details\"></dl></aside></main><script src=\"app.js\"></script></body></html>"""
CSS = """html,body{margin:0;height:100%;font-family:system-ui,sans-serif}body{display:flex;flex-direction:column}header{padding:.6rem 1rem;border-bottom:1px solid #ccc;font-size:.8rem}header div{margin-top:.2rem}main{display:grid;grid-template-columns:minmax(0,1fr) 360px;min-height:0;flex:1}section{padding:.5rem;min-height:0}#viewer{height:100%;background:#202328}aside{padding:1rem;border-left:1px solid #ccc;overflow:auto}select{width:100%;margin:.4rem 0 1rem}.evidence-box{border:2px solid currentColor;box-sizing:border-box;pointer-events:none}dl{display:grid;grid-template-columns:100px 1fr;gap:.4rem}dd{margin:0;overflow-wrap:anywhere}@media(max-width:850px){main{grid-template-columns:1fr;grid-template-rows:65vh auto}}"""
JS = r"""let manifest,viewer,current,overlayEl;const $=id=>document.getElementById(id);
function pick(){const q=new URLSearchParams(location.search);return manifest.entries.find(e=>e.task_id===q.get('task'))||manifest.entries.find(e=>e.region_id===q.get('region'))||manifest.entries[0]}
function detail(e){const a=[['Source',e.source_code],['Hash',e.source_sha256],['Region',e.region_id],['Transform',e.transform_id],['Reading',e.reading_state],['Observation',e.observation],['Known',e.known_claims],['Unknown',e.unknown_claims],['Authority',e.authority_note]];$('details').innerHTML=a.map(([k,v])=>`<dt>${k}</dt><dd>${v||'—'}</dd>`).join('')}
function rect(e){const i=viewer.world.getItemAt(0),s=i.getContentSize(),b=e.bbox;return i.imageToViewportRectangle(b.x*s.x,b.y*s.y,b.width*s.x,b.height*s.y)}
function fit(){if(!viewer||!viewer.world.getItemCount())return;const r=rect(current);viewer.viewport.fitBounds(r,true);if(overlayEl)viewer.removeOverlay(overlayEl);overlayEl=document.createElement('div');overlayEl.className='evidence-box';viewer.addOverlay({element:overlayEl,location:r})}
function openEntry(e){current=e;const u=new URL(location.href);u.search='';u.searchParams.set('task',e.task_id);history.replaceState(null,'',u);$('task-select').value=e.task_id;$('task-label').textContent=`${e.task_id} · ${e.reference_item}`;detail(e);if(viewer)viewer.destroy();viewer=OpenSeadragon({id:'viewer',prefixUrl:'vendor/openseadragon/images/',tileSources:e.dzi,showNavigator:true,navigatorAutoFade:false,gestureSettingsMouse:{clickToZoom:false},maxZoomPixelRatio:4});viewer.addOnceHandler('open',fit)}
async function boot(){manifest=await(await fetch('viewer_manifest.json',{cache:'no-store'})).json();$('authority').textContent=manifest.authority_banner;$('geometry').textContent=manifest.geometry_banner;for(const e of manifest.entries){const o=document.createElement('option');o.value=e.task_id;o.textContent=`${e.task_id} — ${e.reference_item}`;$('task-select').appendChild(o)}$('task-select').onchange=()=>openEntry(manifest.entries.find(e=>e.task_id===$('task-select').value));$('fit').onclick=fit;$('home').onclick=()=>viewer.viewport.goHome(true);openEntry(pick())}boot();"""


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--out-dir", required=True); args = ap.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    (out / "viewer_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "index.html").write_text(HTML, encoding="utf-8")
    (out / "styles.css").write_text(CSS, encoding="utf-8")
    (out / "app.js").write_text(JS, encoding="utf-8")
    print(f"SOURCE_VIEWER_MANIFEST_ENTRIES={len(manifest['entries'])}")
    for e in manifest["entries"]:
        print(f"VIEWER_BINDING={e['task_id']}->{e['region_id']}->{e['transform_id']}->{e['dzi']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
