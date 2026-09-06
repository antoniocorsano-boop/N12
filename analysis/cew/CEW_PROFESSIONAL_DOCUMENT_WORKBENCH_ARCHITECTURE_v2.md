# CEW Professional Document Workbench v2

## Status

This document is the canonical workbench topology contract for Document Discovery. It replaces incremental viewer-layout experiments with one stable professional panel architecture.

A source-level/string validator is **not sufficient** to certify this UI. The workbench must also execute successfully in a real browser against the mounted FastAPI route and materialize the canonical parts in the DOM.

## Reference model

The topology and panel behavior are grounded in mature, inspectable workbench patterns rather than copied proprietary UI:

- **Microsoft VS Code — Custom Layout / Agents Window layout**: stable part ownership, Activity Bar view switching, a flexible central surface, independently sized side parts, compact density and persisted layout state;
- **JupyterLab application shell**: persistent left/right/main/bottom areas, active-sidebar collapse behavior and explicit left/right sidebar keyboard commands;
- **OpenHands Agent Canvas**: one workspace coordinates multiple tool surfaces while UI state remains distinct from agent/execution authority;
- **Bluebeam Revu** (behavioral reference only): technical-PDF main workspace dominates while specialized panels, panel access bars, navigation and status remain separate;
- **Autodesk Viewer** (behavioral reference only): viewer navigation stays on the viewer while Properties is contextual to selection.

Detailed source notes and adopted/non-adopted principles are recorded in:

`analysis/cew/CEW_PANEL_MATURITY_REFERENCE_v1.md`

A Devin/Cascade-style interface may be used as a behavioral usability benchmark, but CEW does not copy third-party branding, source code, icons or protected visual assets.

## Canonical topology

```text
TITLE_BAR
COMMAND_BAR
WORKBENCH
├── ACTIVITY_RAIL
├── PRIMARY_SIDEBAR
├── LEFT_SASH
├── FLEXIBLE_EDITOR_CANVAS
├── RIGHT_SASH
└── AUXILIARY_SIDEBAR
STATUS_BAR
```

The central editor is the flexible surface. Sidebars retain user-established sizes inside governed bounds and must not consume general window resize.

## Part ownership

| Part | Ownership |
|---|---|
| TITLE_BAR | Workspace identity, provider/runtime summary |
| COMMAND_BAR | Project/source/PDF intake and analysis commands |
| ACTIVITY_RAIL | Stable primary-view switching |
| PRIMARY_SIDEBAR | Page/evidence navigation |
| FLEXIBLE_EDITOR_CANVAS | Original document / technical drawing inspection |
| AUXILIARY_SIDEBAR | Contextual properties, provenance, governed decision surface |
| STATUS_BAR | Compact persistent viewer/acquisition/authority state |

## Mature panel-quality contract

The canonical topology is now considered stable. Internal panel quality follows these additional rules:

1. **One visible title per panel level.** The active Primary Sidebar title is owned by the sidebar header and is not repeated immediately inside its body.
2. **Human-readable panel copy.** Machine state tokens may remain in logs and compact diagnostics, but ordinary panel content uses readable Italian labels.
3. **Compact chrome.** Panel headers, activity items, tabs, counts and action controls minimize non-document area.
4. **Context before forms.** Properties and Provenance are ordinary inspector surfaces. Decision appears only when governed teaching is enabled.
5. **Document-first space allocation.** Either sidebar may collapse independently and the central editor absorbs the reclaimed width.
6. **Keyboard parity.** `Ctrl+B` toggles the Primary Sidebar; `Ctrl+J` toggles the Auxiliary Sidebar. Focused sashes remain keyboard adjustable.
7. **Accessible interaction state.** Activity items expose current/pressed state; inspector tabs expose selected state; sashes expose orientation, min/max/current values; panel toggles expose expanded state.
8. **No decorative controls.** Visible controls must perform a current operation. Governed-but-unavailable actions remain unavailable rather than ornamental.
9. **Status separation.** Execution completion, graphic-evidence result, source authority and training authority remain separate states.

These refinements are implemented by a presentation-only mature-panel layer over the v2 workbench shell. They do not redefine topology.

## Activity rail and Primary Sidebar

Stable primary views:

- `pages`
- `primitives`
- `clusters`
- `verify`

The activity rail is persistent. Selecting the already-active primary view toggles the Primary Sidebar, so a collapsed sidebar remains recoverable without a hidden control.

The Primary Sidebar is independently resizable and collapsible. Its width is persisted within the range defined by `CEW_DOCUMENT_WORKBENCH_PANEL_CONTRACT_v2.json`.

The Activity Rail is a **view selector**, not a domain-action toolbar. It may expose compact icons and keyboard hints, but actions such as teaching, canonical promotion or source registration do not belong there.

Viewport commands do not belong in the Primary Sidebar.

## Flexible editor canvas

The document is the dominant visual authority.

The editor surface contains:

- a compact editor tab/header;
- page fit;
- width fit;
- zoom in/out/reset;
- mouse-wheel zoom around the cursor;
- drag pan;
- 90-degree rotation;
- direct graphic-cluster hotspot selection.

Navigation tools remain anchored to the editor viewport. They do not travel away with the document during pan.

The central editor absorbs remaining width when either side panel is resized or collapsed.

## Auxiliary Sidebar

Stable inspector views:

- `properties`
- `provenance`
- `decision`

`decision` is available only when governed project-local teaching is actually enabled by immutable `SourceVersion + READY Page` identities.

When teaching is blocked, the permanent inspector must not expose an editable training form as its default surface.

The Inspector is contextual: selection changes properties, not workbench topology. Provenance remains independently inspectable.

## Sashes and resize behavior

Left and right sidebars are independently resizable by sashes.

Required interaction:

- pointer drag changes the relevant panel only;
- keyboard Left/Right adjusts a focused sash;
- double click restores the default width;
- width is clamped to the machine-readable bounds;
- the editor canvas absorbs the complementary change;
- accessible separator state exposes orientation and current/min/max width.

## Persistent layout state

Storage key:

`cew.documentDiscovery.workbench.v2`

Persisted state:

- `leftWidth`
- `rightWidth`
- `leftVisible`
- `rightVisible`
- `activeNav`
- `activeInspector`

This state is presentation-only. It has no engineering, semantic, learning, evidence, or canonical authority.

## Keyboard contract

- `Ctrl+B` — toggle Primary Sidebar;
- `Ctrl+J` — toggle Auxiliary Sidebar;
- `Alt+1` — Pagine;
- `Alt+2` — Primitive;
- `Alt+3` — Cluster;
- `Alt+4` — Da verificare;
- Arrow Up/Down while focus is in the Activity Rail — move focus among activity items;
- Arrow Left/Right on a focused sash — resize the associated sidebar.

Keyboard commands are presentation/navigation commands only.

## Result semantics

Execution completion and evidence acquisition are separate states.

`ANALYSIS_COMPLETED` does not imply `GRAPHIC_EVIDENCE_FOUND`.

If analysis completes with `0 primitive` and `0 cluster`, the UI must show:

`NESSUNA_REGIONE_GRAFICA_ACQUISITA -> VERIFICA_NECESSARIA`

It must not display a green success state for graphic acquisition.

Ordinary panel copy may render this state as **“Nessuna regione grafica acquisita”** while preserving the machine token in logs/contracts.

## Authority invariants

- `automatic_semantic_authority = NONE`;
- automatic semantic labels remain disabled;
- unregistered preview training remains `BLOCKED`;
- canonical write remains `BLOCKED`;
- structural identity remains `BLOCKED`;
- engineering authority effect remains `NONE`;
- original document remains evidentiary authority;
- panel/layout state is presentation state only.

## Browser materialization gate

A canonical workbench release is not valid merely because its CSS/JavaScript markers exist in generated HTML.

The dedicated browser gate must start the **real mounted FastAPI application**, navigate Chromium to `/workbench/document-discovery`, and prove all of the following before any Render deployment or HVA:

1. HTTP response identifies `X-CEW-Document-Workbench: PROFESSIONAL_V2`;
2. HTTP response identifies `X-CEW-Panel-Architecture: ACTIVITY_PRIMARY_EDITOR_AUXILIARY_STATUS`;
3. HTTP response identifies the current panel-quality layer;
4. no browser startup JavaScript or console error occurs;
5. `body.cew-professional-document` is active;
6. Activity Rail materializes;
7. Primary Sidebar header/content materialize;
8. left sash materializes;
9. editor bar and document canvas materialize;
10. Auxiliary Sidebar header/tabs materialize;
11. right sash materializes;
12. status bar materializes;
13. title/provider are actually composed into the professional title bar;
14. Primary Sidebar collapse/restore expands/contracts the editor as expected;
15. Auxiliary Sidebar collapse persists through `cew.documentDiscovery.workbench.v2`;
16. blocked training keeps the `decision` tab unavailable;
17. mature-panel keyboard/accessibility state is functional;
18. duplicate active-view title is not rendered inside the Primary Sidebar body.

A screenshot or HVA showing the legacy composition on a `PROFESSIONAL_V2` candidate is an explicit `UI_MATERIALIZATION_FAIL`, even when static marker tests, build, security, and `/readyz` pass.

## Change policy

The topology, part ownership, persistence schema, panel bounds, panel-quality invariants or authority boundaries may change only through:

1. an update to this architecture document;
2. an update to `automation/CEW_DOCUMENT_WORKBENCH_PANEL_CONTRACT_v2.json` when the machine contract changes;
3. deterministic validation;
4. mounted-route browser validation;
5. exact-head CI/security;
6. focused human HVA.

Pixel styling and ordinary bug fixes do not redefine topology, but they still must preserve the browser materialization gate.
