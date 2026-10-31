# CEW-COL-02 Axis-aware Whole-symbol Repair — Design

## Intent

Close the residual COL-02 graphical-occurrence gap exposed by the bounded Human Review without invalidating the already-qualified 611 neutral proposals or the completed mobile review bundle.

Human finding:
- R01 / `COL02-FP-0252`: fragmented column symbol; only part of the whole symbol is boxed.
- R02 / `COL02-FP-0106`: mislocalized target between beam section and column; does not hit the column.
- R03 / `COL02-FP-0073`: fragmented column symbol.
- R04 / `COL02-FP-0241`: fragmented column symbol.
- R05 / `COL02-FP-0261`: fragmented column symbol.
- R06 / `COL02-FP-0071`: fragmented column symbol.

The recurrent failure mode is axis-induced fragmentation: two orthogonal structural axes cross the column symbol and visually divide it into four parts; the current proposal layer can treat one fragment as a standalone footprint.

## Goals

- Reconstruct one whole rectangular graphical symbol around an orthogonal axis crossing when a human-reviewed seed is known to be a fragmented column symbol.
- Preserve the original candidate IDs and the 611-proposal v1 set unchanged.
- Reject the R02 mislocalized target rather than attempting to repair it.
- Produce target-explicit derived repair candidates for a final bounded graphical review.
- Keep all structural/canonical authority closed.

## Non-goals

- No support-number assignment.
- No text-to-column identity binding.
- No family/section/fixed-line assignment.
- No structural identity.
- No canonical geometry/write.
- No G2C/G3 promotion.
- No merge authorization.
- No global rerun of the completed ten-candidate Human Review.

## Approaches considered

### 1. Mutate `extract_footprint_proposals()` globally

Would make the producer axis-aware for every proposal, but can reorder/rerank the 611 proposals and therefore change `COL02-FP-*` identifiers already referenced by durable human receipts. Rejected for this bounded repair.

### 2. Global morphological closing after axis suppression

Cheap, but risks joining beam lines and column symbols across junctions and would directly reproduce the R02 failure class. Rejected as insufficiently fail-closed.

### 3. Seeded axis-aware whole-symbol repair — selected

Keep v1 proposals immutable. For each human-confirmed fragmented seed, reconstruct a derived whole-symbol bbox only when source geometry supplies an orthogonal long-axis crossing plus a bounded rectangular envelope around that crossing. The derived object retains explicit provenance to the seed proposal and receives a new repair-local ID.

## Geometry rule

For a seed bbox known by Human Review to be a fragmented column symbol:

1. Rebuild the same grayscale/binary/long-axis masks used by COL-02 v1.
2. Find an orthogonal long-axis intersection in a bounded neighborhood of the seed.
3. Bridge only the axis-width gaps in the local axis-suppressed mask using directional closing sized from the observed axis thickness.
4. Find rectangular envelope candidates that:
   - contain the selected axis intersection;
   - overlap the original seed;
   - are larger than the seed fragment;
   - remain within the existing neutral proposal size bounds;
   - have outer-boundary evidence on all four sides.
5. If zero or multiple equally valid envelopes remain, return `UNRESOLVED` rather than selecting arbitrarily.
6. Never use support IDs, family ratios, expected dimensions, OCR identity, or previously known structural identities to choose the envelope.

A beam/column junction without a four-side enclosing rectangle around the axis crossing must not qualify as a whole-symbol repair.

## Provenance and identifiers

Derived repairs use repair-local IDs (`COL02-WSR-001` …) and record:
- source candidate ID;
- Human Review decision ID;
- original seed bbox;
- reconstructed bbox;
- axis crossing point and observed axis thickness;
- deterministic replay digest.

Original `COL02-FP-*` IDs and the v1 proposal payload are never rewritten.

## Human adjudication receipt

The six-case micro-review is materialized as a governed graphical receipt:
- five `FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY` findings;
- one `MISLOCALIZED_NOT_COLUMN` finding for R02 / `COL02-FP-0106`.

This receipt authorizes only bounded graphical repair generation.

## Authority

`graphical_whole_symbol_repair_authorized = true` only for the five explicit fragmented seeds.

All of the following remain `false`: support identity, text identity binding, family assignment, section assignment, fixed-line assignment, structural identity, canonical geometry, canonical write, G2C, G3, merge.

## Completion condition

This repair stage is complete only when exact-source replay deterministically produces either:
- one reviewable whole-symbol repair for each of the five fragmented seeds, or
- an explicit unresolved status for any seed that cannot be reconstructed safely.

Occurrence coverage remains open until the resulting derived repairs receive bounded Human Graphical Review.
