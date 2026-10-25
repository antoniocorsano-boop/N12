# CEW-CAD-INT-01 — Recovery Ruling

## Ruling

The original plan assumed recovery would always start from a persisted completed Change Receipt. LAB-004 demonstrates a stricter failure class: OCS may complete the mutation while the governed process fails before the Change Receipt is durably available.

Therefore recovery MUST also cover the crash window between OCS completion and Change Receipt persistence.

## Required proof before reconstructing mutation-confirmed state

Recovery may reconstruct a completed Change Receipt only when all conditions hold:

1. the original Changeset digest is valid;
2. the original signed Approval verifies against that Changeset;
3. the Approval is already durably recorded as consumed — recovery never consumes it again;
4. the deterministic request ID derived from the Changeset is queried through `operation_status`;
5. operation status is exactly `completed`;
6. returned revision is an integer strictly greater than the approved base revision;
7. returned changed-entity identifiers are a non-empty valid string list;
8. current live CAD session/document/path/source hash/capabilities still match the Changeset identity;
9. current live revision equals the reconciled post-mutation revision.

If any condition fails, recovery is fail-closed and performs no mutation and no save.

## Consequence

`ExecutionService` gains a non-mutating reconciliation path. The lab `recover` path may use the Approval artifact as evidence, but it MUST NOT call `ApprovalVerifier.consume()` or `CADAdapter.apply_operation()`.

This ruling supersedes the narrower recovery wording in the initial INT-01 plan where the two conflict.