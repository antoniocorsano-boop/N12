# CEW-B01 Hosted-Marker Occurrence Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Search the frozen TAV.5 source for additional occurrences of the two already-qualified neutral hosted-marker graphical configurations and generate a deterministic human-review package without semantic promotion.

**Architecture:** Reuse the exact-source carrier-first/hybrid pipeline from PR #167. Add a small occurrence-search layer that feeds every `RECTILINEAR_CLOSED_SHAPE` through the existing hybrid detector, computes neutral scale-normalized review similarity to C5/C7, then extends exact-source qualification to emit a complete receipt and bounded review atlas.

**Tech Stack:** Python 3.12.15, existing CEW-B01 OpenCV/PDF toolchain, unittest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-30-cew-b01-hosted-marker-occurrence-search-design.md`

## Global Constraints

- TAV.5 only; source SHA-256 must remain `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Start from qualified PR #167 head `5daa6e1f8dd43654a3627b155c0d6dc0c37c820e`.
- Reuse existing carrier-first, overwide-carrier hardening, raster-profile detector and hybrid evidence adapter; do not rewrite their semantics.
- All `RECTILINEAR_CLOSED_SHAPE` observations are eligible search inputs; do not pre-filter by technical meaning or text.
- C5 and C7 are neutral review-ordering prototypes only.
- Atlas maximum: 12 additional occurrences per neutral graphical state, excluding C5/C7.
- No minimum number of additional occurrences may be asserted.
- Semantic classification, structural identity, canonical writes, G2C, G3 and merge authority remain false.

## Review Focus

- Annotation/dimension rectangles that happen to lie inside broad parallel geometry must not bypass the existing local-carrier binding rules; pinned by Task 1 regression coverage using the existing overwide-carrier behavior plus a non-bound marker fixture.
- Reversing primitive input order must not change occurrence IDs, states, distances or ordering; pinned by Task 1 determinism test.
- An occurrence with raster pair evidence but only one G1 local track must preserve both facts separately; pinned by Task 1 hybrid evidence test.
- Similarity ranking must be scale-normalized and must not prefer absolute pixel size alone; pinned by Task 2 scale-equivalence test.
- Exact-source search may legitimately find zero additional matches in either state and must still qualify; pinned by Task 3 workflow logic and receipt assertions that avoid minimum-count gates.

---

### Task 1: Discover every neutral hosted-marker occurrence

**Files:**
- Create: `experiments/cew_b01/hosted_marker_occurrence_search.py`
- Create: `tests/cew_b01/test_hosted_marker_occurrence_search.py`
- Modify: `.github/workflows/validate-cew-b01-beam-hosted-marker-pilot.yml`

**Interfaces:**
- Consumes: `build_hybrid_hosted_marker_candidates(primitives, marker_seed_ids, binary_ink)` from `experiments.cew_b01.beam_hosted_marker_hybrid`.
- Produces: `discover_hosted_marker_occurrences(primitives: list[dict[str, Any]], binary_ink: Sequence[Sequence[Any]]) -> list[dict[str, Any]]`.

- [ ] **Step 1: Write the failing occurrence-discovery tests**

Add tests proving:
- every `RECTILINEAR_CLOSED_SHAPE` seed is considered without manually supplying seed IDs;
- only shapes that bind through the existing local-carrier rules are emitted;
- raster pair recovery preserves `primitive_graphical_state` separately from final `graphical_state`;
- every authority flag remains false and `semantic_meaning is None`;
- reversed primitive input returns byte-equivalent ordered output.

- [ ] **Step 2: Run the dedicated tests and verify RED**

Run:
`python -m unittest tests.cew_b01.test_hosted_marker_occurrence_search -v`

Expected: FAIL because `experiments.cew_b01.hosted_marker_occurrence_search` or `discover_hosted_marker_occurrences` does not yet exist.

- [ ] **Step 3: Implement the minimal discovery layer**

Create:
`discover_hosted_marker_occurrences(primitives: list[dict[str, Any]], binary_ink: Sequence[Sequence[Any]]) -> list[dict[str, Any]]`

Behavior:
- collect and sort every primitive ID whose family is `RECTILINEAR_CLOSED_SHAPE`;
- call the existing hybrid builder once with the complete sorted seed list;
- add no semantic labels or new binding rules;
- return deterministic output sorted by marker primitive ID and hosted-marker ID.

- [ ] **Step 4: Run Task 1 tests GREEN**

Run:
`python -m unittest tests.cew_b01.test_hosted_marker_occurrence_search -v`

Expected: PASS.

- [ ] **Step 5: Add Task 1 to the existing unit gate and run the complete pilot suite**

Modify `.github/workflows/validate-cew-b01-beam-hosted-marker-pilot.yml` to include the new test module and search implementation path.

Run:
`python -m unittest tests.cew_b01.test_beam_hosted_markers tests.cew_b01.test_beam_hosted_marker_raster tests.cew_b01.test_beam_hosted_marker_hybrid tests.cew_b01.test_beam_hosted_marker_binding_hardening tests.cew_b01.test_hosted_marker_occurrence_search -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Commit message:
`feat: discover neutral hosted-marker occurrences`

### Task 2: Rank occurrences for human review without semantic promotion

**Files:**
- Modify: `experiments/cew_b01/hosted_marker_occurrence_search.py`
- Modify: `tests/cew_b01/test_hosted_marker_occurrence_search.py`

**Interfaces:**
- Consumes: Task 1 occurrence dictionaries.
- Produces:
  - `hosted_marker_signature(candidate: dict[str, Any]) -> dict[str, float]`
  - `prototype_distance(candidate_signature: dict[str, float], prototype_signature: dict[str, float]) -> float`
  - `rank_occurrences_for_review(occurrences: list[dict[str, Any]], prototype_by_state: dict[str, dict[str, Any]]) -> list[dict[str, Any]]`

- [ ] **Step 1: Write failing ranking tests**

Tests must assert:
- geometrically scaled copies of the same configuration have distance approximately zero;
- a distorted carrier-separation ratio ranks farther than a scale-equivalent copy;
- pair separation is included only when both candidate and prototype expose valid raster pair evidence;
- ranking is restricted to same-state prototypes;
- C5/C7 IDs can be excluded from an additional-occurrence review list;
- ordering is deterministic on equal distance by geometry then primitive ID.

- [ ] **Step 2: Run tests and verify RED**

Run:
`python -m unittest tests.cew_b01.test_hosted_marker_occurrence_search -v`

Expected: FAIL because signature/ranking functions are absent.

- [ ] **Step 3: Implement scale-normalized signatures and distance**

Implement the exact signature components from the spec:
- marker longitudinal span / cross-span;
- carrier separation / marker cross-span;
- marker longitudinal span / carrier overlap length;
- optional raster pair separation / marker longitudinal span.

Use sum of absolute natural-log ratio differences across shared positive-valued components. Same-state prototypes only; missing optional pair metrics are omitted, never synthesized.

- [ ] **Step 4: Implement deterministic ranking**

`rank_occurrences_for_review` must attach:
- `prototype_marker_primitive_id`;
- `prototype_distance`;
- `review_state = "UNREVIEWED"`.

Do not change `graphical_state` or evidence fields.

- [ ] **Step 5: Run full Task 2 suite GREEN**

Run:
`python -m unittest tests.cew_b01.test_hosted_marker_occurrence_search -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Commit message:
`feat: rank hosted-marker matches for review`

### Task 3: Exact-source full-TAV.5 occurrence replay and bounded atlas

**Files:**
- Create: `.github/workflows/validate-cew-b01-hosted-marker-occurrence-search.yml`
- Create: `governance/cew-b01/HOSTED_MARKER_OCCURRENCE_SEARCH_v1.json`
- Modify: `docs/experiments/2026-10-30-cew-b01-beam-hosted-marker-design.md`

**Interfaces:**
- Consumes: Task 1 discovery and Task 2 ranking functions; frozen source materialization and existing exact-source raster/G1 pipeline.
- Produces workflow artifact `cew-b01-hosted-marker-occurrence-search` containing:
  - `hosted-marker-occurrences.json`;
  - `hosted-marker-occurrence-atlas.png`.

- [ ] **Step 1: Add exact-source workflow before hard-coding a governed result**

Workflow must:
- checkout exact candidate head;
- install the frozen CEW-B01 toolchain;
- materialize archival TAV.5 and assert source SHA;
- regenerate 300-dpi raster and confirmed zones;
- replay G1 twice and assert exactly 5,633 primitives / 733 axis-aligned line observations;
- execute full occurrence discovery and ranking twice;
- assert byte-identical occurrence payloads;
- assert frozen C5 and C7 are present with their qualified neutral states;
- assert all authority flags remain false;
- make no assertion that additional matches must exist.

- [ ] **Step 2: Generate the bounded atlas from the original raster**

For each state, select up to 12 ranked occurrences excluding C5/C7. Each panel must show:
- candidate ID;
- neutral graphical state;
- original raster crop;
- marker rectangle;
- local carrier edges/band;
- raster pair strokes when detected;
- prototype distance.

No beam/slab semantic text.

- [ ] **Step 3: Run the workflow on the exact branch head**

Expected: workflow PASS and evidence artifact uploaded.

- [ ] **Step 4: Inspect the generated JSON and atlas before recording findings**

Record actual counts by state, additional candidate IDs and replay digest. If a state has zero additional matches, preserve zero and do not relax thresholds.

- [ ] **Step 5: Write governed result receipt from observed evidence**

Create `governance/cew-b01/HOSTED_MARKER_OCCURRENCE_SEARCH_v1.json` containing:
- source and workflow provenance;
- exact head;
- total hosted-marker occurrence count;
- counts by neutral graphical state;
- frozen prototype records;
- additional review candidates in ranked order;
- deterministic replay digest;
- authority block with every promotion flag false.

- [ ] **Step 6: Update experiment documentation**

Document actual search findings and next human-review boundary. Do not translate neutral states into structural meaning.

- [ ] **Step 7: Commit documentation/receipt and rerun both unit and exact-source gates on the final exact head**

Expected: all relevant gates PASS on the same final SHA.

### Task 4: Draft stacked PR and freeze the review boundary

**Files:**
- PR metadata only.

**Interfaces:**
- Consumes: final Task 3 exact head and evidence.
- Produces: Draft PR from `spike/cew-b01-hosted-marker-occurrence-search` to `spike/cew-b01-beam-hosted-markers`.

- [ ] **Step 1: Create/update Draft PR**

PR body must state:
- bounded TAV.5-only scope;
- exact qualified parent head `5daa6e1f...`;
- exact final search head and workflow runs;
- actual counts by neutral state;
- artifact ID/digest;
- no semantic/structural/G2C/G3/merge authority.

- [ ] **Step 2: Verify final PR state**

Expected:
- open;
- Draft;
- mergeable if GitHub reports it;
- not merged;
- base `spike/cew-b01-beam-hosted-markers`;
- head `spike/cew-b01-hosted-marker-occurrence-search`.

- [ ] **Step 3: Record final checkpoint**

The next permitted action after this plan is **Human Review of the generated additional-occurrence atlas only**. Semantic mapping remains a separate later decision.
