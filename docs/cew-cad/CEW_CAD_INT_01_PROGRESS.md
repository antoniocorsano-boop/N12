# CEW-CAD-INT-01 Progress Ledger

Base exact SHA: `8a509a19efbb410d56beaaad40e1d5f7766ddcda`

Plan: `docs/superpowers/plans/2026-10-25-cew-cad-int-01-transaction-recovery.md`

## Task 1 — real OCS v2026.42 contract

Causal RED:

- CEW-CAD Qualification #124 / run `40173237917`;
- Task 1–6 PASS;
- Task 7 failed exactly on the three LAB-004 interoperability mismatches:
  - vertices encoded as objects rather than `[x,y]` arrays;
  - missing `result.handles` normalization;
  - missing CallToolResult-like `model_dump()` parsing.

Implemented:

- live `[x,y]` vertex arrays;
- `result.handles` support;
- fail-closed structured/model-dump/content MCP response parsing;
- two legacy test expectations corrected because they encoded the pre-pilot object-vertex assumption.

## Task 2 — mutation-confirmed reconciliation

Causal RED:

- full CEW-CAD suite: 116 tests, exactly one error;
- failure was `AttributeError: ExecutionService.reconcile` in the new recovery contract.

Implemented:

- `ApprovalVerifier.is_consumed()` based on durable consumed-approval claims;
- `ExecutionService.reconcile()`;
- deterministic request-ID lookup through `operation_status`;
- no call to `apply_operation` during recovery;
- exact live identity checks excluding only the expected post-mutation revision transition;
- reconstruction/persistence of a completed Change Receipt only after completed-status, valid post revision and valid changed handles are proven.

## Task 3 — verification/save-only recovery

Causal RED:

- CEW-CAD Qualification #133 / run `40173716549`;
- 118 tests, exactly two errors;
- missing `GatewayRuntimeImpl.recover_approved_changeset`;
- missing lab-runner `recover` command.

Implemented:

- runtime recovery path `reconcile → verify → save_verified_copy`;
- lab `recover` command with no mutation confirmation, private key or arbitrary output path;
- source hash rechecked before/after recovery;
- `mutation_replayed: false` recorded by the recovery runner.

Integrated GREEN checkpoint:

- exact head `5d097aac4cb71ac4ef7947f5b41aee9b67634c03`;
- CEW-CAD Qualification #135 / run `40173803712`: PASS;
- complete suite PASS, compile PASS, native Windows durability PASS.

## Task 3A — approval-age semantics during post-mutation recovery

Causal RED:

- exact head `ac62bea462e0a42ddf7fc00abc0e60d1eb766431`;
- CEW-CAD Qualification #137 / run `40173890935`;
- Task 1–10 PASS;
- full suite: 121 tests, exactly one error, one Windows-only skip;
- only failure: an already durably consumed approval could not be reconciled after its original execution-age window expired.

Ruling and repair:

- approval age remains mandatory before a new mutation may start;
- recovery is permitted only for an already durably consumed approval;
- recovery revalidates exact Changeset binding and Ed25519 signature but does not reapply the original execution-age window because it authorizes no new mutation;
- tampered signatures remain fail-closed;
- unconsumed approvals remain ineligible for recovery.

## Task 4 — internal AI authority boundary

Materialized `docs/cew-cad/CEW_CAD_INTERNAL_AI_BOUNDARY.md`.

The internal AI is explicitly limited to inspection, reasoning, evidence binding, uncertainty handling and structured Changeset proposal. Raw `ocs_execute`, signing, approval consumption, policy relaxation, arbitrary output paths, canonical writes and replay of known-completed mutations remain outside model authority.

The existing MCP surface gate remains unchanged and continues to enforce exactly the governed CEW tools.

## Runbook

`docs/cew-cad/CEW_CAD_01_LIVE_PILOT_RUNBOOK.md` now distinguishes:

- normal `prepare → approve → execute`;
- `FAILED_AFTER_MUTATION → recover` only;
- `AMBIGUOUS_MUTATION_STATE → FAIL`, never replay.

## Governance status

- PR #158 remains Draft and unmerged.
- No live CAD pilot has been executed by CEW-CAD-INT-01.
- No LAB-005 is authorized by this branch.
- No deploy, OpenCADStudio `ADOPT`, CEW-FEM or canonical N12 mutation is authorized.
- Final exact-head qualification and independent review remain required before `READY_FOR_HUMAN_DECISION`.