# CEW-COL-03D-BIN-01 — Lossless Historical Package Transport

**Status:** DESIGN APPROVED BY CONTINUATION / IMPLEMENTATION AUTHORIZED / NO MERGE / NO DEPLOY / NO AUTHORITY PROMOTION

## Intent

Close the sole COL-03D blocker `HISTORICAL_PACKAGE_NOT_REPOSITORY_REPLAYABLE` by preserving the exact original bytes of `Ariano_Irpino_DXF_strutturale_v25.zip` in repository-owned storage that GitHub Actions can retrieve reproducibly without a public host.

Frozen package identity:

- size: `5,345,286` bytes;
- SHA-256: `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`;
- ZIP members: `91`.

The persistent Library copy was independently re-verified against those values and ZIP integrity before transfer.

## Ruling superseding the provisional split-blob design

A repository-owned binary channel became available after the initial RED contract: a **private draft GitHub release asset**. It avoids routing 5.3 MB through model text, avoids public file hosting and preserves the original bytes as one GitHub-managed object.

The provisional 21-part split design is therefore SUPERSEDED before implementation. No split package parts are canonical.

Governed storage identity:

- GitHub repository: `antoniocorsano-boop/N12`;
- draft release id: `430435574`;
- release tag contract: `cew-col03d-v25-package-10eba8c6`;
- release state required by qualification: `draft = true`;
- asset id: `697696555`;
- asset name: `Ariano_Irpino_DXF_strutturale_v25.zip`;
- asset content type: `application/zip`;
- asset size: `5,345,286` bytes;
- GitHub asset digest: `sha256:10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`.

The asset upload itself was performed only after an independent SHA-256 and size check. Transfer used an authenticated/private temporary file bridge; the bridge is not a qualification source.

## Immutability model

GitHub does not mutate release-asset bytes in place. Replacing the payload requires deleting the asset and uploading a new asset, which yields a different asset identity. COL-03D therefore pins **asset id + repository + expected name + size + SHA-256**.

Qualification fails closed if asset id `697696555` is unavailable, renamed unexpectedly, has a different size/digest, or downloads bytes that fail the frozen package verification. A different asset with the same filename is not an authorized substitute.

The release remains **draft/private**. Publishing the release is not required and is not authorized by COL-03D.

## Retrieval contract

GitHub Actions retrieves the pinned asset through the GitHub REST asset endpoint:

`GET /repos/antoniocorsano-boop/N12/releases/assets/697696555`

with `Accept: application/octet-stream` and the workflow `GITHUB_TOKEN`. The workflow must not use the browser download URL as an unpinned public source.

The downloaded file is accepted only after `verify_package_source()` proves:

1. exact byte size `5,345,286`;
2. exact SHA-256 `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`;
3. ZIP integrity PASS;
4. exact member count `91`.

## Repository manifest

Add `archive/historical_packages/v25/package_asset_manifest.json` containing only non-secret immutable retrieval metadata:

- repository owner/name;
- release id;
- required release state (`draft`);
- asset id;
- asset name/content type;
- expected size/digest;
- package member count;
- authority `HISTORICAL_DERIVED_EVIDENCE`;
- all promotion flags false.

No bearer token, signed URL, Drive URL or temporary transfer locator may be committed.

## Code interfaces

Add `experiments/cew_col03d/package_asset.py` with pure/fail-closed helpers:

- `load_package_asset_manifest(path: Path) -> dict[str, Any]`;
- `validate_package_asset_metadata(manifest: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]`;
- `verify_downloaded_package_asset(path: Path, manifest: dict[str, Any]) -> dict[str, Any]`.

The first two helpers validate the pinned GitHub metadata. The third delegates byte-level package verification to existing `verify_package_source()` and may then return a witness with:

- `repository_materialized = true`;
- `exact_source_replayable = true`;
- `verification_state = MATERIALIZED_VERIFIED`;
- historical-evidence authority unchanged;
- identity promotion false.

`exact_source.build_exact_source_recovery()` accepts a verified package witness supplied by the exact-source workflow. Local unit paths may use a verified downloaded fixture only; no network call belongs inside evidence parsing code.

## Fail-closed rules

Qualification MUST fail for any of:

- release not draft;
- asset id mismatch or unavailable;
- asset name/content-type/size/digest metadata drift;
- downloaded size or SHA-256 drift;
- invalid ZIP integrity;
- member count other than 91;
- fallback to a same-name but different asset;
- fallback to PDF rendering, JPEG regeneration, lossy conversion, public host or unpinned URL.

## Qualification

Fresh exact-SHA qualification must prove:

1. a causal RED exists before the release-asset implementation;
2. pinned release/asset metadata are retrieved using authenticated GitHub API access;
3. exact asset bytes download without manual intervention;
4. downloaded ZIP is exactly 5,345,286 bytes with the frozen SHA-256, ZIP integrity PASS and 91 members;
5. all eight governed member checks remain PASS;
6. COL-03C regression remains PASS;
7. generated COL-03D closure has no qualification blockers and `col03d_exact_source_qualification_complete = true`;
8. all support identity, family, section, fixed line, vertical chain, structural identity, canonical geometry/write, G2C/G3 and merge flags remain false.

PR #179 remains Draft/open/unmerged. No deployment or structural promotion is authorized by BIN-01.
