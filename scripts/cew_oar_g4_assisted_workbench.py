#!/usr/bin/env python3
"""Assisted mobile-first localization surface for the G4 OAR pilot.

This router is intentionally additive. The existing freehand localization page
remains available as a fallback, while this surface uses self-hosted mature UI
components plus a build-derived snap index. All persistence continues through
the existing governed OAR receipt endpoint.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

import cew_oar_g4_region_binding as binding
import cew_oar_g4_region_workbench as oar

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "artifacts" / "cew_oar_g4_assisted"
MANIFEST = ASSET_ROOT / "manifest.json"
SNAP_JSON = ASSET_ROOT / "snap_candidates.json"
DZI_ROOT = ASSET_ROOT / "deepzoom"
VENDOR_ROOT = ASSET_ROOT / "vendor"
PILOT = ROOT / "automation" / "CEW_OAR_G4_COLUMN_PILOT_INPUT_v1.json"
IMAGE_WIDTH = 7016
IMAGE_HEIGHT = 12530
VENDOR_ALLOWLIST = {
    "openseadragon-6.1.0.min.js": "application/javascript",
    "annotorious-openseadragon-3.8.10.js": "application/javascript",
    "annotorious-openseadragon-3.8.10.css": "text/css",
}


def _json(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    body = dict(payload)
    body.setdefault("canonical_write_authorized", False)
    body.setdefault("structural_identity_authorized", False)
    body.setdefault("engineering_authority_effect", "NONE")
    return JSONResponse(body, status_code=status_code, headers={"Cache-Control": "no-store"})


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"OAR_ASSISTED_ASSET_MISSING:{path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest() -> dict[str, Any]:
    data = _load_json(MANIFEST)
    if data.get("schema") != "CEW_OAR_G4_ASSISTED_ASSET_MANIFEST_v1":
        raise ValueError("OAR_ASSISTED_MANIFEST_SCHEMA_INVALID")
    if data.get("derived_asset_sha256") != oar.REGISTERED_RENDER_SHA256:
        raise ValueError("OAR_ASSISTED_MANIFEST_RENDER_SHA_MISMATCH")
    authority = data.get("authority", {})
    if authority.get("canonical_write_authorized") is not False:
        raise ValueError("OAR_ASSISTED_MANIFEST_AUTHORITY_DRIFT")
    return data


def _families() -> dict[str, dict[str, Any]]:
    return _load_json(PILOT)["families"]


def _support_family(support_id: str) -> str:
    contract = binding.load_contract()
    return binding.support_row(contract, support_id)["family_id"]


def _snap_payload() -> dict[str, Any]:
    data = _load_json(SNAP_JSON)
    if data.get("schema") != "CEW_OAR_G4_SNAP_CANDIDATES_v1":
        raise ValueError("OAR_ASSISTED_SNAP_SCHEMA_INVALID")
    if data.get("source_dimensions_px") != [IMAGE_WIDTH, IMAGE_HEIGHT]:
        raise ValueError("OAR_ASSISTED_SNAP_DIMENSIONS_INVALID")
    if data.get("authority", {}).get("snap_candidates_are_authority") is not False:
        raise ValueError("OAR_ASSISTED_SNAP_AUTHORITY_DRIFT")
    return data


def _rank_snap(support_id: str, x: float, y: float, radius: float = 0.055) -> dict[str, Any]:
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
        raise ValueError("OAR_ASSISTED_SNAP_TAP_OUT_OF_RANGE")
    radius = max(0.005, min(0.12, float(radius)))
    family_id = _support_family(support_id)
    family = _families()[family_id]
    target_ratio = float(family["section_x_cm"]) / float(family["section_y_cm"])
    candidates = _snap_payload()["candidates"]
    ranked: list[dict[str, Any]] = []
    for row in candidates:
        center = row["center"]
        distance = math.hypot(float(center["x"]) - x, float(center["y"]) - y)
        if distance > radius:
            continue
        actual_ratio = max(1e-9, float(row["aspect_ratio"]))
        ratio_error = abs(math.log(actual_ratio / target_ratio))
        distance_score = max(0.0, 1.0 - distance / radius)
        ratio_score = math.exp(-ratio_error)
        build_quality = max(0.0, min(1.0, float(row.get("build_quality", 0.0))))
        score = 0.65 * distance_score + 0.25 * ratio_score + 0.10 * build_quality
        ranked.append({
            "candidate_id": row["candidate_id"],
            "bbox": row["bbox"],
            "center": row["center"],
            "score": round(score, 6),
            "tap_distance": round(distance, 7),
            "family_id": family_id,
            "target_aspect_ratio": round(target_ratio, 6),
            "candidate_aspect_ratio": round(actual_ratio, 6),
            "ratio_compatibility": round(ratio_score, 6),
            "rectangularity": round(float(row.get("rectangularity", 0.0)), 6),
        })
    ranked.sort(key=lambda row: (-row["score"], row["tap_distance"], row["candidate_id"]))
    return {
        "state": "SNAP_PROPOSALS_READY" if ranked else "NO_SNAP_CANDIDATE_IN_APERTURE",
        "support_id": str(support_id),
        "family_id": family_id,
        "tap": {"x": x, "y": y},
        "aperture_radius_normalized": radius,
        "candidates": ranked[:8],
        "snap_is_proposal_only": True,
        "oar_classification_confirmed": False,
        "canonical_write_authorized": False,
        "structural_identity_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def _safe_asset(root: Path, relative: str, suffixes: set[str]) -> Path:
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("OAR_ASSISTED_ASSET_PATH_ESCAPE") from exc
    if target.suffix.lower() not in suffixes or not target.is_file():
        raise ValueError("OAR_ASSISTED_ASSET_NOT_FOUND")
    return target


def _page() -> str:
    return r'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>CEW — Localizzazione assistita G4</title>
<link rel="stylesheet" href="/workbench/oar/g4-assisted/vendor/annotorious-openseadragon-3.8.10.css">
<style>
:root{--bg:#edf1f4;--panel:#fff;--ink:#17202a;--muted:#64717d;--line:#cbd3db;--accent:#173f5f;--ok:#1e6b45;--warn:#8a5a00}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,sans-serif}header{display:flex;align-items:center;gap:12px;padding:10px 12px;background:#fff;border-bottom:1px solid var(--line)}header h1{font-size:16px;margin:0}header small{color:var(--muted)}header a{margin-left:auto;color:var(--accent)}main{display:grid;grid-template-columns:250px minmax(0,1fr) 285px;height:calc(100vh - 55px)}aside{background:#fff;padding:12px;overflow:auto}.left{border-right:1px solid var(--line)}.right{border-left:1px solid var(--line)}h2{font-size:14px;margin:0 0 8px}.supports{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}.support{border:1px solid var(--line);border-radius:6px;background:#fff;padding:6px 3px;font-weight:700}.support span{display:block;font-size:8px;color:var(--muted);font-weight:400;overflow:hidden}.support.active{outline:2px solid var(--accent)}.support.proposed{border-color:var(--warn)}.support.confirmed{border-color:var(--ok)}
.viewer-wrap{min-width:0;position:relative;background:#d9dee3}.toolbar{position:absolute;z-index:30;top:8px;left:8px;display:flex;gap:5px;flex-wrap:wrap;max-width:calc(100% - 16px)}.tool{border:1px solid #aeb7c0;border-radius:6px;background:#fff;padding:8px 10px;font-weight:700;box-shadow:0 1px 4px #0002}.tool.active{background:var(--accent);color:#fff}#viewer{width:100%;height:100%}.field{margin:8px 0;font-size:13px}.field b{display:block}.action{width:100%;padding:10px;margin-top:7px;border:0;border-radius:7px;font-weight:700}.primary{background:var(--accent);color:#fff}.confirm{background:var(--ok);color:#fff}.secondary{background:#e9edf1;color:var(--ink)}button:disabled{opacity:.4}.notice{font-size:12px;line-height:1.4;color:var(--muted)}#message{min-height:68px;padding:8px;background:#f4f6f8;border-radius:6px;font-size:12px;white-space:pre-wrap}.snap-list{display:flex;gap:4px;flex-wrap:wrap}.snap-choice{font-size:11px;padding:5px 7px}.progress{font-size:12px;color:var(--muted);margin-bottom:8px}
@media(max-width:900px){header small{display:none}main{display:flex;flex-direction:column;height:auto}.left{order:1;border:0}.viewer-wrap{order:2;height:64vh;min-height:430px}.right{order:3;border:0}.supports{grid-template-columns:repeat(6,1fr)}aside{overflow:visible}.toolbar{position:absolute}.tool{padding:9px}.right{padding-bottom:30px}}
</style></head><body>
<header><div><h1>Localizzazione assistita — Pilastri G4</h1><small>TAV-05S · Deep Zoom · Snap proposal · Human confirmation</small></div><a href="/workbench/oar/g4-regions">Fallback</a></header>
<main><aside class="left"><h2>Supporti</h2><div id="progress" class="progress">Caricamento…</div><div id="supports" class="supports"></div><p class="notice">1. Seleziona un supporto. 2. Naviga/zoom. 3. Premi <b>Snap</b> e tocca vicino al simbolo. 4. Sposta o ridimensiona il box se necessario. 5. Registra e poi conferma.</p></aside>
<section class="viewer-wrap"><div class="toolbar"><button class="tool" id="home">Adatta</button><button class="tool" id="zin">＋</button><button class="tool" id="zout">−</button><button class="tool" id="rot">↻ 90°</button><button class="tool" id="pan">Pan</button><button class="tool" id="edit">Modifica box</button><button class="tool" id="snap">Snap</button></div><div id="viewer"></div></section>
<aside class="right"><h2>Decisione</h2><div class="field"><b>Supporto</b><span id="selected">—</span></div><div class="field"><b>Famiglia candidata</b><span id="family">—</span></div><div class="field"><b>Stato</b><span id="state">UNBOUND</span></div><div class="field"><b>Rettangolo</b><code id="bbox">—</code></div><div class="field"><b>Snap</b><span id="snapinfo">—</span><div id="snapchoices" class="snap-list"></div></div><button class="action primary" id="propose" disabled>Registra proposta geometrica</button><button class="action confirm" id="confirm" disabled>Conferma localizzazione</button><button class="action secondary" id="clear" disabled>Scarta proposta visuale</button><p class="notice"><b>Lo snap non conferma nulla.</b> Famiglia OAR, EvidenceRegion canonica e identità strutturale restano gate separati.</p><div id="message"></div></aside></main>
<script src="/workbench/oar/g4-assisted/vendor/openseadragon-6.1.0.min.js"></script>
<script src="/workbench/oar/g4-assisted/vendor/annotorious-openseadragon-3.8.10.js"></script>
<script>
const W=7016,H=12530;let report=null,selected=null,draft=null,draftDirty=false,snapMode=false,snapCandidates=[],snapIndex=0,anno=null;
const el=id=>document.getElementById(id), message=el('message');
const viewer=OpenSeadragon({id:'viewer',tileSources:'/workbench/oar/g4-assisted/deepzoom/TAV05S_OAR_300dpi.dzi',showNavigationControl:false,showNavigator:true,navigatorSizeRatio:0.16,animationTime:0.25,blendTime:0.1,gestureSettingsTouch:{pinchToZoom:true,flickEnabled:true,clickToZoom:false,dblClickToZoom:true}});
viewer.addHandler('open',()=>{anno=AnnotoriousOSD.createOSDAnnotator(viewer,{drawingEnabled:false,autoSave:true,style:{fill:'#173f5f',fillOpacity:0.14,stroke:'#173f5f',strokeWidth:2}});anno.on('updateAnnotation',a=>{draft=bboxFromAnnotation(a);draftDirty=true;syncDecision();message.textContent='Box modificato: registra di nuovo la proposta prima della conferma.'});refreshSelection()});
function row(){return report?.objects.find(o=>String(o.support_id)===String(selected))}
function clean(v){return String(v).replace(/[^A-Za-z0-9._-]+/g,'_')}
function decision(action){return `oar-g4-assisted-${clean(selected)}-${action.toLowerCase()}-${Date.now()}`}
function bboxFromAnnotation(a){const g=a.target.selector.geometry;return{x:g.x/W,y:g.y/H,w:g.w/W,h:g.h/H}}
function annotationFromBBox(b){const x=b.x*W,y=b.y*H,w=b.w*W,h=b.h*H,id=`cew-g4-${clean(selected)}`;return{id,target:{selector:{type:'RECTANGLE',geometry:{x,y,w,h,bounds:{minX:x,minY:y,maxX:x+w,maxY:y+h}}}}}}
function showBBox(b,editable=true,fit=false){draft=b;draftDirty=false;if(!anno)return;anno.clearAnnotations();if(!b){syncDecision();return}const a=annotationFromBBox(b);anno.addAnnotation(a);anno.setSelected(a.id,editable);if(fit)anno.fitBounds(a.id,{padding:90});syncDecision()}
function syncDecision(){const r=row();el('selected').textContent=selected??'—';el('family').textContent=r?.family_id??'—';el('state').textContent=r?.state??'UNBOUND';el('bbox').textContent=draft?JSON.stringify(draft):'—';const frozen=r?.state==='GEOMETRY_CONFIRMED';el('propose').disabled=!selected||!draft||frozen;el('confirm').disabled=!(r?.state==='PROPOSED'&&draft&&!draftDirty);el('clear').disabled=!draft||frozen;el('edit').disabled=!draft||frozen;el('snap').disabled=!selected||frozen}
function refreshSelection(){if(!report)return;const r=row();document.querySelectorAll('.support').forEach(b=>{const rr=report.objects.find(o=>String(o.support_id)===b.dataset.support);b.classList.toggle('active',b.dataset.support===String(selected));b.classList.toggle('proposed',rr?.state==='PROPOSED');b.classList.toggle('confirmed',rr?.state==='GEOMETRY_CONFIRMED')});snapCandidates=[];snapIndex=0;el('snapchoices').innerHTML='';el('snapinfo').textContent='—';if(!r){showBBox(null);return}showBBox(r.bbox??null,r.state!=='GEOMETRY_CONFIRMED',Boolean(r.bbox));}
async function loadStatus(){const res=await fetch('/api/workbench/oar/g4-regions/status',{cache:'no-store'});const body=await res.json();if(!res.ok)throw new Error(body.state||'OAR_STATUS_UNAVAILABLE');report=body;renderSupports();refreshSelection()}
function renderSupports(){const host=el('supports');host.innerHTML='';for(const r of report.objects){const b=document.createElement('button');b.className='support';b.dataset.support=String(r.support_id);b.innerHTML=`${r.support_id}<span>${r.family_id.replace('COL-G4-','')}</span>`;b.onclick=()=>{selected=String(r.support_id);refreshSelection()};host.appendChild(b)}const s=report.summary;el('progress').textContent=`${s.GEOMETRY_CONFIRMED}/34 confermati · ${s.PROPOSED} proposti · ${s.UNBOUND} da localizzare`}
function currentTap(event){const item=viewer.world.getItemAt(0),vp=viewer.viewport.pointFromPixel(event.position),ip=item.viewportToImageCoordinates(vp);return{x:Math.max(0,Math.min(1,ip.x/W)),y:Math.max(0,Math.min(1,ip.y/H))}}
viewer.addHandler('canvas-click',async event=>{if(!snapMode||!selected||!event.quick)return;event.preventDefaultAction=true;snapMode=false;el('snap').classList.remove('active');const p=currentTap(event);message.textContent='Ricerca snap…';const res=await fetch(`/api/workbench/oar/g4-assisted/snap?support_id=${encodeURIComponent(selected)}&x=${p.x}&y=${p.y}`,{cache:'no-store'});const body=await res.json();if(!res.ok){message.textContent=body.state||'OAR_ASSISTED_SNAP_REJECTED';return}snapCandidates=body.candidates||[];snapIndex=0;if(!snapCandidates.length){el('snapinfo').textContent='Nessun candidato vicino';message.textContent='Nessun contorno compatibile nell’apertura. Zooma e tocca più vicino oppure usa il fallback.';return}renderSnap(0);renderSnapChoices();message.textContent='Snap proposto. Controlla, sposta/ridimensiona se necessario, poi registra.'});
function renderSnap(i){snapIndex=i;const c=snapCandidates[i];showBBox(c.bbox,true,true);draftDirty=true;el('snapinfo').textContent=`${c.candidate_id} · score ${Math.round(c.score*100)}% · ratio ${Math.round(c.ratio_compatibility*100)}%`}
function renderSnapChoices(){const host=el('snapchoices');host.innerHTML='';snapCandidates.slice(0,5).forEach((c,i)=>{const b=document.createElement('button');b.className='snap-choice';b.textContent=`${i+1} · ${Math.round(c.score*100)}%`;b.onclick=()=>renderSnap(i);host.appendChild(b)})}
el('home').onclick=()=>viewer.viewport.goHome();el('zin').onclick=()=>viewer.viewport.zoomBy(1.6);el('zout').onclick=()=>viewer.viewport.zoomBy(0.625);el('rot').onclick=()=>viewer.viewport.setRotation((viewer.viewport.getRotation()+90)%360);el('pan').onclick=()=>{if(anno)anno.setSelected();message.textContent='Pan attivo: trascina la tavola. Il box resta visibile.'};el('edit').onclick=()=>{if(anno&&draft&&selected)anno.setSelected(`cew-g4-${clean(selected)}`,true)};el('snap').onclick=()=>{if(!selected)return;snapMode=!snapMode;el('snap').classList.toggle('active',snapMode);message.textContent=snapMode?'Tocca vicino al pilastro: il sistema cercherà i contorni compatibili.':'Snap annullato.'};el('clear').onclick=()=>{showBBox(row()?.bbox??null,row()?.state!=='GEOMETRY_CONFIRMED');message.textContent='Proposta visuale scartata; stato persistito invariato.'};
async function postAction(action){if(!selected||!draft)return;const payload={decision_id:decision(action),support_id:selected,action,bbox:draft};message.textContent='Registrazione…';const res=await fetch('/api/workbench/oar/g4-regions/receipt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const body=await res.json();if(!res.ok){message.textContent=body.state||'OAR_REGION_RECEIPT_REJECTED';return}message.textContent=`${body.object_state} · receipt ${body.runtime_receipt_id}`;await loadStatus()}
el('propose').onclick=()=>postAction('PROPOSE_GEOMETRY');el('confirm').onclick=()=>postAction('CONFIRM_GEOMETRY');
loadStatus().catch(()=>message.textContent='OAR_STATUS_UNAVAILABLE');
</script></body></html>'''


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/oar/g4-assisted", response_class=HTMLResponse)
    def assisted_page():
        try:
            _manifest()
            _snap_payload()
        except ValueError:
            return HTMLResponse("CEW OAR assisted surface unavailable", status_code=503)
        return HTMLResponse(
            _page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-OAR-Assisted": "POC_NON_PROMOTING",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Structural-Identity": "false",
            },
        )

    @router.get("/workbench/oar/g4-assisted/vendor/{filename}")
    def vendor_asset(filename: str):
        media = VENDOR_ALLOWLIST.get(filename)
        if media is None:
            return _json({"state": "OAR_ASSISTED_VENDOR_NOT_ALLOWED"}, 404)
        try:
            target = _safe_asset(VENDOR_ROOT, filename, {".js", ".css"})
        except ValueError:
            return _json({"state": "OAR_ASSISTED_VENDOR_UNAVAILABLE"}, 404)
        return FileResponse(target, media_type=media, headers={"Cache-Control": "private, max-age=86400"})

    @router.get("/workbench/oar/g4-assisted/deepzoom/{asset_path:path}")
    def deepzoom_asset(asset_path: str):
        try:
            target = _safe_asset(DZI_ROOT, asset_path, {".dzi", ".jpg"})
        except ValueError:
            return _json({"state": "OAR_ASSISTED_DEEPZOOM_UNAVAILABLE"}, 404)
        media = "application/xml" if target.suffix.lower() == ".dzi" else "image/jpeg"
        return FileResponse(target, media_type=media, headers={"Cache-Control": "private, max-age=86400"})

    @router.get("/api/workbench/oar/g4-assisted/status")
    def assisted_status():
        try:
            manifest = _manifest()
            report = oar.load_report()
        except ValueError:
            return _json({"state": "OAR_ASSISTED_STATUS_BLOCKED"}, 503)
        return _json({
            "state": "READY_FOR_ASSISTED_LOCALIZATION",
            "build": manifest,
            "oar_summary": report["summary"],
            "fallback_surface": "/workbench/oar/g4-regions",
            "assisted_surface": "/workbench/oar/g4-assisted",
            "snap_auto_confirms": False,
            "oar_classification_confirmed": False,
        })

    @router.get("/api/workbench/oar/g4-assisted/snap")
    def snap(support_id: str, x: float, y: float, radius: float = 0.055):
        try:
            binding.support_row(binding.load_contract(), support_id)
            result = _rank_snap(support_id, float(x), float(y), float(radius))
        except (ValueError, KeyError):
            return _json({"state": "OAR_ASSISTED_SNAP_REJECTED"}, 422)
        return _json(result)

    return router
