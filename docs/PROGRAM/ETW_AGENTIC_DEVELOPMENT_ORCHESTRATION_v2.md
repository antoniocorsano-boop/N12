# ETW Agentic Development & Orchestration v2

Status: REQUIRED EXECUTION CONTRACT  
Supersedes for future promotion: `ETW_AGENTIC_DEVELOPMENT_ORCHESTRATION_v1.md`  
Program: `ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2`  
Governing agency model: `docs/GOVERNANCE/AI_NATIVE_PRODUCT_AGENCY_OPERATING_MODEL_v1.md`

## 1. Operating model

One specialist agent owns each promotable vertical slice. Independent support agents may work concurrently on the same selected slice, but only the declared promotion owner may submit the promotable result handshake consumed by the orchestrator.

Preparation and verification may be parallel. Promotion is serial.

The orchestrator is not a super-agent with professional authority. It is a deterministic coordinator of declared dependencies, evidence and gate state.

## 2. Agent contract model

Every ETW agent must declare:

- stable `agent_id`;
- bounded mission;
- owned work items;
- admitted contract/input set;
- allowed result/output set;
- branch/write scope;
- forbidden writes;
- promotion authority;
- professional authority;
- required independent assurance;
- escalation/stop conditions.

### Least authority

Read access never implies write access. Ability to propose never implies ability to approve. Ability to build a result never implies authority to change professional or canonical state.

### Promotion owner

The promotion owner may produce the result handshake for its own slice only. It cannot bypass missing external/human gates.

### Support agents

Support agents return evidence and blockers. They cannot mutate queue/promotion state.

## 3. Standing support roles

### Security Isolation

Tests project/scope/discipline isolation, stale context, cache/query/async/deep-link behavior and fail-closed rules.

### Contract Compatibility

Tests compatibility with CEW promoted/contract baselines and shared governance contracts.

### Human Factors

Runs or prepares formative/evaluative/release human work using the shared v2 model. It does not ask participants to operate release governance.

### Authority Audit

Tests that UI/read models/agents/source availability/spatial relations do not create unauthorized domain or canonical authority.

### QA Assurance

Tests deterministic behavior, regression, receipts, evidence completeness and same-revision rules independently from implementation convenience.

## 4. Branch model

Dedicated branches remain the default:

- `work/etw-a0-platform-identity`
- `work/etw-a1-project-source-scope`
- `work/etw-a2-portfolio`
- `work/etw-a3-cross-discipline-identity`
- `work/etw-a4-property-assertions`
- `work/etw-a5-decision-cockpit`
- `work/etw-a6-multidisciplinary-viewer`
- `work/etw-z0-production-acceptance`

A branch contains one declared vertical. Unrelated fixes are routed to another branch or upstream owning slice.

Cross-cutting governance changes use a separate governance branch and cannot silently mutate the already-tested head of a product slice.

## 5. Same-revision rule

A promotable result requires all applicable deterministic gates, independent assurance, human acceptance evidence and required Production smoke to identify one immutable accepted revision or an explicitly traceable equivalent.

Evidence from a different SHA is not inherited silently.

## 6. Human-system integration

Human work has three modes:

1. **formative research** — discovers product/user needs and may change design/backlog;
2. **evaluative Human Factors** — observes representative tasks on prototypes/candidates;
3. **release HVA** — reviewer decision on the immutable release candidate.

### Participant layer

Shows professional context, one dominant task and the product.

It must not primarily show:
- internal task IDs;
- live telemetry counters;
- runtime SHA;
- gate states;
- release decision enums;
- receipt export.

### Observation layer

Collects declared metrics invisibly by default.

### Reviewer layer

Shows evidence, blockers, residuals, mental-model findings, accessibility findings and candidate identity. The reviewer owns HVA/release decision.

### Receipt layer

Binds human evidence to revision/environment after reviewer decision.

## 7. Per-slice execution cycle

1. Read `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`.
2. Resolve the current programme contract and admitted baseline.
3. Resolve the current queue and human/external gate state.
4. Select one eligible promotion-owner work item.
5. Emit owner task and independent support tasks.
6. Owner implements the minimum end-to-end slice.
7. Deterministic gates run.
8. Independent support agents return findings.
9. Formative/evaluative human work runs where needed before release HVA.
10. Immutable candidate is frozen for HVA.
11. Participant/reviewer HVA runs under the shared human contract.
12. Required Preview/Pilot/Production smoke runs on the accepted revision.
13. Owner writes one result matching the current result contract.
14. Orchestrator validates evidence, archives receipt and changes queue state.
15. External/human professional gates are resolved separately.
16. Only after all required evidence is persisted may the next owner slice be released.

## 8. Slice ownership topology

### ETW-A0

Promotion owner: `ETW_PLATFORM_IDENTITY_AGENT`

Support:
- Security Isolation;
- Contract Compatibility;
- Human Factors;
- Authority Audit;
- QA Assurance.

A0 may remain `PREPARED_BLOCKED_PROMOTION` while CEW promoted baseline is missing.

A0 promotion requires v2 Human Factors revalidation even if prior v1 preparation gates passed.

### ETW-A1

Promotion owner: `ETW_SOURCE_SCOPE_AGENT`

Support emphasizes exact SourceVersion, lineage, shared-source isolation, no F1/F2 rewrite and human source/scope comprehension.

### ETW-A2

Promotion owner: `ETW_PORTFOLIO_HUMAN_FACTORS_AGENT`

Support emphasizes context-switch/deep-link isolation and human comprehension of ACTIVE / NOT_YET_RELEASED / TEST_ONLY.

### ETW-A3

Promotion owner: `ETW_CROSS_DISCIPLINE_AGENT`

Support emphasizes ArchitectureDisciplineContract, exact TAV-02 identity, source-DOC != entity-DOC, candidate/review/relation comprehension and scope isolation.

Human gate `APPROVE_CROSSDISCIPLINE_CONTRACT` remains mandatory before A4 release.

### ETW-A4

Promotion owner: `ETW_PROPERTY_ASSERTION_AGENT`

Support emphasizes assertion genealogy, conflict/projection comprehension, false equivalence and compare-query isolation.

### ETW-A5

Promotion owner: `ETW_DECISION_AUTHORITY_AGENT`

Support emphasizes Level-C boundary, append-only professional receipt, provenance, project/scope persistence and authority comprehension.

`HUMAN_AUTHORITY_REQUIRED` is a legitimate machine outcome, not a failure.

### ETW-A6

Promotion owner: `ETW_MULTIDISCIPLINARY_VIEWER_AGENT`

Support emphasizes viewer semantics/accessibility, no visual-state identity creation and selected-scope enforcement across every layer/request.

### ETW-Z0

Promotion owner: `ETW_QA_ASSURANCE_AGENT`

All support agents run independently against a frozen candidate. No specialist may fix its own failed evidence inside Z0; failures return to the owning slice.

Z0 contains no functional implementation.

## 9. Concurrency rules

Allowed:
- owner implementation with independent QA/security/authority review;
- formative research while technical preparation continues;
- non-promotable future contract preparation where explicitly declared;
- CEW B1 completion while ETW-A0 remains PREP_ONLY/PREPARED_BLOCKED_PROMOTION.

Forbidden:
- two promotion-owner items simultaneously mutating promotion state;
- parallel mutation of shared canonical authority artifacts;
- A1 promotion while A0/platform-boundary gate is open;
- A4 promotion before cross-discipline contract approval;
- Product promotion based on mismatched revision evidence;
- human participant self-certification of release state;
- eTwin Production promotion before Z0 and final human approval.

## 10. Immediate stop conditions

Stop and preserve evidence when any occurs:

- cross-project leakage;
- cross-discipline leakage;
- wrong SourceVersion/unresolved version mismatch;
- stale ScopeContext accepted as current;
- geometry interpreted as identity;
- source DOC promoted to entity/property DOC without evidence;
- Level-C auto-completion;
- UI/runtime canonical write outside authorized boundary;
- CEW baseline incompatibility;
- TEST_ONLY fixture entering canonical N12 history;
- HVA false success on a safety-critical task;
- participant/reviewer role collapse that materially invalidates human evidence;
- candidate revision drift after HVA;
- required gate evidence missing.

## 11. Human authority integration

Human gates live in machine-readable gate state. Agents cannot mark them satisfied unless the gate contract explicitly names an automated owner, which professional gates must not do.

Gate evidence points to append-only receipts or immutable promoted baseline SHAs.

Human release acceptance and professional engineering decision authority remain different gate types and must not share a generic `approved=true` field without context.

## 12. Current transition state

Existing ETW-A0 preparation on head `36b101ed32cb61263609c84f17b740c2446be9c1` remains valid as historical preparation evidence.

It may not be promoted solely from its prior automated PASS set because:
- `CEW_PROMOTED_BASELINE` is still missing;
- the shared Human Factors model changed after direct observation of the B1.7 instrument;
- A0 Human Factors must be revalidated under participant/reviewer separation before promotion;
- Production smoke and `APPROVE_PLATFORM_BOUNDARY` remain required.

The next technical work item is therefore not ETW-A1. The next admissible programme action is CEW B1 human-acceptance/promotion completion followed by A0 revalidation.
