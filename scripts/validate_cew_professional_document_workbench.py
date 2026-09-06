#!/usr/bin/env python3
"""Deterministic gate for CEW Professional Document Workbench v2 + mature panels."""
from __future__ import annotations

import json
from pathlib import Path

import cew_professional_document_workbench_mature_panels as professional


def main() -> None:
    html = professional._patched_page()
    professional_source = Path("cew_professional_document_workbench_mature_panels.py").read_text(encoding="utf-8")
    contract_path = Path("../automation/CEW_DOCUMENT_WORKBENCH_PANEL_CONTRACT_v2.json")
    spec_path = Path("../analysis/cew/CEW_PROFESSIONAL_DOCUMENT_WORKBENCH_ARCHITECTURE_v2.md")
    research_path = Path("../analysis/cew/CEW_PANEL_MATURITY_REFERENCE_v1.md")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    spec = spec_path.read_text(encoding="utf-8")
    research = research_path.read_text(encoding="utf-8")
    spec_lower = spec.lower()
    research_lower = research.lower()

    assert contract["schema"] == "CEW_DOCUMENT_WORKBENCH_PANEL_CONTRACT_v2"
    assert contract["architecture_id"] == "CEW_PROFESSIONAL_DOCUMENT_WORKBENCH_V2"
    assert contract["panel_quality_layer"] == "MATURE_V1"
    assert contract["layout_state"]["storage_key"] == "cew.documentDiscovery.workbench.v2"
    assert contract["panel_quality_contract"]["density"] == "COMPACT"
    assert contract["panel_quality_contract"]["single_visible_title_per_panel_level"] is True
    assert contract["panel_quality_contract"]["ordinary_panel_copy"] == "HUMAN_READABLE_ITALIAN"
    assert contract["keyboard_contract"]["toggle_primary_sidebar"] == "Ctrl+B"
    assert contract["keyboard_contract"]["toggle_auxiliary_sidebar"] == "Ctrl+J"
    assert contract["authority_invariants"]["canonical_write"] == "BLOCKED"
    assert contract["authority_invariants"]["automatic_semantic_authority"] == "NONE"

    required = (
        "cew-professional-document-style",
        "cew-professional-document-script",
        "cew-mature-panel-style",
        "cew-mature-panel-script",
        "data-cew-panel-quality",
        "WORKBENCH_STATE_KEY='cew.documentDiscovery.workbench.v2'",
        "PRIMARY_VIEWS",
        "cew-activity-rail",
        "cew-primary-head",
        "cew-primary-content",
        "cew-left-sash",
        "cew-canvas-shell",
        "cew-editor-bar",
        "cew-inspector-head",
        "cew-inspector-tabs",
        "cew-inspector-properties",
        "cew-inspector-provenance",
        "cew-decision-panel",
        "cew-right-sash",
        "cew-statusbar",
        "NESSUNA_REGIONE_GRAFICA_ACQUISITA",
        "Nessuna regione grafica acquisita",
        "NON ASSEGNATO",
        "UMANA RICHIESTA",
        "Trascina: pan · rotella: zoom",
        "aria-pressed",
        "aria-selected",
        "aria-valuenow",
        "aria-expanded",
    )
    missing = [marker for marker in required if marker not in html]
    assert not missing, missing

    # Canonical panel topology: rail + independent sidebars + sashes + flexible editor.
    assert "grid-template-columns:var(--cew-rail) var(--cew-left-column,var(--cew-left))" in html
    assert "minmax(420px,1fr)" in html
    assert "var(--cew-right-column,var(--cew-right))" in html
    assert ".cew-canvas-shell{grid-column:4" in html
    assert ".cew-sash{position:relative" in html
    assert "cursor:col-resize" in html

    # Side panels have independent, persistent presentation state.
    for field in contract["layout_state"]["persist"]:
        assert field in html, field
    assert "localStorage.getItem(WORKBENCH_STATE_KEY)" in html
    assert "localStorage.setItem(WORKBENCH_STATE_KEY" in html
    assert "wireSash(s,'left')" in html
    assert "wireSash(s,'right')" in html
    assert "pointerdown" in html and "dblclick" in html and "ArrowLeft" in html and "ArrowRight" in html
    assert "cew-primary-collapsed" in html and "cew-aux-collapsed" in html

    # Mature-panel refinement keeps only one visible active-view title in the sidebar body.
    assert ".cew-nav-panel>.cew-sidebar-title:first-child{display:none!important}" in html
    assert "cew-primary-count" in html
    assert "humanizePanelCopy" in html
    assert "Nessuna sessione" in html and "Revisione umana richiesta" in html

    # Stable view registry and mature keyboard parity.
    for view_id in ("pages", "primitives", "clusters", "verify"):
        assert f"id:'{view_id}'" in html
    for shortcut in ("Alt+1", "Alt+2", "Alt+3", "Alt+4"):
        assert shortcut in html
    assert "e.key.toLowerCase()==='j'" in html
    assert "ArrowDown" in html and "ArrowUp" in html
    assert "showInspectorTab" in html
    for inspector_id in ("properties", "provenance", "decision"):
        assert f'data-inspector="{inspector_id}"' in html

    # Viewport controls remain anchored to the editor viewport and compact.
    assert "#preview-view-controls{" in html
    assert "position:absolute!important" in html
    assert "top:42px!important" in html
    assert "flex-direction:column!important" in html
    assert "if(shell&&bar&&bar.parentElement!==shell)shell.appendChild(bar)" in html
    assert "wheel" in html and "setPreviewZoom(next)" in html
    assert "['1:1'" in html or "['1:1'," in html

    # Blocked preview must not expose the human decision form as the default inspector.
    assert "decisionTab.hidden=!teaching" in html
    assert "decision.hidden=id!=='decision'||!teaching" in html
    assert "NESSUNA AUTORITÀ AUTOMATICA" in html
    assert "Scrittura canonica</dt><dd>BLOCCATA" in html

    # A successful execution with zero graphic evidence is intercepted before green success.
    assert "const baseProfessionalIntakeMessage=intakeMessage" in html
    assert "kind==='ok'&&state&&pc===0&&cc===0" in html
    assert "nessuna regione grafica acquisita · verifica necessaria" in html
    assert "'warn'" in html
    assert "intake-status.warn" in html

    # Authority route headers are explicit and unchanged by the presentation tranche.
    assert '"X-CEW-Canonical-Write": "false"' in professional_source
    assert '"X-CEW-Engineering-Authority-Effect": "NONE"' in professional_source
    assert '"X-CEW-Document-Workbench": "PROFESSIONAL_V2"' in professional_source
    assert '"X-CEW-Panel-Architecture": "ACTIVITY_PRIMARY_EDITOR_AUXILIARY_STATUS"' in professional_source
    assert '"X-CEW-Panel-Quality": "MATURE_V1"' in professional_source
    assert "nessuna classificazione automatica" in html
    assert "Preview analizzabile, ma training bloccato" in html

    # Prose and research docs preserve the source-backed panel maturity rationale.
    for concept in (
        "activity_rail",
        "primary_sidebar",
        "flexible_editor_canvas",
        "auxiliary_sidebar",
        "status_bar",
    ):
        assert concept in spec_lower, concept
    assert "cew.documentdiscovery.workbench.v2" in spec_lower
    assert "cew_document_workbench_panel_contract_v2.json" in spec_lower
    assert "microsoft vs code" in spec_lower
    assert "jupyterlab" in spec_lower
    assert "bluebeam revu" in spec_lower
    assert "autodesk viewer" in spec_lower
    assert "openhands agent canvas" in spec_lower
    assert "browser materialization gate" in spec_lower
    assert "ui_materialization_fail" in spec_lower
    for source_name in ("microsoft vs code", "jupyterlab", "bluebeam revu", "autodesk viewer", "openhands agent canvas"):
        assert source_name in research_lower, source_name
    assert "no source code, icons, branding" in research_lower

    composition = Path("cew_professional_workbench_api.py").read_text(encoding="utf-8")
    assert "import cew_professional_document_workbench_mature_panels as _professional_document_workbench" in composition
    professional_mount = "router.include_router(_professional_document_workbench.build_router())"
    async_mount = "router.include_router(_document_discovery_async_preview.build_router())"
    legacy_mount = "router.include_router(_document_discovery.build_router(source_workspace))"
    assert professional_mount in composition
    assert async_mount in composition
    assert legacy_mount in composition
    assert composition.index(professional_mount) < composition.index(async_mount) < composition.index(legacy_mount)

    router = professional.build_router()
    assert [route.path for route in router.routes] == ["/workbench/document-discovery"]

    print("CEW_PROFESSIONAL_DOCUMENT_WORKBENCH_V2_MATURE_PANELS_PASS")
    print("layout=TITLE+COMMAND+ACTIVITY+PRIMARY+FLEX_EDITOR+AUXILIARY+STATUS")
    print("panel_quality=MATURE_V1 density=COMPACT human_copy=PASS single_title=PASS")
    print("panel_state=PERSISTED independent_resize=PASS central_editor_absorbs_resize=PASS")
    print("keyboard=CTRL_B+CTRL_J+ALT_1_4 accessibility_state=PASS")
    print("viewport_tools=EDITOR_ANCHORED wheel_zoom=ENABLED drag_pan=INHERITED")
    print("zero_graphic_result=WARNING_REVIEW_REQUIRED")
    print("decision_surface=GOVERNED_CONTEXTUAL_ONLY canonical_write_authorized=false semantic_authority=NONE")


if __name__ == "__main__":
    main()
