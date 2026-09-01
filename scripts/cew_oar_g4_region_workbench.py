#!/usr/bin/env python3
"""Composizione del Workbench OAR G4 con risoluzione governata di TAV-05S."""
from __future__ import annotations

from cew_oar_g4_region_workbench_base import *  # noqa: F401,F403
import cew_oar_g4_audit_history as _history
import cew_oar_g4_region_binding as _binding
import cew_oar_g4_region_workbench_base as _base
import cew_oar_g4_source_resolver as _resolver

# L'interfaccia e le API restano quelle già validate; cambia soltanto il modo
# in cui la SourceVersion viene materializzata. Il PDF è recuperato dal commit
# archivio immutabile tramite Source Workspace e verificato SHA-256 prima del
# rendering, invece di essere assunto presente nel checkout del runtime.
verify_source = _resolver.verify_source
ensure_runtime_raster = _resolver.ensure_runtime_raster
EXPECTED_SOURCE_SHA256 = _resolver.EXPECTED_SOURCE_SHA256
EXPECTED_PAGE_WIDTH_PT = _resolver.EXPECTED_PAGE_WIDTH_PT
EXPECTED_PAGE_HEIGHT_PT = _resolver.EXPECTED_PAGE_HEIGHT_PT
RUNTIME_DPI = _resolver.RUNTIME_DPI
RUNTIME_RASTER = _resolver.RUNTIME_RASTER

_base.verify_source = verify_source
_base.ensure_runtime_raster = ensure_runtime_raster
_base.EXPECTED_SOURCE_SHA256 = EXPECTED_SOURCE_SHA256
_base.EXPECTED_PAGE_WIDTH_PT = EXPECTED_PAGE_WIDTH_PT
_base.EXPECTED_PAGE_HEIGHT_PT = EXPECTED_PAGE_HEIGHT_PT
_base.RUNTIME_DPI = RUNTIME_DPI
_base.RUNTIME_RASTER = RUNTIME_RASTER

# OAR uses the domain aggregate itself as the single authority for concurrent
# confirmation equivalence. No wrapper-level duplicate predicate is allowed:
# authority-divergent receipts must reach the domain and fail closed.
_original_runtime_loader = _base.audit_store.load_runtime_receipts


def _governed_runtime_loader(receipt_type, store, *, max_receipts=_history.MAX_PAGE_SIZE):
    if receipt_type == _binding.RECEIPT_TYPE:
        return _history.load_runtime_receipts(receipt_type, store, max_receipts=max_receipts)
    return _original_runtime_loader(receipt_type, store, max_receipts=max_receipts)


# The base Workbench calls audit_store.load_runtime_receipts from both status
# reconstruction and pre-append validation. Route only the OAR receipt type to
# the paginated/reduced reader; every other runtime receipt type keeps its
# existing governed loader unchanged.
_base.audit_store.load_runtime_receipts = _governed_runtime_loader

# Harden the already validated base UI without duplicating its router/domain
# implementation. A displayed bbox that has been edited is explicitly dirty:
# confirmation is disabled until PROPOSE_GEOMETRY persists it. Confirmation
# also sends the displayed bbox so the server-side mismatch guard remains a
# second, independent fail-closed boundary.
_base_build_page = _base.build_page


def build_page() -> str:
    page = _base_build_page()
    replacements = (
        (
            "let report=null, selected=null, draft=null, dragStart=null;",
            "let report=null, selected=null, draft=null, dragStart=null, draftDirty=false;",
        ),
        (
            "setBox(r?.bbox??null);propose.disabled=!selected;confirmBtn.disabled=!(r&&r.state==='PROPOSED');",
            "setBox(r?.bbox??null);draftDirty=false;propose.disabled=!selected;confirmBtn.disabled=!(r&&r.state==='PROPOSED');",
        ),
        (
            "setBox({x,y,w:Math.abs(p.x-dragStart.x),h:Math.abs(p.y-dragStart.y)});propose.disabled=!(draft&&draft.w>0&&draft.h>0)",
            "setBox({x,y,w:Math.abs(p.x-dragStart.x),h:Math.abs(p.y-dragStart.y)});draftDirty=true;confirmBtn.disabled=true;propose.disabled=!(draft&&draft.w>0&&draft.h>0)",
        ),
        (
            "if(action==='PROPOSE_GEOMETRY')payload.bbox=draft;message.textContent='Registrazione…';",
            "if(action==='PROPOSE_GEOMETRY'||action==='CONFIRM_GEOMETRY')payload.bbox=draft;if(action==='CONFIRM_GEOMETRY'&&draftDirty){message.textContent='Registra prima la geometria modificata.';return};message.textContent='Registrazione…';",
        ),
    )
    for old, new in replacements:
        if old not in page:
            raise RuntimeError("OAR_G4_UI_STALE_GEOMETRY_PATCH_MARKER_MISSING")
        page = page.replace(old, new, 1)
    return page


_base.build_page = build_page


def build_router():
    return _base.build_router()
