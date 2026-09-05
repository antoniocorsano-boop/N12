#!/usr/bin/env python3
"""Opt-in ephemeral audit adapter for isolated CEW HVA runtimes.

This adapter exists only to make a disposable human-validation runtime usable
when the deployment platform cannot receive a governed audit credential through
the automation connector. It never grants canonical, structural or engineering
authority.

Precedence is fail-closed:
- any configured Neon/HTTPS/Supabase backend keeps its normal authority;
- local development keeps its existing filesystem behavior;
- Render remains UNCONFIGURED_PRODUCTION unless the explicit
  CEW_HVA_EPHEMERAL_AUDIT=1 flag is present;
- the adapter affects audit persistence only, not project/canonical writes.
"""
from __future__ import annotations

import os

import cew_runtime_audit_store as audit_store

_FLAG = "CEW_HVA_EPHEMERAL_AUDIT"
_INSTALLED_MARKER = "_cew_hva_ephemeral_audit_installed"
_ORIGINAL_MARKER = "_cew_hva_ephemeral_audit_original_backend_status"


def enabled() -> bool:
    return bool(os.getenv("RENDER")) and os.getenv(_FLAG, "").strip() == "1"


def install() -> None:
    """Install an idempotent backend-status adapter for an explicit HVA runtime."""
    if getattr(audit_store, _INSTALLED_MARKER, False):
        return

    original = audit_store.backend_status
    setattr(audit_store, _ORIGINAL_MARKER, original)

    def backend_status() -> str:
        state = original()
        if state == "UNCONFIGURED_PRODUCTION" and enabled():
            return "FILESYSTEM_APPEND_ONLY"
        return state

    audit_store.backend_status = backend_status
    setattr(audit_store, _INSTALLED_MARKER, True)
