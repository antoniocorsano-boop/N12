#!/usr/bin/env python3
"""Mature-panel refinement layer for the CEW Professional Document Workbench.

This module keeps the canonical v2 topology and validated Document Discovery
engine intact, then adds compact panel chrome, human-readable panel copy,
keyboard parity and accessibility state derived from mature workbench patterns.

It is presentation-only. It does not change acquisition, semantic, learning,
SourceVersion/Page, structural-identity or canonical-write authority.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench as base


_MATURE_PANEL_STYLE = r'''<style id="cew-mature-panel-style">
/* Mature-panel refinement: compact, contextual, document-first. */
body.cew-professional-document[data-cew-panel-quality="mature-v1"]{
  --cew-panel-head:32px;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-primary-head,
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-inspector-head{
  height:var(--cew-panel-head);
  padding:0 7px 0 10px;
  background:#f6f7f8;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-primary-head strong,
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-inspector-head strong{
  font-size:10px;
  letter-spacing:.075em;
}
.cew-panel-head-count{
  display:inline-flex;align-items:center;justify-content:center;
  min-width:20px;height:18px;padding:0 6px;border-radius:9px;
  background:#e5eaee;color:#53616b;font-size:9px;font-weight:800;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-primary-content{padding:0}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-nav-panel{padding:8px 9px 12px}
/* The panel header owns the active-view title; do not repeat it in the body. */
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-nav-panel>.cew-sidebar-title:first-child{display:none!important}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-activity-rail{padding-top:7px;gap:2px}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-activity-rail button{
  width:36px;height:36px;min-width:36px;line-height:36px;
  border-radius:6px;font-size:17px;font-weight:650;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-activity-rail button.active:before{
  top:6px;bottom:6px;width:2px;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-page-row,
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-summary-row{
  min-height:31px;padding:6px 7px;margin-bottom:2px;border-radius:4px;font-size:11px;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-kv{
  grid-template-columns:minmax(92px,.8fr) minmax(0,1.35fr);
  gap:6px 10px;font-size:11px;line-height:1.32;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-kv dt{color:#6b7780}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-kv dd{
  font-weight:650;overflow-wrap:anywhere;word-break:normal;
}
.cew-state-text[data-tone="warn"]{color:#795500}
.cew-state-text[data-tone="blocked"]{color:#8b3434}
.cew-state-text[data-tone="ok"]{color:#1f6d4b}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-empty{
  padding:22px 10px;color:#73808a;font-size:11px;line-height:1.5;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-inspector-tabs{
  height:34px;background:#fafbfc;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-inspector-tabs button{
  height:34px;padding:0 11px;font-size:10px;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-inspector-body{padding:10px 11px 14px}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-inspector-section h4{
  margin-bottom:9px;font-size:9px;letter-spacing:.09em;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-editor-bar{height:34px;padding:0 6px}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-editor-tab{padding:0 8px}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-editor-pill{height:19px;font-size:9px}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-panel-action:focus-visible,
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-activity-rail button:focus-visible,
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-inspector-tabs button:focus-visible{
  outline:2px solid #4b9ac7;outline-offset:-2px;
}
body.cew-professional-document[data-cew-panel-quality="mature-v1"] .cew-statusbar{font-variant-numeric:tabular-nums}
</style>'''


_MATURE_PANEL_SCRIPT = r'''<script id="cew-mature-panel-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
const ICONS={pages:'▤',primitives:'⌁',clusters:'◎',verify:'!'};
const HUMAN={
  'NESSUNA_REGIONE_GRAFICA_ACQUISITA':'Nessuna regione grafica acquisita',
  'EVIDENZA_GRAFICA_RILEVATA':'Evidenza grafica rilevata',
  'NESSUNA_SESSIONE':'Nessuna sessione',
  'BLOCCATO':'Bloccato',
  'CONSENTITO':'Consentito',
  'NON ASSEGNATO':'Non assegnato',
  'UMANA RICHIESTA':'Revisione umana richiesta',
  'NESSUNA AUTORITÀ AUTOMATICA':'Nessuna autorità automatica',
  'BLOCCATA':'Bloccata'
};
let syncPending=false;

function humanize(text){return HUMAN[String(text||'').trim()]||String(text||'')}
function setTextIfDifferent(el,text){if(el&&el.textContent!==text)el.textContent=text}
function setAttrIfDifferent(el,name,value){if(el&&el.getAttribute(name)!==String(value))el.setAttribute(name,String(value))}

function enhanceActivityRail(){
  const rail=ce('cew-activity-rail');if(!rail)return;
  setAttrIfDifferent(rail,'aria-label','Navigazione documento');
  for(const b of rail.querySelectorAll('button[data-nav]')){
    const id=b.dataset.nav||'',icon=ICONS[id]||'•',active=b.classList.contains('active');
    setTextIfDifferent(b,icon);
    setAttrIfDifferent(b,'aria-pressed',active?'true':'false');
    setAttrIfDifferent(b,'aria-controls',`cew-nav-${id}`);
    const label=b.getAttribute('aria-label')||b.title||id;
    const shortcut=id==='pages'?'Alt+1':id==='primitives'?'Alt+2':id==='clusters'?'Alt+3':'Alt+4';
    const title=`${label} · ${shortcut}`;
    if(b.title!==title)b.title=title;
  }
}

function syncPrimaryHeader(){
  const head=document.querySelector('.cew-primary-head'),title=ce('cew-primary-title');if(!head||!title)return;
  let count=ce('cew-primary-count');
  if(!count){count=document.createElement('span');count.id='cew-primary-count';count.className='cew-panel-head-count';head.insertBefore(count,ce('cew-hide-primary'))}
  const active=document.querySelector('.cew-nav-panel:not([hidden])');
  const sourceCount=active?.querySelector('.cew-count')?.textContent?.trim()||'';
  setTextIfDifferent(count,sourceCount);
  count.hidden=!sourceCount;
}

function humanizePanelCopy(){
  const scopes=[ce('cew-nav-verify'),ce('cew-inspector-properties'),ce('cew-inspector-provenance')].filter(Boolean);
  for(const scope of scopes){
    for(const dd of scope.querySelectorAll('dd')){
      const raw=dd.textContent.trim(),text=humanize(raw);setTextIfDifferent(dd,text);
      dd.classList.add('cew-state-text');
      const low=text.toLowerCase();
      const tone=low.includes('blocc')?'blocked':low.includes('nessuna')||low.includes('richiest')?'warn':low.includes('rilevata')||low.includes('consent')?'ok':'';
      if(tone)setAttrIfDifferent(dd,'data-tone',tone);else if(dd.hasAttribute('data-tone'))dd.removeAttribute('data-tone');
    }
  }
}

function enhanceInspectorTabs(){
  const tabs=ce('cew-inspector-tabs');if(!tabs)return;
  setAttrIfDifferent(tabs,'role','tablist');setAttrIfDifferent(tabs,'aria-label','Ispettore documento');
  for(const b of tabs.querySelectorAll('button[data-inspector]')){
    setAttrIfDifferent(b,'role','tab');
    setAttrIfDifferent(b,'aria-selected',b.classList.contains('active')?'true':'false');
    const target=b.dataset.inspector==='decision'?'cew-decision-panel':`cew-inspector-${b.dataset.inspector}`;
    setAttrIfDifferent(b,'aria-controls',target);
  }
}

function syncPanelToggleState(){
  const body=document.body,leftOpen=!body.classList.contains('cew-primary-collapsed'),rightOpen=!body.classList.contains('cew-aux-collapsed');
  setAttrIfDifferent(ce('cew-toggle-primary'),'aria-expanded',leftOpen?'true':'false');
  setAttrIfDifferent(ce('cew-toggle-aux'),'aria-expanded',rightOpen?'true':'false');
}

function syncSash(sash,min,max){
  if(!sash)return;const rect=sash.id==='cew-left-sash'?document.querySelector('aside.left')?.getBoundingClientRect():document.querySelector('aside.right')?.getBoundingClientRect();
  setAttrIfDifferent(sash,'aria-orientation','vertical');setAttrIfDifferent(sash,'aria-valuemin',min);setAttrIfDifferent(sash,'aria-valuemax',max);
  if(rect)setAttrIfDifferent(sash,'aria-valuenow',Math.round(rect.width));
}
function syncSashes(){syncSash(ce('cew-left-sash'),220,500);syncSash(ce('cew-right-sash'),260,560)}

function activateRailIndex(index){
  const buttons=[...document.querySelectorAll('#cew-activity-rail button[data-nav]')];const b=buttons[index];if(b){b.click();b.focus()}
}

function installMatureKeyboard(){
  if(document.body.dataset.cewMatureKeys==='1')return;document.body.dataset.cewMatureKeys='1';
  document.addEventListener('keydown',e=>{
    if((e.ctrlKey||e.metaKey)&&!e.altKey&&!e.shiftKey&&e.key.toLowerCase()==='j'){
      e.preventDefault();ce('cew-toggle-aux')?.click();scheduleSync();return;
    }
    if(e.altKey&&!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&['1','2','3','4'].includes(e.key)){
      e.preventDefault();activateRailIndex(Number(e.key)-1);scheduleSync();return;
    }
    const rail=document.activeElement?.closest?.('#cew-activity-rail');
    if(rail&&(e.key==='ArrowDown'||e.key==='ArrowUp')){
      const buttons=[...rail.querySelectorAll('button[data-nav]')],i=buttons.indexOf(document.activeElement);if(i<0)return;
      e.preventDefault();buttons[(i+(e.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length].focus();
    }
  });
}

function wireSashRefresh(){
  for(const s of [ce('cew-left-sash'),ce('cew-right-sash')].filter(Boolean)){
    if(s.dataset.cewMatureWired==='1')continue;s.dataset.cewMatureWired='1';
    for(const evt of ['pointermove','pointerup','keydown','dblclick'])s.addEventListener(evt,()=>requestAnimationFrame(syncSashes));
  }
}

function syncAll(){
  document.body.dataset.cewPanelQuality='mature-v1';
  enhanceActivityRail();syncPrimaryHeader();humanizePanelCopy();enhanceInspectorTabs();syncPanelToggleState();syncSashes();wireSashRefresh();
}
function scheduleSync(){if(syncPending)return;syncPending=true;requestAnimationFrame(()=>{syncPending=false;syncAll()})}

installMatureKeyboard();syncAll();
const observer=new MutationObserver(scheduleSync);
observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['class','hidden','style']});
window.addEventListener('resize',scheduleSync,{passive:true});
})();
</script>'''


def _patched_page() -> str:
    html = base._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_MATURE_PANEL_HTML_MARKER_MISSING")
    html = html.replace("</head>", _MATURE_PANEL_STYLE + "</head>", 1)
    html = html.replace("</body>", _MATURE_PANEL_SCRIPT + "</body>", 1)
    return html


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def mature_professional_document_page():
        return HTMLResponse(
            _patched_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
                "X-CEW-Document-Workbench": "PROFESSIONAL_V2",
                "X-CEW-Panel-Architecture": "ACTIVITY_PRIMARY_EDITOR_AUXILIARY_STATUS",
                "X-CEW-Panel-Quality": "MATURE_V1",
            },
        )

    return router
