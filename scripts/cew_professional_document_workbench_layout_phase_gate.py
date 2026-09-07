#!/usr/bin/env python3
"""Phase-gated layout workflow for CEW Document Discovery.

The operator validates page organization before semantic teaching. After layout
confirmation, one reading unit is analysed locally. Legacy page-scale clusters
are never reused for teaching unless a backend candidate is genuinely local to
the selected unit. All state in this layer is non-canonical.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench_layout_learning as layout_learning


_STYLE = r'''<style id="cew-layout-phase-gate-style">
body.cew-professional-document[data-cew-semantic-ready="false"] #cew-decision-tab{display:none!important}
#cew-layout-phase-panel{padding:10px 11px 14px;font-size:11px;line-height:1.4}
#cew-layout-phase-panel h3{font-size:15px;margin:0 0 7px;color:#263640}
#cew-layout-phase-panel .phase-state{display:inline-flex;padding:3px 7px;border-radius:10px;background:#fff3d3;color:#775300;font-size:9px;font-weight:800}
#cew-layout-phase-panel .phase-state.ok{background:#e7f3eb;color:#286343}
#cew-layout-phase-panel dl{display:grid;grid-template-columns:112px 1fr;gap:5px 8px;margin:10px 0}
#cew-layout-phase-panel dt{color:#6a7780}#cew-layout-phase-panel dd{margin:0;font-weight:650}
#cew-layout-phase-panel .phase-actions{display:grid;gap:6px;margin-top:10px}
#cew-layout-phase-panel button{padding:8px 9px;border:0;border-radius:5px;font-weight:750}
#cew-layout-confirm{background:#1d704b;color:#fff}
#cew-layout-alternative,#cew-layout-teach,#cew-layout-reset{background:#e3e9ed;color:#25353f}
#cew-layout-feedback{margin-top:8px;padding:7px 8px;border-radius:5px;background:#eef4f0;color:#315d45;font-weight:650}
#cew-layout-feedback[hidden]{display:none!important}
#cew-local-analysis{margin-top:11px;padding-top:10px;border-top:1px solid #d5dbe1}
#cew-local-analysis strong{display:block;margin-bottom:4px}.cew-layout-muted{color:#68757e}
#cew-local-overlay{position:absolute;inset:0;z-index:7;pointer-events:none}
#cew-local-overlay .cew-local-fragment{position:absolute;border:2px solid #138a83;background:#138a8312;border-radius:2px}
#cew-layout-structure-tab[aria-selected="true"]{color:#174f70;border-bottom-color:#2f88b8;background:#fff}
#cew-layout-overlay .cew-layout-unit::after{content:attr(data-cew-unit-label);position:absolute;left:5px;top:5px;z-index:3;min-width:22px;padding:2px 5px;border-radius:10px;background:#5f5297;color:#fff;font-size:9px;font-weight:800;line-height:16px;text-align:center;pointer-events:none;box-shadow:0 1px 3px #0003}
#cew-layout-overlay .cew-layout-unit.active::after{background:#2f6f8f}
</style>'''


_SCRIPT = r'''<script id="cew-layout-phase-gate-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
const LAYOUT_UNCONFIRMED='LAYOUT_UNCONFIRMED',LAYOUT_CONFIRMED='LAYOUT_CONFIRMED';
const SEMANTIC_GATE='LOCAL_BACKEND_CANDIDATE_REQUIRED_V1';
const gate={phase:LAYOUT_UNCONFIRMED,confirmed:false,activeUnit:null,localCandidates:[],semanticReady:false,lastKey:'',syncing:false};
document.body.dataset.cewLayoutPhaseGate='v3';
document.body.dataset.cewLayoutPhase='unconfirmed';
document.body.dataset.cewSemanticReady='false';

function clamp(n,min,max){return Math.min(max,Math.max(min,Number(n)||0))}
function units(){return window.CEWLayoutLearning?.units?.()||[]}
function unitButtons(){return [...document.querySelectorAll('#cew-layout-overlay .cew-layout-unit')]}
function humanUnitLabel(id,index=0){const suffix=(String(id||'').match(/(\d+)$/)||[])[1]||String(index+1);return `U${suffix}`}
function key(){return `cew.layoutConfirmed.v1:${ce('project')?.value?.trim()||'NO_PROJECT'}:${ce('source')?.value||'NO_SOURCE'}:${currentPreviewPageIndex||0}`}
function readConfirmed(){try{return localStorage.getItem(key())==='CONFIRMED'}catch(_){return false}}
function writeConfirmed(v){try{v?localStorage.setItem(key(),'CONFIRMED'):localStorage.removeItem(key())}catch(_){}}
function setText(id,text){const el=ce(id);if(el&&el.textContent!==text)el.textContent=text}
function setHidden(id,value){const el=ce(id);if(el&&el.hidden!==!!value)el.hidden=!!value}

function unitCentres(){
  const us=units(),buttons=unitButtons(),stage=ce('page-stage');
  if(buttons.length===us.length&&buttons.length>1&&stage){
    const sr=stage.getBoundingClientRect();if(sr.width>0&&sr.height>0){
      return {cx:buttons.map(b=>{const r=b.getBoundingClientRect();return (r.left+r.width/2-sr.left)/sr.width}),cy:buttons.map(b=>{const r=b.getBoundingClientRect();return (r.top+r.height/2-sr.top)/sr.height})};
    }
  }
  return {cx:us.map(u=>Number(u.x||0)+Number(u.w||0)/2),cy:us.map(u=>Number(u.y||0)+Number(u.h||0)/2)};
}
function describe(){
  const us=units();
  if(!us.length)return {label:'Nessuna unità proposta',reading:'da definire',repeat:'da definire',kind:'NONE'};
  const {cx,cy}=unitCentres(),spanX=Math.max(...cx)-Math.min(...cx),spanY=Math.max(...cy)-Math.min(...cy);
  if(spanX>=Math.max(.06,spanY*1.65))return {label:`${us.length} colonne di lettura candidate`,reading:'dall’alto verso il basso',repeat:'da sinistra verso destra',kind:'COLUMNS'};
  if(spanY>=Math.max(.06,spanX*1.65))return {label:`${us.length} fasce di lettura candidate`,reading:'da sinistra verso destra',repeat:'dall’alto verso il basso',kind:'ROWS'};
  return {label:`${us.length} unità di lettura candidate`,reading:'da verificare',repeat:'da verificare',kind:'MIXED'};
}
function decorateUnits(){
  const bs=unitButtons();bs.forEach((b,i)=>{const label=humanUnitLabel(b.dataset.layoutUnit,i);b.dataset.cewUnitLabel=label;b.title=`Unità di lettura ${label} · clicca per analizzare questa zona`;b.setAttribute('aria-label',`Seleziona unità di lettura ${label}`)});return bs;
}
function confirmedGuidance(){
  decorateUnits();const us=units();if(!us.length)return 'Struttura confermata. Nessuna unità di lettura disponibile.';
  const labels=us.map((u,i)=>humanUnitLabel(u.id,i));return `Struttura confermata. Le unità sono i riquadri viola ${labels[0]}–${labels[labels.length-1]}; clicca una unità per avviare l’analisi locale.`;
}

function showStructure(){
  for(const p of document.querySelectorAll('.cew-inspector-panel'))p.hidden=p.id!=='cew-layout-phase-panel';
  for(const b of document.querySelectorAll('#cew-inspector-tabs button')){const on=b.id==='cew-layout-structure-tab';b.classList.toggle('active',on);b.setAttribute('aria-selected',on?'true':'false')}
}
function ensurePanel(){
  const tabs=ce('cew-inspector-tabs'),body=document.querySelector('.cew-inspector-body');if(!tabs||!body)return;
  let tab=ce('cew-layout-structure-tab');if(!tab){tab=document.createElement('button');tab.id='cew-layout-structure-tab';tab.type='button';tab.textContent='Struttura';tab.setAttribute('role','tab');tab.addEventListener('click',showStructure);tabs.insertBefore(tab,tabs.firstChild)}
  let p=ce('cew-layout-phase-panel');if(!p){
    p=document.createElement('section');p.id='cew-layout-phase-panel';p.className='cew-inspector-panel';
    p.innerHTML=`<h3>Struttura della tavola</h3><span id="cew-layout-state" class="phase-state" aria-live="polite">Struttura da verificare</span><dl><dt>Proposta</dt><dd id="cew-layout-proposal">—</dd><dt>Lettura interna</dt><dd id="cew-layout-reading">—</dd><dt>Ripetizione</dt><dd id="cew-layout-repeat">—</dd><dt>Significato</dt><dd>Nessuno assegnato</dd></dl><div class="phase-actions"><button id="cew-layout-confirm" type="button">Conferma struttura</button><button id="cew-layout-alternative" type="button">Mostra alternativa</button><button id="cew-layout-teach" type="button">Insegna con un esempio</button><button id="cew-layout-reset" type="button" hidden>Rivedi struttura</button></div><div id="cew-layout-feedback" role="status" aria-live="polite" hidden></div><div id="cew-local-analysis"><strong>Analisi locale</strong><span id="cew-local-summary" class="cew-layout-muted">Prima conferma come va letta la tavola.</span><div id="cew-local-block" class="cew-layout-muted" style="margin-top:5px" hidden></div></div>`;
    body.insertBefore(p,body.firstChild);ce('cew-layout-confirm').addEventListener('click',confirm);ce('cew-layout-alternative').addEventListener('click',alternative);ce('cew-layout-teach').addEventListener('click',()=>ce('preview-teach-layout')?.click());ce('cew-layout-reset').addEventListener('click',reset);
  }
  updatePanel();
}
function feedback(text){const el=ce('cew-layout-feedback');if(!el)return;el.textContent=text;el.hidden=!text}
function updatePanel(){
  decorateUnits();const d=describe();setText('cew-layout-proposal',d.label);setText('cew-layout-reading',d.reading);setText('cew-layout-repeat',d.repeat);
  const stateEl=ce('cew-layout-state');if(stateEl){stateEl.textContent=gate.confirmed?'Struttura confermata':'Struttura da verificare';stateEl.classList.toggle('ok',gate.confirmed)}
  setHidden('cew-layout-confirm',gate.confirmed);setHidden('cew-layout-reset',!gate.confirmed);
  let local='Prima conferma come va letta la tavola.';if(gate.confirmed)local=gate.activeUnit?`Unità ${humanUnitLabel(gate.activeUnit)}: ${gate.localCandidates.length} frammenti grafici locali rilevati.`:'Seleziona uno dei riquadri viola U1, U2, …; CEW analizzerà soltanto quella zona.';setText('cew-local-summary',local);
  const block=ce('cew-local-block'),blocked=gate.confirmed&&gate.activeUnit&&!gate.semanticReady;if(block){block.hidden=!blocked;if(blocked)block.textContent='La semantica resta bloccata: i vecchi cluster globali non vengono riutilizzati. Serve un candidato backend realmente locale.'}
  const pill=ce('cew-layout-pill');if(pill&&units().length&&pill.textContent!==d.label)pill.textContent=d.label;
}
function syncSemantics(){
  const ready=!!gate.semanticReady;document.body.dataset.cewSemanticReady=ready?'true':'false';const tab=ce('cew-decision-tab');if(tab){tab.hidden=!ready;tab.disabled=!ready;tab.title=ready?'Decisione semantica sul candidato locale':'Disponibile solo dopo struttura confermata e candidato locale collegato'}for(const id of ['pos','neg','amb','similar']){const b=ce(id);if(b&&!ready)b.disabled=true}
}
function confirm(){
  if(!units().length){feedback('Nessuna unità di lettura disponibile da confermare.');return}
  gate.confirmed=true;gate.phase=LAYOUT_CONFIRMED;writeConfirmed(true);document.body.dataset.cewLayoutPhase='confirmed';updatePanel();feedback(confirmedGuidance());showStructure();syncSemantics();
}
function reset(){gate.confirmed=false;gate.phase=LAYOUT_UNCONFIRMED;gate.activeUnit=null;gate.localCandidates=[];gate.semanticReady=false;writeConfirmed(false);document.body.dataset.cewLayoutPhase='unconfirmed';clearLocal();feedback('');updatePanel();showStructure();syncSemantics()}
function alternative(){window.CEWLayoutLearning?.cycle?.();gate.activeUnit=null;gate.localCandidates=[];gate.semanticReady=false;clearLocal();feedback('Alternativa di impaginazione mostrata; verificala prima della conferma.');setTimeout(()=>{updatePanel();showStructure();syncSemantics()},50)}

function imageMatrix(maxSide=760){
  const img=ce('page');if(!img||img.hidden||!img.naturalWidth||!img.naturalHeight)return null;const s=Math.min(1,maxSide/Math.max(img.naturalWidth,img.naturalHeight)),w=Math.max(80,Math.round(img.naturalWidth*s)),h=Math.max(80,Math.round(img.naturalHeight*s));const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d',{willReadFrequently:true});if(!x)return null;x.drawImage(img,0,0,w,h);const d=x.getImageData(0,0,w,h).data,l=new Uint8Array(w*h);let sum=0;for(let i=0,p=0;i<d.length;i+=4,p++){const v=Math.round(.2126*d[i]+.7152*d[i+1]+.0722*d[i+2]);l[p]=v;sum+=v}const t=clamp(sum/Math.max(1,l.length)-24,115,226),ink=new Uint8Array(w*h);for(let i=0;i<l.length;i++)ink[i]=l[i]<t?1:0;return {w,h,ink}
}
function localFragments(u){
  const m=imageMatrix();if(!m)return [];const x0=clamp(Math.floor(u.x*m.w),0,m.w-1),x1=clamp(Math.ceil((u.x+u.w)*m.w),1,m.w),y0=clamp(Math.floor(u.y*m.h),0,m.h-1),y1=clamp(Math.ceil((u.y+u.h)*m.h),1,m.h),W=x1-x0,H=y1-y0;if(W<6||H<6)return [];const a=new Uint8Array(W*H);for(let y=0;y<H;y++)for(let x=0;x<W;x++)a[y*W+x]=m.ink[(y+y0)*m.w+x+x0];const dil=new Uint8Array(a.length);for(let y=0;y<H;y++)for(let x=0;x<W;x++)if(a[y*W+x])for(let yy=Math.max(0,y-1);yy<=Math.min(H-1,y+1);yy++)for(let xx=Math.max(0,x-1);xx<=Math.min(W-1,x+1);xx++)dil[yy*W+xx]=1;const seen=new Uint8Array(dil.length),out=[];for(let p=0;p<dil.length;p++){if(!dil[p]||seen[p])continue;const q=[p];seen[p]=1;let k=0,minx=W,miny=H,maxx=0,maxy=0,n=0;while(k<q.length){const z=q[k++],x=z%W,y=Math.floor(z/W);n++;minx=Math.min(minx,x);maxx=Math.max(maxx,x);miny=Math.min(miny,y);maxy=Math.max(maxy,y);for(let yy=Math.max(0,y-1);yy<=Math.min(H-1,y+1);yy++)for(let xx=Math.max(0,x-1);xx<=Math.min(W-1,x+1);xx++){const j=yy*W+xx;if(dil[j]&&!seen[j]){seen[j]=1;q.push(j)}}}const bw=maxx-minx+1,bh=maxy-miny+1,rel=bw*bh/(W*H);if(n>=8&&bw>=3&&bh>=2&&rel<=.72)out.push({x:(x0+minx)/m.w,y:(y0+miny)/m.h,w:bw/m.w,h:bh/m.h,pixels:n})}if(!out.length)return [{id:'LF-1',x:u.x,y:u.y,w:u.w,h:u.h,pixels:0,fallback:true}];return out.sort((a,b)=>b.pixels-a.pixels).slice(0,36).map((r,i)=>({...r,id:`LF-${i+1}`}))
}
function overlay(){const stage=ce('page-stage');if(!stage)return null;let el=ce('cew-local-overlay');if(!el){el=document.createElement('div');el.id='cew-local-overlay';stage.appendChild(el)}return el}
function clearLocal(){const el=ce('cew-local-overlay');if(el&&el.childNodes.length)el.replaceChildren()}
function renderLocal(){const el=overlay();if(!el)return;el.replaceChildren();for(const r of gate.localCandidates){const b=document.createElement('div');b.className='cew-local-fragment';b.style.left=`${r.x*100}%`;b.style.top=`${r.y*100}%`;b.style.width=`${r.w*100}%`;b.style.height=`${r.h*100}%`;el.appendChild(b)}}
function backendCandidateFor(u){if(typeof state==='undefined'||!state?.teaching_enabled)return null;const area=Math.max(.001,u.w*u.h);for(const c of state.clusters||[]){const r=c?.representative?.bbox;if(!r)continue;const cx=r.x+r.w/2,cy=r.y+r.h/2;if(cx>=u.x&&cx<=u.x+u.w&&cy>=u.y&&cy<=u.y+u.h&&r.w*r.h<=area*1.35)return c}return null}
function selectUnit(id){
  if(!gate.confirmed)return false;const u=units().find(x=>x.id===id);if(!u)return false;gate.activeUnit=id;gate.localCandidates=localFragments(u);renderLocal();const c=backendCandidateFor(u);gate.semanticReady=!!c;if(c){if(typeof clusterId!=='undefined')clusterId=c.cluster_id;if(typeof clusters==='function')clusters();if(typeof selected==='function')selected()}feedback(`Unità ${humanUnitLabel(id)} selezionata. Analisi locale avviata su questa sola zona.`);updatePanel();showStructure();syncSemantics();return true
}
function syncKey(){
  const next=`${session||''}:${currentPreviewPageIndex||0}:${ce('project')?.value||''}:${ce('source')?.value||''}`;if(next===gate.lastKey)return false;gate.lastKey=next;gate.confirmed=readConfirmed();gate.phase=gate.confirmed?LAYOUT_CONFIRMED:LAYOUT_UNCONFIRMED;gate.activeUnit=null;gate.localCandidates=[];gate.semanticReady=false;clearLocal();document.body.dataset.cewLayoutPhase=gate.confirmed?'confirmed':'unconfirmed';feedback('');return true
}
function sync(){if(gate.syncing)return;gate.syncing=true;requestAnimationFrame(()=>{gate.syncing=false;syncKey();ensurePanel();updatePanel();if(gate.confirmed&&!gate.activeUnit)feedback(confirmedGuidance());syncSemantics()})}
document.addEventListener('pointerup',e=>{const u=e.target.closest?.('#cew-layout-overlay .cew-layout-unit');if(!u||!gate.confirmed)return;selectUnit(u.dataset.layoutUnit)},true);
document.addEventListener('click',e=>{const d=e.target.closest?.('#cew-decision-tab');if(d&&!gate.semanticReady){e.preventDefault();e.stopImmediatePropagation();showStructure()}},true);
const obs=new MutationObserver(records=>{for(const r of records){if(r.target?.closest?.('#cew-layout-phase-panel'))continue;sync();break}});obs.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden','class','style']});window.addEventListener('resize',sync,{passive:true});sync();
window.CEWLayoutPhaseGate={state:()=>({phase:gate.phase,confirmed:gate.confirmed,activeUnit:gate.activeUnit,localCandidateCount:gate.localCandidates.length,semanticReady:gate.semanticReady,semanticGate:SEMANTIC_GATE}),confirm,reset,selectUnit,describe,decorateUnits};
})();
</script>'''


def _patched_page() -> str:
    html = layout_learning._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_LAYOUT_PHASE_GATE_HTML_MARKER_MISSING")
    html = html.replace("</head>", _STYLE + "</head>", 1)
    html = html.replace("</body>", _SCRIPT + "</body>", 1)
    return html


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def layout_phase_page():
        return HTMLResponse(
            _patched_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
                "X-CEW-Layout-Phase-Gate": "LAYOUT_CONFIRM_BEFORE_SEMANTICS_V3",
                "X-CEW-Layout-Unit-Selection": "PHASE_GATE_POINTER_V2",
                "X-CEW-Local-Unit-Analysis": "BROWSER_GRAPHIC_FRAGMENTS_V1",
                "X-CEW-Semantic-Gate": "LOCAL_BACKEND_CANDIDATE_REQUIRED_V1",
            },
        )

    return router
