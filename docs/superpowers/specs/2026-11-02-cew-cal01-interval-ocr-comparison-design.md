# CEW-CAL-01 — Interval OCR Comparison Design

## Status

`ACTIVE / NON_PROMOTING_OCR_ASSISTANCE`

This slice starts from the qualified external-chain geometry and the deterministic interval review crops produced by `interval_text_review_exact.py`. It does not reopen carrier, tick, interval, source-frame, or structural-grid geometry.

## Problem

The external dimension-chain geometry is now sufficiently localized to generate one exact review crop per interval, but the handwritten dimension text is not yet qualified. A remote TrOCR attempt returned HTTP 402 and the local execution environment does not carry `transformers` or a cached TrOCR model. Adding that dependency to the governed exact-source toolchain would be disproportionate and would make the replay heavier without establishing professional authority.

The useful next step is therefore a comparative OCR layer that extracts multiple independent text proposals from each exact crop, preserves disagreement, and optionally accepts a separately produced TrOCR observation when available. OCR remains assistance to human review; it is not a metric or structural authority.

## Goal

Produce a deterministic, source-bound comparison report for every exact interval crop using multiple local Tesseract recognition families plus an optional external TrOCR observation, while preserving fail-closed authority and requiring human validation before any value can enter primary metric calibration.

## Canonical evidence order

`qualified external chain -> exact interval crop -> local OCR family observations -> optional external TrOCR observation -> comparison/consensus diagnostic -> human validation -> later documented metric relation`

The comparison layer cannot bypass the human-validation step.

## Inputs

For each source (`TAV-01S`, `TAV-02S`):

- `interval-text-review-manifest.json` produced by `interval_text_review_exact.py`;
- each `review-crops/*.png` file referenced by the manifest;
- crop SHA-256 recorded in the manifest;
- optional external provider JSON bound to the same `review_id` and `crop_sha256`.

Any crop digest mismatch fails closed.

## Local recognizer policy

Use only the already available exact-source toolchain plus the system `tesseract` binary. Do not add `transformers`, Torch model downloads, network inference, or model caches to the required workflow.

Run at least three deterministic local families whose preprocessing/segmentation choices differ:

1. grayscale/contrast normalized, `psm 7`;
2. thresholded and line-suppressed, `psm 7`;
3. enlarged thresholded crop, `psm 13`.

All local passes use a numeric punctuation whitelist appropriate to dimension labels. Raw OCR text, confidence, family identifier, Tesseract version and crop digest are retained. Geometry must never be used to correct OCR text.

## Optional TrOCR policy

TrOCR remains an optional provider, not a workflow dependency.

The repository may ingest externally produced TrOCR observations only when the payload contains:

- `review_id`;
- exact `crop_sha256`;
- `provider_id = TROCR`;
- explicit `model_id`;
- raw text;
- confidence when available.

The comparator never calls a remote endpoint and never downloads a TrOCR model. Provider absence is a valid state.

## Comparison semantics

For each `review_id`, preserve all provider/family observations. Normalization may create a numeric comparison key, but must retain the raw text unchanged.

Diagnostic states:

- `OCR_COMPARATIVE_AGREEMENT`: at least two distinct recognition families/providers independently yield the same normalized text;
- `OCR_COMPARATIVE_CONFLICT`: two or more valid observations disagree;
- `OCR_COMPARATIVE_INSUFFICIENT`: fewer than two valid observations are available;
- `OCR_NO_PROPOSAL`: no valid numeric text proposal exists.

A diagnostic agreement is not a documentary validation receipt.

Every row must keep:

- `human_review_required = true`;
- `primary_anchor_authorized = false`;
- `eligible_for_metric_calibration = false`.

The top-level artifact keeps `primary_anchor_count = 0` and all CEW-CAL-01 authority flags false.

## Determinism

The comparison artifact is canonicalized before hashing. Its digest must be invariant to input provider-observation ordering. Local family execution order is fixed. Provider rows are sorted by `(review_id, family_id/provider_id, raw_text)` before digesting.

## Exact-source workflow

The external-chain workflow will:

1. materialize exact interval review crops for TAV-01S and TAV-02S;
2. run the local comparative OCR stage on those crops;
3. write a separate comparison artifact per source;
4. assert source/crop bindings, review counts and authority closure;
5. upload the comparison artifacts with the existing governed external-chain evidence.

The workflow must not assert specific recognized dimension values because OCR quality is diagnostic and can vary with the system Tesseract build. It must assert replay structure, source/crop binding and closed authority.

## Non-goals

This slice does not:

- create calibration anchors;
- assign metric coordinates;
- infer values from chain length or neighboring intervals;
- bind historical M0-G or `N###` identities;
- install or invoke TrOCR automatically;
- change external-chain geometry;
- merge or deploy.

## Exit condition

The slice is complete when both structural-grid sources replay from exact interval crops to deterministic comparative OCR artifacts, the full CEW-CAL-01 contract suite is green, the exact-source workflow is green on the same SHA, and all metric/structural/canonical authority remains closed.