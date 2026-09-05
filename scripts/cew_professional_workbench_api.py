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


def _assert_base_contract() -> None:
    base_path = Path(_base.__file__).resolve()
    source = base_path.read_text(encoding="utf-8")
    missing = [marker for marker in _REQUIRED_BASE_MARKERS if marker not in source]
    if missing:
        raise RuntimeError("CEW_PROFESSIONAL_WORKBENCH_BASE_CONTRACT_DRIFT:" + "|".join(missing))


_assert_base_contract()
_reference_review_hardening.install(_reference_review)
_reference_review_asset_hardening.install(_reference_review)


def _sync_runtime_stores() -> None:
    """Keep legacy writable runtime-store overrides effective through the wrapper."""
    _base.R2HR_RUNTIME_STORE = R2HR_RUNTIME_STORE
    _base.R2GM_RUNTIME_STORE = R2GM_RUNTIME_STORE


def _runtime_r2gi_report():
    """Compatibility delegate for governed R2GI runtime consumers and validators."""
    _sync_runtime_stores()
    return _base._runtime_r2gi_report()


def _runtime_r2gm_report():
    """Compatibility delegate for governed R2GM runtime consumers and validators."""
    _sync_runtime_stores()
    return _base._runtime_r2gm_report()


def build_router(source_workspace):
    _sync_runtime_stores()
    router = _base.build_router(source_workspace)
    router.include_router(_oar_g4.build_router())
    router.include_router(_oar_g4_assisted.build_router())
    router.include_router(_reference_review.build_router())
    # Mount the async/bounded adapter first so its HTML route shadows the
    # historical synchronous Preview button. Existing session/learning API
    # routes remain provided by the preserved Document Discovery router below.
    router.include_router(_document_discovery_async_preview.build_router())
    router.include_router(_document_discovery.build_router(source_workspace))
    return router
