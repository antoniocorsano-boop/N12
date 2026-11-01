# CEW-COL-03D-BIN-01 Exact Package Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans task-by-task with TDD. No merge or deploy.

**Goal:** Preserve the exact historical v25 ZIP in Git and make COL-03D fully repository-replayable without promoting structural authority.

**Architecture:** Commit the exact ZIP as an opaque binary blob at the already frozen repository path. Reuse `verify_package_source()` as the byte/ZIP verifier, change `exact_source` to derive the package witness from that checked-out file, and tighten the COL-03D workflow so final qualification becomes true only from exact repository bytes.

**Tech Stack:** Python 3.12 stdlib, unittest, Git binary blob/tree APIs, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-01-cew-col03d-bin01-exact-package-replay-design.md`

## Global Constraints

- Parent checkpoint: `89c423bd4f1a95ca7e000eed966eb26626547c2f`.
- Package SHA-256: `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`.
- Package size: `5,345,286`; members: `91`.
- Exact binary only; no raster regeneration or package rewrite.
- All downstream authority flags remain false.
- No merge, deploy, M0-S, M0-G, G2C/G3 or canonical write.

## Review Focus

- Missing or altered repository ZIP must fail closed.
- Same-name/different-bytes package must be `PROVENANCE_MISMATCH`.
- `exact_source` must not silently fall back to the external witness once BIN-01 is active.
- Existing eight-member transport/replay must remain unchanged and green.
- Final closure may change only replay/materialization/qualification fields; authority closures remain false.

---

### Task 1: RED contract for exact repository package

**Files:**
- Modify: `tests/cew_col03d/test_package_source.py`
- Modify: `tests/cew_col03d/test_exact_source_writer.py`

- [ ] Assert the frozen repository ZIP exists, verifies to exact digest/size/91 members, and reports `repository_materialized = true`.
- [ ] Assert exact-source closure reports repository materialized/replayable and no blocker.
- [ ] Run exact COL-03D unit workflow and observe causal RED because package bytes and witness behavior are not yet present.

### Task 2: Preserve exact binary package

**Files:**
- Add binary: `archive/historical_packages/v25/Ariano_Irpino_DXF_strutturale_v25.zip`

- [ ] Commit the Library-recovered exact bytes as a Git binary blob.
- [ ] Verify blob/check-out identity through workflow SHA/size/ZIP checks.

### Task 3: GREEN exact-source witness

**Files:**
- Modify: `experiments/cew_col03d/package_source.py`
- Modify: `experiments/cew_col03d/exact_source.py`

- [ ] Freeze `repository_materialized = true` in the package contract now that the exact source exists.
- [ ] Replace the external witness stub with `verify_package_source(Path(repository_path))` and add `verification_state=MATERIALIZED_VERIFIED`, `exact_source_replayable=true` only after verification.
- [ ] Run COL-03D tests; expect GREEN.

### Task 4: Exact-SHA workflow qualification

**Files:**
- Modify: `.github/workflows/validate-cew-col03d-historical-package-recovery.yml`

- [ ] Permit the stacked successor base branch.
- [ ] Add direct SHA/size/ZIP/member-count assertions against the checked-out package before evidence generation.
- [ ] Change closure assertions to repository materialized/replayable/qualification complete true and blocker list empty.
- [ ] Run COL-03C regression and all COL-03D contracts on exact successor SHA.
- [ ] Record workflow run/artifact and Repository Memory Gate results.

### Task 5: Final review/checkpoint

- [ ] Confirm parent PR #179 exact head remains unchanged.
- [ ] Confirm successor diff is limited to BIN-01 docs/tests/package/source/workflow.
- [ ] Confirm no authority drift and no open review findings.
- [ ] Leave successor Draft/open/unmerged and stop.
