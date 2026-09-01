#!/usr/bin/env python3
from __future__ import annotations

PR1_RUNTIME_MARKER = "CEW_PR1_ONE_SCROLL_OWNER_WORKSPACE"
OA_PILOT_TASK = "OA-N12-G4-COLUMN-PILOT"


def augment(rendered: str, task: str) -> str:
    """Enforce one vertical scroll owner in the professional context rail.

    Presentation only. Existing OA/EWS components retain semantic and persistence ownership.
    """
    if PR1_RUNTIME_MARKER in rendered or task != OA_PILOT_TASK:
        return rendered

    style = r'''
<style id="cew-pr1-one-scroll-owner-style">
@media (min-width:901px){
  body.pr1-one-scroll-owner #oaPanel{
    overflow:hidden!important;display:flex!important;flex-direction:column!important;min-height:0!important
  }
  body.pr1-one-scroll-owner #ews2RailHeader,
  body.pr1-one-scroll-owner #ews21Summary{flex:0 0 auto!important}
  body.pr1-one-scroll-owner #ews2RailBody{
    flex:1 1 auto!important;min-height:0!important;max-height:none!important;
    overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important;
    scrollbar-gutter:stable!important;display:block!important
  }

  /* ONE_SCROLL_OWNER: every descendant must yield vertical scroll to #ews2RailBody. */
  body.pr1-one-scroll-owner #ews2RailBody>#oaTeach,
  body.pr1-one-scroll-owner #ews2RailBody>#oaSimilar,
  body.pr1-one-scroll-owner #ews2RailBody>#oaStructuralResolver,
  body.pr1-one-scroll-owner #ews2RailBody>#oaG5Review,
  body.pr1-one-scroll-owner #oaSimilarResult,
  body.pr1-one-scroll-owner .ews4-set,
  body.pr1-one-scroll-owner .ews4-active,
  body.pr1-one-scroll-owner .ews4-reasons,
  body.pr1-one-scroll-owner #oaPilotTray{
    overflow:visible!important;max-height:none!important;min-height:auto!important;height:auto!important
  }

  body.pr1-one-scroll-owner.ews2-mode-review #oaSimilar{
    display:block!important;min-height:auto!important;max-height:none!important;overflow:visible!important
  }
  body.pr1-one-scroll-owner.ews2-mode-review #oaSimilarResult{display:block!important}
  body.pr1-one-scroll-owner.ews2-mode-review .ews4-set{display:grid!important;margin:7px 0!important}
  body.pr1-one-scroll-owner.ews2-mode-review .ews4-active{margin-top:8px!important;border-top:0!important;padding-top:9px!important}
  body.pr1-one-scroll-owner .ews4-reasons{max-height:none!important}

  /* Primary review actions remain reachable without becoming a second scroll container. */
  body.pr1-one-scroll-owner .ews4-actions{
    position:sticky;bottom:0;z-index:12;background:#fff;padding:8px 0 6px;margin-top:8px;
    box-shadow:0 -7px 12px rgba(255,255,255,.96)
  }
  body.pr1-one-scroll-owner #ews2Advance,
  body.pr1-one-scroll-owner #ews2ValidateAdvance{
    position:sticky!important;bottom:0!important;z-index:13!important
  }
}
</style>'''
    rendered = rendered.replace("</head>", style + "</head>", 1)

    script = f'''
<script id="cew-pr1-one-scroll-owner-script" data-pr1-runtime="{PR1_RUNTIME_MARKER}">
(() => {{
const MARKER={PR1_RUNTIME_MARKER!r};
if(TASK!=={OA_PILOT_TASK!r})return;
function install(){{
  const panel=document.getElementById('oaPanel'),body=document.getElementById('ews2RailBody');
  if(!panel||!body)return false;
  document.body.classList.add('pr1-one-scroll-owner');
  document.body.dataset.pr1OneScrollOwner=MARKER;
  panel.dataset.verticalScrollOwner='NONE';
  body.dataset.verticalScrollOwner='PRIMARY';
  document.querySelectorAll('#ews2RailBody *').forEach(el=>{{
    const cs=getComputedStyle(el);
    if(el!==body && (cs.overflowY==='auto'||cs.overflowY==='scroll')) el.dataset.pr1NestedScrollNeutralized='true';
  }});
  window.__CEW_PR1_SCROLL__={{
    state:'ONE_SCROLL_OWNER_ACTIVE',task:TASK,owner:'#ews2RailBody',nested_vertical_scroll:false,
    sticky_workmode_header:true,sticky_primary_actions:true,canonical_write_authorized:false,
    engineering_authority_effect:'NONE'
  }};
  window.dispatchEvent(new CustomEvent('cew:pr1-one-scroll-owner-ready',{{detail:window.__CEW_PR1_SCROLL__}}));
  return true;
}}
let tries=0;const timer=setInterval(()=>{{tries++;if(install())clearInterval(timer);else if(tries>160)clearInterval(timer)}},80);
}})();
</script>'''
    return rendered.replace("</body>", script + "</body>", 1)
