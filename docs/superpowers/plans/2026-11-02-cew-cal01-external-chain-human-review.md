# CEW-CAL-01 External Chain Human Review Reconciliation Plan

> **Execution mode:** inline on `feat/cew-cal01-primary-metric-calibration` using TDD. No merge or deploy.

**Goal:** Reuse existing qualified human professional metric-relation receipts when they bind unambiguously to the new exact external-chain intervals, then generate a governed pending-review packet for the remaining intervals.

**Spec:** `docs/superpowers/specs/2026-11-02-cew-cal01-external-chain-human-review-design.md`

## Repository Memory / Reuse Assessment

- Existing human receipts under `governance/cew-cal01/CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_*`: `REUSE` after exact source + geometry reconciliation.
- `CEW_CAL01_EXTERNAL_CHAIN_VISUAL_PRECHECK_v1.json`: `REFERENCE_ONLY`; AI precheck cannot satisfy the human gate.
- `anchor_inventory.py` / `PRIMARY_VISUAL_VALIDATED` fit policy: `REUSE` unchanged.
- New capability boundary: frame transform + receipt reconciliation + review-packet generation only.

## Global constraints

- Never generate `HUMAN_PROFESSIONAL_USER` decisions automatically.
- Never use OCR or AI precheck to create `PRIMARY_VISUAL_VALIDATED` state.
- Existing receipt reuse requires exact source SHA and unambiguous geometric containment after the governed rotation transform.
- Reused receipts authorize a metric relation only; `eligible_for_metric_calibration=false`, `primary_anchor_authorized=false`.
- Conflicting/ambiguous matches fail closed.
- No historical affine, M0-G identity, structural identity or canonical write authority is opened.

### Task 1 — Source-frame transform and receipt reconciliation core

**Create:**
- `experiments/cew_cal01/external_chain_human_review.py`
- `tests/cew_cal01/test_external_chain_human_review.py`

- [ ] Write RED tests for 90° CCW source-bbox normalization.
- [ ] Write RED tests proving SG-T01-02 binds to `TAV-01S:RIGHT:RIGHT:R1:I0`.
- [ ] Write RED tests proving SG-T02-01 binds to `TAV-02S:BOTTOM:BOTTOM:R1:I3` and SG-T02-02 to `...:I2`.
- [ ] Write RED test proving SG-T01-01 does not bind to the qualified external-chain crops.
- [ ] Write RED tests for source-SHA mismatch, non-human reviewer, non-linear receipt, multiple interval matches and conflicting receipts.
- [ ] Implement minimal reconciliation core and require focused + full CAL-01 suite PASS.

### Task 2 — Governed review packet

**Modify:**
- `experiments/cew_cal01/external_chain_human_review.py`
- `tests/cew_cal01/test_external_chain_human_review.py`

- [ ] Add RED tests for one row per exact interval and exact crop-digest preservation.
- [ ] Require `REUSED_HUMAN_RECEIPT` only for successfully reconciled prior receipts; all others `PENDING_HUMAN_REVIEW`.
- [ ] Require summary counts and deterministic packet digest.
- [ ] Require all authority flags closed and every row `eligible_for_metric_calibration=false`, `primary_anchor_authorized=false`.
- [ ] Add a static HTML board generator referencing relative exact crops and showing OCR evidence without inventing values.
- [ ] Run focused + full CAL-01 suite and require PASS.

### Task 3 — Exact-source workflow qualification

**Modify:**
- `.github/workflows/validate-cew-cal01-external-chain.yml`
- `tests/cew_cal01/test_external_chain_workflow.py`

- [ ] Add RED workflow-contract assertions for human-review packet generation on TAV-01S and TAV-02S.
- [ ] Integrate the already committed qualified receipt files as explicit workflow inputs.
- [ ] Assert exact expected reuse count from geometric reconciliation, pending count, crop bindings and closed authority without asserting any new human value.
- [ ] Upload packet + HTML board inside the existing governed external-chain artifact.
- [ ] Require `CEW-CAL-01 Primary Metric Calibration`, `CEW-CAL-01 External Dimension Chains`, and `CEW Repository Memory Gate` PASS on the same exact SHA.

### Task 4 — Canonical checkpoint update

**Modify only after Task 3 qualification:**
- `governance/cew-cal01/CEW_CAL01_EXTERNAL_CHAIN_EXECUTION_LEDGER.md`
- PR #187 description

- [ ] Record exact SHA, workflow runs, governed artifact id/digest, reused receipt count and pending human-review count.
- [ ] Keep PR Draft/open/unmerged.
- [ ] Do not create new human receipts until the professional user has actually reviewed the pending intervals.