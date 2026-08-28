# ETWIN Platform Extension over CEW v2

Status: REQUIRED PLATFORM PROGRAM CONTRACT  
Supersedes for future eTwin promotion: `ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1.md`  
Current execution dependency: ETW-A0 remains prepared on the v1/CEW contract baseline and must be revalidated before promotion  
Governing agency model: `docs/GOVERNANCE/AI_NATIVE_PRODUCT_AGENCY_OPERATING_MODEL_v1.md`  
Shared human model: `docs/PROGRAM/CEW_HUMAN_CENTRED_GOVUK_MODEL_v2.md`

## 1. Objective

Extend eTwin as the multi-project, multi-discipline platform shell above specialist discipline products while preserving discipline authority.

For the first release:

- `N12 / STRUCTURES` is active and bound to CEW;
- `N12 / ARCHITECTURE` may expose governed source inventory before the Architecture domain is released;
- `TEST_PROJECT / STRUCTURES` is test-only and contains zero N12 engineering data.

The platform must be understandable and safe to a professional user without requiring knowledge of repository paths, internal IDs, gate codes or agent topology.

## 2. Product boundary

```text
eTwin PLATFORM
├── Portfolio
├── Project
│   ├── ProjectDisciplineScope
│   │   ├── Structures -> CEW -> P0-P16
│   │   └── Architecture -> autonomous Architecture discipline contract
│   └── explicit CrossDisciplineRelation
├── ScopeContext / isolation
└── shared project navigation, governance and human-system conventions
```

eTwin owns:
- Project;
- Discipline;
- ProjectDisciplineScope;
- ScopeContext;
- project/discipline isolation;
- portfolio/navigation;
- project-scoped references;
- explicit cross-discipline coordination;
- platform-level release and human-safety metrics.

CEW remains the Structures / Existing Structures specialist authority and retains its lifecycle, source/evidence/claim, engineering decision, epistemic and canonical-model semantics.

N12 is the first Project. It is not the eTwin data model.

## 3. Product-agency principles

Every eTwin slice is delivered as:

`NEED -> CAPABILITY -> REPRESENTATIVE JOURNEY -> SLICE -> IMMUTABLE CANDIDATE -> DETERMINISTIC GATES -> INDEPENDENT ASSURANCE -> HUMAN EVIDENCE -> REQUIRED RELEASE/SMOKE -> RECEIPT -> PROMOTION`

Preparation and verification may be parallel. Promotion is serialized.

Implementation speed does not change authority. A prepared or deployed platform feature is not promoted until its declared evidence exists.

## 4. Shared Human System

eTwin does not create an independent HVA philosophy. It consumes the shared CEW/GOV.UK v2 human model.

Human evidence is divided into:

1. formative research;
2. evaluative usability/Human Factors;
3. release HVA on an immutable candidate.

### Participant rule

The participant performs a realistic project/discipline task. They do not operate internal release governance.

### Reviewer rule

A separate reviewer surface/role interprets task evidence, safety failures, usability residuals and mental-model findings and makes the HVA/release decision.

### Telemetry rule

Task timing/interactions/help/recovery are normally invisible to participants and are evidence rather than automatic PASS/FAIL thresholds.

### Non-compensable platform failures

The following always block where applicable:
- cross-project leakage;
- cross-discipline leakage;
- wrong project/scope restoration;
- discipline-owner misidentification;
- cross-discipline false equivalence;
- spatial relation misread as identity;
- wrong Source/SourceVersion;
- canonical-write misconception;
- false success on an authority/safety-critical task.

## 5. Non-negotiable authority invariants

- UI state is never engineering authority.
- Agent output is never engineering authority by itself.
- AI/OCR/vector consensus never self-promotes engineering truth.
- Snapshot/read-model is never authority.
- Solver output never rewrites source evidence.
- Spatial coincidence does not create identity.
- Workflow/admission state does not upgrade epistemic state.
- Source DOC does not imply entity/property/relation DOC.
- Missing/ND information is never silently filled.
- Human EngineeringDecision Level C cannot be auto-completed.
- SourceVersion content identity remains immutable and project-independent.
- Production deployment does not imply canonical authority.
- Platform usability success cannot compensate for a project/discipline safety failure.

## 6. CEW baseline governance

Two baseline concepts remain mandatory.

### CEW_CONTRACT_BASELINE

Immutable SHA admitted for mapping contracts, adapter work, PREP_ONLY implementation and deterministic tests. It may refer to technically validated work that is not promoted.

### CEW_PROMOTED_BASELINE

Immutable SHA for which the applicable CEW deterministic gates, v2 human acceptance, required Production smoke, receipt and product promotion have completed.

ETW-A0 may remain prepared against a CEW_CONTRACT_BASELINE but cannot become COMPLETE or release ETW-A1 until a compatible CEW_PROMOTED_BASELINE is frozen and A0 is revalidated against the current governance/human model.

## 7. Platform primitives

### Project

`project_id` is a required hard boundary. Project metadata/lifecycle state is platform/product state, not engineering truth.

### Discipline

Initial declared disciplines:
- `STRUCTURES`
- `ARCHITECTURE`

Future disciplines are added only through an explicit discipline contract.

### ProjectDisciplineScope

Represents whether a discipline exists and is usable inside a Project.

Initial states:
- `N12 / STRUCTURES = ACTIVE + CEW_BOUND`
- `N12 / ARCHITECTURE = NOT_YET_RELEASED`
- `TEST_PROJECT / STRUCTURES = TEST_ONLY`

### ScopeContext

Carries at minimum Project and Discipline through:
- routes;
- APIs;
- queries;
- cache;
- async operations;
- deep links;
- browser history;
- background tasks.

Missing, stale, unknown or unauthorized scope fails closed. There is no implicit fallback to N12.

### ProjectScopedReference

General platform reference with:
- `project_id` required;
- optional owner discipline;
- explicit discipline scope;
- scope kind;
- target type/id.

### ProjectSourceBinding

Specialized source-root binding only. Targets Source or exact SourceVersion, never `latest`.

Derived Page/DocumentMap/EvidenceRegion project scope must be resolvable through immutable SourceVersion lineage.

## 8. Architecture before domain release

Governed architectural sources may be visible as source inventory before the Architecture domain is released.

Before Architecture admission:
- scope may exist;
- source inventory may exist;
- domain contract is `NOT_YET_RELEASED`;
- workspace is `NOT_YET_RELEASED`;
- `ArchitecturalEntity count = 0`;
- architectural property count = 0;
- no synthetic engineering data is invented.

**Document available is not interpreted discipline truth.**

## 9. Cross-discipline model

`SpatialReference` is neutral and never replaces discipline identity.

`StructuralEntity` and `ArchitecturalEntity` remain autonomous.

`CrossDisciplineRelation` is explicit, typed, evidence-backed, reviewable and append-only/supersedable. Same position, geometry, shape or label does not imply same identity.

Before any ArchitecturalEntity is admitted, `ArchitectureDisciplineContract` must define:
- entity types;
- properties;
- epistemic vocabulary;
- source classes;
- ownership;
- minimum evidence;
- relations;
- forbidden equivalences;
- validation rules.

## 10. Assertion-first property model

A PropertyDefinition may have multiple concurrent PropertyAssertions, each with value/unit, source, discipline owner and epistemic state.

ResolvedPropertyProjection is an operational projection; it does not delete assertion genealogy, conflict or provenance.

## 11. Read models

Snapshots/read models are `ReadModelProjection` objects.

If a projection diverges from authority, state becomes `AUTHORITY_CONFLICT`. The platform does not silently select a winner.

## 12. Human/professional authority

CEW Structures gates remain Structures gates. CrossDisciplineGate may depend on them but does not replace them.

Level-C flow remains:

`Assertion / Evidence -> EngineeringDecision -> HUMAN_AUTHORITY_REQUIRED -> human professional decision -> append-only receipt -> resolver/verifier -> affected gate`

Human release HVA and human engineering authority are different roles and receipts.

## 13. Platform capability sequence

### ETW-A0 — Platform Identity Boundary

Capability: establish safe, comprehensible Project/Discipline context.

Introduces only:
- Project;
- Discipline;
- ProjectDisciplineScope;
- ScopeContext;
- read-only CEWSourceInventoryAdapter;
- ScopeInventoryProjection.

Forbidden in A0:
- ProjectSourceBinding;
- ArchitecturalEntity;
- CrossDisciplineRelation;
- SourceVersion or CEW engineering mutation.

A0 promotion requires:
- compatible CEW_PROMOTED_BASELINE;
- deterministic/security/authority gates;
- v2 human evaluation of Project/Discipline comprehension and context behavior;
- required Production smoke;
- explicit `APPROVE_PLATFORM_BOUNDARY` human gate;
- one revision-bound receipt set.

### ETW-A1 — Project-scoped Source / Evidence

Capability: explicitly scope governed sources/evidence to Projects without rewriting CEW identity.

Rules:
- bind only Source/exact SourceVersion;
- no `latest` binding;
- derived scope resolves through lineage;
- shared SourceVersion does not transfer permissions/claims/decisions;
- idempotent materialization;
- no F1/F2 rewrite;
- mismatch fails closed.

### ETW-A2 — Portfolio

Capability: understand and switch Project/Discipline context safely.

Representative journey includes:
- enter N12/Structures;
- identify Architecture as not yet released despite source presence;
- switch to TEST_PROJECT/Structures;
- deep-link/reload/back-forward exact scope;
- return to portfolio.

Human evaluation tests comprehension, false success and leakage without showing internal gate machinery to the participant.

### ETW-A3 — Cross-discipline Identity

Capability: admit one real evidence-backed Architecture vertical and relate it explicitly to Structures without false equivalence.

Initial source: exact TAV-02 architectural Source/SourceVersion, distinct from TAV-02S structural.

Flow:

`ArchitectureDisciplineContract -> exact source evidence -> ArchitecturalEntityCandidate -> human review -> ArchitecturalEntity -> SpatialReference -> CrossDisciplineRelation -> StructuralEntity`

Required human gate: `APPROVE_CROSSDISCIPLINE_CONTRACT`.

### ETW-A4 — Property Assertions / Compare

Capability: compare discipline assertions without collapsing genealogy/conflict into one alleged truth.

Human evaluation verifies distinction between assertion, conflict, operational projection, epistemic state and relation/identity.

### ETW-A5 — Decision Cockpit

Capability: prove one real Level-C professional decision vertical.

Agents/UI/workflow cannot auto-complete the human professional decision.

### ETW-A6 — Multidisciplinary Viewer

Capability: visualize already-governed multidisciplinary knowledge.

Viewer state creates no identity, relation, assertion or engineering truth. Visual meaning cannot rely on colour alone.

### ETW-Z0 — Platform Production Acceptance

Frozen-candidate acceptance only. Z0 contains no functional fixes.

Verifies:
- complete admitted platform journeys;
- N12/TEST_PROJECT isolation;
- discipline isolation;
- cross-discipline authority;
- provenance;
- Level-C boundaries;
- append-only audit;
- human-evidence receipts;
- Production smoke receipts;
- gate reconciliation.

Final human gate: `APPROVE_PRODUCTION_ACCEPTANCE`.

## 14. Agentic delivery

Current orchestration authority: `docs/PROGRAM/ETW_AGENTIC_DEVELOPMENT_ORCHESTRATION_v2.md`.

Each slice has one promotion owner and independent support agents. Agents operate under least authority and do not self-promote professional/product truth.

## 15. Execution sequence

```text
CEW B1 Human Acceptance v2 / persistence reconciliation
        |
        +------------------------- ETW-A0 PREPARED
        |                              |
        v                              |
CEW_PROMOTED_BASELINE <----------------+
        |
        v
ETW-A0 revalidation under v2 governance
        |
APPROVE_PLATFORM_BOUNDARY
        |
ETW-A1 -> ETW-A2 -> ETW-A3
                         |
            APPROVE_CROSSDISCIPLINE_CONTRACT
                         |
              ETW-A4 -> ETW-A5 -> ETW-A6
                                      |
                                    ETW-Z0
                                      |
                         APPROVE_PRODUCTION_ACCEPTANCE
                                      |
                         eTwin Platform promoted release
```

## 16. Current transition rule

Existing ETW-A0 preparation on the prior contract remains valid **as preparation evidence only**. It is not discarded and must not be rewritten as if the v2 model existed before the finding.

Before A0 promotion:
- freeze the CEW promoted baseline;
- ingest the v2 governance/human contracts;
- revalidate A0 deterministic/security/authority invariants;
- run the v2 human Project/Scope evaluation;
- run required Production smoke;
- resolve `APPROVE_PLATFORM_BOUNDARY`.

Only then may ETW-A1 be released.
