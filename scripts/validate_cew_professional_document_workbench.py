#!/usr/bin/env python3
"""Deterministic gate for CEW Professional Document Workbench v1."""
from __future__ import annotations

from pathlib import Path

import cew_professional_document_workbench as professional


def main() -> None:
    html = professional._patched_page()
    professional_source = Path("cew_professional_document_workbench.py").read_text(encoding="utf-8")

    required = (
        "cew-professional-document-style",
        "cew-professional-document-script",
        "cew-activity-rail",
        "cew-primary-content",
        "cew-canvas-shell",
        "cew-nav-pages",
        "cew-nav-primitives",
        "cew-nav-clusters",
        "cew-nav-verify",
        "cew-inspector-meta",
        "cew-decision-panel",
        "cew-statusbar",
        "Trascina per spostare · rotella per zoom",
        "NESSUNA_REGIONE_GRAFICA_ACQUISITA",
        "Decisione umana",
        "NON ASSEGNATO",
        "UMANA RICHIESTA",
    )
    missing = [marker for marker in required if marker not in html]
    assert not missing, missing

    # Mature workbench contract: sidebars + dominant viewport + truly anchored tools + status bar.
    assert "grid-template-columns:var(--cew-left) minmax(360px,1fr) var(--cew-right)" in html
    assert ".cew-canvas-shell{position:relative" in html
    assert "#preview-view-controls{position:absolute!important" in html
    assert "position:sticky!important" not in html
    assert "flex-direction:column!important" in html
    assert "if(shell&&bar&&bar.parentElement!==shell)shell.appendChild(bar)" in html
    assert "body.cew-professional-document #viewer" in html
    assert "wheel" in html and "setPreviewZoom(next)" in html

    # The blocked preview must not expose the training form as the primary inspector surface.
    assert "decision.hidden=!state?.teaching_enabled" in html
    assert "body.cew-professional-document .right>label" in html
    assert "Significato</dt><dd>NON ASSEGNATO" in html

    # A successful execution with zero graphic evidence is intercepted at the
    # message boundary itself, so a later async success message cannot turn it green.
    assert "const baseProfessionalIntakeMessage=intakeMessage" in html
    assert "intakeMessage=function(text,kind='')" in html
    assert "kind==='ok'&&state&&pc===0&&cc===0" in html
    assert "nessuna regione grafica acquisita · verifica necessaria" in html
    assert "'warn'" in html
    assert "intake-status.warn" in html

    # Authority headers belong to the HTML route response, while semantic/training
    # declarations remain visible in the rendered workbench.
    assert '"X-CEW-Canonical-Write": "false"' in professional_source
    assert '"X-CEW-Engineering-Authority-Effect": "NONE"' in professional_source
    assert '"X-CEW-Document-Workbench": "PROFESSIONAL_V1"' in professional_source
    assert "nessuna classificazione automatica" in html
    assert "Preview analizzabile, ma training bloccato" in html

    composition = Path("cew_professional_workbench_api.py").read_text(encoding="utf-8")
    professional_mount = "router.include_router(_professional_document_workbench.build_router())"
    async_mount = "router.include_router(_document_discovery_async_preview.build_router())"
    legacy_mount = "router.include_router(_document_discovery.build_router(source_workspace))"
    assert professional_mount in composition
    assert async_mount in composition
    assert legacy_mount in composition
    assert composition.index(professional_mount) < composition.index(async_mount) < composition.index(legacy_mount)

    router = professional.build_router()
    assert [route.path for route in router.routes] == ["/workbench/document-discovery"]

    print("CEW_PROFESSIONAL_DOCUMENT_WORKBENCH_V1_PASS")
    print("layout=PRIMARY_SIDEBAR+DOMINANT_CANVAS+CONTEXTUAL_INSPECTOR+STATUS_BAR")
    print("viewport_tools=ABSOLUTE_CANVAS_ANCHORED wheel_zoom=ENABLED drag_pan=INHERITED")
    print("zero_graphic_result=WARNING_REVIEW_REQUIRED_AT_MESSAGE_BOUNDARY")
    print("training=CONTEXTUAL_ONLY canonical_write_authorized=false semantic_authority=NONE")


if __name__ == "__main__":
    main()
