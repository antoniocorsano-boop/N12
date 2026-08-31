#!/usr/bin/env python3
from __future__ import annotations

import cew_ews4_oa_result_review_runtime as ews4_runtime
import cew_enterprise_governed_resume_runtime as resume_runtime

EWS1_RUNTIME_MARKER = "CEW_EWS1_VIEWPORT_BOUND_APPLICATION_FRAME"
EWS11_RUNTIME_MARKER = "CEW_EWS11_RESIZABLE_PROFESSIONAL_FRAME"
OA_PILOT_TASK = "OA-N12-G4-COLUMN-PILOT"


def _downstream(rendered: str, task: str) -> str:
    return resume_runtime.augment(ews4_runtime.augment(rendered, task), task)


def augment(rendered: str, task: str) -> str:
    """Apply the EWS-1 application frame without changing CEW domain semantics.

    EWS-1.1 adds a user-resizable context rail and deterministic utility-popover
    layering. Rail width is UI preference only; it never enters governed state.
    """
    if EWS1_RUNTIME_MARKER in rendered:
        return _downstream(rendered, task)

    style = '''
<style id="cew-ews1-application-frame-style">
/* CEW EWS-1 / EWS-1.1 — Enterprise application frame. Presentation only. */
:root{--ews-context-rail-width:400px;--ews-splitter-width:10px}
@media (min-width:901px){
  html{height:100%;overflow:hidden}
  body.ews1-frame{height:100dvh;min-height:100dvh;max-height:100dvh;overflow:hidden}
  body.ews1-frame .app-header,
  body.ews1-frame .tools,
  body.ews1-frame .bottom-status{flex:0 0 auto}
  body.ews1-frame .app-header{min-height:52px}
  body.ews1-frame .tools{min-height:45px;flex-wrap:nowrap;overflow-x:auto;overflow-y:hidden;scrollbar-width:thin}
  body.ews1-frame #workspace.workspace{flex:1 1 auto;height:auto;min-height:0;max-height:none;overflow:hidden;align-items:stretch;position:relative}
  body.ews1-frame #workspace>.pane,
  body.ews1-frame #workspace>.inspector{min-height:0;height:100%;max-height:100%}
  body.ews1-frame #workspace>.pane{overflow:hidden}
  body.ews1-frame #workspace>.inspector{overflow:auto;overscroll-behavior:contain}
  body.ews1-frame .source-pane,body.ews1-frame .technical-pane{contain:layout paint}
  body.ews1-frame #sourceViewport,body.ews1-frame #technicalViewport{min-height:0}
  body.ews1-frame .bottom-status{position:relative;z-index:70;white-space:nowrap;overflow-x:auto;overflow-y:hidden}

  /* Utility popovers must never be occluded by the context rail. */
  body.ews1-frame #layerPop{
    position:fixed!important;top:108px!important;right:calc(var(--ews-context-rail-width) + 18px)!important;
    left:auto!important;z-index:240!important;max-height:calc(100dvh - 160px);overflow:auto
  }

  /* OA pilot: one stable canvas + one independently scrolling, resizable rail. */
  body.ews1-frame.oa-human-first #workspace.workspace,
  body.ews1-frame.oa-human-first.mode-source #workspace.workspace,
  body.ews1-frame.oa-human-first.mode-source #workspace.workspace.inspector-open{
    grid-template-columns:minmax(0,1fr) var(--ews-context-rail-width)!important;
    grid-template-rows:minmax(0,1fr)!important;gap:0!important
  }
  body.ews1-frame.oa-human-first .source-pane{grid-column:1;grid-row:1;width:auto;height:100%!important;min-height:0!important;overflow:hidden!important}
  body.ews1-frame.oa-human-first #sourceViewport{position:absolute!important;inset:0!important;width:auto!important;height:auto!important;min-height:0!important}
  body.ews1-frame.oa-human-first #oaPanel{
    grid-column:2;grid-row:1;align-self:stretch;position:relative!important;inset:auto!important;width:auto!important;
    height:auto!important;min-height:0!important;max-height:100%!important;overflow-x:hidden!important;overflow-y:auto!important;
    overscroll-behavior:contain;scrollbar-gutter:stable;border-left:1px solid var(--line)!important
  }
  body.ews1-frame.oa-human-first #oaPanel>*{min-width:0}
  body.ews1-frame.oa-human-first #oaPilotTray{max-height:240px!important;overflow:auto!important;overscroll-behavior:contain}

  #ews1RailSplitter{
    position:absolute;top:0;bottom:0;z-index:190;width:var(--ews-splitter-width);
    right:calc(var(--ews-context-rail-width) - (var(--ews-splitter-width) / 2));
    cursor:col-resize;touch-action:none;background:transparent;border:0;padding:0
  }
  #ews1RailSplitter::before{content:"";position:absolute;left:4px;top:0;bottom:0;width:2px;background:#aeb9c2;opacity:.38;transition:opacity .12s,background .12s}
  #ews1RailSplitter:hover::before,#ews1RailSplitter:focus-visible::before,#ews1RailSplitter.dragging::before{opacity:1;background:var(--accent)}
  #ews1RailSplitter:focus-visible{outline:3px solid var(--focus);outline-offset:-2px}
  body.ews1-frame.ews-resizing,body.ews1-frame.ews-resizing *{cursor:col-resize!important;user-select:none!important}
}
</style>'''
    rendered = rendered.replace("</head>", style + "</head>", 1)

    task_json = repr(task)
    script = f'''
<script id="cew-ews1-application-frame-script" data-ews1-runtime="{EWS1_RUNTIME_MARKER}" data-ews11-runtime="{EWS11_RUNTIME_MARKER}">
(() => {{
  const EWS1_MARKER={EWS1_RUNTIME_MARKER!r};
  const EWS11_MARKER={EWS11_RUNTIME_MARKER!r};
  const TASK_ID={task_json};
  const PREF_KEY='cew-ui:context-rail-width';
  const DEFAULT_RAIL=400,MIN_RAIL=280,MAX_RAIL=640,MIN_CANVAS_RATIO=.55;
  document.body.classList.add('ews1-frame');
  document.body.dataset.ews1ApplicationFrame=EWS1_MARKER;
  document.body.dataset.ews11ResizableFrame=EWS11_MARKER;
  document.body.dataset.ews1Task=TASK_ID;
  const workspace=document.getElementById('workspace');
  if(workspace) workspace.dataset.ews1Frame='VIEWPORT_BOUND';
  const rail=document.getElementById('oaPanel');
  if(rail) rail.dataset.ews1Overflow='INDEPENDENT_SCROLL';
  const source=document.querySelector('.source-pane');
  if(source) source.dataset.ews1Canvas='STABLE_PRIMARY_SURFACE';

  function clampRail(px){{
    const w=workspace?.getBoundingClientRect().width||window.innerWidth;
    const dynamicMax=Math.max(MIN_RAIL,Math.min(MAX_RAIL,w*(1-MIN_CANVAS_RATIO)));
    return Math.round(Math.max(MIN_RAIL,Math.min(dynamicMax,Number(px)||DEFAULT_RAIL)));
  }}
  function publishFrameState(){{
    const frame={{
      state:'EWS1_APPLICATION_FRAME_ACTIVE',task:TASK_ID,
      viewport_height:window.visualViewport?.height||window.innerHeight,
      viewport_width:window.visualViewport?.width||window.innerWidth,
      page_growth_from_context_rail:false,context_rail_independent_scroll:true,
      context_rail_resizable:TASK_ID==={OA_PILOT_TASK!r},
      context_rail_width_px:Number(document.body.dataset.ewsContextRailWidth||DEFAULT_RAIL),
      ui_preference_authority:'NONE',source_content_obstruction:false,
      utility_popovers_above_context_rail:true,
      canonical_write_authorized:false,engineering_authority_effect:'NONE'
    }};
    window.__CEW_EWS1_FRAME__=frame;
    window.dispatchEvent(new CustomEvent('cew:ews1-frame-ready',{{detail:frame}}));
  }}
  function positionUtilities(){{const pop=document.getElementById('layerPop');if(pop)pop.dataset.ewsUtilityLayer='FLOAT_ABOVE_FRAME'}}
  function applyRailWidth(px,persist=false){{
    if(TASK_ID!=={OA_PILOT_TASK!r})return;
    const width=clampRail(px);
    document.documentElement.style.setProperty('--ews-context-rail-width',width+'px');
    document.body.dataset.ewsContextRailWidth=String(width);
    if(persist){{try{{localStorage.setItem(PREF_KEY,String(width))}}catch(e){{}}}}
    positionUtilities();publishFrameState();
  }}
  function storedRailWidth(){{try{{return Number(localStorage.getItem(PREF_KEY)||DEFAULT_RAIL)}}catch(e){{return DEFAULT_RAIL}}}}
  function installSplitter(){{
    if(TASK_ID!=={OA_PILOT_TASK!r}||!workspace||!rail||document.getElementById('ews1RailSplitter'))return;
    const splitter=document.createElement('button');
    splitter.id='ews1RailSplitter';splitter.type='button';splitter.setAttribute('aria-label','Ridimensiona pannello laterale');
    splitter.setAttribute('aria-orientation','vertical');splitter.title='Trascina per allargare o restringere il pannello. Doppio clic: larghezza standard.';
    workspace.appendChild(splitter);let active=false;
    const move=(ev)=>{{if(!active)return;const rect=workspace.getBoundingClientRect();applyRailWidth(rect.right-ev.clientX,false)}};
    const stop=()=>{{if(!active)return;active=false;splitter.classList.remove('dragging');document.body.classList.remove('ews-resizing');applyRailWidth(Number(document.body.dataset.ewsContextRailWidth||DEFAULT_RAIL),true);window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',stop)}};
    splitter.addEventListener('pointerdown',ev=>{{active=true;splitter.classList.add('dragging');document.body.classList.add('ews-resizing');splitter.setPointerCapture?.(ev.pointerId);window.addEventListener('pointermove',move);window.addEventListener('pointerup',stop)}});
    splitter.addEventListener('dblclick',()=>applyRailWidth(DEFAULT_RAIL,true));
    splitter.addEventListener('keydown',ev=>{{const current=Number(document.body.dataset.ewsContextRailWidth||DEFAULT_RAIL);if(ev.key==='ArrowLeft'){{ev.preventDefault();applyRailWidth(current+24,true)}}else if(ev.key==='ArrowRight'){{ev.preventDefault();applyRailWidth(current-24,true)}}else if(ev.key==='Home'){{ev.preventDefault();applyRailWidth(DEFAULT_RAIL,true)}}}});
  }}
  if(TASK_ID==={OA_PILOT_TASK!r}){{applyRailWidth(storedRailWidth(),false);installSplitter()}}
  positionUtilities();publishFrameState();
  window.visualViewport?.addEventListener('resize',()=>{{applyRailWidth(Number(document.body.dataset.ewsContextRailWidth||DEFAULT_RAIL),false);publishFrameState()}},{{passive:true}});
  window.addEventListener('resize',()=>applyRailWidth(Number(document.body.dataset.ewsContextRailWidth||DEFAULT_RAIL),false),{{passive:true}});
}})();
</script>'''
    rendered = rendered.replace("</body>", script + "</body>", 1)
    return _downstream(rendered, task)
