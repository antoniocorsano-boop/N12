# CEW Stakeholder Product Blueprint v2

Status: CANONICAL PRODUCT ARCHITECTURE
Date: 2026-08-24
Reference implementation: N12

## 1. Product thesis

CEW (Civil Engineering Workflow) is the operating environment of an engineering project, not merely a model viewer, parser, solver or document repository.

For the responsible engineer, CEW must continuously answer five questions:

1. What do we know?
2. How do we know it?
3. What remains uncertain or blocked?
4. What can be done next to reduce that uncertainty?
5. What model / scenario / decision is currently authorized?

Civil Existing Workflow (CEW-EX) is the vertical for existing structures reconstructed from heterogeneous, possibly old, incomplete or contradictory evidence.

## 2. Benchmark-derived principles

CEW adopts and extends mature product patterns from:

- ISO 19650 information management: persistent information containers, recording, versioning, federation, status/use authorization, common data environment concepts;
- buildingSMART IFC: open exchange model and stable entity identities across tools;
- buildingSMART BCF: model-contextual issues linked to view, snapshot, coordinates and model entities;
- Bentley iTwin-style digital twin federation: engineering model + reality / external data + lifecycle changes without forcing one authoring tool;
- Tekla-style model ownership/versioned collaboration: controlled shared model state, user roles, local work and synchronized authoritative history;
- ISO 55000 lifecycle/asset-management thinking: decisions are tied to value, outcomes, assurance, adaptability and lifecycle maturity;
- fib / ISO existing-structure assessment: acquisition -> condition assessment -> performance prediction -> decision / intervention, with uncertainty and evidence preserved.

CEW must not imitate these systems feature-by-feature. Its differentiation is epistemic engineering: every project object must expose evidence, uncertainty, residuals, scenario status and decision authority.

## 3. Primary stakeholder journeys

### 3.1 Responsible Engineer / Project Owner

Needs to:
- set project objectives and assessment strategy;
- know project readiness at a glance;
- approve evidence promotions and modeling assumptions;
- select investigations and scenarios;
- authorize solver handoff;
- compare intervention alternatives;
- sign off project generations.

Primary surface: Project Control Room.

### 3.2 Structural Engineer / Model Author

Needs to:
- reconstruct geometry/topology;
- bind sections, materials, reinforcement, loads and foundations;
- inspect source evidence while editing model claims;
- understand residual impact;
- generate solver projections without corrupting source evidence.

Primary surfaces: Reconstruction Workspace, Structural Model Workspace, Solver Handoff.

### 3.3 Survey / Inspection Specialist

Needs to:
- see exactly what information is missing;
- capture measurements, observations, photos and locations in a structured field workflow;
- avoid performing redundant tests;
- upload results directly against project claims / entities.

Primary surface: Investigation Workspace / Field Pack.

### 3.4 Geologist / Geotechnical Engineer

Needs scoped requests, foundation identities, site evidence, historic assumptions, current missing parameters and required outputs.

Primary surface: Geotechnical Work Package.

### 3.5 Reviewer / Checker

Needs immutable lineage, conflict history, approvals, scenario rules, gate results and reproducible evidence.

Primary surface: Review & Audit Workspace.

### 3.6 Client / Asset Owner

Needs a simplified decision view: risk, uncertainty, investigation options, intervention alternatives, costs/status and lifecycle consequences; not raw engineering internals.

Primary surface: Decision Dashboard.

## 4. Project lifecycle / phase model

CEW projects are organized as a state machine, not a folder hierarchy.

P0 PROJECT DEFINITION
- scope, asset identity, objectives, stakeholders, roles, target codes, solver targets, intended knowledge strategy.

P1 SOURCE ACQUISITION
- documents, drawings, photos, reports, CAD/BIM, field data, test results.
- every source receives immutable identity, hash, metadata and role.

P2 DOCUMENT UNDERSTANDING
- page/tile segmentation, sheet identification, source authority, OCR only when justified, image/snippet extraction.

P3 CLAIM / EVIDENCE RECONSTRUCTION
- structured claims extracted from sources;
- DOC/MIS/RIF/INF/INC/ND state;
- conflicts preserved, never overwritten silently.

P4 GEOMETRY & TOPOLOGY
- support/node/axis reconstruction;
- explicit structural connectivity;
- metric and topology gates separated.

P5 STRUCTURAL SEMANTICS
- beams, columns, walls, slabs, foundations, rigid offsets, special features;
- stable entity identity.

P6 CANONICAL 3D MODEL
- solver-independent graph;
- incomplete and symbolic coordinates allowed;
- evidence lineage queryable per entity.

P7 ENGINEERING PROPERTIES
- sections, materials, reinforcement, loads, boundary conditions, foundations, soil interface.

P8 CONDITION & EXPOSURE
- exposure zones, protection state, inspection observations, damage indicators, measurements.

P9 KNOWLEDGE / INVESTIGATION
- blocker and residual analysis;
- candidate investigations;
- future sensitivity / Value of Information.

P10 ASSESSMENT SCENARIOS
- Historical, Conservative Existing, Probabilistic Degradation, Essential Tests Updated, Surveyed Existing.

P11 SOLVER HANDOFF & VERIFICATION
- EdiLus / open-source FEM / future adapters;
- round-trip entity identity mapping.

P12 INTERVENTION DESIGN
- alternatives, local/global strengthening, repair/protection, scenario comparison.

P13 EXECUTED / MONITORED ASSET
- as-built intervention generation, inspections, monitoring, future reassessment.

Phases may overlap. Local residuals must not block unrelated work.

## 5. Core workspaces

### 5.1 Project Control Room

Must display:
- current project phase;
- domain readiness matrix;
- blocker/residual count by impact;
- current canonical generation;
- current assessment mode;
- next best work item;
- latest approvals / gates;
- evidence completeness;
- solver eligibility;
- investigation status;
- intervention status.

The top-level language is action-oriented: READY / WATCH / RESIDUAL / BLOCKED / FAIL.

### 5.2 Source Hub

Functions:
- immutable upload/version registry;
- source authority classification;
- file/page/sheet metadata;
- high-resolution tiling;
- document comparison;
- source lifecycle / supersession;
- direct navigation from any claim back to source.

### 5.3 Evidence Viewer

A technical viewer, not merely PDF rendering.

Required interaction levels:
- MICRO: exact crop / label / dimension;
- MESO: local structural context;
- MACRO: whole drawing / source.

Functions:
- deep zoom;
- persistent tiles;
- coordinate readout;
- overlays;
- crop creation;
- dimension/axis markup;
- side-by-side source comparison;
- source-to-model highlighting.

### 5.4 Human Evidence Resolution Module

Every ambiguous extraction can produce a review card containing:
- issue / claim;
- evidence crop;
- surrounding context;
- source/page/tile coordinates;
- machine alternatives;
- confidence / ambiguity reason;
- previous claims;
- relevant model entity;
- actions: confirm, correct, reject, defer, create residual.

No opaque AI confidence is sufficient for promotion.

### 5.5 Claim & Conflict Workspace

A claim is first-class:
- claim_id;
- target entity/property;
- proposed/current value;
- epistemic state;
- source refs;
- evidence snippets;
- author/agent;
- method;
- review decision;
- generation;
- supersession chain.

Conflicts are persistent objects. A current claim may supersede another, but never erase it.

### 5.6 Geometry Reconstruction Workspace

Synchronized views:
1. original drawing;
2. reconstructed 2D network;
3. tables/coordinates;
4. canonical 3D preview;
5. residual map.

Selection is identity-synchronized across all views.

### 5.7 Structural Model Workspace

Provides four primary maps over one canonical graph:
- Geometry Map;
- Evidence Map;
- Completion Map;
- Assessment/Scenario Map.

Additional future maps:
- load map;
- reinforcement map;
- condition/degradation map;
- utilization/result map;
- intervention map.

### 5.8 Residual / Issue Manager

CEW Issue extends BCF-style model contextual issues with engineering semantics.

Minimum fields:
- issue_id;
- linked entity/entities;
- source/view/snippet context;
- domain;
- problem statement;
- epistemic state;
- impact class: BLOCKING / LOCAL_BLOCKING / NON_BLOCKING / INFORMATIONAL;
- affected verification scopes;
- suggested resolution routes;
- assigned stakeholder / agent;
- decision state;
- evidence additions;
- closure gate / receipt.

Opening an issue must prepare all useful context automatically: candidate sources, crops, related claims, neighboring/homologous entities (without authorizing analogy), model view and possible investigation path.

### 5.9 Materials & Knowledge Workspace

Separates:
- historical design material;
- current observed/measured material;
- regulatory knowledge level / confidence factor;
- model/scenario material assumptions;
- statistical/posterior distributions.

LC/FC is governed separately from probabilistic model confidence.

### 5.10 Loads & Mass Workspace

Separates:
- historical load reconstruction;
- current as-built permanent loads;
- occupancy/use actions;
- later additions;
- mass model;
- combination rules;
- source vs adopted-code values;
- tributary/load-path mappings.

Every numerical load must answer: source? rule? scope? scenario?

### 5.11 Foundation & Geotechnical Workspace

Combines, without conflating:
- foundation primary geometry;
- member/property binding;
- foundation elevations;
- soil/site evidence;
- historical geotechnical assumptions;
- current site-specific geotechnics;
- soil-structure interface model.

### 5.12 Exposure / Condition / Degradation Workspace

Distinct layers:
Exposure -> Condition -> Mechanism Screening -> Degradation Model -> Structural Effect.

No layer may auto-promote the next.

### 5.13 Investigation Planner

For every unresolved decision-relevant domain:
- missing fact;
- possible acquisition method;
- invasiveness;
- cost band;
- uncertainty reduction;
- affected model outputs;
- dependencies;
- priority;
- future expected Value of Information.

The product supports diffuse, essential and model-comparison knowledge strategies.

### 5.14 Scenario Manager

Scenario is a first-class immutable overlay against a canonical generation.

Modes:
- MODE-1 HISTORICAL_BASELINE;
- MODE-2 CONSERVATIVE_EXISTING;
- MODE-3 PROBABILISTIC_DEGRADATION;
- MODE-4 ESSENTIAL_TESTS_UPDATED;
- MODE-5 SURVEYED_EXISTING.

Scenario comparison must expose exactly which assumptions/measurements create response differences.

### 5.15 Solver Handoff

Solver projects are derived projections.

Adapter requirements:
- explicit model-rule pack;
- stable entity mapping;
- unsupported-feature report;
- residual exclusions;
- input receipt;
- round-trip results mapping;
- no automatic write-back to source evidence.

### 5.16 Verification & Intervention Workspace

Results mapped back to 3D identity:
- demand/capacity;
- failure mode;
- governing combination;
- uncertainty/scenario sensitivity;
- affected evidence gaps.

Intervention alternatives create new proposed generations rather than mutating AS-IS.

## 6. Collaboration / Common Data Environment

CEW must implement a CDE-inspired information workflow.

Recommended logical states:
- WORKING;
- SHARED_FOR_COORDINATION;
- REVIEW_REQUIRED;
- APPROVED_FOR_USE;
- SUPERSEDED;
- ARCHIVED.

These are information-use states, separate from epistemic states such as DOC/MIS/ND.

Roles and permissions must operate at project/work-package level. Technical approval remains attributable to humans even where agents prepare work.

## 7. Federation and interoperability

CEW's canonical graph remains native, but interoperability is mandatory.

Priorities:
1. stable internal IDs;
2. external identifier registry (IFC GUID, solver IDs, CAD labels, document IDs);
3. IFC import/export where semantics support it;
4. BCF-compatible issue interchange where useful;
5. solver adapters;
6. open JSON/CSV/API contracts for evidence, claims and scenarios.

The product must be able to federate design data, reality data, inspections and solver results without requiring one tool to become authoritative for every domain.

## 8. Agent architecture

Agents operate inside bounded work packages:
- Source Agent;
- Document Agent;
- Geometry Agent;
- Topology Agent;
- Section Agent;
- Reinforcement Agent;
- Load Agent;
- Foundation Agent;
- Geotechnical Agent;
- Condition Agent;
- Degradation Agent;
- Investigation Agent;
- Solver Agent;
- QA / Adjudication Agent.

An Orchestrator selects work; agents return claims/evidence/residuals/gate candidates. No agent is allowed to silently mutate the entire canonical project.

## 9. Human authority model

Three decision levels:

A. MACHINE DETERMINISTIC
- hashes, count checks, topology consistency, schema validation.

B. MACHINE PROPOSES / HUMAN REVIEWS
- ambiguous drawing interpretation, claim promotion, source authority conflict, scenario assumption adoption.

C. HUMAN ENGINEERING AUTHORITY
- LC/FC decision, investigation approval, material/geotechnical characterization acceptance, solver model authorization, verification conclusion, intervention approval.

## 10. UX rule: one screen, one engineering decision

Every operational surface should answer one dominant question.

Examples:
- Source Hub: What sources do I trust / still need?
- Evidence Resolution: What does this source actually say?
- Geometry Workspace: Where is this entity and how is it connected?
- Residual Manager: What prevents progress and how can I resolve it?
- Investigation Planner: Which test/information acquisition is worth doing?
- Scenario Manager: What changes if this assumption is different?
- Solver Handoff: Is this model authorized to calculate?

Complex context remains available progressively, not shown all at once.

## 11. Product maturity model

L0 DOCUMENT REPOSITORY
Files exist but no structured engineering graph.

L1 TRACEABLE EVIDENCE
Sources, claims, snippets and provenance exist.

L2 CANONICAL RECONSTRUCTION
Identity, geometry, topology and property graph exist with residuals.

L3 INTERACTIVE ENGINEERING TWIN
2D/3D maps, issues, evidence and project state are synchronized and queryable.

L4 ASSESSMENT-READY
Scenarios, investigation planner, solver adapters and round-trip results are controlled.

L5 DECISION-READY
Sensitivity / uncertainty / Value of Information, intervention alternatives and decision packages are available.

L6 LIFECYCLE TWIN
Executed intervention generation, monitoring, future inspections and reassessment become continuous asset history.

N12 currently spans L1-L3 strongly, with early L4 components present; it is not yet L4 complete because M1E calculation readiness remains blocked by unresolved evidence domains.

## 12. Quality and acceptance gates

Each module needs four gates:

1. DATA GATE — schema, identity, provenance completeness;
2. ENGINEERING GATE — domain-specific semantic correctness;
3. HUMAN GATE — where professional judgment is required;
4. PRODUCT/HUMAN-FACTORS GATE — user can understand state, next action, authority and evidence.

A technically correct feature that does not allow the engineer to understand why a decision is possible is not product-complete.

## 13. Canonical product records

The following records should become platform-level primitives:

- Project;
- Asset;
- Source;
- InformationContainer;
- Claim;
- EvidenceSnippet;
- Conflict;
- Entity;
- PropertyBinding;
- Issue/Residual;
- WorkItem;
- Gate;
- Receipt;
- Investigation;
- Observation;
- Measurement;
- ExposureZone;
- DamageState;
- Scenario;
- ModelRule;
- SolverProjection;
- SolverResult;
- Intervention;
- Generation;
- Approval.

## 14. Immediate product roadmap

R1 PROJECT CONTROL ROOM
Aggregate current CEW/N12 state into stakeholder-facing project dashboard.

R2 UNIVERSAL ISSUE / RESIDUAL WORKSPACE
Model-linked issue + crop/context + source candidates + action path.

R3 SYNCHRONIZED 2D/3D EVIDENCE MAP
Drawing/viewer/model identity synchronization.

R4 FIELD / INVESTIGATION PACK
Turn planner candidates into executable inspection/test work packages and ingest results.

R5 SOLVER ROUND-TRIP
CEW -> solver projection -> result import -> 3D result map.

R6 SCENARIO / SENSITIVITY
Comparative scenarios with transparent property changes.

R7 INTERVENTION GENERATIONS
AS-IS -> proposed -> executed -> monitored.

## 15. Product invariant

CEW is successful when the responsible engineer can navigate from any final engineering conclusion back through:

result -> scenario -> model property -> claim -> evidence -> immutable source,

and in the opposite direction can navigate from any unresolved source ambiguity to:

residual -> impact -> resolution method -> investigation/work item -> updated claim -> new model generation.
