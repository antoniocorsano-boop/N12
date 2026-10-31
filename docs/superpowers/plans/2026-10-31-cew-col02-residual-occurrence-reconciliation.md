# CEW COL-02 Residual Occurrence Reconciliation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the completed COL-02 mobile Human Review into a bounded reconciliation pass for two misframed positives and four human-added occurrence points, without re-running the completed ten-candidate review or promoting structural authority.

**Architecture:** Add a small deterministic reconciliation module inside `experiments/cew_col02` that replays the append-only Human Review bundle, builds enlarged reframing tasks for the two `INQUADRATO_MALE` candidates, and resolves human-added points against the frozen neutral footprint proposal set with fail-closed deduplication. A dedicated exact-source workflow artifact will contain the reconciliation JSON and target-explicit review images.

**Tech Stack:** Python 3.12/3.12.15, existing COL-02 exact-source modules, OpenCV already pinned by `requirements/cew-b01.lock.txt`, pytest, GitHub Actions.

**Spec:** `docs/experiments/2026-10-31-cew-col02-residual-occurrence-reconciliation-design.md`

## Global Constraints

- Frozen COL-02 producer exact SHA: `5664614d813cd11cf357bed40d7cdfaa843720f2`.
- Frozen source SHA-256: `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Never re-run or alter the already completed ten-candidate Human Review decisions.
- Similarity weights, proposal generation and OCR thresholds remain unchanged.
- Human-added points may bind only to the frozen neutral proposal set or remain `HUMAN_POINT_UNBOUND`.
- No support/text/family/section/fixed-line/structural identity.
- No canonical geometry/write, G2C/G3 or merge authority.

## Review Focus

- Multiple UNDO events must resolve to exactly one effective decision per original residual candidate.
- A human point that falls inside two nested proposals must be resolved deterministically or remain unbound; it must never silently choose an ambiguous structural identity.
- Two human points resolving to the same frozen proposal must yield one review task plus duplicate provenance.
- A point resolving to an already reviewed S01-S24 or residual candidate must be marked duplicate and not re-reviewed.
- Reframing must preserve the original candidate bbox while expanding only context; it must not change the candidate identity.

---

### Task 1: Human review replay and validation

**Files:**
- Create: `experiments/cew_col02/residual_occurrence_reconciliation.py`
- Create: `tests/cew_col02/test_residual_occurrence_reconciliation.py`

**Interfaces:**
- Produces: `replay_mobile_review(bundle: dict) -> dict` returning effective terminal decisions, effective additional-occurrence events and source-lineage metadata.

- [ ] **Step 1: Write failing replay tests**

Cover: 24-event bundle semantics; duplicate terminal decision removed by `UNDO_LAST`; exactly 10 effective terminal decisions; four effective additional occurrences; source replay hashes must match the frozen values.

- [ ] **Step 2: Run targeted tests and confirm RED**

Run: `pytest -q tests/cew_col02/test_residual_occurrence_reconciliation.py -k replay`
Expected: FAIL because `residual_occurrence_reconciliation` does not exist.

- [ ] **Step 3: Implement minimal replay/lineage validation**

Implement `replay_mobile_review(bundle: dict) -> dict` with fail-closed validation for review ID, candidate set, source SHA, producer SHA and replay hashes.

- [ ] **Step 4: Run targeted tests and confirm GREEN**

Run: `pytest -q tests/cew_col02/test_residual_occurrence_reconciliation.py -k replay`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: replay COL-02 mobile review receipt`.

### Task 2: Point-to-proposal reconciliation and deduplication

**Files:**
- Modify: `experiments/cew_col02/residual_occurrence_reconciliation.py`
- Modify: `tests/cew_col02/test_residual_occurrence_reconciliation.py`

**Interfaces:**
- Consumes: frozen neutral proposal records and effective additional-occurrence events.
- Produces: `reconcile_human_points(points: list[dict], proposals: list[dict], reviewed_ids: set[str]) -> list[dict]`.

- [ ] **Step 1: Write failing binding/dedup tests**

Cover containment-first match, deterministic center-distance tie-break, ambiguous equal-ranked case remaining `HUMAN_POINT_UNBOUND`, duplicate existing candidate, and two points resolving to one proposal.

- [ ] **Step 2: Run targeted tests and confirm RED**

Run: `pytest -q tests/cew_col02/test_residual_occurrence_reconciliation.py -k 'point or duplicate'`
Expected: FAIL because reconciliation API is absent.

- [ ] **Step 3: Implement bounded reconciliation**

Use only the frozen proposal set. Rank by containment, then normalized point-to-bbox-center distance, then candidate ID. Do not synthesize candidate IDs for ambiguous/unbound points.

- [ ] **Step 4: Run targeted tests and confirm GREEN**

Run: same targeted command; expected PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: reconcile human occurrence points`.

### Task 3: Reframe the two misframed positives

**Files:**
- Modify: `experiments/cew_col02/residual_occurrence_reconciliation.py`
- Modify: `tests/cew_col02/test_residual_occurrence_reconciliation.py`

**Interfaces:**
- Produces: `build_reframe_tasks(search: dict, effective_decisions: list[dict]) -> list[dict]` for exactly `COL02-FP-0252` and `COL02-FP-0106`.

- [ ] **Step 1: Write failing reframe tests**

Assert exactly two tasks; original candidate IDs and original normalized target bbox are unchanged; context bounds expand and remain within source raster; no adequately framed candidate enters this set.

- [ ] **Step 2: Run targeted tests and confirm RED**

Run: `pytest -q tests/cew_col02/test_residual_occurrence_reconciliation.py -k reframe`
Expected: FAIL.

- [ ] **Step 3: Implement reframe task builder**

Reuse existing source/crop geometry helpers where possible; expansion is context-only.

- [ ] **Step 4: Run targeted tests and confirm GREEN**

Run: same targeted command; expected PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: build COL-02 reframe tasks`.

### Task 4: Exact-source reconciliation artifact

**Files:**
- Modify: `experiments/cew_col02/residual_occurrence_reconciliation.py`
- Create: `governance/cew-col02/COL02_RESIDUAL_OCCURRENCE_RECONCILIATION_v1.json` only after exact-source output is known and validated.
- Modify: `.github/workflows/validate-cew-col02-footprint-text-binding.yml`
- Modify: `tests/cew_col02/test_residual_occurrence_reconciliation.py`

**Interfaces:**
- Produces CLI/module entrypoint that accepts the Human Review bundle path and existing COL-02 evidence root, then emits reconciliation JSON plus target-explicit review crops/atlas.

- [ ] **Step 1: Write failing manifest/governance tests**

Require frozen source lineage, original human event IDs, dedup status for every added point, exactly two reframe tasks, authority booleans all false except graphical-review evidence retention, and `occurrence_coverage_complete=false` until successor Human Review.

- [ ] **Step 2: Run full COL-02 unit suite and confirm causal RED**

Run: `pytest -q tests/cew_col02`
Expected: existing tests PASS; new reconciliation contract FAIL.

- [ ] **Step 3: Implement exact-source output and workflow step**

Materialize source/evidence through the existing exact-source workflow; render only unresolved reconciliation items. Upload a dedicated artifact without altering previous artifacts.

- [ ] **Step 4: Run full unit suite and exact-source workflow**

Run locally where possible: `pytest -q tests/cew_col02`.
Then require GitHub Actions exact-source job PASS on the exact branch head.

- [ ] **Step 5: Freeze governed receipt from actual exact-source output**

Record exact SHA, artifact ID/digest, replay/dedup summary and next Human Review gate. No occurrence-complete claim yet.

- [ ] **Step 6: Commit**

Commit message: `feat: qualify COL-02 residual occurrence reconciliation`.

### Task 5: Open successor Draft PR and preserve boundaries

**Files:**
- No product-code changes.

**Interfaces:**
- Consumes exact qualified branch head and artifact metadata.

- [ ] **Step 1: Open Draft PR**

Base: `spike/cew-col02-footprint-text-binding`.
Head: `spike/cew-col02-residual-occurrence-reconciliation`.

- [ ] **Step 2: Record source Human Review bundle digest and exact qualified evidence**

PR body must state that the ten-candidate review is complete and not repeated, while occurrence completeness remains open.

- [ ] **Step 3: Verify PR state**

Require Draft/open/non-merged, exact head unchanged after qualification, no authority broadening, and no merge authorization.
