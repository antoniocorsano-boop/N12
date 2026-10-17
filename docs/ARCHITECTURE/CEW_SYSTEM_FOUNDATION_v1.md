# Civil Existing Workflow — System Foundation v1

## Status

`FOUNDATION_BASELINE`

This document defines the product-level foundation of Civil Existing Workflow (CEW). It sits above individual domain slices such as M0-G, M1A, M1L, foundations, ERW, and calculation handoff.

N12 is the reference project used to prove the architecture against real existing-building evidence.

## Product mission

CEW is an evidence-first system for reconstructing, validating, maintaining, and handing off structural knowledge about existing buildings from heterogeneous historical and current sources.

The core product loop is:

`Source -> Observation -> Candidate interpretation -> Binding -> Validation -> Canonical knowledge -> Residual/Anomaly -> Human/Deterministic resolution -> Promotion -> Calculation handoff`

CEW is not a generic PDF viewer, generic BIM authoring environment, or an AI chat wrapper.

## Constitutional rules

1. Primary sources remain immutable.
2. Every engineering claim that may feed canonical knowledge shall be traceable to evidence.
3. Observation and interpretation are distinct objects.
4. AI may create observations, candidates, bindings, anomalies, suggested resolutions and drafts; AI does not directly create canonical authority.
5. Epistemic authority shall never be increased by convenience, similarity, visual plausibility, language-model confidence, or conversation memory.
6. The canonical epistemic regime remains `DOC`, `MIS`, `RIF`, `INF`, `ND`.
7. Workflow state and epistemic state are separate dimensions.
8. Every inference method has an epistemic ceiling.
9. Residuals and anomalies are first-class workflow objects and shall remain explicit when unresolved.
10. Unrelated residuals shall not block global progress unless an explicit gate declares the dependency.
11. Human review is requested only where human judgment or accountability adds value.
12. Important decisions shall be reproducible from source hashes, regions, observations, model context, rules, reviewer disposition and validator output.
13. The calculation model is downstream of canonical knowledge and declared analysis assumptions.
14. A calculation result cannot retroactively establish documentary fact.
15. A frozen canonical domain may only be changed through an explicit reopen procedure.

## Authority hierarchy

The mandatory direction of authority is:

`Primary sources -> Observations -> Canonical knowledge -> Analysis assumptions -> Calculation model -> Results`

Derived renderings, crops, enhanced views, OCR text, embeddings, AI summaries and numerical analyses are assistive representations unless explicitly promoted through a valid gate.

## Core bounded domains

### 1. Source & Evidence Repository

Responsible for:
- immutable source identity and versioning;
- hashes and source authority;
- pages, regions and coordinate systems;
- derived viewer assets and tile pyramids;
- reproducible evidence navigation.

### 2. Document Intelligence

Responsible for:
- document classification;
- layout/region detection;
- literal technical observations;
- candidate technical readings;
- authored drawing-grammar candidates.

It produces observations and candidates, never canonical structural facts directly.

### 3. Structural Knowledge Graph

Responsible for:
- structural entities;
- claims/properties;
- evidence bindings;
- per-property epistemic state;
- temporal states (`ORIGINAL_DESIGN`, `AS_BUILT`, `CURRENT_OBSERVED`, `ASSESSMENT_MODEL`);
- provenance and dependency relationships.

### 4. Structural Model Workspace

Responsible for:
- 2D/3D representation of the current supportable interpretation;
- navigation and selection;
- model-source overlays;
- frozen-model consumption;
- non-authoritative visual aids.

### 5. Evidence Resolution Workspace (ERW)

Responsible for:
- residual/anomaly task navigation;
- source region + model context;
- candidate comparison;
- human dispositions;
- reproducible review views.

`CEW_EVIDENCE_RESOLUTION_WORKSPACE_v1.md` is a subordinate implementation contract of this foundation.

### 6. Validation & Promotion Engine

Responsible for:
- schema and invariant validation;
- topology and consistency checks;
- epistemic-ceiling enforcement;
- promotion/rejection of candidate assertions;
- receipts;
- formal reopen rules.

### 7. Analysis & Calculation Handoff

Responsible for:
- transformation from canonical knowledge to an assessment/calculation model;
- explicit assumptions;
- load/material/geotechnical model inputs;
- coverage and unresolved-blocker reporting;
- export to downstream analysis software.

### 8. Reporting & Fascicolo

Responsible for:
- evidence coverage;
- unresolved knowledge;
- source provenance;
- decision history;
- calculation handoff documentation;
- project reports and fascicolo outputs.

## Core object model

CEW shall progressively converge on these product objects:

- `Project`
- `Source`
- `SourceVersion`
- `Page`
- `DerivedAsset`
- `EvidenceRegion`
- `Observation`
- `Assertion`
- `Binding`
- `StructuralEntity`
- `StructuralProperty`
- `DrawingRule`
- `EvidenceAnomaly`
- `Residual`
- `ResolutionTask`
- `EvidencePack`
- `InterpretationCandidate`
- `ReviewView`
- `ResolutionDecision`
- `GateResult`
- `Receipt`
- `CanonicalSnapshot`
- `AnalysisAssumption`
- `CalculationHandoff`

CSV files may remain canonical interchange/projection artifacts during migration, but the conceptual authority shall follow these objects and relationships.

## AI operating model

CEW shall use specialist workers/agents rather than one unconstrained general agent. Initial roles:

- Source Curator
- Layout Reader
- Geometry Reader
- Structural Drawing Reader
- Reinforcement Reader
- Text/Notation Reader
- Evidence Binder
- Consistency Agent
- Residual Manager
- Reviewer Assistant
- Reporting Agent

Workers shall operate on bounded `EvidencePack` inputs whenever possible. A worker output shall declare its evidence, method, generated object type and epistemic ceiling.

## Promotion boundary

The mandatory promotion flow is:

`Observation/Candidate -> Validation -> optional Human Review -> Promotion Gate -> Canonical Assertion or retained Residual`

The UI, AI worker and 2D/3D viewer shall not write directly into frozen canonical structural datasets.

A promotion gate shall reject at minimum:

- missing immutable source identity;
- missing evidence region when a source-region assertion is required;
- unresolved source/member binding;
- open contradiction that invalidates the claim;
- requested state above epistemic ceiling;
- missing required human disposition;
- failed deterministic validator.

## Human experience contract

CEW shall expose engineering work in terms of tasks and decisions, not repository internals.

A technician shall be able to:

1. understand project state and blockers from a control room;
2. open a structural entity or unresolved question;
3. reach the exact primary-source context and current 2D/3D model context;
4. understand known, unknown and conflicting information;
5. inspect provenance for any important value through `Show evidence`;
6. decide, defer, reject or request better evidence without being forced to invent a value;
7. continue to the next relevant task;
8. produce a reproducible handoff/report without manually editing canonical CSV files.

Repository files, commits, validators and receipts remain available for audit but are not the primary user interface.

## Reference implementation baseline

Initial implementation direction:

- Frontend: React + TypeScript
- 2D source viewer: OpenSeadragon + PDF.js where applicable
- image pyramid generation: libvips
- 2D semantic overlays: SVG first
- structural 3D: Three.js/WebGL
- API/AI/validation services: Python + FastAPI
- operational store: PostgreSQL
- object store: content-addressed filesystem or S3-compatible storage
- optional semantic retrieval: pgvector, never an authority source
- canonical/audit layer: Git-backed snapshots, validators and receipts during the transition

This stack is a direction, not authorization to introduce a production dependency before its milestone gate.

## N12 reference constraints

N12 is the reference proving ground. Existing canonical work is preserved.

In particular:

- M0-G geometry remains frozen unless formally reopened;
- existing `DOC/MIS/RIF/INF/ND` semantics remain binding;
- existing M1A/M1L/foundation gates remain authoritative within their scope;
- ERW work shall consume existing residuals rather than silently rewrite them;
- no unresolved field may be completed by analogy unless an inference rule explicitly permits an `INF` candidate within its ceiling.

## Foundation completion criterion

The CEW foundation is complete only when:

- this constitution is canonical;
- the machine-readable foundation contract exists and validates;
- milestones and dependencies are canonical;
- the first source/evidence vertical slice uses the foundation contracts;
- N12 existing canonical artifacts can be referenced without semantic loss;
- no user-facing feature bypasses the promotion boundary.
