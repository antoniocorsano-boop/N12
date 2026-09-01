#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

EWS3_RUNTIME_MARKER = "CEW_EWS3_SPATIAL_CANDIDATE_REVIEW"
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
        "registration_validation_state": reg["validation_state"],
        "registration_method": reg["registration_method"],
        "inlier_count": int(reg["inlier_count"]),
        "qa_rms_px_preview": float(reg["qa_rms_px_preview"]),
        "usage_rule": reg["usage_rule"],
        "locator_count": len(locators),
    }
    return locators, meta


def augment(rendered: str, task: str) -> str:
    """Add evidence-navigation focus for the active OA review candidate.

    Source positions are derived only by inverting the CROSS_VALIDATED TAV-05S/G4
    coordinate registration against governed common-XY support coordinates.
    They are navigation locators, never canonical geometry or identity evidence.
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
<script id="cew-ews3-spatial-candidate-review-script" data-ews3-runtime="{EWS3_RUNTIME_MARKER}">
(() => {{
const MARKER={EWS3_RUNTIME_MARKER!r};
const LOCATORS={locators_json};
const REGISTRATION={meta_json};
let lastCandidate=null,marker=null,observer=null;
function candidateObject(id){{return (scene?.objects||[]).find(o=>o.object_id===id)||null}}
function supportIdFor(id){{const o=candidateObject(id),p=o?.properties||{{}};return p.support_id!=null?String(p.support_id):null}}
function activeCandidateId(){{const el=document.querySelector('#oaSimilarResult [data-candidate][aria-current="true"]');return el?.dataset?.candidate||null}}
function locatorForCandidate(id){{const support=supportIdFor(id);return support?LOCATORS[support]||null:null}}
function tiledImage(){{try{{return viewer?.world?.getItemAt(0)||null}}catch(e){{return null}}}}
function ensureMarker(){{
 if(marker)return marker;marker=document.createElement('div');marker.id='ews3SourceMarker';marker.setAttribute('aria-hidden','true');return marker;
}}
function removeMarker(){{if(!viewer||!marker)return;try{{viewer.removeOverlay(marker)}}catch(e){{}}}}
function focusLocator(locator,animate=true){{
 if(!locator||!viewer)return false;const item=tiledImage();if(!item)return false;
 const u=Number(locator.u_px),v=Number(locator.v_px);if(!Number.isFinite(u)||!Number.isFinite(v))return false;
 const fw=Number(REGISTRATION.frame_width_px),fh=Number(REGISTRATION.frame_height_px);
 const contextW=Math.max(1200,fw*.145),contextH=Math.max(900,fh*.18);
 const x=Math.max(0,Math.min(fw-contextW,u-contextW/2)),y=Math.max(0,Math.min(fh-contextH,v-contextH/2));
 const rect=item.imageToViewportRectangle(x,y,Math.min(contextW,fw),Math.min(contextH,fh));
 const point=item.imageToViewportCoordinates(new OpenSeadragon.Point(u,v));
 removeMarker();viewer.addOverlay({{element:ensureMarker(),location:point,placement:OpenSeadragon.Placement.CENTER,checkResize:false}});
 viewer.viewport.fitBounds(rect,!animate);viewer.viewport.applyConstraints();
 document.body.dataset.ews3SourceLocator='REGISTERED_DERIVED';
 return true;
}}
function locationHtml(candidateId,locator){{
 if(!locator)return '<div class="ews3-location unlocated"><div><b>Posizione non collegata alla tavola</b>Il candidato resta revisionabile, ma CEW non inventa un focus spaziale.</div></div>';
 return `<div class="ews3-location"><div><b>Posizione registrata sulla fonte</b>Supporto ${{locator.support_id}} · locator derivato dalla registrazione TAV-05S/G4.</div><button type="button" id="ews3Refocus">Mostra sulla tavola</button></div><details class="ews3-provenance"><summary>Provenienza posizione</summary><div>Stato: <code>${{locator.state}}</code><br>Frame: <code>${{locator.source_frame}}</code><br>Registrazione: <code>${{locator.registration_validation_state}}</code> · ${{locator.registration_inlier_count}} inlier<br>XY comune: ${{Number(locator.metric_x_m).toFixed(3)}}, ${{Number(locator.metric_y_m).toFixed(3)}} m<br>Uso: navigazione evidenza; identità strutturale = false; geometria canonica = false.</div></details>`;
}}
function decorateAndFocus(force=false){{
 const candidateId=activeCandidateId();if(!candidateId)return;
 const locator=locatorForCandidate(candidateId),note=document.querySelector('.ews4-active .ews4-spatial-note');
 if(note){{note.innerHTML=locationHtml(candidateId,locator);note.classList.remove('ews4-spatial-note');note.classList.add('ews3-location-host');document.getElementById('ews3Refocus')?.addEventListener('click',()=>focusLocator(locator,true));}}
 if(force||candidateId!==lastCandidate){{lastCandidate=candidateId;if(locator)focusLocator(locator,true);else removeMarker();window.dispatchEvent(new CustomEvent('cew:ews3-source-focus',{{detail:{{candidate_object_id:candidateId,support_id:supportIdFor(candidateId),locator_state:locator?.state||'UNLOCATED',navigation_only:true,canonical_geometry_authorized:false,structural_identity_authorized:false}}}}));}}
}}
function init(){{
 document.body.dataset.ews3SpatialCandidateReview=MARKER;
 window.__CEW_EWS3_SPATIAL_REVIEW__={{state:'ACTIVE',task:TASK,registration:REGISTRATION,locator_count:Object.keys(LOCATORS).length,navigation_only:true,canonical_write_authorized:false,engineering_authority_effect:'NONE'}};
 const host=document.getElementById('oaSimilarResult');if(!host)return;observer=new MutationObserver(()=>setTimeout(()=>decorateAndFocus(false),0));observer.observe(host,{{subtree:true,childList:true,attributes:true,attributeFilter:['aria-current']}});host.addEventListener('click',()=>setTimeout(()=>decorateAndFocus(false),0));
 window.addEventListener('cew:oa3-similarity-run',()=>setTimeout(()=>decorateAndFocus(true),40));window.addEventListener('cew:ews2-mode-change',()=>setTimeout(()=>decorateAndFocus(false),40));decorateAndFocus(true);
}}
let tries=0;const timer=setInterval(()=>{{tries++;if(typeof viewer!=='undefined'&&viewer&&viewer.world?.getItemCount?.()>0&&document.getElementById('oaSimilarResult')){{clearInterval(timer);init()}}else if(tries>180)clearInterval(timer)}},100);
}})();
</script>'''
    return rendered.replace("</body>", script + "</body>", 1)
