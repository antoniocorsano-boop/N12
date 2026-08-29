#!/usr/bin/env python3
from __future__ import annotations

"""Compatibility entrypoint for the B1 acceptance route.

B1.7 remains preserved in repository history and by its historical contract.
The active route now serves the hardened B1.8 Human-Centred Acceptance v2 experience.
R2HR professional gap review is integrated into the authenticated CEW runtime:
no local package download or JSON export is required from the reviewer.
"""

import cew_evidence_viewer_interaction
import cew_r2hr_system_review
import cew_runtime_render_budget
from cew_b1_human_acceptance_v2_hardening import build_app, task_specs

# app.py imports this module during runtime bootstrap. Install runtime reading
# aids and the R2HR receipt dispatcher before FastAPI serves the HVA shell.
cew_runtime_render_budget.install()
cew_evidence_viewer_interaction.install()
cew_r2hr_system_review.install()


def build_lab() -> str:
    body = build_app()
    panel = cew_r2hr_system_review.render_panel()
    navigation = '<a href="#r2hr-system-review" style="font-weight:800">Revisione R2HR nel sistema</a>'
    if "</header>" in body:
        body = body.replace("</header>", navigation + "</header>", 1)
    if "</body>" in body:
        return body.replace("</body>", panel + "</body>", 1)
    return body + panel
