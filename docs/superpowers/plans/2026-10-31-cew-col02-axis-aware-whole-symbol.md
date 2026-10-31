# CEW-COL-02 Axis-aware Whole-symbol Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the five human-confirmed fragmented COL-02 proposals into derived whole-symbol graphical repair candidates while rejecting the one mislocalized R02 target and preserving the original 611-proposal ID space.

**Architecture:** Keep `CEW_COL02_FOOTPRINT_PROPOSALS_v1` immutable. Add a seeded axis-aware reconstruction helper driven only by raster geometry and the governed six-case Human Review receipt; generate a separate exact-source repair manifest/atlas with new repair-local IDs. No repair output is canonical or structurally identified.

**Tech Stack:** Python 3.12.15, OpenCV 5.0.0.93 unit dependency, existing frozen CEW-B01 exact-source toolchain, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-31-cew-col02-axis-aware-whole-symbol-design.md`

## Global Constraints

- Preserve all existing `COL02-FP-*` IDs and the 611-proposal v1 payload unchanged.
- Repair only the five explicit `FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY` seeds.
- `COL02-FP-0106` is `MISLOCALIZED_NOT_COLUMN` and must not be repaired.
- Use only graphical source evidence; no support IDs, OCR identity, family ratios, expected dimensions, or structural identity.
- Fail closed on zero or ambiguous whole-symbol envelopes.
- Canonical geometry/write, G2C, G3 and merge remain unauthorized.

## Review Focus

- Thick scanned axes that create wider-than-3px gaps must still reconstruct the outer rectangle.
- A beam/column junction must not qualify without a four-side enclosing envelope.
- A seed near but not on the axis crossing must still bind to the correct local crossing.
- Multiple equally valid enclosing rectangles must return unresolved rather than choosing by ID/order.
- The original 611-proposal replay count and IDs must remain stable after adding the repair helper.

---

### Task 1: Govern the six-case Human Review result

**Files:**
- Create: `governance/cew-col02/COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW_v1.json`
- Test: `tests/cew_col02/test_axis_aware_whole_symbol_receipt.py`

**Interfaces:**
- Consumes: PR #175 review task IDs R01–R06 and their source proposal IDs.
- Produces: `load_axis_aware_repair_receipt(path)` validation contract and the exact five repair seeds plus one rejected seed.

- [ ] **Step 1: Write the failing receipt-validation test** asserting five fragmented findings, R02 mislocalized, exact candidate IDs, and all structural/canonical authority flags false.
- [ ] **Step 2: Run the COL-02 unit suite and verify RED** because the governed receipt/loader does not yet exist.
- [ ] **Step 3: Add the receipt and minimal fail-closed loader** in a focused module `experiments/cew_col02/axis_aware_whole_symbol.py`.
- [ ] **Step 4: Run the full COL-02 unit suite and verify GREEN.**
- [ ] **Step 5: Commit** `feat: govern COL-02 residual geometry findings`.

### Task 2: Reconstruct a whole symbol around an orthogonal axis crossing

**Files:**
- Modify: `experiments/cew_col02/axis_aware_whole_symbol.py`
- Test: `tests/cew_col02/test_axis_aware_whole_symbol.py`

**Interfaces:**
- Consumes: grayscale analysis raster plus a normalized seed bbox.
- Produces: `reconstruct_axis_split_whole_symbol(image, seed_bbox) -> dict | None` with bbox, axis-cross evidence and deterministic geometric diagnostics.

- [ ] **Step 1: Write RED synthetic tests** for: complete outer rectangle split into four quadrants by orthogonal axes; thick axes; beam/column junction rejection; ambiguous double-envelope rejection.
- [ ] **Step 2: Run tests and verify failures are caused by missing reconstruction behavior.**
- [ ] **Step 3: Implement the minimal geometry-only reconstruction:** reproduce v1 threshold/axis masks, select a bounded orthogonal crossing near the seed, directionally bridge only observed axis-width gaps, require four-side envelope evidence, fail closed on ambiguity.
- [ ] **Step 4: Add a regression assertion that `extract_footprint_proposals()` output on the existing synthetic fixture is unchanged.**
- [ ] **Step 5: Run the complete COL-02 unit suite and verify GREEN.**
- [ ] **Step 6: Commit** `feat: reconstruct axis-split whole column symbols`.

### Task 3: Exact-source repair manifest and target-explicit atlas

**Files:**
- Create: `experiments/cew_col02/axis_aware_whole_symbol_exact_source.py`
- Modify: `.github/workflows/validate-cew-col02-footprint-text-binding.yml`
- Test: `tests/cew_col02/test_axis_aware_whole_symbol_manifest.py`

**Interfaces:**
- Consumes: frozen Tav. 5 exact source, governed Human Review receipt, immutable 611 proposals.
- Produces: `col02-axis-aware-whole-symbol-repair.json`, five-or-fewer repair records with new `COL02-WSR-*` IDs, and `col02-axis-aware-whole-symbol-repair-atlas.png`.

- [ ] **Step 1: Write RED manifest tests** asserting R02 is rejected, only five seeds are repair-eligible, derived IDs never replace `COL02-FP-*`, unresolved repairs remain explicit, authority remains closed.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement exact-source runner and atlas rendering.** Red bbox = reconstructed whole-symbol candidate; source-only image remains side-by-side.
- [ ] **Step 4: Extend workflow** to run the repair after residual reconciliation and assert the original proposal count remains exactly 611.
- [ ] **Step 5: Run full unit suite and exact-source workflow; verify GREEN and capture artifact digest.**
- [ ] **Step 6: Commit** `ci: qualify COL-02 axis-aware whole-symbol repair`.

### Task 4: Record qualification and stop before promotion

**Files:**
- Modify: PR #175 description/comment only.

**Interfaces:**
- Consumes: exact-source repair artifact and workflow evidence.
- Produces: a bounded Human Graphical Review checkpoint; no canonical write.

- [ ] **Step 1: Verify exact head, workflow success, artifact digest and absence of open review threads.**
- [ ] **Step 2: Record counts:** repaired / unresolved / rejected.
- [ ] **Step 3: Keep PR Draft and explicitly record `occurrence_coverage_complete = false` until Human Graphical Review of the repaired atlas.**
- [ ] **Step 4: Do not merge or promote G2C/G3.**
