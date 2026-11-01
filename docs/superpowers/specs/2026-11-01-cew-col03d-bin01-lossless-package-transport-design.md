# CEW-COL-03D-BIN-01 — Lossless Historical Package Transport

**Status:** DESIGN APPROVED BY CONTINUATION / IMPLEMENTATION AUTHORIZED / NO MERGE / NO DEPLOY / NO AUTHORITY PROMOTION

## Intent

Close the sole COL-03D blocker `HISTORICAL_PACKAGE_NOT_REPOSITORY_REPLAYABLE` by preserving the exact original bytes of `Ariano_Irpino_DXF_strutturale_v25.zip` in repository-owned storage that is reproducible from an exact checkout.

Frozen package identity:

- size: `5,345,286` bytes;
- SHA-256: `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`;
- ZIP members: `91`.

The persistent Library copy has been independently re-verified against those three values and ZIP integrity.

## Ruling: split raw-byte repository transport

The available GitHub write surface cannot upload the 5.3 MB ZIP as one binary file without routing the payload through model text. COL-03D therefore uses a binary-safe repository transport made of raw byte segments.

- source transport root: `archive/historical_packages/v25/package_transport/`;
- file naming: `Ariano_Irpino_DXF_strutturale_v25.zip.part000` ... in zero-padded lexical order;
- maximum part payload: `262144` bytes (256 KiB), except the final part;
- expected part count: `21`;
- Git blob bytes are raw slices of the exact original ZIP, not base64 text files and not recompressed data;
- reconstruction is strict byte concatenation in manifest order;
- every part has frozen byte size and SHA-256 in `package_transport_manifest.json`;
- the reconstructed package is accepted only after full size, SHA-256, ZIP integrity and exact member-count verification.

This transport is lossless segmentation, not regeneration. The package is considered `repository_materialized = true` only when the complete governed transport is present and reconstructs the frozen package exactly from the checkout.

## Fail-closed rules

Qualification MUST fail for any of:

- missing part;
- extra ungoverned part;
- duplicate part index;
- part-size drift;
- part SHA-256 drift;
- reordered or renamed part surface;
- reconstructed size or package SHA drift;
- invalid ZIP integrity;
- member count other than 91.

No fallback to PDF rendering, JPEG regeneration, lossy conversion, public host or unpinned external URL is permitted.

## Interfaces

Add `experiments/cew_col03d/package_transport.py` with:

- `load_package_transport_manifest(path: Path) -> dict[str, Any]`;
- `verify_package_transport(transport_root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]`;
- `reconstruct_historical_package_from_transport(transport_root: Path, output_path: Path, manifest: dict[str, Any]) -> dict[str, Any]`.

The reconstruction result must carry the existing historical-evidence authority closure and may set `repository_materialized = true` and `exact_source_replayable = true` only after `verify_package_source()` accepts the reconstructed ZIP against the frozen package contract.

`exact_source.build_exact_source_recovery()` must use the package transport as its package witness while continuing to use the already qualified eight-member transport for row/DXF evidence. No historical member semantics are promoted.

## Qualification

Fresh exact-SHA qualification must prove:

1. transport contract RED before implementation;
2. all 21 repository parts are present and individually verified;
3. reconstructed ZIP is exactly 5,345,286 bytes with the frozen SHA-256;
4. ZIP integrity PASS and 91 members;
5. all eight governed member checks remain PASS;
6. COL-03C regression remains PASS;
7. generated COL-03D closure has no qualification blockers and `col03d_exact_source_qualification_complete = true`;
8. all support identity, family, section, fixed line, vertical chain, structural identity, canonical geometry/write, G2C/G3 and merge flags remain false.

PR #179 remains Draft/open/unmerged. No deployment or structural promotion is authorized by BIN-01.
