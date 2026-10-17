# CEW Evidence Resolution Workspace (ERW) v1

## Purpose

CEW Evidence Resolution Workspace is the human-adjudication environment used when structural evidence is incomplete, ambiguous, conflicting, source-unbound, or only partially readable.

It is not a generic PDF viewer and it is not a BIM authoring environment. Its purpose is to connect:

- immutable primary source documents;
- precise source regions and reproducible viewports;
- the current CEW structural interpretation;
- epistemic state (`DOC`, `MIS`, `RIF`, `INF`, `ND`);
- residuals and anomalies;
- candidate interpretations;
- human decisions;
- deterministic promotion gates.

Core rule: **no graphical convenience may silently increase epistemic authority**.

## Product outcome

When a gate produces a residual such as `ND`, `DOC_SOURCE_UNBOUND`, `DOC_DIRECT_PARTIAL`, `INF_STRONG_DRAFTING_RULE`, or a cross-source conflict, CEW shall be able to create a `ResolutionTask` that opens directly on the relevant drawing region and model context.

A technician shall be able to:

1. navigate the full technical drawing with deep zoom, pan and overview navigation;
2. inspect the primary source at native resolution without creating ad-hoc derivative crops as new authority;
3. switch visual-only enhancement layers on/off;
4. overlay CEW interpretation, nodes, members, sections, reinforcement evidence, residuals and anomalies;
5. inspect the corresponding 3D structural zone as currently interpreted;
6. isolate elements, orbit, pan, zoom, section and use transparency/x-ray;
7. compare 2D source evidence and 3D interpretation in synchronized views;
8. inspect conflicts and competing interpretations;
9. make a human disposition without being forced to resolve an unreadable case;
10. save a reproducible decision receipt and rerun the relevant gate.

## Mature-product patterns adopted

ERW intentionally adopts mature interaction patterns while retaining CEW-specific provenance semantics:

- synchronized 2D/3D navigation and drawing/model overlay;
- visual document comparison and registration;
- issue/residual anchoring to exact 2D or 3D locations;
- anomaly navigation that isolates implicated model objects;
- saved/reproducible viewpoints.

ERW does not inherit any commercial-product data model or epistemic behavior.

## Reference implementation stack

Preferred free/open implementation baseline:

- **OpenSeadragon** for deep-zoom tiled raster drawings;
- **libvips** for generation of tiled pyramids from immutable source renders;
- **PDF.js** for PDF page access/vector-friendly rendering where suitable;
- **SVG overlay** for first-generation hit-testing, labels, regions and markup;
- **Three.js/WebGL** for the CEW analytical structural 3D view.

IFC is an exchange target, not the initial canonical model. Full BIM-authoring capability is explicitly out of scope.

## Source authority model

The immutable primary file remains the authority. Derived representations are assistive only.

Preferred chain:

`immutable source PDF/image -> hash -> lossless/high-resolution render -> tiled pyramid -> viewport references`

A crop is a generated view, not a new source.

Every persisted source region shall use a stable coordinate system, preferably native source-pixel coordinates plus page identity and source hash.

## Main desktop layout

ERW shall support a resizable three-zone layout:

- **2D Source Viewer**;
- **3D Current Interpretation**;
- **Resolution / Evidence / Decision Panel**.

Supported presentation modes:

- 2D only;
- 3D only;
- vertical split;
- horizontal split;
- source/model overlay;
- source/source comparison.

## 2D source viewer requirements

Minimum functions:

- deep zoom;
- pan;
- overview navigator;
- fit page / fit region;
- rotation;
- stable native coordinate readout;
- permalink to exact evidence region;
- show/hide semantic overlays;
- original/enhanced toggle.

Visual-only enhancement may include contrast, levels, grayscale, inversion, sharpening and thresholding. Enhancements shall never overwrite the primary source or be treated as evidence by themselves.

## Semantic overlays

Selectable overlays shall include, as available:

- interpreted geometry;
- nodes/supports;
- axes and support faces;
- beams/columns/special members;
- identifiers;
- sections;
- reinforcement evidence;
- evidence regions;
- residuals;
- anomalies;
- candidate interpretations.

Visual grammar shall encode epistemic state independently of color so that state remains readable in monochrome and accessible modes.

## Epistemic 3D model

The 3D scene shall represent the building **as currently supportable by CEW evidence**, not as a visually completed idealization.

Each model property may carry its own epistemic state. Example:

- geometry: `DOC`;
- endpoints: `DOC`;
- section: `ND`;
- reinforcement: `ND`;
- source binding: unresolved or rejected.

Minimum 3D operations:

- orbit;
- pan;
- zoom;
- fit selected;
- isolate/hide;
- transparency/x-ray;
- section box / cutting plane;
- orthographic X/Y/Z views;
- storey/frame/run filtering;
- measurement;
- evidence links.

## 2D to 3D binding

The binding chain shall be explicit and auditable:

`source pixel -> sheet coordinates -> project XY -> model XYZ`

Transforms shall retain provenance, residual/error information and epistemic state. A convenient visual registration shall not imply documentary precision.

When registration is not documentary, the UI shall disclose the corresponding `MIS`/watch state.

## Drawing projection in 3D

Where a plan/elevation can be registered, ERW shall support projection of the source raster as a semi-transparent plane in the 3D scene, including independent opacity controls for drawing and model.

This projection is an inspection aid and may be used by consistency checks, but does not by itself promote evidence.

## Evidence Consistency Engine

ERW shall consume or produce `ConflictCandidate` / `EvidenceAnomaly` objects rather than silently correcting data.

Initial anomaly classes:

1. `SOURCE_MODEL_GEOMETRY` — registered source geometry differs from interpreted geometry beyond tolerance;
2. `SOURCE_TOPOLOGY` — source scheme topology conflicts with candidate member topology;
3. `SOURCE_SECTION` — source section and current member section conflict;
4. `CROSS_SOURCE` — two primary sources disagree;
5. `MODEL_INTERNAL` — disconnected, duplicate, off-plane or otherwise internally inconsistent interpretation;
6. `DOCUMENT_GRAMMAR` — possible authored shorthand/homologous-run pattern requiring adjudication.

Document-grammar findings can produce `INF_STRONG_DRAFTING_RULE` candidates but can never directly produce `DOC`.

## Candidate interpretations

ERW shall allow multiple candidate interpretations to coexist temporarily. The technician shall be able to toggle candidates in 2D/3D and inspect:

- supporting evidence;
- contradictory evidence;
- topology fit;
- section fit;
- authored drafting-grammar fit;
- unsupported assumptions;
- epistemic ceiling.

No percentage confidence shall substitute for this evidence list.

## Resolution outcomes

A technician may disposition a task as:

- `CONFIRMED`;
- `REJECTED`;
- `UNREADABLE`;
- `UNBOUND`;
- `NEEDS_BETTER_SOURCE`;
- `NEEDS_SITE_SURVEY`;
- `DEFER`.

`DEFER` and unresolved outcomes shall preserve explicit blocking scope so unrelated work can continue.

## Core data contracts

### EvidenceRegion

Required fields:

- `evidence_region_id`;
- `source_id`;
- `source_hash`;
- `page`;
- `coordinate_system`;
- `bbox`;
- `semantic_type`;
- `candidate_entity_ids`;
- `epistemic_state`;
- `created_by`.

### ResolutionTask

Required fields:

- `task_id`;
- `residual_id`;
- `question`;
- `domain`;
- `source_regions`;
- `model_entities`;
- `known_claims`;
- `unknown_claims`;
- `conflicts`;
- `suggested_actions`;
- `blocking_scope`;
- `status`.

### InterpretationCandidate

Required fields:

- `candidate_id`;
- `task_id`;
- `interpretation`;
- `model_delta`;
- `supporting_evidence`;
- `contradicting_evidence`;
- `epistemic_ceiling`.

### ResolutionDecision

Required fields:

- `decision_id`;
- `task_id`;
- `outcome`;
- `selected_candidate`;
- `human_observation`;
- `reason`;
- `evidence_regions`;
- `review_view`;
- `requested_epistemic_state`;
- `reviewer`;
- `timestamp`.

### ReviewView

A `ReviewView` shall preserve enough state to reproduce the adjudication context, including source/page, source viewport, enabled overlays, selected entities, 3D camera, cut/section state and visible candidates.

## Promotion boundary

The viewer and review UI shall never write directly to canonical structural datasets.

Flow:

`Residual -> ResolutionTask -> EvidencePack -> Human Review -> ResolutionDecision -> Validation/Promotion Gate -> Canonical update or retained residual`

A requested state above an object's `epistemic_ceiling` shall be rejected by the gate.

## Initial N12 validation cases

ERW shall initially be validated against real N12 residuals rather than synthetic demos.

### TAV-05A field-reading tasks

- `M1E-B06-R08`: `T5A-G01 / G01-R06`; length 1040 is `DOC`; quantity/diameter remain `ND`;
- `M1E-B06-R09`: `T5A-G07 / G07-R07`; length 865 is `DOC`; quantity/diameter remain `ND`;
- `M1E-B06-R10`: `T5A-G05 / G05-R04`; intermediate sagomato is directly partial; remaining dimensions are `ND`.

### TAV-06A source-binding task

- `M1E-B06-R11`: `G5-B017` versus `T6A-G03`; the source scheme is directly documented but the current topology does not support direct binding. ERW shall display the source scheme, current B017 model context and the topology conflict, permitting `UNBOUND` without forcing assignment.

## Delivery slices

### ERW-0 — Deep Drawing Viewer

- source manifest;
- immutable source hash;
- tiled pyramid contract;
- OpenSeadragon viewer;
- pan/zoom/overview;
- native source coordinates;
- open task at evidence region.

### ERW-1 — Evidence Overlay

- SVG overlay;
- EvidenceRegion rendering;
- nodes/members/labels;
- residual markers;
- epistemic visual grammar.

### ERW-2 — Structural 3D

- consume frozen CEW structural model;
- storey/member isolation;
- epistemic property display;
- orbit/pan/zoom/section/transparency.

### ERW-3 — Synchronized 2D/3D

- register one N12 drawing first;
- bidirectional selection;
- saved source/model viewpoints;
- optional drawing plane projection.

### ERW-4 — Resolution Task

- task queue;
- known/unknown/conflict panels;
- candidate interpretations;
- explicit human outcomes.

### ERW-5 — Decision Receipt and Gate

- reproducible ReviewView;
- immutable ResolutionDecision receipt;
- promotion validation;
- rerun relevant CEW gate;
- retained residual when evidence remains insufficient.

## Acceptance criterion for first end-to-end MVP

A technician unfamiliar with repository internals shall be able to open `M1E-B06-R11`, understand what is missing, inspect the primary evidence with unrestricted pan/zoom, inspect B017 in the 3D model, understand why the current T6A-G03 binding is incompatible, record `UNBOUND`, and later reproduce the exact review context without opening a CSV or GitHub file.

## Explicit non-goals for v1

- photorealistic digital twin;
- CAD/BIM authoring;
- automatic completion of unreadable structural data;
- automatic promotion of inference to `DOC`;
- replacement of primary source files with enhanced derivatives;
- generic IFC-first canonical modeling.
