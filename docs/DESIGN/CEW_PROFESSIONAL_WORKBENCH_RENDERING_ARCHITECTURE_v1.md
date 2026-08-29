# CEW Professional Evidence Workbench — Rendering Architecture v1

**Status:** `DESIGN_BASELINE_PROPOSED`  
**Authority effect:** `NONE`  
**Canonical write:** `false`

## 1. Objective

Provide a performant, reproducible rendering architecture for very large existing-structure drawings and derived technical scenes without reintroducing on-request full-PDF rasterization or creating a parallel source authority.

## 2. Architectural split

The Workbench has two rendering pipelines:

### Source pipeline
Verified immutable source → multiresolution tiles → Source Viewport.

### Technical pipeline
Governed extraction/model records → normalized technical scene → Technical Viewport.

A registration layer coordinates them but does not merge their identities.

## 3. Source rendering — reuse F3

F3 OpenSeadragon/DZI is the mandatory starting point.

Reuse:

- OpenSeadragon 5.0.1 behavior;
- DZI pyramid concept;
- libvips tile generation;
- navigator/overview;
- deep-link to task/EvidenceRegion;
- 300 dpi baseline assets where current F3 contract applies;
- source identity/read-only guards.

The B1.8 single-PNG build cache remains a fallback/test asset, not the primary professional zoom architecture.

## 4. Immutable source-tile artifacts

Tile pyramid identity must be bound to:

- SourceVersion id;
- source SHA-256;
- Page id;
- render policy/version;
- pixel density;
- tile policy/version;
- build revision;
- manifest SHA/version.

A runtime must never serve a tile pyramid whose manifest/source identity does not match the requested source version.

## 5. Runtime behavior

Managed runtime should serve prebuilt/static multires assets or equivalent immutable object storage assets.

No normal pan/zoom interaction triggers full PDF rasterization.

A missing/mismatched pyramid fails closed with source-unavailable state; it does not silently fall back to another source/version.

## 6. Technical scene pipeline

Upstream inputs:

- Dual Vector Agreement outputs;
- normalized document primitives/text/dimensions;
- F6/M0G governed structural projection;
- EvidenceRegion/Observation links;
- ReadingIssue/WorkingEdit state.

The client consumes a versioned scene manifest plus scene chunks/objects.

## 7. Technical rendering technology

V1 target is an SVG-first interactive scene for ordinary engineering-sheet complexity because it provides:

- direct object ids;
- selection/hit testing;
- crisp vector zoom;
- accessible DOM labels where practical;
- layer grouping;
- in-place text/geometry decoration;
- straightforward export/debug inspection.

The scene contract must not depend on SVG semantics so a future Canvas/WebGL renderer can be introduced for very large object counts without changing authority/data contracts.

## 8. Scene chunking and culling

The architecture must permit spatial chunking/indexing.

For large scenes:

- load visible/near-visible chunks;
- keep object metadata available for search/selection;
- cull hidden layers;
- avoid rebuilding the entire scene on each pan/zoom;
- preserve stable object ids across chunk loads.

No fixed object-count threshold is declared until measured on representative drawings.

## 9. Source/technical overlay

Overlay has one visual coordinate basis at a time.

When `RegistrationTransform=VERIFIED`:

- source remains the base deep-zoom surface;
- technical scene is transformed into source-view coordinates or both are mapped into a common viewport transform;
- opacity is view state;
- technical layers remain individually toggleable;
- source/technical selection remains identifiable.

When registration is not VERIFIED, overlay is unavailable.

## 10. Spatial synchronization

For SPLIT + SPATIAL_LOCKED:

1. active viewport emits transform change;
2. workbench maps centre/scale/rotation through verified registration;
3. peer viewport updates without feeding an infinite feedback loop;
4. residual/validity state is continuously checked against registration revision.

Semantic selection sync may operate independently.

## 11. Orientation

Source orientation is display state layered over original Page coordinates.

A useful automatic orientation may be proposed, but original page transform/orientation remains reproducible.

Technical scene orientation follows its coordinate-space contract. Rotation for presentation cannot mutate model/source coordinates.

## 12. Cache hierarchy

Conceptual hierarchy:

1. immutable source bytes;
2. immutable source tile pyramid;
3. immutable extraction/agreement artifacts;
4. immutable base technical scene revision;
5. mutable/non-canonical working session deltas;
6. transient viewport state.

Lower levels cannot overwrite higher-authority source data.

## 13. Build/runtime separation

Expensive operations should occur outside interactive runtime where feasible:

- PDF raster/tile generation;
- vector extraction;
- Docling/PyMuPDF comparison;
- scene normalization/indexing.

Interactive runtime performs:

- asset lookup;
- viewport delivery;
- scene/query delivery;
- working-state/audit operations;
- authorization checks.

## 14. Failure modes

Fail closed on:

- source hash mismatch;
- tile manifest/source mismatch;
- scene/source revision mismatch;
- missing extraction agreement required by a scene object;
- stale registration transform;
- unknown coordinate space;
- structural projection without governed object id;
- unsupported scene schema.

The user should retain access to the verified source whenever source integrity itself remains valid.

## 15. Performance instrumentation

Measure, do not prematurely set pass thresholds:

- initial source first-useful-render;
- tile latency/cache hit;
- pan/zoom frame responsiveness;
- technical scene first meaningful render;
- visible object count;
- selection latency;
- overlay transform latency;
- memory use on representative desktop/tablet devices.

Performance metrics are product evidence, not engineering authority.

## 16. Accessibility rendering requirements

Canvas/WebGL fallback must not erase semantic access. If non-DOM rendering is introduced, selected objects/issues must still have an accessible inspector/list representation and full keyboard routes.

## 17. Security and isolation

All source/scene/tile requests remain scoped to project/source/workbench context. Cache keys must include project/source revision identity as applicable; no cross-project asset leakage is permitted.

## 18. Acceptance criteria

Rendering architecture is implemented only when tests demonstrate:

- F3-class DZI source viewer is used by the Workbench;
- no interactive full-page PyMuPDF raster call is required for zoom/pan;
- source assets are manifest/hash/revision bound;
- technical scene is vector and selectable;
- overlay fails closed without verified registration;
- working edits do not rebuild/mutate base scene authority;
- representative large drawing remains navigable without Render instance failure;
- source remains accessible if technical scene fails.
