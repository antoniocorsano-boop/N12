#!/usr/bin/env python3
"""Phase-gated layout workflow for CEW Document Discovery.

Professional interaction rule:
- establish and validate page organization first;
- inspect one reading unit locally;
- only then expose semantic teaching when a backend candidate is actually local to that unit.

The layer is deliberately non-canonical. It changes neither the governed source,
engineering authority nor structural identity.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench_layout_learning as layout_learning


_STYLE = r'''<style id="cew-layout-phase-gate-style">
body.cew-professional-document[data-cew-layout-phase="unconfirmed"] #cew-decision-tab,
body.cew-professional-document[data-cew-layout-phase="confirmed"] #cew-decision-tab{
  display:none!important;
}
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
#cew-local-analysis{margin-top:11px;padding-top:10px;border-top:1px solid #d5dbe1}
#cew-local-analysis strong{display:block;margin-bottom:4px}
#cew-local-analysis .muted{color:#68757e}
#cew-local-overlay{position:absolute;inset:0;z-index:7;pointer-events:none}
#cew-local-overlay .cew-local-fragment{position:absolute;border:2px solid #138a83;background:#138a8312;border-radius:2px}
#cew-local-overlay .cew-local-fragment.active{border-width:3px;background:#138a8320}
#cew-layout-structure-tab[aria-selected="true"]{color:#174f70;border-bottom-color:#2f88b8;background:#fff}
</style>'''


_SCRIPT = r'''<script id="cew-layout-phase-gate-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
const gate={confirmed:false,activeUnit:null,localCandidates:[],semanticReady:false,lastKey:'',syncing:false};
document.body.dataset.cewLayoutPhaseGate='v1';
document.body.dataset.cewLayoutPhase='unconfirmed';

function clamp(n,min,max){return Math.min(max,Math.max(min,Number(n)||0))}
function units(){return window.CEWLayoutLearning?.units?.()||[]}
function prototype(){return window.CEWLayoutLearning?.prototype?.()||null}
function key(){return `cew.layoutConfirmed.v1:${ce('project')?.value?.trim()||'NO_PROJECT'}:${ce('source')?.value||'NO_SOURCE'}:${currentPreviewPageIndex||0}`}
function median(values){if(!values.length)return 0;const v=[...values].sort((a,b)=>a-b),m=Math.floor(v.length/2);return v.length%2?v[m]:(v[m-1]+v[m])/2}
function unitKind(){
  const us=units();if(!us.length)return {label:'Nessuna unità proposta',reading:'da definire',repeat:'da definire'};
  const ratios=us.map(u=>Number(u.h||0)/Math.max(.001,Number(u.w||0))),r=median(ratios);
  if(r>=1.35)return {label:`${us.length} colonne di lettura candidate`,reading:'dall’alto verso il basso',repeat:'da sinistra verso destra'};
  if(r<=.74)return {label:`${us.length} fasce di lettura candidate`,reading:'da sinistra verso destra',repeat:'dall’alto verso il basso'};
  return {label:`${us.length} unità di lettura candidate`,reading:'da verificare',repeat:'da verificare'};
}
function localStorageRead(){try{return localStorage.getItem(key())==='CONFIRMED'}catch(_){return false}}
function localStorageWrite(v){try{if(v)localStorage.setItem(key(),'CONFIRMED');else localStorage.removeItem(key())}catch(_){}}

function ensurePanel(){
  const tabs=ce('cew-inspector-tabs'),body=document.querySelector('.cew-inspector-body');if(!tabs||!body)return;
  let tab=ce('cew-layout-structure-tab');
  if(!tab){
    tab=document.createElement('button');tab.id='cew-layout-structure-tab';tab.type='button';tab.textContent='Struttura';tab.setAttribute('role','tab');
    tab.onclick=()=>showStructure();tabs.insertBefore(tab,tabs.firstChild);
  }
  let panel=ce('cew-layout-phase-panel');
  if(!panel){panel=document.createElement('section');panel.id='cew-layout-phase-panel';panel.className='cew-inspector-panel';body.insertBefore(panel,body.firstChild)}
  renderPanel();
}
function showStructure(){
  for(const p of document.querySelectorAll('.cew-inspector-panel'))p.hidden=p.id!=='cew-layout-phase-panel';
  for(const b of document.querySelectorAll('#cew-inspector-tabs button')){b.classList.toggle('active',b.id==='cew-layout-structure-tab');b.setAttribute('aria-selected',b.id==='cew-layout-structure-tab'?'true':'false')}
}
function suppressLegacySemantics(){
  const decision=ce('cew-decision-tab');if(decision){decision.hidden=true;decision.disabled=true;decision.title='Disponibile solo dopo struttura confermata e candidato locale collegato al motore di apprendimento'}
  for(const id of ['pos','neg','amb','similar']){const b=ce(id);if(b)b.disabled=true}
}
function maybeEnableLegacySemantics(unit){
  gate.semanticReady=false;
  if(!gate.confirmed||!unit||typeof state==='undefined'||!state?.teaching_enabled)return;
  const area=Math.max(.001,unit.w*unit.h),inside=[];
  for(const c of state.clusters||[]){
    const r=c?.representative?.bbox;if(!r)continue;
    const cx=r.x+r.w/2,cy=r.y+r.h/2,local=cx>=unit.x&&cx<=unit.x+unit.w&&cy>=unit.y&&cy<=unit.y+unit.h&&r.w*r.h<=area*1.35;
    if(local)inside.push(c);
  }
  if(!inside.length)return;
  gate.semanticReady=true;
  const c=inside[0];
  if(typeof clusterId!=='undefined')clusterId=c.cluster_id;
  if(typeof clusters==='function')clusters();if(typeof selected==='function')selected();
  const decision=ce('cew-decision-tab');if(decision){decision.hidden=false;decision.disabled=false;decision.title='Decisione semantica sul candidato locale'}
}

function renderPanel(){
  const panel=ce('cew-layout-phase-panel');if(!panel)return;const d=unitKind(),phase=gate.confirmed?'Struttura confermata':'Struttura da verificare';
  panel.innerHTML=`<h3>Struttura della tavola</h3><span class="phase-state ${gate.confirmed?'ok':''}">${phase}</span><dl><dt>Proposta</dt><dd>${d.label}</dd><dt>Lettura interna</dt><dd>${d.reading}</dd><dt>Ripetizione</dt><dd>${d.repeat}</dd><dt>Significato</dt><dd>Nessuno assegnato</dd></dl><div class="phase-actions">${gate.confirmed?'':'<button id="cew-layout-confirm">Conferma struttura</button>'}<button id="cew-layout-alternative">Mostra alternativa</button><button id="cew-layout-teach">Insegna con un esempio</button>${gate.confirmed?'<button id="cew-layout-reset">Rivedi struttura</button>':''}</div><div id="cew-local-analysis"><strong>Analisi locale</strong><span class="muted">${gate.confirmed?(gate.activeUnit?`Unità ${gate.activeUnit}: ${gate.localCandidates.length} frammenti grafici locali rilevati.`:'Seleziona una unità; CEW analizzerà automaticamente solo quella zona.'):'Prima conferma come va letta la tavola.'}</span>${gate.confirmed&&gate.activeUnit&&!gate.semanticReady?'<div class="muted" style="margin-top:5px">La semantica resta bloccata finché i candidati locali non sono collegati al motore di apprendimento: nessun uso dei vecchi cluster globali.</div>':''}</div>`;
  ce('cew-layout-confirm')?.addEventListener('click',confirm);
  ce('cew-layout-alternative')?.addEventListener('click',()=>{window.CEWLayoutLearning?.cycle?.();gate.activeUnit=null;gate.localCandidates=[];clearLocal();setTimeout(()=>{renderPanel();showStructure()},40)});
  ce('cew-layout-teach')?.addEventListener('click',()=>ce('preview-teach-layout')?.click());
  ce('cew-layout-reset')?.addEventListener('click',reset);
}
function confirm(){
  if(!units().length)return;gate.confirmed=true;localStorageWrite(true);document.body.dataset.cewLayoutPhase='confirmed';
  renderPanel();showStructure();suppressLegacySemantics();
}
function reset(){gate.confirmed=false;gate.activeUnit=null;gate.localCandidates=[];gate.semanticReady=false;localStorageWrite(false);document.body.dataset.cewLayoutPhase='unconfirmed';clearLocal();renderPanel();showStructure();suppressLegacySemantics()}

function imageMatrix(maxSide=760){
  const img=ce('page');if(!img||img.hidden||!img.naturalWidth||!img.naturalHeight)return null;
  const scale=Math.min(1,maxSide/Math.max(img.naturalWidth,img.naturalHeight)),w=Math.max(80,Math.round(img.naturalWidth*scale)),h=Math.max(80,Math.round(img.naturalHeight*scale));
  const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d',{willReadFrequently:true});if(!ctx)return null;
  ctx.drawImage(img,0,0,w,h);const data=ctx.getImageData(0,0,w,h).data,lum=new Uint8Array(w*h);let sum=0;
  for(let i=0,p=0;i<data.length;i+=4,p++){const v=Math.round(.2126*data[i]+.7152*data[i+1]+.0722*data[i+2]);lum[p]=v;sum+=v}
  const mean=sum/Math.max(1,lum.length),thr=clamp(mean-24,115,226),ink=new Uint8Array(w*h);for(let i=0;i<lum.length;i++)ink[i]=lum[i]<thr?1:0;
  return {w,h,ink};
}
function localComponents(unit){
  const m=imageMatrix();if(!m)return [];
  const x0=clamp(Math.floor(unit.x*m.w),0,m.w-1),x1=clamp(Math.ceil((unit.x+unit.w)*m.w),1,m.w),y0=clamp(Math.floor(unit.y*m.h),0,m.h-1),y1=clamp(Math.ceil((unit.y+unit.h)*m.h),1,m.h);
  const W=x1-x0,H=y1-y0;if(W<6||H<6)return [];
  const a=new Uint8Array(W*H);for(let y=0;y<H;y++)for(let x=0;x<W;x++)a[y*W+x]=m.ink[(y+y0)*m.w+(x+x0)];
  const d=new Uint8Array(a.length);for(let y=0;y<H;y++)for(let x=0;x<W;x++){if(!a[y*W+x])continue;for(let yy=Math.max(0,y-1);yy<=Math.min(H-1,y+1);yy++)for(let xx=Math.max(0,x-1);xx<=Math.min(W-1,x+1);xx++)d[yy*W+xx]=1}
  const seen=new Uint8Array(d.length),out=[];
  for(let p=0;p<d.length;p++){
    if(!d[p]||seen[p])continue;const q=[p];seen[p]=1;let k=0,minx=W,miny=H,maxx=0,maxy=0,count=0;
    while(k<q.length){const z=q[k++],x=z%W,y=Math.floor(z/W);count++;minx=Math.min(minx,x);maxx=Math.max(maxx,x);miny=Math.min(miny,y);maxy=Math.max(maxy,y);for(let yy=Math.max(0,y-1);yy<=Math.min(H-1,y+1);yy++)for(let xx=Math.max(0,x-1);xx<=Math.min(W-1,x+1);xx++){const n=yy*W+xx;if(d[n]&&!seen[n]){seen[n]=1;q.push(n)}}}
    const bw=maxx-minx+1,bh=maxy-miny+1,rel=(bw*bh)/(W*H);if(count<8||bw<3||bh<2||rel>.72)continue;
    out.push({x:(x0+minx)/m.w,y:(y0+miny)/m.h,w:bw/m.w,h:bh/m.h,pixels:count});
  }
  return out.sort((a,b)=>b.pixels-a.pixels).slice(0,36).map((r,i)=>({...r,id:`LF-${i+1}`}));
}
function localOverlay(){const stage=ce('page-stage');if(!stage)return null;let el=ce('cew-local-overlay');if(!el){el=document.createElement('div');el.id='cew-local-overlay';stage.appendChild(el)}return el}
function clearLocal(){const el=ce('cew-local-overlay');if(el)el.innerHTML=''}
function renderLocal(){const el=localOverlay();if(!el)return;el.innerHTML='';for(const r of gate.localCandidates){const b=document.createElement('div');b.className='cew-local-fragment';b.style.left=`${r.x*100}%`;b.style.top=`${r.y*100}%`;b.style.width=`${r.w*100}%`;b.style.height=`${r.h*100}%`;el.appendChild(b)}}
function selectUnit(id){
  if(!gate.confirmed)return;const u=units().find(x=>x.id===id);if(!u)return;gate.activeUnit=id;gate.localCandidates=localComponents(u);renderLocal();maybeEnableLegacySemantics(u);renderPanel();showStructure();
}
function syncKey(){
  const next=`${session||''}:${currentPreviewPageIndex||0}:${ce('project')?.value||''}:${ce('source')?.value||''}`;if(next===gate.lastKey)return;gate.lastKey=next;gate.confirmed=localStorageRead();gate.activeUnit=null;gate.localCandidates=[];gate.semanticReady=false;clearLocal();document.body.dataset.cewLayoutPhase=gate.confirmed?'confirmed':'unconfirmed';
}
function sync(){
  if(gate.syncing)return;gate.syncing=true;requestAnimationFrame(()=>{gate.syncing=false;syncKey();ensurePanel();suppressLegacySemantics();const pill=ce('cew-layout-pill'),d=unitKind();if(pill&&units().length)pill.textContent=d.label;})
}
document.addEventListener('click',e=>{const u=e.target.closest?.('.cew-layout-unit');if(u){const id=u.dataset.layoutUnit;setTimeout(()=>selectUnit(id),0)}const dt=e.target.closest?.('#cew-decision-tab');if(dt&&!gate.semanticReady){e.preventDefault();e.stopImmediatePropagation();showStructure()}},true);
const obs=new MutationObserver(sync);obs.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden','class','style']});
window.addEventListener('resize',sync,{passive:true});sync();
window.CEWLayoutPhaseGate={state:()=>({confirmed:gate.confirmed,activeUnit:gate.activeUnit,localCandidateCount:gate.localCandidates.length,semanticReady:gate.semanticReady}),confirm,reset,selectUnit,describe:()=>unitKind()};
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
                "X-CEW-Layout-Phase-Gate": "LAYOUT_CONFIRM_BEFORE_SEMANTICS_V1",
                "X-CEW-Local-Unit-Analysis": "BROWSER_GRAPHIC_FRAGMENTS_V1",
                "X-CEW-Semantic-Gate": "LOCAL_BACKEND_CANDIDATE_REQUIRED_V1",
            },
        )

    return router
