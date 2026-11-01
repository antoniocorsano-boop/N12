# CEW-CAL-01 Primary Metric Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a replayable primary-evidence metric calibration for TAV.5 with frozen calibration/holdout anchors, affine fitting, independent validation, and 22 current metric candidate projections without using M0-G or historical affine coefficients in fitting.

**Architecture:** CEW-CAL-01 is a successor to qualified CEW-SPIRAL-01 head `ee23c221118064022fa77b694ff88119530cc454`. It first freezes source-bound anchor observations and their documented metric relations, then deterministically separates fit anchors from holdouts, estimates the minimum 2D affine model, validates only on excluded anchors, and projects the 22 current StructuralObjectCandidate records. Historical M0-G is loaded only after those outputs are frozen and remains an external regression witness.

**Tech Stack:** Python 3.12, existing CEW exact-source B01/TAV.5 toolchain, existing CEW-DXF-01 source-native reader where useful for candidate localization, `pytest`, deterministic JSON artifacts, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-01-cew-cal01-primary-metric-calibration-design.md`

## Global Constraints

- Predecessor exact SHA: `ee23c221118064022fa77b694ff88119530cc454`.
- Primary source authority: frozen TAV.5 source and governed source/raster bindings only.
- Historical M0-G nodes and historical affine coefficients MUST NOT enter anchor fitting or holdout selection.
- Historical CEW `S-*` annotations MUST NOT become primary calibration anchors.
- First model is 2D affine only.
- Minimum sufficiency: >=3 non-collinear fit anchors and >=2 holdout anchors with spatial separation; otherwise `INSUFFICIENT_PRIMARY_ANCHORS`.
- Holdout split is frozen before fitting and cannot use residuals.
- No automatic historical-node binding and no historical `N###` identity assignment.
- `structural_identity_authorized=false`, `canonical_geometry_authorized=false`, `canonical_write_authorized=false`, `m0g_authorized=false` throughout CEW-CAL-01.
- No merge or deploy is part of this plan.

## Review Focus

- **Circular calibration:** reject any anchor whose metric ordinate depends on the historical affine transform or M0-G node coordinates; pin in Task 2 provenance tests.
- **Degenerate affine fit:** fail closed for collinear/near-degenerate fit anchors rather than returning unstable coefficients; pin in Task 4.
- **Biased holdout selection:** prove split is determined from frozen anchor metadata, not residuals; pin in Task 3.
- **Mixed coordinate frames:** verify governed TAV.5 raster/source frame metadata before fitting or projection; pin in Tasks 2 and 6.
- **Hidden authority escalation:** every artifact and projection preserves closed authority regardless of residual quality; pin in Tasks 4–7.

---

### Task 0: Activate CEW-CAL-01 from the qualified predecessor

**Files:**
- Create: `governance/cew-cal01/CEW_CAL01_ACTIVATION_v1.json`
- Test: `tests/cew_cal01/test_activation_contract.py`

**Interfaces:**
- Consumes: predecessor SHA `ee23c221118064022fa77b694ff88119530cc454`, run `41317800420`, metric artifact id `13088253052`, digest `sha256:c0ffc5ed72db1bc26db242f27b1f7bea5fbecb9977681ec6b61e2d32bf107974`.
- Produces: frozen activation record that later tasks reference as `activation_ref`.

- [ ] **Step 1: Write the failing activation test** asserting predecessor SHA, all three predecessor jobs PASS, diagnostic min/median/max distances, authority closed, and `next_required_action=BUILD_PRIMARY_METRIC_CALIBRATION`.
- [ ] **Step 2: Run `pytest tests/cew_cal01/test_activation_contract.py -q`** and verify RED because the activation artifact does not exist.
- [ ] **Step 3: Create `CEW_CAL01_ACTIVATION_v1.json`** with the exact predecessor evidence and no promotion authority.
- [ ] **Step 4: Re-run the activation test** and require PASS.
- [ ] **Step 5: Commit** `governance(cew): activate CAL-01 primary calibration`.

### Task 1: Build the primary-anchor inventory contract

**Files:**
- Create: `experiments/cew_cal01/__init__.py`
- Create: `experiments/cew_cal01/anchor_inventory.py`
- Create: `tests/cew_cal01/test_anchor_inventory.py`
- Create: `governance/cew-cal01/CEW_CAL01_ANCHOR_SCHEMA_v1.json`

**Interfaces:**
- Consumes: governed TAV.5 source/raster binding; optional qualified DXF observations only as localization proposals.
- Produces: `PrimaryAnchorCandidate` records and `build_primary_anchor_inventory(...) -> dict`.

- [ ] **Step 1: Write RED tests** for deterministic IDs, allowed anchor classes, source-bound points, metric ordinate provenance, explicit rejection reasons, and rejection of `S-*`, M0-G, and historical-affine-derived inputs.
- [ ] **Step 2: Run the focused test file** and verify failure only because `cew_cal01.anchor_inventory` is absent.
- [ ] **Step 3: Implement minimal anchor record validation and inventory builder**; do not yet infer new anchors.
- [ ] **Step 4: Re-run tests** and require PASS.
- [ ] **Step 5: Commit** `feat(cew): add CAL-01 primary anchor contract`.

### Task 2: Discover and freeze real TAV.5 primary anchors

**Files:**
- Create: `experiments/cew_cal01/exact_source.py`
- Create: `experiments/cew_cal01/anchor_discovery.py`
- Create: `experiments/cew_cal01/validate_anchor_inventory.py`
- Test: `tests/cew_cal01/test_exact_source_anchor_inventory.py`
- Output artifact: `governance/cew-cal01/CEW_CAL01_PRIMARY_ANCHOR_INVENTORY_v1.json`

**Interfaces:**
- Consumes: frozen TAV.5 primary source, current governed raster binding, source-native vector/text observations where provenance is compatible.
- Produces: frozen anchor inventory with `eligible_for_fit` and provenance per metric ordinate.

- [ ] **Step 1: Write RED exact-source tests** that require source digest match, frame metadata, no historical comparator loaded, and zero accepted anchors whose metric coordinates originate from M0-G/historical affine/CEW-derived annotations.
- [ ] **Step 2: Implement source-native candidate discovery** for documented axis intersections, dimension-chain points, and other permitted source relations; every discovered anchor must bind back to TAV.5 evidence.
- [ ] **Step 3: Run discovery on exact source twice** and require identical inventory digest.
- [ ] **Step 4: Validate mathematical sufficiency**; if fewer than required independent anchors exist, emit `INSUFFICIENT_PRIMARY_ANCHORS` and stop rather than fabricating data.
- [ ] **Step 5: Commit** `feat(cew): freeze TAV5 primary anchors`.

### Task 3: Freeze deterministic calibration/holdout split

**Files:**
- Create: `experiments/cew_cal01/anchor_split.py`
- Test: `tests/cew_cal01/test_anchor_split.py`
- Output: `governance/cew-cal01/CEW_CAL01_ANCHOR_SPLIT_v1.json`

**Interfaces:**
- Consumes: frozen eligible anchor inventory.
- Produces: `split_anchors(inventory) -> AnchorSplit` with immutable `CALIBRATION` and `HOLDOUT` IDs.

- [ ] **Step 1: Write RED tests** for determinism, non-overlap, minimum counts, non-collinearity of fit anchors, holdout spatial separation, and invariance to any residual field added later.
- [ ] **Step 2: Implement deterministic spatial split** from frozen anchor IDs/positions only.
- [ ] **Step 3: Replay split twice** and require identical digest.
- [ ] **Step 4: Commit** `feat(cew): freeze CAL-01 holdout split`.

### Task 4: Estimate the source-derived affine transform

**Files:**
- Create: `experiments/cew_cal01/affine_fit.py`
- Test: `tests/cew_cal01/test_affine_fit.py`
- Output: `governance/cew-cal01/CEW_CAL01_AFFINE_CALIBRATION_v1.json`

**Interfaces:**
- Consumes: calibration anchors only.
- Produces: `fit_affine(calibration_anchors) -> AffineCalibration` with coefficients, determinant, residuals, source/split digests, and closed authority.

- [ ] **Step 1: Write RED synthetic tests** for exact affine recovery, noisy overdetermined recovery, collinear rejection, singular/near-singular rejection, and authority closure.
- [ ] **Step 2: Implement least-squares 2D affine fit** with deterministic ordering and explicit degeneracy checks.
- [ ] **Step 3: Run unit tests** and require PASS.
- [ ] **Step 4: Fit on frozen real calibration anchors** without loading holdouts or historical witnesses.
- [ ] **Step 5: Commit** `feat(cew): fit primary TAV5 affine calibration`.

### Task 5: Validate exclusively on frozen holdouts

**Files:**
- Create: `experiments/cew_cal01/holdout_validation.py`
- Test: `tests/cew_cal01/test_holdout_validation.py`
- Output: `governance/cew-cal01/CEW_CAL01_HOLDOUT_VALIDATION_v1.json`

**Interfaces:**
- Consumes: frozen affine calibration + holdout anchors.
- Produces: holdout-only residual report with RMS/median/max and no promotion decision.

- [ ] **Step 1: Write RED tests** proving holdouts never occur in fit anchor IDs and validation cannot alter coefficients.
- [ ] **Step 2: Implement residual report** with per-anchor vectors and aggregate statistics.
- [ ] **Step 3: Verify `historical_comparator_loaded=false`** in the validation artifact.
- [ ] **Step 4: Commit** `feat(cew): validate CAL-01 on holdout anchors`.

### Task 6: Project the 22 current StructuralObjectCandidate records

**Files:**
- Create: `experiments/cew_cal01/current_projection.py`
- Test: `tests/cew_cal01/test_current_projection.py`
- Output: `governance/cew-cal01/CEW_CAL01_CURRENT_CANDIDATE_PROJECTION_v1.json`

**Interfaces:**
- Consumes: qualified 22-object source-derived bundle + frozen affine calibration.
- Produces: 22 metric candidate positions with transform digest and uncertainty context; no historical-node binding.

- [ ] **Step 1: Write RED tests** requiring exactly 22 projections, stable one-to-one occurrence/object mapping, correct frame conversion, no `N###` requirement, and all authority flags false.
- [ ] **Step 2: Implement deterministic projection** from governed source centers through the frozen affine transform.
- [ ] **Step 3: Replay twice** and require identical digest.
- [ ] **Step 4: Commit** `feat(cew): project current columns with primary calibration`.

### Task 7: Compare against historical M0-G only after freeze

**Files:**
- Create: `experiments/cew_cal01/historical_comparison.py`
- Test: `tests/cew_cal01/test_historical_comparison.py`
- Output: `governance/cew-cal01/CEW_CAL01_HISTORICAL_COMPARISON_v1.json`

**Interfaces:**
- Consumes: already-frozen current projection + immutable historical M0-G witness.
- Produces: diagnostic distance comparison only.

- [ ] **Step 1: Write RED tests** proving historical data is loaded after projection, cannot mutate transform/projection digests, and produces no binding or threshold.
- [ ] **Step 2: Implement diagnostic comparison** against G4 `SUPPORT_CORE` witness nodes.
- [ ] **Step 3: Compare new residual distribution to predecessor diagnostic baseline** without defining pass/fail from distance alone.
- [ ] **Step 4: Commit** `feat(cew): audit primary calibration against historical M0-G`.

### Task 8: Exact-source qualification workflow

**Files:**
- Create: `.github/workflows/validate-cew-cal01.yml`
- Create: `governance/cew-cal01/CEW_CAL01_QUALIFICATION_SCHEMA_v1.json`
- Create: `experiments/cew_cal01/validate_artifacts.py`
- Test: `tests/cew_cal01/test_qualification_contract.py`

**Interfaces:**
- Consumes: Tasks 0–7.
- Produces: one exact-SHA qualification receipt and separate artifacts for anchors, split, calibration, holdout validation, current projection, and post-freeze historical audit.

- [ ] **Step 1: Write RED workflow contract tests** for exact checkout, frozen source digests, deterministic rerun, and authority closure.
- [ ] **Step 2: Implement workflow** using the minimum required toolchain; do not reinstall unrelated B01 dependencies where artifacts can be safely passed within the same run.
- [ ] **Step 3: Run exact-source qualification twice where determinism requires it** and compare artifact digests.
- [ ] **Step 4: Record final qualification receipt** including whether primary-anchor sufficiency was achieved.
- [ ] **Step 5: Commit** `ci(cew): qualify CAL-01 primary metric calibration`.

### Task 9: Technical handoff, no promotion

**Files:**
- Create: `governance/cew-cal01/CEW_CAL01_HANDOFF_v1.json`
- Modify: PR body for the CEW-CAL-01 successor PR.

**Interfaces:**
- Consumes: exact-SHA qualification receipt.
- Produces: one of `PRIMARY_CALIBRATION_QUALIFIED_NONCANONICAL`, `INSUFFICIENT_PRIMARY_ANCHORS`, or `REWORK_REQUIRED` plus the next residual.

- [ ] **Step 1: Summarize evidence and residuals** without converting geometric quality into structural identity.
- [ ] **Step 2: Keep canonical/structural authority closed** unless a later explicit governance action authorizes promotion.
- [ ] **Step 3: Record next action**: canonical-geometry promotion gate if sufficient, otherwise targeted acquisition of missing primary anchors.
- [ ] **Step 4: Commit** `governance(cew): hand off CAL-01 qualification`.
