# CEW-B01 Hosted-Marker Graphical Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair D1 bilateral transverse evidence, D2 carrier topology, and D3 marker alignment while preserving PR #168 provenance and authority boundaries.

**Architecture:** Add a neutral refinement module over PR #168 occurrences. Existing G1, hybrid pair evidence and annotation separation remain immutable inputs; the new layer adds bilateral raster evidence, carrier-topology evidence and marker-alignment evidence, then assigns a conservative graphical repair role for Human Review.

**Tech Stack:** Python 3.12.15, OpenCV, NumPy, existing CEW-B01 deterministic exact-source workflow.

**Spec:** `docs/superpowers/specs/2026-10-30-cew-b01-hosted-marker-graphical-repair-design.md`

## Global Constraints

- TAV.5 only.
- Preserve all original primitive IDs, carrier IDs and PR #168 occurrence provenance.
- No automatic beam/pillar/column/slab semantics.
- No mutation/snapping of G1 marker geometry.
- Semantic classification, structural identity, canonical writes, G2C, G3 and merge authority remain false.
- Human review state remains `UNREVIEWED`.

## Review Focus

- One-side pair must not masquerade as bilateral double pair — Task 1 regression.
- A carrier ending close to the marker must not enter the through-carrier family — Task 2 regression.
- A valid through carrier near a junction must not be rejected merely because unrelated orthogonal linework exists nearby — Task 2 regression.
- A shifted marker bbox must be flagged without silently rewriting the primitive — Task 3 regression.
- Existing PR #168 occurrence IDs must be conserved exactly in exact-source replay — Task 4 regression.

---

### Task 1: Bilateral transverse evidence

**Files:**
- Modify: `experiments/cew_b01/beam_hosted_marker_raster.py`
- Create: `tests/cew_b01/test_hosted_marker_bilateral_transverse.py`

**Interfaces:**
- Consumes: current `detect_local_transverse_pair_from_binary(...)` inputs.
- Produces: `detect_bilateral_transverse_section_from_binary(...) -> dict[str, Any]` with `before`, `after`, `bilateral_double_pair_detected`, `pair_side_count`, and neutral `section_state`.

- [ ] **Step 1: Write failing tests** for bilateral pair, unilateral pair and no-pair synthetic rasters; assert unilateral evidence never yields `BILATERAL_DOUBLE_PAIR`.
- [ ] **Step 2: Run the focused tests** and capture causal RED because the new API does not exist.
- [ ] **Step 3: Implement the minimal bilateral detector** by evaluating both cross-axis side windows independently using the existing stroke/pair rules.
- [ ] **Step 4: Run focused + inherited raster tests** and require PASS.
- [ ] **Step 5: Commit** `feat: add bilateral hosted-marker transverse evidence`.

### Task 2: Neutral carrier topology

**Files:**
- Create: `experiments/cew_b01/hosted_marker_graphical_repair.py`
- Create: `tests/cew_b01/test_hosted_marker_graphical_repair.py`

**Interfaces:**
- Consumes: one PR #168 occurrence and its selected carrier.
- Produces: `carrier_topology_evidence(candidate, carrier) -> dict[str, Any]` with before/after run, normalized ratios and `topology_state`.

- [ ] **Step 1: Write failing tests** for through carrier, end/terminated carrier and deterministic reversed inputs.
- [ ] **Step 2: Run focused tests** and capture RED for missing topology API.
- [ ] **Step 3: Implement topology evidence** from carrier overlap interval relative to marker long-axis interval; no structural labels.
- [ ] **Step 4: Add junction-safety regression** showing unrelated orthogonal linework does not alone change `THROUGH_LINEAR_CARRIER`.
- [ ] **Step 5: Run tests** and require PASS.
- [ ] **Step 6: Commit** `feat: classify neutral hosted-marker carrier topology`.

### Task 3: Marker alignment evidence and repair role

**Files:**
- Modify: `experiments/cew_b01/hosted_marker_graphical_repair.py`
- Modify: `tests/cew_b01/test_hosted_marker_graphical_repair.py`

**Interfaces:**
- Produces: `marker_alignment_evidence(binary_ink, marker_geometry) -> dict[str, Any]` and `refine_graphical_candidate(candidate, carrier, binary_ink) -> dict[str, Any]`.

- [ ] **Step 1: Write failing tests** with an aligned rectangle and an intentionally shifted rectangle; assert no geometry mutation occurs.
- [ ] **Step 2: Run focused tests** and capture causal RED.
- [ ] **Step 3: Implement per-side raster edge-support measurement** in a narrow tolerance band and neutral states `ALIGNED`, `WEAK_EDGE_SUPPORT`, `GEOMETRY_MISMATCH`.
- [ ] **Step 4: Implement repair-role precedence**: alignment review, carrier topology review, partial transverse review, eligible bilateral double pair, eligible alone.
- [ ] **Step 5: Run tests** and require PASS with authority flags false.
- [ ] **Step 6: Commit** `feat: add marker alignment and graphical repair roles`.

### Task 4: Exact TAV.5 replay and corrective micro-atlas

**Files:**
- Create: `.github/workflows/validate-cew-b01-hosted-marker-graphical-repair.yml`
- Create: `governance/cew-b01/HOSTED_MARKER_GRAPHICAL_REPAIR_v1.json`
- Create or update: `docs/experiments/2026-10-30-cew-b01-hosted-marker-graphical-repair.md`

**Interfaces:**
- Consumes: exact frozen TAV.5 source and PR #168 occurrence search.
- Produces: governed repair JSON, corrective micro-atlas PNG, deterministic replay digest.

- [ ] **Step 1: Add exact-source workflow** that regenerates TAV.5, PR #168 occurrences and repair evidence twice.
- [ ] **Step 2: Assert conservation**: every PR #168 review-eligible occurrence ID is present exactly once in repair output; no original provenance removed.
- [ ] **Step 3: Assert authority boundary** false for semantic, structural, canonical, G2C, G3 and merge flags.
- [ ] **Step 4: Render bounded micro-atlas** for eligible ALONE, bilateral double pair, partial, carrier-topology review and marker-alignment review; show both-side transverse overlays and alignment warnings.
- [ ] **Step 5: Execute exact-source workflow** and accept observed counts as-is; do not relax thresholds to fit expectations.
- [ ] **Step 6: Freeze governed receipt** with exact SHA, run/artifact IDs, counts, replay digest and Human Review status.
- [ ] **Step 7: Commit** `docs: freeze hosted-marker graphical repair evidence`.

### Task 5: Final verification and PR checkpoint

**Files:**
- No product changes expected.

**Interfaces:**
- Consumes: complete branch delta and exact-source evidence.
- Produces: Draft PR checkpoint only.

- [ ] **Step 1: Run/inspect Unit Gate, Memory Gate and exact-source repair gate on one exact head.**
- [ ] **Step 2: Inspect net changed files and ensure no diagnostic/temp workflow remains.**
- [ ] **Step 3: Auto-review the complete delta for provenance loss, semantic leakage and threshold overfitting.**
- [ ] **Step 4: Update Draft PR body with exact head, run IDs, artifact/digest, observed repair-role counts and unresolved Human Review items.**
- [ ] **Step 5: Keep Draft/open/non-promoting; do not merge.**
