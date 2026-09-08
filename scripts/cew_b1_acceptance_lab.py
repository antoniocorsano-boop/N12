#!/usr/bin/env python3
from __future__ import annotations

"""Compatibility entrypoint for the B1 acceptance route.

B1.7 remains preserved in repository history and by its historical contract.
The active route now serves the hardened B1.8 Human-Centred Acceptance v2 experience.
R2HR professional gap review is integrated into the authenticated CEW runtime:
no local package download or JSON export is required from the reviewer.
"""

import os

import cew_evidence_viewer_interaction
import cew_r2hr_system_review
import cew_runtime_render_budget
from cew_b1_human_acceptance_v2_hardening import build_app, task_specs

# app.py imports this module during runtime bootstrap. Install runtime reading
# aids and the R2HR receipt dispatcher before FastAPI serves the HVA shell.
cew_runtime_render_budget.install()
cew_evidence_viewer_interaction.install()
cew_r2hr_system_review.install()

# The real managed candidate runtime opts into a strict startup contract through
# CEW_R2HR_STRICT_RUNTIME=1. Policy tests and local execution can still exercise
# the generic Render fail-closed paths without first materializing R2HR assets.
if (os.getenv("RENDER") or os.getenv("VERCEL")) and os.getenv("CEW_R2HR_STRICT_RUNTIME") == "1":
    _r2hr_status = cew_r2hr_system_review.status()
    if _r2hr_status.get("state") != "READY_IN_SYSTEM":
        raise RuntimeError(
            "CEW_R2HR_MANAGED_RUNTIME_NOT_READY:"
            + str(_r2hr_status.get("reason", _r2hr_status.get("state", "UNKNOWN")))
        )


def build_lab() -> str:
    body = build_app()
    panel = cew_r2hr_system_review.render_panel()
    navigation = '<a href="#r2hr-system-review" style="font-weight:800">Revisione R2HR nel sistema</a>'
    if "</header>" in body:
        body = body.replace("</header>", navigation + "</header>", 1)
    if "</body>" in body:
        return body.replace("</body>", panel + "</body>", 1)
    return body + panel
