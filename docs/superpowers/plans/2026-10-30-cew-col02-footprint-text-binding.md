# CEW-COL-02 Footprint/Text Binding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reuse CEW's historical footprint/prototype acquisition stack and add only the residual deterministic text-to-footprint binding plus target-explicit Human Review needed to repair COL-01.

**Architecture:** COL-02 remains an experiment layer on immutable TAV-05S. A pure geometry binder classifies OCR/text observations relative to footprint proposals; a bounded port of the PR #136 prototype-similarity core ranks footprint candidates without known support IDs; exact-source export then produces paired source-only and target-explicit review crops. Existing structural/canonical authority remains closed.

**Tech Stack:** Python 3.12, OpenCV/PyMuPDF toolchain already used by B01/COL-01, unittest, GitHub Actions.

**Spec:** `docs/experiments/2026-10-30-cew-col02-footprint-text-binding-design.md`

## Global Constraints

- Exact source: `archive/documentazione_originaria/tavola 5.pdf`, page `0`, SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Historical 34-support / five-family register is benchmark evidence only and must never generate candidates or inject missing IDs.
- Symmetry axes are optional evidence, never a candidate prerequisite.
- OCR/text is relational evidence, never a candidate prerequisite or structural identity source.
- Reuse/port the smallest coherent PR #136 prototype-search and axis-suppressed footprint proposal slices; do not create a new generic column detector.
- Structural identity, support-ID assignment, family/section assignment, fixed lines, canonical geometry/write, G2C/G3 and merge remain unauthorized.
- Human graphical decision and text-binding decision remain separate.

## Review Focus

1. **Text centered inside a footprint but larger than/partly outside it** must not be falsely classified `INSIDE_FOOTPRINT`; Task 1 tests contained fraction plus center condition.
2. **Dimension text just outside a footprint** must remain `NEAR_OUTSIDE_FOOTPRINT`, never preferred as an internal label; Tasks 1–2 test this explicitly.
3. **Multiple internal numeric tokens** must remain ambiguous instead of silently choosing one; Task 2 pins this.
4. **Elongated footprint without axes** must remain eligible for prototype similarity; Task 3 includes a 30×110/110×30-shaped synthetic case without axis evidence.
5. **Human confirmation of a column** must not automatically confirm a text binding; Task 4 manifest/receipt contract tests the two decisions as independent fields.

---

### Task 1: Pure text-to-footprint spatial relation

**Files:**
- Create: `experiments/cew_col02/__init__.py`
- Create: `experiments/cew_col02/text_footprint_binding.py`
- Create: `tests/cew_col02/test_text_footprint_binding.py`
- Create/Modify: `.github/workflows/validate-cew-col02-footprint-text-binding.yml`

**Interfaces:**
- Consumes: footprint bbox and text bbox dictionaries using `{x, y, width, height}` in one coordinate system.
- Produces: `classify_text_relation(footprint: dict, text: dict, *, near_radius: float = 0.35) -> dict` with `relation`, `intersection_area`, `text_contained_fraction`, `center_in_footprint`, `normalized_center_distance`, `edge_distance`.

- [ ] **Step 1: Write failing tests** for `INSIDE_FOOTPRINT`, `INTERSECTS_FOOTPRINT`, `NEAR_OUTSIDE_FOOTPRINT`, `UNRELATED_OR_UNBOUND`, zero-area rejection and a center-inside/low-contained-fraction negative case.
- [ ] **Step 2: Run** `python -m unittest tests.cew_col02.test_text_footprint_binding -v`; expect import/function failure only.
- [ ] **Step 3: Implement minimal pure geometry classifier** with `INSIDE_FOOTPRINT` requiring text center inside and contained fraction `>= 0.80`.
- [ ] **Step 4: Run the Task 1 tests** and expect all PASS.
- [ ] **Step 5: Commit** `feat(col02): add text footprint relation classifier`.

### Task 2: Internal-label selection without false binding

**Files:**
- Modify: `experiments/cew_col02/text_footprint_binding.py`
- Create: `tests/cew_col02/test_internal_text_selection.py`

**Interfaces:**
- Consumes: one footprint plus iterable text observations containing stable token IDs and bboxes.
- Produces: `bind_text_observations(footprint: dict, observations: list[dict]) -> dict` containing `bindings`, `internal_token_ids`, `preferred_internal_token_id`, `binding_state`; states include `NO_INTERNAL_TEXT`, `ONE_INTERNAL_TEXT`, `MULTIPLE_INTERNAL_TEXT_AMBIGUOUS`.

- [ ] **Step 1: Write failing tests** proving one internal token is preferred, external dimension text is never preferred, multiple internal tokens remain ambiguous, and no internal token remains explicit.
- [ ] **Step 2: Run** `python -m unittest tests.cew_col02.test_internal_text_selection -v`; expect missing function failure.
- [ ] **Step 3: Implement minimal binding aggregation** using Task 1 relations only; no OCR semantics or expected-ID lookup.
- [ ] **Step 4: Run Task 1+2 tests** and expect all PASS.
- [ ] **Step 5: Commit** `feat(col02): bind internal text to footprint candidates`.

### Task 3: Reuse historical footprint/prototype retrieval core

**Files:**
- Create: `experiments/cew_col02/footprint_similarity.py`
- Create: `experiments/cew_col02/footprint_proposals.py`
- Create: `tests/cew_col02/test_footprint_similarity.py`
- Create: `tests/cew_col02/test_footprint_proposals.py`

**Interfaces:**
- Consumes: a human prototype bbox plus footprint proposal rows independent of support identity.
- Produces: `rank_similar_footprints(prototype_bbox: dict, proposals: list[dict], *, limit: int = 64) -> list[dict]` and `extract_footprint_proposals(image, *, max_candidates: int = 6000) -> dict`.

- [ ] **Step 1: Port test expectations from PR #136** for size/aspect similarity, rectangularity, envelope preference, prototype-overlap exclusion and candidate NMS; add a synthetic elongated no-axis candidate that must remain eligible.
- [ ] **Step 2: Run similarity tests** and capture causal RED because the port does not yet exist.
- [ ] **Step 3: Port/adapt the bounded similarity core** from PR #136 commit `3087c715e403d29418e5bb3ec81e6376caab93d9`, removing support/family-ID dependency and preserving proposal-only authority.
- [ ] **Step 4: Run similarity tests** and expect PASS.
- [ ] **Step 5: Write failing footprint-proposal tests** for long-axis suppression and nested-subcontour suppression using synthetic rasters; expected result must not depend on historical family IDs.
- [ ] **Step 6: Port/adapt PR #136 raster proposal logic** so family ratios are not identity/candidate oracles; broad geometry + prototype compatibility own retrieval.
- [ ] **Step 7: Run Task 3 tests plus Task 1–2 suite** and expect all PASS.
- [ ] **Step 8: Commit** `feat(col02): reuse footprint prototype retrieval core`.

### Task 4: Exact-source target-explicit review package

**Files:**
- Create: `experiments/cew_col02/exact_source_audit.py`
- Create: `experiments/cew_col02/review_export.py`
- Create: `tests/cew_col02/test_review_manifest.py`
- Modify: `.github/workflows/validate-cew-col02-footprint-text-binding.yml`
- Create: `governance/cew-col02/COL02_EXACT_SOURCE_AUDIT_v1.json` only after a successful exact-source run and Human Review status remains pending.

**Interfaces:**
- Consumes: immutable B01 source contract/zoning/raster chain, footprint proposals, prototype bbox/reference, OCR observations, Task 1–3 components.
- Produces: deterministic JSON manifest plus paired `source-only` and `overlay` crops; manifest fields independently store `column_graphic_decision` and `text_binding_decision`.

- [ ] **Step 1: Write failing manifest tests** requiring exact footprint bbox, exact token bbox/token ID, relation metrics, separate human decision fields, source provenance and all authority booleans false.
- [ ] **Step 2: Run manifest tests** and capture causal RED.
- [ ] **Step 3: Implement target-explicit review exporter**; overlay must mark candidate footprint and text bbox separately while preserving an untouched crop.
- [ ] **Step 4: Run unit suite** and expect all PASS.
- [ ] **Step 5: Wire exact-source runner** to frozen TAV-05S using existing B01 source contract/zoning; OCR failure remains visible and no benchmark ID may enter generation.
- [ ] **Step 6: Run exact-source workflow** on exact candidate SHA; require deterministic replay and artifact upload, not a specific recall threshold.
- [ ] **Step 7: Inspect artifact metrics** including relation-state counts, single/multiple internal-token counts and benchmark reporting for `18`, `23`, `30` only after generation.
- [ ] **Step 8: Create governed audit receipt** recording measured result, artifact digest and `HUMAN_REVIEW_PENDING`; keep support identity/structural/canonical authority false.
- [ ] **Step 9: Re-run full workflow on receipt head** and require unit + exact-source + Repository Memory PASS on the same exact SHA before stronger checkpoint language.
- [ ] **Step 10: Commit** `governance(col02): record exact source footprint text audit`.

## Final verification

- [ ] Run all `tests/cew_col02` and confirm zero failures.
- [ ] Confirm exact-source workflow PASS on the current receipt head.
- [ ] Confirm Repository Memory Gate PASS on the same current head.
- [ ] Confirm artifact source SHA-256 equals the frozen TAV-05S digest.
- [ ] Confirm no generated candidate contains a support identity injected from the historical benchmark.
- [ ] Confirm authority remains false for support identity, family/section assignment, fixed lines, structural identity, canonical write, G2C, G3 and merge.
- [ ] Leave the PR Draft until target-explicit Human Review is completed.
