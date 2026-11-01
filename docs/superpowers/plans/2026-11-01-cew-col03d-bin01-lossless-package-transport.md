# CEW-COL-03D-BIN-01 Lossless Package Transport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make the exact historical v25 ZIP reproducible from the PR #179 checkout and remove only `HISTORICAL_PACKAGE_NOT_REPOSITORY_REPLAYABLE` without promoting structural authority.

**Architecture:** Preserve the exact ZIP as 21 raw Git blobs of at most 256 KiB plus a frozen transport manifest. Reconstruct by strict concatenation, verify each part and the final package, then feed the verified package witness into the existing COL-03D recovery closure.

**Tech Stack:** Python 3.12 stdlib (`hashlib/json/zipfile/pathlib`), pytest/unittest, GitHub Git blobs/trees, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-01-cew-col03d-bin01-lossless-package-transport-design.md`

## Global Constraints

- Parent qualified checkpoint: `89c423bd4f1a95ca7e000eed966eb26626547c2f`.
- Frozen package SHA-256: `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`.
- Frozen size: `5,345,286`; member count: `91`.
- 21 raw parts; maximum part size `262144` bytes.
- No recompression, rendering or regeneration.
- Existing eight-member transport remains unchanged.
- All downstream authority flags remain false.
- No merge, deploy, M0-S, M0-G, canonical write, G2C or G3.

## Review Focus

- Missing/reordered/altered part must fail before package qualification.
- Exact concatenation must reproduce frozen package hash, not merely a valid ZIP.
- Extra ungoverned part must fail.
- Existing required-member hashes and cardinalities must remain unchanged.
- Setting exact-source replayable must not alter any authority flag.

---

### Task 1: RED transport contract

**Files:**
- Create: `tests/cew_col03d/test_package_transport.py`

- [ ] Add failing tests for missing implementation, expected 21-part manifest contract and exact package replay.
- [ ] Commit and observe fresh COL-03D workflow RED for the new contract.

### Task 2: Preserve exact package bytes

**Files:**
- Create: `archive/historical_packages/v25/package_transport/package_transport_manifest.json`
- Add binary: `archive/historical_packages/v25/package_transport/Ariano_Irpino_DXF_strutturale_v25.zip.part000` ... `.part020`

- [ ] Split the independently verified original ZIP into raw 256 KiB slices.
- [ ] Record each part name, size and SHA-256 plus full-package identity.
- [ ] Add raw blobs without text encoding or recompression.

### Task 3: GREEN deterministic reconstruction

**Files:**
- Create: `experiments/cew_col03d/package_transport.py`
- Modify: `experiments/cew_col03d/exact_source.py`
- Modify: `tests/cew_col03d/test_exact_source_writer.py`

- [ ] Implement strict manifest loading and part-surface verification.
- [ ] Implement byte concatenation to a caller-provided output path.
- [ ] Verify reconstructed bytes via existing `verify_package_source` before returning `repository_materialized=true` / `exact_source_replayable=true`.
- [ ] Make exact-source recovery use the verified repository package witness.
- [ ] Update closure tests to require no package replay blocker while authority remains closed.

### Task 4: Workflow qualification

**Files:**
- Modify: `.github/workflows/validate-cew-col03d-historical-package-recovery.yml`
- Modify: `tests/cew_col03d/test_scope_hygiene.py` only if needed to pin the governed transport surface.

- [ ] Reconstruct the package from checkout before evidence build.
- [ ] Assert size/hash/ZIP integrity/member count and 21 verified parts.
- [ ] Run all COL-03D tests and COL-03C regression.
- [ ] Assert closure has zero blockers and all authority flags false.
- [ ] Capture exact-SHA workflow receipt and Repository Memory Gate.

### Task 5: Final checkpoint

- [ ] Verify PR #179 remains Draft/open/mergeable/unmerged.
- [ ] Verify no review-thread or authority drift.
- [ ] Update PR body and issue #180 with exact qualification evidence.
- [ ] Stop: no merge/deploy and no successor structural work.
