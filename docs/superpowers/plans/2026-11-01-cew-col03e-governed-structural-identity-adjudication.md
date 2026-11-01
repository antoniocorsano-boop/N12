# CEW-COL-03E Governed Structural Identity Adjudication Implementation Plan

> **Execution mode:** superpowers:executing-plans + test-driven-development. No merge or deploy.

**Goal:** Build deterministic adjudication dossiers for all 22 governed column occurrences without promoting structural identity or canonical geometry.

**Architecture:** Rebuild the already-qualified COL-03B and COL-03C evidence surfaces from the frozen repository sources using their established exact-source chain; validate their frozen state; replay COL-03D from the exact v25 package now preserved in Git; combine those evidence surfaces in a pure COL-03E dossier builder. No expiring Actions artifact is an input to qualification and no duplicate predecessor snapshot is committed.

**Tech stack:** Python 3.12 stdlib, unittest, frozen CEW B01 toolchain, Tesseract 5.3.4, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-01-cew-col03e-governed-structural-identity-adjudication-design.md`

## Global constraints

- Exact qualified predecessor: `df4a0a38d00d18dace597e9ca1cf449edfefca03`.
- Exactly 22 `COL-OCC-0001` … `COL-OCC-0022` subjects.
- Qualified COL-03B lineage SHA: `cfd9382b703d0a974daf63c23dc2b6d3d81eadad`.
- Qualified COL-03C lineage SHA: `a9daa18ddfb56eaf1834ad17f329e2f2db0af72e`.
- Historical v25 package remains exact-source replayable and evidence-only.
- No automatic `COL-OCC ↔ N###` bridge.
- Historical `VER` is not current structural truth.
- All structural/canonical authority flags remain false.
- No merge, deploy, M0-S, M0-G, G2C/G3, EdiLus export or canonical write.

## Evidence reality frozen by qualification history

- COL-03B: 22 occurrences; 20 with no documentary candidate; `COL-OCC-0001 → 4` and `COL-OCC-0015 → 30` are single-channel candidates only.
- COL-03C: 22/22 `EVALUATED_NO_MATCH`, zero cross-document hypotheses, zero resolved identities.
- COL-03D: 27 historical TAV.5↔TAV.7 rows are recovered, but their own note states `associazione al singolo pilastro non ancora dimostrata`; the historical material remains unbound to `COL-OCC-*`.

## Review focus

- A historical `VER` row with a non-demonstration note must never make a dossier review-ready.
- `N###` rows with matching coordinates/order/shape remain unbound without an explicit governed bridge.
- Duplicate/ambiguous candidates classify `AMBIGUOUS`, never first-match.
- A unique candidate with incomplete provenance remains `INSUFFICIENT_EVIDENCE`.
- Completing a dossier does not resolve structural identity.

---

### Task 1 — Validate replayed COL-03B/C predecessor boundary

**Files:**
- `tests/cew_col03e/test_predecessor_snapshots.py`
- `experiments/cew_col03e/predecessor.py`

- [x] Acquire RED: validator missing while all new predecessor contracts fail causally.
- [x] Implement exact 22-occurrence validation, frozen documentary candidate mapping, zero COL-03C match/hypothesis state, lineage check and authority fail-closed checks.
- [x] GREEN: 5/5 predecessor contracts PASS on `cc973fe8a7da6592620856e9aff8ce1e13252491`.
- [x] Architecture correction: do not persist duplicate Actions snapshots; rebuild predecessor evidence from frozen repository sources in the final workflow.

### Task 2 — Build pure adjudication dossiers

**Files:**
- `tests/cew_col03e/test_adjudication.py`
- `experiments/cew_col03e/adjudication.py`

- [x] Acquire RED: 5 predecessor tests PASS; four dossier contracts fail only because builder/classifier are absent.
- [x] Implement fail-closed readiness precedence:
  `CONTRADICTED > AMBIGUOUS > BLOCKED_BY_HISTORICAL_SEMANTICS > INSUFFICIENT_EVIDENCE > READY_FOR_HUMAN_REVIEW`.
- [x] Keep historical evidence `UNBOUND` unless an explicit governed bridge already exists.
- [x] Preserve documentary candidates `4` and `30` without promotion.
- [x] Current real evidence contract: 22/22 dossiers classify `INSUFFICIENT_EVIDENCE`.
- [x] GREEN: 9/9 COL-03E contracts PASS on `9805300f446561f8f6bc40ccbc7ac87a6aac1fb9`.

### Task 3 — Build the three governed COL-03E artifacts

**Files:**
- `tests/cew_col03e/test_exact_source.py`
- `experiments/cew_col03e/exact_source.py`

**Outputs:**
- `identity-adjudication-dossiers.json`
- `identity-adjudication-readiness.json`
- `identity-adjudication-closure.json`

- [x] Acquire RED: prior 9 tests PASS; three exact-source contracts fail only because builder/writer are absent.
- [x] Implement exact predecessor SHA gate, deterministic three-artifact writer and authority closure.
- [x] Separate `adjudication_dossiers_complete=true` from `any_identity_resolved=false`.
- [x] Freeze current resolution blockers as `NO_GOVERNED_HISTORICAL_BRIDGE` and `NO_TAV07_CROSS_DOCUMENT_MATCH`.
- [x] GREEN: 12/12 COL-03E contracts PASS on `6a3e44ad2512bda9ff06c563982f9cc0f2bb5fa2`.

### Task 4 — Exact-SHA end-to-end qualification

**File:** `.github/workflows/validate-cew-col03e-governed-structural-identity-adjudication.yml`

- [x] Exact candidate checkout + qualified COL-03D ancestry gate.
- [x] Reuse frozen COL-03C exact-source chain: Tesseract 5.3.4, locked B01 toolchain, archive commit `78c20a52...`, registration commit `643dc893...`.
- [x] Rebuild COL-02 → COL-03A → COL-03B → COL-03C from repository sources.
- [x] Replay COL-03D from the exact v25 Git package.
- [x] Build COL-03E and assert 22 dossiers, 0 identities resolved, 0 silent historical bindings and all authority flags false.
- [x] Add COL-03D and COL-03C regression suites and evidence upload.
- [ ] Obtain fresh SUCCESS on the final exact SHA and record artifact receipt.

### Task 5 — Final independent review checkpoint

- [ ] Confirm predecessor PR #181 exact head/base remains `df4a0a38d00d18dace597e9ca1cf449edfefca03`.
- [ ] Compare successor against exact base; scope must be COL-03E design/plan/code/tests/workflow only.
- [ ] Confirm no review threads/findings remain.
- [ ] Confirm all qualification runs are fresh on the exact final SHA.
- [ ] Update PR #183 receipt with current evidence.
- [ ] Leave PR Draft/open/unmerged and stop before human receipt acceptance or identity promotion.
