#!/usr/bin/env python3
from __future__ import annotations

import cew_ews4_oa_result_review_runtime as ews4_runtime
import cew_enterprise_governed_resume_runtime as resume_runtime

EWS1_RUNTIME_MARKER = "CEW_EWS1_VIEWPORT_BOUND_APPLICATION_FRAME"
OA_PILOT_TASK = "OA-N12-G4-COLUMN-PILOT"


def _downstream(rendered: str, task: str) -> str:
    return resume_runtime.augment(ews4_runtime.augment(rendered, task), task)


def augment(rendered: str, task: str) -> str:
    """Apply the EWS-1 application frame without changing CEW domain semantics.

    The frame is viewport-bound on professional desktop sizes. Canvas and contextual
    surfaces own independent overflow. The OA G4 pilot additionally keeps the source
    canvas primary because source position remains UNREGISTERED. EWS-4 is composed
    after the frame as a presentation adapter over existing OA-3/OA-4 behavior; the
    governed resume adapter is last so login/reload restores browser cache from the
    append-only ledger without creating a second decision.
    """
    if EWS1_RUNTIME_MARKER in rendered:
        return _downstream(rendered, task)

    style = '''
<style id="cew-ews1-application-frame-style">
/* CEW EWS-1 — Enterprise application frame. Structural layout only. */
@media (min-width:901px){
  html{height:100%;overflow:hidden}
  body.ews1-frame{height:100dvh;min-height:100dvh;max-height:100dvh;overflow:hidden}
  body.ews1-frame .app-header,
  body.ews1-frame .tools,
  body.ews1-frame .bottom-status{flex:0 0 auto}
  body.ews1-frame .app-header{min-height:52px}
  body.ews1-frame .tools{min-height:45px;flex-wrap:nowrap;overflow-x:auto;overflow-y:hidden;scrollbar-width:thin}
  body.ews1-frame #workspace.workspace{
    flex:1 1 auto;
    height:auto;
    min-height:0;
    max-height:none;
    overflow:hidden;
    align-items:stretch;
  }
  body.ews1-frame #workspace>.pane,
  body.ews1-frame #workspace>.inspector{
    min-height:0;
    height:100%;
    max-height:100%;
  }
  body.ews1-frame #workspace>.pane{overflow:hidden}
  body.ews1-frame #workspace>.inspector{overflow:auto;overscroll-behavior:contain}
  body.ews1-frame .source-pane,
  body.ews1-frame .technical-pane{contain:layout paint}
  body.ews1-frame #sourceViewport,
  body.ews1-frame #technicalViewport{min-height:0}
  body.ews1-frame .bottom-status{position:relative;z-index:70;white-space:nowrap;overflow-x:auto;overflow-y:hidden}

  /* OA pilot: one stable canvas + one independently scrolling context rail. */
  body.ews1-frame.oa-human-first #workspace.workspace,
  body.ews1-frame.oa-human-first.mode-source #workspace.workspace,
  body.ews1-frame.oa-human-first.mode-source #workspace.workspace.inspector-open{
    grid-template-columns:minmax(0,1fr) clamp(320px,30vw,440px)!important;
    grid-template-rows:minmax(0,1fr)!important;
    gap:0!important;
  }
  body.ews1-frame.oa-human-first .source-pane{
    grid-column:1;
    grid-row:1;
    width:auto;
    height:100%!important;
    min-height:0!important;
    overflow:hidden!important;
  }
  body.ews1-frame.oa-human-first #sourceViewport{
    position:absolute!important;
    inset:0!important;
    width:auto!important;
    height:auto!important;
    min-height:0!important;
  }
  body.ews1-frame.oa-human-first #oaPanel{
    grid-column:2;
    grid-row:1;
    align-self:stretch;
    position:relative!important;
    inset:auto!important;
    width:auto!important;
    height:auto!important;
    min-height:0!important;
    max-height:100%!important;
    overflow-x:hidden!important;
    overflow-y:auto!important;
    overscroll-behavior:contain;
    scrollbar-gutter:stable;
    border-left:1px solid var(--line)!important;
  }
  body.ews1-frame.oa-human-first #oaPanel>*{min-width:0}
  body.ews1-frame.oa-human-first #oaPilotTray{max-height:240px!important;overflow:auto!important;overscroll-behavior:contain}
}
</style>'''
    rendered = rendered.replace("</head>", style + "</head>", 1)

    task_json = repr(task)
    script = f'''
<script id="cew-ews1-application-frame-script" data-ews1-runtime="{EWS1_RUNTIME_MARKER}">
(() => {{
  const EWS1_MARKER={EWS1_RUNTIME_MARKER!r};
  const TASK_ID={task_json};
  document.body.classList.add('ews1-frame');
  document.body.dataset.ews1ApplicationFrame=EWS1_MARKER;
  document.body.dataset.ews1Task=TASK_ID;
  const workspace=document.getElementById('workspace');
  if(workspace) workspace.dataset.ews1Frame='VIEWPORT_BOUND';
  const rail=document.getElementById('oaPanel');
  if(rail) rail.dataset.ews1Overflow='INDEPENDENT_SCROLL';
  const source=document.querySelector('.source-pane');
  if(source) source.dataset.ews1Canvas='STABLE_PRIMARY_SURFACE';

  function publishFrameState(){{
    const frame={{
      state:'EWS1_APPLICATION_FRAME_ACTIVE',
      task:TASK_ID,
      viewport_height:window.visualViewport?.height||window.innerHeight,
      viewport_width:window.visualViewport?.width||window.innerWidth,
      page_growth_from_context_rail:false,
      context_rail_independent_scroll:true,
      source_content_obstruction:false,
      canonical_write_authorized:false,
      engineering_authority_effect:'NONE'
    }};
    window.__CEW_EWS1_FRAME__=frame;
    window.dispatchEvent(new CustomEvent('cew:ews1-frame-ready',{{detail:frame}}));
  }}
  publishFrameState();
  window.visualViewport?.addEventListener('resize',publishFrameState,{{passive:true}});
}})();
</script>'''
    rendered = rendered.replace("</body>", script + "</body>", 1)
    return _downstream(rendered, task)
