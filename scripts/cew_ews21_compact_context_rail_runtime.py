#!/usr/bin/env python3
from __future__ import annotations

EWS21_RUNTIME_MARKER = "CEW_EWS21_COMPACT_PROFESSIONAL_RAIL"
OA_PILOT_TASK = "OA-N12-G4-COLUMN-PILOT"


def augment(rendered: str, task: str) -> str:
    """Compact the focused OA rail without changing OA semantics or persistence."""
    if EWS21_RUNTIME_MARKER in rendered or task != OA_PILOT_TASK:
        return rendered

    style = r'''
<style id="cew-ews21-compact-context-rail-style">
@media (min-width:901px){
 body.ews21-compact-rail #ews2RailHeader{padding:8px 10px;box-shadow:0 1px 0 rgba(0,0,0,.04)}
 body.ews21-compact-rail #ews2RailHeader h2{font-size:15px;margin:1px 0 5px}
 body.ews21-compact-rail #ews2PhaseMessage{margin-top:5px;font-size:10px;line-height:1.25;max-height:2.6em;overflow:hidden}
 body.ews21-compact-rail .ews2-stage-nav{gap:2px}
 body.ews21-compact-rail .ews2-stage{padding:5px 2px;font-size:9.5px}
 body.ews21-compact-rail #ews21Summary{flex:0 0 auto;background:#f7f9fa;border-bottom:1px solid var(--line);padding:7px 10px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;font-size:11px}
 body.ews21-compact-rail #ews21Summary b{display:block;font-size:12px}
 body.ews21-compact-rail #ews21Summary small{color:var(--muted)}
 body.ews21-compact-rail #ews21Summary button{padding:5px 8px;font-size:10px;white-space:nowrap}
 body.ews21-compact-rail #ews2RailBody{overflow:hidden!important;padding:8px 10px!important;display:flex;flex-direction:column;min-height:0}
 body.ews21-compact-rail #ews2RailBody>#oaTeach,
 body.ews21-compact-rail #ews2RailBody>#oaSimilar,
 body.ews21-compact-rail #ews2RailBody>#oaStructuralResolver,
 body.ews21-compact-rail #ews2RailBody>#oaG5Review{min-height:0;max-height:100%;overflow:auto;overscroll-behavior:contain;scrollbar-gutter:stable}
 body.ews21-compact-rail #oaTeach>.authority-note,
 body.ews21-compact-rail #oaSimilar>.authority-note{display:none!important}
 body.ews21-compact-rail #oaTeachResult .oa2-receipt{margin:0;padding:7px;font-size:10px}
 body.ews21-compact-rail.ews21-prototype-governed:not(.ews21-edit-example) #oaPilotTrayBlock,
 body.ews21-compact-rail.ews21-prototype-governed:not(.ews21-edit-example) #oaTeach>label,
 body.ews21-compact-rail.ews21-prototype-governed:not(.ews21-edit-example) #oaTeachCreate{display:none!important}
 body.ews21-compact-rail.ews21-prototype-governed:not(.ews21-edit-example) #oaTeach{overflow:hidden!important}
 body.ews21-compact-rail.ews21-edit-example #oaPilotTray{max-height:180px!important}
 body.ews21-compact-rail.ews2-mode-find #oaSimilar{display:flex!important;flex-direction:column;min-height:0}
 body.ews21-compact-rail.ews2-mode-find #oaSimilarResult{min-height:0;overflow:auto}
 body.ews21-compact-rail.ews2-mode-review #oaSimilar{display:grid!important;grid-template-rows:auto minmax(120px,.42fr) minmax(220px,.58fr);min-height:0;overflow:hidden!important;gap:7px}
 body.ews21-compact-rail.ews2-mode-review #oaSimilarResult{display:contents}
 body.ews21-compact-rail.ews2-mode-review .ews4-summary{grid-row:1}
 body.ews21-compact-rail.ews2-mode-review .ews4-set{grid-row:2;max-height:none!important;min-height:0;overflow:auto!important}
 body.ews21-compact-rail.ews2-mode-review .ews4-active{grid-row:3;min-height:0;overflow:auto;margin:0!important;border-top:1px solid var(--line);padding-top:7px}
 body.ews21-compact-rail .ews4-reasons{max-height:58px!important;overflow:auto}
 body.ews21-compact-rail .ews3-provenance{font-size:9px}
 body.ews21-compact-rail #ews2Advance,
 body.ews21-compact-rail #ews2ValidateAdvance{position:sticky;bottom:0;z-index:6;background:var(--accent);box-shadow:0 -6px 10px rgba(255,255,255,.92)}
}
</style>'''
    rendered = rendered.replace("</head>", style + "</head>", 1)

    script = f'''
<script id="cew-ews21-compact-context-rail-script" data-ews21-runtime="{EWS21_RUNTIME_MARKER}">
(() => {{
const MARKER={EWS21_RUNTIME_MARKER!r};
if(TASK!=={OA_PILOT_TASK!r})return;
let editExample=false;
function readJson(key){{try{{return JSON.parse(sessionStorage.getItem(key)||'null')}}catch(e){{return null}}}}
function latestPrototype(){{const prefix='cew-oa2:'+TASK+':';let hit=null;for(let i=0;i<sessionStorage.length;i++){{const k=sessionStorage.key(i);if(!k||!k.startsWith(prefix))continue;const row=readJson(k);if(row?.governed_receipt_id)hit=row}}return hit}}
function currentMode(){{return window.__CEW_EWS2_RAIL__?.mode||'ACQUIRE'}}
function summaryFor(mode,p){{
 if(mode==='ACQUIRE')return p?{{title:(p.family_label||p.family_id||'Prototipo governato'),text:'Esempio già registrato · nessuna nuova scrittura',action:'Nuovo esempio'}}:{{title:'Nessun esempio governato',text:'Scegli un supporto e dichiarane la famiglia',action:''}};
 if(mode==='FIND_SIMILAR')return {{title:'Ricerca simili',text:p?'Prototipo '+(p.family_label||p.family_id||''):'Serve prima un prototipo',action:''}};
 if(mode==='REVIEW_SET')return {{title:'Revisione candidati',text:'Un candidato alla volta · fonte sempre visibile',action:''}};
 if(mode==='RESOLVE_IDENTITY')return {{title:'Identità strutturale',text:'Solo dopo decisioni OA-4 governate',action:''}};
 return {{title:'Validazione identità',text:'Decisione umana separata · nessuna scrittura canonica',action:''}};
}}
function ensureSummary(){{const head=document.getElementById('ews2RailHeader');if(!head)return null;let s=document.getElementById('ews21Summary');if(!s){{s=document.createElement('div');s.id='ews21Summary';head.insertAdjacentElement('afterend',s)}}return s}}
function refresh(){{
 const p=latestPrototype(),mode=currentMode(),s=ensureSummary();
 document.body.classList.add('ews21-compact-rail');document.body.dataset.ews21CompactRail=MARKER;
 document.body.classList.toggle('ews21-prototype-governed',!!p);document.body.classList.toggle('ews21-edit-example',editExample);
 if(!s)return;const x=summaryFor(mode,p);s.innerHTML=`<div><b>${{x.title}}</b><small>${{x.text}}</small></div>${{x.action?'<button type="button" id="ews21ToggleExample">'+(editExample?'Chiudi modifica':x.action)+'</button>':''}}`;
 document.getElementById('ews21ToggleExample')?.addEventListener('click',()=>{{editExample=!editExample;refresh()}});
 document.querySelectorAll('#ews2RailBody details').forEach(d=>{{if(!d.dataset.ews21Touched){{d.open=false;d.dataset.ews21Touched='true'}}}});
 window.__CEW_EWS21_RAIL__={{state:'COMPACT_PROFESSIONAL_RAIL_ACTIVE',mode,prototype_governed:!!p,secondary_details_collapsed:true,canonical_write_authorized:false,engineering_authority_effect:'NONE'}};
}}
['cew:ews2-mode-change','cew:oa2-prototype-persisted','cew:governed-context-resumed','cew:enterprise-governed-resume','cew:ews4-candidate-reviewed'].forEach(e=>window.addEventListener(e,()=>setTimeout(refresh,0)));
let tries=0;const timer=setInterval(()=>{{tries++;if(document.getElementById('ews2RailHeader')&&document.getElementById('ews2RailBody')){{clearInterval(timer);refresh()}}else if(tries>160)clearInterval(timer)}},80);
}})();
</script>'''
    return rendered.replace("</body>", script + "</body>", 1)
