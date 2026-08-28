# AI-Native Product Agency Operating Model v1

Status: REQUIRED GOVERNANCE CONTRACT  
Applies to: CEW, eTwin and future product work in this repository  
Date: 2026-08-28

## 1. Purpose

This document defines how mature products are conceived, built, evaluated, released and improved in an AI-native development agency.

The model exists to prevent a central failure mode of AI-accelerated delivery: implementation can move faster than people can understand, evaluate and govern the resulting product. Therefore **generation speed and promotion speed are deliberately separated**.

The repository is the institutional memory. Conversations, agent sessions and local workspaces are operating interfaces, not sources of truth.

The governing chain is:

`USER / PROFESSIONAL NEED -> CAPABILITY -> REPRESENTATIVE JOURNEY -> PRODUCT SLICE -> IMPLEMENTATION -> AUTOMATED EVIDENCE -> HUMAN EVIDENCE -> RELEASE CANDIDATE -> PILOT / PRODUCTION -> OBSERVATION -> PROMOTION / ITERATION`

For regulated or professional decisions, an additional authority chain applies:

`INFORMATION -> EVIDENCE -> INTERPRETATION -> HUMAN PROFESSIONAL DECISION -> RECEIPT -> GOVERNED STATE`

No delivery mechanism may collapse these two chains.

## 2. Five permanent systems

### 2.1 Product System

Owns what problem is being solved and what product capability must exist.

Canonical concerns:
- user and professional needs;
- jobs to be done;
- capability map;
- end-to-end journeys;
- product architecture;
- outcome and safety metrics;
- roadmap and sequencing;
- scope and non-goals.

A route, component, AI feature, parser or solver is never the primary product objective. It is an implementation choice serving a capability.

### 2.2 Human System

Owns understanding and evaluating how people actually work with the product.

It includes three different activities that must not be conflated:

1. **Formative research** — understand context, workflow, language, constraints, uncertainty and consequences of error before or during design.
2. **Evaluative usability** — observe whether a representative person can complete a realistic task with a prototype or candidate.
3. **Release acceptance** — determine whether an immutable candidate satisfies the already-declared human, safety and authority criteria required for promotion.

Human research is not a final cosmetic gate. It is continuous product evidence.

### 2.3 Agentic Delivery System

Owns implementation and bounded analysis through specialist agents and developers.

Agents are treated as a workforce with explicit identity, mission, inputs, outputs, permissions and forbidden authority. They are not treated as unconstrained chat assistants.

Every promotable slice has exactly one promotion owner. Independent support agents may verify security, human factors, contract compatibility, authority and quality, but cannot promote the slice.

### 2.4 Evidence & Governance System

Owns contracts, baselines, gates, receipts, decision records, promotion state and auditability.

The governing principle is:

> AI and software produce work; governance determines when that work may change product or professional state.

Automated success is necessary where declared but never substitutes for human authority or human evidence where those are required.

### 2.5 Operations System

Owns environments, deployment, production observation, telemetry, incidents, rollback and service reliability.

A successful build is not a successful service. A successful Preview is not Production acceptance. Production is not automatically canonical authority.

## 3. Work hierarchy

All product work is represented using the following hierarchy.

### Need

A real human, organizational or professional problem.

Example: a structural engineer needs to find the correct drawing and understand the evidence behind a model statement without knowing repository internals.

### Capability

A durable ability the product must provide.

Example: **Find, inspect and verify governed project drawings.**

A capability may require multiple screens, services, contracts and agents.

### Representative journey

A realistic end-to-end task through which the capability can be observed.

A journey is expressed in the user's language and has a verifiable outcome.

### Slice

The smallest end-to-end increment that materially advances a capability and can be independently evaluated.

### Candidate

An immutable revision for which the applicable automated checks and evidence can be collected.

### Release

A deployed instance of a candidate in a declared environment: Preview, pilot, limited Production or Production.

### Promotion

A governance decision that changes the admitted state of the product/program. Promotion is not synonymous with deployment or merge.

## 4. Separate state dimensions

A mature product does not overload one status field. At minimum the following dimensions remain distinct.

### 4.1 Delivery state

`PROPOSED -> DESIGNED -> PREPARED -> IMPLEMENTED -> AUTOMATED_VALIDATED`

This describes whether the work exists technically.

### 4.2 Human evidence state

`NOT_ASSESSED -> RESEARCHED -> EVALUATION_PENDING -> EVALUATED_PASS | EVALUATED_WITH_RESIDUAL | EVALUATED_FAIL`

This describes human evidence, not technical quality.

### 4.3 Release state

`NOT_DEPLOYED -> PREVIEW -> PILOT -> PRODUCTION`

This describes where the candidate runs.

### 4.4 Promotion state

`NOT_PROMOTABLE -> CANDIDATE -> BLOCKED_GATE -> PROMOTED`

This describes governance admission.

### 4.5 Professional / engineering authority state

Domain-specific authority and epistemic states remain owned by their domain contracts. Product maturity must never be used to upgrade engineering truth.

For CEW this means product state remains separate from `DOC / MIS / RIF / INF / INC / ND`, EvidenceRegion state, EngineeringDecision and canonical engineering generation state.

## 5. Generated is not accepted

AI-native delivery requires explicit distance between what was generated and what was accepted.

Artifacts may move through:

`GENERATED -> DETERMINISTICALLY_CHECKED -> INDEPENDENTLY_REVIEWED -> HUMAN_EVALUATED -> RELEASED -> OBSERVED -> PROMOTED`

No agent may infer acceptance from:
- code compilation;
- green CI alone;
- model confidence;
- consensus among agents;
- successful deployment;
- user completion without checking for false success;
- absence of complaints.

## 6. Agent operating contract

Every specialist agent contract must declare at minimum:

| Field | Required meaning |
|---|---|
| `agent_id` | stable identity |
| `mission` | bounded purpose |
| `owned_work_items` | work it may prepare/implement |
| `inputs` | admitted sources/contracts |
| `outputs` | allowed result artifacts |
| `write_scope` | branches/stores it may modify |
| `forbidden_writes` | canonical or external state it may not modify |
| `promotion_authority` | normally NONE except declared orchestrator handshake |
| `professional_authority` | NONE unless explicitly human |
| `required_independent_checks` | security / QA / authority / human factors etc. |
| `escalation_conditions` | when it must stop |

### Least-authority principle

An agent receives the minimum authority needed to do its work. Read access to authoritative data does not imply write authority. Ability to propose a change does not imply authority to approve it.

### One promotion owner

Each promotable vertical slice has exactly one owner responsible for the result handshake. Support agents return evidence and blockers but cannot mutate promotion state.

### Independent assurance

Where practical, the agent that implements a safety-critical behavior must not be the sole verifier of that behavior.

## 7. Orchestration model

Preparation and verification may be parallel; promotion is serialized.

The standard execution cycle is:

1. resolve the admitted baseline;
2. select one eligible promotable work item;
3. emit owner and support tasks;
4. implement the smallest end-to-end slice;
5. run deterministic gates;
6. collect independent assurance findings;
7. run human research/evaluation where applicable;
8. deploy to the required environment;
9. run same-revision smoke/acceptance;
10. archive result and evidence receipts;
11. resolve human/external authority gates;
12. promote only if all required evidence is present;
13. release the next dependent item.

The orchestrator must stop rather than infer missing authority or evidence.

## 8. Human-centred operating principles

### 8.1 The person performs their work; the evaluation system observes

Users must not be required to operate the internal validation model.

A participant should see the professional situation and task. Internal test IDs, runtime SHAs, gate states, receipt schemas and telemetry belong to researcher/reviewer or audit surfaces.

### 8.2 Professional language first

Primary interfaces use domain language. Internal architecture terms remain available through progressive disclosure when they are needed for audit or expert diagnostics.

### 8.3 Participant and reviewer are different roles

The participant completes realistic work. The reviewer interprets evidence and makes the HVA/release decision. A participant is never asked to decide whether a software release should pass its own governance gate.

### 8.4 Telemetry is normally invisible during the task

Time, interactions, help requests, recoveries and navigation paths are collected without pressuring the participant to optimize for the test.

### 8.5 Mental models are evaluated after action

Critical concepts are tested after the participant has acted, using natural questions such as whether an operation modified an original document or which object is authoritative.

### 8.6 Critical errors are non-compensable

A fast task does not compensate for a wrong project, wrong source/version, authority misunderstanding, canonical-write misconception, cross-scope leakage or false success.

### 8.7 Usability friction and safety failure are different

Extra time or interactions may be usability residuals. Wrong authority, wrong source, false equivalence or unsafe scope behavior are blockers.

## 9. Product evidence model

Every capability should have an evaluation twin: a durable statement of how the agency knows the capability works.

The evaluation twin contains:
- representative tasks;
- success conditions;
- critical failure conditions;
- baseline metrics;
- qualitative observations;
- mental-model checks;
- environment and revision identity;
- accessibility/inclusion considerations;
- decision and residuals.

This allows the agency to compare the same capability across versions rather than relying on subjective impressions.

## 10. Release rings

The default release rings are:

`DEV -> PREVIEW -> HUMAN EVALUATION -> PILOT -> PRODUCTION -> OBSERVED PRODUCTION`

Not every capability needs every ring, but any omitted ring must be justified by its risk and contract.

### Preview

Technical and human evaluation environment. Preview readiness does not equal product acceptance.

### Pilot

Controlled real-use environment with bounded users/projects and explicit observation.

### Production

Operational service state. Production may still contain noncanonical or proposal-only workflows.

### Observed Production

A production capability with real operational evidence and no unresolved critical incidents. This is the strongest product maturity signal before/with promotion.

## 11. Same-revision rule

For a promotable user-facing candidate, applicable automated gates, HVA evidence and Production smoke must identify one immutable revision or a traceably equivalent promoted revision.

Evidence from a different revision cannot silently satisfy the current candidate.

## 12. Decision records

Material product decisions must be persisted with:
- decision ID;
- context/problem;
- evidence;
- alternatives considered where material;
- decision;
- consequences;
- affected contracts/work items;
- supersession rule.

A later agent must be able to learn why the current design exists without reconstructing the decision from conversation history.

## 13. Documentation as institutional memory

The repository is the durable organizational memory.

Rules:
- chat/session text is not canonical governance;
- current contracts identify their authority and version;
- superseded documents remain available and are not silently rewritten as if history never occurred;
- machine-readable manifests point agents to current authoritative documents;
- state files describe current state, not aspirational architecture;
- receipts describe observed execution, not intention;
- decisions explain why an authority or contract changed.

The documentation hierarchy and precedence rules are defined in `docs/GOVERNANCE/DOCUMENTATION_AUTHORITY_MODEL_v1.md`.

## 14. Quality model

Quality is multidimensional and cannot be reduced to CI.

Required dimensions where applicable:
- functional correctness;
- contract compatibility;
- data/provenance integrity;
- security and isolation;
- accessibility;
- human effectiveness;
- human efficiency;
- confidence/comprehension;
- professional authority correctness;
- operational reliability;
- observability and rollback;
- auditability.

## 15. Stop conditions

Work stops and evidence is preserved when any of the following occurs:
- required human/professional authority is missing;
- primary evidence required by the domain is missing;
- source/version identity is unresolved;
- a safety-critical representative task produces false success;
- project/scope/discipline isolation is violated;
- an agent would need to write outside its authority;
- the candidate revision differs from the revision carrying required acceptance evidence;
- product continuity would require inventing or normalizing away missing professional information;
- a test would need to be weakened solely to obtain a green result.

## 16. Application to CEW and eTwin

### CEW

CEW remains the specialist structural-engineering product/domain authority for its declared lifecycle, evidence, claims, engineering entities, engineering decisions and governed model generations.

CEW product/runtime state remains distinct from N12 engineering authority.

### eTwin

eTwin is the project/discipline platform shell. It owns platform identity, scope, portfolio and explicitly admitted cross-discipline coordination. It does not absorb CEW engineering authority.

### Shared human system

CEW and eTwin use the same human-research/evaluation principles. Human factors is not implemented separately by each product in incompatible ways.

## 17. Adoption rule

New product or development contracts must declare whether they:
- implement this operating model;
- specialize it for a product/domain; or
- intentionally deviate from it.

Any deviation affecting authority, human safety, promotion or evidence requires a decision record.
