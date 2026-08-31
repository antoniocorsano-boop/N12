#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_SOURCE_VIEWER_CONTRACT_v1.json"
BINDINGS = ROOT / "data" / "canonical" / "CEW_SOURCE_VIEWER_BINDINGS_v1.csv"
OA_BINDINGS = ROOT / "data" / "canonical" / "CEW_OA_SOURCE_VIEWER_BINDINGS_v1.csv"
REGIONS = ROOT / "data" / "canonical" / "CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
OBS = ROOT / "data" / "canonical" / "CEW_OBSERVATION_REGISTRY_v1.csv"
TASKS = ROOT / "data" / "canonical" / "CEW_ERW_RESOLUTION_TASKS_v1.csv"
OA_TASKS = ROOT / "data" / "canonical" / "CEW_OA_TASK_REGISTRY_v1.csv"
SOURCES = ROOT / "data" / "canonical" / "CEW_SOURCE_IDENTITY_REGISTRY_v1.csv"
PAGES = ROOT / "data" / "canonical" / "CEW_PAGE_REGISTRY_v1.csv"
TRANSFORMS = ROOT / "data" / "canonical" / "CEW_PAGE_TRANSFORM_REGISTRY_v1.csv"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def idx(path: Path, key: str) -> dict[str, dict[str, str]]:
    return {r[key].strip(): r for r in rows(path)}


def _union_by_id(primary: list[dict[str, str]], extension: list[dict[str, str]], key: str, label: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in [*primary, *extension]:
        value = row[key].strip()
        if value in result:
            raise AssertionError(f"duplicate {label}: {value}")
        result[value] = row
    return result


def build_manifest() -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    binding_rows = [*rows(BINDINGS), *rows(OA_BINDINGS)]
    regions = idx(REGIONS, "evidence_region_id")
    observations = {r["reference_item"].strip(): r for r in rows(OBS)}
    tasks = _union_by_id(rows(TASKS), rows(OA_TASKS), "task_id", "viewer task id")
    source_rows = rows(SOURCES)
    sources = {r["source_version_id"].strip(): r for r in source_rows}
    pages = idx(PAGES, "page_id")
    transforms = idx(TRANSFORMS, "transform_id")

    expected = set(contract["reference_tasks"])
    actual = {r["task_id"].strip() for r in binding_rows}
    if actual != expected:
        raise AssertionError(f"viewer binding task set mismatch: expected={sorted(expected)} actual={sorted(actual)}")

    source_to_dzi = {
        "TAV-05A": "tiles/TAV-05A.dzi",
        "TAV-06A": "tiles/TAV-06A.dzi",
        "TAV-05S": "tiles/TAV-05S.dzi",
        "TAV-06S": "tiles/TAV-06S.dzi",
    }
    entries: list[dict] = []
    for b in binding_rows:
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
            "context_only": False,
        })

    context_sources = []
    for code in ("TAV-05S", "TAV-06S"):
        candidates = [r for r in source_rows if r["logical_source_code"].strip() == code and r["readiness_state"].strip() == "READY"]
        if len(candidates) != 1:
            raise AssertionError(f"expected exactly one READY context source for {code}")
        r = candidates[0]
        context_sources.append({
            "source_code": code,
            "source_version_id": r["source_version_id"].strip(),
            "source_sha256": r["sha256"].strip(),
            "document_role": r["document_role"].strip(),
            "dzi": source_to_dzi[code],
            "context_only": True,
            "authority_note": "Fonte primaria di carpenteria mostrata in modalità contesto; questa modalità non crea automaticamente EvidenceRegion, classificazioni di oggetto o decisioni.",
        })

    return {
        "contract_id": contract["contract_id"],
        "milestone": contract["milestone"],
        "authority_banner": "IL PDF PRIMARIO È LA FONTE AUTOREVOLE — RENDER E TILE DEL VIEWER SONO SOLO AUSILI DERIVATI PER LA REVISIONE",
        "geometry_banner": "LE REGIONI F2 ESISTENTI SONO IN SOLA LETTURA — LE VISTE DI CONTESTO NON CREANO AUTOMATICAMENTE NUOVE REGIONI",
        "view_modes": contract["view_modes"],
        "entries": entries,
        "context_sources": context_sources,
    }


HTML = """<!doctype html>
<html lang=\"it\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>CEW — Viewer fonte</title><link rel=\"stylesheet\" href=\"styles.css\"><script src=\"vendor/openseadragon/openseadragon.min.js\"></script></head>
<body><header><strong>CEW — Viewer della fonte primaria</strong><span id=\"task-label\"></span><div id=\"authority\"></div><div id=\"geometry\"></div></header><main><section><div id=\"viewer\"></div></section><aside><label>Fonte / task</label><select id=\"task-select\"></select><div><button id=\"fit\">Centra evidenza</button><button id=\"home\">Intera tavola</button></div><p><button id=\"original-mode\" aria-pressed=\"true\">Originale</button> <button id=\"enhanced-mode\" disabled>Migliorata — non disponibile</button></p><p id=\"mode-note\"></p><dl id=\"details\"></dl></aside></main><script src=\"app.js\"></script></body></html>"""
CSS = """html,body{margin:0;height:100%;font-family:system-ui,sans-serif}body{display:flex;flex-direction:column}header{padding:.6rem 1rem;border-bottom:1px solid #ccc;font-size:.8rem}header div{margin-top:.2rem}main{display:grid;grid-template-columns:minmax(0,1fr) 360px;min-height:0;flex:1}section{padding:.5rem;min-height:0}#viewer{height:100%;background:#202328}aside{padding:1rem;border-left:1px solid #ccc;overflow:auto}select{width:100%;margin:.4rem 0 1rem}.evidence-box{border:4px solid #d00000;box-sizing:border-box;pointer-events:none;position:relative}.evidence-label{position:absolute;left:0;top:0;background:#d00000;color:#fff;font:bold 12px system-ui;padding:3px 6px;white-space:nowrap;transform:translateY(-100%)}dl{display:grid;grid-template-columns:110px 1fr;gap:.4rem}dd{margin:0;overflow-wrap:anywhere}@media(max-width:850px){main{grid-template-columns:1fr;grid-template-rows:65vh auto}}"""
JS = r"""let manifest,viewer,current,overlayEl;const $=id=>document.getElementById(id);
function pick(){const q=new URLSearchParams(location.search);const source=q.get('source');if(source){const c=manifest.context_sources.find(e=>e.source_code===source);if(c)return c}return manifest.entries.find(e=>e.task_id===q.get('task'))||manifest.entries.find(e=>e.region_id===q.get('region'))||manifest.entries[0]}
function detail(e){const a=e.context_only?[['Fonte',e.source_code],['Hash',e.source_sha256],['Ruolo',e.document_role],['Autorità',e.authority_note]]:[['Fonte',e.source_code],['Hash',e.source_sha256],['Regione',e.region_id],['Trasformazione',e.transform_id],['Stato lettura',e.reading_state],['Osservazione',e.observation],['Dato noto',e.known_claims],['Dato ignoto',e.unknown_claims],['Autorità',e.authority_note]];$('details').innerHTML=a.map(([k,v])=>`<dt>${k}</dt><dd>${v||'—'}</dd>`).join('')}
function rect(e){const i=viewer.world.getItemAt(0),s=i.getContentSize(),b=e.bbox;return i.imageToViewportRectangle(b.x*s.x,b.y*s.y,b.width*s.x,b.height*s.y)}
function fit(){if(!viewer||!viewer.world.getItemCount())return;if(current.context_only||!current.bbox){viewer.viewport.goHome(true);return}const r=rect(current);viewer.viewport.fitBounds(r,true);if(overlayEl)viewer.removeOverlay(overlayEl);overlayEl=document.createElement('div');overlayEl.className='evidence-box';overlayEl.innerHTML='<span class="evidence-label">ZONA DA CONTROLLARE</span>';viewer.addOverlay({element:overlayEl,location:r})}
function openEntry(e){current=e;const u=new URL(location.href);u.search='';if(e.context_only)u.searchParams.set('source',e.source_code);else u.searchParams.set('task',e.task_id);history.replaceState(null,'',u);$('task-select').value=e.context_only?`source:${e.source_code}`:`task:${e.task_id}`;$('task-label').textContent=e.context_only?` · ${e.source_code} — carpenteria di contesto`:` · ${e.task_id} · ${e.reference_item}`;$('fit').disabled=!!e.context_only;$('mode-note').textContent=e.context_only?'Carpenteria primaria per ricerca e localizzazione. La vista di contesto non crea automaticamente evidenza o oggetti.':'La cornice rossa “ZONA DA CONTROLLARE” è la regione di evidenza F2 certificata per questo task.';detail(e);if(viewer)viewer.destroy();overlayEl=null;viewer=OpenSeadragon({id:'viewer',prefixUrl:'vendor/openseadragon/images/',tileSources:e.dzi,showNavigator:true,navigatorAutoFade:false,gestureSettingsMouse:{clickToZoom:false},maxZoomPixelRatio:4});viewer.addOnceHandler('open',fit)}
async function boot(){manifest=await(await fetch('viewer_manifest.json',{cache:'no-store'})).json();$('authority').textContent=manifest.authority_banner;$('geometry').textContent=manifest.geometry_banner;const sel=$('task-select');for(const e of manifest.entries){const o=document.createElement('option');o.value=`task:${e.task_id}`;o.textContent=`${e.task_id} — ${e.reference_item}`;sel.appendChild(o)}for(const e of manifest.context_sources){const o=document.createElement('option');o.value=`source:${e.source_code}`;o.textContent=`${e.source_code} — carpenteria primaria`;sel.appendChild(o)}sel.onchange=()=>{const [kind,id]=sel.value.split(':');openEntry(kind==='source'?manifest.context_sources.find(e=>e.source_code===id):manifest.entries.find(e=>e.task_id===id))};$('fit').onclick=fit;$('home').onclick=()=>viewer.viewport.goHome(true);openEntry(pick())}boot();"""


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--out-dir", required=True); args = ap.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    (out / "viewer_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "index.html").write_text(HTML, encoding="utf-8")
    (out / "styles.css").write_text(CSS, encoding="utf-8")
    (out / "app.js").write_text(JS, encoding="utf-8")
    print(f"SOURCE_VIEWER_MANIFEST_ENTRIES={len(manifest['entries'])}")
    print(f"SOURCE_VIEWER_CONTEXT_SOURCES={len(manifest['context_sources'])}")
    for e in manifest["entries"]:
        print(f"VIEWER_BINDING={e['task_id']}->{e['region_id']}->{e['transform_id']}->{e['dzi']}")
    for e in manifest["context_sources"]:
        print(f"VIEWER_CONTEXT={e['source_code']}->{e['source_version_id']}->{e['dzi']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
