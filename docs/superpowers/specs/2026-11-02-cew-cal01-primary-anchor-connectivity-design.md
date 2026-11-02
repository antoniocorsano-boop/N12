# CEW-CAL-01 — Primary Anchor Connectivity and Inter-Source Registration Design

## Status

`ACTIVE_SUCCESSOR / PRIMARY_ANCHOR_DISCOVERY`

Qualified predecessor exact head: `ae00f9f565c683c75cf7249c9c0bf8a59838f4b2`.

Qualified predecessor evidence:

- CEW-CAL-01 Primary Metric Calibration run `41476290034` — PASS;
- CEW-CAL-01 External Dimension Chains run `41476289874` — PASS;
- CEW Repository Memory Gate run `41476290272` — PASS;
- governed external-chain artifact `13156938723`, digest `sha256:2a8ff67a10aa6f6b8343788d6df15769c190b08d213baebe3e3e517a6a479497`.

TAV-02S currently has a diagnostically sufficient metric-relation network but no primary metric anchors. TAV-01S remains on targeted human review and is out of scope for this slice.

## Intent

Turn the already-qualified TAV-02S documented dimension relations into a deterministic local metric reference lattice, then use only primary, source-bound homologies to transfer that lattice to TAV.5 and discover candidate TAV.5 primary anchors.

The slice must not invent an absolute survey origin, reuse the historical affine transform, use M0-G nodes for fitting, or treat TAV-02S coordinates as if they were TAV.5 coordinates.

## Ruling: TOP + RIGHT are sufficient for the first local lattice

An earlier working hypothesis treated the pending LEFT chain as a prerequisite for a connected 2D metric grid. Exact-source inspection disproves that requirement.

Qualified TAV-02S relation geometry already provides:

- TOP:R1 — six validated horizontal intervals and seven ordered x-reference ticks;
- RIGHT:R1 — two validated vertical intervals and three ordered y-reference ticks;
- relation-scale consistency within the existing governed 5% diagnostic threshold.

The Cartesian intersections of the independently documented x-reference and y-reference lines define a 7 × 3 local reference lattice. The carriers themselves do not need to intersect. LEFT remains useful as later independent vertical holdout evidence, but is not required to establish the first local frame.

## Local metric frame

The lattice uses a deterministic **local reference frame**, not an absolute project coordinate system.

Reference origin:

- x-origin: first ordered TOP:R1 reference tick;
- y-origin: first ordered RIGHT:R1 reference tick;
- local metric coordinate of their intersection: `[0.0, 0.0]`.

This origin is a coordinate convention only. It carries no survey, cadastral, structural-identity, or canonical-geometry authority.

Coordinates are reconstructed by cumulative signed sums of the already-qualified human dimensions:

- x coordinates from TOP:R1 interval values;
- y coordinates from RIGHT:R1 interval values.

Every coordinate component must retain provenance back to the exact validated relation IDs used in the cumulative sum. The metric provenance class is `RIF` because the coordinate is reconstructed from documented primary relations rather than directly printed as an absolute ordinate.

No pending interval may contribute a value.

## TAV-02S reference lattice artifact

Materialize `CEW_CAL01_TAV02_REFERENCE_LATTICE_v1` with:

- exact TAV-02S source id and SHA;
- input metric-network digest;
- x/y ordered reference-line coordinates in normalized pixels;
- cumulative local metric coordinates;
- 21 Cartesian intersection nodes;
- per-axis provenance refs;
- deterministic lattice digest;
- explicit `coordinate_frame = LOCAL_RELATIVE_METRIC`;
- explicit `absolute_origin_authorized = false`;
- all existing CEW authority flags false.

A lattice node is **not** a TAV.5 anchor and is not fit-eligible by itself.

## Inter-source registration policy

The next step is primary-to-primary registration between TAV-02S and TAV.5.

Permitted correspondence classes:

1. unambiguous structural-axis intersections visible in both primary sources;
2. column/support centers whose occurrence is independently source-bound in TAV.5 and whose homologous position in TAV-02S can be localized without historical identity;
3. distinctive documented reference intersections present in both sources.

Forbidden correspondence inputs:

- historical M0-G coordinates or node IDs;
- historical affine coefficients;
- historical CEW `S-*` annotations as geometric truth;
- nearest-neighbour matching to historical nodes;
- OCR text alone;
- manually typed pixel correspondences without primary visual/evidentiary binding;
- correspondences selected because they minimize transform residuals.

Candidate correspondence discovery may be automatic, but promotion to a governed correspondence requires exact source bindings and either deterministic source-native equivalence or human professional confirmation.

## Registration model

The first inter-source model is a 2D affine transformation from TAV.5 governed raster coordinates to the TAV-02S normalized reference frame.

Minimum registration evidence:

- at least 4 governed homologous point pairs total;
- at least 3 non-collinear pairs for fitting;
- at least 1 additional pair reserved before fitting as holdout;
- source and target points must each be non-degenerate.

The fit/holdout partition must be deterministic and frozen before coefficient estimation. Holdout selection cannot use residuals.

If these conditions are not met, emit `INSUFFICIENT_INTERSOURCE_CORRESPONDENCES` and stop.

## TAV.5 anchor promotion

Only after an inter-source registration has been frozen and independently checked may a TAV.5 source point receive a local metric coordinate derived from the TAV-02S reference lattice.

Promoted candidates use:

- source: governed TAV.5 raster/source binding;
- `source_point_px`: TAV.5 point;
- `metric_xy_m`: local relative metric coordinate obtained through the frozen primary-to-primary registration;
- metric provenance: `RIF` for both ordinates;
- evidence refs: TAV.5 source point + governed inter-source correspondence/registration + TAV-02S lattice provenance;
- metric source kind: a new bounded source kind for primary inter-source reconstructed metric coordinates;
- validation state requiring a qualified inter-source registration receipt;
- `eligible_for_fit` only when the anchor contract accepts the new source kind and all evidence bindings are complete.

This promotion does not create absolute survey coordinates. It creates a reproducible local metric frame suitable for source-derived geometric calibration.

## Relationship with existing TAV.5 candidates

The already-qualified 22 TAV.5 `StructuralObjectCandidate` occurrences may be reused as source-bound localization evidence. Their historical support identity remains unnecessary and forbidden as a registration input.

The existing candidate bridge records pixel geometry in the governed TAV.5 raster frame and already carries human-reviewed object evidence. This slice may derive stable candidate centers from those records, but candidate semantic identity cannot establish cross-source homology by itself.

## LEFT-chain role

Pending TAV-02S LEFT intervals are not required to create the first local lattice.

They become a targeted later control path:

- use LEFT only if additional vertical holdout coverage is required;
- never prefill values from scale inference;
- any LEFT value must come from a professional human decision bound to exact `review_id + crop_sha256`;
- LEFT measurements cannot retroactively alter already-qualified RIGHT human decisions merely to reduce residuals.

## Fail-closed conditions

Stop without producing fit-eligible TAV.5 anchors when any of the following occurs:

- source SHA or raster-frame drift;
- metric-network digest drift;
- missing or non-positive relation value;
- use of a pending relation value;
- inter-source correspondence source mismatch;
- duplicate source or target correspondence with conflicting partner;
- fewer than 4 governed correspondences;
- degenerate fit geometry;
- holdout not frozen before fitting;
- any historical affine/M0-G input loaded before registration freeze;
- authority escalation in any intermediate artifact.

## Expected artifact sequence

1. `tav02-reference-lattice.json`
2. `tav5-tav02-correspondence-candidates.json`
3. `tav5-tav02-governed-correspondences.json`
4. `tav5-tav02-registration-split.json`
5. `tav5-tav02-affine-registration.json`
6. `tav5-tav02-holdout-validation.json`
7. `CEW_CAL01_PRIMARY_ANCHOR_INVENTORY_v1.json` for TAV.5 local-metric anchors

The implementation may stop at any fail-closed state; it must not fabricate evidence to force later artifacts.

## Authority boundary

Throughout this slice:

- `absolute_origin_authorized = false`;
- `structural_identity_authorized = false`;
- `canonical_geometry_authorized = false`;
- `canonical_write_authorized = false`;
- `m0g_authorized = false`;
- `engineering_authority_effect = NONE`.

No merge or deploy is authorized by this design.
