#!/usr/bin/env python3
"""Composizione del Workbench OAR G4 con risoluzione governata di TAV-05S."""
from __future__ import annotations

from cew_oar_g4_region_workbench_base import *  # noqa: F401,F403
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

# Multiple workers may validate two confirmation requests against the same
# pre-confirmation state before either append becomes visible to the other.
# Append-only audit must retain both receipts, but the governed state machine
# treats only *equivalent* confirmations as one idempotent transition. Any
# differing bbox/provenance is deliberately preserved so the strict aggregate
# continues to fail closed as a conflict.
_strict_aggregate = _binding.aggregate
_CONFIRM_EQUIVALENCE_FIELDS = (
    "support_id",
    "evidence_object_id",
    "pilot_id",
    "binding_id",
    "source_version_id",
    "page_id",
    "derived_asset_id",
    "page_transform_id",
    "coordinate_system",
)


def _equivalent_confirmation(left: dict, right: dict) -> bool:
    if left.get("action") != _binding.CONFIRM_ACTION or right.get("action") != _binding.CONFIRM_ACTION:
        return False
    if any(left.get(key) != right.get(key) for key in _CONFIRM_EQUIVALENCE_FIELDS):
        return False
    return _binding.normalize_bbox(left.get("bbox")) == _binding.normalize_bbox(right.get("bbox"))


def _aggregate_concurrency_safe(receipts, contract=None):
    filtered = []
    first_confirmation_by_support = {}
    for receipt in _binding._ordered_receipts(list(receipts)):
        if receipt.get("action") == _binding.CONFIRM_ACTION:
            support_id = str(receipt.get("support_id", ""))
            previous = first_confirmation_by_support.get(support_id)
            if previous is not None and _equivalent_confirmation(previous, receipt):
                # Equivalent concurrent confirmation: retain it in append-only
                # audit storage, but do not replay a second state transition.
                continue
            if previous is None:
                first_confirmation_by_support[support_id] = receipt
        filtered.append(receipt)
    return _strict_aggregate(filtered, contract)


_binding.aggregate = _aggregate_concurrency_safe
_base.binding.aggregate = _aggregate_concurrency_safe


def build_router():
    return _base.build_router()
