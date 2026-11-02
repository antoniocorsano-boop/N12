# CEW-CAL-01 External Dimension Chain Detector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a chain-first detector that identifies long external dimension carriers, repeated ticks and interval-bound OCR observations on structural-grid sheets without modifying qualified TAV.5 grammar.

**Architecture:** Introduce a pure normalized-page chain detector in a new module, then integrate it into the structural-grid discovery pipeline using one Hough line inventory per perimeter band. Preserve the existing local candidate inventory during the first exact-source qualification so new chain evidence can be compared safely against the governed baseline.

**Tech Stack:** Python 3.12.15, OpenCV, Tesseract 5.x, unittest/pytest-compatible tests, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-02-cew-cal01-external-dimension-chain-design.md`

## Global Constraints

- Branch remains `feat/cew-cal01-primary-metric-calibration`; PR #187 remains open and unmerged.
- Structural-grid source commit remains `78c20a52db4f391ce0d13b9705b9f04737e218c9`.
- TAV-02S SHA-256 remains `cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f`.
- Do not modify `experiments/cew_cal01/numeric_role.py` or the shared TAV.5 `dimension_tick_relation()` grammar in this slice.
- Do not correct OCR text from chain geometry.
- Existing `candidate_count/candidates` remain present and unchanged in semantics during first qualification.
- `primary_anchor_count = 0`; metric calibration, canonical geometry/write, M0-G and engineering authority remain closed.

## Review Focus

- A nearby long structural edge without repeated ticks must not become a dimension chain.
- A local short two-reference dimension must not become an external chain.
- Nested parallel carriers on the same side must remain distinct and must not cross-associate tokens.
- A token equidistant between plausible carriers must remain unresolved.
- Zero qualifying chains must remain a valid closed result.

---

### Task 1: Pure external-chain grammar

**Files:**
- Create: `experiments/cew_cal01/external_dimension_chain.py`
- Create: `tests/cew_cal01/test_external_dimension_chain.py`

**Interfaces:**
- Consumes: normalized-page line segments, OCR observations containing `observation_id` and `bbox_normalized_px`, plan envelope bbox.
- Produces: `detect_external_dimension_chains(*, side, line_segments, observations, plan_envelope_bbox) -> dict` with deterministic `chains`, intervals, member IDs, unresolved IDs and closed authority.

- [ ] **Step 1: Write failing contract tests** for a four-interval horizontal chain, rejection of a long unticked structural edge, rejection of a short local dimension, nested carrier separation, ambiguous-token fail-closed behavior and valid zero-chain result.
- [ ] **Step 2: Run the CEW-CAL-01 contract workflow** and require causal RED because `external_dimension_chain` does not yet exist.
- [ ] **Step 3: Implement minimal pure grammar**: axis classification, long-carrier threshold relative to plan envelope, short perpendicular/diagonal tick intersections, tick clustering, consecutive interval construction, bounded token association and deterministic ordering.
- [ ] **Step 4: Run the full CEW-CAL-01 contract workflow** and require GREEN with existing structural-grid and TAV.5 contract suites unchanged.
- [ ] **Step 5: Commit** `feat(cal01): add external dimension chain grammar`.

### Task 2: Structural-grid pipeline integration

**Files:**
- Modify: `experiments/cew_cal01/structural_grid_dimension.py`
- Modify: `tests/cew_cal01/test_structural_grid_dimension.py`

**Interfaces:**
- Consumes: Task 1 `detect_external_dimension_chains()`.
- Produces: per-source discovery fields `external_chain_count`, `external_chain_member_count`, `external_chains`, `external_chain_unresolved_observation_ids`, while preserving legacy candidate fields.

- [ ] **Step 1: Add failing tests** requiring one normalized-frame Hough segment inventory per band and deterministic aggregation of chain results without changing legacy candidate classification.
- [ ] **Step 2: Run contracts** and verify causal RED from missing integration.
- [ ] **Step 3: Implement band-level Hough extraction** in normalized page coordinates and invoke the pure detector after OCR observations are assembled.
- [ ] **Step 4: Include chain fields in the deterministic discovery digest and review overlay without promoting chain evidence to calibration authority.**
- [ ] **Step 5: Run full CEW-CAL-01 contract workflow** and require GREEN.
- [ ] **Step 6: Commit** `feat(cal01): integrate external dimension chains`.

### Task 3: Exact-source qualification and governed checkpoint

**Files:**
- Modify only after fresh workflow evidence: `governance/cew-cal01/CEW_CAL01_EXTERNAL_CHAIN_VISUAL_PRECHECK_v1.json`
- Modify: `governance/cew-cal01/CEW_CAL01_STATUS_v1.json`
- Create: `governance/cew-cal01/CEW_CAL01_EXTERNAL_CHAIN_RESULT_v1.json`

**Interfaces:**
- Consumes: fresh exact-source structural-grid artifact on the exact Task 2 head.
- Produces: governed diagnostic result comparing machine-detected chains with the existing visual precheck, without changing existing human-value receipts.

- [ ] **Step 1: Wait for the exact-source workflow on the Task 2 head and inspect TAV-01S/TAV-02S discovery JSON and overlays.**
- [ ] **Step 2: Record exact head, workflow run, artifact ID/digest, per-side chain counts, member IDs and unresolved IDs.**
- [ ] **Step 3: Compare TAV-02S machine chains against the visual precheck only as validation evidence; do not feed human-transcribed values back into detection.**
- [ ] **Step 4: If a false chain or missed obvious carrier is present, record REWORK and stop promotion; otherwise record MACHINE_CHAIN_DIAGNOSTIC_PASS.**
- [ ] **Step 5: Keep `primary_anchor_count = 0` and all authority closed; preserve SG-T02-01/02 human value receipts unchanged.**
- [ ] **Step 6: Commit** `docs(cal01): record external dimension chain qualification`.
