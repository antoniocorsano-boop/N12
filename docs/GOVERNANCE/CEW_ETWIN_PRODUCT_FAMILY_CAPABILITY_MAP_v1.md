# CEW / eTwin Product Family Capability Map v1

Status: REQUIRED PRODUCT BOUNDARY CONTRACT  
Date: 2026-08-28  
Governing model: `AI_NATIVE_PRODUCT_AGENCY_OPERATING_MODEL_v1.md`

## 1. Purpose

This document prevents product-boundary drift between eTwin, CEW and the N12 reference project.

The rule is:

> **eTwin owns the multi-project / multi-discipline platform context. CEW owns the specialist Structures / Existing Structures workflow. N12 owns its engineering facts through its governed engineering authority. Shared governance and Human Factors are product-family services, not duplicated product domains.**

## 2. Layer model

```text
AI-NATIVE PRODUCT AGENCY GOVERNANCE
│
├── Shared Human System / QA / Security / Release Governance
│
└── eTwin Platform
    ├── Portfolio / Project / Discipline / ScopeContext
    ├── shared project navigation and isolation
    ├── explicit cross-discipline coordination
    │
    └── Project Discipline Products
        ├── Structures / Existing Structures -> CEW
        │   └── P0-P16 specialist engineering workflow
        └── Architecture -> autonomous future discipline product/contract

N12 = reference Project data/engineering authority, not product architecture
```

## 3. eTwin-owned capabilities

### Portfolio and project identity

- list/select Projects;
- Project identity and platform metadata;
- Project availability/state at platform level;
- safe switch between Projects.

### Discipline context

- Discipline registry;
- ProjectDisciplineScope;
- active/not-yet-released/test-only discipline availability;
- exact ScopeContext propagation.

### Isolation

- route/API/query/cache/async/deep-link/history project isolation;
- discipline isolation;
- fail-closed unknown/stale/unauthorized scope.

### Project-scoped references

- ProjectScopedReference;
- explicit Source/SourceVersion binding where admitted;
- lineage consistency checks across derived objects.

### Portfolio / multidisciplinary navigation

- project/discipline selection;
- cross-discipline navigation;
- coordinated view of admitted discipline states.

### Explicit cross-discipline coordination

- neutral SpatialReference;
- CrossDisciplineRelation;
- discipline ownership visibility;
- comparison without false equivalence.

### Platform release governance

- platform candidate identity;
- platform safety metrics;
- cross-project/cross-discipline acceptance;
- final eTwin production acceptance.

## 4. CEW-owned capabilities

CEW is the specialist Structures / Existing Structures product.

### P0-P16 lifecycle

CEW owns the specialist project lifecycle from project definition through source/evidence, reconstruction, model, properties, condition, investigation, scenarios, solver handoff, FEM, verification, intervention, as-built/monitoring and dossier.

### Source and document semantics inside Structures

CEW owns governed source/version/page/document-understanding semantics for its specialist workflow, including read-only/admitted use state and provenance.

eTwin may scope/reference these objects; it does not redefine them.

### Evidence / claim reconstruction

CEW owns:
- EvidenceRegionCandidate / EvidenceRegion boundaries;
- Observation/Claim semantics;
- evidence state and provenance;
- `DOC / MIS / RIF / INF / INC / ND` domain use where declared;
- conflict/residual behavior.

### Structural identity and canonical model

CEW owns:
- structural entities;
- topology/geometry semantics;
- property bindings;
- canonical AS-IS generations;
- solver-neutral structural projection boundary.

### Engineering decisions

CEW owns specialist engineering-decision semantics and gates. eTwin may host/navigation-coordinate them but does not turn platform approval into engineering approval.

### Solver / verification / intervention workflow

CEW owns specialist solver handoff, analysis result mapping, verification and intervention-generation workflow.

## 5. Architecture discipline boundary

Architecture is not a lower-precision copy of Structures and is not automatically created from architectural source presence.

Before release it requires an autonomous `ArchitectureDisciplineContract` defining:
- entity types;
- property semantics;
- epistemic vocabulary;
- ownership;
- evidence requirements;
- allowed/forbidden relations;
- validation and human authority.

Architectural documents may be visible in a source inventory while Architecture domain entities remain zero.

## 6. Shared product-family capabilities

These are governed once and specialized by products rather than reinvented independently.

### Human System

- formative research model;
- evaluative Human Factors model;
- release HVA model;
- participant/reviewer separation;
- accessibility/inclusion conventions;
- benchmark/evaluation-twin pattern.

Current authority: `docs/PROGRAM/CEW_HUMAN_CENTRED_GOVUK_MODEL_v2.md` until a future product-family-neutral human model supersedes it.

### Agent operating model

Current authority: `automation/AI_NATIVE_AGENT_OPERATING_CONTRACT_v1.json`.

### Documentation authority

Current authority: `docs/GOVERNANCE/DOCUMENTATION_AUTHORITY_MODEL_v1.md`.

### Product decision register

Current authority: `automation/PRODUCT_DECISION_REGISTER_v1.json`.

### Release/governance principles

- generated != accepted;
- CI != HVA;
- deployment != promotion;
- Production != canonical authority;
- same-revision evidence for promotion;
- one promotion owner per slice;
- professional authority remains explicit.

## 7. N12 boundary

N12 is the reference project used to prove the product on real engineering material.

N12 does not define:
- global eTwin project schema;
- future discipline contracts;
- generic CEW product architecture.

N12 engineering authority remains:

`knowledge/CURRENT_STATE.json` plus governed canonical engineering artifacts.

Product/runtime state may reference or project N12 state but cannot silently duplicate or replace it.

## 8. Capability ownership matrix

| Capability | eTwin | CEW | N12 engineering authority |
|---|---|---|---|
| Portfolio | OWNER | consumer | none |
| Project identity/context | OWNER | consumes | none |
| Discipline scope/isolation | OWNER | consumes within Structures | none |
| Structures P0-P16 | host/navigation | OWNER | supplies project facts/decisions |
| Source/SourceVersion specialist semantics | scopes/references | OWNER for Structures workflow | source facts governed in project |
| DocumentMap / EvidenceRegion | scopes/references | OWNER | evidence instances/facts |
| Structural entities/model | platform reference only | OWNER | canonical project instances |
| Architecture entities | host future contract | not owner | project instances after admission |
| CrossDisciplineRelation | OWNER platform relation contract | participant discipline | evidence/decision inputs where applicable |
| EngineeringDecision Level C | exposes context | OWNER specialist semantics | HUMAN PROFESSIONAL AUTHORITY |
| Solver projection / FEM mapping | platform may display status | OWNER specialist workflow | project run/results under governance |
| Human research/HVA method | SHARED FAMILY MODEL | SHARED FAMILY MODEL | participant/reviewer may be engineer |
| Product promotion | OWNER platform release for eTwin | OWNER CEW product release | does not change engineering truth by itself |

## 9. Boundary tests

A change is likely in the wrong product if any answer is yes:

- Does eTwin need to understand beam reinforcement semantics to implement it? -> likely CEW.
- Does CEW need to know about unrelated Projects to implement it? -> likely eTwin.
- Does source availability automatically create a discipline entity? -> forbidden.
- Does a platform relation collapse discipline identities? -> forbidden.
- Does product deployment change an engineering fact? -> forbidden unless a separate governed professional write boundary explicitly exists.
- Are Human Factors rules being duplicated differently in CEW and eTwin? -> move to shared family governance.

## 10. Change rule

Moving ownership of a capability between eTwin and CEW, or changing N12 engineering authority, requires an explicit product decision record and contract migration. It cannot happen through incidental code reuse or UI placement.
