#!/usr/bin/env python3
from __future__ import annotations

"""Compatibility entrypoint for the B1 acceptance route.

B1.7 remains preserved in repository history and by its historical contract.
The active route now serves the hardened B1.8 Human-Centred Acceptance v2 experience.
"""

import cew_runtime_render_budget
from cew_b1_human_acceptance_v2_hardening import build_app, task_specs

# app.py imports this module during runtime bootstrap. Install the bounded
# reading-aid renderer before the FastAPI routes are served.
cew_runtime_render_budget.install()


def build_lab() -> str:
    return build_app()
