# CEW Structural Model Workspace v1 — Contract

**Program:** `CEW-GOAL-01`  
**Work package:** `CEW-B2-RECONSTRUCTION-PROPERTIES`  
**Preparation status:** `PARALLEL_PREPARATION_NOT_RELEASED`  
**Blocking predecessor:** `CEW-B1-SOURCE-EVIDENCE-JOURNEY / CEW-B1-PROD-01`  
**Engineering authority:** `knowledge/CURRENT_STATE.json` and its governed handoffs/gates.

## Purpose

The Structural Model Workspace is the engineer-facing view of the current authorized AS-IS structural representation before assessment-scenario assumptions and solver-specific idealizations are applied.

It must make the distinction explicit between:

1. **evidence / observations**;
2. **canonical structural identity and geometry**;
3. **engineering properties and their evidence states**;
4. **admitted modeling rules**;
5. **solver projection**;
6. **solver results**.

The workspace itself is not any of those authorities and may not collapse them into a single “model value”.

## Current N12 readiness basis

The current M1E handoff is `RESIDUAL_NOT_CALCULATION_MODEL_READY` with `calculation_model_ready=false`.

### Transferable now

The handoff currently authorizes transfer of:

- frozen superstructure connectivity and rigid-zone semantics;
- usable sections for all 359 ordinary superstructure members, with evidence watches retained;
- the current 38-support / 55-member foundation structural topology;
- the admitted 38/38 foundation XY solver-placement rule, with source-coordinate provenance preserved;
- identity maps and a solver project shell.

### Not authorized now

The workspace must visibly block any interpretation that current numerical verification is ready because the current handoff retains six blocking domains:

- current concrete assessment / LC / FC;
- numerical loads, masses and combinations;
- foundation numerical Z;
- 15 foundation property gaps plus one supported-only binding;
- affected superstructure reinforcement residuals;
- current geotechnical model.

## Model-generation model

The primary model object is a versioned **AS-IS Generation**.

Each generation references rather than duplicates:

- geometry/topology handoff;
- entity registries and connectivity ledgers;
- property bindings;
- evidence/provenance;
- current watch/residual register;
- admitted modeling-rule references.

Generation status must be separate from engineering readiness.

Suggested product states:

- `WORKING_GENERATION`;
- `REVIEW_REQUIRED`;
- `AS_IS_APPROVED_FOR_DECLARED_USE`;
- `SUPERSEDED`.

A generation may be structurally coherent while still being not eligible for solver execution.

## Workspace structure

### A. Model tree

The model tree is organized by engineering object, not repository path:

- Building
  - Levels G1–G5
    - Beams
    - Columns
    - Rigid zones / offsets
  - Foundations
    - Supports
    - Foundation members
  - Roof special geometry

The tree must support filtering by:

- entity type;
- level;
- evidence/use state;
- watch/residual state;
- property completeness;
- solver-transfer eligibility.

### B. 3D / 2D coordinated model

A selected member is the same stable entity in 3D, plan/elevation, table, properties and source/evidence panels.

Display layers must distinguish:

- ordinary structural members;
- rigid analytical links;
- foundation members;
- roof special nonordinary geometry;
- entities with local watches;
- entities excluded from a declared downstream use.

### C. Readiness panel

The model header never displays a single generic “complete” status. It shows independent readiness dimensions:

- Geometry / topology;
- Sections;
- Reinforcement;
- Materials;
- Loads / masses;
- Foundations;
- Geotechnics;
- Calculation-model readiness.

For N12, the present truthful top-level state is:

`GEOMETRY READY WITH WATCHES · SECTIONS USABLE WITH WATCHES · OTHER DOMAINS PARTIAL/ND · CALCULATION MODEL NOT READY`.

These labels are derived from current gates and are not hard-coded facts.

### D. Entity inspector

For any entity, expose separately:

- stable identity;
- geometry/topology reference;
- section binding;
- reinforcement binding;
- material binding;
- load/mass host state;
- boundary/foundation relationship;
- evidence state (`DOC/MIS/RIF/INF/ND` or governed supported state where applicable);
- use eligibility;
- watch/residual IDs;
- source/evidence links;
- generation/scenario lineage.

## “Evidence state” versus “use state”

The product must distinguish at least:

- **evidence state** — what supports the fact;
- **use state** — whether the fact is usable for a declared engineering/modeling purpose;
- **workflow state** — whether review/promotion is complete.

Examples from current N12 that must remain representable:

- a section can be usable while carrying a MIS/watch provenance;
- a foundation property binding can be supported but not direct;
- a historical concrete value can be DOC historical evidence but not a current solver material parameter;
- foundation XY can be numerically placed by an admitted modeling rule without rewriting primary foundation XY evidence.

## Foundation-specific boundary

The current foundation model must follow FPEP/P07 authority:

- 38 distinct support identities;
- 55 primary foundation members;
- legacy pre-P07 58-member topology is history/regression only;
- 22 and 22bis remain distinct;
- no PT/M0-G coordinate is promoted back into foundation evidence;
- solver XY placement remains a modeling projection;
- numeric foundation Z remains ND until direct evidence or a separately authorized rule exists.

## Downstream solver handoff

This workspace may prepare a solver-neutral projection only after the relevant P12 authorization.

Before that authorization it may show:

- what can already be transferred;
- what will require a modeling rule;
- what remains blocking;
- which entities are excluded from a given analysis scope.

It may not execute or label a current-state analysis as valid merely because the geometry can be exported.

## Human-factors acceptance

An engineer unfamiliar with the repository must be able to answer within the workspace:

1. What is currently in the AS-IS structural model?
2. Which parts are directly documented versus modeled/supported?
3. Which properties are usable and which are missing?
4. Why is the calculation model not yet ready?
5. What is the smallest affected scope for each residual?
6. Which source/evidence supports the selected object?
7. What would change if a later scenario/modeling rule is admitted?

## Forbidden

- a global green “model complete” state while blocking domains remain open;
- treating solver-transfer eligibility as calculation readiness;
- hiding property provenance behind a single numerical value;
- converting historical material/load/geotechnical values into current parameters silently;
- replacing source/foundation evidence with a solver-coordinate projection;
- collapsing supported evidence into direct documentary evidence;
- copying a property to fill ND values by adjacency or storey analogy;
- modifying AS-IS history when creating an intervention/scenario generation;
- direct canonical writes from model-view interactions.

## Release condition

This contract is preparation only until `CEW-B1-PROD-01` is closed and B2 is released by the product orchestrator.
