# CEW-CAL-01 — Primary Metric Calibration Design

## Status

`ACTIVE_SUCCESSOR / SOURCE_DERIVED_CALIBRATION_REQUIRED`

Predecessor exact head: `ee23c221118064022fa77b694ff88119530cc454` on PR #186.

Fresh predecessor qualification: workflow run `41317800420` — adapter contracts PASS, DXF documentary exact-source PASS, structural-candidate exact-source PASS, metric witness comparison PASS.

Qualified metric-comparison artifact:

- name: `cew-spiral01-metric-comparison`
- artifact id: `13088253052`
- digest: `sha256:c0ffc5ed72db1bc26db242f27b1f7bea5fbecb9977681ec6b61e2d32bf107974`
- 22 current `StructuralObjectCandidate` projections compared against historical G4 `SUPPORT_CORE` witness nodes
- distance audit: min `0.2107452724 m`, median `1.9936776851 m`, max `2.6637044432 m`
- 19 unique nearest historical nodes for 22 candidates
- comparison semantics: `DISTANCE_AUDIT_ONLY_NO_BINDING_NO_THRESHOLD`

These distances are a diagnostic baseline only. They are not calibration targets.

## Problem

The current 22 source-derived column candidates are valid CEW object candidates, but their metric projection still relies on a historical TAV.5/G4 affine registration whose coefficient provenance is not replayable from its historical commit. The witness is useful for audit, but it cannot establish current metric geometry.

The next blocker is therefore not historical `N###` identity and not OCR. The blocker is a replayable, source-derived transformation between governed TAV.5 coordinates and the metric structural coordinate system.

## Goal

Construct a reproducible primary-evidence metric calibration for TAV.5, with independent holdout validation, so each governed current column candidate can receive a metric candidate position with an explicit residual/uncertainty record before any comparison with historical M0-G.

## Canonical evidence order

`Primary TAV.5 -> source-bound anchor observations -> metric anchor relations from documented dimensions/axes -> calibration set -> frozen transform -> holdout validation -> current candidate metric projection -> historical M0-G comparison`

The historical comparator is deliberately last.

## Authority boundary

CEW-CAL-01 is non-promoting until a later governance decision.

Always false throughout this slice:

- `structural_identity_authorized=false`
- `canonical_geometry_authorized=false`
- `canonical_write_authorized=false`
- `m0g_authorized=false`
- `historical_support_identity_authorized=false`

No `N###` value is required to calibrate geometry.

## Primary-anchor policy

A calibration anchor must ultimately be bound to governed primary TAV.5 evidence. Candidate localization may reuse qualified source-native/vector tooling, including recovered DXF observations, but recovered historical CEW annotations and M0-G nodes cannot themselves become calibration evidence.

Permitted anchor classes, when supported by TAV.5:

1. intersections of documented structural axes;
2. dimension-chain endpoints or ticks with documented metric values;
3. unambiguous intersections between documented reference lines whose metric relationship is stated on the sheet;
4. other source-native geometric points only when their metric coordinates can be independently reconstructed from documented dimensions/axes.

Rejected as calibration anchors:

- nearest historical M0-G nodes;
- historical CEW-derived `S-*` annotations;
- inferred `N###` labels without metric relation;
- OCR text alone without geometric binding;
- manually typed coordinates without primary provenance;
- points whose metric coordinate is derived from the same historical affine transform being replaced.

## Anchor record

Each anchor must preserve at least:

- `anchor_id` — deterministic CEW identifier;
- `source_version_sha256`;
- `source_page` / governed raster binding;
- `source_point_px` and/or source-native point;
- `anchor_class`;
- `metric_x_m`, `metric_y_m`;
- provenance for each metric ordinate (`DOC`, `MIS`, `RIF`, or fail-closed `ND`);
- evidence references supporting source position and metric relation;
- `role = CALIBRATION | HOLDOUT` assigned only after the inventory is frozen;
- `eligible_for_fit` boolean;
- reasons for rejection when false.

## Calibration model

The first admissible model is a 2D affine transform.

No projective, polynomial, spline, or local warp is allowed unless the affine model fails independent holdout validation and a later design explicitly justifies the added degrees of freedom.

Minimum mathematical sufficiency:

- at least 3 non-collinear eligible calibration anchors;
- at least 2 eligible holdout anchors not used in fitting;
- holdouts must not all occupy the same local neighborhood;
- if these conditions are not met, return `INSUFFICIENT_PRIMARY_ANCHORS` and stop.

More anchors are preferred; the implementation must not fabricate anchors to meet the minimum.

## Holdout rule

The calibration/holdout split is deterministic and frozen before fitting.

The split must preserve spatial coverage and must not be chosen by looking at residuals. Holdout anchors are never used to estimate coefficients. A calibration result that cannot reproduce its holdout partition from the frozen anchor inventory is invalid.

## Qualification outputs

CEW-CAL-01 must produce inspectable artifacts:

1. `CEW_CAL01_PRIMARY_ANCHOR_INVENTORY_v1.json`
2. `CEW_CAL01_ANCHOR_SPLIT_v1.json`
3. `CEW_CAL01_AFFINE_CALIBRATION_v1.json`
4. `CEW_CAL01_HOLDOUT_VALIDATION_v1.json`
5. `CEW_CAL01_CURRENT_CANDIDATE_PROJECTION_v1.json`
6. optional post-freeze `CEW_CAL01_HISTORICAL_COMPARISON_v1.json`

Every artifact carries source digests, tool versions, deterministic digest, and closed authority flags.

## Validation semantics

CEW-CAL-01 must report residuals; it must not silently convert residuals into identity or canonical geometry decisions.

The validation report must include at least:

- calibration-anchor residuals;
- holdout residuals separately;
- max/median/RMS residual for holdouts;
- spatial distribution of holdouts;
- transform determinant / invertibility check;
- exact input inventory digest and split digest;
- explicit `historical_comparator_loaded=false` during fit and holdout validation.

No acceptance threshold is introduced merely to make the test pass. A professional tolerance, if needed for promotion, is a later governance decision supported by source scale, drawing quality, model purpose, and uncertainty analysis.

## Current-candidate projection

Only after the affine transform and holdout report are frozen may the 22 current `StructuralObjectCandidate` centers be projected into metric candidate coordinates.

Each projection records:

- current CEW object candidate id;
- source occurrence id;
- source center;
- projected metric coordinates;
- transform id/digest;
- calibration status;
- uncertainty/residual context;
- all authority flags false.

No nearest-node binding is produced.

## Historical M0-G role

The old M0-G is an external regression witness only.

It may be loaded only after the primary calibration, split, holdout validation, and current-candidate projection are frozen. It may answer questions such as whether systematic disagreement remains, but it cannot mutate coefficients, anchor selection, object identity, or current coordinates.

## Exit condition

CEW-CAL-01 is technically complete when the repository can replay from the frozen TAV.5 source to:

`primary anchors -> frozen split -> affine fit -> independent holdout residuals -> 22 current metric candidate projections`

with deterministic artifacts and with no use of M0-G or historical registration coefficients in fitting.

Only then may the project decide whether the primary calibration is sufficient to support a later canonical-geometry promotion gate.
