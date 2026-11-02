# CEW-CAL-01 Metric Sufficiency Gate — Design

## Intent

Turn qualified human metric relations into a source-local diagnostic network and decide, fail-closed, what evidence is still required before any calibration candidate may be fit.

The gate is not a calibration algorithm. It does not create canonical geometry, structural identity, M0-G identity, or canonical writes.

## Current baseline

- Branch: `feat/cew-cal01-primary-metric-calibration`.
- Qualified implementation checkpoint before this slice: `5ed2534ee4980b4ce6025faf62e929a4b9fe8a8d`.
- Documentation-only head after recording that checkpoint: `669b7dbf812ec0ab10e56d755b812a51a5a92a95`.
- TAV-01S: 15 external-chain intervals, 1 validated human relation, 14 pending.
- TAV-02S: 19 external-chain intervals, 10 validated human relations, 9 pending.
- All current relations are relation-only: `primary_anchor_count = 0`, `eligible_for_metric_calibration = false`.

## Source-local rule

A metric relation network is built separately for each `source_id + source.sha256`.

TAV-01S and TAV-02S must never be merged into one geometric graph or one scale estimate. Program-level reporting may sum counts only; it may not combine coordinates, graph nodes, scale diagnostics, or sufficiency state across distinct source frames.

## Inputs

For one source:

1. `interval-text-review-manifest.json`
   - authoritative source-local interval geometry;
   - `review_id`, `orientation`, `carrier_axis_px`, `interval_start_px`, `interval_end_px`, chain and side.
2. `external-chain-human-review-packet.json`
   - qualified human state and `validated_value_m`;
   - exact binding to the manifest through `review_manifest_digest`.
3. Optional `CEW_CAL01_PRIMARY_ANCHOR_INVENTORY_v1`.
   - only anchors with `eligible_for_fit = true` may contribute to affine/holdout readiness.

OCR text, image crops, historical affine coefficients, historical M0-G and historical CEW annotations cannot provide network metric values or anchor eligibility.

## Metric relation network

For each validated human relation (`REUSED_HUMAN_RECEIPT` or `DIRECT_HUMAN_DECISION`) create one deterministic edge:

- source id and SHA;
- `review_id`, side, chain id, interval index;
- orientation;
- source endpoint A/B in normalized pixel coordinates;
- pixel span;
- validated length in metres;
- diagnostic `px_per_m = pixel_span / validated_value_m`;
- human provenance state;
- `eligible_for_metric_calibration = false`;
- `primary_anchor_authorized = false`.

Endpoints are derived only from governed interval geometry:
- horizontal: A=`[interval_start_px, carrier_axis_px]`, B=`[interval_end_px, carrier_axis_px]`;
- vertical: A=`[carrier_axis_px, interval_start_px]`, B=`[carrier_axis_px, interval_end_px]`.

Pending intervals are retained only as review candidates; they never receive inferred values.

## Diagnostic consistency audit

The audit is descriptive and fail-closed. It may establish `RELATION_NETWORK_DIAGNOSTIC_SUFFICIENT`; this is not fit eligibility.

Default thresholds for this slice:

- at least 4 validated relations;
- at least 2 horizontal and 2 vertical validated relations;
- at least 2 sides represented;
- at least 1 fully validated chain;
- for each orientation with >=2 relations, every `px_per_m` must be within 5% of that orientation's median;
- horizontal-vs-vertical median `px_per_m` drift must be <=5% when both are available.

Any non-positive length/span, manifest/packet source drift, digest drift, duplicate `review_id`, unsupported state, or relation scale residual >5% fails closed.

These thresholds qualify only whether the relation network is coherent enough to stop indiscriminate human review. They do not authorize an affine fit.

## Targeted human review

If the relation network is diagnostically insufficient and pending intervals exist, emit `TARGETED_HUMAN_REVIEW` plus at most 4 deterministic review ids.

Ranking:
1. complete a partially validated chain that is one interval short;
2. add evidence in the underrepresented orientation;
3. add a new side;
4. increase an already represented incomplete chain;
5. stable tie-break by `review_id`.

No suggested row receives a proposed metric value.

## Primary anchor sufficiency

Affine calibration remains blocked unless an optional primary anchor inventory is supplied and all fit conditions hold.

Minimum candidate gate:
- at least 4 eligible anchors total;
- at least 3 non-collinear eligible source points for fitting;
- at least 3 corresponding non-collinear metric points;
- at least 1 additional eligible anchor reserved for holdout.

If no eligible anchor inventory is supplied, the blocker is `PRIMARY_ANCHOR_REQUIRED`.

This gate does not choose the fit/holdout split or fit the affine transform; that is a later slice.

## Gate states

Exactly one top-level state:

- `TARGETED_HUMAN_REVIEW`
  - relation network diagnostic criteria are not met and pending intervals can address the deficiency.
- `INSUFFICIENT`
  - relation network may be coherent, but a non-review blocker remains, including `PRIMARY_ANCHOR_REQUIRED`, or evidence is invalid.
- `SUFFICIENT_FOR_CALIBRATION_CANDIDATE`
  - relation network diagnostic criteria are met and anchor sufficiency is met.

`SUFFICIENT_FOR_CALIBRATION_CANDIDATE` still does not authorize canonical geometry, structural identity, M0-G or writes. It only authorizes the next governed step: construction of a calibration candidate with frozen fit/holdout evidence.

## Expected current-source results

### TAV-02S

The currently qualified relations should produce:

- 10 validated relations;
- 8 horizontal and 2 vertical;
- sides TOP, RIGHT, BOTTOM represented;
- TOP:R1 fully validated;
- diagnostic relation network expected to satisfy the 5% consistency criteria;
- no need for indiscriminate review of the remaining 9 intervals at this stage;
- overall gate: `INSUFFICIENT`;
- blocker: `PRIMARY_ANCHOR_REQUIRED`;
- next action: `PRIMARY_ANCHOR_DISCOVERY`.

### TAV-01S

The current single validated relation is insufficient as a source-local network:

- 1 validated vertical relation;
- no validated horizontal relation;
- no fully validated chain;
- overall gate: `TARGETED_HUMAN_REVIEW`;
- up to 4 pending rows selected deterministically for maximum diagnostic gain.

## Artifacts

Per source, materialize:

- `metric-relation-network.json`
- `metric-sufficiency-gate.json`

The existing external-chain artifact remains the carrier. The workflow must assert authority closure and current expected gate states.

## Authority

At all times in this slice:

- `primary_anchor_authorized = false` for relation edges;
- relation edges remain `eligible_for_metric_calibration = false`;
- `canonical_geometry_authorized = false`;
- `structural_identity_authorized = false`;
- `canonical_write_authorized = false`;
- `m0g_authorized = false`;
- `engineering_authority_effect = NONE`.

No merge or deploy is authorized by this design.
