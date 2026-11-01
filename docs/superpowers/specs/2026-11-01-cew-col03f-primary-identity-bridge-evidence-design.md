# CEW-COL-03F — Primary-Source Identity Bridge Evidence Design

**Status:** DESIGN AUTHORIZED BY CONTINUATION / IMPLEMENTATION AUTHORIZED / EVIDENCE ACQUISITION ONLY / NO IDENTITY PROMOTION / NO MERGE / NO DEPLOY

## 1. Intent

COL-03F is the governed successor to qualified COL-03E exact head:

`cbf57e9261228a7376df826baadc79abe2da254c`

COL-03E proved that all 22 governed `COL-OCC-*` occurrences have complete adjudication dossiers but none has enough governed evidence for structural-identity resolution. The required successor action is:

`ACQUIRE_NEW_IDENTITY_BRIDGE_EVIDENCE`

COL-03F therefore acquires a new, exact-source-replayable evidence surface from the primary TAV.5 source. It answers only:

> Can a focused re-reading of the primary TAV.5 source produce a direct, provenance-complete support-label observation for a governed `COL-OCC-*` occurrence that is suitable for later human bridge adjudication?

COL-03F does **not** answer:

> Which historical `N###` node, TAV.7 type, vertical chain, family, section or canonical structural identity belongs to the occurrence?

No identity is promoted in COL-03F.

## 2. Frozen predecessor and authority boundary

Implementation MUST descend from exact qualified COL-03E head:

`cbf57e9261228a7376df826baadc79abe2da254c`

It MUST preserve:

- exactly 22 governed occurrence identities `COL-OCC-0001` … `COL-OCC-0022`;
- the qualified COL-03A occurrence geometry and source lineage;
- the qualified COL-03B documentary evidence surface;
- the qualified COL-03C cross-document result (`22/22 EVALUATED_NO_MATCH`);
- the qualified COL-03D historical evidence boundary (`UNBOUND` for occurrence identity);
- the qualified COL-03E adjudication dossiers and their digests;
- primary TAV.5 source identity `CEW-N12-SRC-TAV05S-V2143DBCF` and source SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.

Throughout COL-03F the following remain false:

- `support_identity_authorized`;
- `text_identity_binding_authorized`;
- `family_assignment_authorized`;
- `section_assignment_authorized`;
- `fixed_line_assignment_authorized`;
- `vertical_chain_assignment_authorized`;
- `structural_identity_authorized`;
- `canonical_node_assignment_authorized`;
- `canonical_geometry_authorized`;
- `canonical_write_authorized`;
- `g2c_promotion_authorized`;
- `g3_authorized`;
- `merge_authorized`.

## 3. Approaches considered

### A. Join governed occurrences directly to historical `N###` by coordinate proximity

Reject. COL-03E already freezes the rule that historical coordinates, row order, morphology and historical state `VER` are not a governed occurrence-to-identity bridge. Using them now would convert derived historical context into structural truth.

### B. Search TAV.7 again by geometric or nearest-neighbour matching

Reject for COL-03F. COL-03C already evaluated the governed TAV.7 evidence surface and returned `22/22 EVALUATED_NO_MATCH`. Re-running the same class of cross-document matching does not create new primary evidence.

### C. Focused exact-source TAV.5 re-read with deterministic review crops and targeted OCR

Chosen. The primary TAV.5 source is re-materialized from the frozen source contract and rasterized by the established qualified toolchain. Each governed occurrence is inspected in bounded, deterministic source regions at multiple crop scales and fixed OCR configurations. Direct label observations are recorded as bridge **candidates** only; source-only and target-overlay crops are emitted for later human inspection.

This produces genuinely new primary-source-backed evidence without importing historical identity.

## 4. Acquisition order

The inspection queue is deterministic and intentionally asymmetric:

1. `COL-OCC-0001` — existing documentary candidate `4`;
2. `COL-OCC-0015` — existing documentary candidate `30`;
3. the remaining 20 occurrences in ascending occurrence-ID order.

The first two cases are used as high-value bridge probes because COL-03B already found a direct in-footprint documentary label. COL-03F tests whether a focused re-read independently re-observes those values from the same primary source under a different bounded extraction configuration.

No special authority is granted to these two cases.

## 5. Primary-source acquisition surface

COL-03F may consume only:

1. qualified COL-03A `column-occurrence-ledger.json`;
2. qualified COL-03B `documentary-identity-evidence-ledger.json`;
3. qualified COL-03E `identity-adjudication-dossiers.json`;
4. the frozen TAV.5 source contract `governance/cew-b01/N12_TAV5_SOURCE_v1.json`;
5. the exact primary TAV.5 source materialized through the existing B01 source contract;
6. the established 300-DPI page transform for TAV.5.

Historical DXFs, historical CSVs, `N###`, `C###`, TAV.7 inferred positions, prior geometric proposals and historical association state MUST NOT contribute positive evidence to a COL-03F label candidate.

They may be cited only in closure text as excluded downstream context.

## 6. Deterministic focused re-read

For each occurrence, COL-03F derives bounded source regions from the governed occurrence bbox. Three region classes are produced:

- `FOOTPRINT` — the occurrence plus a small guard margin;
- `LOCAL` — a wider local context intended to retain nearby label fragments;
- `CONTEXT` — a larger review context intended for human interpretation.

Pixel bounds MUST be derived deterministically from the normalized governed bbox and the exact raster dimensions.

Targeted OCR is run only on `FOOTPRINT` and `LOCAL` regions using fixed configurations:

- Tesseract `--psm 6`;
- Tesseract `--psm 11`.

The OCR engine/version is frozen by the workflow. Region images may be deterministically upscaled for recognition, but every observation MUST map back to exact page coordinates and carry:

- occurrence ID;
- acquisition region class;
- OCR configuration;
- raw and normalized token;
- confidence;
- crop-local bbox;
- page-normalized bbox;
- spatial relation to the governed occurrence (`INTERNAL`, `INTERSECTING`, `NEARBY`, `OUTSIDE`);
- source version/page/page-transform IDs;
- source and raster SHA-256;
- exact-source reconstruction fields.

Only `INTERNAL` and `INTERSECTING` observations are eligible to support a bridge candidate.

## 7. Candidate classification

Each occurrence receives exactly one acquisition state.

### `CORROBORATED_EXISTING_LABEL_CANDIDATE`

Allowed only when:

- COL-03B has exactly one documentary candidate for the occurrence;
- focused COL-03F re-read observes the same normalized value in at least one eligible direct relation;
- no different eligible direct value is observed;
- every supporting observation is provenance-complete.

This state means the existing candidate has been re-observed under a focused extraction configuration. It does **not** authorize identity.

### `NEW_MULTI_CONFIG_LABEL_CANDIDATE`

Allowed only when:

- COL-03B has no documentary candidate;
- exactly one normalized value is observed in an eligible direct relation;
- that value is observed under both fixed OCR configurations (`PSM6` and `PSM11`) in `FOOTPRINT` and/or `LOCAL` regions;
- no different eligible direct value exists;
- all observations are provenance-complete.

### `SINGLE_CONFIG_DIRECT_OBSERVATION`

Used when exactly one eligible direct value exists but only one fixed OCR configuration observes it.

This is evidence, but not a bridge candidate.

### `AMBIGUOUS_DIRECT_LABELS`

Used when more than one distinct eligible direct value remains plausible.

### `NO_DIRECT_LABEL_OBSERVED`

Used when no eligible direct label is observed.

### `CONTRADICTS_EXISTING_DOCUMENTARY_CANDIDATE`

Used when COL-03B has one documentary candidate but the focused eligible direct observations contain a different value and do not uniquely corroborate the predecessor candidate.

Classification is fail-closed. Candidate states are only:

- `CORROBORATED_EXISTING_LABEL_CANDIDATE`;
- `NEW_MULTI_CONFIG_LABEL_CANDIDATE`.

Neither is an identity-resolution state.

## 8. Review imagery

For every occurrence COL-03F emits deterministic review images:

- `source-only` context crop;
- `target-overlay` context crop showing the governed occurrence bbox and eligible OCR boxes;
- one combined atlas ordered by the acquisition queue.

The overlay is explanatory evidence only. It MUST NOT change source pixels or substitute for the source-only crop.

Every image entry is accompanied by SHA-256 and exact crop bounds.

## 9. Outputs

Derived evidence only under:

`evidence/cew-col03f/`

Required JSON outputs:

1. `primary-bridge-evidence-ledger.json`
2. `primary-bridge-inspection-queue.json`
3. `primary-bridge-closure.json`

Required review output:

4. `review/primary-bridge-atlas.png`
5. per-occurrence `review/<occurrence-id>-source-only.png`
6. per-occurrence `review/<occurrence-id>-target-overlay.png`

No COL-03A/B/C/D/E evidence artifact is rewritten.

## 10. Closure semantics

COL-03F qualification means only:

- the exact primary source was re-materialized;
- all 22 governed occurrences were inspected in deterministic bounded regions;
- the candidate-first order was respected;
- every observation and review image is provenance-complete;
- candidate classification is deterministic and fail-closed;
- no historical identity entered positive evidence;
- no downstream authority flag is true.

Closure records:

- counts by acquisition state;
- candidate occurrence IDs;
- unresolved occurrence IDs;
- candidate-first probe results for `COL-OCC-0001` and `COL-OCC-0015`;
- `any_identity_resolved = false`;
- `next_required_action`.

If one or more bridge candidates exist, the next action is:

`HUMAN_ADJUDICATE_PRIMARY_LABEL_BRIDGE_CANDIDATES`

If zero bridge candidates exist, the next action is:

`ACQUIRE_EXTERNAL_OR_MANUAL_PRIMARY_IDENTITY_EVIDENCE`

## 11. Determinism

JSON outputs MUST be invariant to:

- input occurrence ordering;
- OCR TSV row ordering after canonical normalization;
- dictionary serialization order;
- repeated exact-source replay with the frozen toolchain.

The inspection queue and atlas ordering are fixed by Section 4.

## 12. Qualification conditions

COL-03F may qualify only when:

- exact COL-03E predecessor ancestry is verified;
- exact COL-03A/B/E evidence is replayed and validated;
- exactly 22 ledger rows exist with exact governed IDs;
- every row has exactly one allowed acquisition state;
- all rows contain all three deterministic crop bounds;
- all OCR observations map back to page coordinates;
- candidate states satisfy Section 7 strictly;
- review image hashes exist and files are present;
- the first two inspection queue entries are `COL-OCC-0001`, `COL-OCC-0015`;
- historical identifiers are absent from positive candidate evidence;
- all authority flags remain false;
- COL-03E, COL-03D and COL-03C regression suites remain green.

## 13. Stop conditions

COL-03F MUST stop before:

- accepting or synthesizing a human receipt;
- binding a support label as structural identity;
- joining any occurrence to `N###`;
- using historical coordinates as identity proof;
- assigning TAV.7 type, family, section, fixed line, vertical chain or canonical node;
- M0-S;
- M0-G;
- canonical CAD/BIM write;
- G2C/G3;
- EdiLus export;
- merge/deploy.

## 14. Success condition

COL-03F succeeds when the system can say, reproducibly and auditably:

> Every governed column occurrence has been re-read in deterministic, provenance-complete regions of the primary TAV.5 source; any directly observed support label is exposed only as a reviewable bridge candidate, the two pre-existing candidate cases are evaluated first, unresolved cases remain explicit, historical `N###` identities remain unbound, and all structural/canonical authority stays closed.
