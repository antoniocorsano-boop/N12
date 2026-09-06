# CEW PWB-005 — R2BR Bridge Review Layer Plan v1

## Purpose

R2BR is a **review-only triage layer** above R2S/R2SN. It does not create missing drawing geometry, does not repair the raster, does not infer structural members and does not authorize R2C.

Inputs are the ten `GapContinuityHypothesis` records measured by R2S and controlled by R2SN on the same immutable build revision.

## Review-tier rule

The rule exists only to order human inspection. It is **not** a correctness threshold and has no engineering authority.

A gap receives `HIGH_CONTRAST_REVIEW` only when all four cross-scale minima satisfy:

- `r2s_cross_scale_min_support_fraction >= 0.70`
- `r2s_cross_scale_min_longest_run_fraction >= 0.40`
- `cross_scale_min_support_contrast >= 0.70`
- `cross_scale_min_run_contrast >= 0.40`

Every other complete gap receives `STANDARD_REVIEW`. An incomplete negative control receives `CONTROL_INCOMPLETE_REVIEW`.

These values are conservative **review-priority cutoffs**, not evidence acceptance criteria. Passing them does not mean that the gap is a real continuous line.

## Invariants

R2BR MUST:

1. retain all R2SN gap hypotheses exactly once;
2. preserve evidence-region, source, source-version, page and revision binding;
3. preserve the exact candidate IDs and bridge endpoints measured by R2S/R2SN;
4. compute only a review tier and evidence summary;
5. keep every gap `bridge_candidate_authorized=false`;
6. keep `geometry_materialization_authorized=false`;
7. keep `technical_identity_authorized=false` and `structural_identity_authorized=false`;
8. keep `r2c_scene_adapter_authorized=false`;
9. keep `canonical_write_authorized=false` and `engineering_authority_effect=NONE`.

## Interpretation boundary

`HIGH_CONTRAST_REVIEW` means only:

> this hypothesis is more useful to inspect first because the measured raster support is both strong and locally distinguishable from lateral controls at both scales.

It does **not** mean:

- continuous technical line confirmed;
- beam/column/axis/member inferred;
- structural node inferred;
- technical identity established;
- geometry eligible for canonical publication.

## Next admissible transition

R2BR may feed a later **human inspection overlay** that draws hypotheses using a visually distinct proposal style (for example dashed review marks). Such an overlay must remain independent from technical geometry and must not silently become R2C.

`R2BR review priority != bridge acceptance != R2C != structural identity != canonical authority`
