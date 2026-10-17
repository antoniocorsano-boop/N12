# CEW Product Architecture v1

## Product identity

**CEW — Civil Engineering Workflow** is the parent engineering-workflow platform.

CEW is not a single solver and is not tied to one commercial FEM package. It is an evidence-first engineering system that converts heterogeneous project information into auditable engineering models, analysis scenarios, decisions, intervention designs and final technical records.

The first vertical subsystem is:

**Civil Existing Workflow (CEW-EX)** — workflows for assessment, recovery, repair, strengthening and re-use of existing structures reconstructed from legacy or incomplete documentation, surveys, tests, photographs and engineering evidence.

N12 is the reference pilot and proving ground for CEW-EX.

---

## Product decomposition

```text
CEW — Civil Engineering Workflow
|
+-- Core Platform
|   +-- Project / source registry
|   +-- Evidence + provenance graph
|   +-- Epistemic-state engine
|   +-- Claim / residual / conflict ledger
|   +-- Orchestrator + specialist agents
|   +-- Gate / receipt system
|   +-- Human review and approval
|   +-- Artifact / version registry
|   +-- Standards / rule packs
|
+-- Civil Existing Workflow (CEW-EX)
|   +-- Legacy Documentation Intake
|   +-- Primary Evidence Reconstruction
|   +-- Canonical Structural Model Builder
|   +-- Existing-Structure Knowledge Model
|   +-- Multi-Mode Existing Assessment Engine
|   +-- Deterioration / Exposure Engine
|   +-- Investigation Planner + Value of Information
|   +-- Structural Analysis Adapters
|   +-- Intervention / Repair / Strengthening Workflow
|   +-- Reassessment + comparison workflow
|   +-- Existing-building dossier / technical report generator
|
+-- Future CEW verticals
    +-- New Structures Workflow
    +-- Geotechnical Workflow
    +-- Infrastructure / Bridges Workflow
    +-- Inspection / Monitoring Workflow
    +-- Construction / QA Workflow
```

The CEW core must remain domain-generic. Existing-building semantics live in CEW-EX.

---

# 1. Canonical information architecture

CEW uses four different objects. They must never be collapsed into one another.

## 1.1 Source
An immutable or versioned source artifact:
- legacy drawing;
- calculation report;
- photograph;
- survey;
- laboratory result;
- geotechnical report;
- monitoring stream;
- regulation / standard;
- engineer-supplied measurement.

## 1.2 Evidence / claim
A statement extracted from one or more sources with provenance and epistemic state.

Examples:
- `P22 section = 40x50 cm — DOC`;
- `support core XY = (...) — MIS`;
- `foundation member 22bis-27 family B — SUPPORTED`;
- `current concrete strength — ND`.

## 1.3 Canonical structural model
A solver-independent engineering representation of structural identity, topology and properties.

It contains stable identities for:
- levels / diaphragms;
- supports;
- nodes;
- rigid offsets / rigid zones;
- beam / column / wall / slab / foundation members;
- sections;
- materials;
- reinforcement;
- loads;
- boundary conditions;
- soil-interface objects;
- deterioration state;
- uncertainty variables.

Every populated field must point to evidence or to an explicitly admitted modeling rule.

## 1.4 Derived analysis model
A scenario-specific solver model generated from the canonical model.

Examples:
- historical-as-designed;
- conservative existing;
- probabilistic degradation P50;
- severe degradation P95;
- essential-test posterior;
- surveyed current state;
- repaired state;
- strengthened state.

A derived model may never silently overwrite the canonical evidence model.

---

# 2. Epistemic model

Existing CEW states remain valid:

- `DOC` — directly documented;
- `MIS` — measured;
- `RIF` — reported/reference information;
- `INF` — explicit engineering inference;
- `INC` — inconsistent/conflicting;
- `ND` — not determined.

CEW-EX adds two derived states:

- `MOD` — model-derived scenario value; not evidence;
- `POST` — posterior value/distribution updated from evidence and a declared probabilistic model.

Mandatory rule:

```text
MOD != MIS
POST != MIS
MOD and POST cannot overwrite DOC/MIS evidence.
```

Every scenario output therefore carries both:

```text
value
value_state
source_claims[]
model_rule_id (optional)
scenario_id
```

---

# 3. Canonical Structural Model Builder

This component is **not yet implemented**. N12 currently has canonical tables and a frozen analytical topology, but does not yet have the reusable CEW 3D model-building subsystem.

The product implementation shall consist of five layers.

## 3.1 Structural identity graph
Creates globally stable IDs independent of drawings and solvers.

Example:

```text
BUILDING/N12/G2/PILLAR/P22
BUILDING/N12/G3/BEAM/B036
BUILDING/N12/FOUNDATION/MEMBER/22bis-27
```

Identity persists through reassessment, repair and strengthening.

## 3.2 Geometric kernel
Solver-independent 3D representation:

```text
Point3D
Axis3D
MemberAxis
CrossSectionPlacement
RigidOffset
Surface
StoreyPlane
FoundationPlane
LocalCoordinateSystem
```

It must support incomplete geometry. A node may temporarily have symbolic Z or unresolved coordinates if the evidence gate allows it.

## 3.3 Structural topology graph
Defines actual engineering connectivity independently from geometric proximity.

A beam is connected to a column only through an authoritative topology claim or admitted rule — never because two lines happen to be near each other.

## 3.4 Property graph
Binds:
- section;
- material;
- reinforcement;
- loads;
- support/soil properties;
- deterioration state;
- uncertainty distributions.

## 3.5 3D viewer / human adjudication layer
The viewer is not an authority by itself. It provides:
- structural 3D visualization;
- source overlay;
- epistemic coloring;
- residual/conflict highlighting;
- element selection -> evidence lineage;
- before/after scenario comparison;
- manual adjudication with receipt.

Proposed visual semantics:
- DOC = documented;
- MIS = measured;
- RIF = reported;
- INF = inferred;
- MOD = scenario-derived;
- INC = conflict;
- ND = unresolved.

Color is a UI concern; evidence state remains machine-readable and independent of color.

---

# 4. Multi-Mode Existing Assessment Engine

The engine shall generate analysis scenarios from one canonical structural model without changing the evidence model.

Mandatory modes:

## MODE-1 — HISTORICAL_BASELINE
Reconstructs the historical/as-designed state from documented historical values.

Purpose:
- reproduce historical assumptions;
- compare original design with current assessment;
- distinguish original weakness from subsequent deterioration.

## MODE-2 — CONSERVATIVE_EXISTING
Uses only evidence plus explicitly declared conservative modeling rules.

Purpose:
- allow bounded screening where comprehensive tests are unavailable;
- expose every assumption;
- never promote assumptions to measured facts.

## MODE-3 — PROBABILISTIC_DEGRADATION
Uses exposure, age, protection, material priors and visible condition to generate distributions/scenario envelopes.

Purpose:
- mild / expected / severe or percentile states;
- sensitivity analysis;
- identify controlling uncertainty.

## MODE-4 — ESSENTIAL_TESTS_UPDATED
Updates MODE-3 priors using a deliberately small number of high-information tests.

Purpose:
- Bayesian/posterior updating;
- maximize information per test/cost/invasiveness;
- produce a test plan through Value of Information analysis.

## MODE-5 — SURVEYED_EXISTING
Uses sufficiently complete direct surveys/tests for the current-state engineering model.

Purpose:
- highest measurement-driven assessment mode supported by project evidence.

The mode name does **not** assert an NTC knowledge level. LC/FC remains a separate regulatory assessment produced only from the evidence actually available and the applicable rule pack.

---

# 5. Deterioration / Exposure Engine

The deterioration engine sits between the evidence model and analysis adapters.

```text
Canonical Structural Model
        |
        v
Exposure Profile
        |
        v
Deterioration Models
        |
        v
Scenario State / Distribution
        |
        v
Structural Property Adapter
        |
        v
Solver Adapter
```

Initial mechanism registry:

- carbonation initiation;
- chloride ingress where applicable;
- reinforcement corrosion propagation;
- longitudinal-bar section loss;
- stirrup section loss;
- cover cracking/spalling state;
- bond degradation;
- moisture / water-exposure state;
- freeze/thaw or chemical attack only when applicable;
- foundation/soil uncertainty as a separate geotechnical mechanism family.

The engine does not assume that every mechanism applies to every project.

Every model has:
- applicability criteria;
- input variables;
- units;
- parameter provenance;
- uncertainty model;
- validity range;
- output variables;
- citation/reference identifier;
- calibration state.

No deterioration model may directly alter evidence fields.

---

# 6. Investigation Planner and Value of Information

The CEW-EX assessment workflow shall be iterative:

```text
Evidence
 -> preliminary model
 -> uncertainty/sensitivity
 -> candidate investigations
 -> Value of Information ranking
 -> selected tests
 -> evidence update
 -> posterior model
 -> reassessment
```

Each proposed investigation records:
- fact/parameter to determine;
- affected elements;
- current epistemic state;
- candidate test;
- invasiveness;
- expected uncertainty reduction;
- affected verification outputs;
- cost/time placeholder;
- priority;
- decision: execute / defer / not justified.

This permits three practical project strategies:

1. **Distributed investigations** — broad evidence acquisition;
2. **Essential investigations** — minimum high-value tests;
3. **Comparison-only modeling** — no new invasive evidence, explicit uncertainty envelope.

---

# 7. Analysis adapter architecture

CEW does not embed one solver as its authority.

```text
Canonical Structural Model
   + Scenario Manifest
           |
           +-- EdiLus adapter
           +-- Open-source FEM adapter
           +-- future solver adapters
```

Every adapter must produce an export receipt containing:
- canonical model version;
- scenario version;
- element ID mapping;
- assumptions translated;
- unsupported features;
- units;
- solver-specific transformations;
- export checksum.

Results return through a reverse mapping to canonical identities.

This makes cross-solver comparison possible.

---

# 8. Intervention workflow

CEW-EX must continue beyond assessment.

```text
Existing state
 -> damage/deficiency diagnosis
 -> intervention objectives
 -> candidate repair/strengthening measures
 -> intervention model variants
 -> structural reassessment
 -> constructability / durability checks
 -> selected design
 -> drawings/specifications
 -> execution / QA evidence
 -> post-intervention canonical state
```

The pre-intervention model remains immutable. Strengthening creates a new model generation.

---

# 9. N12 as reference implementation

N12 already proves several CEW-EX concepts:
- immutable source roles;
- evidence states;
- residual-first workflow;
- blind primary-evidence extraction;
- claim-scoped promotion;
- stable structural identities;
- frozen M0-G topology;
- FPEP foundation authority;
- solver placement rules separated from source evidence;
- deterministic receipts and queues.

Current N12 M1E remains `RESIDUAL_NOT_CALCULATION_MODEL_READY`; therefore the first CEW-EX multi-mode implementation must consume that state rather than bypass it.

The N12 reference implementation should next build:

1. Canonical Structural Model Contract;
2. 3D Structural Model Builder v0 (identity + topology + geometric kernel export);
3. Multi-Mode Existing Assessment Engine v1;
4. Exposure/Deterioration Model Registry v1;
5. Investigation Planner v1;
6. EdiLus/Open-FEM adapters after calculation inputs are eligible.

---

# 10. Non-negotiable safety and epistemic invariants

1. Sources are never rewritten by models.
2. Solver outputs never become source evidence automatically.
3. Geometric proximity never creates topology.
4. `MOD` and `POST` never become `MIS` silently.
5. Historical values remain historical unless a rule explicitly uses them in a scenario.
6. A scenario may be executable without being a verified current-state model, but must say so explicitly.
7. Regulatory LC/FC and probabilistic confidence are different quantities.
8. Every residual stays machine-readable.
9. Every human override requires rationale and receipt.
10. Every intervention creates a new model generation rather than mutating the pre-intervention baseline.
