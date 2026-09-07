#!/usr/bin/env python3
"""Compatibility route headers for layout-guided Document Discovery."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench_layout_phase_gate as layout_phase_gate


_UNIT_SELECTION_STYLE = r'''<style id="cew-layout-unit-selection-style">
#cew-layout-overlay .cew-layout-unit::after{
  content:attr(data-cew-unit-label);position:absolute;left:5px;top:5px;z-index:2;
  min-width:22px;padding:2px 5px;border-radius:10px;background:#5f5297;color:#fff;
  font-size:9px;font-weight:800;line-height:16px;text-align:center;pointer-events:none;
  box-shadow:0 1px 3px #0003;
}
#cew-layout-overlay .cew-layout-unit.active::after{background:#2f6f8f}
#cew-layout-unit-hint{margin-top:6px;color:#4f5f69;font-size:10px;line-height:1.35}
</style>'''


_UNIT_SELECTION_SCRIPT = r'''<script id="cew-layout-unit-selection-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
function labelFor(button,index){
  const raw=button?.dataset?.layoutUnit||`LU-${index+1}`;
  const suffix=(raw.match(/(\d+)$/)||[])[1]||String(index+1);
  return `U${suffix}`;
}
function setFeedback(text){
  const el=ce('cew-layout-feedback');if(!el)return;el.textContent=text;el.hidden=false;
}
function decorate(){
  const buttons=[...document.querySelectorAll('#cew-layout-overlay .cew-layout-unit')];
  buttons.forEach((b,i)=>{
    const label=labelFor(b,i);b.dataset.cewUnitLabel=label;
    b.title=`Unità di lettura ${label} · clicca per analizzare questa zona`;
    b.setAttribute('aria-label',`Seleziona unità di lettura ${label}`);
  });
  const gate=window.CEWLayoutPhaseGate?.state?.();
  if(gate?.confirmed&&!gate.activeUnit&&buttons.length){
    const labels=buttons.map((b,i)=>labelFor(b,i));
    setFeedback(`Struttura confermata. Le unità sono i riquadri viola ${labels[0]}–${labels[labels.length-1]}; clicca una unità per avviare l’analisi locale.`);
  }
}
function selectFromPointer(e){
  const b=e.target?.closest?.('#cew-layout-overlay .cew-layout-unit');if(!b)return;
  const api=window.CEWLayoutPhaseGate,state=api?.state?.();if(!api||!state?.confirmed)return;
  const id=b.dataset.layoutUnit,label=b.dataset.cewUnitLabel||id;
  try{
    api.selectUnit(id);
    requestAnimationFrame(()=>{
      const after=api.state?.();
      if(after?.activeUnit===id){
        setFeedback(`Unità ${label} selezionata. Analisi locale avviata su questa sola zona.`);
        ce('cew-local-analysis')?.scrollIntoView({block:'nearest'});
      }else{
        setFeedback(`Unità ${label} non selezionata. Riprova oppure usa “Rivedi struttura”.`);
      }
    });
  }catch(err){
    console.error('CEW_LAYOUT_UNIT_SELECTION_FAILED',err);
    setFeedback(`Impossibile avviare l’analisi locale per ${label}. Nessun significato è stato assegnato.`);
  }
}
document.addEventListener('pointerup',selectFromPointer,true);
const observer=new MutationObserver(records=>{
  if(records.some(r=>r.target?.id==='cew-layout-overlay'||r.target?.closest?.('#cew-layout-overlay')||[...r.addedNodes].some(n=>n?.id==='cew-layout-overlay'||n?.querySelector?.('.cew-layout-unit'))))requestAnimationFrame(decorate);
});
observer.observe(document.body,{subtree:true,childList:true});
window.addEventListener('cew-layout-confirmed',decorate);
requestAnimationFrame(decorate);
window.CEWLayoutUnitSelection={decorate,select:id=>window.CEWLayoutPhaseGate?.selectUnit?.(id)};
})();
</script>'''


def _patched_page() -> str:
    html = layout_phase_gate._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_LAYOUT_UNIT_SELECTION_HTML_MARKER_MISSING")
    html = html.replace("</head>", _UNIT_SELECTION_STYLE + "</head>", 1)
    html = html.replace("</body>", _UNIT_SELECTION_SCRIPT + "</body>", 1)
    return html


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def region_guided_compat_page():
        return HTMLResponse(
            _patched_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
                "X-CEW-Document-Workbench": "PROFESSIONAL_V2",
                "X-CEW-Panel-Architecture": "ACTIVITY_PRIMARY_EDITOR_AUXILIARY_STATUS",
                "X-CEW-Panel-Quality": "MATURE_V1",
                "X-CEW-Panel-Content": "HVA_REFINED_V1",
                "X-CEW-Governed-Analysis": "ASYNC_BOUNDED_RECONSTRUCT_V1",
                "X-CEW-Preview-Runtime-Recovery": "BROWSER_RECONSTRUCT_V1",
                "X-CEW-Region-Guidance": "LAYOUT_PRIMITIVES_V1",
                "X-CEW-Region-Semantic-Authority": "NONE",
                "X-CEW-Layout-Learning": "HYPOTHESIS_PLUS_TEACH_ONE_RELATION_V1",
                "X-CEW-Layout-Semantic-Authority": "NONE",
                "X-CEW-Layout-Prototype-Persistence": "LOCAL_NON_CANONICAL_V1",
                "X-CEW-Layout-Phase-Gate": "LAYOUT_CONFIRM_BEFORE_SEMANTICS_V2",
                "X-CEW-Layout-Unit-Selection": "EXPLICIT_POINTER_UI_BRIDGE_V1",
                "X-CEW-Local-Unit-Analysis": "BROWSER_GRAPHIC_FRAGMENTS_V1",
                "X-CEW-Semantic-Gate": "LOCAL_BACKEND_CANDIDATE_REQUIRED_V1",
            },
        )

    return router
