# ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1

Status: CANONICAL  
Execution state: AUTHORIZED_FOR_PREPARATION  
Current slice: ETW-A0  
ETW-A0 promotion authorized: false  
Promotion blocker: CEW_PROMOTED_BASELINE

## 1. Objective

Extend eTwin as the multi-project, multi-discipline platform shell above CEW while preserving CEW as the specialist Structures / Existing Structures authority. Delivery remains evidence-first, human-centred, runtime-verifiable and promotion-gated.

The first platform journey contains:

- `N12 / Structures` — `ACTIVE + CEW_BOUND`;
- `N12 / Architecture` — architectural sources visible, discipline domain not yet released;
- `TEST_PROJECT / Structures` — `TEST_ONLY`, with zero N12 engineering data.

## 2. Product boundary

```text
eTwin PLATFORM
├── Portfolio
├── Project
│   ├── ProjectDisciplineScope
│   │   ├── Structures -> CEW -> P0-P16
│   │   └── Architecture -> Architecture module
│   └── Cross-discipline relations
└── Shared project/scope context and isolation
```

eTwin owns Project, Discipline, ProjectDisciplineScope, ScopeContext, project isolation, discipline isolation, portfolio/navigation and explicit cross-discipline coordination.

CEW remains authority for its specialist domain and owns/reuses its existing lifecycle and evidence primitives, including P0-P16, Source/SourceVersion, Page, DocumentMap, EvidenceRegionCandidate, EvidenceRegion, Claim, EngineeringDecision, PhaseGate, InformationRequirement, engineering-rule boundaries, epistemic states and CEW/GOV.UK usability metrics.

N12 is the first Project, not the eTwin data model.

## 3. Non-negotiable invariants

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
- Project and discipline safety failures are non-compensable usability failures.

## 4. CEW baseline governance

Two baseline concepts are mandatory.

### CEW_CONTRACT_BASELINE

An immutable SHA usable for mapping contracts, adapter work, PREP_ONLY implementation and tests. It may point to technically validated work that is not yet promoted.

### CEW_PROMOTED_BASELINE

An immutable SHA for which the applicable CEW automated gates, HVA, Production smoke, receipt and promotion have completed.

ETW-A0 may be prepared against `CEW_CONTRACT_BASELINE`, but it cannot become COMPLETE or release ETW-A1 until a compatible `CEW_PROMOTED_BASELINE` has been frozen and reconciled.

## 5. Platform primitives

### Project

- `project_id` — required hard boundary;
- project metadata and lifecycle state are product/platform state, not engineering truth.

### Discipline

Initial values:

- `STRUCTURES`
- `ARCHITECTURE`

Future disciplines are not modelled prematurely.

### ProjectDisciplineScope

Represents whether a discipline exists and is usable inside a Project.

Initial examples:

- `N12 / Structures = ACTIVE + CEW_BOUND`
- `N12 / Architecture = NOT_YET_RELEASED`, sources present, domain entities unavailable
- `TEST_PROJECT / Structures = TEST_ONLY`

### ScopeContext

Runtime context carrying at minimum project and discipline. It must be enforced in route, API, query, cache, async operations, deep links and browser history. Missing, unknown or unauthorized scope fails closed; there is no implicit fallback to N12.

### ProjectScopedReference

General platform reference:

- `project_id` REQUIRED
- `owner_discipline_id` OPTIONAL
- `discipline_scope` 0..N
- `scope_kind = PROJECT_WIDE | DISCIPLINE_SET | UNCLASSIFIED`
- `target_type`
- `target_id`

### ProjectSourceBinding

Specialized source-root binding only. Allowed binding targets are `Source` and exact `SourceVersion`; never `latest`.

Derived Page / DocumentMap / EvidenceRegion scope must be resolvable from immutable source lineage. Direct references to derived objects use ProjectScopedReference, but validators must prove consistency with the ancestor SourceVersion project scope.

## 6. Architecture source state before domain release

The CEW source registry already contains four primary architectural sources: `TAV-01`, `TAV-02`, `TAV-03`, `TAV-04`.

Before ETW-A3 the state is:

- `scope_exists = true`
- `domain_contract = NOT_YET_RELEASED`
- `workspace_state = NOT_YET_RELEASED`
- `source_inventory_state = SOURCES_PRESENT_NOT_YET_ADMITTED_TO_ARCH_DOMAIN`
- `source_count = derived from CEW registry/adaptation layer`
- `ArchitecturalEntity count = 0`
- `architectural property count = 0`
- `synthetic_engineering_data = false`

Document available is not the same as interpreted discipline domain.

## 7. A0 inventory before A1 binding

ETW-A0 must not create ProjectSourceBinding. It introduces a read-only `CEWSourceInventoryAdapter` over `CEW_EXISTING_SOURCE_REGISTRY`, producing a `ScopeInventoryProjection` reconciled using Source ID + exact SourceVersion/hash.

ETW-A1 later materializes explicit idempotent bindings and must prove inventory parity before/after.

## 8. Canonical identity TAV-02

`TAV-02` architectural and `TAV-02S` structural are distinct sources. All ETW-A3 work must resolve TAV-02 by Source ID + exact SourceVersion/hash, never by approximate display label.

`DOC_PRIMARY_IMMUTABLE` proves document identity/integrity/classification only. It does not automatically promote extracted ArchitecturalEntity, PropertyAssertion or CrossDisciplineRelation to DOC.

## 9. ArchitectureDisciplineContract

Before any ArchitecturalEntity is admitted, ETW-A3 must release a domain contract covering:

- entity types;
- property definitions;
- epistemic vocabulary;
- source classes;
- ownership;
- minimum evidence;
- allowed relations;
- forbidden relations;
- validation rules.

Architecture is an autonomous domain, not a lower-precision copy of Structures.

## 10. Cross-discipline identity

`SpatialReference` is neutral and never replaces discipline identity.

`StructuralEntity` and `ArchitecturalEntity` remain autonomous DisciplineEntity instances.

`CrossDisciplineRelation` is explicit, typed, evidence-backed, append-only and reviewed. Same position, shape or label does not imply same identity.

## 11. Assertion-first property model

`PropertyDefinition` may have multiple concurrent `PropertyAssertion` values with source, discipline ownership and epistemic state. `ResolvedPropertyProjection` is a qualified operational projection; it never deletes or rewrites assertion genealogy or conflict.

## 12. Lifecycle and human authority

Structures continues to use CEW P0-P16 as a dependency graph. N12 engineering gates remain Structures gates. CrossDisciplineGate may depend on discipline gates but cannot replace them.

EngineeringDecision Level C remains human-authority-bound:

`PropertyAssertion -> Evidence -> EngineeringDecision -> HUMAN_AUTHORITY_REQUIRED -> human decision -> append-only receipt -> resolver/verifier -> affected gate`

## 13. Read-model and authority conflict

Snapshot and read-model objects are `ReadModelProjection`. If a projection diverges from authority, the state is `AUTHORITY_CONFLICT`; the platform does not select a winner automatically.

## 14. Human-centred metrics

eTwin reuses CEW/GOV.UK effectiveness, efficiency, satisfaction/confidence and safety metrics. It adds only these non-compensable platform safety metrics:

- `cross_project_leakage`
- `cross_discipline_leakage`
- `cross_discipline_false_equivalence`
- `discipline_owner_misidentification`
- `spatial_relation_misread_as_identity`

Any critical safety violation is FAIL regardless of task speed or apparent completion.

## 15. Development model

Every slice follows:

`CANONICAL BASELINE -> SMALL VERTICAL SLICE -> DEDICATED BRANCH -> PR -> AUTOMATED GATES -> HVA -> PRODUCTION SMOKE -> RECEIPT -> PROMOTION`

Parallel preparation is allowed. Promotion is serialized. Architecture-only completion is forbidden.

---

# ETW-A0 — Platform Identity Boundary

Initial state: `PREP_ONLY`.

## Goal

Introduce only:

- Project
- Discipline
- ProjectDisciplineScope
- ScopeContext
- CEWSourceInventoryAdapter
- ScopeInventoryProjection

No ProjectSourceBinding. No ArchitecturalEntity.

## Runtime acceptance

- `N12 / Structures = ACTIVE + CEW_BOUND`
- `N12 / Architecture = NOT_YET_RELEASED`, 4 architectural sources visible, 0 ArchitecturalEntity, 0 architectural properties
- `TEST_PROJECT / Structures = TEST_ONLY`, zero N12 engineering data

## Non-negotiable tests

1. N12 -> TEST_PROJECT: zero leakage.
2. Structures -> Architecture: zero discipline/domain leakage.
3. Deep-link/reload/back-forward restores exact ScopeContext.
4. Cache/query/async responses cannot leak old scope.
5. Document available != interpreted domain.
6. Missing/unknown/unauthorized project or scope fails closed; no fallback to N12.
7. Architectural source count is derived, not hard-coded.

## Gates

DATA_GATE, INTEGRATION_GATE, SECURITY_GATE, HUMAN_FACTORS_GATE, HVA_GATE, PRODUCTION_SMOKE, QA_GATE.

## Promotion

Preparation may use CEW_CONTRACT_BASELINE. Completion requires a compatible CEW_PROMOTED_BASELINE.

---

# ETW-A1 — Project-scoped Source / Evidence

Depends on approved ETW-A0 platform boundary.

## Goal

Materialize ProjectScopedReference and ProjectSourceBinding in the adaptation layer without modifying SourceVersion identity or historical CEW artifacts.

## Rules

- ProjectSourceBinding binds only Source or exact SourceVersion.
- Never bind by `latest`.
- Page, DocumentMap and EvidenceRegion project scope must resolve through SourceVersion lineage.
- Shared SourceVersion must not transfer permissions, claims or decisions across projects.

## Acceptance

- idempotent materialization;
- inventory parity before/after;
- no SourceVersion duplication;
- no Architecture domain admission;
- no F1/F2 rewrite;
- version mismatch fail-closed;
- AUTHORITY_CONFLICT has no automatic winner.

Scope model combinations may be tested only with non-persisted `TEST_ONLY` fixtures; no N12 common/unclassified source is invented.

---

# ETW-A2 — Multi-project Portfolio

## Goal

Deliver the first complete human-facing platform surface.

Portfolio exposes:

- N12 / Structures
- N12 / Architecture — sources present, workspace/domain not released
- TEST_PROJECT / Structures — TEST_ONLY

## Acceptance

Users can select Project and discipline, understand ACTIVE / NOT_YET_RELEASED / TEST_ONLY, restore/deep-link exact context, return to portfolio and avoid false success or leakage.

Use CEW/GOV.UK task benchmarking, HVA and Production smoke before promotion.

---

# ETW-A3 — Cross-discipline Identity

## Goal

Release Architecture through one real, evidence-backed vertical only.

## Initial source

TAV-02 exact Source ID + SourceVersion/hash, explicitly distinct from TAV-02S.

## Flow

`ArchitectureDisciplineContract -> TAV-02 exact SourceVersion -> EvidenceRegion -> ArchitecturalEntityCandidate -> human review -> ArchitecturalEntity -> SpatialReference -> CrossDisciplineRelation -> StructuralEntity`

Only one representative candidate is admitted in v1; no global ingestion.

## Required cases

1. documented relation;
2. same area but distinct identity;
3. present in one discipline and ND in the other.

Review admission does not upgrade epistemic state.

---

# ETW-A4 — Property Assertions and Compare

## Goal

Compare governed entities through assertion genealogy rather than one active value.

UI must expose PropertyDefinition, assertions, value/unit, source/SourceVersion, epistemic state, discipline owner, relation and ResolvedPropertyProjection.

## Acceptance

Users distinguish assertion, conflict, operational projection, DOC/MIS/RIF, ND and provenance; spatial relation cannot be misunderstood as identity and resolved projection cannot be presented as a single documentary truth.

---

# ETW-A5 — Decision Cockpit

## Goal

Prove one real Level-C decision vertical, not the whole P0-P16 lifecycle.

Flow:

`conflicting PropertyAssertions -> Evidence -> Decision Card -> EngineeringDecision Level C -> HUMAN_AUTHORITY_REQUIRED -> human decision -> append-only receipt -> resolver/verifier -> affected gate`

## Receipt

Must capture project, scope, author, motivation, evidence viewed, alternatives, input state, decision, output, affected gate and timestamp.

Agents, UI and workflow must be unable to auto-complete Level C.

---

# ETW-A6 — Multidisciplinary Viewer

## Goal

Visualize only already-governed knowledge.

Consumes DisciplineEntity, SpatialReference, CrossDisciplineRelation, PropertyAssertion, Evidence and Decision Trail. Viewer creates no identity or engineering truth.

Visual state must not rely on colour alone; use text, symbol, legend and source context.

A6 ends only with viewer-specific automated gates, HVA, Production smoke and receipt. It does not certify the platform.

---

# ETW-Z0 — Platform Production Acceptance

Depends on ETW-A6.

## Goal

Validate the complete platform on a frozen candidate. Z0 contains no functional fixes. Any failure reopens the owning slice.

## Frozen manifest

Record platform SHA, CEW promoted baseline SHA, contracts, schemas, expected authorities and gate versions.

## P0-P16 replay policy

Z0 must not artificially advance N12.

Use `ACTUAL_N12_RECEIPT` only for professional decisions that actually occurred. For lifecycle transitions not genuinely executed on N12, use non-persisted `TEST_ONLY_LIFECYCLE_FIXTURE` solely to verify lifecycle behaviour and fail-closed boundaries.

A fixture never becomes canonical engineering history and never represents a professional decision that did not occur.

## Z0 verifies

- N12 / Structures end-to-end;
- representative P0-P16 behaviour;
- actual human receipts where available;
- TEST_ONLY fixtures elsewhere;
- TEST_PROJECT isolation;
- Architecture boundary;
- bidirectional provenance;
- immutable SourceVersion;
- zero project leakage;
- zero discipline leakage;
- zero false equivalence;
- Level-C authority boundary;
- append-only audit;
- HVA receipts;
- Production smoke receipts;
- gate reconciliation.

## Final human gate

`approve-production-acceptance` is required before eTwin Platform v1 promotion.

---

# Execution sequence

```text
CEW B1 HVA / promotion
        |
        +-------------------- ETW-A0 PREP_ONLY
        |                           |
        v                           |
CEW_PROMOTED_BASELINE <-------------+
        |
        v
ETW-A0 COMPLETE
        |
approve-platform-boundary
        |
ETW-A1
        |
ETW-A2
        |
ETW-A3
        |
approve-crossdiscipline-contract
        |
ETW-A4
        |
ETW-A5
        |
ETW-A6
        |
ETW-Z0
        |
approve-production-acceptance
        |
eTwin Platform v1 PRODUCTION
```

## Superseded planning genealogy

Earlier macro-plans `semantic-contract`, `design-workbench`, `shell-read-model`, `structural-architectural-integration`, `validation-cockpit`, and `viewer-multilevel` remain historical `DROPPED / SUPERSEDED` records. They are not execution authority.
