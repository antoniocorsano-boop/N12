# CEW-B01 Prototype-Guided Occurrence Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic first-pass shortlist of non-DOUBLE TAV.5 occurrences for Human Review against approved T1/T2 graphical prototypes, and export source-only review evidence without changing detector thresholds.

**Architecture:** Add a pure shortlist function over the existing exact-source replay records, then wire it into a source-only export tool and the current exact-source workflow. The function never assigns T1/T2; it only selects and prioritizes review candidates. Human Review remains the only authority for `SIMILAR_TO_T1`, `SIMILAR_TO_T2`, `NEITHER`, or `UNCERTAIN`.

**Tech Stack:** Python 3.12.15, unittest, OpenCV, existing CEW-B01 exact-source replay and GitHub Actions.

**Spec:** `docs/experiments/2026-10-30-cew-b01-prototype-guided-occurrence-expansion-design.md`

## Global Constraints

- Source remains TAV.5 SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Reuse existing exact-source 46-record replay; no new extraction logic.
- No changes to `describe_transverse_band` thresholds or graphical-state rules.
- Already-reviewed DOUBLE records are excluded from expansion.
- Known negative-control primitive IDs are excluded.
- First-pass expansion accepts only `RECT_PLUS_PARTIAL_TRANSVERSE_TRACES` with `THROUGH_CONTINUOUS` topology.
- Shortlist ranking is A/B/C as defined by the spec; ranking is not semantic classification.
- No automatic T1/T2 assignment.
- Semantic classification, structural identity, canonical write, G2C, G3 and merge authority remain false.

## Review Focus

- Input-order reversal must not change shortlist membership or ranking.
- A DOUBLE record must never re-enter the expansion shortlist.
- A `JUNCTION_COMPLEX` partial must stay out of the first pass.
- A known negative control must stay out even if its graphical metadata otherwise qualifies.
- A shortlisted candidate must still carry `PROTOTYPE_MATCH_PENDING_HUMAN_REVIEW` and no semantic authority.

---

### Task 1: Add deterministic shortlist contract

**Files:**
- Create: `experiments/cew_b01/prototype_guided_occurrence_search.py`
- Create: `tests/cew_b01/test_prototype_guided_occurrence_search.py`
- Modify: `.github/workflows/validate-cew-b01-beam-hosted-marker-pilot.yml`

**Interfaces:**
- Consumes: exact-source replay `records` plus a set of excluded primitive IDs.
- Produces: `shortlist_prototype_guided_occurrences(records, excluded_ids) -> list[dict]`.

- [ ] **Step 1: Write failing tests** covering exclusion of DOUBLE, exclusion of `JUNCTION_COMPLEX`, exclusion by primitive ID, A/B/C priority assignment, authority flags, and input-order determinism.
- [ ] **Step 2: Wire the new test module into the Unit Gate and run it to observe RED** because the production module/function does not yet exist.
- [ ] **Step 3: Implement the minimal pure shortlist function** with stable ordering `(priority, marker_primitive_id)` and no T1/T2 assignment.
- [ ] **Step 4: Run the targeted test and the complete Beam-Hosted Marker Unit Gate; expect PASS.**
- [ ] **Step 5: On the frozen exact-source replay, assert 11 shortlisted candidates distributed A=6, B=2, C=3.**

### Task 2: Export exact-source Human Review package

**Files:**
- Create: `experiments/cew_b01/prototype_guided_occurrence_export.py`
- Modify: `.github/workflows/validate-cew-b01-marker-cross-axis-repair.yml`

**Interfaces:**
- Consumes: `marker-cross-axis-repair.json`, exact 300-dpi raster, T1/T2 prototype registry, negative-control receipt.
- Produces: `prototype-guided-occurrence-candidates.json`, individual source-only crops, and `prototype-guided-occurrence-review-atlas.png`.

- [ ] **Step 1: Add a failing unit contract for manifest structure and authority flags using a synthetic raster.**
- [ ] **Step 2: Implement source-only crop export using the existing crop geometry convention; metadata and labels remain outside each crop.**
- [ ] **Step 3: Include T1/T2 reference identifiers in the manifest but do not duplicate them as new candidates.**
- [ ] **Step 4: Add the exporter to the exact-source workflow and upload its output in the existing evidence artifact.**
- [ ] **Step 5: Run fresh Unit, Repository Memory, Cross-Axis Exact-Source and Topology Exact-Source qualification on one exact SHA.**

### Task 3: Freeze governed expansion receipt and prepare Human Review

**Files:**
- Create: `governance/cew-b01/PROTOTYPE_GUIDED_OCCURRENCE_EXPANSION_v1.json`
- Modify: PR #169 body.

**Interfaces:**
- Consumes: exact-source expansion manifest from Task 2.
- Produces: governed receipt with 11 candidate primitive IDs and `PENDING_HUMAN_REVIEW` decisions.

- [ ] **Step 1: Record exact source/run/artifact provenance and all 11 candidate IDs.**
- [ ] **Step 2: Keep allowed Human Review decisions limited to `SIMILAR_TO_T1`, `SIMILAR_TO_T2`, `NEITHER`, `UNCERTAIN`.**
- [ ] **Step 3: Keep all semantic/structural/canonical/G2C/G3/merge flags false.**
- [ ] **Step 4: Update PR #169 with exact head, gate results and `PROTOTYPE_GUIDED_OCCURRENCE_HUMAN_REVIEW_PENDING`.**
- [ ] **Step 5: Do not merge or promote any candidate before Human Review.**
