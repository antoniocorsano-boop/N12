#!/usr/bin/env python3
"""Generate a self-contained CEW Structural Viewer v0 from the canonical graph.

The viewer is read-only. It never modifies topology, evidence or properties.
Foundation Z is unresolved in N12; for visualization only foundation entities are
placed on a synthetic display plane below G1. The synthetic display coordinate
is never serialized back into the canonical engineering model.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from cew_structural_model_builder import BuildError, build_model


def make_html(model: dict) -> str:
    payload = json.dumps(model, ensure_ascii=False, separators=(",", ":"))
    inv = model["inventory"]
    title = f"CEW Structural Viewer · {model['project_id']}"
    return f'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{--bg:#0f141a;--panel:#17202a;--text:#e9eef3;--muted:#99a7b4;--line:#8393a1;--accent:#4fa3ff;--doc:#56c596;--mis:#e8b44a;--inf:#9f86ff;--nd:#ec6b73;--mod:#5cc8d7;}}
*{{box-sizing:border-box}} html,body{{height:100%;margin:0;background:var(--bg);color:var(--text);font:14px/1.35 system-ui,-apple-system,Segoe UI,sans-serif}}
#app{{height:100%;display:grid;grid-template-columns:minmax(0,1fr) 340px;grid-template-rows:auto 1fr}}
header{{grid-column:1/-1;display:flex;gap:18px;align-items:center;padding:10px 14px;background:#111922;border-bottom:1px solid #293541}}
header strong{{font-size:15px}} .stat{{color:var(--muted);font-size:12px}} .warn{{margin-left:auto;color:#ffd17a;font-size:12px}}
#viewport{{position:relative;overflow:hidden}} canvas{{width:100%;height:100%;display:block;cursor:grab}} canvas.drag{{cursor:grabbing}}
#toolbar{{position:absolute;left:12px;top:12px;background:rgba(20,29,38,.92);padding:9px;border:1px solid #334250;border-radius:8px;display:grid;gap:7px;min-width:190px}}
label{{display:flex;align-items:center;gap:6px;color:#cad3dc;font-size:12px}} select,button{{background:#222e39;color:var(--text);border:1px solid #41505e;border-radius:5px;padding:5px 7px}} button{{cursor:pointer}}
#legend{{display:flex;flex-wrap:wrap;gap:8px;font-size:11px;color:var(--muted)}} .dot{{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:3px}}
aside{{background:var(--panel);border-left:1px solid #2a3743;overflow:auto;padding:14px}} aside h2{{font-size:15px;margin:0 0 12px}} .empty{{color:var(--muted)}}
.kv{{display:grid;grid-template-columns:105px 1fr;gap:5px 8px;padding:8px 0;border-bottom:1px solid #2a3743}} .k{{color:var(--muted)}} .v{{word-break:break-word}}
.badge{{display:inline-block;padding:2px 6px;border-radius:999px;background:#263440;font-size:11px}}
.sources{{margin:6px 0 0;padding-left:18px;color:#b9c5cf}} #residual{{padding:8px 10px;background:#33272a;border:1px solid #61434a;border-radius:6px;color:#ffd4d7;margin-top:12px}}
@media(max-width:850px){{#app{{grid-template-columns:1fr;grid-template-rows:auto 62vh auto}} aside{{border-left:0;border-top:1px solid #2a3743}} header{{gap:8px;flex-wrap:wrap}} .warn{{margin-left:0}}}}
</style>
</head>
<body>
<div id="app">
<header>
<strong>{html.escape(title)}</strong>
<span class="stat">{inv['superstructure_nodes']} nodi</span>
<span class="stat">{inv['ordinary_members']} aste</span>
<span class="stat">{inv['rigid_offsets']} offset rigidi</span>
<span class="stat">fondazioni {inv['foundation_supports']}+{inv['foundation_members']}</span>
<span class="warn">ZF_COMMON: quota numerica ND · piano fondazioni solo grafico</span>
</header>
<div id="viewport"><canvas id="c"></canvas>
<div id="toolbar">
<label><input id="members" type="checkbox" checked> aste ordinarie</label>
<label><input id="rigid" type="checkbox"> offset rigidi</label>
<label><input id="found" type="checkbox" checked> fondazioni</label>
<label><input id="nodes" type="checkbox"> nodi</label>
<label>Piano <select id="level"><option value="ALL">Tutti</option><option>G1</option><option>G2</option><option>G3</option><option>G4</option><option>G5</option></select></label>
<label>Colore <select id="colorMode"><option value="type">tipo</option><option value="evidence">evidenza</option></select></label>
<div><button id="reset">Reset vista</button></div>
<div id="legend"></div>
</div></div>
<aside><h2>Elemento selezionato</h2><div id="detail" class="empty">Clicca una linea o un nodo del modello.</div><div id="residual">La geometria fondazioni è visualizzata su un piano sintetico solo per orientamento. Nessuna quota Z viene promossa nel modello canonico.</div></aside>
</div>
<script>
const MODEL={payload};
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
const detail=document.getElementById('detail');
const checks={{members:document.getElementById('members'),rigid:document.getElementById('rigid'),found:document.getElementById('found'),nodes:document.getElementById('nodes')}};
const level=document.getElementById('level'), colorMode=document.getElementById('colorMode');
let view={{az:-0.72,el:0.55,zoom:25,panX:0,panY:0}}, drag=null, hit=[];
const nodeMap=new Map(MODEL.nodes.map(n=>[n.entity_id,n]));
const fMap=new Map(MODEL.foundation_supports.map(n=>[n.entity_id,n]));
const syntheticFoundationZ=-1.2; // DISPLAY ONLY — not engineering data.
function pointOf(n){{let p=n.point3d;if(p.z===null||p.z===undefined)return [p.x,p.y,syntheticFoundationZ];return [p.x,p.y,p.z];}}
function evidenceColor(s){{s=String(s||'ND').toUpperCase();if(s.includes('DOC'))return '#56c596';if(s.includes('MIS'))return '#e8b44a';if(s.includes('INF'))return '#9f86ff';if(s.includes('MOD'))return '#5cc8d7';if(s.includes('ND')||s.includes('INC'))return '#ec6b73';return '#a7b4bf';}}
function typeColor(t){{if(t==='BEAM')return '#62a9e8';if(t==='COLUMN')return '#d7dce1';if(t==='RIGID_OFFSET')return '#8a7ca8';if(t==='FOUNDATION_MEMBER')return '#cf9a61';if(t==='FOUNDATION_SUPPORT')return '#e5ba83';return '#9aa8b5';}}
function col(e){{return colorMode.value==='evidence'?evidenceColor(e.evidence_state):typeColor(e.entity_type)}}
function resize(){{const r=canvas.getBoundingClientRect(),d=devicePixelRatio||1;canvas.width=Math.round(r.width*d);canvas.height=Math.round(r.height*d);ctx.setTransform(d,0,0,d,0,0);draw();}}
function project(p){{let [x,y,z]=p;let ca=Math.cos(view.az),sa=Math.sin(view.az),ce=Math.cos(view.el),se=Math.sin(view.el);let xr=x*ca-y*sa, yr=x*sa+y*ca;let yy=yr*ce-z*se;return [canvas.clientWidth/2+view.panX+xr*view.zoom,canvas.clientHeight/2+view.panY-yy*view.zoom];}}
function levelOk(e){{if(level.value==='ALL')return true;return e.storey_id===level.value||e.level_id===level.value;}}
function line(a,b,e,w=1,dash=[]){{let p=project(a),q=project(b);ctx.beginPath();ctx.setLineDash(dash);ctx.moveTo(...p);ctx.lineTo(...q);ctx.strokeStyle=col(e);ctx.lineWidth=w;ctx.stroke();ctx.setLineDash([]);hit.push({{kind:'line',p,q,e}});}}
function dot(p,e,r=2.5){{let q=project(p);ctx.beginPath();ctx.arc(q[0],q[1],r,0,Math.PI*2);ctx.fillStyle=col(e);ctx.fill();hit.push({{kind:'point',p:q,e}});}}
function draw(){{ctx.clearRect(0,0,canvas.clientWidth,canvas.clientHeight);hit=[];ctx.lineCap='round';
 if(checks.members.checked)for(const e of MODEL.members){{if(!levelOk(e))continue;let a=nodeMap.get(e.member_axis.start_node_id),b=nodeMap.get(e.member_axis.end_node_id);if(a&&b)line(pointOf(a),pointOf(b),e,e.entity_type==='COLUMN'?2.2:1.7);}}
 if(checks.rigid.checked)for(const e of MODEL.rigid_offsets){{let a=nodeMap.get(e.core_node_id),b=nodeMap.get(e.face_node_id);if(a&&b&&levelOk(a))line(pointOf(a),pointOf(b),e,1,[3,3]);}}
 if(checks.found.checked){{for(const e of MODEL.foundation_members){{let a=fMap.get(e.member_axis.start_node_id),b=fMap.get(e.member_axis.end_node_id);if(a&&b)line(pointOf(a),pointOf(b),e,2.4);}} for(const e of MODEL.foundation_supports)dot(pointOf(e),e,3);}}
 if(checks.nodes.checked)for(const e of MODEL.nodes){{if(levelOk(e))dot(pointOf(e),e,e.entity_type==='SUPPORT_CORE'?2.8:1.7);}}
}}
function distSeg(px,py,a,b){{let vx=b[0]-a[0],vy=b[1]-a[1],wx=px-a[0],wy=py-a[1],c1=vx*wx+vy*wy,c2=vx*vx+vy*vy,t=c2?Math.max(0,Math.min(1,c1/c2)):0,dx=px-(a[0]+t*vx),dy=py-(a[1]+t*vy);return Math.hypot(dx,dy)}}
function pick(x,y){{let best=null,bd=10;for(const h of hit){{let d=h.kind==='line'?distSeg(x,y,h.p,h.q):Math.hypot(x-h.p[0],y-h.p[1]);if(d<bd){{bd=d;best=h.e}}}}if(best)show(best)}}
function esc(s){{return String(s??'').replace(/[&<>]/g,m=>({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[m]))}}
function row(k,v){{return `<div class="k">${{esc(k)}}</div><div class="v">${{esc(v??'—')}}</div>`}}
function show(e){{let src=(e.source_claim_refs||[]).filter(Boolean).map(s=>`<li>${{esc(s)}}</li>`).join('');let axis=e.member_axis?`${{e.member_axis.start_node_id}} → ${{e.member_axis.end_node_id}}`:'';let p=e.point3d?`${{e.point3d.x}}, ${{e.point3d.y}}, ${{e.point3d.z??e.point3d.z_symbol??'ND'}}`:'';
 detail.className='';detail.innerHTML=`<div class="kv">${{row('ID',e.entity_id)}}${{row('Tipo',e.entity_type)}}${{row('Stato',e.status)}}<div class="k">Evidenza</div><div class="v"><span class="badge">${{esc(e.evidence_state)}}</span></div>${{row('Piano',e.storey_id||e.level_id)}}${{row('Supporto',e.support_id)}}${{row('Asse',axis)}}${{row('Coordinate',p)}}${{row('Sezione',e.section_ref_or_value||e.section_family)}}${{row('Binding',e.property_binding_class)}}${{row('Geometria',e.geometry_status)}}</div><div class="k">Provenienza</div><ul class="sources">${{src||'<li>non esposta</li>'}}</ul>`;}}
canvas.addEventListener('pointerdown',e=>{{drag={{x:e.clientX,y:e.clientY,px:view.panX,py:view.panY,az:view.az,el:view.el,button:e.button}};canvas.setPointerCapture(e.pointerId);canvas.classList.add('drag')}});
canvas.addEventListener('pointermove',e=>{{if(!drag)return;let dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(e.shiftKey||drag.button===1){{view.panX=drag.px+dx;view.panY=drag.py+dy}}else{{view.az=drag.az+dx*.008;view.el=Math.max(-1.2,Math.min(1.2,drag.el-dy*.006))}}draw()}});
canvas.addEventListener('pointerup',e=>{{if(drag&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)<4){{let r=canvas.getBoundingClientRect();pick(e.clientX-r.left,e.clientY-r.top)}}drag=null;canvas.classList.remove('drag')}});
canvas.addEventListener('wheel',e=>{{e.preventDefault();view.zoom=Math.max(4,Math.min(120,view.zoom*Math.exp(-e.deltaY*.001)));draw()}},{{passive:false}});
for(const x of [...Object.values(checks),level,colorMode])x.addEventListener('change',draw);
document.getElementById('reset').onclick=()=>{{view={{az:-0.72,el:0.55,zoom:25,panX:0,panY:0}};draw()}};
function legend(){{document.getElementById('legend').innerHTML=colorMode.value==='evidence'?'<span><i class="dot" style="background:#56c596"></i>DOC</span><span><i class="dot" style="background:#e8b44a"></i>MIS</span><span><i class="dot" style="background:#9f86ff"></i>INF</span><span><i class="dot" style="background:#5cc8d7"></i>MOD</span><span><i class="dot" style="background:#ec6b73"></i>ND/INC</span>':'<span>travi · pilastri · offset · fondazioni</span>';}}
colorMode.addEventListener('change',legend);legend();new ResizeObserver(resize).observe(document.getElementById('viewport'));resize();
</script></body></html>'''


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--handoff", required=True, type=Path)
    p.add_argument("--nodes", required=True, type=Path)
    p.add_argument("--rigid-offsets", required=True, type=Path)
    p.add_argument("--members", required=True, type=Path)
    p.add_argument("--foundation", required=True, type=Path)
    p.add_argument("--foundation-xy-rule", required=True, type=Path)
    p.add_argument("--output-html", required=True, type=Path)
    args = p.parse_args()
    try:
        model = build_model(args.handoff,args.nodes,args.rigid_offsets,args.members,args.foundation,args.foundation_xy_rule)
    except (OSError, json.JSONDecodeError, BuildError) as exc:
        print(f"CEW STRUCTURAL VIEWER: FAIL: {exc}")
        return 2
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    args.output_html.write_text(make_html(model), encoding="utf-8")
    print(f"CEW STRUCTURAL VIEWER: PASS | output={args.output_html} | entities={len(model['nodes'])+len(model['rigid_offsets'])+len(model['members'])+len(model['foundation_supports'])+len(model['foundation_members'])}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
