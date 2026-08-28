#!/usr/bin/env python3
from __future__ import annotations

"""Runtime-only CEW bootstrap for managed candidate services.

Installs operational safety policies that must affect the actual FastAPI
runtime. This module does not change canonical data or engineering authority.
"""

import cew_runtime_render_budget as render_budget


render_budget.install()

RUNTIME_RENDER_BUDGET_INSTALLED = True
