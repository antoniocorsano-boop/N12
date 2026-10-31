# CEW-COL-02 Human Graphical Review Rework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct only the two whole-symbol repairs rejected by bounded Human Graphical Review (`COL02-WSR-001` / `COL02-FP-0252` and `COL02-WSR-003` / `COL02-FP-0241`) while preserving the three accepted repairs and all closed authority boundaries.

**Architecture:** Keep the frozen 611 neutral proposals and the existing seeded local detector unchanged through candidate generation and scoring. Refine only final selection among nested plausible envelopes: the top-score candidate establishes the minimum four-side boundary quality; a smaller nested candidate may replace it only when its weakest boundary is not worse. This preserves the useful smallest-envelope bias for WSR-001 while preventing WSR-003's weak internal top edge from overriding a stronger outer envelope. Materially non-nested plausible competitors continue to fail closed.

**Tech Stack:** Python 3.12, OpenCV, unittest, GitHub Actions exact-source replay.

**Spec:** `docs/superpowers/specs/2026-10-31-cew-col02-axis-aware-whole-symbol-design.md`; governed review finding: `governance/cew-col02/COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW_v1.json`.

## Global Constraints

- Preserve all original `COL02-FP-*` IDs and the 611-proposal v1 payload unchanged.
- Modify no global proposal extraction, similarity threshold, OCR binding, support identity, family, section, fixed-line or structural identity logic.
- `COL02-FP-0106` remains rejected as `MISLOCALIZED_NOT_COLUMN`.
- `COL02-WSR-002`, `COL02-WSR-004`, and `COL02-WSR-005` are regression anchors and must not change geometrically.
- Any materially non-nested competing envelope remains `UNRESOLVED`.
- Reuse the existing `top_score - 0.08` plausibility window; introduce no new geometric acceptance threshold.
- `canonical_geometry_authorized=false`, `canonical_write_authorized=false`, `g2c_promotion_authorized=false`, `g3_authorized=false`, `merge_authorized=false`.
- No merge or deploy.

## Review Focus

- Nested internal horizontal line must not beat a stronger outer top boundary.
- Lower overshoot must collapse to a smaller nested envelope when that smaller envelope has equal-or-better weakest-side boundary evidence.
- Equal/near-equal non-nested envelopes remain unresolved.
- Previously accepted WSR-002/004/005 bboxes remain unchanged on exact-source replay.
- Half-scale fallback remains available only after native-scale failure.

---

### Task 1: Pin the Human Review failures as RED selection contracts

**Files:**
- Modify: `tests/cew_col02/test_axis_aware_local_envelope.py`

**Interfaces:**
- Consumes: candidate rows with `score`, `box`, and four-side `coverage`.
- Produces: regression contracts for nested candidate selection.

- [ ] Add a test proving a smaller nested candidate with a materially weaker top edge cannot override the top-score outer envelope.
- [ ] Add a test proving a smaller nested true envelope with equal-or-better weakest-side evidence is preferred over a lower overshoot.
- [ ] Add a test proving materially non-nested plausible candidates still fail closed.
- [ ] Run the focused test file and observe causal RED because the bounded selector seam does not yet exist.
- [ ] Commit test-only RED.

### Task 2: Make weakest-side graphical evidence the guard on nested selection

**Files:**
- Modify: `experiments/cew_col02/axis_aware_local_envelope.py`
- Test: `tests/cew_col02/test_axis_aware_local_envelope.py`

**Interfaces:**
- Produces: `_select_plausible_envelope(candidates) -> dict[str, Any] | None` used only after candidate generation/deduplication.

- [ ] Implement the minimal selector: sort by existing repair score; retain the existing `top_score - 0.08` plausibility window; fail closed for materially non-nested competitors; use the top-score candidate's weakest-side coverage as a floor; among nested plausible candidates meeting that floor choose the smallest area, then the stronger score.
- [ ] Replace the inline final selection with the helper; do not alter candidate-generation thresholds or scale fallback.
- [ ] Run the focused tests and the complete COL-02 unit suite; require GREEN.
- [ ] Commit implementation.

### Task 3: Exact-source qualification and bounded visual re-review

**Files:**
- No production files unless exact-source evidence exposes a causal defect.
- Update governed review evidence only after examining the regenerated overlays.

**Interfaces:**
- Consumes: exact-source Tav. 5 replay, five repair overlays, prior Human Graphical Review receipt.
- Produces: qualified repaired geometry or explicit remaining REWORK; no canonical promotion.

- [ ] Verify exact head and fresh unit workflow.
- [ ] Require exact-source replay to retain proposal count 611, five bounded repair tasks, R02 rejected, all authority flags closed.
- [ ] Download the fresh evidence artifact and compare WSR-001/003 against the source; compare WSR-002/004/005 bboxes to run #70 and require no drift.
- [ ] Record the bounded graphical re-review outcome. Keep `occurrence_coverage_complete=false` unless all five repairs are graphically accepted under the governed gate.
- [ ] Leave PR #175 Draft and non-promoting; no merge, G2C, G3 or deploy.
