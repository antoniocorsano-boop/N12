#!/usr/bin/env python3
"""Professional Workbench router composition.

The historical Workbench API is preserved byte-for-byte in
cew_professional_workbench_api_base.py. This composition layer adds the governed
G4/TAV-05S OAR evidence-localization router, the additive assisted-localization
POC, the governed external-reference human review workspace, and the document-
first discovery/teaching workspace without altering existing R2HR/R2GM routes or
their authority semantics.

The delegated compatibility markers below are executable invariants, not stale
comments: import fails closed if the preserved base implementation no longer
contains the governed routes/authority boundaries expected by existing CEW
validators and runtime consumers.
"""
from __future__ import annotations

from pathlib import Path

from cew_professional_workbench_api_base import *  # noqa: F401,F403
import cew_professional_workbench_api_base as _base
import cew_oar_g4_region_workbench as _oar_g4
import cew_oar_g4_assisted_workbench as _oar_g4_assisted
import cew_external_graphic_reference_review_workbench as _reference_review
import cew_external_graphic_reference_review_hardening as _reference_review_hardening
import cew_external_graphic_reference_review_asset_hardening as _reference_review_asset_hardening
import cew_professional_document_workbench_mature_panels as _professional_document_workbench
import cew_professional_document_workbench_mature_content as _professional_document_content
import cew_professional_document_workbench_governed_async as _professional_document_governed_async
import cew_professional_document_workbench_region_guidance as _professional_document_region_guidance
import cew_professional_document_workbench_region_guidance_compat as _professional_document_region_guidance_compat
import cew_document_discovery_governed_async as _document_discovery_governed_async
import cew_document_discovery_async_preview as _document_discovery_async_preview
import cew_document_discovery_workbench as _document_discovery

_REQUIRED_BASE_MARKERS = (
    '@router.get("/workbench", response_class=HTMLResponse)',
    'X-CEW-Canonical-Write": "false"',
    'X-CEW-Engineering-Authority-Effect": "NONE"',
    '_public_workbench_html(task.strip())',
    'client.build_client(task)',
    'Progetto N12 › Evidenza › Revisione tecnica',
    '<title>CEW — Ambiente grafico professionale</title>',
    '@router.get("/workbench/gap-review"',
    '@router.post("/api/workbench/gap-review/receipt")',
    'audit_store.persist_runtime_receipt',
    'R2HR_RECEIPT_PERSISTED_AUDIT_ONLY',
    'Verifica continuità raster',
    '@router.get("/api/workbench/gap-review/ingest-status")',
    '@router.get("/workbench/geometry-acceptance"',
    '@router.get("/api/workbench/geometry-acceptance/status")',
    '@router.post("/api/workbench/geometry-acceptance/receipt")',
    'R2GM_RECEIPT_PERSISTED_DOCUMENT_GEOMETRY_DECISION',
    '/workbench/assets/{asset_path:path}',
)

_DOCUMENT_RENDER_TARGET_COMPAT_SCRIPT = r'''<script id="cew-document-render-target-compat">
(function(){
  'use strict';
  const ce=id=>document.getElementById(id);
  document.body.dataset.cewDocumentContextGuard='v1';

  if(!ce('status')){
    const status=document.createElement('div');
    status.id='status';
    status.hidden=true;
    status.setAttribute('aria-hidden','true');
    document.body.appendChild(status);
  }

  function purgeUnsafeNoProjectMemory(){
    try{
      const prefixes=['cew.layoutPrototype.v1:NO_PROJECT:','cew.layoutConfirmed.v1:NO_PROJECT:'];
      for(let i=localStorage.length-1;i>=0;i--){
        const key=localStorage.key(i)||'';
        if(prefixes.some(prefix=>key.startsWith(prefix)))localStorage.removeItem(key);
      }
    }catch(_){}
  }

  function ensureContextBadge(){
    const meta=document.querySelector('.cew-editor-meta');
    if(!meta)return null;
    let badge=ce('cew-active-context');
    if(!badge){
      badge=document.createElement('span');
      badge.id='cew-active-context';
      badge.className='cew-editor-pill optional';
      badge.hidden=true;
      badge.title='Identità della sessione documentale attiva';
      meta.appendChild(badge);
    }
    return badge;
  }

  function sessionContext(){
    try{
      if(typeof state==='undefined'||!state?.project_id)return null;
      return {project:String(state.project_id||''),source:String(state.source_id||''),version:String(state.source_version_id||'')};
    }catch(_){return null}
  }

  function updateContextBadge(){
    const badge=ensureContextBadge(),ctx=sessionContext();
    if(!badge)return;
    badge.hidden=!ctx;
    if(ctx)badge.textContent=`Progetto ${ctx.project} · ${ctx.source||'PDF locale'}`;
  }

  function clearTransientVisualState(){
    for(const id of ['cew-region-overlay','cew-layout-overlay','cew-local-overlay'])ce(id)?.remove();
    for(const id of ['cew-region-pill','cew-layout-pill'])ce(id)?.remove();
    try{window.CEWLayoutPhaseGate?.reset?.()}catch(_){}
    document.body.dataset.cewSemanticReady='false';
  }

  function invalidateActiveSession(reason='Contesto modificato. Avvia di nuovo Analizza fonte.'){
    try{
      if(typeof state!=='undefined')state=null;
      if(typeof session!=='undefined')session=null;
      if(typeof clusterId!=='undefined')clusterId=null;
      if(typeof candidateId!=='undefined')candidateId=null;
      if(typeof resetViewer==='function')resetViewer();
    }catch(_){}
    ce('clusters')?.replaceChildren();
    const title=ce('title');if(title)title.textContent='Nessun gruppo selezionato';
    ce('detail')?.replaceChildren();
    clearTransientVisualState();
    const badge=ensureContextBadge();if(badge)badge.hidden=true;
    try{if(typeof intakeMessage==='function')intakeMessage(reason,'error')}catch(_){}
  }

  function currentFormContext(){
    return {project:ce('project')?.value?.trim()||'',source:ce('source')?.value||''};
  }

  function enforceContextMatch(){
    const ctx=sessionContext();if(!ctx){updateContextBadge();return}
    const form=currentFormContext();
    if(form.project!==ctx.project||form.source!==ctx.source){
      invalidateActiveSession('Il progetto o la fonte sono cambiati. La sessione precedente è stata chiusa: esegui Analizza fonte nel nuovo contesto.');
      return;
    }
    updateContextBadge();
  }

  function refreshTransientLayers(){
    setTimeout(()=>{
      try{window.CEWRegionGuidance?.refresh?.()}catch(_){}
      try{window.CEWLayoutLearning?.refresh?.()}catch(_){}
    },0);
  }

  function applyDeepLink(){
    const params=new URLSearchParams(window.location.search),project=params.get('project'),source=params.get('source');
    const projectInput=ce('project'),sourceSelect=ce('source');
    if(project&&projectInput&&projectInput.value!==project)projectInput.value=project;
    if(source&&sourceSelect&&[...sourceSelect.options].some(option=>option.value===source)&&sourceSelect.value!==source){
      sourceSelect.value=source;
    }
    const applied=(!project||projectInput?.value===project)&&(!source||sourceSelect?.value===source);
    document.body.dataset.cewDeepLinkReady=applied?'true':'false';
    return applied;
  }

  purgeUnsafeNoProjectMemory();
  applyDeepLink();
  for(const delay of [100,300,800,1500])setTimeout(()=>{if(applyDeepLink())refreshTransientLayers()},delay);
  const sourceSelect=ce('source');
  if(sourceSelect){
    const sourceObserver=new MutationObserver(()=>{if(applyDeepLink())refreshTransientLayers()});
    sourceObserver.observe(sourceSelect,{childList:true});
  }

  ce('project')?.addEventListener('input',()=>{enforceContextMatch();refreshTransientLayers()});
  ce('source')?.addEventListener('change',()=>{enforceContextMatch();refreshTransientLayers()});

  // Fail closed when an intake context is incomplete. The original handler also
  // validates these fields, but capture-phase blocking prevents stale session
  // content from remaining visible after an incomplete-context click.
  document.addEventListener('click',event=>{
    const analyze=event.target.closest?.('#analyze');if(!analyze)return;
    const form=currentFormContext();
    if(form.project&&form.source)return;
    event.preventDefault();event.stopImmediatePropagation();
    const message=!form.project?'Inserisci l’ID progetto prima di analizzare la fonte.':'Seleziona una fonte governata prima di avviare l’analisi.';
    invalidateActiveSession(message);
    (!form.project?ce('project'):ce('source'))?.focus();
  },true);

  // Reading units are selectable editor objects, not pan handles. Intercept the
  // initial pointer in document capture phase, before the viewer can call
  // setPointerCapture(), and hand the unit directly to the phase gate.
  document.addEventListener('pointerdown',event=>{
    if(event.button!==0)return;
    const unit=event.target.closest?.('#cew-layout-overlay .cew-layout-unit');
    if(!unit)return;
    const phaseGate=window.CEWLayoutPhaseGate;
    if(!phaseGate?.state?.().confirmed)return;
    event.preventDefault();
    event.stopPropagation();
    const selected=phaseGate.selectUnit?.(unit.dataset.layoutUnit);
    if(selected){
      for(const button of document.querySelectorAll('#cew-layout-overlay .cew-layout-unit')){
        button.classList.toggle('active',button.dataset.layoutUnit===unit.dataset.layoutUnit);
      }
    }
  },true);

  const contextTimer=setInterval(enforceContextMatch,350);
  window.addEventListener('pagehide',()=>clearInterval(contextTimer),{once:true});
  window.CEWDocumentContextGuard={
    state:()=>({form:currentFormContext(),session:sessionContext(),deepLinkReady:document.body.dataset.cewDeepLinkReady==='true'}),
    applyDeepLink,
    invalidate:invalidateActiveSession
  };
})();
</script>'''


def _assert_base_contract() -> None:
    base_path = Path(_base.__file__).resolve()
    source = base_path.read_text(encoding="utf-8")
    missing = [marker for marker in _REQUIRED_BASE_MARKERS if marker not in source]
    if missing:
        raise RuntimeError("CEW_PROFESSIONAL_WORKBENCH_BASE_CONTRACT_DRIFT:" + "|".join(missing))


def _install_document_render_target_compat() -> None:
    if getattr(_professional_document_workbench, "_cew_render_target_compat_installed", False):
        return
    original_patched_page = _professional_document_workbench._patched_page

    def patched_page_with_render_target_compat() -> str:
        html = original_patched_page()
        if 'id="cew-document-render-target-compat"' in html:
            return html
        if "</body>" not in html:
            raise RuntimeError("CEW_DOCUMENT_RENDER_TARGET_COMPAT_BODY_MARKER_MISSING")
        return html.replace("</body>", _DOCUMENT_RENDER_TARGET_COMPAT_SCRIPT + "</body>", 1)

    _professional_document_workbench._patched_page = patched_page_with_render_target_compat
    _professional_document_workbench._cew_render_target_compat_installed = True


_assert_base_contract()
_install_document_render_target_compat()
_reference_review_hardening.install(_reference_review)
_reference_review_asset_hardening.install(_reference_review)


def _sync_runtime_stores() -> None:
    _base.R2HR_RUNTIME_STORE = R2HR_RUNTIME_STORE
    _base.R2GM_RUNTIME_STORE = R2GM_RUNTIME_STORE


def _runtime_r2gi_report():
    _sync_runtime_stores()
    return _base._runtime_r2gi_report()


def _runtime_r2gm_report():
    _sync_runtime_stores()
    return _base._runtime_r2gm_report()


def build_router(source_workspace):
    _sync_runtime_stores()
    router = _base.build_router(source_workspace)
    router.include_router(_oar_g4.build_router())
    router.include_router(_oar_g4_assisted.build_router())
    router.include_router(_reference_review.build_router())
    # First route owns the live HTML response and preserves all accepted MATURE_V1
    # headers while adding semantic-free region guidance markers.
    router.include_router(_professional_document_region_guidance_compat.build_router())
    router.include_router(_professional_document_region_guidance.build_router())
    router.include_router(_professional_document_governed_async.build_router())
    router.include_router(_professional_document_content.build_router())
    router.include_router(_professional_document_workbench.build_router())
    router.include_router(_document_discovery_governed_async.build_router(source_workspace))
    router.include_router(_document_discovery_async_preview.build_router())
    router.include_router(_document_discovery.build_router(source_workspace))
    return router
