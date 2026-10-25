# CEW-CAD-INT-01 — Recovery Ruling

## Ruling

The original plan assumed recovery would always start from a persisted completed Change Receipt. LAB-004 demonstrates a stricter failure class: OCS may complete the mutation while the governed process fails before the Change Receipt is durably available.

Therefore recovery MUST also cover the crash window between OCS completion and Change Receipt persistence.

## Required proof before reconstructing mutation-confirmed state

Recovery may reconstruct a completed Change Receipt only when all conditions hold:

1. the original Changeset digest is valid;
2. the original signed Approval verifies against that Changeset;
3. the Approval is already durably recorded as consumed — recovery never consumes it again;
4. the durable consumed claim binds to the **exact Approval Receipt digest and exact Changeset digest**, not merely to a reusable `approval_id`;
5. the deterministic request ID derived from the Changeset is queried through `operation_status`;
6. operation status is exactly `completed`;
7. returned revision is an integer strictly greater than the approved base revision;
8. returned changed-entity identifiers are a non-empty valid string list;
9. current live CAD session/document/path/source hash/capabilities still match the Changeset identity;
10. current live revision equals the reconciled post-mutation revision.

If any condition fails, recovery is fail-closed and performs no mutation and no save.

## Legacy consumed claims

A historical consumed-approval claim containing only `approval_id` remains sufficient to prevent that identifier from being consumed again. It is **not sufficient evidence for recovery**, because it cannot prove which exact signed Approval artifact crossed the original mutation boundary.

This deliberately means that recovery is available only for transactions whose durable consumption record contains the exact approval and Changeset digests required by CEW-CAD-INT-01.

## Approval age

The approval-age window remains mandatory before a new mutation starts. Once the exact approval has already been durably consumed and bound as above, recovery does not reapply that original age window because it authorizes no new mutation. Signature and binding checks remain mandatory.

## Consequence

`ExecutionService` gains a non-mutating reconciliation path. The lab `recover` path may use the Approval artifact as evidence, but it MUST NOT call `ApprovalVerifier.consume()` or `CADAdapter.apply_operation()`.

This ruling supersedes the narrower recovery wording in the initial INT-01 plan where the two conflict.