# CEW-COL-03E Governed Structural Identity Adjudication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic adjudication dossiers for all 22 governed column occurrences without promoting structural identity or canonical geometry.

**Architecture:** Preserve the exact qualified COL-03B and COL-03C evidence snapshots in-repository with pinned workflow/artifact digests, replay COL-03D historical evidence from exact package bytes, and combine the three evidence surfaces in a pure COL-03E dossier builder. Readiness remains fail-closed; no human receipt is consumed and no identity is promoted.

**Tech Stack:** Python 3.12 stdlib, unittest, GitHub Actions, repository-preserved JSON evidence snapshots.

**Spec:** `docs/superpowers/specs/2026-11-01-cew-col03e-governed-structural-identity-adjudication-design.md`

## Global Constraints

- Exact predecessor: `df4a0a38d00d18dace597e9ca1cf449edfefca03`.
- Exactly 22 `COL-OCC-0001` … `COL-OCC-0022` subjects.
- Qualified COL-03B source SHA: `cfd9382b703d0a974daf63c23dc2b6d3d81eadad`.
- Qualified COL-03C source SHA: `a9daa18ddfb56eaf1834ad17f329e2f2db0af72e`.
- COL-03B artifact: run `41239465886`, artifact `13057251710`, digest `sha256:aaddc342e81983bbbd4f164a8e5c70dcbc14de5626bfc821ba7489b576821391`.
- COL-03C artifact: run `41244244236`, artifact `13058716773`, digest `sha256:468108dc107d813e9d4759a208560b566d7395b2db6eedf07787375238a91a2f`.
- Historical v25 package remains exact-source replayable and evidence-only.
- No automatic `COL-OCC ↔ N###` bridge.
- All structural/canonical authority flags remain false.
- No merge, deploy, M0-S, M0-G, G2C/G3, EdiLus export or canonical write.

## Review Focus

- A historical `VER` row with “associazione al singolo pilastro non ancora dimostrata” must never make a dossier review-ready.
- `N###` rows with matching coordinates must remain unbound without an explicit governed bridge.
- Duplicate/ambiguous candidates must classify `AMBIGUOUS`, never pick first-by-order.
- A unique candidate with incomplete provenance must remain `INSUFFICIENT_EVIDENCE`.
- Any authority drift in predecessor snapshots or produced dossiers must fail closed.

---

### Task 1: Preserve qualified COL-03B/C evidence snapshots

**Files:**
- Create: `archive/qualified_evidence/col03b/manifest.json`
- Create: `archive/qualified_evidence/col03b/documentary-identity-evidence-ledger.json`
- Create: `archive/qualified_evidence/col03b/documentary-identity-hypotheses.json`
- Create: `archive/qualified_evidence/col03b/documentary-identity-reconciliation.json`
- Create: `archive/qualified_evidence/col03b/documentary-identity-evidence-closure.json`
- Create: `archive/qualified_evidence/col03c/manifest.json`
- Create: `archive/qualified_evidence/col03c/cross-document-evidence-ledger.json`
- Create: `archive/qualified_evidence/col03c/cross-document-reconciliation.json`
- Create: `archive/qualified_evidence/col03c/cross-document-evidence-closure.json`
- Create: `archive/qualified_evidence/col03c/derived-reference-quality.json`
- Create: `archive/qualified_evidence/col03c/source-materialization-manifest.json`
- Test: `tests/cew_col03e/test_predecessor_snapshots.py`

**Interfaces:**
- Consumes: exact downloaded workflow artifacts named in Global Constraints.
- Produces: `load_qualified_predecessor_snapshots() -> dict[str, dict]` in Task 2.

- [ ] **Step 1: Write failing snapshot-contract tests** asserting exact source SHAs, artifact IDs/digests, exact file SHA-256 values, COL-03B 22 occurrences with candidate distribution `20×0 + 2×1`, and COL-03C 22 occurrences all `EVALUATED_NO_MATCH` with zero hypotheses.
- [ ] **Step 2: Run** `python -m unittest tests.cew_col03e.test_predecessor_snapshots -v` and verify causal failure because snapshots/loader do not yet exist.
- [ ] **Step 3: Materialize exact JSON bytes** from the qualified artifacts and write manifests containing run ID, artifact ID, artifact digest, source SHA and per-file SHA-256.
- [ ] **Step 4: Implement loader/verification** in `experiments/cew_col03e/predecessor.py`; reject missing files, digest drift, occurrence drift and authority drift.
- [ ] **Step 5: Re-run test** and expect PASS.
- [ ] **Step 6: Commit** snapshot + verifier slice.

### Task 2: Build pure adjudication dossiers

**Files:**
- Create: `experiments/cew_col03e/adjudication.py`
- Create: `tests/cew_col03e/test_adjudication.py`

**Interfaces:**
- Consumes: verified COL-03B/C snapshots; COL-03D `historical-derived-data-quality.json` payload.
- Produces: `build_adjudication_dossiers(*, col03b_ledger: dict, col03c_ledger: dict, historical_quality: dict, predecessor_sha: str) -> list[dict]`.

- [ ] **Step 1: Write RED tests** for exact 22 dossiers, deterministic ordering/digests, readiness precedence, explicit-unbound historical context, no coordinate/`N###` bridge, and all authority flags false.
- [ ] **Step 2: Run** `python -m unittest tests.cew_col03e.test_adjudication -v`; expect failures for missing builder.
- [ ] **Step 3: Implement minimal builder** with readiness states `READY_FOR_HUMAN_REVIEW`, `AMBIGUOUS`, `CONTRADICTED`, `BLOCKED_BY_HISTORICAL_SEMANTICS`, `INSUFFICIENT_EVIDENCE` and fail-closed precedence from the spec.
- [ ] **Step 4: Assert current real evidence outcome**: no case may become review-ready solely from historical rows; current COL-03C no-match state remains machine-visible.
- [ ] **Step 5: Run tests** and expect PASS.
- [ ] **Step 6: Commit** dossier-builder slice.

### Task 3: Exact-source COL-03E evidence build

**Files:**
- Create: `experiments/cew_col03e/exact_source.py`
- Create: `tests/cew_col03e/test_exact_source.py`

**Interfaces:**
- Consumes: `load_qualified_predecessor_snapshots()`, `build_adjudication_dossiers(...)`, `experiments.cew_col03d.exact_source.build_exact_source_recovery(...)`.
- Produces exactly:
  - `identity-adjudication-dossiers.json`
  - `identity-adjudication-readiness.json`
  - `identity-adjudication-closure.json`

- [ ] **Step 1: Write RED tests** for exact output surface, byte-deterministic replay, current readiness counts, predecessor lineage and authority closure.
- [ ] **Step 2: Run** `python -m unittest tests.cew_col03e.test_exact_source -v`; expect causal failure.
- [ ] **Step 3: Implement exact-source builder** that replays COL-03D from repository package/transport, verifies COL-03D closure, loads pinned COL-03B/C snapshots, builds dossiers twice with reversed set-like inputs, and rejects nondeterminism.
- [ ] **Step 4: Persist outputs** only under `evidence/cew-col03e/` with deterministic JSON serialization.
- [ ] **Step 5: Run COL-03E tests** and expect PASS.
- [ ] **Step 6: Commit** exact-source slice.

### Task 4: Exact-SHA qualification workflow

**Files:**
- Create: `.github/workflows/validate-cew-col03e-governed-structural-identity-adjudication.yml`

**Interfaces:**
- Consumes: exact candidate SHA and repository evidence/materialization.
- Produces: exact-SHA qualification receipt + uploaded `evidence/cew-col03e/` artifact.

- [ ] **Step 1: Add workflow** triggered only on the stacked COL-03E PR/base and COL-03E paths.
- [ ] **Step 2: Verify exact checkout** and `git merge-base --is-ancestor df4a0a38... HEAD`.
- [ ] **Step 3: Run all COL-03E unit contracts**, then COL-03D and COL-03C regression suites.
- [ ] **Step 4: Build exact-source evidence** and assert exactly 22 dossiers, no authority promotion, no silent `N###` bridge, deterministic closure and `adjudication_dossiers_complete=true`.
- [ ] **Step 5: Upload only** `evidence/cew-col03e/`.
- [ ] **Step 6: Record run/artifact receipt** in the Draft PR body.

### Task 5: Final independent review checkpoint

**Files:** none unless review finds a defect.

- [ ] Confirm predecessor PR #181 exact head used as base remains unchanged.
- [ ] Compare successor against exact base; scope must be only COL-03E snapshots/spec/plan/code/tests/workflow.
- [ ] Confirm no review threads/findings remain.
- [ ] Confirm all qualification runs are fresh on the exact final SHA.
- [ ] Leave PR Draft/open/unmerged and stop before human receipt acceptance or identity promotion.
