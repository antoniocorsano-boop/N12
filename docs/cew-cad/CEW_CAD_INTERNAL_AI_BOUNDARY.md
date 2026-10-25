# CEW-CAD — Internal AI Authority Boundary

**Status:** NORMATIVE FOR CEW-CAD-INT-01  
**Applies to:** any LLM/agent/runtime used inside Civil Existing Workflow, including ChatGPT, Codex, OpenCode or future local/remote models.

## Principle

The AI is a **cognitive proposal layer**, not the CAD transaction authority.

OpenCADStudio is a subordinated CAD execution engine behind the CEW Gateway. Neither the model nor its host may bypass the Gateway to obtain broader authority.

## AI-authorized capabilities

The internal AI may, through governed CEW interfaces:

- read governed CAD status;
- inspect/query entities;
- request measurements;
- request target-aware audits;
- request captures/diffs;
- reason over CEW evidence, claims, decisions and epistemic states;
- classify/document uncertainty;
- propose a structured Changeset;
- explain a proposed change and its evidence bindings;
- diagnose a failed transaction from persisted evidence;
- request a **non-mutating recovery assessment** after a confirmed mutation.

These are cognitive or read/proposal activities. None grants write authority.

## AI-forbidden capabilities

The internal AI must never be given direct authority to:

- invoke raw `ocs_execute`;
- execute arbitrary CAD commands;
- choose arbitrary filesystem output paths;
- access or use an Ed25519 private signing key;
- sign its own Approval Receipt;
- mark its own proposal as human-approved;
- consume an approval outside `ApprovalVerifier`;
- relax `CEW_CAD_POLICY_v1.json` or fail-closed conditions to make a run pass;
- overwrite an existing CAD artifact;
- write to canonical, baseline or issued N12 paths;
- promote an artifact or tool to canonical/`ADOPT` status;
- silently convert `INF`, `RIF`, `ND` or other uncertain knowledge into documentary fact;
- re-execute a mutation that is already proven `completed` by its deterministic request ID.

## Authority chain

The mandatory mutation chain is:

`Evidence → AI/logic proposal → governed Changeset → human external signature → ApprovalVerifier → deterministic ExecutionService → Change Receipt → VerificationService → Verified Copy → human promotion decision`

No model may shortcut this chain.

## Transaction-state rule

A CAD transaction has materially different failure classes:

- **FAILED_BEFORE_MUTATION** — no mutation is proven; a new approved execution may be considered under normal rules.
- **MUTATION_CONFIRMED** — OCS proves the deterministic request completed and the approval was already durably consumed.
- **FAILED_AFTER_MUTATION** — mutation is confirmed but verification/save did not complete.
- **AMBIGUOUS_MUTATION_STATE** — completion cannot be proven; fail closed.
- **VERIFIED** — deterministic technical verification passed.
- **SAVED** — a new verified copy was created without overwriting the source.

For `FAILED_AFTER_MUTATION`, the only permitted automatic continuation is **reconciliation → verification → verified save**. The mutation must not be replayed.

## Recovery authority

Recovery is not a second execution approval. It is a non-mutating reconciliation of an operation already executed under a valid, durably consumed human approval.

Recovery must prove:

1. exact Changeset identity and digest;
2. valid signed Approval binding;
3. durable prior consumption of that approval;
4. deterministic request ID;
5. OCS `operation_status == completed`;
6. valid post-mutation revision and changed-entity handles;
7. current session/document/path/source hash/capabilities still match the governed identity;
8. current revision equals the proven post-mutation revision.

Only then may CEW reconstruct/persist the Change Receipt and continue to deterministic verification and save.

Recovery must never call the mutating `apply` path and must never consume/sign a new approval merely to finish verification of the already completed mutation.

## Model interchangeability

The boundary is model-agnostic. A future local model, hosted model, ChatGPT, Codex or OpenCode may be substituted behind the same cognitive interface without changing CAD authority.

The safety property therefore belongs to CEW architecture, not to the behavior or trustworthiness of a particular AI provider.

## Current enforcement evidence

The existing MCP surface contract tests already require the exact governed tool set and reject exposure of raw commands, arbitrary paths and signing material. CEW-CAD-INT-01 does not broaden that model-facing mutation authority.

A future AI-specific implementation must add tests around its own proposal interface, but it may not weaken the existing MCP boundary.