# CEW Platform OS v0

Status: EXPERIMENTAL INTEGRATION GOVERNANCE
Reference pilot: N12
Base capability branch: `exp/cew-document-intelligence-foundation-v0`
Canonical CEW boundary remains unchanged: F2 is not closed by this branch and no later milestone is promoted by this work.

## 1. Purpose

CEW Platform OS is the operating model that turns the existing CEW/N12 capabilities into one governed engineering product.

It does not replace `CEW_PRODUCT_ARCHITECTURE_v1`. It operationalizes that product direction using the development model proven in DOCENTE OS:

`discover -> extract -> classify -> candidate -> review -> approved artifact -> runtime -> gate -> receipt`

For CEW the corresponding engineering chain is:

`SourceVersion -> ProcessingGeneration -> Observation -> CandidateMeaning/Claim -> Supported -> HumanDecision -> CanonicalGeneration -> ScenarioGeneration -> SolverAdapter -> ResultMapping -> Receipt`

Repeated mechanics are automated. Engineering meaning is exposed for human decision. Ambiguity fails closed.

## 2. Product decomposition

### W0 — Source & Evidence Foundation
Owns immutable originals, SourceVersion identity, page/region transforms, EvidenceRegion, Observation, provenance, residuals and conflicts.

### W1 — Document Intelligence & Graphic Knowledge
Owns raster/vector reading, OCR/HTR, geometry extraction, symbol mining, graphic-convention knowledge, active-learning datasets and semantic drawing reconstruction.

Output is evidence-bound observations and supported candidates. It does not create canonical structural truth by itself.

### W2 — Canonical Structural Knowledge & Smart Entity
Owns stable engineering identities and the solver-independent entity model.

A structural entity is a versioned smart object with:
- stable identity;
- geometry/topology references;
- evidence lineage;
- properties and reinforcement;
- epistemic state per property;
- lifecycle generation;
- deterioration/exposure state;
- solver mappings;
- intervention history;
- quantities/cost references;
- unresolved residuals.

### W3 — 3D Model & Evidence Workspace
Owns 3D representation, model/source synchronization, entity selection, evidence lineage, epistemic overlays, human adjudication and model-generation comparison.

The viewer is never authority by itself.

### W4 — Existing Assessment & FEM
Owns scenario generation, solver-independent analysis contract, solver adapters, round-trip entity mapping, verification results, cross-solver comparison and calculation eligibility.

Historical, conservative, probabilistic, surveyed and post-intervention scenarios remain separate generations.

### W5 — Exposure, Degradation & Investigation
Owns degradation model registry, applicability, uncertainty, calibration state, condition observations, sensitivity, investigation planning and Value of Information.

Model-derived deterioration cannot overwrite measured/documented evidence.

### W6 — Intervention Intelligence
Owns deficiencies, intervention objectives, candidate repair/strengthening solutions, technical applicability, compatibility constraints, product/system references, human selection and post-intervention model generation.

Market solutions are reference candidates until project applicability and engineering design are validated.

### W7 — Quantity, Cost & Before/After
Owns quantity takeoff from validated model generations, intervention quantities, price-source generations, cost scenarios, before/after comparison and audit trail.

Quantities must be traceable to entity IDs and model generation. Prices must be traceable to price-source generation.

### W8 — Dossier, Reporting & Lifecycle
Owns evidence-backed reports, calculation dossiers, intervention records, inspection/monitoring updates and immutable historical generations.

## 3. Development operating model

Every coherent tranche follows:

1. READ CURRENT STATE — repository, canonical boundary, active generations, current evidence.
2. DISCOVER — identify authoritative inputs and existing reusable capability.
3. BUILD CANDIDATE — produce the smallest complete derived artifact or feature.
4. RUN GENERIC INVARIANTS — provenance, identity, state, schema, regression and domain-specific gates.
5. SELF-CORRECT — the executing agent fixes technical failures inside its authorized scope instead of returning a plan.
6. HUMAN GATE — only genuine semantic/engineering decisions are surfaced.
7. MATERIALIZE — create the approved artifact/generation.
8. RUN FULL GATES — tests, validation, build, deterministic receipts and exact-SHA checks.
9. COMPLETE — update work item and emit one machine-readable result.

An agent run may end only in one of the result-contract outcomes. `I made a plan` is never a completion state.

## 4. Generation model

The DOCENTE OS generation-safe pattern is adopted as a CEW core invariant.

For every reprocessable derivative:

- the original identity is immutable;
- a new monotonically ordered ProcessingGeneration is created;
- all derived observations/indexes/artifacts belong to that generation;
- a generation becomes current only after all required stages succeed;
- a failed generation never replaces the last successful current generation;
- historical generations and validated bindings remain auditable;
- source drift invalidates dependent derived artifacts rather than silently updating them.

This applies to document parsing, graphic extraction, symbol datasets, canonical model builds, scenario builds, solver exports, degradation calculations, intervention variants and cost generations.

## 5. Human-centered boundary

Automation should remove mechanical review, not professional responsibility.

Human decisions are required when the system must choose among materially different engineering meanings, assumptions, interventions or promotions.

The machine should present:
- evidence;
- candidate interpretation;
- alternatives;
- conflicts/counterevidence;
- consequences of each option;
- requested decision.

Allowed decisions are explicit: `APPROVE`, `CORRECT`, `REJECT`, `DEFER`, `DESIGN_NEW_RULE`.

No unresolved semantic conflict may be converted into guessed canonical data.

## 6. Agent architecture

Use specialist workers behind stable ports rather than one super-agent.

Core agent roles:
- Source/Ingestion Agent;
- Document Reconstruction Agent;
- Geometry Agent;
- OCR/HTR Agent;
- Symbol/Convention Learning Agent;
- Evidence/Provenance Auditor;
- Structural Knowledge Agent;
- 3D Model Builder Agent;
- FEM/Scenario Agent;
- Degradation/Exposure Agent;
- Investigation/VoI Agent;
- Intervention Intelligence Agent;
- Quantity/Cost Agent;
- Dossier Agent;
- Platform Orchestrator.

The Platform Orchestrator owns state transitions and work eligibility. Specialist agents own technical execution inside a work item. Human reviewers own semantic approval gates.

## 7. Open-source composition policy

CEW should compose mature specialist components where they fit and keep CEW authority in its own contracts and data model.

Initial decisions:

- PDF programmatic extraction: `PyMuPDF` + independent `docling-parse` adapter;
- scanned-document OCR/layout benchmark: `PaddleOCR` family; keep detector interface provider-neutral;
- raster/vector geometry: `OpenCV` plus CEW geometry normalization/classification;
- high-resolution source viewer: `OpenSeadragon`;
- canonical persistence target: PostgreSQL with spatial geometry support; semantic vectors are secondary indexes, not truth;
- 3D/IFC interoperability: `IfcOpenShell`; IFC is an interchange/projection surface, not automatic CEW authority;
- graph algorithms: start with relational explicit edges plus `NetworkX` for in-process analysis before introducing a dedicated graph database;
- agent orchestration: deterministic CEW queues remain authority; a durable workflow framework may be used as execution infrastructure only when long-running/resumable HITL workflows require it;
- FEM: maintain solver-independent CEW contract and at least one independent open-source adapter, with OpenSeesPy and Code_Aster as benchmark candidates;
- solver output never writes evidence automatically.

No external library is adopted merely because it is AI-enabled. It must pass CEW provenance, reproducibility and failure-mode gates.

## 8. N12 capability consolidation

Existing N12 branches are treated as reference implementations or candidate modules, not automatically merged truth.

Already represented in the repository family are:
- Source Foundation;
- Evidence Foundation;
- source/evidence viewer work;
- AI Observation;
- Knowledge Graph;
- Evidence Review Workspace;
- human decision/promotion work;
- 3D Structural Model Builder;
- Structural Viewer;
- Existing Assessment Engine;
- Exposure/Degradation Engine;
- Investigation Planner;
- evidence-map/control-room work;
- N12 deterministic work queues and receipts;
- experimental Document Intelligence and supervised symbol learning.

Platform OS will progressively inventory, test, reconcile and adopt those capabilities behind stable contracts rather than restarting them.

## 9. Non-negotiable invariants

1. Original sources are immutable/versioned and never replaced by AI derivatives.
2. Every derived artifact belongs to an explicit generation.
3. Only a fully successful generation may become current.
4. Every canonical engineering value has evidence lineage or an explicit admitted modeling rule.
5. Geometry proximity never creates topology automatically.
6. `MOD/POST` never become `MIS` silently.
7. Solver files/results are projections, not canonical authority.
8. Human overrides require rationale and receipt.
9. Every intervention creates a new model generation.
10. Every quantity/cost result identifies the model and price generation used.
11. Agents must finish authorized mechanical work before asking for human input.
12. Human review is reserved for genuine semantic/engineering decisions.
13. A green technical gate never substitutes required visual/engineering validation.
14. This experimental branch cannot close CEW-F2 or authorize later canonical milestones.

## 10. Immediate implementation sequence

The first operational path is intentionally short:

`TAV07 source tiles -> Document Intelligence generation -> indexed observations -> symbol/graphic training labels -> Graphic Convention candidates -> human validation -> reusable drawing-reading rules`

In parallel, Platform OS inventories the already-developed CEW model/assessment/degradation modules and defines the Smart Entity contract that will later bind them after their upstream gates are eligible.
