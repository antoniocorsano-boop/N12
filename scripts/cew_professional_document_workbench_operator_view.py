#!/usr/bin/env python3
"""Operator-clean local review layer for CEW Document Discovery.

Low-level connected components remain available as diagnostics but are not shown
as operator candidates. The active reading unit stays visually primary. This
matches mature technical-review practice: preserve the drawing, expose one
working selection, and keep segmentation/debug geometry opt-in.
"""
from __future__ import annotations

import cew_professional_document_workbench_layout_phase_gate as layout_phase_gate


_STYLE = r'''<style id="cew-operator-clean-local-style">
body.cew-professional-document[data-cew-operator-view="clean-local-v1"] #cew-local-overlay{display:none!important}
body.cew-professional-document[data-cew-operator-view="clean-local-v1"][data-cew-show-local-diagnostics="true"] #cew-local-overlay{display:block!important}
body.cew-professional-document[data-cew-operator-view="clean-local-v1"] #cew-region-pill{display:none!important}
#cew-local-diagnostics-toggle{margin-top:8px;width:100%;padding:7px 8px;border:0;border-radius:5px;background:#e3e9ed;color:#25353f;font-weight:750}
#cew-local-diagnostics-note{display:block;margin-top:5px;color:#6a7780;font-size:10px;line-height:1.35}
</style>'''


_SCRIPT = r'''<script id="cew-operator-clean-local-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
document.body.dataset.cewOperatorView='clean-local-v1';
document.body.dataset.cewShowLocalDiagnostics='false';
let savedEvidence='';

function unitLabel(id){const n=(String(id||'').match(/(\d+)$/)||[])[1]||'?';return `U${n}`}
function setText(id,text){const el=ce(id);if(el&&el.textContent!==text)el.textContent=text}
function ensureDiagnosticControl(){
  const host=ce('cew-local-analysis');if(!host||ce('cew-local-diagnostics-toggle'))return;
  const button=document.createElement('button');button.id='cew-local-diagnostics-toggle';button.type='button';button.textContent='Mostra segnali diagnostici';
  const note=document.createElement('span');note.id='cew-local-diagnostics-note';note.textContent='I riquadri diagnostici descrivono solo componenti grafici grezzi: non sono oggetti, armature o candidati semantici.';
  button.addEventListener('click',()=>{
    const show=document.body.dataset.cewShowLocalDiagnostics!=='true';
    document.body.dataset.cewShowLocalDiagnostics=show?'true':'false';
    button.textContent=show?'Nascondi segnali diagnostici':'Mostra segnali diagnostici';
  });
  host.append(button,note);
}
function syncOperatorView(){
  const api=window.CEWLayoutPhaseGate;if(!api?.state)return;
  ensureDiagnosticControl();
  const s=api.state();const evidence=ce('cew-editor-evidence');
  if(evidence&&!savedEvidence)savedEvidence=evidence.textContent||'';
  if(s.confirmed&&s.activeUnit){
    const label=unitLabel(s.activeUnit),count=Number(s.localCandidateCount||0);
    setText('cew-local-summary',`Unità ${label} attiva. Vista locale pulita; ${count} segnali grafici grezzi restano disponibili solo come diagnostica.`);
    const block=ce('cew-local-block');
    if(block&&!s.semanticReady){block.hidden=false;block.textContent='La semantica resta bloccata: nessun candidato locale affidabile è stato ancora riconosciuto. CEW non trasforma i componenti grafici grezzi in oggetti.'}
    const fb=ce('cew-layout-feedback');if(fb){fb.hidden=false;fb.textContent=`Unità ${label} selezionata. La tavola resta pulita; usa la diagnostica solo se serve a verificare il motore.`}
    if(evidence)evidence.textContent=`${label} · vista locale`;
  }else if(evidence&&savedEvidence){
    evidence.textContent=savedEvidence;
  }
}
function wrapPhaseGate(){
  const api=window.CEWLayoutPhaseGate;if(!api||api.__cewOperatorWrapped)return;
  api.__cewOperatorWrapped=true;
  if(typeof api.selectUnit==='function'){
    const original=api.selectUnit.bind(api);
    api.selectUnit=id=>{const result=original(id);queueMicrotask(syncOperatorView);return result};
  }
}
function install(){wrapPhaseGate();ensureDiagnosticControl();syncOperatorView()}
const observer=new MutationObserver(()=>requestAnimationFrame(install));
observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden','class','data-cew-layout-phase']});
install();
window.CEWOperatorView={sync:syncOperatorView,diagnostics:show=>{document.body.dataset.cewShowLocalDiagnostics=show?'true':'false';syncOperatorView()}};
})();
</script>'''


def _patched_page() -> str:
    html = layout_phase_gate._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_OPERATOR_VIEW_HTML_MARKER_MISSING")
    html = html.replace("</head>", _STYLE + "</head>", 1)
    html = html.replace("</body>", _SCRIPT + "</body>", 1)
    return html
