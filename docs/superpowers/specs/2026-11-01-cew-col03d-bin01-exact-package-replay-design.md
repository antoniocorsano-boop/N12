# CEW-COL-03D-BIN-01 — Exact Historical Package Repository Replay

**Status:** DESIGN APPROVED BY CONTINUATION / IMPLEMENTATION AUTHORIZED / NO IDENTITY PROMOTION / NO MERGE / NO DEPLOY

## Purpose

Close the sole remaining COL-03D blocker `HISTORICAL_PACKAGE_NOT_REPOSITORY_REPLAYABLE` without changing any structural authority.

Current parent: PR #179, exact head `9385001252aa793f66d02468cc4267f4ff843606`.
Qualified recovery-evidence checkpoint retained inside that history: `89c423bd4f1a95ca7e000eed966eb26626547c2f`.

## Frozen source identity

The source is the recovered original historical package, treated as opaque immutable bytes:

- logical name: `Ariano_Irpino_DXF_strutturale_v25.zip`
- repository path: `archive/historical_packages/v25/Ariano_Irpino_DXF_strutturale_v25.zip`
- Git blob SHA: `4c2396c57c044b4d61551ce05ee8f8227208590f`
- size: `5,345,286` bytes
- SHA-256: `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`
- ZIP members: `91`

The three historical raster JPEGs are not regenerated. Their bytes are preserved only as members of the exact original ZIP.

## Active architecture

Use Git itself as the durable binary-preservation channel. Commit the exact ZIP as a binary blob at the frozen repository path. Qualification reads the checked-out file, recomputes size and SHA-256, verifies ZIP integrity/member count, and only then allows COL-03D to mark package repository materialization and exact-source replayability true.

No external URL, release asset or object store is part of the **active durable replay contract**. No regenerated raster, decompression/recompression or package rewrite is authorized.

## Reconciliation with the parallel release-asset attempt

While BIN-01 was being implemented from the qualified `89c423bd…` checkpoint, PR #179 advanced independently to `9385001252aa793f66d02468cc4267f4ff843606` with a second design based on a private GitHub draft-release asset. That work is retained in the parent history as forensic and design evidence.

Its exact-source qualification run `41286974169` did not qualify the package because the workflow download of the draft release asset received **HTTP 403**. Therefore the release-asset path is not used as the successor's operative replay dependency.

The successor is rebased on the live parent and preserves its documentation, but the active exact-source path is the repository checkout. Qualification must succeed without calling the release API or requiring the draft release asset.

## One-shot bootstrap provenance

The exact package was recovered from the persistent project Library and independently verified before repository insertion. Because the Git connector could not accept a local binary path directly, the already verified bytes were Base64-encoded for a one-shot transfer and fetched by a temporary GitHub Actions bootstrap workflow. That workflow decoded the transfer, verified the frozen SHA-256, exact size, ZIP integrity and 91-member count **before** committing the binary to Git.

The bootstrap workflow was then removed and its temporary transfer draft was discarded without sending it. The transient transfer locator is not part of the current branch surface, is not required for any qualification run, and confers no authority. From repository insertion onward, the only governed replay source is the checked-out Git blob at the frozen repository path.

Bootstrap receipt:

- source package SHA-256: `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`;
- source package size: `5,345,286` bytes;
- ZIP member count: `91`;
- bootstrap workflow result: PASS;
- historical bootstrap commit: `e63aa6af6fd3ccdc9d3ae7ca3895bee1dae7275b`;
- durable Git blob identity: `4c2396c57c044b4d61551ce05ee8f8227208590f`.

The bootstrap commit is a transport receipt only; replayability depends on the durable blob present in the successor tree, not on that historical commit remaining the branch tip.

## Required behavior

1. `verify_package_source()` must verify the checked-out package against the frozen contract.
2. `build_exact_source_recovery()` must obtain its package witness from that verified repository file, not from an external witness stub or release API.
3. `historical_package_repository_materialized = true` only for the exact repository path.
4. `historical_package_exact_source_replayable = true` only after byte, ZIP-integrity and 91-member checks pass.
5. The existing eight governed members remain independently replayed and verified as before.
6. Every authority flag remains false, including support identity, family, section, fixed line, vertical chain, structural identity, canonical node/geometry/write, G2C/G3 and merge.

## Fail-closed conditions

Missing package, changed digest/size, invalid ZIP, wrong member count or wrong repository location must prevent final COL-03D qualification. A same-name package with different bytes is `PROVENANCE_MISMATCH`.

## Workflow acceptance

A fresh exact-SHA run must prove:

- checked-out package SHA-256 exactly `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`;
- size exactly `5,345,286`;
- ZIP integrity PASS;
- exactly `91` members;
- all eight governed member contracts still PASS;
- qualified COL-03C regression still PASS;
- `historical_package_repository_materialized = true`;
- `historical_package_exact_source_replayable = true`;
- `col03d_exact_source_qualification_complete = true`;
- `qualification_blockers = []`;
- all downstream authority flags remain false;
- no release-asset/API dependency is required for replay.

## Stop condition

This successor stops after COL-03D exact-source qualification. It does not authorize merge/deploy, M0-S, M0-G, structural identity adjudication or canonical write.
