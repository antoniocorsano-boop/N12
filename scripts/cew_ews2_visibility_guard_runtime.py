#!/usr/bin/env python3
from __future__ import annotations

EWS2_VISIBILITY_GUARD_MARKER = "CEW_EWS2_POST_ORCHESTRATION_VISIBILITY_GUARD"


def augment(rendered: str, task: str) -> str:
    if EWS2_VISIBILITY_GUARD_MARKER in rendered:
        return rendered
    style = r'''
<style id="cew-ews2-post-orchestration-visibility-guard">
@media (min-width:901px){
  /* Default after DOM reparenting: every lifecycle form is hidden. */
  body.ews2-focused-rail #ews2RailBody>#oaTeach,
  body.ews2-focused-rail #ews2RailBody>#oaSimilar,
  body.ews2-focused-rail #ews2RailBody>#oaClusterReview,
  body.ews2-focused-rail #ews2RailBody>#oaStructuralResolver,
  body.ews2-focused-rail #ews2RailBody>#oaG5Review{display:none!important}

  /* Exactly one presentation-owned work panel can become visible. */
  body.ews2-focused-rail.ews2-mode-acquire #ews2RailBody>#oaTeach{display:block!important}
  body.ews2-focused-rail.ews2-mode-find #ews2RailBody>#oaSimilar{display:block!important}
  body.ews2-focused-rail.ews2-mode-review #ews2RailBody>#oaSimilar{display:block!important}
  body.ews2-focused-rail.ews2-mode-resolve #ews2RailBody>#oaStructuralResolver{display:block!important}
  body.ews2-focused-rail.ews2-mode-validate #ews2RailBody>#oaG5Review{display:block!important}

  /* OA-4 remains an invisible persistence adapter used by EWS-4. */
  body.ews2-focused-rail #ews2RailBody>#oaClusterReview{display:none!important}
}
</style>
<script id="cew-ews2-post-orchestration-visibility-script" data-ews2-visibility-guard="CEW_EWS2_POST_ORCHESTRATION_VISIBILITY_GUARD">
(() => {
  window.__CEW_EWS2_VISIBILITY_GUARD__={
    state:'ACTIVE',
    invariant:'ONE_PRIMARY_WORK_PANEL_AT_A_TIME',
    oa4_persistence_owner_visible:false,
    canonical_write_authorized:false,
    engineering_authority_effect:'NONE'
  };
})();
</script>'''
    return rendered.replace("</body>", style + "</body>", 1)
