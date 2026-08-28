#!/usr/bin/env python3
from __future__ import annotations

"""Compatibility entrypoint for the B1 acceptance route.

B1.7 remains preserved in repository history and by its historical contract.
The active route now serves the hardened B1.8 Human-Centred Acceptance v2 experience.
"""

from cew_b1_human_acceptance_v2_hardening import build_app, task_specs


def build_lab() -> str:
    return build_app()
