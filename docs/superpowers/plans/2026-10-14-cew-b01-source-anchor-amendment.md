# CEW-B01 Source Anchor Amendment 01

**Date:** 2026-10-14  
**Applies to:** `docs/superpowers/plans/2026-10-14-cew-b01-external-tool-qualification-vertical-slice.md`  
**Scope:** source SHA-256 correction only  
**Status:** VERIFIED BY REPOSITORY-NATIVE REAL-SOURCE CHECK

## Correction

The B01 implementation plan records the following historical SHA-256 for the frozen source `archive/documentazione_originaria/tavola 5.pdf`:

`2143b256511788691291cef533559306fc2988c7cb59a16d49cf86d1d7e94c7f`

That value is **incorrect** and is superseded everywhere in CEW-B01 by the verified value:

`2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`

No other source anchor changes.

The following remain unchanged and verified:

- repository: `antoniocorsano-boop/N12`
- commit: `78c20a52db4f391ce0d13b9705b9f04737e218c9`
- path: `archive/documentazione_originaria/tavola 5.pdf`
- Git blob SHA: `ec32cd621877e9037cb26ebc083164140a8e3e68`
- page index: `0`

Verified byte size: `744562` bytes.

## Evidence

GitHub Actions run `38533007878` executed against CEW-B01 Step 1 exact head `6a9be295ecf7bb092dc88d262db4e8068dc2339c` with `contents: read` permissions only.

The runner:

1. fetched the exact archival commit;
2. resolved the exact commit/path to Git blob `ec32cd621877e9037cb26ebc083164140a8e3e68`;
3. materialized the blob bytes directly with Git;
4. computed SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`;
5. recorded size `744562` bytes;
6. passed all 10 Step 1 tests;
7. materialized the source through the CEW-B01 CLI;
8. byte-compared direct Git and CEW-B01 materializations successfully.

Final result: `real_source_verification = PASS`.

## Authority rule

For CEW-B01, whenever the original implementation-plan text and this amendment differ **only on the frozen source SHA-256**, this amendment is authoritative.

This amendment does not modify scope, tool choices, epistemic rules, phase boundaries, WIP=1, PR #147 protection, or any CEW-FEM prohibition.
