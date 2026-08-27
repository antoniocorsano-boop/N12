# CEW Reconstruction Workspace v1 — Contract

**Program:** `CEW-GOAL-01`  
**Work package:** `CEW-B2-RECONSTRUCTION-PROPERTIES`  
**Preparation status:** `PARALLEL_PREPARATION_NOT_RELEASED`  
**Blocking predecessor:** `CEW-B1-SOURCE-EVIDENCE-JOURNEY / CEW-B1-PROD-01`  
**Engineering authority:** `knowledge/CURRENT_STATE.json` and referenced governed canonical artifacts.

## Purpose

The Reconstruction Workspace is the engineer-facing surface for understanding how documentary evidence becomes the current structural geometry/topology without turning drawing interpretation, visual proximity or UI state into engineering authority.

It integrates P4–P6:

`historical/current context -> geometry -> topology -> stable structural identity`

It is not a second geometric model and it is not a solver preprocessor.

## Current N12 basis

The current authority declares M0-G `FROZEN_PASS_WITH_WATCH_REVALIDATED_B055`. The downstream geometric handoff is `data/canonical/M0G_GEOMETRY_HANDOFF_v1.json`.

The frozen superstructure inventory currently referenced by that handoff is:

- 629 analytical nodes;
- 464 rigid joint links;
- 359 ordinary structural members;
- 232 ordinary beams;
- 127 vertical column segments;
- 3 roof ridge axes and 3 eaves edge sets retained outside ordinary frame connectivity unless later evidence authorizes a structural-member role.

These counts are display/reporting projections of the authority artifact; the workspace must load current ledgers rather than hard-code them.

`model/M0-G/STATUS.md` is historical and must not override the later CURRENT/handoff state.

## Primary user questions

1. Where is the structural object?
2. What source/evidence supports its location and identity?
3. How is it connected to adjacent structural objects?
4. Is the displayed geometry documented, measured, supported, modeled or still uncertain?
5. Which unresolved watch affects only this object and which one affects a wider scope?
6. What changed between model generations and why?

## Workspace layout

### 1. Model navigator

Primary navigation uses engineering concepts:

- storey / structural level;
- beams;
- columns;
- rigid zones / offsets;
- foundations;
- roof special geometry;
- open geometry/topology watches.

Internal canonical IDs remain available in technical details and are never the only way to find an object.

### 2. Coordinated views

The workspace must provide coordinated selection across:

- **2D plan/elevation view** — storey geometry, supports and member connectivity;
- **3D structural view** — the same stable entities in the current model generation;
- **table view** — entity identity, endpoints, storey, role, evidence/use state and watches;
- **source/evidence context** — links back into Source Hub/Evidence Workspace for the selected object where bindings exist.

Selection in one view selects the same CEW entity in the other views. No nearest-object heuristic may silently create an identity or structural binding.

### 3. Selected-object inspector

For the selected object show separately:

- stable CEW / N12 entity identity;
- structural role;
- geometry/topology state;
- coordinate frame and level;
- connected entities;
- rigid-offset semantics where applicable;
- source/evidence references;
- current watches/residuals;
- downstream-use eligibility;
- generation lineage.

A field displayed with numerical precision must retain its evidence/authority state. Numerical precision is never evidence precision.

## Geometry authority rules

The workspace consumes the current handoff and ledgers referenced by it, including:

- `M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv`;
- `M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv`;
- `M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv`;
- `ROOF_G5_SPECIAL_FEATURES_3D_CURRENT_v1.csv`;
- `M0G_GLOBAL_TOPOLOGY_GATE_v1.csv`.

Rules that must remain visible and executable:

- beam-face nodes and support-core nodes are distinct analytical roles;
- rigid links are analytical constraints, not ordinary structural members;
- beam-face-to-core collapse is forbidden;
- geometric proximity does not create connectivity;
- roof ridge/eave geometry is not automatically a structural member;
- relative G1–G5 Z may be used as registered;
- absolute/project/geodetic Z remains ND unless separately evidenced;
- terrace supports `a–d` terminate where documented and are not extended by UI continuity;
- a model watch is not silently repaired for visual completeness.

## Watches and residuals

The UI uses explicit scoped overlays instead of a single global “model incomplete” banner.

Minimum watch classes from the current geometry handoff include:

- section/evidence watches;
- roof-Z watches;
- eaves centerline watch;
- ridge XY evidence-state watch;
- absolute-Z watch;
- source/model binding residuals.

A local watch blocks only uses that depend on it unless an explicit dependency propagates the block.

## Historical / current separation

The user must be able to distinguish:

- historical/documentary geometry;
- current surveyed or revalidated geometry;
- analytical representation;
- scenario/modeling transformations.

No scenario or solver placement may rewrite the historical/current geometry evidence chain.

## Human-factors acceptance

A structural engineer unfamiliar with the repository must be able to:

1. open the building model;
2. choose a storey and a member without knowing an internal ID;
3. understand its structural role and connectivity;
4. see whether a property/watch affects it;
5. navigate back to supporting evidence;
6. distinguish evidence geometry from analytical idealization;
7. inspect technical IDs/provenance only when needed.

## Forbidden

- creating connectivity from visual proximity;
- treating a visually continuous line as one member without identity authority;
- hiding rigid offsets to make the model look simpler;
- auto-closing a watch to render a clean model;
- using `model/M0-G/STATUS.md` as current authority;
- using solver output to correct source evidence;
- promoting modeled coordinates to DOC/MIS evidence;
- direct canonical writes from the workspace.

## Release condition

This contract may become an executable B2 workspace only after `CEW-B1-PROD-01` is closed and B2 is formally released by the product orchestrator.
