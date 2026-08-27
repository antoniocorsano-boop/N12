#!/usr/bin/env python3
from __future__ import annotations

import html
from pathlib import Path
from urllib.parse import quote

import cew_source_evidence_workspace as source_workspace

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DPI = 90
ALLOWED_DPI = {54, 72, 90, 120}
DIMENSION_TOLERANCE_PT = 0.75


def esc(value) -> str:
    return html.escape(str(value or ""))


def drawing_context(source_id: str) -> dict:
    m = source_workspace.maps()
    source = m["sources"].get(source_id)
    if not source:
        raise KeyError("SOURCE_NOT_FOUND")

    pages = [p for p in m["pages"].values() if p.get("logical_source_code") == source_id]
    pages.sort(key=lambda p: int(p.get("page_index") or 0))
    if not pages:
        return {
            "source": source,
            "viewer_ready": False,
            "viewer_reason": "PAGE_REGISTRY_NOT_READY",
            "page": None,
            "regions": [],
            "tasks_by_region": {},
        }

    page = pages[0]
    if page.get("readiness_state") != "READY":
        return {
            "source": source,
            "viewer_ready": False,
            "viewer_reason": "PAGE_REGISTRY_NOT_READY",
            "page": page,
            "regions": [],
            "tasks_by_region": {},
        }

    regions = [
        r for r in m["regions"].values()
        if r.get("page_id") == page.get("page_id") and r.get("readiness_state") == "READY"
    ]
    regions.sort(key=lambda r: (float(r.get("y") or 0), r.get("evidence_region_id") or ""))

    tasks_by_region: dict[str, list[dict]] = {}
    for task_id, binding in m["bindings"].items():
        region_id = binding.get("evidence_region_id")
        task = m["tasks"].get(task_id)
        if task and region_id:
            tasks_by_region.setdefault(region_id, []).append(task)

    return {
        "source": source,
        "viewer_ready": True,
        "viewer_reason": "READY",
        "page": page,
        "regions": regions,
        "tasks_by_region": tasks_by_region,
    }


def render_full_page(source_id: str, dpi: int = DEFAULT_DPI) -> tuple[bytes, dict]:
    import fitz

    if dpi not in ALLOWED_DPI:
        raise ValueError("UNSUPPORTED_DRAWING_DPI")

    ctx = drawing_context(source_id)
    if not ctx["viewer_ready"]:
        raise ValueError(ctx["viewer_reason"])

    page_record = ctx["page"]
    payload, source = source_workspace.fetch_verified_source(source_id)
    page_index = int(page_record["page_index"])

    with fitz.open(stream=payload, filetype="pdf") as doc:
        if page_index < 0 or page_index >= doc.page_count:
            raise ValueError("PAGE_INDEX_OUT_OF_RANGE")
        page = doc.load_page(page_index)
        expected_w = float(page_record["source_width"])
        expected_h = float(page_record["source_height"])
        if abs(page.rect.width - expected_w) > DIMENSION_TOLERANCE_PT or abs(page.rect.height - expected_h) > DIMENSION_TOLERANCE_PT:
            raise ValueError("PAGE_DIMENSION_MISMATCH")
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        png = pix.tobytes("png")

    return png, {
        **ctx,
        "dpi": dpi,
        "verified_sha256": source["sha256"],
        "derived_authority": "READING_AID_ONLY",
        "canonical_write_authorized": False,
    }


def _overlay_svg(region: dict, page: dict, tasks: list[dict]) -> str:
    if region.get("coordinate_space") != "NORMALIZED_0_1":
        raise ValueError("UNSUPPORTED_REGION_COORDINATE_SPACE")
    w = float(page["source_width"])
    h = float(page["source_height"])
    x = float(region["x"]) * w
    y = float(region["y"]) * h
    rw = float(region["width"]) * w
    rh = float(region["height"]) * h
    label = region.get("reference_item") or region.get("evidence_region_id")
    task = tasks[0] if tasks else None
    rect = (
        f"<rect class='evidence-overlay' x='{x:.6f}' y='{y:.6f}' width='{rw:.6f}' height='{rh:.6f}' "
        f"data-region='{esc(region.get('evidence_region_id'))}'><title>{esc(label)}</title></rect>"
    )
    if task:
        return f"<a href='/evidence/review?task={quote(task['task_id'])}'>{rect}</a>"
    return rect


def build_viewer(source_id: str) -> str:
    ctx = drawing_context(source_id)
    source = ctx["source"]
    if not ctx["viewer_ready"]:
        return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — {esc(source_id)}</title>
<style>body{{font-family:system-ui;margin:0;background:#f4f6f8;color:#17202a}}main{{max-width:900px;margin:48px auto;background:white;padding:28px;border:1px solid #d8dde3;border-radius:12px}}a{{color:#173f5f;font-weight:700}}.notice{{border-left:5px solid #8a4b08;padding:14px;background:#fff7e8}}</style></head><body><main><a href="/drawings">← Tavole</a><h1>{esc(source_id)}</h1><div class="notice"><b>Viewer non ancora governato.</b> La fonte primaria esiste, ma la Page non è ancora READY nel registro CEW. Il sistema non inventa dimensioni o trasformazioni per rendere disponibile il viewer.</div><p><a href="/api/source/pdf/{esc(source_id)}" target="_blank" rel="noopener">Apri il PDF originale verificato</a></p><p><a href="/sources/{esc(source_id)}">Vedi provenienza e identità tecnica</a></p></main></body></html>'''

    page = ctx["page"]
    width = float(page["source_width"])
    height = float(page["source_height"])
    overlays = "".join(
        _overlay_svg(region, page, ctx["tasks_by_region"].get(region["evidence_region_id"], []))
        for region in ctx["regions"]
    )

    evidence_rows = []
    for region in ctx["regions"]:
        tasks = ctx["tasks_by_region"].get(region["evidence_region_id"], [])
        action = ""
        if tasks:
            action = f"<a href='/evidence/review?task={quote(tasks[0]['task_id'])}'>Apri evidenza</a>"
        evidence_rows.append(
            f"<li><b>{esc(region.get('reference_item'))}</b><span>{esc(region.get('readiness_state'))}</span>{action}</li>"
        )

    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Viewer {esc(source_id)}</title>
<style>
:root{{--ink:#17202a;--muted:#65717e;--line:#d8dde3;--paper:#fff;--bg:#eef1f4;--accent:#173f5f;--overlay:#d33}}
*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}}a{{color:var(--accent)}}header{{background:#fff;border-bottom:1px solid var(--line)}}.top{{max-width:1500px;margin:auto;padding:14px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}}.title{{min-width:220px;flex:1}}.brand{{font-size:11px;font-weight:850;letter-spacing:.08em;color:var(--accent)}}h1{{font-size:22px;margin:3px 0}}.muted{{color:var(--muted);font-size:13px}}.toolbar{{display:flex;gap:6px;flex-wrap:wrap}}button,.button{{border:1px solid #bbc6cf;background:#fff;color:var(--ink);border-radius:7px;padding:8px 10px;font-weight:750;cursor:pointer;text-decoration:none}}button.primary,.button.primary{{background:var(--accent);color:#fff;border-color:var(--accent)}}main{{max-width:1500px;margin:auto;padding:14px 20px 28px;display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:12px}}#viewport{{height:calc(100vh - 150px);min-height:520px;background:#2d3238;border-radius:10px;overflow:hidden;touch-action:none;position:relative}}#drawingSvg{{width:100%;height:100%;display:block;cursor:grab}}#drawingSvg.dragging{{cursor:grabbing}}#pageGroup image{{image-rendering:auto}}.evidence-overlay{{fill:rgba(255,40,40,.08);stroke:var(--overlay);stroke-width:6;vector-effect:non-scaling-stroke;pointer-events:all}}.evidence-overlay:hover{{fill:rgba(255,40,40,.20);stroke-width:10}}aside{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto;max-height:calc(100vh - 150px)}}aside h2{{font-size:16px;margin:4px 0 10px}}ul{{list-style:none;padding:0;margin:0}}li{{border-top:1px solid #edf0f2;padding:9px 0;display:grid;gap:3px}}li span{{font-size:12px;color:var(--muted)}}.state{{margin-left:auto;font-size:12px;padding:5px 8px;background:#eef3f7;border-radius:999px}}.notice{{font-size:12px;color:var(--muted);border-top:1px solid #edf0f2;margin-top:12px;padding-top:12px}}
@media(max-width:900px){{main{{grid-template-columns:1fr}}aside{{max-height:none}}#viewport{{height:68vh}}}}
</style></head><body>
<header><div class="top"><a href="/drawings">← Tavole</a><div class="title"><div class="brand">CEW · DRAWING VIEWER B1.2 PREPARATION</div><h1>{esc(source_id)}</h1><div class="muted">{esc(source.get('classe','').replace('_',' '))} · {esc(source.get('livello_uso','').replace('_',' '))} · Page READY</div></div><div class="toolbar"><button onclick="fitPage()">Adatta pagina</button><button onclick="fitWidth()">Adatta larghezza</button><button onclick="zoomBy(1.25)">＋ Zoom</button><button onclick="zoomBy(0.8)">− Zoom</button><button onclick="rotateBy(-90)">↶ 90°</button><button onclick="rotateBy(90)">↷ 90°</button><button onclick="resetOrientation()">Reset orientamento</button><button onclick="toggleOverlays()">Evidenze</button><a class="button primary" href="/api/source/pdf/{esc(source_id)}" target="_blank" rel="noopener">PDF verificato</a></div><span id="viewerState" class="state">Viewer 0° · sola visualizzazione</span></div></header>
<main><section id="viewport"><svg id="drawingSvg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.6f} {height:.6f}" preserveAspectRatio="xMidYMid meet"><g id="pageGroup"><image href="/api/drawing/render/{esc(source_id)}?dpi={DEFAULT_DPI}" x="0" y="0" width="{width:.6f}" height="{height:.6f}" />{overlays}</g></svg></section><aside><h2>Evidenze sulla tavola</h2><ul>{''.join(evidence_rows) if evidence_rows else '<li>Nessuna EvidenceRegion READY su questa Page.</li>'}</ul><div class="notice"><b>Autorità:</b> rotazione, zoom e pan sono stato del viewer. Non modificano SourceVersion, Page, PageTransform o EvidenceRegion. L’immagine renderizzata è un ausilio di lettura; il PDF verificato resta la fonte primaria.</div><p><a href="/sources/{esc(source_id)}">Provenienza tecnica</a></p></aside></main>
<script>
const svg=document.getElementById('drawingSvg');const group=document.getElementById('pageGroup');const viewport=document.getElementById('viewport');const stateEl=document.getElementById('viewerState');
const W={width:.6f},H={height:.6f};let rotation=0;let overlays=true;let vb={{x:0,y:0,w:W,h:H}};let drag=null;
function dims(){{return (rotation===90||rotation===270)?[H,W]:[W,H];}}
function groupTransform(){{if(rotation===0)return '';if(rotation===90)return `translate(${{H}} 0) rotate(90)`;if(rotation===180)return `translate(${{W}} ${{H}}) rotate(180)`;return `translate(0 ${{W}}) rotate(270)`;}}
function apply(){{group.setAttribute('transform',groupTransform());svg.setAttribute('viewBox',`${{vb.x}} ${{vb.y}} ${{vb.w}} ${{vb.h}}`);stateEl.textContent=`Viewer ${{rotation}}° · sola visualizzazione`;}}
function fitPage(){{const [rw,rh]=dims();vb={{x:0,y:0,w:rw,h:rh}};apply();}}
function fitWidth(){{const [rw,rh]=dims();const ar=Math.max(.1,viewport.clientHeight/Math.max(1,viewport.clientWidth));const targetH=rw*ar;if(targetH>=rh){{fitPage();return;}}vb={{x:0,y:(rh-targetH)/2,w:rw,h:targetH}};apply();}}
function zoomBy(factor){{const [rw,rh]=dims();const cx=vb.x+vb.w/2,cy=vb.y+vb.h/2;let nw=vb.w/factor,nh=vb.h/factor;const minW=rw/24,minH=rh/24;const maxW=rw*2,maxH=rh*2;nw=Math.min(maxW,Math.max(minW,nw));nh=Math.min(maxH,Math.max(minH,nh));vb={{x:cx-nw/2,y:cy-nh/2,w:nw,h:nh}};apply();}}
function rotateBy(delta){{rotation=(rotation+delta+360)%360;fitPage();}}
function resetOrientation(){{rotation=0;fitPage();}}
function toggleOverlays(){{overlays=!overlays;document.querySelectorAll('.evidence-overlay').forEach(el=>el.style.display=overlays?'':'none');}}
svg.addEventListener('pointerdown',e=>{{drag={{x:e.clientX,y:e.clientY,vx:vb.x,vy:vb.y}};svg.setPointerCapture(e.pointerId);svg.classList.add('dragging');}});
svg.addEventListener('pointermove',e=>{{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;vb.x=drag.vx-dx*(vb.w/Math.max(1,svg.clientWidth));vb.y=drag.vy-dy*(vb.h/Math.max(1,svg.clientHeight));apply();}});
svg.addEventListener('pointerup',e=>{{drag=null;svg.classList.remove('dragging');try{{svg.releasePointerCapture(e.pointerId)}}catch(_e){{}}}});
svg.addEventListener('wheel',e=>{{e.preventDefault();zoomBy(e.deltaY<0?1.12:0.89)}},{{passive:false}});
fitPage();
</script></body></html>'''
