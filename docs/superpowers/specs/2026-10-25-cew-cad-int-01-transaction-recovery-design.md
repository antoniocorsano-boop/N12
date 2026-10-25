# CEW-CAD-INT-01 — Transaction Recovery and Internal Intelligence Boundary

## Intent

CEW-CAD-LAB-004 proved that OpenCADStudio can perform the authorized typed mutation on a disposable DWG, but the governed runner failed after the mutation had already succeeded. CEW therefore needs an explicit post-mutation transaction state and a recovery path that can continue verification/save without re-executing the mutation or re-consuming approval.

This increment also establishes the architectural boundary for future CEW internal AI: AI may inspect state, reason over evidence, and propose structured changesets, but it never directly invokes `ocs_execute`, signs approvals, relaxes policy, or performs canonical writes.

## Goals

1. Encode the real OCS v2026.42 interoperability observed in LAB-004:
   - `entities_create.vertices` uses `[x, y]` arrays;
   - mutation handles may be returned as `result.handles`;
   - MCP responses may arrive as CallToolResult-like objects requiring structured/content/model-dump extraction.
2. Persist a durable mutation-confirmed checkpoint immediately after OCS confirms a successful mutation and before downstream verification.
3. Distinguish failures before mutation from failures after mutation.
4. Allow a deterministic `verification-only` recovery from a previously persisted completed Change Receipt.
5. Forbid a second mutation once the transaction is known to be mutation-confirmed.
6. Preserve all existing governance constraints: disposable working-copy only, no canonical N12 mutation, no merge/deploy/adoption authorization, human approval remains external and single-use.

## Non-goals

- No LAB-005 execution in this increment.
- No OpenCADStudio promotion to `ADOPT`.
- No general autonomous CAD agent.
- No direct model access to raw `ocs_execute`.
- No weakening of revision, session, capability, source-hash, approval, or workspace checks.
- No automatic recovery from ambiguous mutation state.

## Architecture

### 1. Adapter boundary

`OpenCADStudioAdapter` owns vendor-specific protocol translation. CEW domain code continues to use the stable normalized mutation result:

- `status`
- `revision`
- `changed_entities`

The adapter accepts only known OCS response forms and fails closed otherwise.

### 2. Transaction state

Introduce `CADTransactionCheckpoint` with schema `cew.cad.transaction-checkpoint.v1` and terminally ordered states:

- `APPROVED`
- `MUTATION_CONFIRMED`
- `VERIFIED`
- `SAVED`
- `FAILED_BEFORE_MUTATION`
- `FAILED_AFTER_MUTATION`
- `AMBIGUOUS_MUTATION_STATE`

For this increment, the critical persisted checkpoint is `MUTATION_CONFIRMED`, bound to:

- changeset SHA-256;
- approval SHA-256;
- deterministic request ID;
- revision before;
- revision after;
- changed entity handles.

A checkpoint is written immediately after the normalized OCS response passes execution validation and at the same logical point as the Change Receipt. It must exist before any technical verification begins.

### 3. Recovery contract

`GatewayRuntimeImpl.recover_verified_changeset(changeset_id, change_id)`:

- loads the original Changeset and persisted Change Receipt;
- never calls `ExecutionService.apply`;
- verifies the live CAD state against `change.revision_after` through `VerificationService.verify`;
- if PASS, continues with normal `save_verified_copy`;
- if the persisted change is absent or not `COMPLETED`, fails closed;
- if live state no longer matches the mutation-confirmed state, fails with verification/recovery error and does not mutate CAD.

The laboratory runner gains a `recover` command that uses this path. It does not accept an approval ID or mutation confirmation token because recovery is explicitly non-mutating.

### 4. Internal AI boundary

Future CEW internal intelligence sits above `InspectionService` and `ChangesetService` only. Its permitted outputs are proposals, classifications, evidence links and explanations. Mutation remains under deterministic ExecutionService + external human approval + VerificationService.

## Safety and governance invariants

- Approval is consumed exactly once before mutation.
- A known successful mutation is never repeated as a retry mechanism.
- `request_id` stays deterministic for ambiguity resolution.
- Source DWG hash remains an invariant; session memory may be dirty while the source file stays unchanged.
- Recovery may verify/save only; it cannot mutate.
- Ambiguous OCS completion never becomes `MUTATION_CONFIRMED` without deterministic evidence.
- Every vendor-specific compatibility rule belongs in the adapter and is regression-tested.

## Acceptance criteria

1. RED tests reproduce all three LAB-004 real-contract mismatches.
2. Adapter emits `[x, y]` vertices and normalizes `result.handles`.
3. MCP CallToolResult-like response objects normalize without bypassing fail-closed validation.
4. A successful mutation persists a Change Receipt/checkpoint before verification.
5. Recovery from a completed persisted Change Receipt executes zero mutation calls.
6. Recovery verifies current revision equals `revision_after`, then may save a new verified copy.
7. Recovery refuses missing/non-completed change receipts and state drift.
8. Existing CEW-CAD qualification suite remains green.
9. No new live pilot is executed by this change.