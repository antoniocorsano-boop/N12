# CEW COL-02 Review-Directed Outer-Envelope Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the single remaining WSR-003 top-truncation defect without modifying the generic local-envelope detector or changing any already accepted repair geometry.

**Architecture:** Add a separate review-directed completion module. It consumes an explicitly authorized graphical `REWORK`, freezes the three already reliable sides, searches only the reviewed missing side for one coherent outer closure, and fails closed on ambiguity. Integrate it into the exact-source repair producer only for the authorized WSR-003 finding.

**Tech Stack:** Python 3.12, OpenCV, `unittest`, existing COL-02 exact-source workflow.

**Spec:** `docs/superpowers/specs/2026-10-31-cew-col02-review-directed-outer-envelope-completion-design.md`

## Global Constraints

- Frozen proposal count remains `611`; proposal IDs remain immutable.
- Do not modify `axis_aware_local_envelope.py` to solve WSR-003.
- Only `COL02-WSR-003` / `COL02-FP-0241` may enter review-directed completion.
- Only the review finding `TOP_TRUNCATED_INTERNAL_LINE_SELECTED` is supported.
- Preserve left, right and bottom coordinates during top completion.
- Ambiguity returns unresolved; no best-effort guessing.
- No OCR/semantic/structural inference.
- Canonical geometry/write, G2C, G3, merge and deploy remain unauthorized.

## Review Focus

- Multiple strong horizontal edges above the current top → `UNRESOLVED`, not arbitrary selection.
- Weak left/right closure from candidate top to frozen bottom → `UNRESOLVED`.
- Unsupported review finding → completion not authorized.
- Review-authorized completion failure → known-invalid base repair must not remain review-ready.
- Non-target repairs → exact reconstructed coordinates must remain unchanged.

---

### Task 1: Pin review-directed completion as RED

**Files:**
- Create: `tests/cew_col02/test_review_directed_outer_envelope.py`

**Interfaces:**
- Consumes: governed review finding `TOP_TRUNCATED_INTERNAL_LINE_SELECTED`.
- Produces: failing behavioral contracts for the new completion component.

- [ ] Add a synthetic top-truncation test: a complete rectangle has an internal horizontal line selected as the current top; completion must extend only `y/height` to the true outer top while preserving `x`, `width` and bottom.
- [ ] Add ambiguity test: two equally coherent outer-top closures must return `None`.
- [ ] Add weak-three-side-anchor test: completion must return `None` when left/right/bottom evidence is insufficient.
- [ ] Add receipt authorization test using `COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW_v1.json`: only `COL02-FP-0241` is authorized for this stage.
- [ ] Run the focused test file and require causal RED because the module/functions do not yet exist.
- [ ] Commit test-only RED.

### Task 2: Implement bounded top completion

**Files:**
- Create: `experiments/cew_col02/review_directed_outer_envelope.py`
- Test: `tests/cew_col02/test_review_directed_outer_envelope.py`

**Interfaces:**
- Produces: `authorized_completion_requests(receipt: dict[str, Any]) -> dict[str, str]`.
- Produces: `complete_review_directed_outer_envelope(image: np.ndarray, base_result: dict[str, Any], *, finding: str) -> dict[str, Any] | None`.

- [ ] Validate the review receipt schema and closed authority; expose only `REWORK` rows with the supported finding.
- [ ] Require strong existing left/right/bottom evidence before attempting completion.
- [ ] Convert the base bbox to pixel coordinates; freeze left/right/bottom.
- [ ] Search a bounded region above the current top for horizontal line bands using only grayscale geometry.
- [ ] For each top candidate compute top-edge coverage plus continuity of both frozen vertical sides to the frozen bottom.
- [ ] Reject weak candidates and fail closed when two materially distinct candidates have equivalent closure evidence.
- [ ] Return a copy of the base result with only the top coordinate/height changed and with review-directed provenance; otherwise return `None`.
- [ ] Run focused tests, then the complete COL-02 unit suite; require PASS.
- [ ] Commit GREEN implementation.

### Task 3: Integrate only the governed WSR-003 exception

**Files:**
- Modify: `experiments/cew_col02/axis_aware_whole_symbol_exact_source.py`
- Test: `tests/cew_col02/test_review_directed_outer_envelope.py`

**Interfaces:**
- Consumes: `authorized_completion_requests(...)` and `complete_review_directed_outer_envelope(...)` from Task 2.
- Produces: exact-source repair manifest where only WSR-003 may differ from run #80.

- [ ] Load the graphical review receipt separately from the residual-reconciliation receipt.
- [ ] Build the generic five repair results exactly as before.
- [ ] Apply review-directed completion only to an explicitly authorized candidate.
- [ ] If completion returns `None`, replace that known-invalid repair result with `None` so the manifest becomes unresolved rather than review-ready.
- [ ] Add/extend a unit contract proving unsupported/non-target candidates are untouched and authorized unresolved completion does not preserve the invalid base result.
- [ ] Run complete COL-02 unit suite; require PASS.
- [ ] Commit integration.

### Task 4: Exact-source qualification and graphical gate

**Files:**
- Evidence only from GitHub Actions artifact.
- If and only if all five pass: create `governance/cew-col02/COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW_v2.json`.

**Interfaces:**
- Consumes: exact head produced by Task 3.
- Produces: qualification checkpoint, and v2 graphical receipt only on full five-case acceptance.

- [ ] Require `CEW-COL-02 Footprint Text Binding` unit + exact-source jobs PASS on the same exact SHA.
- [ ] Download the fresh artifact and verify proposal count `611` and immutable ID space.
- [ ] Compare WSR-001/002/004/005 reconstructed bboxes against run #80; require exact coordinate equality.
- [ ] Inspect fresh WSR-003 source-only and overlay: red bbox must follow the complete visible outer rectangle, including the previously excluded top portion.
- [ ] Inspect the four preserved overlays for regressions.
- [ ] If all five are accepted, record v2 receipt while keeping `occurrence_coverage_complete=false` unless the governing occurrence-coverage contract is separately satisfied.
- [ ] Record the exact SHA/run/artifact/digest on PR #175.
- [ ] Keep PR #175 Draft and non-promoting; no merge, G2C, G3 or deploy.
