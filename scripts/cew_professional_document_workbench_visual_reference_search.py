#!/usr/bin/env python3
"""Reference-first visual similarity review for CEW Document Discovery.

This layer follows mature drawing-review interaction: the operator selects one
tight visual reference inside an already confirmed reading unit, explicitly
starts a search, and reviews proposed graphic matches. It does not classify the
reference, does not convert low-level components into objects, and cannot write
canonical or structural state.
"""
from __future__ import annotations

import cew_professional_document_workbench_operator_view as operator_view


_STYLE = r'''<style id="cew-visual-reference-search-style">
#cew-visual-search{margin-top:12px;padding-top:10px;border-top:1px solid #d5dbe1}
#cew-visual-search h4{margin:0 0 5px;font-size:12px;color:#263640}
#cew-visual-search .cew-visual-note{display:block;color:#6a7780;font-size:10px;line-height:1.35;margin-bottom:7px}
#cew-visual-search button{width:100%;padding:8px 9px;border:0;border-radius:5px;font-weight:750;margin-top:6px}
#cew-reference-start,#cew-reference-search{background:#1f607f;color:#fff}
#cew-reference-reset{background:#e3e9ed;color:#25353f}
#cew-visual-sensitivity-wrap{display:grid;grid-template-columns:1fr auto;gap:6px 8px;align-items:center;margin-top:8px;font-size:10px;color:#52616a}
#cew-visual-sensitivity{grid-column:1 / -1;width:100%}
#cew-visual-status{margin-top:7px;padding:7px 8px;border-radius:5px;background:#eef4f7;color:#28556b;font-size:10px;font-weight:650;line-height:1.35}
#cew-visual-results-list{display:grid;gap:4px;margin-top:7px}
#cew-visual-results-list label{display:flex;align-items:center;gap:6px;padding:5px 6px;border-radius:4px;background:#f5f7f8;font-size:10px;color:#33444e}
#cew-visual-reference-overlay,#cew-visual-select-layer{position:absolute;inset:0}
#cew-visual-reference-overlay{z-index:9;pointer-events:none}
#cew-visual-select-layer{z-index:12;pointer-events:none;cursor:crosshair}
#cew-visual-select-layer.active{pointer-events:auto}
.cew-visual-ref-box,.cew-visual-match-box,.cew-visual-drag-box{position:absolute;box-sizing:border-box;border-radius:2px}
.cew-visual-ref-box{border:3px solid #7a4aa8;background:#7a4aa80b}
.cew-visual-ref-box::after{content:'RIF';position:absolute;left:3px;top:3px;padding:1px 4px;border-radius:8px;background:#7a4aa8;color:#fff;font-size:8px;font-weight:800}
.cew-visual-match-box{border:2px dashed #16738f;background:#16738f0a}
.cew-visual-match-box::after{content:attr(data-label);position:absolute;left:3px;top:3px;padding:1px 4px;border-radius:8px;background:#16738f;color:#fff;font-size:8px;font-weight:800}
.cew-visual-match-box.rejected{display:none}
.cew-visual-drag-box{border:2px solid #7a4aa8;background:#7a4aa812}
</style>'''


_SCRIPT = r'''<script id="cew-visual-reference-search-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
const visual={activeUnit:null,mode:'IDLE',reference:null,matches:[],threshold:.74,matrix:null,matrixKey:''};
document.body.dataset.cewVisualReferenceSearch='reference-first-v1';
document.body.dataset.cewVisualSearchAuthority='none';

function units(){return window.CEWLayoutLearning?.units?.()||[]}
function phase(){return window.CEWLayoutPhaseGate?.state?.()||{confirmed:false,activeUnit:null}}
function unitById(id){return units().find(u=>u.id===id)||null}
function unitLabel(id){const n=(String(id||'').match(/(\d+)$/)||[])[1]||'?';return `U${n}`}
function clamp(n,min,max){return Math.min(max,Math.max(min,Number(n)||0))}
function stage(){return ce('page-stage')}
function image(){return ce('page')}
function setStatus(text){const el=ce('cew-visual-status');if(el){if(el.textContent!==text)el.textContent=text;const hidden=!text;if(el.hidden!==hidden)el.hidden=hidden}}

function ensureUi(){
  const host=ce('cew-local-analysis');if(!host||ce('cew-visual-search'))return;
  const box=document.createElement('section');box.id='cew-visual-search';box.hidden=true;
  box.innerHTML=`<h4>Ricerca visiva da riferimento</h4><span class="cew-visual-note">Seleziona un solo dettaglio grafico ben delimitato. CEW cercherà corrispondenze visive nelle altre unità; i risultati restano proposte da rivedere e non hanno significato strutturale.</span><button id="cew-reference-start" type="button">Seleziona riferimento visivo</button><button id="cew-reference-search" type="button" hidden>Cerca simili nelle altre unità</button><div id="cew-visual-sensitivity-wrap"><span>Somiglianza minima</span><strong id="cew-visual-sensitivity-value">74%</strong><input id="cew-visual-sensitivity" type="range" min="55" max="95" value="74" step="1"></div><button id="cew-reference-reset" type="button" hidden>Nuovo riferimento</button><div id="cew-visual-status" role="status" aria-live="polite" hidden></div><div id="cew-visual-results-list"></div>`;
  host.append(box);
  ce('cew-reference-start').addEventListener('click',startReference);
  ce('cew-reference-search').addEventListener('click',searchSimilar);
  ce('cew-reference-reset').addEventListener('click',resetReference);
  ce('cew-visual-sensitivity').addEventListener('input',e=>{visual.threshold=Number(e.target.value)/100;ce('cew-visual-sensitivity-value').textContent=`${e.target.value}%`;if(visual.matches.length)renderMatches()});
}

function ensureLayers(){
  const s=stage();if(!s)return null;
  let overlay=ce('cew-visual-reference-overlay');if(!overlay){overlay=document.createElement('div');overlay.id='cew-visual-reference-overlay';s.appendChild(overlay)}
  let selector=ce('cew-visual-select-layer');if(!selector){selector=document.createElement('div');selector.id='cew-visual-select-layer';s.appendChild(selector);wireSelector(selector)}
  return {overlay,selector};
}

function resetReference(){
  visual.mode='IDLE';visual.reference=null;visual.matches=[];
  const layers=ensureLayers();if(layers){layers.overlay.replaceChildren();layers.selector.replaceChildren();layers.selector.classList.remove('active')}
  const list=ce('cew-visual-results-list');if(list)list.replaceChildren();
  const start=ce('cew-reference-start'),search=ce('cew-reference-search'),reset=ce('cew-reference-reset');if(start)start.hidden=false;if(search)search.hidden=true;if(reset)reset.hidden=true;
  setStatus('');
}

function startReference(){
  const p=phase(),u=unitById(p.activeUnit);if(!p.confirmed||!u){setStatus('Prima conferma la struttura e seleziona una unità di lettura.');return}
  resetReference();visual.mode='SELECTING';visual.activeUnit=p.activeUnit;
  const layers=ensureLayers();if(layers)layers.selector.classList.add('active');
  ce('cew-reference-start').hidden=true;ce('cew-reference-reset').hidden=false;
  setStatus(`Disegna un rettangolo stretto attorno al riferimento dentro ${unitLabel(p.activeUnit)}.`);
}

function pointerNorm(e){const img=image(),r=img?.getBoundingClientRect();if(!r||r.width<2||r.height<2)return null;return {x:clamp((e.clientX-r.left)/r.width,0,1),y:clamp((e.clientY-r.top)/r.height,0,1)}}
function insideUnit(p,u){return p&&u&&p.x>=u.x&&p.x<=u.x+u.w&&p.y>=u.y&&p.y<=u.y+u.h}
function clampToUnit(p,u){return {x:clamp(p.x,u.x,u.x+u.w),y:clamp(p.y,u.y,u.y+u.h)}}
function boxFrom(a,b){return {x:Math.min(a.x,b.x),y:Math.min(a.y,b.y),w:Math.abs(b.x-a.x),h:Math.abs(b.y-a.y)}}
function drawTemp(rect){const selector=ce('cew-visual-select-layer');if(!selector)return;selector.replaceChildren();const b=document.createElement('div');b.className='cew-visual-drag-box';place(b,rect);selector.appendChild(b)}
function place(el,r){el.style.left=`${r.x*100}%`;el.style.top=`${r.y*100}%`;el.style.width=`${r.w*100}%`;el.style.height=`${r.h*100}%`}

function wireSelector(layer){
  let down=null;
  layer.addEventListener('pointerdown',e=>{
    if(visual.mode!=='SELECTING'||e.button!==0)return;const u=unitById(phase().activeUnit),p=pointerNorm(e);if(!insideUnit(p,u)){setStatus(`Il riferimento deve essere disegnato dentro ${unitLabel(phase().activeUnit)}.`);return}e.preventDefault();e.stopPropagation();down=clampToUnit(p,u);layer.setPointerCapture?.(e.pointerId);drawTemp({x:down.x,y:down.y,w:.001,h:.001});
  });
  layer.addEventListener('pointermove',e=>{if(!down||visual.mode!=='SELECTING')return;const u=unitById(phase().activeUnit),p=clampToUnit(pointerNorm(e),u);drawTemp(boxFrom(down,p))});
  layer.addEventListener('pointerup',e=>{
    if(!down||visual.mode!=='SELECTING')return;const u=unitById(phase().activeUnit),p=clampToUnit(pointerNorm(e),u),rect=boxFrom(down,p);down=null;layer.releasePointerCapture?.(e.pointerId);
    if(rect.w<Math.max(.008,u.w*.035)||rect.h<Math.max(.008,u.h*.035)){setStatus('Riferimento troppo piccolo: racchiudi il dettaglio grafico completo ma senza troppo spazio vuoto.');layer.replaceChildren();return}
    visual.reference=rect;visual.mode='REFERENCE_READY';layer.classList.remove('active');layer.replaceChildren();renderReference();ce('cew-reference-search').hidden=false;setStatus(`Riferimento acquisito in ${unitLabel(phase().activeUnit)}. Controlla il riquadro viola, poi avvia la ricerca.`);
  });
}

function imageMatrix(maxSide=760){
  const img=image();if(!img||img.hidden||!img.naturalWidth||!img.naturalHeight)return null;const key=`${img.src}|${img.naturalWidth}x${img.naturalHeight}`;if(visual.matrix&&visual.matrixKey===key)return visual.matrix;
  const scale=Math.min(1,maxSide/Math.max(img.naturalWidth,img.naturalHeight)),w=Math.max(100,Math.round(img.naturalWidth*scale)),h=Math.max(100,Math.round(img.naturalHeight*scale));const c=document.createElement('canvas');c.width=w;c.height=h;const ctx=c.getContext('2d',{willReadFrequently:true});if(!ctx)return null;ctx.drawImage(img,0,0,w,h);const data=ctx.getImageData(0,0,w,h).data,gray=new Uint8Array(w*h);for(let i=0,p=0;i<data.length;i+=4,p++)gray[p]=Math.round(.2126*data[i]+.7152*data[i+1]+.0722*data[i+2]);visual.matrix={w,h,gray};visual.matrixKey=key;return visual.matrix;
}
function descriptor(rect){
  const m=imageMatrix();if(!m)return null;const gx=18,gy=12,v=[];for(let yy=0;yy<gy;yy++)for(let xx=0;xx<gx;xx++){const nx=rect.x+rect.w*(xx+.5)/gx,ny=rect.y+rect.h*(yy+.5)/gy,x=clamp(Math.floor(nx*m.w),0,m.w-1),y=clamp(Math.floor(ny*m.h),0,m.h-1);v.push(m.gray[y*m.w+x])}
  const mean=v.reduce((a,b)=>a+b,0)/v.length,center=v.map(x=>x-mean),norm=Math.sqrt(center.reduce((a,b)=>a+b*b,0));if(norm<45)return null;return center.map(x=>x/norm);
}
function similarity(a,b){if(!a||!b||a.length!==b.length)return 0;let dot=0;for(let i=0;i<a.length;i++)dot+=a[i]*b[i];return clamp((dot+1)/2,0,1)}
function translatedRect(sourceUnit,targetUnit,ref,dx=0,dy=0,scale=1){
  const rx=(ref.x-sourceUnit.x)/sourceUnit.w,ry=(ref.y-sourceUnit.y)/sourceUnit.h,rw=ref.w/sourceUnit.w,rh=ref.h/sourceUnit.h,nw=targetUnit.w*rw*scale,nh=targetUnit.h*rh*scale,cx=targetUnit.x+targetUnit.w*(rx+rw/2+dx),cy=targetUnit.y+targetUnit.h*(ry+rh/2+dy);return {x:clamp(cx-nw/2,targetUnit.x,targetUnit.x+targetUnit.w-nw),y:clamp(cy-nh/2,targetUnit.y,targetUnit.y+targetUnit.h-nh),w:nw,h:nh}
}
function bestForUnit(source,target,ref,refDesc){
  let best=null;const offsets=[-.08,-.04,0,.04,.08],scales=[.92,1,1.08];for(const dy of offsets)for(const dx of offsets)for(const sc of scales){const rect=translatedRect(source,target,ref,dx,dy,sc),score=similarity(refDesc,descriptor(rect));if(!best||score>best.score)best={unitId:target.id,rect,score,accepted:true}}return best;
}

function searchSimilar(){
  const p=phase(),source=unitById(p.activeUnit),ref=visual.reference;if(!p.confirmed||!source||!ref){setStatus('Seleziona prima un riferimento visivo dentro l’unità attiva.');return}
  const refDesc=descriptor(ref);if(!refDesc){setStatus('Il riferimento contiene troppo poco segnale grafico. Ridisegna un riquadro più aderente al dettaglio.');return}
  visual.matches=[];for(const u of units()){if(u.id===source.id)continue;const best=bestForUnit(source,u,ref,refDesc);if(best)visual.matches.push(best)}visual.mode='RESULTS';renderMatches();ce('cew-reference-search').hidden=true;setStatus(resultSummary());
}
function resultSummary(){const hits=visual.matches.filter(m=>m.score>=visual.threshold).length;return hits?`${hits} corrispondenze grafiche sopra la soglia. Rivedi i riquadri azzurri e deseleziona gli esiti non pertinenti.`:'Nessuna corrispondenza supera la soglia. Puoi ridurre la somiglianza minima o scegliere un riferimento più caratteristico.'}

function renderReference(){const layers=ensureLayers();if(!layers)return;layers.overlay.replaceChildren();if(!visual.reference)return;const ref=document.createElement('div');ref.className='cew-visual-ref-box';place(ref,visual.reference);layers.overlay.appendChild(ref)}
function renderMatches(){
  renderReference();const overlay=ce('cew-visual-reference-overlay'),list=ce('cew-visual-results-list');if(!overlay||!list)return;list.replaceChildren();
  const shown=visual.matches.filter(m=>m.score>=visual.threshold).sort((a,b)=>b.score-a.score);for(const m of shown){const box=document.createElement('div');box.className='cew-visual-match-box'+(m.accepted?'':' rejected');box.dataset.unitId=m.unitId;box.dataset.label=`${unitLabel(m.unitId)} ${Math.round(m.score*100)}%`;place(box,m.rect);overlay.appendChild(box);const row=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=m.accepted;check.addEventListener('change',()=>{m.accepted=check.checked;renderMatches()});const text=document.createElement('span');text.textContent=`${unitLabel(m.unitId)} · somiglianza ${Math.round(m.score*100)}%`;row.append(check,text);list.appendChild(row)}
  if(visual.mode==='RESULTS')setStatus(resultSummary());
}

function sync(){
  ensureUi();const p=phase(),host=ce('cew-visual-search');if(!host)return;const ready=!!(p.confirmed&&p.activeUnit),desiredHidden=!ready;if(host.hidden!==desiredHidden)host.hidden=desiredHidden;
  if(!ready){if(visual.activeUnit!==null)resetReference();visual.activeUnit=null;return}
  if(visual.activeUnit&&visual.activeUnit!==p.activeUnit)resetReference();visual.activeUnit=p.activeUnit;
}
let syncScheduled=false;
function scheduleSync(){if(syncScheduled)return;syncScheduled=true;requestAnimationFrame(()=>{syncScheduled=false;sync()})}
function wrapPhaseGate(){
  const api=window.CEWLayoutPhaseGate;if(!api||api.__cewVisualReferenceWrapped)return;api.__cewVisualReferenceWrapped=true;
  if(typeof api.selectUnit==='function'){const original=api.selectUnit.bind(api);api.selectUnit=id=>{const result=original(id);queueMicrotask(sync);return result}}
}
function install(){ensureUi();wrapPhaseGate();sync()}
document.addEventListener('click',e=>{const id=e.target?.id;if(id==='cew-layout-confirm'||id==='cew-layout-reset'||id==='cew-layout-alternative')setTimeout(sync,0)},true);
const observer=new MutationObserver(mutations=>{if(mutations.some(m=>m.target===document.body&&m.attributeName==='data-cew-layout-phase'))scheduleSync()});
observer.observe(document.body,{attributes:true,attributeFilter:['data-cew-layout-phase']});
install();
window.CEWVisualReferenceSearch={state:()=>({mode:visual.mode,activeUnit:visual.activeUnit,reference:visual.reference?{...visual.reference}:null,matches:visual.matches.map(m=>({...m,rect:{...m.rect}})),threshold:visual.threshold}),start:startReference,search:searchSimilar,reset:resetReference};
})();
</script>'''


def _patched_page() -> str:
    html = operator_view._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_VISUAL_REFERENCE_SEARCH_HTML_MARKER_MISSING")
    html = html.replace("</head>", _STYLE + "</head>", 1)
    html = html.replace("</body>", _SCRIPT + "</body>", 1)
    return html
