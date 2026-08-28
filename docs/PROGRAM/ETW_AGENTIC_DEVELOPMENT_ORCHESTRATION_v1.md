# ETW Agentic Development & Orchestration v1

Status: REQUIRED EXECUTION CONTRACT  
Program: `ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1`

## Operating model

One specialist agent owns each promotable vertical slice. Independent support agents may work concurrently on the same selected slice, but only the promotion owner can submit the result handshake consumed by `scripts/etw_orchestrator.py`.

Promotion is always serial. Preparation and verification may be parallel.

## Branch model

Every slice uses a dedicated branch from the exact admitted baseline:

- `work/etw-a0-platform-identity`
- `work/etw-a1-project-source-scope`
- `work/etw-a2-portfolio`
- `work/etw-a3-cross-discipline-identity`
- `work/etw-a4-property-assertions`
- `work/etw-a5-decision-cockpit`
- `work/etw-a6-multidisciplinary-viewer`
- `work/etw-z0-production-acceptance`

A branch may contain only its declared vertical. Unrelated fixes are split into another branch or returned to the owning upstream slice.

## Same-head rule

For a promotable result, all applicable deterministic gates, HVA evidence, Production smoke and receipt must refer to one immutable accepted revision or to a traceably promoted equivalent. A green result from another revision does not satisfy the current slice.

## Owner and support topology

### ETW-A0

Promotion owner: `ETW_PLATFORM_IDENTITY_AGENT`

Parallel support:
- `ETW_SECURITY_ISOLATION_AGENT` — route/query/cache/async isolation and fail-closed scope;
- `ETW_CONTRACT_COMPATIBILITY_AGENT` — CEW baseline mapping/drift;
- `ETW_HUMAN_FACTORS_AGENT` — project/scope comprehension tasks;
- `ETW_AUTHORITY_AUDIT_AGENT` — prove read-only inventory adapter and no CEW primitive migration.

A0 starts PREP_ONLY. The owner may submit `PREP_PASS`; it cannot submit a promotable PASS while CEW_PROMOTED_BASELINE is unsatisfied.

### ETW-A1

Promotion owner: `ETW_SOURCE_SCOPE_AGENT`

Parallel support:
- Security Isolation — shared-source cross-project isolation;
- Authority Audit — exact SourceVersion, lineage consistency, no F1/F2 rewrite;
- Human Factors — source/scope interpretation and canonical-write misconception.

### ETW-A2

Promotion owner: `ETW_PORTFOLIO_HUMAN_FACTORS_AGENT`

Parallel support:
- Security Isolation — context switch and deep-link isolation;
- Human Factors — benchmark Portfolio task flows;
- Authority Audit — Architecture source inventory must not imply domain release.

### ETW-A3

Promotion owner: `ETW_CROSS_DISCIPLINE_AGENT`

Parallel support:
- Contract Compatibility — ArchitectureDisciplineContract compatibility;
- Authority Audit — exact TAV-02 identity, source DOC != entity DOC;
- Human Factors — candidate/review/relation comprehension;
- Security Isolation — no cross-scope admission leakage.

Human gate `APPROVE_CROSSDISCIPLINE_CONTRACT` is mandatory before A4 release.

### ETW-A4

Promotion owner: `ETW_PROPERTY_ASSERTION_AGENT`

Parallel support:
- Authority Audit — assertion genealogy and epistemic state;
- Human Factors — compare comprehension and false-equivalence tests;
- Security Isolation — project/discipline isolation in compare queries.

### ETW-A5

Promotion owner: `ETW_DECISION_AUTHORITY_AGENT`

Parallel support:
- Authority Audit — Level-C boundary, append-only receipt, provenance;
- Human Factors — authority comprehension and decision confidence;
- Security Isolation — project/scope preserved through decision persistence.

A machine result may legitimately be `HUMAN_AUTHORITY_REQUIRED`; this is not a failure and must not be bypassed.

### ETW-A6

Promotion owner: `ETW_MULTIDISCIPLINARY_VIEWER_AGENT`

Parallel support:
- Human Factors — viewer semantics/accessibility;
- Authority Audit — visual state must not create identity;
- Security Isolation — selected project/scope must constrain every layer/request.

A6 ends at viewer-specific acceptance only.

### ETW-Z0

Promotion owner: `ETW_QA_ASSURANCE_AGENT`

Parallel support:
- all support agents run independently against the frozen candidate;
- no specialist is allowed to fix its own failed evidence inside Z0.

Any failure is routed to the owning slice. Z0 contains no functional implementation.

## Per-slice execution cycle

1. Orchestrator validates contracts and selects one owner item.
2. Owner task is emitted to `automation/outbox/ETW_AGENT_TASK.json`.
3. Required support tasks are emitted independently and run in parallel.
4. Owner implements the smallest end-to-end vertical on the dedicated branch.
5. Deterministic gates run.
6. Support agents return independent findings; critical safety findings block promotion.
7. User-facing changes enter HVA with representative CEW/GOV.UK tasks.
8. A real Preview/Production smoke is executed where required.
9. Owner writes one result matching `ETW_AGENT_RESULT_CONTRACT_v1.json`.
10. Orchestrator ingests the result, archives a receipt and changes queue state.
11. If a human/external gate is pending, the next item remains blocked.
12. Only after gate evidence is persisted may the orchestrator release the next owner slice.

## Concurrency rules

Allowed concurrently:
- owner implementation + independent QA/security/authority review;
- preparation of non-promotable future contracts where explicitly declared;
- CEW B1 completion and ETW-A0 PREP_ONLY.

Forbidden concurrently:
- two promotion-owner work items in `IN_PROGRESS`;
- parallel mutation of shared canonical authority artifacts;
- A1 promotion while A0/platform-boundary gate is open;
- A4 promotion before cross-discipline human approval;
- eTwin Production promotion before Z0 and final human approval.

## Escalation / stop rules

Immediate stop and preserve evidence when any of these occurs:

- cross-project leakage;
- cross-discipline leakage;
- wrong SourceVersion or unresolved version mismatch;
- geometry interpreted as identity;
- source DOC promoted to entity/property DOC without evidence;
- Level-C auto-completion;
- UI/runtime canonical write outside authorized boundary;
- CEW baseline incompatibility;
- TEST_ONLY fixture entering canonical N12 history;
- HVA FALSE_SUCCESS on a safety-critical task.

## Human authority integration

Human gates live in `automation/ETW_HUMAN_GATE_STATE_v1.json`. Agents cannot mark them satisfied. Gate evidence must point to append-only receipts or an immutable promoted baseline SHA.

## Current authorized work

Current owner slice: `ETW-A0`  
Execution mode: `PREP_ONLY`  
Current CEW contract baseline: `cab1c53b62b2b70294b6b7e8d7dddd14ccdcb832`  
Promotion blocker: `CEW_PROMOTED_BASELINE`

Therefore the first agentic implementation may build and validate the A0 platform identity boundary, but must stop at `PREP_PASS` until CEW B1 is actually HVA/smoke/promotion complete and a compatible promoted SHA is frozen.
