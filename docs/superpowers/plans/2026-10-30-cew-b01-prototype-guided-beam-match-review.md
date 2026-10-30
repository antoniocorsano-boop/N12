# CEW-B01 Prototype-Guided Beam Graphical Match Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a governed Human Review matrix that compares all eight frozen TAV.5 DOUBLE candidates with the two approved graphical prototypes without granting semantic or structural authority.

**Architecture:** Reuse the exact-source candidate manifest from run `41044608383` and the approved prototype registry. Perform a source-only relational review, record proposed buckets in a governance JSON, then generate a human-readable review sheet outside the detector path. No production detector code or thresholds change.

**Tech Stack:** JSON governance records, existing GitHub Actions qualification, Python only for local review-sheet assembly.

**Spec:** `docs/experiments/2026-10-30-cew-b01-prototype-guided-beam-match-review-design.md`

## Global Constraints

- Frozen source: `archive/documentazione_originaria/tavola 5.pdf`, SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Frozen exact-source evidence: run `41044608383`, artifact `12971414043`, digest `sha256:fbec5e5eedebb122b666bc0db8bdb660fadaa8a00f1ae194618f38bfe09b26a3`.
- Approved prototype registry: `governance/cew-b01/BEAM_GRAPHICAL_TYPE_PROTOTYPES_v1.json`.
- Every non-reference candidate remains `PENDING_HUMAN_REVIEW`.
- No automatic semantic classification, structural identity, canonical write, G2C, G3 or merge authority.
- No detector threshold change and no re-extraction.

## Review Focus

- Absolute page orientation must not decide T1/T2; only the relation between marker major axis and visible double-band direction does.
- Annotation or dimension text must not override source geometry.
- D03/D06 are vertical long-axis cases and must not be misread as T1 merely because T1's approved exemplar is vertical.
- D02 is a mirrored-side cross-axis case and must remain eligible for T1.
- Any visually ambiguous relation must become `UNCERTAIN`, not be forced into a prototype family.

---

### Task 1: Freeze prototype-guided candidate review matrix

**Files:**
- Create: `governance/cew-b01/BEAM_GRAPHICAL_TYPE_MATCH_REVIEW_v1.json`

**Interfaces:**
- Consumes: `BEAM_GRAPHICAL_TYPE_PROTOTYPES_v1.json` and the frozen `double-candidates-manifest.json` from artifact `12971414043`.
- Produces: one governed review record for each of D01–D08.

- [ ] **Step 1:** Verify the frozen candidate count is exactly 8 and the primitive IDs match the exact-source manifest.
- [ ] **Step 2:** Record D01 and D05 as prototype reference anchors, not new automatic decisions.
- [ ] **Step 3:** Record the source-only proposed buckets for D02–D04 and D06–D08 with `human_review_state = PENDING_HUMAN_REVIEW`.
- [ ] **Step 4:** Set all semantic/structural/canonical/G2C/G3/merge authority flags false.
- [ ] **Step 5:** Validate the JSON parses and contains exactly one row per frozen candidate.

### Task 2: Produce Human Review sheet

**Files:**
- Local review artifact only; no detector code changes.

**Interfaces:**
- Consumes: the eight source-only crops and Task 1 review matrix.
- Produces: a labeled contact sheet showing prototype anchors and proposed bucket for all candidates.

- [ ] **Step 1:** Assemble the source-only crops without modifying their image content.
- [ ] **Step 2:** Add labels outside each crop: panel ID, primitive ID suffix, proposed bucket and review state.
- [ ] **Step 3:** Keep T1/T2 prototype anchors visibly identified.
- [ ] **Step 4:** Present the sheet for Human Review; no candidate becomes confirmed merely by generating the sheet.

### Task 3: Requalify governance-only head

**Files:**
- No additional product files unless a validator requires an explicit governance contract.

**Interfaces:**
- Consumes: current branch head after Task 1.
- Produces: fresh Unit Gate, Repository Memory Gate and exact-source replay status.

- [ ] **Step 1:** Confirm PR #169 remains open, Draft and non-merged.
- [ ] **Step 2:** Verify Unit Gate and Repository Memory Gate on the exact new head.
- [ ] **Step 3:** Verify both exact-source replay workflows on the exact new head.
- [ ] **Step 4:** Update PR body with the new exact head and `PROTOTYPE_GUIDED_MATCH_HUMAN_REVIEW_PENDING`.
- [ ] **Step 5:** Do not merge or promote any authority.
