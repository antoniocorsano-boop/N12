#!/usr/bin/env python3
from __future__ import annotations

import html

OA1_RUNTIME_MARKER = "CEW_OA1_RUNTIME_OBJECT_WORKBENCH"


def augment(rendered: str, task: str) -> str:
    """Augment the existing Professional Workbench without creating a second product.

    OA-1 is read/inspection-only. It consumes only explicit object type/state metadata
    already present in the governed technical scene. Geometry shape is never used to
    infer COLUMN/BEAM identity.
    """
    if OA1_RUNTIME_MARKER in rendered:
        return rendered

    task_escaped = html.escape(task, quote=True)
    toolbar_marker = '<button id="layersButton" aria-expanded="false">Livelli</button>'
    oa_toolbar = f'''<span class="separator"></span>
  <label for="oaType" class="status-chip"><strong>Oggetti</strong>
    <select id="oaType" aria-label="Tipologia oggetto">
      <option value="COLUMN" selected>Pilastri</option>
      <option value="BEAM">Travi</option>
      <option value="BEAM_SECTION_SYMBOL">Sezioni trave</option>
      <option value="SLAB">Solai</option>
      <option value="FOUNDATION_BEAM">Travi di fondazione</option>
      <option value="LONGITUDINAL_REBAR">Armature longitudinali</option>
      <option value="STIRRUP">Staffe</option>
      <option value="GRID_AXIS">Assi</option>
      <option value="DIMENSION">Quote</option>
      <option value="CALLOUT">Richiami</option>
      <option value="NODE">Nodi</option>
      <option value="TECHNICAL_TEXT">Testi tecnici</option>
    </select>
  </label>
  <button id="oaPanelButton" aria-expanded="false">Acquisizione oggetti</button>'''
    if toolbar_marker in rendered:
        rendered = rendered.replace(toolbar_marker, toolbar_marker + oa_toolbar, 1)

    css = '''
<style id="cew-oa1-runtime-style">
#oaPanel{position:absolute;z-index:55;right:12px;top:108px;width:min(390px,calc(100vw - 24px));max-height:calc(100vh - 160px);overflow:auto;background:#fff;border:1px solid var(--line);border-radius:9px;box-shadow:0 10px 34px rgba(0,0,0,.24);padding:12px;display:none}
#oaPanel.open{display:block}#oaPanel h2{font-size:17px;margin:2px 0 4px}#oaPanel h3{font-size:13px;margin:14px 0 6px}.oa-muted{font-size:12px;color:var(--muted)}.oa-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.oa-card{border:1px solid var(--line);border-radius:6px;padding:7px;background:#f8fafb;font-size:12px}.oa-card b{display:block;font-size:16px}.oa-list{display:grid;gap:6px}.oa-row{width:100%;text-align:left;border:1px solid var(--line);border-radius:6px;padding:7px;background:#fff}.oa-row:hover{background:#f4f7f9}.oa-state{font-size:10px;font-weight:850;letter-spacing:.04em}.oa-block{border-left:4px solid var(--danger);background:#fff3f3;padding:8px;margin:6px 0;font-size:12px}.oa-warn{border-left:4px solid var(--warn);background:#fff7e8;padding:8px;margin:6px 0;font-size:12px}.oa-ok{border-left:4px solid var(--ok);background:#edf8f1;padding:8px;margin:6px 0;font-size:12px}#oaType{margin-left:6px;border:0;background:transparent;font-weight:750;max-width:155px}.technical-object.oa-dim{opacity:.16}.technical-object.oa-active{opacity:1;filter:drop-shadow(0 0 2px rgba(23,63,95,.25))}
</style>'''
    rendered = rendered.replace('</head>', css + '</head>', 1)

    panel = f'''
<section id="oaPanel" aria-label="Acquisizione oggetti" data-oa1-runtime="{OA1_RUNTIME_MARKER}" data-task="{task_escaped}">
  <h2>Acquisizione oggetti</h2>
  <div class="oa-muted">Vista CAD operativa. La fonte originale resta autorità probatoria e si apre solo quando serve.</div>
  <h3 id="oaPassTitle">Passata: Pilastri</h3>
  <div id="oaSummary" class="oa-grid"></div>
  <h3>Famiglie</h3><div id="oaFamilies" class="oa-list"></div>
  <h3>Cosa blocca</h3><div id="oaBlockers"></div>
  <h3>Oggetti della passata</h3><div id="oaObjects" class="oa-list"></div>
  <p><button id="oaViewSource">Vedi fonte</button></p>
  <div class="authority-note">OA-1 non classifica automaticamente e non crea identità strutturale. Gli oggetti senza tipologia esplicita restano non analizzati.</div>
</section>
<script id="cew-oa1-runtime-script">
(() => {{
const OA1_MARKER={OA1_RUNTIME_MARKER!r};
const OA_LABELS={{COLUMN:'Pilastri',BEAM:'Travi',BEAM_SECTION_SYMBOL:'Sezioni trave',SLAB:'Solai',FOUNDATION_BEAM:'Travi di fondazione',LONGITUDINAL_REBAR:'Armature longitudinali',STIRRUP:'Staffe',GRID_AXIS:'Assi',DIMENSION:'Quote',CALLOUT:'Richiami',NODE:'Nodi',TECHNICAL_TEXT:'Testi tecnici'}};
const OA_STATES=['VERIFIED','PROPOSED','AMBIGUOUS','BLOCKING','NOT_ANALYZED'];
function explicitType(o){{const p=o?.properties||{{}};return o?.oa_object_type||o?.object_type||p.oa_object_type||p.object_type||p.structural_type||p.entity_type||null}}
function explicitState(o){{const p=o?.properties||{{}};const s=o?.oa_state||p.oa_state||p.object_acquisition_state||'NOT_ANALYZED';return OA_STATES.includes(String(s).toUpperCase())?String(s).toUpperCase():'NOT_ANALYZED'}}
function explicitFamily(o){{const p=o?.properties||{{}};return o?.oa_family_id||p.oa_family_id||p.object_family_id||null}}
function typedObjects(type){{return (scene?.objects||[]).filter(o=>explicitType(o)===type)}}
function updateLineEmphasis(ids){{document.querySelectorAll('.technical-object').forEach(el=>{{const active=ids.has(el.dataset.objectId);el.classList.toggle('oa-active',active);el.classList.toggle('oa-dim',ids.size>0&&!active)}})}}
function rowButton(o){{const b=document.createElement('button');b.className='oa-row';b.type='button';const state=explicitState(o),fam=explicitFamily(o)||'Famiglia non assegnata';b.innerHTML=`<span class="oa-state">${{state}}</span><br><b>${{fam}}</b><br><span>${{o.object_id}}</span>`;b.onclick=()=>{{if(typeof selectObject==='function')selectObject(o);if(typeof requestMode==='function')requestMode('TECHNICAL')}};return b}}
function renderOA1(){{if(typeof scene==='undefined'||!scene)return;const type=document.getElementById('oaType').value;const objects=typedObjects(type);const states=Object.fromEntries(OA_STATES.map(s=>[s,0]));objects.forEach(o=>states[explicitState(o)]++);document.getElementById('oaPassTitle').textContent='Passata: '+(OA_LABELS[type]||type);document.getElementById('oaSummary').innerHTML=OA_STATES.map(s=>`<div class="oa-card"><span>${{s}}</span><b>${{states[s]}}</b></div>`).join('');
const fams=new Map();objects.forEach(o=>{{const f=explicitFamily(o)||'NON_ASSEGNATA';fams.set(f,(fams.get(f)||0)+1)}});document.getElementById('oaFamilies').innerHTML=fams.size?[...fams].map(([f,n])=>`<div class="oa-card"><b>${{n}}</b>${{f}}</div>`).join(''):'<div class="oa-warn">Nessuna famiglia esplicita disponibile. OA-2 non è ancora autorizzata a crearne.</div>';
const blocking=objects.filter(o=>['BLOCKING','AMBIGUOUS','NOT_ANALYZED'].includes(explicitState(o)));let blockers='';if(!objects.length)blockers='<div class="oa-block">Nessun oggetto '+(OA_LABELS[type]||type)+' è tipizzato esplicitamente nella scena corrente. Il sistema non lo deduce dalla forma delle linee.</div>';else if(blocking.length)blockers=blocking.map(o=>`<div class="oa-block"><b>${{o.object_id}}</b> · ${{explicitState(o)}}${{explicitFamily(o)?' · '+explicitFamily(o):' · famiglia non assegnata'}}</div>`).join('');else blockers='<div class="oa-ok">Nessun blocco OA-1 visibile per gli oggetti esplicitamente tipizzati in questa scena.</div>';document.getElementById('oaBlockers').innerHTML=blockers;
const list=document.getElementById('oaObjects');list.innerHTML='';objects.forEach(o=>list.appendChild(rowButton(o)));if(!objects.length)list.innerHTML='<div class="oa-muted">Nessun oggetto disponibile per questa passata.</div>';updateLineEmphasis(new Set(objects.map(o=>o.object_id)));}}
function initOA1(){{const panel=document.getElementById('oaPanel'),btn=document.getElementById('oaPanelButton'),sel=document.getElementById('oaType');if(!panel||!btn||!sel)return;btn.onclick=()=>{{panel.classList.toggle('open');btn.setAttribute('aria-expanded',String(panel.classList.contains('open')));if(panel.classList.contains('open'))renderOA1()}};sel.onchange=renderOA1;document.getElementById('oaViewSource').onclick=()=>{{if(typeof requestMode==='function')requestMode('SOURCE')}};renderOA1();}}
let tries=0;const timer=setInterval(()=>{{tries++;if(typeof scene!=='undefined'&&scene){{clearInterval(timer);initOA1()}}else if(tries>80)clearInterval(timer)}},100);
}})();
</script>'''
    return rendered.replace('</body>', panel + '</body>', 1)
