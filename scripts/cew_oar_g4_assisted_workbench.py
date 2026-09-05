#!/usr/bin/env python3
"""Mobile-first human object workbench for the G4 OAR pilot.

The primary interaction is prototype-led: the operator teaches one correct
project-local example and asks CEW to search the page for similar occurrences.
Deep Zoom and editable rectangles remain the human review surface. Local contour
snap is retained only as a fallback aid. No path here grants OAR classification,
canonical EvidenceRegion, CAD, structural identity, or engineering authority.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

import cew_oar_g4_prototype_search as prototype_search
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
    """Legacy local snap retained as a fallback box aid, never primary search."""
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
        envelope_bonus = 1.0 if row.get("detector") == "LONG_AXIS_SUPPRESSED" else 0.55
        score = 0.50 * distance_score + 0.25 * ratio_score + 0.15 * build_quality + 0.10 * envelope_bonus
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
            "detector": row.get("detector"),
        })
    ranked.sort(key=lambda row: (-row["score"], row["tap_distance"], row["candidate_id"]))
    return {
        "state": "SNAP_PROPOSALS_READY" if ranked else "NO_SNAP_CANDIDATE_IN_APERTURE",
        "support_id": str(support_id),
        "family_id": family_id,
        "tap": {"x": x, "y": y},
        "aperture_radius_normalized": radius,
        "candidates": ranked[:8],
        "snap_role": "FALLBACK_LOCAL_BOX_AID",
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
<title>CEW — Object Workbench G4</title>
<link rel="stylesheet" href="/workbench/oar/g4-assisted/vendor/annotorious-openseadragon-3.8.10.css">
<style>
:root{--bg:#edf1f4;--panel:#fff;--ink:#17202a;--muted:#64717d;--line:#cbd3db;--accent:#173f5f;--ok:#1e6b45;--warn:#8a5a00;--proto:#5b3f91}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,sans-serif}header{display:flex;align-items:center;gap:12px;padding:10px 12px;background:#fff;border-bottom:1px solid var(--line)}header h1{font-size:16px;margin:0}header small{color:var(--muted)}header a{margin-left:auto;color:var(--accent)}main{display:grid;grid-template-columns:250px minmax(0,1fr) 310px;height:calc(100vh - 55px)}aside{background:#fff;padding:12px;overflow:auto}.left{border-right:1px solid var(--line)}.right{border-left:1px solid var(--line)}h2{font-size:14px;margin:0 0 8px}.supports{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}.support{border:1px solid var(--line);border-radius:6px;background:#fff;padding:6px 3px;font-weight:700}.support span{display:block;font-size:8px;color:var(--muted);font-weight:400;overflow:hidden}.support.active{outline:2px solid var(--accent)}.support.proposed{border-color:var(--warn)}.support.confirmed{border-color:var(--ok)}
.viewer-wrap{min-width:0;position:relative;background:#d9dee3}.toolbar{position:absolute;z-index:30;top:8px;left:8px;display:flex;gap:5px;flex-wrap:wrap;max-width:calc(100% - 16px)}.tool{border:1px solid #aeb7c0;border-radius:6px;background:#fff;padding:8px 10px;font-weight:700;box-shadow:0 1px 4px #0002}.tool.active{background:var(--accent);color:#fff}#viewer{width:100%;height:100%}.field{margin:8px 0;font-size:13px}.field b{display:block}.action{width:100%;padding:10px;margin-top:7px;border:0;border-radius:7px;font-weight:700}.primary{background:var(--accent);color:#fff}.prototype{background:var(--proto);color:#fff}.confirm{background:var(--ok);color:#fff}.secondary{background:#e9edf1;color:var(--ink)}button:disabled{opacity:.4}.notice{font-size:12px;line-height:1.4;color:var(--muted)}#message{min-height:68px;padding:8px;background:#f4f6f8;border-radius:6px;font-size:12px;white-space:pre-wrap}.choice-list{display:flex;gap:4px;flex-wrap:wrap}.choice{font-size:11px;padding:5px 7px}.progress{font-size:12px;color:var(--muted);margin-bottom:8px}.section-rule{border:0;border-top:1px solid var(--line);margin:12px 0}
@media(max-width:900px){header small{display:none}main{display:flex;flex-direction:column;height:auto}.left{order:1;border:0}.viewer-wrap{order:2;height:64vh;min-height:430px}.right{order:3;border:0}.supports{grid-template-columns:repeat(6,1fr)}aside{overflow:visible}.toolbar{position:absolute}.tool{padding:9px}.right{padding-bottom:30px}}
</style></head><body>
<header><div><h1>Object Workbench — Pilastri G4</h1><small>TAV-05S · Teach example · Find similar · Human review</small></div><a href="/workbench/oar/g4-regions">Fallback libero</a></header>
<main><aside class="left"><h2>Supporti</h2><div id="progress" class="progress">Caricamento…</div><div id="supports" class="supports"></div><p class="notice">Flusso principale: <b>1.</b> seleziona un supporto, <b>2.</b> disegna una volta il box corretto, <b>3.</b> Insegna esempio, <b>4.</b> Cerca simili, <b>5.</b> controlla i candidati. Snap è solo un aiuto locale di fallback.</p></aside>
<section class="viewer-wrap"><div class="toolbar"><button class="tool" id="home">Adatta</button><button class="tool" id="zin">＋</button><button class="tool" id="zout">−</button><button class="tool" id="rot">↻ 90°</button><button class="tool" id="pan">Pan</button><button class="tool" id="draw">Disegna box</button><button class="tool" id="edit">Modifica box</button><button class="tool" id="snap">Snap fallback</button></div><div id="viewer"></div></section>
<aside class="right"><h2>Oggetto</h2><div class="field"><b>Supporto</b><span id="selected">—</span></div><div class="field"><b>Famiglia candidata</b><span id="family">—</span></div><div class="field"><b>Stato geometria</b><span id="state">UNBOUND</span></div><div class="field"><b>Rettangolo di lavoro</b><code id="bbox">—</code></div>
<hr class="section-rule"><h2>Prototipo</h2><div class="field"><b>Esempio insegnato</b><span id="prototypeinfo">—</span></div><button class="action prototype" id="teach" disabled>Insegna questo esempio</button><button class="action prototype" id="findsimilar" disabled>Cerca simili nella tavola</button><div class="field"><b>Risultati simili</b><span id="similarinfo">—</span><div id="similarchoices" class="choice-list"></div></div><button class="action secondary" id="backexample" disabled>Torna all'esempio</button>
<hr class="section-rule"><h2>Localizzazione singola</h2><div class="field"><b>Snap fallback</b><span id="snapinfo">—</span><div id="snapchoices" class="choice-list"></div></div><button class="action primary" id="propose" disabled>Registra proposta geometrica</button><button class="action confirm" id="confirm" disabled>Conferma localizzazione</button><button class="action secondary" id="clear" disabled>Scarta proposta visuale</button><p class="notice"><b>Prototipo, ricerca simili e snap non confermano nulla.</b> Identità del supporto, famiglia OAR, EvidenceRegion canonica e identità strutturale restano gate separati.</p><div id="message"></div></aside></main>
<script src="/workbench/oar/g4-assisted/vendor/openseadragon-6.1.0.min.js"></script>
<script src="/workbench/oar/g4-assisted/vendor/annotorious-openseadragon-3.8.10.js"></script>
<script>
const W=7016,H=12530;let report=null,selected=null,draft=null,draftDirty=false,snapMode=false,snapCandidates=[],anno=null,drawingMode=false,prototype=null,prototypeBBox=null,similarCandidates=[],similarPreview=false;
const el=id=>document.getElementById(id), message=el('message');
const viewer=OpenSeadragon({id:'viewer',tileSources:'/workbench/oar/g4-assisted/deepzoom/TAV05S_OAR_300dpi.dzi',showNavigationControl:false,showNavigator:true,navigatorSizeRatio:0.16,animationTime:0.25,blendTime:0.1,gestureSettingsTouch:{pinchToZoom:true,flickEnabled:true,clickToZoom:false,dblClickToZoom:true}});
function invalidatePrototype(reason){prototype=null;prototypeBBox=null;similarCandidates=[];similarPreview=false;el('prototypeinfo').textContent='—';el('similarinfo').textContent='—';el('similarchoices').innerHTML='';el('backexample').disabled=true;if(reason)message.textContent=reason}
viewer.addHandler('open',()=>{anno=AnnotoriousOSD.createOSDAnnotator(viewer,{drawingEnabled:false,autoSave:true,style:{fill:'#173f5f',fillOpacity:0.14,stroke:'#173f5f',strokeWidth:2}});anno.on('updateAnnotation',a=>{if(similarPreview)return;draft=bboxFromAnnotation(a);draftDirty=true;invalidatePrototype('Box modificato: insegna di nuovo l’esempio se vuoi cercare simili.');syncDecision()});anno.on('createAnnotation',a=>{draft=bboxFromAnnotation(a);draftDirty=true;drawingMode=false;if(typeof anno.setDrawingEnabled==='function')anno.setDrawingEnabled(false);invalidatePrototype('Nuovo box creato. Controllalo e premi “Insegna questo esempio”.');syncDecision()});refreshSelection()});
function row(){return report?.objects.find(o=>String(o.support_id)===String(selected))}
function clean(v){return String(v).replace(/[^A-Za-z0-9._-]+/g,'_')}
function decision(action){return `oar-g4-assisted-${clean(selected)}-${action.toLowerCase()}-${Date.now()}`}
function bboxFromAnnotation(a){const g=a.target.selector.geometry;return{x:g.x/W,y:g.y/H,w:g.w/W,h:g.h/H}}
function annotationFromBBox(b,idSuffix='draft'){const x=b.x*W,y=b.y*H,w=b.w*W,h=b.h*H,id=`cew-g4-${clean(selected)}-${idSuffix}`;return{id,target:{selector:{type:'RECTANGLE',geometry:{x,y,w,h,bounds:{minX:x,minY:y,maxX:x+w,maxY:y+h}}}}}}
function drawAnnotation(b,editable=true,fit=false,idSuffix='draft'){if(!anno)return;anno.clearAnnotations();if(!b)return;const a=annotationFromBBox(b,idSuffix);anno.addAnnotation(a);anno.setSelected(a.id,editable);if(fit)anno.fitBounds(a.id,{padding:90})}
function showBBox(b,editable=true,fit=false){draft=b;draftDirty=false;similarPreview=false;drawAnnotation(b,editable,fit,'draft');syncDecision()}
function showPreviewBBox(b,fit=false){similarPreview=true;drawAnnotation(b,false,fit,'similar-preview');syncDecision()}
function syncDecision(){const r=row();el('selected').textContent=selected??'—';el('family').textContent=r?.family_id??'—';el('state').textContent=r?.state??'UNBOUND';el('bbox').textContent=draft?JSON.stringify(draft):'—';const frozen=r?.state==='GEOMETRY_CONFIRMED';el('propose').disabled=!selected||!draft||frozen||similarPreview;el('confirm').disabled=!(r?.state==='PROPOSED'&&draft&&!draftDirty&&!similarPreview);el('clear').disabled=!draft||frozen||similarPreview;el('edit').disabled=!draft||frozen||similarPreview;el('draw').disabled=!selected||frozen;el('snap').disabled=!selected||frozen;el('teach').disabled=!selected||!draft||frozen||similarPreview;el('findsimilar').disabled=!prototype;el('backexample').disabled=!prototypeBBox||!similarPreview}
function refreshSelection(){if(!report)return;const r=row();document.querySelectorAll('.support').forEach(b=>{const rr=report.objects.find(o=>String(o.support_id)===b.dataset.support);b.classList.toggle('active',b.dataset.support===String(selected));b.classList.toggle('proposed',rr?.state==='PROPOSED');b.classList.toggle('confirmed',rr?.state==='GEOMETRY_CONFIRMED')});snapCandidates=[];el('snapchoices').innerHTML='';el('snapinfo').textContent='—';invalidatePrototype();if(!r){showBBox(null);return}showBBox(r.bbox??null,r.state!=='GEOMETRY_CONFIRMED',Boolean(r.bbox));}
async function loadStatus(){const res=await fetch('/api/workbench/oar/g4-regions/status',{cache:'no-store'});const body=await res.json();if(!res.ok)throw new Error(body.state||'OAR_STATUS_UNAVAILABLE');report=body;renderSupports();refreshSelection()}
function renderSupports(){const host=el('supports');host.innerHTML='';for(const r of report.objects){const b=document.createElement('button');b.className='support';b.dataset.support=String(r.support_id);b.innerHTML=`${r.support_id}<span>${r.family_id.replace('COL-G4-','')}</span>`;b.onclick=()=>{selected=String(r.support_id);refreshSelection()};host.appendChild(b)}const s=report.summary;el('progress').textContent=`${s.GEOMETRY_CONFIRMED}/34 confermati · ${s.PROPOSED} proposti · ${s.UNBOUND} da localizzare`}
function currentTap(event){const item=viewer.world.getItemAt(0),vp=viewer.viewport.pointFromPixel(event.position),ip=item.viewportToImageCoordinates(vp);return{x:Math.max(0,Math.min(1,ip.x/W)),y:Math.max(0,Math.min(1,ip.y/H))}}
viewer.addHandler('canvas-click',async event=>{if(!snapMode||!selected||!event.quick)return;event.preventDefaultAction=true;snapMode=false;el('snap').classList.remove('active');const p=currentTap(event);message.textContent='Ricerca snap fallback…';const res=await fetch(`/api/workbench/oar/g4-assisted/snap?support_id=${encodeURIComponent(selected)}&x=${p.x}&y=${p.y}`,{cache:'no-store'});const body=await res.json();if(!res.ok){message.textContent=body.state||'OAR_ASSISTED_SNAP_REJECTED';return}snapCandidates=body.candidates||[];if(!snapCandidates.length){el('snapinfo').textContent='Nessun candidato vicino';message.textContent='Nessun contorno locale. Usa “Disegna box” per creare direttamente l’esempio corretto.';return}renderSnap(0);renderSnapChoices();message.textContent='Snap fallback proposto. Correggi il box se serve; per il flusso maturo premi poi “Insegna questo esempio”.'});
function renderSnap(i){const c=snapCandidates[i];showBBox(c.bbox,true,true);draftDirty=true;invalidatePrototype();el('snapinfo').textContent=`${c.candidate_id} · ${Math.round(c.score*100)}% · ${c.detector||'contour'}`;syncDecision()}
function renderSnapChoices(){const host=el('snapchoices');host.innerHTML='';snapCandidates.slice(0,5).forEach((c,i)=>{const b=document.createElement('button');b.className='choice';b.textContent=`${i+1} · ${Math.round(c.score*100)}%`;b.onclick=()=>renderSnap(i);host.appendChild(b)})}
async function teachExample(){if(!selected||!draft||similarPreview)return;const payload={decision_id:decision('teach-example'),support_id:selected,bbox:draft};message.textContent='Registro esempio di addestramento…';const res=await fetch('/api/workbench/oar/g4-assisted/teach-example',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const body=await res.json();if(!res.ok){message.textContent=body.state||'OAR_PROTOTYPE_TEACH_REJECTED';return}prototype={id:body.prototype_id,family_id:body.family_id};prototypeBBox={...draft};el('prototypeinfo').textContent=`${body.prototype_id} · ${body.family_id}`;el('similarinfo').textContent='Pronto per ricerca globale';message.textContent='Esempio insegnato. Ora “Cerca simili nella tavola”. Nessuna classificazione è stata confermata.';syncDecision()}
async function findSimilar(){if(!prototype)return;message.textContent='Ricerca globale di oggetti simili…';const res=await fetch(`/api/workbench/oar/g4-assisted/find-similar?prototype_id=${encodeURIComponent(prototype.id)}&limit=32`,{cache:'no-store'});const body=await res.json();if(!res.ok){message.textContent=body.state||'OAR_PROTOTYPE_SEARCH_REJECTED';return}similarCandidates=body.candidates||[];el('similarinfo').textContent=`${similarCandidates.length} proposte · prior gruppo ${body.expected_family_occurrence_count_prior}`;renderSimilarChoices();message.textContent=similarCandidates.length?'Candidati trovati. Tocca un numero per ispezionarlo; non viene assegnato ad alcun supporto.':'Nessun candidato sufficientemente simile.';syncDecision()}
function renderSimilarChoices(){const host=el('similarchoices');host.innerHTML='';similarCandidates.slice(0,12).forEach((c,i)=>{const b=document.createElement('button');b.className='choice';b.textContent=`${i+1} · ${Math.round(c.score*100)}%`;b.onclick=()=>{showPreviewBBox(c.bbox,true);el('similarinfo').textContent=`${i+1}/${similarCandidates.length} · ${c.occurrence_candidate_id} · score ${Math.round(c.score*100)}%`;message.textContent='Anteprima di una possibile occorrenza simile. Nessuna identità/supporto è assegnata.'};host.appendChild(b)})}
function backToExample(){if(!prototypeBBox)return;showBBox({...prototypeBBox},true,true);el('similarinfo').textContent=`${similarCandidates.length} proposte disponibili`;message.textContent='Tornato all’esempio insegnato.'}
el('home').onclick=()=>viewer.viewport.goHome();el('zin').onclick=()=>viewer.viewport.zoomBy(1.6);el('zout').onclick=()=>viewer.viewport.zoomBy(0.625);el('rot').onclick=()=>viewer.viewport.setRotation((viewer.viewport.getRotation()+90)%360);el('pan').onclick=()=>{if(anno)anno.setSelected();message.textContent='Pan attivo: trascina la tavola.'};el('draw').onclick=()=>{if(!anno||!selected)return;if(typeof anno.setDrawingTool==='function')anno.setDrawingTool('rectangle');if(typeof anno.setDrawingEnabled==='function'){anno.clearAnnotations();anno.setDrawingEnabled(true);drawingMode=true;message.textContent='Disegna un rettangolo attorno all’intero pilastro. Questo diventerà l’esempio umano.'}else message.textContent='Disegno diretto non disponibile: usa Snap fallback o il fallback libero.'};el('edit').onclick=()=>{if(anno&&draft&&selected&&!similarPreview)anno.setSelected(`cew-g4-${clean(selected)}-draft`,true)};el('snap').onclick=()=>{if(!selected)return;snapMode=!snapMode;el('snap').classList.toggle('active',snapMode);message.textContent=snapMode?'Snap fallback: tocca vicino al pilastro.':'Snap annullato.'};el('clear').onclick=()=>{invalidatePrototype();showBBox(row()?.bbox??null,row()?.state!=='GEOMETRY_CONFIRMED');message.textContent='Proposta visuale scartata; stato persistito invariato.'};el('teach').onclick=teachExample;el('findsimilar').onclick=findSimilar;el('backexample').onclick=backToExample;
async function postAction(action){if(!selected||!draft||similarPreview)return;const payload={decision_id:decision(action),support_id:selected,action,bbox:draft};message.textContent='Registrazione…';const res=await fetch('/api/workbench/oar/g4-regions/receipt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const body=await res.json();if(!res.ok){message.textContent=body.state||'OAR_REGION_RECEIPT_REJECTED';return}message.textContent=`${body.object_state} · receipt ${body.runtime_receipt_id}`;await loadStatus()}
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
                "X-CEW-OAR-Assisted": "PROTOTYPE_SEARCH_POC_NON_PROMOTING",
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
            "state": "READY_FOR_PROTOTYPE_LED_OBJECT_REVIEW",
            "build": manifest,
            "oar_summary": report["summary"],
            "fallback_surface": "/workbench/oar/g4-regions",
            "assisted_surface": "/workbench/oar/g4-assisted",
            "primary_interaction": "TEACH_EXAMPLE_THEN_FIND_SIMILAR",
            "snap_role": "FALLBACK_LOCAL_BOX_AID",
            "snap_auto_confirms": False,
            "prototype_search_auto_assigns_support_identity": False,
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

    @router.post("/api/workbench/oar/g4-assisted/teach-example")
    def teach_example(payload: dict[str, Any]):
        try:
            receipt = prototype_search.build_teach_receipt(
                decision_id=str(payload.get("decision_id", "")),
                support_id=str(payload.get("support_id", "")),
                bbox=payload.get("bbox"),
            )
            stored = prototype_search.persist_teach_receipt(receipt)
        except (ValueError, KeyError, TypeError):
            return _json({"state": "OAR_PROTOTYPE_TEACH_REJECTED"}, 422)
        return _json({"state": "PROTOTYPE_TAUGHT", **stored})

    @router.get("/api/workbench/oar/g4-assisted/find-similar")
    def find_similar(prototype_id: str, limit: int = 32):
        try:
            result = prototype_search.search_similar(prototype_id, limit=limit)
        except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError):
            return _json({"state": "OAR_PROTOTYPE_SEARCH_REJECTED"}, 422)
        return _json(result)

    return router
