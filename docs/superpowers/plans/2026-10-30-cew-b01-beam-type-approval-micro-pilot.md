# CEW-B01 Beam-Type Approval Micro-Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce one exact-source Human Review example for each proposed neutral graphical type — cross-axis double band and long-axis double band — plus two negative controls, without encoding structural semantics.

**Architecture:** Reuse the exact-source replay and frozen TAV.5 evidence already qualified on PR #169. First export source-only crops for every current DOUBLE candidate. Then select one candidate per proposed orientation relation using the source-only raster as authority. Finally generate a four-panel approval package and a provenance manifest; no detector thresholds or semantic authority change in this plan.

**Tech Stack:** Python 3.12.15, OpenCV, existing CEW-B01 exact-source workflow and provenance JSON.

**Spec:** `docs/experiments/2026-10-30-cew-b01-beam-type-approval-micro-pilot-design.md`

## Global Constraints

- Source remains TAV.5 SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Source-only crop is the Human Review visual authority.
- No automatic `trave emergente` / `trave a spessore` semantics.
- No structural identity, canonical writes, G2C, G3 or merge authority.
- Do not tune thresholds to force one candidate per type.

## Review Focus

- A candidate whose major-axis relation is visually ambiguous must become `UNCERTAIN`, not be forced into T1/T2.
- A carrier/support topology that resembles a pillar/junction must be retained as a negative control, not a positive type.
- Source-only and overlay views must refer to the same primitive ID and geometry.
- A candidate may be visually convincing but still lack sufficient provenance; such a candidate cannot become the approval example.
- If one type has no clean example on TAV.5, record `TYPE_EXAMPLE_NOT_FOUND` rather than fabricating one.

---

### Task 1: Export all DOUBLE candidates source-only

**Files:**
- Modify: `.github/workflows/validate-cew-b01-marker-cross-axis-repair.yml`
- Use: `experiments/cew_b01/marker_cross_axis_exact_source.py`

**Interfaces:**
- Consumes: `marker-cross-axis-repair.json` and regenerated 300-dpi TAV.5 raster.
- Produces: `double-candidates-source-only-atlas.png`, individual `double-<n>-<primitive-id>.png`, and `double-candidates-manifest.json`.

- [ ] **Step 1:** Extend only the evidence-export step to enumerate records whose `transverse_band.graphical_state == RECT_PLUS_DOUBLE_TRANSVERSE_BAND`.
- [ ] **Step 2:** Export a source-only crop for every such record with no coloured overlay inside the raster crop.
- [ ] **Step 3:** Emit manifest fields: primitive ID, carrier orientation, marker width/height, major-axis orientation, source/review geometry, evidence sources and cross-axis counts.
- [ ] **Step 4:** Run exact-source workflow on one exact SHA and verify Unit Gate + Memory Gate + Cross-Axis Exact-Source all PASS.
- [ ] **Step 5:** Confirm candidate count matches the replay's DOUBLE count exactly.

### Task 2: Select one example per proposed graphical type

**Files:**
- Create: `governance/cew-b01/BEAM_TYPE_APPROVAL_MICRO_PILOT_v1.json`

**Interfaces:**
- Consumes: source-only atlas and manifest from Task 1.
- Produces: selected P1/P2 primitive IDs and two negative-control IDs with all authority flags false.

- [ ] **Step 1:** Inspect every source-only DOUBLE crop, using only visible source geometry plus recorded major-axis orientation.
- [ ] **Step 2:** Select the cleanest `CROSS_AXIS_DOUBLE_BAND_CANDIDATE` if present; otherwise record `TYPE_EXAMPLE_NOT_FOUND`.
- [ ] **Step 3:** Select the cleanest `LONG_AXIS_DOUBLE_BAND_CANDIDATE` if present; otherwise record `TYPE_EXAMPLE_NOT_FOUND`.
- [ ] **Step 4:** Select one ALONE/PARTIAL negative control and one topology/support negative control.
- [ ] **Step 5:** Write the governed manifest with decisions `PENDING_HUMAN_REVIEW` and all semantic/structural/canonical/G2C/G3/merge flags false.

### Task 3: Produce the four-panel approval package

**Files:**
- Modify: `.github/workflows/validate-cew-b01-marker-cross-axis-repair.yml`
- Evidence output: `beam-type-approval-source-only.png`, `beam-type-approval-overlay.png`.

**Interfaces:**
- Consumes: governed selections from Task 2 and exact-source replay evidence.
- Produces: Human Review package for P1–P4.

- [ ] **Step 1:** Render P1–P4 source-only panels from the exact 300-dpi source.
- [ ] **Step 2:** Render a matching overlay sheet with marker/carrier/evidence provenance, keeping source-only sheet separate.
- [ ] **Step 3:** Verify each panel ID and geometry exactly match the governance manifest.
- [ ] **Step 4:** Run fresh Unit, Memory and Exact-Source qualification on the final exact SHA.
- [ ] **Step 5:** Update PR #169 body with current exact head, artifact ID/digest, selected panel IDs, and `HUMAN_TYPE_APPROVAL_PENDING`.
