# CEW-COL-03D-BIN-01 Lossless Package Transport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the exact historical v25 ZIP automatically replayable by PR #179 qualification and remove only `HISTORICAL_PACKAGE_NOT_REPOSITORY_REPLAYABLE`, without promoting structural authority.

**Architecture:** Pin one private draft GitHub release asset by repository + release id + asset id + exact name/size/digest. GitHub Actions downloads it through the authenticated REST asset endpoint, verifies the complete ZIP with the existing package verifier, and passes the verified package witness into the existing COL-03D recovery closure.

**Spec:** `docs/superpowers/specs/2026-11-01-cew-col03d-bin01-lossless-package-transport-design.md`

## Ruling carried from RED

The first RED contract targeted 21 split Git blobs because no direct binary upload path was known. After RED was observed, a repository-owned private draft release asset channel became available and preserved the exact file without model-text encoding. The split design is therefore **SUPERSEDED before implementation**. The causal RED remains valid evidence that full-package replay was not implemented at that point; the GREEN contract is rewritten to the approved release-asset architecture and must itself be observed RED before code is added.

## Frozen identities

- Parent qualified checkpoint: `89c423bd4f1a95ca7e000eed966eb26626547c2f`.
- Package SHA-256: `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`.
- Package size: `5,345,286`; ZIP members: `91`.
- Draft release id: `430435574`.
- Asset id: `697696555`.
- Asset name: `Ariano_Irpino_DXF_strutturale_v25.zip`.
- Asset digest reported by GitHub: `sha256:10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`.
- Existing eight-member transport remains unchanged.
- All downstream authority flags remain false.
- No merge, deploy, M0-S, M0-G, canonical write, G2C or G3.

---

### Task 1: Replace provisional RED with release-asset RED

**Files:**
- Delete/supersede: `tests/cew_col03d/test_package_transport.py`
- Create: `tests/cew_col03d/test_package_asset.py`

- [ ] Pin the release/asset manifest contract and metadata drift failures.
- [ ] Pin downloaded-byte verification and authority closure.
- [ ] Observe fresh workflow RED because `package_asset` is not implemented.

### Task 2: Freeze non-secret asset metadata in the repository

**Files:**
- Create: `archive/historical_packages/v25/package_asset_manifest.json`

- [ ] Record owner/repo, release id/state, asset id/name/content type, expected size/digest/member count and evidence-only authority.
- [ ] Commit no bearer token, signed URL, Drive locator or temporary transfer reference.

### Task 3: GREEN package-asset verification

**Files:**
- Create: `experiments/cew_col03d/package_asset.py`
- Modify: `experiments/cew_col03d/exact_source.py`
- Modify: `tests/cew_col03d/test_exact_source_writer.py`

- [ ] Implement strict manifest parsing and GitHub metadata validation.
- [ ] Verify downloaded bytes through existing `verify_package_source()`.
- [ ] Return `repository_materialized=true` and `exact_source_replayable=true` only after full byte verification.
- [ ] Let exact-source evidence build accept the workflow-supplied verified package witness.
- [ ] Require zero qualification blockers while all authority flags remain false.

### Task 4: Exact-SHA workflow retrieval and qualification

**Files:**
- Modify: `.github/workflows/validate-cew-col03d-historical-package-recovery.yml`

- [ ] Give only the minimal `contents: read` permission needed for release-asset retrieval.
- [ ] Fetch release metadata and pinned asset metadata by API; require draft release and exact asset id/name/size/digest.
- [ ] Download asset id `697696555` with authenticated `Accept: application/octet-stream`.
- [ ] Verify exact package bytes, ZIP integrity and member count before evidence build.
- [ ] Run all COL-03D tests and COL-03C regression.
- [ ] Assert closure has zero blockers and all authority flags false.
- [ ] Capture fresh exact-SHA workflow receipt and Repository Memory Gate.

### Task 5: Close BIN-01 checkpoint without promotion

- [ ] Verify PR #179 remains Draft/open/mergeable/unmerged.
- [ ] Update PR body and issue #180 with exact qualification evidence.
- [ ] Remove the temporary Google Drive transfer copy after GitHub asset readback/qualification; it is not a source of record.
- [ ] Stop: no merge/deploy and no successor structural work.
