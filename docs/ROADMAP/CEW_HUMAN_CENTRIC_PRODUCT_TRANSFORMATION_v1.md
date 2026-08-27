# CEW Human-Centred Product Transformation Roadmap v1

Status: IMPLEMENTATION PLAN
Date: 2026-08-27
Baseline: CEW canonical branch at `164f8ad924536d2a386c1095d15f8115d218a943`
Reference implementation: N12

## 1. Transformation objective

Transform CEW from a strong engineering kernel with repository-oriented operational surfaces into a coherent professional product for structural assessment of existing structures.

The transformation preserves all validated N12 engineering data and CEW provenance/authority invariants. It changes the product shell, runtime state model and integration sequence; it does not reopen M0-G or promote unresolved engineering data.

## 2. Product North Star

A responsible engineer can enter CEW with a heterogeneous dossier and progress through:

`PROJECT -> SOURCES -> EVIDENCE -> SURVEY/HISTORY -> RECONSTRUCTION -> STRUCTURAL MODEL -> PROPERTIES -> CONDITION -> INVESTIGATION -> AS-IS GENERATION -> SCENARIOS -> SOLVER/FEM -> VERIFICATION -> INTERVENTION -> AS-BUILT/MONITORING`

without needing to know repository paths, CSV names, Git branches or internal queue mechanics.

At every step:

- current engineering state is understandable;
- evidence and model context are available at the point of decision;
- missing information is explicit;
- next useful action is visible;
- machine/human authority is explicit;
- every result is traceable backward to evidence;
- every unresolved fact is traceable forward to its impact.

## 3. Existing CEW assets to retain

| Capability | Existing value | Transformation treatment |
|---|---|---|
| Source/version/evidence provenance | strong | retain as core service |
| Claim/epistemic states | strong | expose in user-facing evidence/model passports |
| N12 canonical geometry/topology | strong | preserve; expose via synchronized workspaces |
| Structural model builder | operational engine | integrate into phase P5-P10 user journey |
| Structural viewer | early operational | turn into element-centric engineering workspace |
| Residual/issue model | strong semantics | make phase/domain/impact aware |
| F7 human review | governed submit path | replace technical review page with source-context decision workspace |
| Existing assessment engine | early L4 engine | integrate after Rule Pack + AS-IS generation |
| Investigation planner | advisory | convert to executable field/test round trip |
| Degradation/exposure engines | early/safety-gated | integrate into P8 condition workflow |
| Audit persistence | production infrastructure | retain as audit service, not engineering authority |
| N12 orchestration/agent contracts | strong backend | project into human-readable work packages |

## 4. Wave A — Product spine

### A0 — State reconciliation gate

Problem:
Current CEW state declarations lag actual merged runtime capabilities, and N12 engineering state is a separate state system.

Deliver:
- `CEW_PRODUCT_STATE_RECONCILIATION` validator;
- explicit mapping between CEW product state and N12 engineering state;
- runtime capability inventory derived from code/contracts;
- no manual reconstruction from conversation history.

Acceptance:
- stale deployment/backend declarations fail CI;
- product state cannot claim a module maturity dimension that has no corresponding evidence/gate;
- N12 engineering state remains authoritative for N12 engineering facts.

### A1 — Project lifecycle domain model

Implement primitives:
- ProjectPhase;
- PhaseGate;
- PhaseDeliverable;
- EngineeringDecision;
- InformationRequirement;
- EngineeringRulePack;
- WorkPackage.

Acceptance:
- current N12 work maps to one or more P0-P16 phases;
- local residuals affect only declared downstream gates;
- phase status can be generated from project graph rather than hard-coded HTML.

### A2 — Project Home v2

Replace current technical Control Room as primary landing surface.

Show:
- project objective;
- active phase(s);
- current approved generation;
- current authorized scenario;
- domain readiness;
- blockers/residuals;
- pending human decisions;
- active investigations;
- solver eligibility;
- next best actions;
- completed/current deliverables.

Acceptance scenario `HF-HOME-01`:
A structural engineer unfamiliar with CEW internal IDs can state within two minutes:
1. where the project is;
2. why calculation is or is not allowed;
3. what three actions are most useful next.

### A3 — Terminology/identity layer

Primary labels use engineering language; internal IDs are secondary.

Example:
`Reinforcement — beam G01/R06` is primary; `ERW-N12-001 / M1E-B06-R08` appears under Technical details.

## 5. Wave B — Source-to-model user journey

### B1 — Source Hub

Implement immutable intake UI and source inventory.

Capabilities:
- upload/import;
- version/hash;
- source type/date/origin/discipline;
- source quality;
- source role;
- source supersession;
- page/sheet browsing;
- missing-source checklist.

### B2 — Evidence Workspace v1

Replace the current F7 form-centric interaction.

Mandatory three-panel layout:
- source/evidence MICRO-MESO-MACRO;
- linked model/entity/claim context;
- human decision and patch preview.

Acceptance `HF-EVIDENCE-01`:
The engineer resolves a real ambiguous drawing reading without navigating to another app/file and without entering parser-specific syntax.

### B3 — Reconstruction Workspace

Synchronize:
- original drawing;
- 2D structural network;
- entity/coordinate table;
- 3D preview;
- residual map.

Selection must be identity-synchronized.

Acceptance `HF-GEOMETRY-01`:
The user can inspect the evidence supporting a node/member/connectivity decision and identify whether it is documented, measured, inferred or unresolved.

### B4 — Structural Model Workspace

Element-centric engineering passport and maps:
- geometry;
- evidence;
- completion;
- sections;
- reinforcement;
- loads;
- condition;
- scenarios;
- FEM results;
- verification;
- interventions.

### B5 — Property Workspaces

Create integrated workflows for:
- sections;
- reinforcement;
- materials/knowledge;
- loads/masses;
- boundary conditions;
- foundations;
- geotechnics.

Each property must carry provenance, epistemic state, scope, scenario and authority.

## 6. Wave C — Assessment readiness

### C1 — Engineering Rule Pack

Implement project-versioned rule packs.

Initial CEW-EX Italian profile:
- NTC 2018 Chapter 8 as principal existing-structure assessment spine;
- applicable Circolare instructions;
- configured Eurocode/reference rules where project-authorized;
- explicit solver implementation mapping.

No normative rule may exist only as an undocumented constant in a solver script.

### C2 — Information Requirements

Implement IDS/IDM-inspired requirements before data production.

For each calculation/decision requirement expose:
- purpose;
- target domain/entity;
- required property;
- allowed evidence state;
- required authority;
- validation;
- downstream gate affected.

### C3 — Executable Investigation Workspace

Convert advisory planner into field work packages.

Flow:
`BLOCKER -> REQUIRED FACT -> METHOD -> LOCATION -> FIELD PACK -> OBSERVATION/TEST -> EVIDENCE -> CLAIM -> REASSESSMENT`

Acceptance `HF-INVESTIGATION-01`:
An engineer creates a field task from a calculation blocker and later binds the returned result without editing repository data manually.

### C4 — Knowledge / LC-FC decision pack

Present historical analysis, survey completeness, materials/testing and uncertainty evidence needed for the responsible engineer's project-specific knowledge decision.

The system prepares; the responsible engineer authorizes.

### C5 — AS-IS generation and scenarios

Formalize:
- AS-IS approved generation;
- scenario overlays;
- scenario delta/causality;
- approval receipts.

## 7. Wave D — Current solver/FEM round trip

### D0 — Retire stale prototype status

Mark `model/open_source_fem/M0-OS-0002` as:
`HISTORICAL_PROTOTYPE / NOT_CURRENT_CANONICAL_ADAPTER / NOT_FOR_VERIFICATION`.

Do not delete it; preserve for history/regression.

### D1 — Solver-neutral projection contract

Input:
- approved canonical generation;
- authorized scenario;
- EngineeringRulePack;
- InformationRequirement compliance result.

Output:
- normalized nodes/members/supports;
- sections/materials/reinforcement representation;
- loads/masses/combinations;
- constraints/releases/offsets;
- foundation/geotechnical idealization;
- units;
- CEW entity IDs;
- unsupported/residual scopes;
- projection hash.

### D2 — Current-canonical OpenSees adapter

Rebuild OpenSees projection from the current M0-G/M1 calculation handoff, not from the 135-node prototype.

Minimum adapter QA:
- node count identity;
- member count identity;
- connectivity graph equivalence;
- rigid-offset preservation;
- section/property coverage;
- load/mass completeness;
- boundary-condition review;
- unit validation;
- unsupported-feature report.

### D3 — EdiLus-EE adapter/handoff

Implement the strongest technically available integration without pretending unsupported automation.

Maintain:
- CEW -> EdiLus entity mapping;
- assumptions/manual entries checklist where APIs/import are unavailable;
- input receipt;
- returned result mapping.

### D4 — Analysis execution and immutable results

Capture:
- solver/version;
- input hash;
- analysis method;
- cases/combinations;
- warnings;
- convergence;
- result bundle hash;
- run receipt.

### D5 — Result import and engineering twin maps

Map results back to CEW IDs.

Never update evidence claims from solver results.

Acceptance `HF-RESULT-01`:
Selecting a result/failure supports:
`result -> run -> projection -> scenario -> property -> claim -> evidence -> source`.

### D6 — Independent benchmark/cross-solver

Configure a limited set of benchmark cases to compare the primary solver projection against an independent solver when useful.

Differences remain explicit comparison results.

## 8. Wave E — Verification and lifecycle

### E1 — Verification Workspace

Per entity/scope show:
- demand;
- capacity;
- verification/failure mode;
- governing case/combination;
- code/rule;
- scenario;
- uncertainty/sensitivity;
- evidence gaps affecting confidence.

### E2 — Sensitivity / uncertainty

Expose which uncertain inputs drive decision-relevant outputs.

Feed Investigation Planner / Value of Information.

### E3 — Intervention Generations

AS-IS remains immutable.

Each option creates:
- intervention objects;
- proposed generation;
- new solver projections/results;
- comparison against baseline;
- approval history.

### E4 — Executed / As-built generation

Capture what was actually executed and deviations from design.

### E5 — Monitoring and reassessment

Link observations/sensors/inspections to entities and trigger explicit reassessment conditions.

### E6 — Technical Dossier Builder

Generate a human-reviewable project dossier from governed records:
- source inventory;
- historical-critical analysis;
- survey;
- materials/testing;
- knowledge decisions;
- model assumptions;
- solver receipts;
- verifications;
- residuals;
- interventions;
- approvals;
- full lineage.

Generated text is a draft until human engineering approval.

## 9. Standing expert board for product acceptance

Every Wave review must include the following competency perspectives:

- Responsible Structural Engineer;
- Existing-Structure Assessment Specialist;
- RC/Material Specialist;
- Seismic Specialist;
- Geotechnical Engineer;
- Survey/Inspection/Test Specialist;
- Durability/Degradation Specialist;
- FEM/Computational Mechanics Specialist;
- BIM/openBIM Information Manager;
- Human-Factors Specialist;
- Independent Checker;
- Field Technician;
- Software/Provenance Assurance;
- Asset-owner decision perspective.

This is a review matrix. Human professional roles retain authority; software agents may only support the work.

## 10. Release gates for every user-facing module

A module is releasable only when all applicable gates pass:

1. DATA GATE
2. ENGINEERING GATE
3. HUMAN AUTHORITY GATE where required
4. INTEGRATION GATE
5. HUMAN-FACTORS GATE
6. SECURITY/PRIVACY GATE
7. PRODUCTION SMOKE

A passing deterministic CI test alone does not establish user readiness.

## 11. Immediate first implementation tranche

After this architecture is accepted, implement **Wave A only** before further UI polishing:

1. state reconciliation validator;
2. phase/deliverable/decision/information-requirement model;
3. lifecycle-based Project Home;
4. terminology layer;
5. human-factors acceptance fixture for Project Home.

Do not add new decorative dashboard components that are not backed by these primitives.

Then proceed to B2 Evidence Workspace because it is the current practical blocker to usable R08/R09 human review.
