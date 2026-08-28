# eTwin Platform Identity Boundary v1

Status: ETW-A0 PREPARATION CONTRACT  
Program: `ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1`

## Purpose

ETW-A0 introduces only the platform identities required to make CEW safe in a multi-project, multi-discipline shell. It does not migrate CEW evidence, create source bindings, release Architecture as an engineering domain, or change N12 engineering truth.

## Authority split

- **eTwin platform owns:** `Project`, `Discipline`, `ProjectDisciplineScope`, `ScopeContext`, portfolio/scope isolation and read-only scope inventory projection.
- **CEW owns Structures/Existing Structures:** P0-P16 lifecycle, Source/SourceVersion evidence lineage, claims, engineering decisions, phase gates and CEW/GOV.UK usability contracts.
- **N12 engineering authority remains:** `knowledge/CURRENT_STATE.json` and governed canonical N12 artifacts.

A platform scope state is never engineering evidence or professional authority.

## Core identities

### Project

A stable platform identity for one project. A project ID is a hard data/API boundary, not a cosmetic filter.

Initial projects:

- `N12` — real reference project.
- `TEST_PROJECT` — QA fixture only; it contains no N12 engineering data.

### Discipline

A stable discipline identity. A discipline context selects a domain workspace; it never transfers domain truth from another discipline.

Initial disciplines:

- `STRUCTURES`
- `ARCHITECTURE`

### ProjectDisciplineScope

Declares whether a discipline exists and what product state is available inside one project.

Initial scopes:

- `N12 / STRUCTURES` → `ACTIVE`, `CEW_BOUND`.
- `N12 / ARCHITECTURE` → `NOT_YET_RELEASED`; source inventory may be visible read-only, but `ArchitecturalEntity` and architectural properties are not admitted in A0.
- `TEST_PROJECT / STRUCTURES` → `TEST_ONLY`; zero N12 engineering data.

### ScopeContext

Runtime context is the exact pair `project_id + discipline_id` plus the resolved scope state. It must be carried through routes, queries, caches, asynchronous responses, deep links and browser history.

There is **no default-project fallback** and no implicit fallback to N12. Missing, unknown, disabled or unauthorized context fails closed.

## Document availability versus interpreted domain

The existing CEW source registry already classifies TAV-01, TAV-02, TAV-03 and TAV-04 as `architettonica`. A0 may expose that read-only inventory fact in `N12 / ARCHITECTURE`.

It may not infer from that inventory that:

- Architecture domain is released;
- an `ArchitecturalEntity` exists;
- an architectural property is DOC;
- a structural and architectural object are the same entity.

Therefore:

`source available != domain interpreted`

and

`source DOC != entity/property DOC`.

## A0 source-scope rule

A0 does not introduce `ProjectSourceBinding` or any equivalent persisted ownership binding.

`CEWSourceInventoryAdapter` is a read-only projection over the frozen CEW source registry:

- Architecture projection is allowed only where the registry already explicitly says `classe=architettonica`.
- Structures remains CEW-bound in A0; eTwin does not reclassify every non-architectural source as Structures.
- TEST_PROJECT has no real source projection.

Explicit project/source binding is an ETW-A1 concern.

## Fail-closed invariants

1. `project_id` is required below the UI layer.
2. `discipline_id` is required for discipline workspaces.
3. Unknown project or discipline does not resolve to N12.
4. A stale asynchronous response from a previous scope is discarded.
5. Cache keys include the complete ScopeContext identity.
6. Deep-link reload and browser history restore the same exact scope.
7. Project/discipline scope does not alter immutable SourceVersion identity.
8. A0 creates no architectural entity/property and no cross-discipline relation.
9. Any cross-project or cross-discipline data leakage is a critical non-compensable failure.

## Promotion boundary

This contract is prepared against CEW contract baseline `cab1c53b62b2b70294b6b7e8d7dddd14ccdcb832`.

A0 may reach `PREP_PASS`, but cannot become COMPLETE until a compatible `CEW_PROMOTED_BASELINE`, HVA, Production smoke and `APPROVE_PLATFORM_BOUNDARY` are satisfied.