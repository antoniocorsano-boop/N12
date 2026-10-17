# CEW Stakeholder Product Architecture Review — Full v1

Status: CANONICAL ANALYSIS SNAPSHOT  
Date: 2026-08-24  
Product: CEW — Civil Engineering Workflow  
Subsystem: Civil Existing Workflow (CEW-EX)  
Reference implementation: N12

## Purpose

This document preserves the complete stakeholder/product-architecture analysis that reframes CEW as an engineering operating system for the technical project, rather than as a collection of parsers, registers, viewers and solver helpers.

The target stakeholder is primarily the engineer/technician responsible for managing the project, its phases, information, evidence, residuals, investigations, model construction, verification and intervention design.

The intended end state is a system capable of taking the project from heterogeneous and possibly old documentation to an interrogable canonical engineering twin, explicit knowledge/uncertainty state, investigation strategy, assessment scenarios, solver handoff, verification and intervention lifecycle.

---

## 1. Product positioning

CEW must not become another BIM authoring tool. It should govern:

**information → evidence → canonical model → uncertainty → decision → verification → intervention → lifecycle.**

The product should appear to the engineer as a single environment that accompanies the project from:

> “I have a folder of documents, photographs and scattered information”

through:

> “I have an interrogable structural model, I know the quality and provenance of every relevant datum, I know what is missing, I can plan investigations, build scenarios, perform checks and design interventions.”

The internal implementation can be complex; the operational interface must remain decision-oriented.

---

## 2. Benchmark-informed product principles

### 2.1 CDE / Information Management

CEW should incorporate an explicit Common Data Environment / information-management layer, consistent with mature ISO 19650-type workflows.

Information state and epistemic state must remain distinct.

Example information states:

- `WORKING`
- `SHARED_FOR_COORDINATION`
- `REVIEW_REQUIRED`
- `APPROVED_FOR_USE`
- `SUPERSEDED`
- `ARCHIVED`

Epistemic states remain:

- `DOC`
- `MIS`
- `RIF`
- `INF`
- `INC`
- `ND`
- `MOD`
- `POST`

A document may be `APPROVED_FOR_USE` and still contain an `ND` property. These two dimensions must never be conflated.

### 2.2 Federated engineering twin

CEW should follow the mature digital-twin pattern of federating heterogeneous engineering data around stable engineering identities rather than forcing every source into one authoring representation.

The CEW Engineering Twin should federate:

- source documents;
- claims;
- geometry;
- topology;
- structural semantics;
- materials;
- reinforcement;
- loads;
- foundations;
- geotechnics;
- observations;
- condition;
- investigations;
- scenarios;
- solver mappings;
- results;
- interventions;
- later monitoring generations.

### 2.3 Contextual issue management

BCF-like issue management is a useful benchmark, but CEW issues must contain richer engineering semantics.

A CEW issue/residual should be capable of linking:

- structural entity;
- 3D viewpoint;
- source sheet/document;
- image crop;
- claim;
- evidence state;
- severity;
- blocking impact;
- candidate sources;
- proposed resolution;
- investigation option;
- assigned specialist;
- human decision;
- closure receipt.

This creates a universal resolution object, not merely a BIM clash ticket.

### 2.4 Collaboration and ownership

CEW should support explicit responsibility boundaries similar to mature shared-model systems, but at a finer engineering-work-package level:

- `PROJECT_OWNER`
- `MODEL_GENERATION_OWNER`
- `WORK_PACKAGE_OWNER`
- `TECHNICAL_REVIEWER`
- `ENGINEERING_APPROVER`

AI agents may extract, compare, propose, validate deterministic rules and prepare evidence, but they do not become the Engineering Approver.

---

## 3. Project Control Room

The project home should be the main stakeholder surface.

For a project such as N12 it should immediately communicate:

- current project phase;
- overall progress;
- information readiness by domain;
- model readiness;
- blockers;
- local residuals;
- non-blocking watches;
- next recommended action;
- active investigations;
- assessment modes available;
- solver readiness;
- intervention generations if present.

Example:

```text
N12
Existing reinforced-concrete building

MODEL                     92%
██████████████████░░

Geometry                  READY
Sections                  READY
Reinforcement             WATCH
Current materials         BLOCKED
Loads                     RESIDUAL
Foundations               WATCH
Geotechnics               BLOCKED
Condition                 DATA REQUIRED

CALCULATION MODEL
NOT READY

6 blockers
17 local residuals
42 non-blocking watches
```

The system should then show a recommended action, for example:

> Recover historical RC-P13 load evidence — zero invasiveness — potentially closes part of B02.

The engineer should not need to understand internal queue mechanics to know what to do next.

---

## 4. End-to-end project phases

The formal CEW-EX lifecycle should be organized as:

- **P0 — Project Definition**
- **P1 — Source Acquisition**
- **P2 — Document Understanding**
- **P3 — Claim / Evidence Reconstruction**
- **P4 — Geometry & Topology**
- **P5 — Structural Semantics**
- **P6 — Canonical 3D Model**
- **P7 — Engineering Properties**
- **P8 — Condition & Exposure**
- **P9 — Knowledge / Investigation**
- **P10 — Assessment Scenarios**
- **P11 — Solver Handoff & Verification**
- **P12 — Intervention Design**
- **P13 — Executed / Monitored Asset**

The workflow is not rigidly linear. Independent work packages may continue while local residuals remain open.

A geotechnical blocker must not prevent reinforcement-document recovery. A local unreadable label must not freeze global geometry reconstruction.

This is a core CEW operating principle:

> **Local residuals do not block unrelated work.**

---

## 5. P0 — Project Definition Workspace

Before processing documents, CEW creates a Project Identity Pack containing at least:

- work/asset identification;
- location;
- structural typology;
- construction period;
- use;
- storey count;
- known additions/extensions;
- known past interventions;
- historical codes/standards if known;
- scope of engagement;
- intended solver/software;
- desired assessment depth;
- known access/investigation constraints.

The engineer may select an initial knowledge strategy:

1. diffuse investigations;
2. essential investigations;
3. document + comparative-model route.

This is a project strategy, not an automatic LC/FC decision.

---

## 6. P1 — Source Hub / CDE

All source material enters one controlled environment:

- PDFs;
- scans;
- drawings;
- photographs;
- calculation reports;
- spreadsheets;
- CAD files;
- survey data;
- laboratory reports;
- field records;
- videos where relevant.

Each source receives stable metadata:

```text
SOURCE_ID
TYPE
DATE
AUTHOR
ORIGIN
QUALITY
HASH
PAGE_COUNT
DISCIPLINE
INFORMATION_STATE
EXPECTED_ROLE
```

No extracted engineering datum may lose the link to its originating source.

---

## 7. Technical Evidence Viewer

The viewer should be a technical high-resolution evidence environment, not a generic PDF viewer.

Capabilities should include:

- very deep zoom;
- persistent tiles;
- image coordinates;
- crop creation;
- markers;
- overlays;
- measurement tools;
- contrast/sharpening controls where legitimate;
- rotation;
- side-by-side comparison;
- source-to-entity linking;
- 2D/3D synchronized navigation.

### EvidenceSnippet

Image/document crops should become persistent engineering objects, not temporary AI artifacts.

Example schema:

```text
snippet_id
source_id
page
bbox
tile_ref
resolution
claim_ids
entity_ids
created_by
review_state
```

The system should preserve three context levels:

- **MICRO** — crop containing the label/detail;
- **MESO** — surrounding element context;
- **MACRO** — sheet/page context.

The user must be able to move instantly from claim → crop → local context → full source.

---

## 8. Human Evidence Resolution Module

When extraction is uncertain, CEW should not merely report “unreadable”.

It should prepare a resolution card containing:

- issue description;
- image crop;
- wider context;
- likely alternatives;
- source location;
- confidence/support state;
- relevant homologous elements, clearly marked as non-authoritative unless an equivalence rule is established;
- actions.

Example:

```text
P22

[image crop]

Possible readings:
○ 40×40
○ 40×50
○ not determinable

Source: TAV-03S
Raster coordinates: ...

[Confirm] [Reject] [Open context] [Leave ND]
```

This module is central to overcoming blocks efficiently while preserving human engineering control.

---

## 9. Claim Engine

CEW should store engineering claims, not just flat data cells.

Example:

```text
CLAIM C12971

target: G2-P18
property: section
value: 110×30 cm
state: DOC
source: TAV-03S
evidence: snippet-874
validated_by: human
timestamp: ...
```

A measured coordinate could instead be:

```text
value: x = 5.55 m
state: MIS
method: AFFINE_REGISTRATION
```

Every claim remains independently traceable.

---

## 10. Conflict and supersession model

Contradictory sources must not overwrite one another silently.

CEW creates a conflict object and records the adjudication.

Example:

```text
P18 section

TAV-02S → 100×30
TAV-03S → 110×30

authoritative_current: TAV-03S
current_value: 110×30
previous_claims: preserved
```

The user must be able to see both the current value and why it became current.

---

## 11. Geometry Reconstruction Workspace

The ideal reconstruction workspace synchronizes:

1. original sheet/image;
2. reconstructed 2D structural grid;
3. entity/property table;
4. residual map;
5. 3D model where available.

Selecting a support or member in any one view highlights it in all others.

This is a **Digital Evidence Twin**, not merely a geometric twin.

The reconstruction assistant may propose candidates but cannot create authoritative geometry without evidence or an admitted modeling rule.

Candidate states may include:

- `CONFIRMED`
- `SUPPORTED`
- `CANDIDATE`
- `CONFLICT`
- `ND`

---

## 12. Geometry versus topology

A major CEW invariant is that visible geometric contact does not automatically create structural connectivity.

The system must separate:

```text
POINT GEOMETRY
→ SUPPORT IDENTITY
→ INCIDENCE
→ STRUCTURAL CONNECTION
```

Connectivity is established by claim/evidence or an explicit modeling rule, not by nearest-neighbour or proximity heuristics.

---

## 13. Structural semantics

Once geometry/topology is established, CEW assigns structural roles such as:

- `NODE`
- `SUPPORT_CORE`
- `FACE_NODE`
- `BEAM`
- `COLUMN`
- `WALL`
- `SLAB`
- `RIGID_OFFSET`
- `FOUNDATION_MEMBER`
- `FOUNDATION_SUPPORT`
- `ROOF_SPECIAL_MEMBER`

These populate the solver-independent Canonical Structural Model.

---

## 14. Canonical 3D Engineering Twin

The canonical model is not a rendered image and is not a solver file.

It is a layered engineering graph containing:

- identity graph;
- geometric kernel;
- topology graph;
- property graph;
- evidence lineage;
- condition state;
- scenario overlays;
- solver mappings;
- generation lineage.

The model may be incomplete. Symbolic or missing coordinates/properties remain explicit.

### Required interactive maps

The same model should support multiple engineering maps:

**Geometry Map** — structural geometry/topology.

**Evidence Map** — colors by `DOC/MIS/RIF/INF/INC/ND`.

**Completion Map** — colors by `READY/WATCH/RESIDUAL/BLOCKED`.

**Assessment Map** — historical/conservative/probabilistic/posterior/surveyed scenarios.

**Condition Map** — observed exposure/damage/measurement states.

**Result Map** — solver response/checks.

**Intervention Map** — proposed/executed strengthening/repair generations.

---

## 15. Element-centric interaction

The engineering entity, not the source file, becomes the main navigation object.

Example selected beam:

```text
G3-B021

GEOMETRY
✓ complete

SECTION
80×20
DOC

MATERIAL
historical DOC
current ND

REINFORCEMENT
longitudinal DOC
stirrups DOC

LOADS
partial

CONDITION
ND

DEGRADATION
not assessed

CALCULATION
not ready

SOURCES
TAV-04S
TAV-034A
RC-P13
```

From the entity the engineer can open evidence, residuals, investigations, solver results or intervention history.

Conversely, any source claim must resolve back to the entity.

---

## 16. Universal Residual / Issue Manager

Residuals should be organized by engineering impact rather than shown as one flat list.

Suggested classes:

- `BLOCKING`
- `LOCAL_BLOCKING`
- `NON_BLOCKING`
- `INFORMATIONAL`

Example:

| Residual | Impact | Next action |
|---|---:|---|
| uncertain section P18 | high | open evidence crop |
| foundation elevation | high | recover vertical datum |
| eaves centerline | low | retain ND |
| reinforcement B021 | medium | inspect TAV-A |
| current geotechnics | high | investigation route |

### Residual Resolution Workspace

Opening a residual should automatically gather:

- affected entity;
- source claims;
- candidate sources;
- relevant crops;
- surrounding context;
- alternative interpretations;
- related homologous elements;
- explicit warning where analogy is not authorized;
- impact on model/verification;
- allowed actions.

Example:

```text
Problem:
reinforcement G3-B021

Candidate sources:
TAV-034A
TAV-05A
RC-P13

[crop A]
[crop B]
[crop C]

Homologous elements:
G3-B019
G3-B020

WARNING:
analogy not authorized

Actions:
[bind evidence]
[leave ND]
[create investigation]
[exclude affected verification scope]
```

---

## 17. Specialist agents and orchestration

CEW should use specialist agents behind the interface, each operating within a bounded authority.

Possible agents:

- Document Agent
- Geometry Agent
- Topology Agent
- Section Agent
- Reinforcement Agent
- Load Agent
- Foundation Agent
- Geotechnical Agent
- Condition Agent
- Degradation Agent
- Investigation Agent
- Solver Agent
- QA Agent

The orchestrator issues limited work items.

Each agent returns:

```text
claims
evidence
residuals
warnings
gate_result
```

Agents do not arbitrarily rewrite the global model.

---

## 18. Work Queue and progress model

The system should expose active work items in stakeholder-readable form.

Example:

```text
M1A-REINF-G3-B021
source: TAV-034A
state: HUMAN_REVIEW
reason: label poorly readable
```

The machine may continue independent work while this item is waiting.

Every domain/work package uses gate states such as:

- `PASS`
- `PASS_WITH_WATCH`
- `RESIDUAL`
- `BLOCKED`
- `FAIL`

This gives the engineer a stable vocabulary for project progress.

---

## 19. Engineering property workspaces

CEW should provide dedicated but connected workspaces for:

### Materials & Knowledge

Separate:

- historical design values;
- current direct evidence;
- current measured properties;
- uncertainty distributions;
- LC/FC or other regulatory knowledge states;
- model assumptions.

Historical values must never silently become current properties.

### Loads & Masses

Separate:

- historical load reconstruction;
- current permanent loads;
- current variable loads;
- mass model;
- tributary/load-path assumptions;
- combinations;
- unresolved load components.

### Foundations & Geotechnics

Separate:

- foundation topology;
- geometry/elevation;
- section and reinforcement binding;
- ground datum;
- current geotechnical model;
- historical soil assumptions;
- settlement/SSI inputs.

### Exposure / Condition / Degradation

Separate:

- exposure;
- protection systems;
- observed condition;
- measured damage;
- candidate deterioration mechanisms;
- calibrated degradation models;
- structural property effects.

No mechanism is activated solely from age, location or visual recollection.

---

## 20. Investigation Planner and future Value of Information

The Investigation Planner should transform unresolved decision-relevant uncertainty into candidate investigation actions.

Initial planner outputs may use advisory heuristics, but true Value of Information requires:

- decision/loss model;
- uncertain parameters;
- priors;
- likelihood/test performance;
- structural response sensitivity;
- investigation cost/invasiveness;
- decision impact.

Target chain:

```text
uncertain parameters
→ structural sensitivity
→ decision sensitivity
→ candidate investigations
→ expected information gain / VoI
→ minimum useful investigation plan
→ observations/tests
→ posterior update
→ reassessment
```

This supports three legitimate project routes within one system:

1. diffuse investigations;
2. essential high-information investigations;
3. comparison/sensitivity route when new testing is unavailable.

The third route remains a comparative/modeling strategy, not a claim that simulated values are measured facts.

---

## 21. Multi-mode assessment manager

CEW-EX should expose five clearly separated assessment modes:

- `MODE-1 HISTORICAL_BASELINE`
- `MODE-2 CONSERVATIVE_EXISTING`
- `MODE-3 PROBABILISTIC_DEGRADATION`
- `MODE-4 ESSENTIAL_TESTS_UPDATED`
- `MODE-5 SURVEYED_EXISTING`

All modes share canonical entity identity/topology while applying different evidence/scenario overlays.

No scenario automatically upgrades the regulatory knowledge level.

---

## 22. Solver Handoff and round trip

Solver files are projections, never canonical authority.

Every solver adapter must preserve round-trip entity identity:

```text
CEW_ID
IFC_GUID
EDILUS_ID
OPENSEES_ID
CAD_LABEL
SOURCE_LABEL
```

A solver result must map back to the same CEW entity.

The engineer should be able to move:

**result → solver element → CEW entity → property → claim → evidence crop → original source**.

And in the opposite direction:

**source detail → claim → residual → investigation/decision → new property → scenario → solver → result**.

This bidirectionality is a defining product requirement.

---

## 23. Verification Workspace

The verification environment should organize results by:

- structural entity;
- load/combination;
- scenario;
- verification type;
- demand/capacity;
- governing result;
- epistemic dependencies;
- residuals that affect validity;
- evidence chain.

A failed check should expose not only the numerical result, but also which uncertain properties materially control it.

---

## 24. Intervention Workspace and generations

CEW continues beyond the as-is verification.

Workflow:

```text
AS-IS
→ deficiencies
→ intervention objectives
→ alternatives
   - repair
   - local strengthening
   - global strengthening
   - durability/protection
→ new model generation
→ analysis
→ comparison
→ design
→ execution
→ post-intervention as-built
→ monitoring
```

Stable entity identity is retained across generations.

Example lifecycle:

- `GEN-0` historical design;
- `GEN-1` reconstructed existing;
- `GEN-2` surveyed existing;
- `GEN-3` proposed intervention;
- `GEN-4` executed intervention;
- `GEN-5` inspection/monitoring;
- later reassessment generations.

---

## 25. Authority model

### Level A — deterministic machine authority

Machine may autonomously decide/check:

- hashes;
- schema validity;
- identity uniqueness;
- count consistency;
- missing references;
- deterministic topology invariants;
- reproducibility;
- provenance completeness.

### Level B — machine proposal / human review

For:

- ambiguous drawing interpretation;
- claim selection;
- source conflict adjudication;
- equivalence/compression interpretation;
- modeling-rule proposals;
- evidence binding where judgment is required.

### Level C — Human Engineering Authority

For:

- LC/FC;
- material characterization acceptance;
- geotechnical characterization;
- investigation-plan approval;
- solver-model authorization;
- engineering judgment on verification;
- intervention design approval.

---

## 26. Interoperability

CEW should interoperate with BIM/IFC ecosystems without making IFC the sole canonical authority.

IFC remains valuable for structured exchange, while CEW retains additional semantics such as:

- epistemic state;
- source claim;
- residual/issue;
- uncertainty/scenario;
- investigation need;
- supersession chain;
- model generation;
- evidence crop;
- human decision receipts.

CEW should also support BCF-like issue export/import where practical, extended by CEW-specific engineering semantics.

---

## 27. Bounded contexts

The product should be structured around stable domain boundaries rather than a sequence of UI pages.

Core bounded contexts:

- `PROJECT_CONTROL`
- `SOURCE_CDE`
- `EVIDENCE`
- `CANONICAL_MODEL`
- `ISSUE_RESIDUAL`
- `CONDITION`
- `ASSESSMENT`
- `INVESTIGATION`
- `SOLVER`
- `INTERVENTION`
- `ORCHESTRATION`

Each bounded context owns its entities and authority rules.

For example, `SOLVER` may create `SolverResult` but may not rewrite a `Claim`.

This boundary discipline is essential for product maintainability and future substitution of viewers, storage systems or solvers.

---

## 28. Product maturity levels

### L0 — Document Repository

Sources are stored and identifiable.

### L1 — Traceable Evidence

Claims, evidence snippets, provenance and conflicts are controlled.

### L2 — Canonical Reconstruction

Geometry, topology, semantics and key property binding are represented canonically.

### L3 — Interactive Engineering Twin

2D/3D entity-centric maps, residuals and source lineage are interrogable.

### L4 — Assessment Ready

Assessment inputs are sufficiently complete or governed by explicit admitted scenarios for the intended scope.

### L5 — Decision Ready

Sensitivity, uncertainty, investigations and decision impact are quantitatively connected; true Value of Information becomes possible.

### L6 — Lifecycle Twin

Intervention generations, executed condition, inspections, monitoring and reassessment remain connected over the asset life.

### N12 current maturity interpretation

N12 is already strong across **L1–L3**, with several L4 components emerging, but it must not be labelled fully L4 while calculation-model blockers remain open.

---

## 29. Recommended development order

The near-term development sequence should prioritize stakeholder usability over adding more isolated technical engines.

### R1 — Project Control Room

Expose everything already known in a project-level decision surface.

### R2 — Universal Issue / Residual Workspace

Turn blockers/residuals into resolvable engineering work objects with evidence context.

### R3 — Synchronized 2D / 3D Evidence Map

Synchronize original drawing, claim, entity and 3D model.

### R4 — Field / Investigation Pack

Transform residuals into structured field tasks and bring results back into claims.

### R5 — Solver Round Trip

Canonical model → solver projection → solver result → same CEW entities.

### R6 — Scenario / Sensitivity

Connect uncertainty and alternative assessment modes to response sensitivity.

### R7 — Intervention Generations

Manage proposed, executed and monitored post-intervention states.

---

## 30. Defining stakeholder journey

CEW reaches product maturity when the engineer can start from:

> **“This beam fails the verification.”**

and navigate backward through:

**result → solver → scenario → property → claim → evidence snippet → original drawing/source**

while also being able to navigate forward from:

**ambiguous detail on drawing → residual → impact → proposed action → investigation → new claim → new model generation → new verification**.

This bidirectional chain is the operational definition of Civil Engineering Workflow.

---

## 31. Product safety invariants

- Canonical evidence is immutable except through controlled supersession.
- Numerical precision never upgrades epistemic precision.
- Missing information remains visible and exportable.
- Geometry proximity never creates topology.
- Historical values remain historical unless a scenario rule explicitly uses them.
- Model-derived values remain `MOD`; posterior-updated values remain `POST`.
- Solver outputs do not rewrite source evidence.
- Scenario models do not automatically upgrade LC/FC.
- Local residuals do not block unrelated work.
- AI agents do not become Engineering Approvers.
- Every engineering decision that changes authoritative state must have traceable provenance and a receipt.
- A visually complete 3D model is not automatically calculation-ready.

---

## 32. Relationship to existing CEW artifacts

This full analysis should be read together with:

- `docs/ARCHITECTURE/CEW_PRODUCT_VISION_AND_EXISTING_WORKFLOW_v1.md`
- `docs/ARCHITECTURE/CEW_STAKEHOLDER_PRODUCT_BLUEPRINT_v2.md`
- `docs/RESEARCH/CEW_PRODUCT_BENCHMARK_AND_MATURITY_REVIEW_v1.md`
- `automation/CEW_PRODUCT_MODULE_CONTRACT_v1.json`
- `automation/CEW_CANONICAL_STRUCTURAL_MODEL_CONTRACT_v1.json`
- `automation/CEW_EXISTING_ASSESSMENT_CONTRACT_v1.json`
- `automation/CEW_EXPOSURE_CONDITION_CONTRACT_v1.json`
- `automation/CEW_DEGRADATION_MODEL_REGISTRY_v1.json`

The documents provide human-readable product reasoning; the contracts provide machine-readable implementation boundaries.

---

## 33. Immediate implementation boundary

The next major product slices should be developed together:

1. **Project Control Room v0**
2. **Universal Residual Workspace v0**

These two surfaces should unify the evidence, canonical model, assessment, condition, investigation and solver-readiness infrastructure already implemented in the N12 reference project.

They are the point at which CEW begins to function as an integrated engineering product rather than a collection of validated backend capabilities.
