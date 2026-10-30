# CEW-COL-01 — Number-anchored column recovery design

**Date:** 2026-10-30  
**Status:** APPROVED_FOR_IMPLEMENTATION  
**Base checkpoint:** `f0b54e14f236aadba8a8950fe3a95c91b1c1b740` (`HUMAN_REVIEW_CONSOLIDATED / EXACT_SOURCE_REQUALIFIED`)

## Objective

Recover column-footprint candidates on exact-source TAV-05S without requiring drawn symmetry axes, and measure the project hypothesis `H-COL-01`: support identifiers are present/detectable on all or nearly all relevant column footprints.

This is a bounded acquisition/retrieval experiment. It does not create structural identity, canonical geometry, section assignment, fixed-line decisions, G2C promotion, G3 authority, or merge authority.

## Why this tranche

The historical G4 pilot established 34 supports and five candidate dimensional families, including elongated `30x110` supports 18/23 and `110x30` support 30. Human inspection indicates that elongated columns can lack drawn symmetry axes. Therefore a detector that requires crossed axes systematically risks false negatives.

The beam work in PR #169 also established a successful project-local pattern: small governed graphical prototypes/cues -> deterministic retrieval -> Human Review -> durable receipt. CEW-COL-01 adapts that pattern to columns.

## Reuse boundary

Reuse before building new code:

1. immutable TAV-05S source contract and SHA-256;
2. exact-source rasterization and human-confirmed document zoning already qualified in CEW-B01;
3. neutral primitive extraction where useful for local footprint evidence;
4. historical G4 support/family register only as **benchmark/review evidence**, never as a production detection oracle;
5. existing CEW authority rules: similarity/retrieval is not identity.

No historical stack is merged wholesale.

## Recognition grammar

Column recovery is multi-cue:

`text/number anchor -> local footprint geometry -> aspect ratio/orientation -> optional axis evidence -> prototype/family retrieval -> Human Review`

Symmetry axes are optional supporting evidence.

A numeric token alone is not a column and never assigns structural identity.

## First-pass object states

- `P1_NUMBER_FOOTPRINT_AXES`: identifier + plausible footprint + axis evidence.
- `P2_NUMBER_FOOTPRINT_NO_AXES`: identifier + plausible footprint, no axis evidence.
- `P3_NUMBER_PARTIAL_FOOTPRINT`: identifier + interrupted/partial local enclosure.
- `P4_FOOTPRINT_NO_NUMBER`: reserved for later expansion; not searched in COL-01 first pass.

The first pass is intentionally number-anchored to test `H-COL-01` rather than silently assuming it.

## Exact-source audit

The workflow must:

1. materialize the exact TAV-05S source using the existing source contract;
2. verify SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`;
3. reuse the confirmed `STRUCTURAL_WORKAREA` zoning;
4. obtain OCR/token observations from the exact raster with a frozen system OCR executable;
5. parse only support-like tokens as **text-anchor candidates**;
6. assess local footprint evidence without requiring axes;
7. export source-only review crops and a machine-readable manifest;
8. run deterministically twice and require byte-identical canonical output.

## H-COL-01 benchmark

For the G4 pilot, the historical benchmark support identifiers are used only to measure retrieval coverage and to select review witnesses:

`1..21, 22, 22', 23..33` as represented by the historical 34-support pilot register.

They must not be embedded as a condition that generates a candidate. Candidate generation starts from exact-source observations.

The audit reports:

- detected support-like text anchors;
- benchmark IDs matched/unmatched after normalization;
- duplicate/ambiguous OCR tokens;
- local-footprint state for each anchor;
- axis evidence present/absent;
- special witness status for elongated historical supports 18, 23 and 30.

`H-COL-01` remains `UNVERIFIED`, `SUPPORTED`, or `REJECTED` based on measured exact-source coverage. No threshold may turn it into an engineering fact.

## Human Review package

The first review package should prioritize:

1. elongated witnesses 18, 23, 30 if retrieved;
2. candidates with footprint but no axes;
3. OCR ambiguities/duplicates;
4. a small sample of ordinary candidates with axes.

Allowed Human Review outcomes:

- `COLUMN_GRAPHIC_CONFIRMED`
- `NOT_COLUMN`
- `UNCERTAIN`
- `TEXT_ANCHOR_WRONG`

Human Review remains graphical/acquisition evidence only.

## Outputs

Planned paths:

- `experiments/cew_col01/number_anchor.py`
- `experiments/cew_col01/local_footprint.py`
- `experiments/cew_col01/exact_source_audit.py`
- `tests/cew_col01/test_number_anchor.py`
- `tests/cew_col01/test_local_footprint.py`
- `.github/workflows/validate-cew-col01-number-anchored-column-recovery.yml`
- `evidence/cew-col01/number-anchored-column-recovery/` as CI artifact output only

## Success criterion for this tranche

COL-01 succeeds when the exact-source workflow produces a deterministic review package that can answer, with measured evidence:

- how many of the historical G4 support identifiers are actually detected as text anchors;
- whether valid column-footprint candidates can be retained when axis evidence is absent;
- whether elongated supports 18/23/30 are recoverable without making axes mandatory.

Success does **not** require 34/34 OCR recall. A shortfall is a valid finding and must remain visible rather than being repaired with hard-coded identifiers.

## Authority boundary

Always false in COL-01 outputs:

- `semantic_classification_authorized`
- `structural_identity_authorized`
- `canonical_geometry_authorized`
- `canonical_write_authorized`
- `section_assignment_authorized`
- `fixed_line_assignment_authorized`
- `g2c_promotion_authorized`
- `g3_authorized`
- `merge_authorized`
