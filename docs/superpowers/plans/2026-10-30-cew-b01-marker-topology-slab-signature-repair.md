# CEW-B01 Marker Topology and Transverse-Band Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the TAV.5 Human Graphical Review defects by grounding marker overlays to the raster, describing carrier topology neutrally, and replacing the generic transverse-pair state with a side-aware complete/partial transverse-band signature.

**Architecture:** Keep PR #168 outputs immutable as parent evidence. Add a new neutral repair layer that consumes existing hosted-marker candidates, G1 primitives/LineTracks, and the exact binary raster; it emits marker-grounding, carrier-topology, and transverse-band descriptors without technical semantics. A bounded exact-source workflow then selects a small diagnostic micro-atlas from C5/C7 plus the strongest topology/grounding outliers for Human Graphical Review.

**Tech Stack:** Python 3.12, existing CEW-B01 primitive/LineTrack/hosted-marker modules, OpenCV/numpy only where already available in the exact-source workflow, GitHub Actions exact-source replay.

**Spec:** `docs/experiments/2026-10-30-cew-b01-marker-topology-slab-signature-repair-design.md`

## Global Constraints

- Parent exact head is PR #168 head `c9bd4c33cf4db88cc3775fb3a2076b94f85c7700`.
- TAV.5 source SHA-256 remains `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Original G1 marker geometry and primitive provenance are immutable evidence.
- No executable `BEAM`, `COLUMN`, `SLAB`, `CARRIES_SLAB`, or equivalent technical class.
- Orientation alone must never accept/reject a carrier.
- No semantic classification, structural identity, canonical writes, G2C promotion, G3, merge or full-corpus scaling.
- Human review vocabulary remains `GRAPHICAL_MATCH / GRAPHICAL_NON_MATCH / ARTIFACT / UNCERTAIN`.

## Review Focus

1. A valid vertical or horizontal through-member must not be rejected merely because of orientation — Task 2 tests both orientations.
2. A carrier that terminates close to a marker must not be indistinguishable from a through-continuous carrier — Task 2 tests terminal topology.
3. A `2+2` transverse configuration must be distinguished from `1+1`, `2+1`, and remote traces — Task 3 tests all four cases.
4. Raster marker refinement must not jump to an adjacent rectangle or erase source geometry — Task 1 tests bounded shift, IoU and provenance.
5. Annotation-dominated controls must stay excluded from the repair review set — Task 4 exact-source contract checks PR #168 roles are preserved.

---

### Task 1: Marker grounding and review geometry

**Files:**
- Create: `experiments/cew_b01/marker_topology_repair.py`
- Create: `tests/cew_b01/test_marker_grounding_repair.py`
- Modify: `.github/workflows/validate-cew-b01-beam-hosted-marker-pilot.yml`

**Interfaces:**
- Consumes: hosted-marker candidate with `marker_geometry`; exact binary raster.
- Produces: `refine_marker_grounding(candidate: dict, binary_ink: Sequence[Sequence[Any]]) -> dict` returning immutable `source_marker_geometry`, `review_marker_geometry`, and `marker_grounding`.

- [ ] **Step 1: Write failing tests**
  - `test_aligned_rectangle_stays_g1_exact`
  - `test_shifted_source_box_refines_to_supported_raster_edges`
  - `test_refinement_cannot_jump_to_adjacent_rectangle`
  - `test_source_geometry_is_preserved_byte_for_byte`
  - Assertions: refinement bounded to a local search radius; qualified refinement requires stronger four-edge support than source; source geometry unchanged.

- [ ] **Step 2: Run the Unit Gate and record causal RED**
  - Expected: import/function absence or failed grounding contracts only; inherited tests remain PASS.

- [ ] **Step 3: Implement minimal local edge-support refinement**
  - `refine_marker_grounding(...)` searches top/bottom/left/right raster edge support only within `max(6 px, 0.15 × min(marker width,height))` of source edges.
  - Accept refinement only when all four edges have material support, geometry remains rectangular, center shift is within the same local radius, and refined edge residual improves over source.
  - Never overwrite `marker_geometry` or source primitive provenance.

- [ ] **Step 4: Run Unit Gate GREEN and commit**

### Task 2: Neutral carrier topology descriptor

**Files:**
- Modify: `experiments/cew_b01/marker_topology_repair.py`
- Create: `tests/cew_b01/test_carrier_topology_descriptor.py`
- Modify: `.github/workflows/validate-cew-b01-beam-hosted-marker-pilot.yml`

**Interfaces:**
- Consumes: repaired candidate from Task 1; complete neutral LineTracks from `build_line_tracks`.
- Produces: `describe_carrier_topology(candidate: dict, tracks: list[dict]) -> dict` with `THROUGH_CONTINUOUS / TERMINAL_OR_STEM / JUNCTION_COMPLEX / AMBIGUOUS` and numeric continuation/junction evidence.

- [ ] **Step 1: Write failing tests**
  - horizontal and vertical through-carriers -> `THROUGH_CONTINUOUS`;
  - one-sided local termination -> `TERMINAL_OR_STEM`;
  - multiple material orthogonal junction tracks at a marker end -> `JUNCTION_COMPLEX`;
  - conflicting/insufficient evidence -> `AMBIGUOUS`;
  - reversed LineTrack input -> byte-identical descriptor.

- [ ] **Step 2: Run Unit Gate and record causal RED**

- [ ] **Step 3: Implement topology from longitudinal continuation distances and end-local orthogonal junction evidence**
  - Orientation is normalized into long/cross axes; no structural names.
  - Do not filter candidates yet; descriptor only.

- [ ] **Step 4: Run Unit Gate GREEN and commit**

### Task 3: Side-aware complete transverse-band signature

**Files:**
- Modify: `experiments/cew_b01/marker_topology_repair.py`
- Create: `tests/cew_b01/test_transverse_band_signature.py`
- Modify: `.github/workflows/validate-cew-b01-beam-hosted-marker-pilot.yml`

**Interfaces:**
- Consumes: candidate, LineTracks, exact binary raster, Task 1 review geometry.
- Produces: `describe_transverse_band(candidate: dict, tracks: list[dict], binary_ink: Sequence[Sequence[Any]]) -> dict` and neutral state `RECT_ALONE_ON_CARRIER / RECT_PLUS_DOUBLE_TRANSVERSE_BAND / RECT_PLUS_PARTIAL_TRANSVERSE_TRACES`.

- [ ] **Step 1: Write failing tests**
  - no material traces -> ALONE;
  - `2+2` side-grouped traces with coherent spacing -> DOUBLE_TRANSVERSE_BAND;
  - `1+1`, `2+1`, or one remote side -> PARTIAL;
  - duplicate Hough observations coalesce and do not inflate counts;
  - primitive and raster provenance remain separate;
  - reversed input determinism.

- [ ] **Step 2: Run Unit Gate and record causal RED**

- [ ] **Step 3: Implement side grouping**
  - Normalize along the carrier long axis.
  - Group orthogonal track/raster stroke centers into negative and positive sides relative to the review marker interval.
  - A complete band requires at least two distinct local traces on each side with bounded intra-side spacing consistency; otherwise partial when material traces exist.
  - Preserve existing primitive/raster evidence; no semantic label.

- [ ] **Step 4: Run Unit Gate GREEN and commit**

### Task 4: Exact-source repair manifest, micro-atlas and governed receipt

**Files:**
- Create: `.github/workflows/validate-cew-b01-marker-topology-repair.yml`
- Create: `governance/cew-b01/MARKER_TOPOLOGY_REPAIR_v1.json`
- Modify: `docs/experiments/2026-10-30-cew-b01-marker-topology-slab-signature-repair-design.md`
- Test: exact-source workflow assertions.

**Interfaces:**
- Consumes: PR #168 46 `REVIEW_ELIGIBLE` candidates, exact 5,633-primitive census, exact 300-dpi raster, Tasks 1–3 descriptors.
- Produces: deterministic JSON result, bounded micro-atlas, frozen repair manifest/receipt.

- [ ] **Step 1: Add exact-source workflow before expected values are known**
  - Regenerate TAV.5 from frozen source twice.
  - Assert 5,633 primitives and parent search invariants.
  - Compute descriptors for all 46 review-eligible candidates without changing their parent role.
  - Always include C5/C7.
  - Select up to 4 largest qualified grounding shifts and up to 4 non-`THROUGH_CONTINUOUS` topology cases; deduplicate IDs; cap micro-atlas at 12 panels.
  - Include 2 annotation-dominated controls outside the review set.
  - No minimum number of outliers is asserted.

- [ ] **Step 2: Run exact-source workflow and inspect RED/observed result**
  - If C5/C7 violate the spec, use systematic debugging; do not relax thresholds to force expected states.
  - Freeze the exact IDs corresponding to the user-observed topology/alignment defects once identified by the diagnostic output.

- [ ] **Step 3: Add exact-source regression assertions**
  - C5 must remain ALONE.
  - C7 must expose `RECT_PLUS_DOUBLE_TRANSVERSE_BAND` only if exact raster/track evidence proves `2+2`; otherwise record `PARTIAL` and keep the design in REWORK rather than forcing PASS.
  - Parent annotation-dominated cases remain annotation-dominated.
  - Frozen topology/alignment Human Review targets remain present in the micro-atlas.
  - Deterministic replay digest identical across two runs.
  - All authority flags false.

- [ ] **Step 4: Generate governed receipt and micro-atlas**
  - Red solid = review geometry; red dashed = source geometry only when materially different; green = carrier; magenta = G1 transverse evidence; blue = raster transverse evidence.
  - Panel text includes topology, negative/positive side counts, grounding shift/residual and provenance.

- [ ] **Step 5: Run final exact-head Unit Gate, Memory Gate and repair exact-source workflow**

- [ ] **Step 6: Auto-review the whole branch**
  - Confirm no technical semantics are executable.
  - Confirm no source geometry/provenance is overwritten.
  - Confirm no unrelated files and no temporary diagnostics remain.
  - Record that this is an auto-review, not an independent review.

- [ ] **Step 7: Update Draft PR body with exact SHA/run/artifact/digest and leave merge/G2C/G3 unauthorized**
