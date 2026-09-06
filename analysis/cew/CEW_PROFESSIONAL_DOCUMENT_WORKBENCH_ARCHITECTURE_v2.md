# CEW Professional Document Workbench v2 — canonical panel architecture

## Decision

The Document Discovery Workspace no longer evolves through local layout experiments. The repository adopts one stable workbench topology for document acquisition, graphic inspection and later governed human teaching.

This is a **workbench architecture**, not a visual clone of another product. The user-provided Devin/Cascade-style screenshot is treated as an interaction benchmark only. The implementation is grounded in open-source workbench patterns that can be inspected and audited.

## Open-source references used

1. **Microsoft VS Code — Agents Window layout**  
   `https://github.com/microsoft/vscode/blob/main/src/vs/sessions/LAYOUT.md`

   Adopted principles:
   - explicit ownership of each workbench part;
   - a flexible central surface absorbs general resize;
   - side parts preserve user-established sizes;
   - layout state is restored independently from domain state.

2. **Microsoft VS Code — workbench organization**  
   `https://github.com/microsoft/vscode/wiki/Source-Code-Organization`

   Adopted principle: the workbench shell is infrastructure; document-discovery features contribute views and state without owning the shell itself.

3. **OpenHands Agent Canvas**  
   `https://github.com/OpenHands/agent-canvas`

   Adopted principle: one persistent workspace can coordinate several tool surfaces while keeping UI state distinct from execution/runtime authority.

No third-party source code or branding is copied into CEW.

## Frozen upstream baselines

- Document acquisition/runtime HVA baseline: `320755e66a7263f1842f73dc14fb9a0ea8ccd7f8`.
- Human orientation/zoom/pan/cluster-selection baseline: `5db4e6bdf1b7a6853edd342ef9cc914e0e74ad91`.
- First professional-workbench checkpoint: `94f26d36b4b3fa6f97891950e0f0bb05d9c2158d`, frozen as `checkpoint/cew-professional-document-workbench-v1-94f26d3`.

The v2 shell is UI-only. It must not modify PDF parsing, raster/vector recovery, primitive discovery, clustering, SourceVersion/Page governance, learning receipts or canonical-write authority.

## Canonical topology

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ TITLE BAR — Document Discovery Workspace · provider/runtime state           │
├──────────────────────────────────────────────────────────────────────────────┤
│ COMMAND BAR — project · governed source · analyze · file · preview          │
├────┬──────────────────┬─┬──────────────────────────────┬─┬──────────────────┤
│    │ PRIMARY SIDEBAR  │ │ EDITOR / DOCUMENT CANVAS     │ │ AUXILIARY SIDEBAR│
│ A  │                  │ │                              │ │                  │
│ C  │ Pagine           │ │ editor tab / page identity   │ │ Proprietà        │
│ T  │ Primitive        │ │                              │ │ Provenienza      │
│ I  │ Cluster          │ │ original document surface    │ │ Decisione*       │
│ V  │ Da verificare    │ │                              │ │                  │
│ I  │                  │ │ viewport tools               │ │ * governed only  │
│ T  │                  │ │                              │ │                  │
│ Y  │                  │ │                              │ │                  │
├────┴──────────────────┴─┴──────────────────────────────┴─┴──────────────────┤
│ STATUS BAR — page · zoom · rotation · renderer · primitives · clusters ... │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Activity rail

The rail switches the active primary view. It does not contain viewport tools or document semantics. Clicking the currently active rail item may collapse the Primary Sidebar; selecting any view reopens it.

Stable view IDs:

- `pages`
- `primitives`
- `clusters`
- `verify`

### Primary Sidebar

Purpose: **find and navigate evidence**.

It is horizontally resizable, collapsible and persistent. Width bounds are governed by the machine-readable contract. Resizing the Primary Sidebar must not resize the Auxiliary Sidebar; the Editor Canvas absorbs the remaining width.

### Editor / document canvas

Purpose: **make the original document the dominant human surface**.

The editor region owns:

- page display;
- fit page / fit width;
- wheel zoom centered on the pointer;
- drag pan;
- 90° rotations;
- direct cluster hotspot selection.

Viewport tools remain anchored to the editor viewport, never to the moving page image. Actual zoom percentage belongs in the Status Bar; the toolbar remains compact.

### Auxiliary Sidebar

Purpose: **inspect the current selection and its authority**.

Canonical tabs:

- `properties`
- `provenance`
- `decision`

`decision` is hidden unless governed teaching is enabled. The blocked preview therefore never presents an editable training form as the main right-hand surface.

The Auxiliary Sidebar is horizontally resizable, collapsible and persistent independently of the Primary Sidebar.

### Status Bar

Persistent compact state:

- current page;
- zoom;
- rotation;
- renderer / preview mode;
- primitive count;
- cluster count;
- source-registration state;
- training state.

## Layout state controller

UI layout state is persisted under:

`cew.documentDiscovery.workbench.v2`

Persisted values:

- `leftWidth`
- `rightWidth`
- `leftVisible`
- `rightVisible`
- `activeNav`
- `activeInspector`

This state has **no evidentiary or engineering authority**. It is presentation-only state and is never part of SourceVersion, Page, Observation, ObjectCandidate or canonical CAD identity.

## Result semantics

Execution completion and evidence acquisition remain separate facts.

`ANALYSIS_COMPLETED != GRAPHIC_EVIDENCE_FOUND`

When analysis completes with zero primitives and zero clusters, the workbench must show:

`NESSUNA_REGIONE_GRAFICA_ACQUISITA -> VERIFICA_NECESSARIA`

It must not render the normal green success state.

## Authority invariants

- automatic semantic authority: `NONE`;
- automatic semantic labels: disabled;
- unregistered preview training: `BLOCKED`;
- canonical write: `BLOCKED`;
- structural identity: `BLOCKED`;
- engineering authority effect: `NONE`;
- original document: evidentiary authority.

## Change policy

The following are now **architecture changes** and require a contract/spec update plus deterministic gate:

- adding/removing a top-level workbench part;
- changing ownership of a part;
- changing persisted layout state;
- allowing a side panel to absorb global resize instead of the central editor;
- moving human-decision controls outside the governed contextual inspector;
- changing authority boundaries.

The following do **not** change the architecture and belong in implementation/tests only:

- exact colors;
- icon glyphs;
- pixel-level padding;
- individual row/card styling;
- small action placement changes inside an owned panel.

## Machine-readable contract

`automation/CEW_DOCUMENT_WORKBENCH_PANEL_CONTRACT_v2.json`

The deterministic validator must prove the code, the HTML shell and this contract remain aligned before deployment.
