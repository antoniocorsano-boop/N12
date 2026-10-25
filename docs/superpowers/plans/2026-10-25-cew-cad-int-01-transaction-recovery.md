# CEW-CAD-INT-01 Transaction Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make CEW-CAD recover deterministically after a mutation has already succeeded, while codifying the real OpenCADStudio v2026.42 contract observed in LAB-004 and preserving a strict internal-AI boundary.

**Architecture:** Vendor-specific OCS translation stays inside `OpenCADStudioAdapter`; domain execution persists a completed mutation receipt before downstream verification; recovery starts only from that persisted receipt and never re-enters mutation. Future AI is constrained to inspection/proposal and cannot call raw mutation primitives.

**Tech Stack:** Python 3.12, pytest/unittest-style existing CEW test suite, MCP client, OpenCADStudio v2026.42 contract, existing ReceiptStore/ArtifactRepository.

**Spec:** `docs/superpowers/specs/2026-10-25-cew-cad-int-01-transaction-recovery-design.md`

## Global Constraints

- Branch from exact repaired candidate `8a509a19efbb410d56beaaad40e1d5f7766ddcda`.
- No LAB-005 live execution.
- No canonical/baseline/issued N12 mutation.
- No merge, deploy, CEW-FEM, or OpenCADStudio `ADOPT` promotion.
- Human approval remains external, durable and single-use.
- Recovery is verification/save-only and must never call `ExecutionService.apply`.
- Unknown or ambiguous OCS response shapes fail closed.

## Review Focus

- OCS response has `result.handles` but no `changes.created`: normalize exactly once and reject empty/non-string handles.
- CallToolResult exposes data through `model_dump()` instead of direct dict/structured content: parse only known structured forms.
- Process fails after OCS mutation but before verification: persisted Change Receipt remains sufficient to recover without mutation.
- Live CAD revision differs from persisted `revision_after`: recovery fails closed and never saves.
- Re-running recovery after a verified copy already exists: existing output collision remains fail-closed; no overwrite.

---

### Task 1: Codify real OCS v2026.42 interoperability

**Files:**
- Modify: `cew_cad_gateway/adapters/opencadstudio.py`
- Test: `tests/cew_cad_gateway/test_opencadstudio_mutation_compiler.py`
- Test: `tests/cew_cad_gateway/test_opencadstudio_adapter.py`

**Interfaces:**
- Consumes: `CreatePolyline`, existing `_mapping`, existing mutation normalization.
- Produces: typed `entities_create` request with `vertices=[[x,y], ...]`; normalized CEW result from `result.handles`; safe parsing of CallToolResult-like objects.

- [ ] **Step 1: Write failing tests** for array vertices, `result.handles`, and model-dump/content MCP response parsing.
- [ ] **Step 2: Run focused adapter tests and verify RED** for those three LAB-004 mismatches.
- [ ] **Step 3: Implement minimal adapter changes** without altering CEW domain contracts.
- [ ] **Step 4: Run focused adapter tests and verify GREEN.**
- [ ] **Step 5: Run the complete CEW-CAD suite and confirm no regression.**
- [ ] **Step 6: Commit** `fix: align OCS adapter with live v2026.42 contract`.

### Task 2: Persist mutation-confirmed transaction state

**Files:**
- Modify: `cew_cad_gateway/types.py`
- Modify: `cew_cad_gateway/execution.py`
- Modify: `cew_cad_gateway/receipts.py` only if required by existing typed-load conventions
- Modify: `cew_cad_gateway/artifacts.py` only if required for retrieval
- Test: `tests/cew_cad_gateway/test_execution.py`
- Test: `tests/cew_cad_gateway/test_receipts.py`

**Interfaces:**
- Consumes: validated normalized mutation result and existing `ChangeReceipt`.
- Produces: durable mutation-confirmed evidence bound to changeset/approval/request/revisions/handles before verification begins.

- [ ] **Step 1: Write failing tests** proving a successful mutation persists the completed Change Receipt/checkpoint before any later verification can fail.
- [ ] **Step 2: Verify RED** because no explicit mutation-confirmed recovery contract exists.
- [ ] **Step 3: Add the smallest typed checkpoint/receipt contract necessary** and persist it atomically with existing receipt infrastructure.
- [ ] **Step 4: Verify GREEN** and ensure ambiguous/incomplete responses never create the checkpoint.
- [ ] **Step 5: Run full CEW-CAD suite.**
- [ ] **Step 6: Commit** `feat: persist mutation-confirmed CAD transaction state`.

### Task 3: Add verification-only deterministic recovery

**Files:**
- Modify: `cew_cad_gateway/runtime.py`
- Modify: `scripts/cew_cad_lab_acceptance.py`
- Modify: `cew_cad_gateway/artifacts.py` if typed change lookup requires it
- Test: `tests/cew_cad_gateway/test_end_to_end_fake.py`
- Test: `tests/cew_cad_gateway/test_lab_acceptance_runner.py`
- Test: `tests/cew_cad_gateway/test_verification.py`

**Interfaces:**
- Consumes: stored Changeset and completed Change Receipt from Task 2.
- Produces: `recover_verified_changeset(changeset_id, change_id)` and lab `recover` path that perform verification/save only.

- [ ] **Step 1: Write failing tests** proving recovery performs zero mutation calls, verifies against `revision_after`, and refuses missing/non-completed/stale state.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement runtime recovery** by loading existing artifacts, calling `VerificationService.verify`, then `save_verified_copy` only after PASS.
- [ ] **Step 4: Add lab-runner `recover` command** with no approval ID and no mutation confirmation argument.
- [ ] **Step 5: Verify GREEN** on focused recovery tests.
- [ ] **Step 6: Run full CEW-CAD suite.**
- [ ] **Step 7: Commit** `feat: recover verified CAD transaction without remutation`.

### Task 4: Freeze the internal-AI authority boundary

**Files:**
- Create: `docs/cew-cad/CEW_CAD_INTERNAL_AI_BOUNDARY.md`
- Modify: `docs/cew-cad/CEW_CAD_01_LIVE_PILOT_RUNBOOK.md`
- Test: `tests/cew_cad_gateway/test_mcp_surface.py`

**Interfaces:**
- Consumes: existing nine governed CEW tools and recovery contract.
- Produces: explicit authority boundary: internal AI can inspect/measure/audit/capture/propose; execution remains deterministic and human-approved.

- [ ] **Step 1: Add a failing contract test** if any raw mutation/signing surface is exposed to the model-facing MCP API.
- [ ] **Step 2: Verify RED only if the boundary is currently violated; otherwise record that the existing gate already enforces it and do not fabricate a failure.**
- [ ] **Step 3: Document the boundary and update the runbook** with `FAILED_AFTER_MUTATION → recover`, explicitly forbidding repeat execution.
- [ ] **Step 4: Run MCP-surface and complete CEW-CAD suite.**
- [ ] **Step 5: Commit** `docs: freeze CEW internal AI authority boundary`.

### Task 5: Qualification and review

**Files:**
- Modify: `docs/cew-cad/CEW_CAD_01_QUALIFICATION_REPORT.md` or create a dedicated INT-01 qualification note if separation is clearer.

**Interfaces:**
- Consumes: Tasks 1–4 exact branch head and CI evidence.
- Produces: exact-SHA qualification result and a human decision point for a future LAB-005 only after PASS.

- [ ] **Step 1: Run CEW-CAD qualification, compile and Gate Authority checks on exact head.**
- [ ] **Step 2: Record exact workflow/run identities and test counts.**
- [ ] **Step 3: Obtain independent whole-branch review.**
- [ ] **Step 4: Resolve any blocking findings through causal RED→GREEN cycles.**
- [ ] **Step 5: Leave branch/PR unmerged and classify `READY_FOR_HUMAN_DECISION` only if all gates pass.**