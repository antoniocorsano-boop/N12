# CEW-CAL-01 — External Chain Human Review Reconciliation Design

## Status

`ACTIVE / HUMAN_VALIDATION_PREPARATION_AND_DIRECT_DECISION_RECONCILIATION`

This slice starts from the qualified external-chain interval OCR checkpoint at exact head `f415433b070ba8a539460cd66a74841e63dca433`. It does not create absolute anchors, structural identities, canonical geometry or write authority.

## Problem

The exact-source pipeline produces 34 deterministic external-chain interval crops and a comparative OCR artifact, but local OCR does not provide cross-family consensus. Human validation is therefore required before any handwritten value can become a documented metric relation.

CEW-CAL-01 contains two kinds of human evidence on the same primary sources:

1. earlier structural-grid receipts, which may be reused only after source SHA and geometric reconciliation;
2. direct interval decisions created after the professional user reviews an exact interval crop, already bound by exact `interval_review_id + crop_sha256`.

Requiring the professional user to validate the same graphic relation twice would waste qualified evidence and violate `BUILD LAST — REUSE FIRST`. Conversely, treating a direct interval decision as if it were an older geometry-based receipt would erase an important provenance distinction.

The generator must therefore reconcile both evidence paths without conflating them.

No AI precheck or OCR result can substitute for a human professional receipt.

## Canonical chain

`qualified external-chain interval -> exact crop digest -> [geometrically reconciled prior receipt OR exact-bound direct human decision OR pending human review] -> documented metric relation -> later anchor construction`

A validated metric relation is not an absolute calibration anchor.

## Repository Memory / Reuse Assessment

Existing capabilities inspected:

- `governance/cew-cal01/CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T01_01_v1.json`
- `governance/cew-cal01/CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T01_02_v1.json`
- `governance/cew-cal01/CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T02_01_v1.json`
- `governance/cew-cal01/CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T02_02_v1.json`
- `governance/cew-cal01/reviews/CEW_CAL01_EXTERNAL_CHAIN_HUMAN_*_v1.json`
- `governance/cew-cal01/CEW_CAL01_EXTERNAL_CHAIN_VISUAL_PRECHECK_v1.json`
- `experiments/cew_cal01/anchor_inventory.py`
- `tests/cew_cal01/test_anchor_validation_gate.py`

Reuse decisions:

- earlier `HUMAN_PROFESSIONAL_USER` structural-grid receipts: **REUSE** only after exact source + geometry reconciliation;
- direct external-chain human decisions: **REUSE** only by exact source SHA + exact interval id + exact crop digest;
- `AI_VISUAL_PRECHECK`: **REFERENCE_ONLY**;
- anchor validation policy (`PRIMARY_VISUAL_VALIDATED`): **REUSE** unchanged;
- new work boundary: deterministic source-frame transformation, prior-receipt reconciliation, direct-decision reconciliation and review-packet generation.

## Source-frame reconciliation for prior receipts

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
- `eligible_for_metric_calibration == false`;
- `primary_anchor_authorized == false`;
- source document/source SHA match the interval source exactly;
- the transformed receipt graphic-location center falls inside exactly one exact interval crop;
- no second reusable receipt binds to the same interval with a conflicting value.

Zero matches means the receipt is unrelated to the current interval set. Multiple interval matches or conflicting receipts fail closed.

## Direct exact-bound human decisions

A record with schema `CEW_CAL01_EXTERNAL_CHAIN_HUMAN_DECISION_v1` is a different evidence class from a prior geometry-based receipt. It is accepted only when all of the following hold:

- `reviewer_role == HUMAN_PROFESSIONAL_USER`;
- `decision == DOCUMENTED_LINEAR_DIMENSION`;
- `metric_relation_state == PRIMARY_VISUAL_VALIDATED`;
- `calibration_role == LINEAR_DIMENSION`;
- `eligible_for_metric_relation_network == true`;
- `eligible_for_metric_calibration == false`;
- `primary_anchor_authorized == false`;
- source document and source SHA equal the current manifest source;
- `interval_review_id` exists in the current manifest;
- `crop_sha256` equals that interval's current exact crop digest;
- `value.length_m` is positive;
- authority remains closed.

A direct decision does not need a source bounding box because the qualified binding is the exact interval id plus exact crop digest.

Fail-closed cases:

- unknown interval id;
- crop digest mismatch;
- source mismatch;
- ineligible decision state;
- two direct decisions on the same interval with different values;
- a direct decision and a geometrically reused prior receipt on the same interval with different values.

Identical duplicate evidence may be deterministically deduplicated but must not increase validated-relation counts.

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

- `REUSED_HUMAN_RECEIPT` — earlier human receipt reconciled geometrically;
- `DIRECT_HUMAN_DECISION` — direct professional decision reconciled by exact interval id + crop digest;
- `PENDING_HUMAN_REVIEW` — no admissible human evidence exists;
- reconciliation conflicts fail closed rather than silently selecting one.

For either validated state preserve the human value/reference but keep:

- `eligible_for_metric_calibration = false`;
- `primary_anchor_authorized = false`;
- all structural/canonical/M0-G authority false.

Packet summary must distinguish:

- `reused_human_receipt_count`;
- `direct_human_decision_count`;
- `validated_human_relation_count` = the sum of those two counts;
- `pending_human_review_count`.

## Human decision contract

A pending interval may be classified by the professional user as:

- `DOCUMENTED_LINEAR_DIMENSION` with a positive `value_m`;
- `NOT_A_DOCUMENTED_DIMENSION`;
- `AMBIGUOUS_REVIEW_REQUIRED`.

Only `DOCUMENTED_LINEAR_DIMENSION` entered by `HUMAN_PROFESSIONAL_USER` may yield `metric_relation_state = PRIMARY_VISUAL_VALIDATED`. Even then it remains relation-only until a later absolute-anchor construction step.

## Review board usability

The static review board is a review aid only. For vertical chains, a human-facing context view may be expanded and rotated to improve legibility, but it must be explicitly distinguished from the canonical exact crop. The human decision remains bound to the canonical `review_id + crop_sha256`, never to the presentation-only context image.

A presentation crop must never alter governed geometry or replace the exact evidence digest.

## Exit condition

This slice is complete when:

- earlier qualified human receipts are reconciled deterministically where possible;
- direct exact-bound human decisions are reconciled deterministically;
- all other intervals remain pending;
- TAV-02S reflects the six direct TOP decisions already confirmed by the professional user plus the two prior reusable bottom relations;
- workflow replay asserts counts, source/crop bindings and closed authority on the same SHA;
- `primary_anchor_count = 0` and no structural/canonical/M0-G authority opens;
- no merge or deploy occurs automatically.
