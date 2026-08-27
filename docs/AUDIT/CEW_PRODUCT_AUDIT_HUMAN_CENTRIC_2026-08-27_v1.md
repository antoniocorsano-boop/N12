# CEW Product Audit — Human-Centred Structural Engineering v1

Status: PRODUCT / ENGINEERING AUDIT
Date: 2026-08-27
Product: CEW — Civil Engineering Workflow
Vertical: CEW-EX — existing structures
Reference implementation: N12
Audit baseline: `work/cew-f5-knowledge-graph-from-e7c0` at `164f8ad924536d2a386c1095d15f8115d218a943`

## 1. Audit objective

Determine whether CEW is becoming a usable professional product for civil/structural engineers, rather than only a technically rigorous repository, evidence pipeline and collection of engineering scripts.

The audit evaluates CEW against a combined reference model:

- ISO 9241-210 human-centred design;
- NTC 2018, Chapter 8, existing structures;
- ISO 13822 assessment of existing structures;
- ISO 19650 information management;
- buildingSMART IDM / IDS / IFC structural-analysis concepts;
- ISO 16311-1/2:2024 and fib Model Code / existing-concrete through-life assessment principles;
- solver-independent structural modelling with round-trip identity.

The audit does not replace regulatory interpretation or professional engineering responsibility.

## 2. Expert board used for the review

CEW product decisions should be tested against a standing role-based expert board. These are competency roles, not software agents with final authority.

1. Responsible structural engineer / project owner
2. Existing-structure assessment specialist
3. Reinforced-concrete specialist
4. Seismic assessment specialist
5. Geotechnical engineer
6. Survey / inspection / diagnostic-testing specialist
7. Durability and degradation specialist
8. FEM / computational structural mechanics specialist
9. BIM / openBIM / information-management specialist
10. Human factors / usability specialist for engineering systems
11. QA / independent checker
12. Field technician / site user
13. Client / asset-owner decision representative
14. Software assurance / provenance engineer

The responsible engineer remains the final authority for engineering decisions.

## 3. Executive finding

CEW has a strong engineering-governance core but is not yet a coherent end-user product.

The central problem is not lack of functionality. It is fragmentation between:

- evidence/provenance machinery;
- N12 automation queues;
- CEW product-state documents;
- structural-model scripts;
- human-review pages;
- future solver/scenario/intervention modules.

The repository has developed from the inside outward. The next product phase must reverse this: start from the engineer's professional workflow and make every internal capability serve a visible phase, decision and deliverable.

## 4. Strong foundations that must be preserved

### 4.1 Epistemic separation — STRONG

CEW explicitly distinguishes documented, measured, reported, inferred, uncertain and unavailable information, and extends scenario space with model-derived/posterior states. This is a major product differentiator and directly supports existing-structure assessment.

Preserve:

- `DOC / MIS / RIF / INF / INC / ND`;
- `MOD / POST` for derived/scenario state;
- no silent promotion;
- incomplete canonical models are allowed.

### 4.2 Immutable source and provenance chain — STRONG

The SourceVersion -> Page -> transform -> EvidenceRegion -> Observation direction is appropriate. Final engineering claims must remain navigable back to immutable primary evidence.

### 4.3 Solver-independent canonical structural model — STRONG

The canonical structural graph is conceptually correct: identity, geometry, topology, properties, evidence lineage and scenarios are separated. Solver files are projections, not authority.

### 4.4 Residual / issue semantics — STRONG

Blocking impact, local blocking, non-blocking and information-only states are useful. Local uncertainty must not freeze unrelated work.

### 4.5 Human authority boundary — STRONG

Machine deterministic checks, machine-proposed/human-reviewed work and human engineering authority are correctly separated.

### 4.6 Specialist-agent bounded contexts — STRONG

Document, geometry, topology, reinforcement, load, foundation, geotechnical, condition, degradation, investigation, solver and QA agents are a suitable decomposition if they return evidence/claims/residuals rather than mutate the global model silently.

## 5. Critical product gaps

### G1 — User workflow is not the primary architecture — CRITICAL

The current FastAPI application is essentially login + Project Control Room + F7 review submission. It does not expose the complete professional workflow.

A structural engineer should enter a project and see the lifecycle, current phase, accepted inputs, required decisions, blockers, deliverables and next action.

Required correction: make project phases first-class runtime objects and navigation primitives.

### G2 — Evidence is not yet embedded in the decision surface — CRITICAL

A human review is not usable when it presents IDs and a form without the source, region, local context and linked structural entity in the same workspace.

Required correction: every human evidence decision must show MICRO / MESO / MACRO source context plus affected entity and downstream impact.

### G3 — Product state drift exists — CRITICAL

`CEW_PROJECT_STATE_CURRENT_v1.json` still describes Netlify/Vercel provisioning paths that no longer fully match the runtime code, which already supports `NEON_APPEND_ONLY` audit persistence.

This conflicts with CEW's own anti-drift rule that current state must be updated with every merged slice.

Required correction: introduce a machine-validated state reconciliation gate between code/runtime capabilities and CEW project-state declarations.

### G4 — Two operational state systems are not explicitly reconciled — HIGH

N12 has `knowledge/CURRENT_STATE.json` and `automation/N12_WORK_QUEUE_v1.json`, while CEW has `CEW_PROJECT_STATE_CURRENT_v1.json` and its own roadmap/current work item.

Both are useful, but their relationship is implicit.

Required correction:

- N12 state = engineering state of the reference project;
- CEW state = product/runtime state;
- add a formal projection mapping from N12 engineering work items into CEW project phases/workspaces.

### G5 — Phase model exists in documentation but not as executable product state — CRITICAL

P0-P13 are already described conceptually, but they are not the runtime backbone of the application.

Required correction: create `ProjectPhase`, `PhaseGate`, `PhaseDeliverable`, `Decision`, `InformationRequirement` and `WorkPackage` as product primitives.

### G6 — Module status can overstate end-user maturity — HIGH

Several modules are marked `OPERATIONAL_V0/V1`, but operational may mean a script, validator, contract or isolated page rather than a complete user journey.

Required correction: separate status dimensions:

- ENGINE_AVAILABLE;
- INTEGRATED;
- USER_WORKFLOW_AVAILABLE;
- HUMAN_FACTORS_VALIDATED;
- PRODUCTION_READY.

A module is product-complete only when all required dimensions pass.

### G7 — FEM path is stale relative to current canonical geometry — CRITICAL

`model/open_source_fem/README.md` describes a preliminary `M0-OS-0002` model with 135 nodes, 108 columns and a single candidate Telaio 5 path. Current N12 canonical state reports a much more advanced frozen M0-G graph with hundreds of nodes/members.

Therefore the old OpenSees path cannot be treated as the current solver adapter.

Required correction: retire it as HISTORICAL/PROTOTYPE and implement Solver Round Trip against the current canonical graph with explicit adapter receipts and entity mapping.

### G8 — No first-class regulatory / code rule pack — HIGH

Existing structures require explicit jurisdiction, code edition, assessment objective, knowledge strategy and analysis/verifications rules.

Required correction: create versioned `EngineeringRulePack` objects for NTC/Eurocode/other admitted frameworks. Code rules are not hidden constants in solver scripts.

### G9 — NTC Chapter 8 professional workflow is not the visible spine — HIGH

CEW contains the relevant technical domains but does not yet present them to the engineer as a coherent sequence aligned with:

- historical-critical analysis;
- survey;
- mechanical characterization;
- knowledge level/confidence factor;
- actions;
- reference model;
- analysis and safety assessment;
- intervention where applicable.

Required correction: make these obligations visible as project deliverables/gates, while keeping CEW generic enough for other jurisdictions.

### G10 — Information requirements are not specified before data production — HIGH

CEW knows many required inputs, but they are dispersed among validators, queues and domain contracts.

Required correction: adopt an IDS/IDM-like pattern: each phase declares what information is required, for what purpose, at what evidence/authority level, and how compliance is checked.

### G11 — Field investigation is not yet an executable workflow — HIGH

Investigation Planner is advisory. The product needs work packages that go from missing fact -> method -> location/entity -> field capture -> test result -> provenance -> claim -> reassessment.

### G12 — Results and verification are not yet round-tripped into the engineering twin — CRITICAL for L4

A solver result must map back to canonical entities, scenarios, load combinations and adopted rules. No current end-to-end user path establishes that loop.

### G13 — Scenario/change comparison needs user-visible causality — MEDIUM/HIGH

It is not enough to run historical/conservative/probabilistic scenarios. The interface must answer: which assumption/measurement changed this result?

### G14 — Intervention and lifecycle are roadmap concepts, not product workflows — MEDIUM

AS-IS, proposed, executed and monitored generations need explicit approvals, differences, model lineage and post-intervention evidence.

### G15 — The top-level UX exposes implementation mechanics — CRITICAL

Repository IDs, gate names and internal status strings are useful audit data but should not be the dominant interaction model.

Required correction: user language first, internal IDs progressively disclosed.

## 6. Human-centred design requirements

CEW development shall use the ISO 9241-210 loop for every major workspace:

1. understand and explicitly describe the context of use;
2. specify user requirements and engineering decisions;
3. produce design solutions;
4. evaluate them with representative engineering tasks;
5. iterate until the task can be completed safely and intelligibly.

For CEW this becomes:

`ENGINEERING TASK -> REQUIRED EVIDENCE -> USER DECISION -> SYSTEM SUPPORT -> HUMAN-FACTORS TEST -> RELEASE`

Every feature shall answer:

- Who is the user?
- What engineering question are they answering?
- What evidence must be visible?
- What may the machine decide?
- What requires human review?
- What is the consequence of an error?
- What is the reversible action?
- What becomes canonical, and through which gate?

## 7. Product-level acceptance test

CEW is not accepted because scripts pass CI. It is accepted when a responsible engineer can complete this end-to-end journey without repository knowledge:

1. create the structural assessment project;
2. define scope, asset, code/rule pack and objective;
3. ingest heterogeneous source material;
4. inspect source inventory and quality;
5. reconstruct evidence and resolve ambiguity in context;
6. build and review geometry/topology;
7. bind structural semantics and properties;
8. identify missing decision-critical information;
9. plan/ingest investigations;
10. authorize an assessment scenario;
11. generate a solver projection;
12. verify adapter/model QA;
13. execute/import FEM results;
14. inspect results mapped to structural entities and evidence;
15. conclude assessment with explicit residuals/uncertainty;
16. create and compare intervention generations when required;
17. issue a traceable technical dossier/report;
18. preserve the asset state for future monitoring/reassessment.

At every step the user must be able to navigate backward to evidence and forward to impact.

## 8. Audit scorecard

Scale: 0 absent; 1 conceptual; 2 prototype; 3 technically operational; 4 integrated usable workflow; 5 production-grade professional workflow.

| Domain | Score | Finding |
|---|---:|---|
| Source identity/version/provenance | 4 | strong technical foundation |
| Evidence/claim governance | 4 | strong, human review surface incomplete |
| Geometry/topology canonicalization | 4 | strong N12 reference implementation |
| Structural semantic model | 3 | technically operational, incomplete product integration |
| Engineering properties | 3 | substantial domain work, user workflow fragmented |
| Condition/exposure/degradation | 2 | early engines/gates, not integrated lifecycle workflow |
| Investigation planning | 2 | advisory, field round trip missing |
| Assessment scenarios | 2-3 | engine exists, full user causality/authorization path missing |
| Solver/FEM adapter | 1-2 | prototype path stale; production round trip absent |
| Verification/result mapping | 1 | not end-to-end |
| Intervention generations | 1 | architecture only |
| Lifecycle/monitoring | 1 | architecture only |
| Human-centred UX | 1-2 | current pilot exposes internal mechanics |
| Product state/governance coherence | 2 | strong rules, current drift detected |

Overall: **strong engineering kernel, weak integrated product shell**.

## 9. Priority correction order

1. Freeze a human-centred phase/state architecture.
2. Reconcile CEW product state and N12 engineering state.
3. Build Project Home around phase, readiness, next action and deliverables.
4. Build Source Hub + integrated Evidence Workspace.
5. Build synchronized Reconstruction Workspace (source / 2D / 3D / table / residuals).
6. Build Engineering Properties workspaces.
7. Turn Investigation Planner into executable field work packages.
8. Replace stale FEM prototype with current canonical Solver Round Trip.
9. Map solver results back to entities/scenarios/claims.
10. Add verification, intervention generations and lifecycle dossier.

## 10. Non-negotiable invariants

- No UI state is engineering authority.
- No solver output rewrites evidence.
- No model precision upgrades evidence precision.
- No missing information is silently filled.
- No geometric proximity creates structural connectivity by itself.
- No human observation is normalized in a way that loses engineering meaning.
- No scenario assumption is presented as measurement.
- No intervention mutates AS-IS history.
- Every decision-grade result must support backward traceability to evidence and forward traceability to decision/use.
