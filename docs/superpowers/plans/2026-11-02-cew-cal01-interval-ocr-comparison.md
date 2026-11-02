# CEW-CAL-01 Interval OCR Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic comparative OCR over the exact interval review crops using multiple local Tesseract families plus optional externally supplied TrOCR observations, without creating metric or structural authority.

**Architecture:** A pure comparison core validates crop-bound observations and reduces them into fail-closed diagnostic states. A separate exact-source runner executes three deterministic Tesseract families over each existing crop and emits source-bound observations. An optional importer accepts TrOCR JSON only when `review_id` and crop digest match. The existing external-chain workflow then replays both sheets through the comparison stage and uploads the separate artifacts.

**Tech Stack:** Python 3.12.15, existing `opencv-python-headless`, system Tesseract 5.x, `unittest`, deterministic JSON, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-02-cew-cal01-interval-ocr-comparison-design.md`

## Global Constraints

- Branch remains `feat/cew-cal01-primary-metric-calibration`; PR #187 remains open, Draft and unmerged.
- Do not add `transformers`, Torch model downloads, remote inference, or required TrOCR runtime dependencies.
- Do not correct OCR text from chain geometry, interval length, adjacent values or historical data.
- Every comparison row keeps `human_review_required=true`, `primary_anchor_authorized=false`, `eligible_for_metric_calibration=false`.
- Top-level `primary_anchor_count=0`; structural, canonical, M0-G and write authority remain closed.
- Optional TrOCR payloads must match both `review_id` and exact `crop_sha256`.
- No merge or deploy is part of this plan.

## Review Focus

- A crop digest mismatch must fail closed instead of attaching an observation to the wrong interval.
- Duplicate observations from the same recognition family must not manufacture cross-family agreement.
- Two distinct families agreeing on the same normalized text may create only a diagnostic agreement, never metric eligibility.
- Conflicting valid readings must remain visible and yield `OCR_COMPARATIVE_CONFLICT`.
- Missing optional TrOCR input must be a valid state and must not change local replay results.

---

### Task 1: Pure comparative OCR contract

**Files:**
- Create: `experiments/cew_cal01/interval_ocr_compare.py`
- Create: `tests/cew_cal01/test_interval_ocr_compare.py`

**Interfaces:**
- Consumes: interval review manifest rows plus provider observations containing `review_id`, `crop_sha256`, `family_id`, `provider_id`, `raw_text`, optional `confidence`.
- Produces: `build_interval_ocr_comparison(manifest, observations) -> dict` and `comparison_status(observations) -> str`.

- [ ] **Step 1: Write RED tests** for crop-digest mismatch, order-independent digest, duplicate same-family non-consensus, two-family agreement, conflict, insufficient/no proposal, and closed authority.
- [ ] **Step 2: Run `python -m unittest tests.cew_cal01.test_interval_ocr_compare -v`** and require causal RED because the module does not exist.
- [ ] **Step 3: Implement the minimal reducer** with deterministic ordering and normalization that preserves raw text.
- [ ] **Step 4: Re-run the focused tests** and require PASS.
- [ ] **Step 5: Commit** `feat(cal01): add interval OCR comparison contract`.

### Task 2: Exact-crop local Tesseract families

**Files:**
- Create: `experiments/cew_cal01/interval_ocr_exact.py`
- Modify: `tests/cew_cal01/test_interval_ocr_compare.py`

**Interfaces:**
- Consumes: `interval-text-review-manifest.json` plus referenced crop files.
- Produces: `run_local_interval_ocr(review_dir: Path, external_observations: list[dict] | None = None) -> dict` and `interval-ocr-comparison.json`.

- [ ] **Step 1: Add RED tests** using an injected command runner to require exactly three fixed local families, stable family IDs, crop-digest verification, numeric whitelist, provider metadata and deterministic observation ordering.
- [ ] **Step 2: Run the focused tests** and require causal RED from the missing exact runner.
- [ ] **Step 3: Implement three local families**: normalized grayscale `psm 7`, thresholded line-suppressed `psm 7`, enlarged thresholded `psm 13`; record Tesseract version and do not infer corrections.
- [ ] **Step 4: Re-run focused tests and then `python -m unittest discover -s tests/cew_cal01 -p 'test_*.py' -v`**; require PASS.
- [ ] **Step 5: Commit** `feat(cal01): run comparative OCR on exact interval crops`.

### Task 3: Optional TrOCR observation importer

**Files:**
- Modify: `experiments/cew_cal01/interval_ocr_compare.py`
- Modify: `experiments/cew_cal01/interval_ocr_exact.py`
- Modify: `tests/cew_cal01/test_interval_ocr_compare.py`

**Interfaces:**
- Consumes: optional JSON list of external observations with `provider_id=TROCR`, `model_id`, `review_id`, `crop_sha256`, raw text and optional confidence.
- Produces: validated external rows included in comparison only when source/crop identity matches.

- [ ] **Step 1: Add RED tests** for valid TrOCR import, absent TrOCR input, wrong provider ID, unknown review ID and crop-digest mismatch.
- [ ] **Step 2: Run focused tests** and require causal RED.
- [ ] **Step 3: Implement validation/import only**; do not add network calls or model execution.
- [ ] **Step 4: Run focused and full CAL-01 contract suites** and require PASS.
- [ ] **Step 5: Commit** `feat(cal01): accept optional crop-bound TrOCR observations`.

### Task 4: Exact-source workflow integration and qualification

**Files:**
- Modify: `.github/workflows/validate-cew-cal01-external-chain.yml`
- Modify: `tests/cew_cal01/test_external_chain_workflow.py`

**Interfaces:**
- Consumes: Task 2 runner and exact review crops for TAV-01S/TAV-02S.
- Produces: `interval-ocr-comparison.json` per source inside the existing governed artifact.

- [ ] **Step 1: Add RED workflow contract assertions** requiring `python -m experiments.cew_cal01.interval_ocr_exact`, both comparison artifact paths, source/crop binding checks, `primary_anchor_count == 0`, human review required and closed canonical authority.
- [ ] **Step 2: Run the CAL-01 contract suite** and verify causal RED from missing workflow integration.
- [ ] **Step 3: Add workflow replay steps for both sources** after crop materialization and add structure/authority assertions without pinning recognized dimension values.
- [ ] **Step 4: Push the exact candidate and inspect `CEW-CAL-01 Primary Metric Calibration`, `CEW-CAL-01 External Dimension Chains`, and `CEW Repository Memory Gate` on the same SHA.**
- [ ] **Step 5: If all are green, record the exact head and artifact identity in the CAL-01 execution ledger; keep PR Draft and unmerged.**
- [ ] **Step 6: Commit** `ci(cal01): qualify comparative interval OCR`.