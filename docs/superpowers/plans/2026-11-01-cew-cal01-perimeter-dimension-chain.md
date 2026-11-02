# CEW-CAL-01 Perimeter Dimension-Chain Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic exact-source discovery of true planimetric dimension chains in the external bands around the TAV.5 structural-plan envelope, without promoting section measures or OCR tokens to metric authority.

**Architecture:** A new `perimeter_dimension.py` module derives a localization-only structural envelope and four clipped perimeter bands from the exact raster. It runs numeric OCR only inside those bands, then reuses the existing two-reference geometry detector to keep only source-bound dimension-chain candidates. The workflow runs this stage after exact-source raster creation and archives its governed JSON/overlay with authority closed.

**Tech Stack:** Python 3.12, OpenCV, NumPy, Tesseract 5.x, unittest, existing CEW-CAL-01 exact-source contracts.

**Spec:** `docs/superpowers/specs/2026-11-01-cew-cal01-perimeter-dimension-chain-design.md`

## Global Constraints

- Exact source SHA-256: `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Historical M0-G, historical affine, historical `S-*`, and TAV02 inputs remain forbidden.
- Search regions have localization authority only.
- OCR alone never creates a metric relation.
- `primary_anchor_count` remains `0`.
- Human `PRIMARY_VISUAL_VALIDATED` review is required before any candidate can enter the metric-relation inventory.
- No merge or deploy is part of this plan.

## Review Focus

- Faint structural linework split into multiple components: envelope selection must either recover one qualifying component or fail closed.
- Title block has high ink density: selection must prefer structural-plan span constraints, not raw component area.
- Bands touching page boundaries: clipping must keep all coordinates in frame.
- Section/identifier numbers inside the inner overlap: they must remain observations unless the two-reference geometry gate binds them.
- Zero bound perimeter candidates: result must be valid and report `PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED`, not fail or manufacture anchors.

---

### Task 1: Structural envelope and perimeter bands

**Files:**
- Create: `experiments/cew_cal01/perimeter_dimension.py`
- Create: `tests/cew_cal01/test_perimeter_dimension.py`

**Interfaces:**
- Produces: `detect_structural_plan_envelope(gray) -> dict`, `build_perimeter_bands(envelope_bbox, page_width, page_height, outer_margin_px, inner_overlap_px) -> list[dict]`.

- [ ] **Step 1: Write failing tests** for portrait normalization, title-block rejection by span constraints, deterministic envelope selection, and clipped four-band geometry.
- [ ] **Step 2: Run** `python -m unittest tests.cew_cal01.test_perimeter_dimension -v`; expected RED because the module/functions do not exist.
- [ ] **Step 3: Implement the minimal envelope/band functions** using landscape normalization, reduced threshold image, 9×9 dilation at the normalized 2200px-width detection frame, and the spec’s 45%/60% span gates.
- [ ] **Step 4: Re-run the task test and full `tests/cew_cal01` suite**; expected PASS.
- [ ] **Step 5: Commit** `feat(cal01): detect structural perimeter search bands`.

### Task 2: Perimeter OCR and dimension-chain binding

**Files:**
- Modify: `experiments/cew_cal01/perimeter_dimension.py`
- Modify: `tests/cew_cal01/test_perimeter_dimension.py`

**Interfaces:**
- Consumes: Task 1 envelope and band records.
- Produces: `build_perimeter_dimension_discovery(image_path, base_discovery_path, output_dir) -> dict`.

- [ ] **Step 1: Write failing tests** proving that OCR observations are preserved, only `geometry.geometrically_bound == True` observations become `PERIMETER_LINEAR_DIMENSION_CANDIDATE`, zero candidates yield `PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED`, and authority/anchor count stay closed.
- [ ] **Step 2: Run the focused test**; expected RED for missing discovery function/behavior.
- [ ] **Step 3: Implement minimal discovery** with Tesseract numeric whitelist in the four bands, exact coordinate backprojection, existing `normalize_dimension_text`, `proposal_from_ocr_token`, and `_dimension_geometry_cv2`.
- [ ] **Step 4: Produce deterministic JSON and overlay** with source digest, envelope, bands, observations, candidates and rejection reasons.
- [ ] **Step 5: Run focused and full CAL-01 tests**; expected PASS.
- [ ] **Step 6: Commit** `feat(cal01): discover perimeter dimension chains`.

### Task 3: Exact-source workflow integration

**Files:**
- Modify: `.github/workflows/validate-cew-cal01.yml`
- Modify: `tests/cew_cal01/test_perimeter_dimension.py`

**Interfaces:**
- Consumes: Task 2 CLI/module.
- Produces: governed `perimeter/perimeter-dimension-discovery.json` and `perimeter/perimeter-search-overlay.png` in the existing CAL-01 artifact.

- [ ] **Step 1: Add failing contract assertions** for source digest, four bands, `primary_anchor_count == 0`, all historical-input flags false, and closed canonical authority.
- [ ] **Step 2: Update workflow** to run perimeter discovery immediately after exact-source raster creation and include perimeter assertions in the governed evidence step.
- [ ] **Step 3: Run contract suite**; expected PASS locally/CI once implementation is present.
- [ ] **Step 4: Push exact candidate and inspect CEW-CAL-01 workflow**; exact-source job must complete and archive the perimeter outputs.
- [ ] **Step 5: Commit** `ci(cal01): qualify perimeter dimension discovery`.

### Task 4: Exact-source evidence assessment

**Files:**
- Create or modify only governed evidence under `governance/cew-cal01/` if needed to record the result; no authority promotion.

**Interfaces:**
- Consumes: qualified workflow artifact from Task 3.
- Produces: a factual checkpoint stating observed perimeter candidate count and whether human review is warranted.

- [ ] **Step 1: Read the exact artifact** and verify source SHA and candidate geometry records.
- [ ] **Step 2: If candidates exist, generate a human-review contact sheet directly from exact-source coordinates; if zero, record `PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED` and proceed later to internal-chain discovery.**
- [ ] **Step 3: Do not alter `primary_anchor_count`, structural identity, canonical geometry or M0-G authority.**
