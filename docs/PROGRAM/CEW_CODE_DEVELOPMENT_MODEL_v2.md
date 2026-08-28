# CEW Code Development Model v2

Status: REQUIRED DEVELOPMENT CONTRACT  
Supersedes for current CEW product delivery: `CEW_CODE_DEVELOPMENT_MODEL_v1.md`  
Governing model: `docs/GOVERNANCE/AI_NATIVE_PRODUCT_AGENCY_OPERATING_MODEL_v1.md`

## 1. Purpose

CEW v2 keeps the proven vertical-slice discipline of v1 but formalizes the separation between:

- product need and implementation;
- technical validation and human evidence;
- deployment and promotion;
- product/runtime state and N12 engineering authority;
- agent preparation and human/professional decision authority.

## 2. Delivery chain

The standard CEW delivery chain is:

`ADMITTED BASELINE -> USER/ENGINEERING NEED -> CAPABILITY -> REPRESENTATIVE JOURNEY -> BOUNDED SLICE -> DEDICATED BRANCH -> PR -> DETERMINISTIC GATES -> INDEPENDENT ASSURANCE -> HUMAN EVALUATION -> RELEASE CANDIDATE -> REQUIRED ENVIRONMENT SMOKE -> RECEIPT -> PROMOTION -> PRODUCTION OBSERVATION`

Not every slice requires every step, but omitted steps must be declared in the slice contract.

## 3. Work starts from capability, not UI

Every slice must declare:

- user / professional role;
- need or engineering job to be done;
- capability being advanced;
- representative journey;
- success outcome;
- critical failure conditions;
- authority boundary;
- data/evidence dependencies;
- release ring required;
- promotion owner.

A route, page, button, model class, parser or agent is an implementation artifact, not an acceptable standalone product goal.

## 4. Branch and PR model

- Every promotable slice starts from an explicit admitted baseline SHA/ref.
- One branch carries one bounded objective.
- Unrelated work is split.
- Parallel preparation is allowed where declared.
- Only one promotion-owner item may mutate promotion state at a time.
- Pull requests preserve reviewable scope and carry the evidence links needed to understand the candidate.
- A future slice may be prepared on a stacked branch but cannot be promoted before its dependencies.

## 5. Same-revision acceptance

For a promotable user-facing revision, the applicable deterministic gates, human acceptance evidence and required Production smoke must refer to the same immutable revision or an explicitly traceable equivalent.

A green gate or human receipt from another SHA does not silently transfer.

## 6. Gate families

CEW may use the following gate families where applicable:

- `DATA_GATE`
- `ENGINEERING_GATE`
- `INTEGRATION_GATE`
- `CONTRACT_GATE`
- `SECURITY_GATE`
- `AUTHORITY_GATE`
- `HUMAN_FACTORS_GATE`
- `HVA_GATE`
- `ACCESSIBILITY_GATE`
- `QA_GATE`
- `PREVIEW_SMOKE`
- `PILOT_GATE`
- `PRODUCTION_SMOKE`
- `OBSERVED_PRODUCTION_GATE`

Gate names do not imply authority. The capability contract states which gates are required and what evidence satisfies them.

## 7. Human evidence lifecycle

Human work is divided into three distinct modes:

### Formative research

Used to understand workflow, terminology, context, uncertainty and design needs. It can change the backlog and design before a candidate exists.

### Evaluative usability / human factors

Used on prototypes or candidates to observe realistic tasks. It produces findings and may block or reshape the slice.

### Release HVA

Used on an immutable candidate to determine whether declared human and safety criteria are satisfied. It never asks the participant to operate internal release governance.

The detailed model is defined in `docs/PROGRAM/CEW_HUMAN_CENTRED_GOVUK_MODEL_v2.md`.

## 8. Participant / reviewer separation

Human acceptance instruments must separate:

- **participant surface** — professional context and realistic tasks only;
- **observer/telemetry layer** — invisible or researcher-facing metrics;
- **reviewer surface** — task evidence, critical errors, comments, mental-model checks and release decision;
- **receipt layer** — machine-readable revision-bound evidence.

Internal IDs, runtime SHA, HVA decision codes and receipt mechanics are not primary participant UI.

## 9. Agentic delivery

Agents operate under least authority.

Every agent must have:
- stable identity;
- bounded mission;
- admitted inputs;
- allowed outputs;
- write scope;
- forbidden writes;
- escalation conditions;
- independent checks where required.

Specialist agents may implement or analyze. They do not become engineering authority.

### Promotion owner

One declared promotion owner submits the result handshake for a promotable slice.

### Support agents

Security, authority audit, contract compatibility, human factors and QA may run independently and concurrently. Their critical findings block promotion but they do not promote.

## 10. Engineering authority boundary

CEW product work must preserve all of the following:

- N12 engineering facts remain owned by `knowledge/CURRENT_STATE.json` and governed canonical artifacts;
- UI state is not engineering truth;
- agent output is not engineering truth;
- machine confidence/consensus does not upgrade epistemic state;
- solver output does not rewrite source evidence;
- missing engineering information remains explicit;
- human observations are never normalized with loss of engineering meaning;
- product tests cannot invent data for continuity;
- professional Level-C decisions remain human-authority-bound where declared.

## 11. Product state dimensions

CEW state must distinguish at minimum:

- technical delivery state;
- human evidence state;
- release/deployment state;
- promotion state;
- engineering/epistemic authority state.

These dimensions may correlate but must not be collapsed into one `COMPLETE` flag.

## 12. Definition of product completion for a slice

A slice is `COMPLETE` only when:

1. the declared capability outcome is achieved;
2. required deterministic gates pass;
3. independent critical assurance findings are resolved;
4. required human evidence exists;
5. required accessibility evidence exists;
6. required Preview/Pilot/Production smoke passes on the admitted revision;
7. no blocking residual remains;
8. a result receipt identifies the baseline, candidate and evidence;
9. applicable human/professional authority is recorded;
10. the orchestrator admits promotion and releases the next dependent item.

## 13. Production and canonical state are distinct

A feature may be deployed in Production while remaining:
- proposal-only;
- read-only;
- noncanonical;
- pilot-limited;
- blocked from professional decision effects.

Production deployment is therefore an operational state, not an authority upgrade.

## 14. Observed Production

For mature capabilities, the strongest product evidence includes real operational observation after release:

- error/incidence rates;
- support/assistance signals;
- completion and abandonment;
- authority/provenance misunderstandings;
- performance/reliability;
- accessibility issues;
- user feedback and rework.

Material regression creates a new work item or reopens a capability even if the previous release passed.

## 15. Decision persistence

Material changes to development, authority or acceptance policy require a decision record. The reason for a change must not remain only in chat history.

## 16. Forbidden patterns

- implementation-first slices with no declared user/professional outcome;
- long-lived branches accumulating unrelated work;
- architecture-only completion without runtime evidence where runtime is required;
- weakening tests to preserve a desired release;
- equating successful build, deploy or CI with service success;
- exposing repository/gate IDs as the primary workflow;
- asking participants to operate release governance;
- visible test telemetry that materially distorts participant behavior without research justification;
- allowing one implementing agent to self-certify all critical assurance;
- silent manual corrections without provenance;
- normalization that loses engineering meaning;
- promotion based on evidence from mismatched revisions;
- promoting future stacked work around an unresolved upstream human or authority gate.
