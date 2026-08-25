#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
MEMBERS = C / "M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"
NODES = C / "M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv"
CONTRACT = ROOT / "automation" / "CEW_ERW_CONTRACT_v1.json"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def one(items: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    matches = [r for r in items if r.get(key, "").strip() == value]
    if len(matches) != 1:
        raise AssertionError(f"expected one {key}={value}, got {len(matches)}")
    return matches[0]


def point(node: dict[str, str]) -> dict:
    return {
        "node_id": node["node_id"].strip(),
        "x_m": float(node["x_m"]),
        "y_m": float(node["y_m"]),
        "z_m": float(node["z_m"]),
        "coordinate_evidence_state": node["coordinate_evidence_state"].strip(),
        "coordinate_derivation": node["coordinate_derivation"].strip(),
        "validation_state": node["validation_state"].strip(),
    }


def member_context(member_rows: list[dict[str, str]], node_rows: list[dict[str, str]], source_member_id: str) -> dict:
    m = one(member_rows, "source_member_id", source_member_id)
    ni = one(node_rows, "node_id", m["node_i"].strip())
    nj = one(node_rows, "node_id", m["node_j"].strip())
    pi, pj = point(ni), point(nj)
    computed = math.dist((pi["x_m"], pi["y_m"], pi["z_m"]), (pj["x_m"], pj["y_m"], pj["z_m"]))
    return {
        "source_member_id": source_member_id,
        "member_id": m["member_id"].strip(),
        "member_class": m["member_class"].strip(),
        "support_i": m["support_i"].strip(),
        "support_j": m["support_j"].strip(),
        "node_i": pi,
        "node_j": pj,
        "frozen_geometric_length_m": float(m["geometric_length_m"]),
        "computed_face_node_length_m": computed,
        "topology_evidence": m["topology_evidence"].strip(),
        "connectivity_evidence": m["connectivity_evidence"].strip(),
        "section_cm": m["section_cm"].strip() or None,
        "authority": "DERIVED_STRUCTURAL_CONTEXT_ONLY",
    }


HTML = """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>CEW F6 Synchronized ERW</title><link rel='stylesheet' href='styles.css'></head><body>
<header><strong>CEW F6 · Synchronized Engineering Review Workspace</strong><span id='authority'></span></header>
<main><nav><label>Review task</label><select id='task'></select><div id='taskmeta'></div></nav><section class='source'><h2>Primary-source review</h2><iframe id='source' title='F3 primary-source viewer'></iframe></section><section class='model'><h2>Derived structural context</h2><p class='warning'>DERIVED STRUCTURAL CONTEXT ONLY — NOT PRIMARY EVIDENCE — NO CANONICAL WRITE</p><svg id='structure' viewBox='0 0 640 420' role='img' aria-label='Derived structural context'></svg><div id='modelmeta'></div></section></main><script src='app.js'></script></body></html>"""

CSS = """html,body{margin:0;height:100%;font-family:system-ui,sans-serif}body{display:flex;flex-direction:column}header{padding:.65rem 1rem;border-bottom:1px solid #bbb}header span{margin-left:1rem;font-size:.78rem}main{display:grid;grid-template-columns:250px minmax(0,1.35fr) minmax(360px,.8fr);min-height:0;flex:1}nav{padding:1rem;border-right:1px solid #ccc;overflow:auto}select{width:100%;margin:.5rem 0 1rem}.source,.model{padding:.6rem;min-height:0;display:flex;flex-direction:column}.source{border-right:1px solid #ccc}h2{font-size:1rem;margin:.15rem 0 .5rem}iframe{border:0;width:100%;flex:1;min-height:520px}svg{width:100%;min-height:320px;background:#f6f6f6;border:1px solid #bbb}.warning{font-size:.76rem;font-weight:700}.context-line{stroke:#555;stroke-width:5}.selected-line{stroke-width:8}.node{fill:#fff;stroke:#333;stroke-width:2}.label{font:14px system-ui,sans-serif}#taskmeta,#modelmeta{font-size:.82rem;overflow-wrap:anywhere}.badge{display:inline-block;border:1px solid #888;padding:.1rem .35rem;margin:.15rem 0}@media(max-width:1050px){main{grid-template-columns:1fr;grid-template-rows:auto 68vh auto}.source{border-right:0}.model{min-height:480px}}"""

JS = r"""let manifest;const $=id=>document.getElementById(id);const ns='http://www.w3.org/2000/svg';
function el(tag,attrs={}){const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);return n}
function proj(p){const X=p.x_m-p.y_m,Y=(p.x_m+p.y_m)*0.42-p.z_m*0.72;return [X,Y]}
function draw(ctx,selected){const svg=$('structure');svg.innerHTML='';if(!ctx){const t=el('text',{x:28,y:55,class:'label'});t.textContent='No structural binding/context available for this review item.';svg.appendChild(t);return}const a=proj(ctx.node_i),b=proj(ctx.node_j),minx=Math.min(a[0],b[0]),maxx=Math.max(a[0],b[0]),miny=Math.min(a[1],b[1]),maxy=Math.max(a[1],b[1]);const sx=500/Math.max(maxx-minx,1),sy=290/Math.max(maxy-miny,1),s=Math.min(sx,sy);const map=q=>[70+(q[0]-minx)*s,70+(q[1]-miny)*s];const A=map(a),B=map(b);svg.appendChild(el('line',{x1:A[0],y1:A[1],x2:B[0],y2:B[1],class:selected?'context-line selected-line':'context-line'}));for(const [p,n] of [[A,ctx.node_i],[B,ctx.node_j]]){svg.appendChild(el('circle',{cx:p[0],cy:p[1],r:7,class:'node'}));const t=el('text',{x:p[0]+10,y:p[1]-10,class:'label'});t.textContent=n.node_id;svg.appendChild(t)}const title=el('text',{x:28,y:390,class:'label'});title.textContent=`${ctx.source_member_id} · ${ctx.support_i}→${ctx.support_j} · ${ctx.frozen_geometric_length_m.toFixed(4)} m`;svg.appendChild(title)}
function openTask(id){const e=manifest.entries.find(x=>x.task_id===id);$('task').value=id;$('source').src=`source-viewer/index.html?task=${encodeURIComponent(id)}`;$('taskmeta').innerHTML=`<b>${e.task_id}</b><br>${e.residual_id}<br><span class='badge'>${e.disposition}</span><p>${e.reference_item}</p>`;draw(e.structural_context,e.structural_selection!==null);let m=`<b>Binding state:</b> ${e.binding_state}<br><b>Selection:</b> ${e.structural_selection||'NONE'}`;if(e.structural_context)m+=`<br><b>Context:</b> ${e.structural_context.source_member_id}<br><b>Coordinate evidence:</b> ${e.structural_context.node_i.coordinate_evidence_state}/${e.structural_context.node_j.coordinate_evidence_state}<br><b>Computed length:</b> ${e.structural_context.computed_face_node_length_m.toFixed(7)} m`;m+=`<p>${e.structural_authority_note}</p>`;$('modelmeta').innerHTML=m;const u=new URL(location.href);u.search='';u.searchParams.set('task',id);history.replaceState(null,'',u)}
async function boot(){manifest=await(await fetch('sync_manifest.json',{cache:'no-store'})).json();$('authority').textContent=manifest.authority_banner;for(const e of manifest.entries){const o=document.createElement('option');o.value=e.task_id;o.textContent=`${e.task_id} — ${e.reference_item}`;$('task').appendChild(o)}$('task').onchange=()=>openTask($('task').value);const q=new URLSearchParams(location.search).get('task');openTask(manifest.entries.some(e=>e.task_id===q)?q:manifest.entries[0].task_id)}boot();"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue-bundle", required=True)
    ap.add_argument("--source-viewer-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(Path(args.queue_bundle).read_text(encoding="utf-8"))
    source_viewer = Path(args.source_viewer_dir)
    if not (source_viewer / "viewer_manifest.json").exists():
        raise AssertionError("F3 viewer manifest missing")
    f3_manifest = json.loads((source_viewer / "viewer_manifest.json").read_text(encoding="utf-8"))
    f3_tasks = {e["task_id"] for e in f3_manifest["entries"]}

    member_rows, node_rows = rows(MEMBERS), rows(NODES)
    g5 = member_context(member_rows, node_rows, "G5-B017")
    entries = []
    for w in queue["workspaces"]:
        tid = w["task"]["task_id"].strip()
        if tid not in f3_tasks:
            raise AssertionError(f"F3 viewer missing task {tid}")
        binding = w["source"]["observation"].get("structural_binding", "").strip()
        context = None
        selection = None
        binding_state = "UNBOUND" if not binding else "BOUND"
        authority_note = "No canonical structural binding exists; structural selection MUST remain empty."
        if binding:
            context = member_context(member_rows, node_rows, binding)
            selection = binding
            authority_note = "Selection mirrors an existing canonical structural binding; the rendering remains derived context only."
        elif tid == "ERW-N12-004":
            context = g5
            authority_note = "G5-B017 is shown only as a rejected candidate-comparison context. T6A-G03 remains UNBOUND and no structural selection/highlight is permitted."
        entries.append({
            "task_id": tid,
            "residual_id": w["residual"]["residual_id"].strip(),
            "reference_item": w["source"]["observation"]["reference_item"].strip(),
            "evidence_region_id": w["source"]["evidence_region"]["evidence_region_id"].strip(),
            "disposition": w["reference_disposition_receipt"]["outcome"],
            "source_view": f"source-viewer/index.html?task={tid}",
            "binding_state": binding_state,
            "structural_selection": selection,
            "structural_context": context,
            "structural_authority_note": authority_note,
        })

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / "source-viewer"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source_viewer, target)
    manifest = {
        "schema_version": "1.0",
        "workspace_id": "CEW-F6-ERW-SYNC-v1",
        "authority": contract["workspace_authority"],
        "authority_banner": "PRIMARY SOURCE PANE RETAINS DOCUMENTARY AUTHORITY — STRUCTURAL PANE IS DERIVED CONTEXT ONLY",
        "canonical_write": False,
        "m0g_reopen": False,
        "epistemic_promotion": False,
        "entries": entries,
    }
    (out / "sync_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out / "index.html").write_text(HTML, encoding="utf-8")
    (out / "styles.css").write_text(CSS, encoding="utf-8")
    (out / "app.js").write_text(JS, encoding="utf-8")
    print("ERW_SYNC_WORKSPACE_BUILT")
    print(f"TASKS={len(entries)}")
    print(f"BOUND_SELECTIONS={sum(e['structural_selection'] is not None for e in entries)}")
    print("UNBOUND_G5_B017_CONTEXT=DERIVED_CANDIDATE_COMPARISON_ONLY")
    print("CANONICAL_WRITE=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
