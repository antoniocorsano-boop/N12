# CEW Professional Document Workbench v2

## Status

This document is the canonical workbench topology contract for Document Discovery. It replaces incremental viewer-layout experiments with one stable professional panel architecture.

A source-level/string validator is **not sufficient** to certify this UI. The workbench must also execute successfully in a real browser against the mounted FastAPI route and materialize the canonical parts in the DOM.

## Reference model

The topology is grounded in mature, inspectable workbench patterns rather than copied proprietary UI:

- **Microsoft VS Code — Agents Window layout**: stable part ownership, a flexible central surface, independently sized side parts, and persisted layout state;
- **Microsoft VS Code workbench**: shell infrastructure is separated from feature contributions and layout controllers own restoration rather than domain state;
- **OpenHands Agent Canvas**: one workspace coordinates multiple tool surfaces while UI state remains distinct from agent/execution authority.

A Devin/Cascade-style interface may be used as a behavioral usability benchmark, but CEW does not copy third-party branding or proprietary source code.

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

## Activity rail and Primary Sidebar

Stable primary views:

- `pages`
- `primitives`
- `clusters`
- `verify`

The activity rail is persistent. Selecting the already-active primary view toggles the Primary Sidebar, so a collapsed sidebar remains recoverable without a hidden control.

The Primary Sidebar is independently resizable and collapsible. Its width is persisted within the range defined by `CEW_DOCUMENT_WORKBENCH_PANEL_CONTRACT_v2.json`.

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

## Sashes and resize behavior

Left and right sidebars are independently resizable by sashes.

Required interaction:

- pointer drag changes the relevant panel only;
- keyboard Left/Right adjusts a focused sash;
- double click restores the default width;
- width is clamped to the machine-readable bounds;
- the editor canvas absorbs the complementary change.

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

## Result semantics

Execution completion and evidence acquisition are separate states.

`ANALYSIS_COMPLETED` does not imply `GRAPHIC_EVIDENCE_FOUND`.

If analysis completes with `0 primitive` and `0 cluster`, the UI must show:

`NESSUNA_REGIONE_GRAFICA_ACQUISITA -> VERIFICA_NECESSARIA`

It must not display a green success state for graphic acquisition.

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
3. no browser startup JavaScript or console error occurs;
4. `body.cew-professional-document` is active;
5. Activity Rail materializes;
6. Primary Sidebar header/content materialize;
7. left sash materializes;
8. editor bar and document canvas materialize;
9. Auxiliary Sidebar header/tabs materialize;
10. right sash materializes;
11. status bar materializes;
12. title/provider are actually composed into the professional title bar;
13. Primary Sidebar collapse/restore expands/contracts the editor as expected;
14. Auxiliary Sidebar collapse persists through `cew.documentDiscovery.workbench.v2`;
15. blocked training keeps the `decision` tab unavailable.

A screenshot or HVA showing the legacy composition on a `PROFESSIONAL_V2` candidate is an explicit `UI_MATERIALIZATION_FAIL`, even when static marker tests, build, security, and `/readyz` pass.

## Change policy

The topology, part ownership, persistence schema, panel bounds, or authority boundaries may change only through:

1. an update to this architecture document;
2. an update to `automation/CEW_DOCUMENT_WORKBENCH_PANEL_CONTRACT_v2.json` when the machine contract changes;
3. deterministic validation;
4. mounted-route browser validation;
5. exact-head CI/security;
6. focused human HVA.

Pixel styling and ordinary bug fixes do not redefine topology, but they still must preserve the browser materialization gate.
