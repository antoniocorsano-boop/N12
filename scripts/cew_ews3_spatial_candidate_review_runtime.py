#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

EWS3_RUNTIME_MARKER = "CEW_EWS3_SPATIAL_CANDIDATE_REVIEW"
EWS31_FRAME_ADAPTER = "ROT90_CCW_REGISTRATION_TO_NATIVE_DZI"
OA_PILOT_TASK = "OA-N12-G4-COLUMN-PILOT"
ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_CSV = ROOT / "data/canonical/STOREY_SUPPORT_XY_REGISTRATION_v1.csv"
SUPPORTS_CSV = ROOT / "data/canonical/VERTICAL_SUPPORT_LINES_CURRENT_v1.csv"


def _load_locators() -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    with REGISTRATION_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    reg = next((r for r in rows if r.get("sheet_id") == "TAV-05S" and r.get("level_id") == "G4"), None)
    if not reg:
        raise RuntimeError("EWS3: TAV-05S/G4 registration missing")
    if reg.get("validation_state") != "CROSS_VALIDATED":
        raise RuntimeError("EWS3: TAV-05S/G4 registration is not CROSS_VALIDATED")
    if reg.get("source_frame") != "ROT90_CCW_300DPI":
        raise RuntimeError(f"EWS3.1: unsupported registration frame {reg.get('source_frame')}")
    a1 = float(reg["metric_x_from_u"])
    a2 = float(reg["metric_x_from_v"])
    a0 = float(reg["metric_x_offset"])
    b1 = float(reg["metric_y_from_u"])
    b2 = float(reg["metric_y_from_v"])
    b0 = float(reg["metric_y_offset"])
    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-12:
        raise RuntimeError("EWS3: non-invertible TAV-05S/G4 registration")
    width = int(reg["frame_width_px"])
    height = int(reg["frame_height_px"])

    with SUPPORTS_CSV.open(newline="", encoding="utf-8") as fh:
        supports = list(csv.DictReader(fh))
    locators: dict[str, dict[str, object]] = {}
    for row in supports:
        if row.get("g4_present") != "PRESENT":
            continue
        support_id = str(row["support_id"])
        x = float(row["x_global_m"])
        y = float(row["y_global_m"])
        dx = x - a0
        dy = y - b0
        u = (dx * b2 - a2 * dy) / det
        v = (a1 * dy - dx * b1) / det
        locators[support_id] = {
            "support_id": support_id,
            "state": "REGISTERED_DERIVED",
            "source_sheet": "TAV-05S",
            "level_id": "G4",
            "source_frame": reg["source_frame"],
            "u_px": round(u, 3),
            "v_px": round(v, 3),
            "metric_x_m": x,
            "metric_y_m": y,
            "metric_provenance": row.get("metric_provenance"),
            "registration_validation_state": reg["validation_state"],
            "registration_method": reg["registration_method"],
            "registration_inlier_count": int(reg["inlier_count"]),
            "registration_qa_rms_px_preview": float(reg["qa_rms_px_preview"]),
            "usage_rule": reg["usage_rule"],
            "navigation_only": True,
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
        }
    meta = {
        "source_sheet": "TAV-05S",
        "level_id": "G4",
        "source_frame": reg["source_frame"],
        "frame_width_px": width,
        "frame_height_px": height,
        "viewer_frame_adapter": EWS31_FRAME_ADAPTER,
        "expected_native_dzi_width_px": height,
        "expected_native_dzi_height_px": width,
        "registration_validation_state": reg["validation_state"],
        "registration_method": reg["registration_method"],
        "inlier_count": int(reg["inlier_count"]),
        "qa_rms_px_preview": float(reg["qa_rms_px_preview"]),
        "usage_rule": reg["usage_rule"],
        "locator_count": len(locators),
    }
    return locators, meta


def _registration_to_native_viewer(u: float, v: float, *, native_width: float, native_height: float) -> tuple[float, float]:
    """Map ROT90_CCW registration coordinates back into the native portrait DZI.

    Registration frame: width=H_native, height=W_native with CCW rotation:
      u = y_native
      v = W_native - x_native
    Therefore:
      x_native = W_native - v
      y_native = u
    This is a viewer adapter only; it does not modify the registered geometry.
    """
    x_native = native_width - v
    y_native = u
    if not (0.0 <= x_native <= native_width and 0.0 <= y_native <= native_height):
        raise ValueError("EWS3.1: mapped viewer locator outside native DZI frame")
    return x_native, y_native


def augment(rendered: str, task: str) -> str:
    """Add evidence-navigation focus for the active OA review candidate.

    Source positions are derived only by inverting the CROSS_VALIDATED TAV-05S/G4
    coordinate registration against governed common-XY support coordinates.
    EWS-3.1 then maps the ROT90_CCW registration frame into the native DZI frame.
    Both are navigation operations, never canonical geometry or identity evidence.
    """
    if EWS3_RUNTIME_MARKER in rendered or task != OA_PILOT_TASK:
        return rendered

    locators, meta = _load_locators()
    locators_json = json.dumps(locators, ensure_ascii=False, separators=(",", ":"))
    meta_json = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))

    style = r'''
<style id="cew-ews3-spatial-candidate-review-style">
#ews3SourceMarker{width:28px;height:28px;border:3px solid #c12f2f;border-radius:50%;box-shadow:0 0 0 4px rgba(255,255,255,.92),0 2px 8px rgba(0,0,0,.35);pointer-events:none;background:rgba(255,255,255,.18)}
#ews3SourceMarker::before,#ews3SourceMarker::after{content:"";position:absolute;background:#c12f2f;left:50%;top:50%;transform:translate(-50%,-50%)}
#ews3SourceMarker::before{width:38px;height:2px}#ews3SourceMarker::after{width:2px;height:38px}
.ews3-location{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;background:#edf8f1;border-left:4px solid var(--ok);padding:8px;margin:7px 0;font-size:11px}.ews3-location b{display:block;font-size:12px}.ews3-location button{padding:5px 8px;font-size:11px}.ews3-location.unlocated{background:#fff7e8;border-left-color:var(--warn)}
.ews3-provenance{margin-top:5px;font-size:10px;color:var(--muted)}.ews3-provenance summary{cursor:pointer;font-weight:750}.ews3-provenance code{font-size:9px;overflow-wrap:anywhere}
</style>'''
    rendered = rendered.replace("</head>", style + "</head>", 1)

    script = f'''
<script id="cew-ews3-spatial-candidate-review-script" data-ews3-runtime="{EWS3_RUNTIME_MARKER}" data-ews31-frame-adapter="{EWS31_FRAME_ADAPTER}">
(() => {{
const MARKER={EWS3_RUNTIME_MARKER!r};
const FRAME_ADAPTER={EWS31_FRAME_ADAPTER!r};
const LOCATORS={locators_json};
const REGISTRATION={meta_json};
let lastCandidate=null,marker=null,observer=null;
function candidateObject(id){{return (scene?.objects||[]).find(o=>o.object_id===id)||null}}
function supportIdFor(id){{const o=candidateObject(id),p=o?.properties||{{}};return p.support_id!=null?String(p.support_id):null}}
function activeCandidateId(){{const el=document.querySelector('#oaSimilarResult [data-candidate][aria-current="true"]');return el?.dataset?.candidate||null}}
function locatorForCandidate(id){{const support=supportIdFor(id);return support?LOCATORS[support]||null:null}}
function tiledImage(){{try{{return viewer?.world?.getItemAt(0)||null}}catch(e){{return null}}}}
function ensureMarker(){{if(marker)return marker;marker=document.createElement('div');marker.id='ews3SourceMarker';marker.setAttribute('aria-hidden','true');return marker;}}
function removeMarker(){{if(!viewer||!marker)return;try{{viewer.removeOverlay(marker)}}catch(e){{}}}}
function nativePoint(locator,item){{
 const u=Number(locator?.u_px),v=Number(locator?.v_px);if(!Number.isFinite(u)||!Number.isFinite(v)||!item)return null;
 const size=item.getContentSize?.();if(!size)return null;const nw=Number(size.x),nh=Number(size.y);
 if(!Number.isFinite(nw)||!Number.isFinite(nh)||nw<=0||nh<=0)return null;
 if(REGISTRATION.source_frame!=='ROT90_CCW_300DPI')return null;
 const x=nw-v,y=u;
 if(x<0||x>nw||y<0||y>nh)return null;
 return {{x,y,nw,nh,u,v}};
}}
function updateRegistrationStatus(locator,p){{
 const el=document.getElementById('registrationState');if(!el)return;
 if(locator&&p){{el.textContent='locator fonte registrato · navigazione';el.dataset.ews3State='REGISTERED_DERIVED';el.title=`${{FRAME_ADAPTER}} · viewer ${{Math.round(p.nw)}}×${{Math.round(p.nh)}}`;}}
 else{{el.textContent='posizione sulla tavola non registrata';el.dataset.ews3State='UNLOCATED';el.removeAttribute('title');}}
}}
function focusLocator(locator,animate=true){{
 if(!locator||!viewer)return false;const item=tiledImage();if(!item)return false;const p=nativePoint(locator,item);if(!p){{updateRegistrationStatus(null,null);return false;}}
 const contextW=Math.max(900,p.nw*.18),contextH=Math.max(1200,p.nh*.145);
 const x=Math.max(0,Math.min(p.nw-contextW,p.x-contextW/2)),y=Math.max(0,Math.min(p.nh-contextH,p.y-contextH/2));
 const rect=item.imageToViewportRectangle(x,y,Math.min(contextW,p.nw),Math.min(contextH,p.nh));
 const point=item.imageToViewportCoordinates(new OpenSeadragon.Point(p.x,p.y));
 removeMarker();viewer.addOverlay({{element:ensureMarker(),location:point,placement:OpenSeadragon.Placement.CENTER,checkResize:false}});
 viewer.viewport.fitBounds(rect,!animate);viewer.viewport.applyConstraints();
 document.body.dataset.ews3SourceLocator='REGISTERED_DERIVED';document.body.dataset.ews31ViewerFrame=FRAME_ADAPTER;
 updateRegistrationStatus(locator,p);
 return true;
}}
function locationHtml(candidateId,locator){{
 if(!locator)return '<div class="ews3-location unlocated"><div><b>Posizione non collegata alla tavola</b>Il candidato resta revisionabile, ma CEW non inventa un focus spaziale.</div></div>';
 return `<div class="ews3-location"><div><b>Posizione registrata sulla fonte</b>Supporto ${{locator.support_id}} · locator derivato dalla registrazione TAV-05S/G4.</div><button type="button" id="ews3Refocus">Mostra sulla tavola</button></div><details class="ews3-provenance"><summary>Provenienza posizione</summary><div>Stato: <code>${{locator.state}}</code><br>Frame registrazione: <code>${{locator.source_frame}}</code><br>Adapter viewer: <code>${{FRAME_ADAPTER}}</code><br>Registrazione: <code>${{locator.registration_validation_state}}</code> · ${{locator.registration_inlier_count}} inlier<br>XY comune: ${{Number(locator.metric_x_m).toFixed(3)}}, ${{Number(locator.metric_y_m).toFixed(3)}} m<br>Uso: navigazione evidenza; identità strutturale = false; geometria canonica = false.</div></details>`;
}}
function decorateAndFocus(force=false){{
 const candidateId=activeCandidateId();if(!candidateId)return;
 const locator=locatorForCandidate(candidateId),note=document.querySelector('.ews4-active .ews4-spatial-note');
 if(note){{note.innerHTML=locationHtml(candidateId,locator);note.classList.remove('ews4-spatial-note');note.classList.add('ews3-location-host');document.getElementById('ews3Refocus')?.addEventListener('click',()=>focusLocator(locator,true));}}
 if(force||candidateId!==lastCandidate){{lastCandidate=candidateId;if(locator)focusLocator(locator,true);else{{removeMarker();updateRegistrationStatus(null,null)}}window.dispatchEvent(new CustomEvent('cew:ews3-source-focus',{{detail:{{candidate_object_id:candidateId,support_id:supportIdFor(candidateId),locator_state:locator?.state||'UNLOCATED',viewer_frame_adapter:FRAME_ADAPTER,navigation_only:true,canonical_geometry_authorized:false,structural_identity_authorized:false}}}}));}}
}}
function init(){{
 document.body.dataset.ews3SpatialCandidateReview=MARKER;
 window.__CEW_EWS3_SPATIAL_REVIEW__={{state:'ACTIVE',task:TASK,registration:REGISTRATION,viewer_frame_adapter:FRAME_ADAPTER,locator_count:Object.keys(LOCATORS).length,navigation_only:true,canonical_write_authorized:false,engineering_authority_effect:'NONE'}};
 const host=document.getElementById('oaSimilarResult');if(!host)return;observer=new MutationObserver(()=>setTimeout(()=>decorateAndFocus(false),0));observer.observe(host,{{subtree:true,childList:true,attributes:true,attributeFilter:['aria-current']}});host.addEventListener('click',()=>setTimeout(()=>decorateAndFocus(false),0));
 window.addEventListener('cew:oa3-similarity-run',()=>setTimeout(()=>decorateAndFocus(true),40));window.addEventListener('cew:ews2-mode-change',()=>setTimeout(()=>decorateAndFocus(false),40));decorateAndFocus(true);
}}
let tries=0;const timer=setInterval(()=>{{tries++;if(typeof viewer!=='undefined'&&viewer&&viewer.world?.getItemCount?.()>0&&document.getElementById('oaSimilarResult')){{clearInterval(timer);init()}}else if(tries>180)clearInterval(timer)}},100);
}})();
</script>'''
    return rendered.replace("</body>", script + "</body>", 1)
