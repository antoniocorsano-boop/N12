# CEW Engineering Property Workspaces v1 — Contract

**Program:** `CEW-GOAL-01`  
**Work package:** `CEW-B2-RECONSTRUCTION-PROPERTIES`  
**Preparation status:** `PARALLEL_PREPARATION_NOT_RELEASED`  
**Blocking predecessor:** `CEW-B1-SOURCE-EVIDENCE-JOURNEY / CEW-B1-PROD-01`  
**Engineering authority:** `knowledge/CURRENT_STATE.json` plus the canonical domain gates referenced below.

## Purpose

Property Workspaces expose the engineering inputs attached to stable structural entities while preserving three distinct questions:

1. **What is known?** — evidence state and source;
2. **What may be used?** — declared use eligibility;
3. **What is still required?** — information requirement / residual / watch.

They must never flatten these into a single value/status column.

## Workspace families

### Sections

Primary authority: `data/canonical/M1S_SECTION_GATE_v1.csv` and referenced member ledgers.

Current N12 state:

- 359/359 ordinary structural members have usable sections;
- overall gate `PASS_WITH_WATCH`;
- five evidence watches remain;
- one G5 beam section is `SUPPORTED` rather than DOC;
- four vertical column segments retain endpoint evidence watches.

The UI must therefore show `usable` separately from `documented/direct`.

### Reinforcement

Primary authority: `data/canonical/M1A_REINFORCEMENT_GATE_v1.csv` and its referenced member/group ledgers.

The workspace must preserve:

- immutable reinforcement-source identity;
- storey/source separation;
- directly member-bound versus group/special-feature evidence;
- incomplete/unreadable claims;
- source/model binding state;
- directional reinforcement meaning;
- explicit residuals before affected member checks.

`2 Φ12 superiori + 2 Φ12 inferiori` and equivalent explicit natural-language observations may never be stored/displayed as merely `4 Φ12`.

### Materials and knowledge level

Primary authority: `data/canonical/M1M_MATERIAL_GATE_v1.csv`.

Current distinction that the UI must make obvious:

- historical concrete notation `R'=300 kg/cm²` is documentary historical evidence;
- steel `FeB38k` is documentary historical evidence;
- current in-situ concrete strength is ND;
- LC is ND;
- FC is ND.

Historical values must not be silently transformed into current solver material parameters.

### Loads and masses

Primary authority: `data/canonical/M1L_LOAD_GATE_v1.csv` and referenced load-model ledgers.

The load workspace must support symbolic/semantic load-path definition even when numeric values are unavailable.

Current N12 state includes:

- complete semantic target/load-path structure;
- zero unsourced numeric load rows;
- numerical Gk/Qk/masses/combination inputs not ready;
- no roof special geometry loaded without an authorized structural role.

A blank numeric value is a first-class `ND / information required` state, not an error to auto-fill.

### Foundations

Primary authority: `data/canonical/M1F_FOUNDATION_GATE_v1.csv`, FPEP/P07 artifacts and later M1E projection rules.

Current structural assembly state:

- 38 distinct support identities;
- 55 primary foundation members;
- one connected component;
- 39 direct TAV-01A property bindings;
- 1 supported-only binding;
- 15 ND documentary property bindings;
- no promoted foundation Cartesian XY from PT/M0-G;
- numeric foundation Z remains ND;
- current solver material/load/geotechnical inputs remain not ready.

The legacy pre-P07 58-member topology is regression/history only and must never appear as the current authority.

### Geotechnics

The geotechnical workspace distinguishes historical context from current assessment inputs.

Historical documentary values may be displayed as provenance, but current:

- stratigraphy;
- groundwater screening;
- strength parameters;
- stiffness/settlement parameters;
- modern soil resistance/springs

remain ND until separately evidenced or admitted through an authorized scenario/rule process.

## Common property-row model

Every property row must support, as applicable:

- entity/scope;
- property name;
- value or symbolic state;
- unit;
- evidence state;
- source/evidence link;
- binding method (`DIRECT`, governed `SUPPORTED`, modeling-rule projection, or other registered class);
- use state;
- intended downstream use;
- watch/residual;
- information requirement;
- last authorized generation/reference.

A numerical value may be displayed only with its evidence/binding context reachable in the same interaction.

## Use-state model

Minimum product use states:

- `NOT_AVAILABLE`;
- `AVAILABLE_NOT_REVIEWED`;
- `USABLE_WITH_WATCH`;
- `APPROVED_FOR_DECLARED_USE`;
- `BLOCKED_FOR_DECLARED_USE`;
- `SCENARIO_ONLY`;
- `SUPERSEDED`.

Use state never changes the underlying epistemic/evidence state.

## Property coverage views

For a selected level, entity set or whole building, CEW may show coverage summaries such as:

- usable sections / total;
- direct reinforcement bindings / residuals;
- current material inputs ready / missing;
- numeric loads ready / missing;
- foundation direct/supported/ND bindings;
- geotechnical information requirements.

Coverage is not a percentage of “engineering completion” and must not imply readiness beyond the declared domain/use.

## Residual interaction

Selecting a missing/watch property opens the relevant evidence/information workflow, not an editable free-form canonical cell.

Actions may include:

- open source/evidence;
- request/review evidence;
- create an investigation/information requirement;
- inspect an existing modeling rule;
- exclude a defined scope from a later verification;
- prepare a human engineering decision.

The action that changes engineering authority remains behind its specific governed gate.

## Cross-domain readiness

Property Workspaces feed the Structural Model readiness panel. They do not directly set `CALCULATION_MODEL_READY`.

For current N12, `data/canonical/M1E_CALCULATION_MODEL_HANDOFF_v1.json` remains the authoritative cross-domain readiness handoff and declares six open blocking domains.

## Human-factors acceptance

Without repository knowledge, an engineer must be able to:

1. select a structural member or domain;
2. see the engineering property needed;
3. understand whether a displayed value is direct, supported, historical, modeled or ND;
4. open the source/evidence supporting it;
5. understand whether it may be used for a declared purpose;
6. see the exact residual when it may not;
7. initiate the appropriate evidence/investigation/decision path without editing canonical data directly.

## Forbidden

- a single ambiguous status combining evidence and usability;
- automatic nearest-member or same-storey property copying;
- automatic MIS/RIF/INF/ND to DOC promotion;
- supported-to-direct promotion by UI formatting;
- historical-to-current material/load/geotechnical conversion without an authorized decision;
- filling numeric load, mass, foundation Z or soil values for visual/model completeness;
- aggregate reinforcement normalization that loses upper/lower meaning;
- direct canonical editing from a property table cell;
- setting `CALCULATION_MODEL_READY` from coverage summaries alone.

## Release condition

This contract remains parallel preparation until `CEW-B1-PROD-01` is closed and B2 is formally released by the product orchestrator.
