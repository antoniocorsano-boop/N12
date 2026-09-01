#!/usr/bin/env python3
"""Professional Workbench router composition.

The historical Workbench API is preserved byte-for-byte in
cew_professional_workbench_api_base.py. This composition layer adds the governed
G4/TAV-05S OAR evidence-localization router without altering existing R2HR/R2GM
routes or their authority semantics.
"""
from __future__ import annotations

from cew_professional_workbench_api_base import *  # noqa: F401,F403
import cew_professional_workbench_api_base as _base
import cew_oar_g4_region_workbench as _oar_g4


def build_router(source_workspace):
    router = _base.build_router(source_workspace)
    router.include_router(_oar_g4.build_router())
    return router
