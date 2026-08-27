# CEW Human-Centred Structural Product Architecture v1

Status: PROPOSED CANONICAL PRODUCT ARCHITECTURE
Date: 2026-08-27
Product family: CEW — Civil Engineering Workflow
Initial vertical: CEW-EX — Existing Structures
Reference project: N12

## 1. Product definition

CEW is the operating environment for a structural engineering project.

It is not primarily:

- a document repository;
- a PDF/OCR tool;
- a BIM authoring package;
- a FEM solver;
- an issue tracker;
- an AI chat interface.

CEW coordinates those capabilities around a human engineering workflow whose purpose is to transform heterogeneous project information into controlled structural knowledge, an auditable model, authorized analyses, engineering conclusions, intervention generations and a through-life asset record.

The defining chain is:

`SOURCE -> EVIDENCE -> CLAIM -> ENGINEERING ENTITY -> CANONICAL MODEL -> SCENARIO -> SOLVER PROJECTION -> RESULT -> VERIFICATION -> DECISION -> GENERATION`

The reverse chain must always remain navigable.

## 2. Development model: Human-Centred Structural Engineering Lifecycle

CEW adopts a domain-specific extension of human-centred design.

For every product capability the development loop is:

1. CONTEXT — identify the real engineering user, task, environment and consequence of error;
2. DECISION — define the engineering question the user must answer;
3. INFORMATION NEED — state what evidence/data are required and at what authority/epistemic level;
4. WORKSPACE — design the minimum interface that makes evidence, model context, options and impact visible together;
5. AUTOMATION BOUNDARY — define what is deterministic, what the machine may propose and what only a human may authorize;
6. ENGINEERING GATE — validate domain semantics and traceability;
7. HUMAN-FACTORS GATE — test the task with representative users and realistic project material;
8. RELEASE — expose the capability only if the user can complete the engineering task without repository/internal-system knowledge;
9. OBSERVE AND ITERATE — collect workflow friction, decision errors, unresolved ambiguity and rework signals.

This is the CEW implementation of the ISO 9241-210 human-centred lifecycle.

## 3. Product design principles

### H1 — The engineer sees the project lifecycle, not the repository

Primary navigation is by project phase and engineering object.

Internal file paths, gate IDs and commit hashes remain available in audit/detail views but never dominate the workflow.

### H2 — One screen, one dominant engineering decision

Every operational screen must have one clear question.

Examples:

- Source Hub: Do I have the right information and can I trust its identity?
- Evidence Workspace: What does this source actually document?
- Reconstruction Workspace: What is the geometry/topology and what remains uncertain?
- Investigation Workspace: Which missing fact should I acquire and how?
- Solver Handoff: Is this model authorized and technically suitable for analysis?
- Verification Workspace: What fails, why, under which scenario/rule, and how certain is the conclusion?

### H3 — Evidence must be visible where decisions are made

No human evidence review is valid as a product interaction if source context is hidden behind IDs.

The standard evidence panel contains:

- MICRO: exact evidence region;
- MESO: local structural context;
- MACRO: whole page/sheet/source;
- source identity/version/hash;
- page and geometric locator;
- linked claim/entity;
- current competing claims/conflicts;
- impact on model/readiness.

### H4 — Progressive disclosure

The engineer first sees professional meaning. Technical provenance, internal IDs and machine diagnostics are expandable.

### H5 — Human authority is explicit

Every action is labelled as one of:

- MACHINE DETERMINISTIC;
- MACHINE PROPOSES / HUMAN REVIEWS;
- HUMAN ENGINEERING AUTHORITY.

### H6 — Missing information remains operational

`ND`, `INC` and residuals do not mean workflow failure. They become explicit project objects with impact and resolution routes.

### H7 — Local uncertainty does not freeze unrelated work

The project state machine supports parallel work packages and local gate scopes.

### H8 — Model and evidence remain separate but synchronized

The 3D/analytical model is a projection of engineering knowledge. It never becomes evidence simply because it is geometrically complete.

### H9 — Every solver is an adapter

EdiLus, OpenSees, Code_Aster or future tools consume a governed projection. No external solver becomes the canonical authority.

### H10 — Current/historical/proposed/executed states never collapse

Engineering generations and scenarios are immutable or superseded, never overwritten in place.

## 4. User roles

### Responsible Engineer

Owns project objectives, codes/rule packs, knowledge strategy, investigation approvals, solver authorization, verification conclusions and generation approvals.

### Structural Model Engineer

Owns reconstruction, analytical idealization proposals, property binding and solver-projection preparation.

### Evidence / Document Specialist

Owns source classification, source reconstruction, document reading and evidence candidates.

### Survey / Investigation Specialist

Receives executable field work packages and returns structured observations/measurements/tests.

### Geotechnical Specialist

Owns soil/site characterization and soil-structure modelling proposals within explicit scope.

### Reviewer / Checker

Reviews lineage, model rules, assumptions, scenario changes, solver receipts and engineering conclusions.

### Client / Asset Owner

Receives decision-oriented summaries, alternatives and uncertainty/risk communication without editing engineering authority.

### Specialist AI Agents

Operate only inside bounded work packages and return proposals/evidence/residuals/gate candidates.

## 5. The CEW project lifecycle

The product shall implement the following phases as first-class runtime objects.

### P0 — PROJECT DEFINITION

User question: What are we assessing and why?

Inputs:
- asset identity/location;
- structure type/material;
- construction period;
- intended use;
- scope of engagement;
- assessment objective;
- applicable jurisdiction/codes;
- target solver(s);
- known changes/interventions;
- knowledge/investigation strategy.

Primary deliverables:
- Project Charter;
- Asset Record;
- Engineering Rule Pack selection;
- Initial Information Requirement Set;
- Responsibility Matrix.

Human authority: Responsible Engineer.

Gate: `PROJECT_DEFINED`.

### P1 — SOURCE ACQUISITION / CDE

User question: What information do I have, where did it come from and what is its status?

Accept:
- PDF/drawings/scans;
- calculation reports;
- photographs/videos;
- CAD/BIM;
- spreadsheets;
- surveys;
- test/lab reports;
- field records;
- geotechnical documents;
- prior intervention/maintenance records.

Every source receives immutable identity/version/hash plus information-use state.

Deliverables:
- Source Register;
- duplicate/version graph;
- missing-source checklist;
- source authority/use classification.

Gate: `SOURCE_BASELINE_READY`.

### P2 — DOCUMENT UNDERSTANDING

User question: What is contained in each source and where are the engineering-relevant regions?

Capabilities:
- page/sheet identification;
- vector/text/image extraction;
- OCR only where justified;
- drawing classification;
- page transforms;
- persistent high-resolution tiles;
- table/detail/callout detection;
- document cross-reference graph.

Deliverables:
- Page Registry;
- Drawing/Document Index;
- Source-to-sheet map;
- Evidence-region candidates;
- unresolved document issues.

Gate: `DOCUMENT_MAP_READY`.

### P3 — EVIDENCE / CLAIM RECONSTRUCTION

User question: What does the source actually document?

Capabilities:
- claim extraction;
- EvidenceRegion / EvidenceSnippet binding;
- `DOC/MIS/RIF/INF/INC/ND` state;
- conflict objects;
- human review in source context;
- supersession without deletion.

Deliverables:
- Claim Ledger;
- Evidence Ledger;
- Conflict Register;
- human decisions/receipts;
- residuals.

Gate: `TRACEABLE_EVIDENCE_READY` scoped by domain.

### P4 — HISTORICAL-CRITICAL ANALYSIS & SURVEY BASELINE

User question: What is the structural history and what current geometry/condition can be established?

This phase provides the visible CEW-EX regulatory spine corresponding to existing-structure assessment practice.

Capabilities:
- historical design chronology;
- construction/modification chronology;
- structural scheme evolution;
- survey control points;
- coordinate systems;
- direct dimensional measurements;
- discrepancy mapping historical vs current.

Deliverables:
- Historical-Critical Record;
- Survey Baseline;
- change/anomaly register.

Gate: `REFERENCE_BASELINE_ESTABLISHED`.

### P5 — GEOMETRY & TOPOLOGY RECONSTRUCTION

User question: Where are the structural objects and how are they connected?

Synchronized workspace:
- source drawing;
- 2D reconstruction;
- table/coordinates;
- canonical 3D preview;
- residual map.

Rules:
- geometry != identity;
- identity != connectivity;
- geometric proximity cannot create connectivity by itself;
- symbolic coordinates are permitted;
- local residuals remain explicit.

Deliverables:
- geometric kernel;
- topology graph;
- support/node/member identities;
- rigid offsets/zones;
- topology residuals.

Gate: `GEOMETRY_TOPOLOGY_READY` scoped by model domain.

### P6 — STRUCTURAL SEMANTICS / ASSET GRAPH

User question: What structural role does each reconstructed object perform?

Entity types include:
- support/core;
- analytical node;
- beam;
- column;
- wall;
- slab/diaphragm;
- rigid offset/zone;
- foundation member/support;
- special roof/member;
- nonstructural mass/load host where relevant.

Deliverable: stable solver-independent Structural Asset Graph.

Gate: `STRUCTURAL_IDENTITY_READY`.

### P7 — ENGINEERING PROPERTIES

User question: Do structural entities have the properties required for the intended assessment?

Workspaces:
- Sections;
- Reinforcement;
- Materials;
- Loads & Masses;
- Boundary Conditions;
- Foundations;
- Geotechnics;
- Diaphragms / offsets / releases;
- special structural features.

Every value answers:
- source?
- state?
- scope/entity?
- adopted rule?
- scenario?
- reviewer/authority?

Deliverables:
- Property Bindings;
- Load Model;
- Material/Knowledge Register;
- Foundation/Geotechnical Model Inputs;
- calculation blockers.

Gate: `ENGINEERING_PROPERTIES_READY` or scoped residual.

### P8 — CONDITION / EXPOSURE / DEGRADATION

User question: What is the current physical state and which mechanisms may affect performance?

Maintain separate layers:

`EXPOSURE -> OBSERVATION -> MEASUREMENT -> DAMAGE STATE -> MECHANISM SCREENING -> DEGRADATION MODEL -> STRUCTURAL EFFECT`

No layer auto-promotes the next.

Deliverables:
- Condition Map;
- Exposure Zones;
- Measurements;
- Damage States;
- degradation-model eligibility/residuals.

Gate: `CONDITION_BASELINE_READY`.

### P9 — KNOWLEDGE LEVEL / INVESTIGATION

User question: What is still unknown, what matters to the decision, and which investigation is worth performing?

Capabilities:
- knowledge-level / confidence-factor evidence pack;
- blocker-to-output impact map;
- candidate field/lab investigations;
- invasiveness/cost/access constraints;
- sensitivity ranking;
- future expected information gain / Value of Information.

Investigation becomes executable:

`MISSING FACT -> METHOD -> LOCATION/ENTITY -> FIELD TASK -> RESULT -> EVIDENCE -> CLAIM -> REASSESSMENT`

Deliverables:
- Knowledge Decision Pack;
- Investigation Plan;
- Field Packs;
- Investigation Results;
- updated claims/scenarios.

Human authority: Responsible Engineer / relevant specialist.

Gate: `KNOWLEDGE_STRATEGY_AUTHORIZED`.

### P10 — CANONICAL AS-IS MODEL GENERATION

User question: What is the current authorized structural representation before analysis assumptions are applied?

The canonical generation contains:
- stable identity;
- geometry/topology;
- current property bindings;
- explicit unknowns;
- evidence lineage;
- condition state;
- unresolved residuals.

It does not contain solver-specific discretization as authority.

Deliverable: `AS_IS_GENERATION`.

Gate: `AS_IS_GENERATION_APPROVED`.

### P11 — ASSESSMENT SCENARIOS & MODEL RULES

User question: Which admissible assumptions define the calculation scenario?

First-class scenario modes may include:
- historical baseline;
- conservative existing;
- probabilistic degradation;
- tests-updated/posterior;
- surveyed existing;
- additional project-specific scenarios.

Every scenario exposes differences from AS-IS:
- changed property;
- reason;
- rule/source;
- uncertainty;
- authorizer;
- downstream affected calculations.

Deliverables:
- Scenario;
- Model Rule Pack;
- scenario comparison/delta.

Gate: `SCENARIO_AUTHORIZED`.

### P12 — CALCULATION MODEL / SOLVER HANDOFF

User question: Is the authorized scenario technically and epistemically ready to be projected into a solver?

Adapter pipeline:

`CEW CANONICAL GENERATION + SCENARIO + RULE PACK -> SOLVER PROJECTION -> ADAPTER QA -> EXECUTION AUTHORIZATION`

Each adapter must produce:
- projection ID/version/hash;
- CEW entity -> solver entity map;
- node/member/section/material/load mappings;
- releases/constraints/rigid-zone mappings;
- unsupported feature report;
- excluded residual scopes;
- numerical idealization report;
- solver version/configuration;
- deterministic QA receipt.

Initial adapters:
- EdiLus-EE guided handoff / import-export where technically available;
- current-canonical OpenSees adapter;
- optional independent Code_Aster or other FEM cross-check adapter.

The existing preliminary OpenSees `M0-OS-0002` is a historical prototype and must not be treated as the current adapter.

Human authority: solver execution authorization.

Gate: `CALCULATION_MODEL_READY`.

### P13 — FEM / STRUCTURAL ANALYSIS

User question: Did the numerical analysis execute as intended and is the result set technically valid?

Capabilities:
- analysis-case management;
- static/dynamic/modal/nonlinear methods as admitted by rule pack;
- convergence/solver diagnostics;
- modal/mass sanity checks;
- equilibrium and boundary-condition QA;
- cross-solver comparison when configured;
- immutable result bundle.

Deliverables:
- Solver Run Receipt;
- Result Set;
- QA diagnostics;
- analysis residuals.

Gate: `ANALYSIS_VALIDATED`.

### P14 — VERIFICATION / ASSESSMENT

User question: What is the structural conclusion, why, and how robust is it?

Every verification result maps to:
- CEW entity/scope;
- scenario;
- solver run;
- combination/case;
- demand;
- capacity;
- failure/verification mode;
- governing rule;
- uncertainty/sensitivity;
- relevant evidence gaps.

Capabilities:
- element/result maps;
- global performance indicators;
- demand/capacity;
- seismic assessment measures where applicable;
- sensitivity to assumptions;
- comparison between scenarios;
- residual-aware conclusion drafting.

Deliverables:
- Verification Register;
- Engineering Assessment;
- unresolved decision risks;
- technical conclusion approval.

Human authority: Responsible Engineer.

Gate: `ASSESSMENT_CONCLUSION_APPROVED`.

### P15 — INTERVENTION DESIGN

User question: What intervention options resolve the identified deficiencies and with what consequences?

Intervention alternatives may include:
- repair;
- local strengthening;
- global strengthening;
- durability/protection;
- foundation/geotechnical intervention;
- operational/use restrictions where applicable.

Each alternative creates a proposed generation rather than editing AS-IS.

Capabilities:
- intervention objects bound to entities;
- new property/topology generation;
- cost/invasiveness/construction constraints;
- solver reassessment;
- option comparison;
- approval history.

Gate: `INTERVENTION_GENERATION_APPROVED`.

### P16 — EXECUTION / AS-BUILT / MONITORING

User question: What was actually executed and how does the asset evolve after intervention?

Capabilities:
- executed-generation evidence;
- deviations from design;
- as-built source pack;
- inspection/monitoring plan;
- sensor/manual observation linkage;
- future reassessment trigger;
- lifecycle history.

Deliverables:
- Executed Generation;
- Monitoring Baseline;
- Asset Dossier;
- future reassessment schedule/conditions.

Gate: `LIFECYCLE_BASELINE_ESTABLISHED`.

## 6. Cross-cutting product workspaces

Primary navigation:

1. Project Home
2. Sources
3. Evidence
4. Reconstruction
5. Structural Model
6. Properties
7. Condition
8. Investigations
9. Scenarios
10. Analysis / FEM
11. Verification
12. Interventions
13. Dossier / Audit

Each workspace reads the same project graph and does not create a parallel source of truth.

## 7. Project Home / Control Room redesign

The Project Home is not an issue list.

It must show:

- current lifecycle phase(s);
- current approved generation;
- current authorized scenario;
- readiness by engineering domain;
- blockers by impact;
- decisions awaiting human authority;
- active investigations;
- analysis eligibility;
- latest solver/verifications;
- next recommended actions;
- deliverables due/complete.

Example:

```text
N12 — Existing RC Building

Current objective: Structural safety assessment
Current generation: GEN-1 Reconstructed Existing
Current phase: P9 Knowledge / Investigation

Geometry & topology       READY
Sections                  READY
Reinforcement             WATCH
Current concrete          BLOCKED
Loads & masses            BLOCKED
Foundation Z              BLOCKED
Geotechnics               BLOCKED
Condition                 DATA REQUIRED

CALCULATION MODEL         NOT READY

Next best actions
1. Decide current-concrete investigation strategy
2. Close load/mass evidence pack
3. Define foundation vertical datum acquisition
```

## 8. Information Requirement model

CEW shall implement an IDM/IDS-inspired product primitive:

`InformationRequirement`

Minimum fields:
- requirement_id;
- phase;
- purpose/use;
- target entity/domain;
- required property/information;
- allowed epistemic states;
- required authority/review;
- units/value constraints where relevant;
- source/evidence requirements;
- mandatory/conditional status;
- compliance validator;
- affected downstream gates.

This prevents hidden requirements inside scripts and lets the engineer know why a datum is required.

## 9. Engineering Rule Pack

`EngineeringRulePack` is versioned and immutable after approval.

Fields:
- jurisdiction;
- standard/code identifiers and editions;
- project assessment objective;
- design/assessment situations;
- actions/combinations rules;
- knowledge-level/confidence-factor rules;
- material rules;
- analysis methods admitted;
- verification rules;
- solver-specific implementation notes;
- exclusions/deviations;
- reviewer/approver;
- effective project generation/scenario.

For the Italian CEW-EX profile, NTC 2018 Chapter 8 and its applicable instructions form a primary rule spine; Eurocodes/other admitted references can be configured where applicable.

## 10. Human Evidence Workspace

Mandatory layout:

LEFT — source and evidence
- deep zoom source viewer;
- selected EvidenceRegion;
- MICRO/MESO/MACRO tabs;
- page coordinates;
- source version.

CENTER — engineering context
- selected structural entity;
- 2D/3D synchronized highlight;
- existing claims;
- related residual;
- downstream impact.

RIGHT — decision
- machine proposal(s);
- human input in natural engineering language;
- confirm/correct/reject/defer;
- epistemic state request;
- authority statement;
- resulting patch preview;
- explicit note that submit != canonical write.

No user is required to convert ordinary engineering language into a parser-specific grammar.

## 11. Structural Model Workspace

The same model supports maps:
- Geometry;
- Evidence;
- Completion;
- Properties;
- Loads/Masses;
- Reinforcement;
- Condition;
- Scenario Delta;
- FEM Results;
- Verification;
- Intervention.

Selecting an element exposes its engineering passport:

```text
ENTITY
identity / storey / type

GEOMETRY
value / state / evidence

SECTION
value / state / evidence

REINFORCEMENT
upper / lower / stirrups / state / evidence

MATERIAL
historical / current / scenario

LOAD HOSTING
source / adopted model

CONDITION
observations / measurements

ANALYSIS
eligible? scenario? solver mapping?

RESULTS
latest authorized run

ISSUES
blocking/local/nonblocking
```

## 12. Solver / FEM architecture

CEW solver integration is a controlled round trip.

### Export

- snapshot canonical generation;
- snapshot authorized scenario;
- resolve InformationRequirements;
- apply ModelRule pack;
- generate solver projection;
- produce entity map;
- validate counts/connectivity/properties/units;
- list unsupported/residual scopes;
- human execution authorization.

### Execute

- record solver/version/input hash;
- run configured analysis;
- capture warnings/convergence/status;
- persist immutable output bundle.

### Import

- verify projection/run identity;
- map solver outputs to CEW entity IDs;
- normalize units without losing raw values;
- create SolverResult objects;
- run sanity/engineering QA;
- never write back into evidence or source claims.

### Independent validation

When required, CEW can project the same canonical scenario into an independent solver for selected benchmarks. Differences become comparison objects, not silent reconciliation.

## 13. Agent system

Agents are specialists behind the workflow, not the user interface.

Required agents/work packages:
- Source Intake Agent;
- Document Understanding Agent;
- Evidence Agent;
- Geometry Agent;
- Topology Agent;
- Structural Semantics Agent;
- Section Agent;
- Reinforcement Agent;
- Material Agent;
- Load Agent;
- Foundation Agent;
- Geotechnical Agent;
- Condition Agent;
- Investigation Agent;
- Scenario Agent;
- Solver Adapter Agent;
- Result QA Agent;
- Verification Support Agent;
- Intervention Comparison Agent;
- Provenance/Adjudication Agent.

Each returns only:
- proposals;
- evidence links;
- residuals;
- diagnostics;
- gate candidates.

No agent owns final engineering approval.

## 14. Product state model

Every capability has independent maturity dimensions:

1. `ENGINE_AVAILABLE`
2. `DATA_CONTRACT_VALIDATED`
3. `INTEGRATED_WITH_PROJECT_GRAPH`
4. `USER_WORKFLOW_AVAILABLE`
5. `ENGINEERING_GATE_VALIDATED`
6. `HUMAN_FACTORS_VALIDATED`
7. `PRODUCTION_READY`

`OPERATIONAL` is no longer sufficient as a single status.

## 15. Human-factors acceptance

Each major workflow needs scenario-based tests using representative engineering material.

Examples:

### HF-EVIDENCE-01
A structural engineer can resolve an ambiguous reinforcement note while simultaneously seeing exact source region, local detail, whole sheet, linked member and downstream effect.

### HF-GEOMETRY-01
A model engineer can identify why two visually touching members are not connected and inspect the evidence/rule supporting topology.

### HF-INVESTIGATION-01
An engineer can move from a calculation blocker to a field test request and ingest the result without manually editing canonical CSV/JSON.

### HF-SOLVER-01
An engineer can understand why the model is not calculation-ready and which exact unresolved facts block authorization.

### HF-RESULT-01
An engineer can select a failed element and trace result -> solver run -> scenario -> property -> claim -> source.

A feature that passes CI but fails its human task is not releasable as a user workflow.

## 16. Product implementation sequence

### Wave A — Product spine

A1. Reconcile CEW product state with actual runtime/canonical project state.
A2. Implement ProjectPhase / Deliverable / Decision / InformationRequirement primitives.
A3. Replace current home with lifecycle/readiness/next-action Project Home.
A4. Add user-facing terminology layer over internal IDs.

### Wave B — Evidence to model

B1. Source Hub.
B2. Integrated Evidence Workspace with MICRO/MESO/MACRO.
B3. Synchronized Reconstruction Workspace.
B4. Element-centric Structural Model Workspace.
B5. Domain Property Workspaces.

### Wave C — Assessment readiness

C1. Engineering Rule Pack.
C2. Executable Investigation / Field Pack.
C3. Knowledge-level and calculation-readiness decision workspace.
C4. Authorized AS-IS generation and scenarios.

### Wave D — Solver round trip

D1. Mark historical OpenSees prototype explicitly non-current.
D2. Build current canonical solver-neutral projection contract.
D3. Implement current-canonical OpenSees adapter.
D4. Implement EdiLus handoff/mapping contract.
D5. Import and map results.
D6. Cross-solver benchmark cases.

### Wave E — Verification and lifecycle

E1. Verification Workspace.
E2. Scenario sensitivity/uncertainty.
E3. Intervention generations.
E4. Executed/as-built generation.
E5. Monitoring/reassessment lifecycle.
E6. Technical dossier/report builder with full lineage.

## 17. Definition of product success

CEW succeeds when the responsible engineer can start with an unstructured dossier and finish with a defensible assessment without ever losing the distinction between evidence, assumption, model and decision.

The decisive product test is bidirectional traceability:

`SOURCE -> RESULT -> DECISION`

and

`DECISION/BLOCKER -> REQUIRED INFORMATION -> ACQUISITION -> UPDATED MODEL -> NEW RESULT`.

The engineer remains in control; automation removes search, transcription, coordination and consistency burden rather than hiding engineering judgment.
