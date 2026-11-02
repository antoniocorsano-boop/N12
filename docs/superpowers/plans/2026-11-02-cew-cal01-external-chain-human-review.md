# CEW-CAL-01 External Chain Human Review Reconciliation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile both earlier geometry-bound human receipts and direct exact-bound professional decisions into the governed external-chain review packet, while keeping all validated relations non-calibrating and all structural/canonical authority closed.

**Architecture:** Preserve the existing geometry-reconciliation path for earlier structural-grid receipts. Add a separate direct-decision path keyed by exact source SHA + `interval_review_id + crop_sha256`, merge the two paths fail-closed, and keep presentation-oriented context crops separate from governed exact crops.

**Tech Stack:** Python 3.12, `unittest`, GitHub Actions, deterministic JSON artifacts.

**Spec:** `docs/superpowers/specs/2026-11-02-cew-cal01-external-chain-human-review-design.md`

## Global Constraints

- Never generate `HUMAN_PROFESSIONAL_USER` decisions automatically.
- Never use OCR or AI precheck to create `PRIMARY_VISUAL_VALIDATED` state.
- Earlier receipt reuse requires exact source SHA and unambiguous geometric containment after the governed rotation transform.
- Direct decisions require exact source SHA + existing interval id + exact crop digest.
- Validated relations authorize relation-network use only; `eligible_for_metric_calibration=false`, `primary_anchor_authorized=false`.
- Conflicting or ambiguous evidence fails closed.
- Presentation-oriented context crops may improve legibility but cannot replace canonical crop digests.
- No historical affine, M0-G identity, structural identity or canonical write authority is opened.
- No merge or deploy.

## Review Focus

- Direct decision references an unknown interval: fail closed.
- Direct decision crop SHA differs from current manifest: fail closed.
- Direct and geometry-based evidence conflict on one interval: fail closed.
- Duplicate same-value direct evidence: deterministic deduplication, one validated relation.
- Vertical presentation crop orientation/context changes: governed exact crop id/digest remain unchanged.

---

### Task 1: Preserve earlier receipt reconciliation

**Files:**
- Existing: `experiments/cew_cal01/external_chain_human_review.py`
- Existing: `tests/cew_cal01/test_external_chain_human_review.py`

**Interfaces:**
- Consumes: prior structural-grid receipt with source bbox.
- Produces: geometry-reconciled binding keyed by interval review id.

- [x] Keep RED/GREEN coverage for 90° CCW source-frame transform.
- [x] Keep exact existing bindings for SG-T01-02, SG-T02-01 and SG-T02-02.
- [x] Keep SG-T01-01 unmatched.
- [x] Keep source mismatch, ineligible receipt, ambiguous interval and conflicting values fail-closed.

### Task 2: Persist direct professional decisions already reviewed

**Files:**
- Modify: `tests/cew_cal01/test_external_chain_human_decisions.py`
- Create: `governance/cew-cal01/reviews/CEW_CAL01_EXTERNAL_CHAIN_HUMAN_T02_TOP_I4_v1.json`
- Create: `governance/cew-cal01/reviews/CEW_CAL01_EXTERNAL_CHAIN_HUMAN_T02_TOP_I5_v1.json`

**Interfaces:**
- Consumes: qualified artifact `13145119457` exact interval ids/crop hashes.
- Produces: six TAV-02S TOP direct human decisions (I0-I5).

- [x] Extend receipt-contract test to TOP I4 = 5.30 m and TOP I5 = 4.70 m using exact qualified crop digests.
- [x] Persist I4 and I5 decision records as relation-only evidence.
- [ ] Run contract test and require PASS after receipt creation.

### Task 3: Add direct exact-bound reconciliation path

**Files:**
- Modify: `tests/cew_cal01/test_external_chain_human_review.py`
- Modify: `experiments/cew_cal01/external_chain_human_review.py`

**Interfaces:**
- Consumes: manifest, comparison, earlier receipts, direct decision records.
- Produces: one binding per validated interval with provenance kind `REUSED_HUMAN_RECEIPT` or `DIRECT_HUMAN_DECISION`.

- [ ] Write RED test: valid direct decision binds without source bbox.
- [ ] Write RED test: crop SHA mismatch fails closed.
- [ ] Write RED test: unknown interval id fails closed.
- [ ] Write RED test: duplicate same-value direct decisions deduplicate.
- [ ] Write RED test: direct decision conflicts with geometry-reused receipt and fails closed.
- [ ] Implement minimal direct-decision reconciliation.
- [ ] Run focused tests and require PASS.

### Task 4: Packet counts and exact-source integration

**Files:**
- Modify: `tests/cew_cal01/test_external_chain_human_review_packet.py` and/or workflow contract tests as needed.
- Modify: `experiments/cew_cal01/external_chain_human_review.py`.
- Modify workflow only if required to make future receipt-only changes trigger replay.

**Interfaces:**
- Consumes: merged reconciliation result.
- Produces: packet summary counts and deterministic digest.

- [ ] Add `direct_human_decision_count` and `validated_human_relation_count`.
- [ ] TAV-01S expected: 1 prior reused + 0 direct + 14 pending.
- [ ] TAV-02S expected: 2 prior reused + 6 direct + 11 pending.
- [ ] Total expected: 9 validated human relations + 25 pending across 34 intervals.
- [ ] Assert every row remains `eligible_for_metric_calibration=false` and `primary_anchor_authorized=false`.
- [ ] Require exact-source workflow replay PASS on same SHA.

### Task 5: Human-facing correction for vertical intervals 7–8

**Files:**
- No canonical evidence mutation required for the current review exchange.
- If productized, modify review-board rendering only after a separate RED test proves exact crop digest is unchanged.

**Interfaces:**
- Consumes: exact TAV-02S RIGHT R1 I0/I1 bounding boxes from qualified artifact.
- Produces: expanded, correctly oriented presentation-only context views.

- [x] Reconstruct review views from the primary raster rather than the screenshot.
- [x] Keep canonical exact crop ids/hashes unchanged.
- [ ] Obtain professional user confirmation before writing decisions for intervals 7–8.

### Task 6: Qualification checkpoint

**Files:**
- Modify only after green exact-source replay: `governance/cew-cal01/CEW_CAL01_EXTERNAL_CHAIN_EXECUTION_LEDGER.md`
- Update PR #187 description after qualification.

- [ ] Require `CEW-CAL-01 Primary Metric Calibration`, `CEW-CAL-01 External Dimension Chains`, and `CEW Repository Memory Gate` PASS on the same exact SHA.
- [ ] Record exact SHA, workflow runs, artifact id/digest, TAV-01S/TAV-02S counts and authority closure.
- [ ] Keep PR Draft/open/unmerged.
