# CEW Engineering Design System v1

Status: `UX FOUNDATION — EXPERIMENTAL / NON-PROMOTIVE`

## 1. Role

The CEW Engineering Design System (EDS) is a CEW-owned visual and interaction language for civil/structural engineering work. Third-party projects may supply behavior or specialist rendering engines, but they do not define CEW identity or engineering semantics.

Layers: `tokens → primitives → engineering components → workspaces → project applications`.

## 2. Engineering-first components

A component represents a professional concept before a visual pattern. `EngineeringEvidenceCard`, for example, is a contracted representation of entity/property, source basis, epistemic state, model coherence and next technical action; it is not a generic card.

## 3. Independent state systems

### Epistemic
`DOC / MIS / RIF / INF / ND` — how do we know this property?

### Workflow
`READY / RUNNING / IN_REVIEW / BLOCKED / COMPLETE / FAILED` — where is the task in its process?

### Engineering severity
`OK / ATTENTION / CRITICAL / NOT_ASSESSED` — what is the engineering significance?

The taxonomies are semantically disjoint. Color alone is forbidden: every state includes text, icon and another visual cue such as stroke/pattern/shape. `ND` is missing knowledge, not an error.

## 4. Visual character

Precise, calm, technical, dense but legible; neutral surfaces; restrained engineering accents; strong alignment; compact controls; high information-to-decoration ratio; motion limited to orientation, state change and spatial continuity. The experience should resemble a high-quality technical instrument rather than a consumer dashboard.

## 5. Typography and numeric data

System sans for primary text; monospaced stack for IDs, coordinates, hashes and numeric tabulation; tabular numbers for dimensions, loads, results and quantities; values and units remain adjacent; significant digits are governed by engineering/domain rules.

## 6. Density

Default workstation profile: `COMPACT_PROFESSIONAL`. Base spacing 4 px, common control 32 px, dense table row 32–36 px. Compact density may never remove accessible hit areas or legibility.

## 7. Initial component catalog

Machine-readable catalog: `ui/foundation/contracts/component-catalog.json`.
Required: `ProjectContextBar`, `EngineeringEvidenceCard`, `EpistemicStateMark`, `EngineeringInspector`, `EvidenceDecisionTrail`, `HumanDecisionPanel`, `TechnicalDataTable`, `SourceModelSplitView`, `ProvenanceDrawer`, `EngineeringStateBanner`.

## 8. Open-source composition policy

CEW adopts behavior, not brand identity.
- React Aria Components: preferred accessible primitive layer for UX1.
- shadcn registry model: preferred CEW-owned component distribution pattern; not CEW visual identity.
- TanStack Table: technical table engine; stable major only at adoption gate.
- Apache ECharts: analysis/result visualization.
- React Flow / xyflow: provenance/dependency/knowledge graph canvas.
- OpenSeadragon: high-resolution source drawing navigation.
- That Open Components + web-ifc: BIM/3D interaction candidate behind CEW entity adapters.
- Storybook: authoritative component catalog when frontend package exists.
- Playwright: end-to-end/visual regression.
- axe-core: automated accessibility gate plus manual professional review.

Versions are pinned at implementation acceptance, not in the conceptual contract.

## 9. Third-party boundary

A library may not define canonical CEW identity, turn viewer geometry into evidence authority, promote epistemic state, create structural binding, switch model/scenario generation silently, or replace CEW decision receipts.

## 10. Accessibility

Critical workflows are keyboard-operable; focus remains visible; state is not color-only; synchronized selection remains understandable at high zoom; dense tables expose headers/units/row identity; reduced motion is respected.

## 11. UX1 boundary

UX0 defines the system. UX1 creates the **single CEW Workbench frontend boundary**. No separate React app is embedded in every legacy viewer. Existing source/3D viewers enter through explicit ports.
