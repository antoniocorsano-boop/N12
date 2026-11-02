# CEW-CAL-01 — External Chain Human Review Reconciliation Design

## Status

`ACTIVE / HUMAN_VALIDATION_PREPARATION_ONLY`

This slice starts from the qualified external-chain interval OCR checkpoint at exact head `f415433b070ba8a539460cd66a74841e63dca433`. It does not create new metric values, absolute anchors, structural identities, canonical geometry or write authority.

## Problem

The exact-source pipeline now produces 34 deterministic external-chain interval crops and a comparative OCR artifact, but local OCR does not provide cross-family consensus. Human validation is therefore required before any handwritten value can become a documented metric relation.

CEW-CAL-01 already contains human professional review receipts for some structural-grid dimensions on the same primary sources. Requiring the professional user to validate the same graphic relation twice would waste qualified evidence and violate the project rule `BUILD LAST — REUSE FIRST`.

The next step must therefore do two things:

1. reconcile existing human receipts to the new interval geometry only when the binding is exact and unambiguous;
2. build a governed review packet for the remaining intervals, initially `PENDING_HUMAN_REVIEW`.

No AI precheck or OCR result can substitute for a human professional receipt.

## Canonical chain

`qualified external-chain interval -> exact crop digest -> existing human receipt reconciliation OR pending human review -> human decision receipt -> documented metric relation -> later anchor construction`

A validated metric relation is not an absolute calibration anchor.

## Repository Memory / Reuse Assessment

Existing capabilities inspected:

- `governance/cew-cal01/CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T01_01_v1.json`
- `governance/cew-cal01/CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T01_02_v1.json`
- `governance/cew-cal01/CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T02_01_v1.json`
- `governance/cew-cal01/CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T02_02_v1.json`
- `governance/cew-cal01/CEW_CAL01_EXTERNAL_CHAIN_VISUAL_PRECHECK_v1.json`
- `experiments/cew_cal01/anchor_inventory.py`
- `tests/cew_cal01/test_anchor_validation_gate.py`

Reuse decisions:

- existing `HUMAN_PROFESSIONAL_USER` receipts: **REUSE**, but only after source SHA and geometric location reconciliation;
- `AI_VISUAL_PRECHECK`: **REFERENCE_ONLY**; it may be shown as an aid but cannot validate a metric relation;
- anchor validation policy (`PRIMARY_VISUAL_VALIDATED`): **REUSE** unchanged;
- new work boundary: deterministic source-frame transformation, receipt-to-interval reconciliation and pending-review packet generation.

## Source-frame reconciliation

The frozen structural-grid rasters are normalized by `ROTATE_90_COUNTERCLOCKWISE` before external-chain detection.

For a source point `(x, y)` in the original raster of width `W`, normalized coordinates are:

`x' = y`

`y' = W - x`

For a source bounding box `[x1, y1, x2, y2]`, the normalized bounding box is:

`[y1, W - x2, y2, W - x1]`.

A prior human receipt is reusable only if:

- `reviewer_role == HUMAN_PROFESSIONAL_USER`;
- `metric_relation_state == PRIMARY_VISUAL_VALIDATED`;
- `calibration_role == LINEAR_DIMENSION`;
- `eligible_for_metric_relation_network == true`;
- `primary_anchor_authorized == false`;
- source document/source SHA match the interval source exactly;
- the transformed receipt graphic-location center falls inside exactly one exact interval crop;
- no second reusable receipt binds to the same interval with a conflicting value.

Zero matches means the receipt is unrelated to the current external-chain interval set. Multiple interval matches or conflicting receipts fail closed.

## Review packet

For every interval, produce one row containing:

- source id and source SHA;
- exact `review_id`;
- side, chain id and interval index;
- exact `crop_file` and `crop_sha256`;
- crop bounding box in normalized frame;
- OCR comparison status, observations and any normalized proposals;
- optional AI precheck reference, explicitly non-authoritative;
- review state.

Review states:

- `REUSED_HUMAN_RECEIPT` — an existing human professional receipt is geometrically reconciled;
- `PENDING_HUMAN_REVIEW` — no reusable receipt exists;
- `RECONCILIATION_CONFLICT` — ambiguous or contradictory evidence; packet generation fails closed rather than silently selecting one.

For `REUSED_HUMAN_RECEIPT`, preserve the existing receipt value and reference but keep:

- `eligible_for_metric_calibration = false`;
- `primary_anchor_authorized = false`;
- all structural/canonical/M0-G authority false.

## Human decision contract

The packet does not create human decisions. A later human decision record may classify a pending interval as:

- `DOCUMENTED_LINEAR_DIMENSION` with a positive `value_m`;
- `NOT_A_DOCUMENTED_DIMENSION`;
- `AMBIGUOUS_REVIEW_REQUIRED`.

Only `DOCUMENTED_LINEAR_DIMENSION` entered by `HUMAN_PROFESSIONAL_USER` may yield `metric_relation_state = PRIMARY_VISUAL_VALIDATED`. Even then it remains a relation-only receipt until a later absolute-anchor construction step.

## Review board

The exact-source workflow may emit a static `external-chain-human-review.html` alongside the packet. The board is a review aid only and references the exact relative crop files; it must not embed or infer values not present in the packet.

## Exit condition

This slice is complete when:

- existing qualified human receipts are reconciled deterministically to exact intervals where possible;
- all other intervals are represented as pending review;
- the workflow replays the packet from frozen exact sources;
- packet counts, source/crop bindings and authority closure are asserted on the same SHA;
- no new human receipt, metric anchor, merge or deploy is created automatically.