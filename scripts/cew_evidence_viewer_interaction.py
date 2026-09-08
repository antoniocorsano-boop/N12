#!/usr/bin/env python3
from __future__ import annotations

"""Human-scale viewport controls for the governed Evidence Workspace.

The module enhances the existing evidence reading aid only. It never mutates
SourceVersion, Page, PageTransform, EvidenceRegion, receipts, or canonical data.
"""

import cew_source_evidence_workspace as source_workspace

_INSTALLED = False
_ORIGINAL_BUILD = None


_STYLE_OLD = ".viewer{background:#20252b;border-radius:10px;padding:8px;min-height:320px;display:flex;align-items:center;justify-content:center}.viewer img{max-width:100%;max-height:72vh;background:white}"
_STYLE_NEW = ".viewer{background:#20252b;border-radius:10px;padding:8px;height:min(72vh,720px);min-height:360px;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative;touch-action:none;cursor:grab;user-select:none}.viewer.dragging{cursor:grabbing}.viewer img{max-width:100%;max-height:100%;width:auto;height:auto;background:white;transform-origin:center center;will-change:transform;pointer-events:none;user-select:none}.view-tools{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}.view-tools button{background:#fff;color:#173f5f}.viewer-readout{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center;margin-top:8px;font-size:13px}.viewer-help{color:#5d6875}"

_VIEWER_OLD = '<div class="viewer"><img id="sourceImage" alt="Rendering verificato della fonte"'
_VIEWER_NEW = '<div class="view-tools" role="toolbar" aria-label="Strumenti di ispezione"><button type="button" onclick="zoomBy(1.25)">＋ Ingrandisci</button><button type="button" onclick="zoomBy(0.8)">− Riduci</button><button type="button" onclick="fitEvidenceView()">Adatta</button><button type="button" onclick="rotateEvidence(-90)">↶ 90°</button><button type="button" onclick="rotateEvidence(90)">↷ 90°</button><button type="button" onclick="resetEvidenceView()">Reset vista</button></div><div class="viewer" id="evidenceViewport" tabindex="0" aria-label="Vista interattiva dell’evidenza: trascina per spostarti, usa rotella o più e meno per ingrandire"><img id="sourceImage" draggable="false" alt="Rendering verificato della fonte"'

_READOUT_OLD = '</div><p id="scaleNote" class="muted">MICRO — regione di evidenza con piccolo margine di lettura.</p>'
_READOUT_NEW = '</div><div class="viewer-readout"><span id="viewerState">Evidenza · Zoom 100% · Zoom non usato · Pan non usato · Rotazione 0°</span><span class="viewer-help">Trascina per spostarti · rotella/trackpad o +/− per zoom · 0 per reset</span></div><p id="scaleNote" class="muted">MICRO — regione di evidenza con piccolo margine di lettura.</p>'

_SCALE_OLD = "function scale(s){document.getElementById('sourceImage').src='/api/source/render?task='+encodeURIComponent(META.task_id)+'&scale='+s+'&v='+Date.now();document.getElementById('scaleNote').textContent={MICRO:'MICRO — regione di evidenza con piccolo margine di lettura.',MESO:'MESO — regione più contesto grafico vicino.',MACRO:'MACRO — pagina completa della fonte.'}[s]}"
_SCALE_NEW = r"""const evidenceViewport=document.getElementById('evidenceViewport');const sourceImage=document.getElementById('sourceImage');const evidenceViewerState=document.getElementById('viewerState');let evidenceZoom=1,evidencePanX=0,evidencePanY=0,evidenceRotation=0,evidencePanEver=false,evidenceZoomEver=false;const evidencePointers=new Map();let evidenceDrag=null,evidencePinch=null;function clampEvidence(v,min,max){return Math.min(max,Math.max(min,v))}function updateEvidenceViewerState(){evidenceViewerState.textContent=`Evidenza · Zoom ${Math.round(evidenceZoom*100)}% · Zoom ${evidenceZoomEver?'usato':'non usato'} · Pan ${evidencePanEver?'usato':'non usato'} · Rotazione ${evidenceRotation}°`}function applyEvidenceView(){sourceImage.style.transform=`translate3d(${evidencePanX}px,${evidencePanY}px,0) rotate(${evidenceRotation}deg) scale(${evidenceZoom})`;updateEvidenceViewerState()}function fitEvidenceView(){evidencePanX=0;evidencePanY=0;const iw=Math.max(1,sourceImage.offsetWidth),ih=Math.max(1,sourceImage.offsetHeight),vw=Math.max(1,evidenceViewport.clientWidth-16),vh=Math.max(1,evidenceViewport.clientHeight-16);const rotated=Math.abs(evidenceRotation)%180===90;const rw=rotated?ih:iw,rh=rotated?iw:ih;evidenceZoom=Math.min(1,vw/rw,vh/rh);applyEvidenceView()}function resetEvidenceView(){evidenceRotation=0;evidencePanX=0;evidencePanY=0;evidenceZoom=1;fitEvidenceView()}function zoomBy(factor,cx,cy){const rect=evidenceViewport.getBoundingClientRect();const px=(cx??(rect.left+rect.width/2))-rect.left-rect.width/2,py=(cy??(rect.top+rect.height/2))-rect.top-rect.height/2;const next=clampEvidence(evidenceZoom*factor,.2,8);const ratio=next/evidenceZoom;evidencePanX=px-(px-evidencePanX)*ratio;evidencePanY=py-(py-evidencePanY)*ratio;evidenceZoom=next;evidenceZoomEver=true;applyEvidenceView()}function rotateEvidence(delta){evidenceRotation=(evidenceRotation+delta+360)%360;fitEvidenceView()}function scale(s){sourceImage.src='/api/source/render?task='+encodeURIComponent(META.task_id)+'&scale='+s+'&v='+Date.now();document.getElementById('scaleNote').textContent={MICRO:'MICRO — regione di evidenza con piccolo margine di lettura.',MESO:'MESO — regione più contesto grafico vicino.',MACRO:'MACRO — pagina completa della fonte.'}[s]}sourceImage.addEventListener('load',()=>fitEvidenceView());evidenceViewport.addEventListener('wheel',e=>{e.preventDefault();zoomBy(e.deltaY<0?1.14:.88,e.clientX,e.clientY)},{passive:false});evidenceViewport.addEventListener('dblclick',e=>{e.preventDefault();zoomBy(1.35,e.clientX,e.clientY)});evidenceViewport.addEventListener('pointerdown',e=>{evidencePointers.set(e.pointerId,{x:e.clientX,y:e.clientY});try{evidenceViewport.setPointerCapture(e.pointerId)}catch(_e){}if(evidencePointers.size===1){evidenceDrag={id:e.pointerId,x:e.clientX,y:e.clientY,panX:evidencePanX,panY:evidencePanY};evidenceViewport.classList.add('dragging')}else if(evidencePointers.size===2){const pts=[...evidencePointers.values()];evidencePinch={distance:Math.hypot(pts[1].x-pts[0].x,pts[1].y-pts[0].y),zoom:evidenceZoom};evidenceDrag=null}});evidenceViewport.addEventListener('pointermove',e=>{if(!evidencePointers.has(e.pointerId))return;evidencePointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(evidencePointers.size>=2&&evidencePinch){const pts=[...evidencePointers.values()].slice(0,2);const dist=Math.hypot(pts[1].x-pts[0].x,pts[1].y-pts[0].y);if(evidencePinch.distance>0){evidenceZoom=clampEvidence(evidencePinch.zoom*(dist/evidencePinch.distance),.2,8);evidenceZoomEver=true;applyEvidenceView()}return}if(evidenceDrag&&evidenceDrag.id===e.pointerId){const dx=e.clientX-evidenceDrag.x,dy=e.clientY-evidenceDrag.y;if(Math.abs(dx)+Math.abs(dy)>3)evidencePanEver=true;evidencePanX=evidenceDrag.panX+dx;evidencePanY=evidenceDrag.panY+dy;applyEvidenceView()}});function endEvidencePointer(e){evidencePointers.delete(e.pointerId);if(evidencePointers.size<2)evidencePinch=null;if(evidencePointers.size===0){evidenceDrag=null;evidenceViewport.classList.remove('dragging')}else if(evidencePointers.size===1){const [id,p]=[...evidencePointers.entries()][0];evidenceDrag={id,x:p.x,y:p.y,panX:evidencePanX,panY:evidencePanY}}try{evidenceViewport.releasePointerCapture(e.pointerId)}catch(_e){}}evidenceViewport.addEventListener('pointerup',endEvidencePointer);evidenceViewport.addEventListener('pointercancel',endEvidencePointer);evidenceViewport.addEventListener('keydown',e=>{if(e.key==='+'||e.key==='='){e.preventDefault();zoomBy(1.2)}else if(e.key==='-'){e.preventDefault();zoomBy(.83)}else if(e.key==='0'){e.preventDefault();resetEvidenceView()}else if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();evidencePanEver=true;const step=42;if(e.key==='ArrowLeft')evidencePanX+=step;if(e.key==='ArrowRight')evidencePanX-=step;if(e.key==='ArrowUp')evidencePanY+=step;if(e.key==='ArrowDown')evidencePanY-=step;applyEvidenceView()}});if(sourceImage.complete)fitEvidenceView();"""


def _enhance(html_text: str) -> str:
    if 'id="sourceImage"' not in html_text:
        return html_text
    required = (_STYLE_OLD, _VIEWER_OLD, _READOUT_OLD, _SCALE_OLD)
    missing = [anchor[:60] for anchor in required if anchor not in html_text]
    if missing:
        raise RuntimeError(f"EVIDENCE_VIEWER_INTERACTION_ANCHOR_MISSING: {missing}")
    enhanced = html_text.replace(_STYLE_OLD, _STYLE_NEW, 1)
    enhanced = enhanced.replace(_VIEWER_OLD, _VIEWER_NEW, 1)
    enhanced = enhanced.replace(_READOUT_OLD, _READOUT_NEW, 1)
    enhanced = enhanced.replace(_SCALE_OLD, _SCALE_NEW, 1)
    return enhanced


def install() -> None:
    global _INSTALLED, _ORIGINAL_BUILD
    if _INSTALLED:
        return
    _ORIGINAL_BUILD = source_workspace.build_evidence_workspace

    def interactive_build(task_id: str) -> str:
        return _enhance(_ORIGINAL_BUILD(task_id))

    interactive_build.__name__ = "build_evidence_workspace_interactive"
    interactive_build._cew_evidence_interaction = True  # type: ignore[attr-defined]
    source_workspace.build_evidence_workspace = interactive_build
    _INSTALLED = True
