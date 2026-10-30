# CEW-B01 G2A0 Coalescence Eight-Seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a neutral co-spatial observation-bundling layer and re-run the same frozen eight-seed TAV.5 pilot to determine whether duplicate G1 observations stop inflating G2B CORE composition without losing provenance.

**Architecture:** Keep the qualified G1 census immutable. Introduce `ObservationBundle`-like neutral bundles only inside the experiment: observations may share one bundle when they are co-spatial/near-coincident and graphically derived from the same local event, while every original `primitive_id`, detector, family and source geometry remains recorded. Build the existing CORE/CONTEXT candidate graph over bundles, not raw observations, then emit explicit before/after diagnostics for the same eight seeds.

**Tech Stack:** Python 3.12, stdlib, existing CEW-B01 JSON artifact and experiment code.

**Spec:** `docs/experiments/2026-10-29-cew-b01-g2-composition-small-spike.md`

## Global Constraints

- Keep the exact eight frozen seed primitive IDs from `governance/cew-b01/G2_COMPOSITION_SMALL_PILOT_v1.json`.
- Keep source SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580` and qualified G1 count `5633` unchanged.
- No semantic labels, structural identity, canonical writes or G3 authorization.
- Coalescence must preserve every original primitive ID and provenance entry; no G1 observation may disappear from the bundle mapping.
- Do not tune the rule to historical structural-object counts or meanings.

## Review Focus

- Near-coincident observations with different derived families must bundle only when their geometry strongly overlaps; nearby but distinct symbols must remain separate.
- A long line crossing a local symbol must not be absorbed into the same bundle merely because its bbox overlaps.
- Bundle membership must be deterministic under reversed input order.
- Every input primitive participating in a candidate must be recoverable from exactly one bundle mapping.
- The real-source eight-seed run must keep the same seed identities and expose before/after CORE sizes without silently dropping context.

---

### Task 1: Neutral co-spatial observation bundling

**Files:**
- Create: `experiments/cew_b01/g2a0_observation_bundles.py`
- Create: `tests/cew_b01/test_g2a0_observation_bundles.py`

**Interfaces:**
- Consumes: qualified G1 primitive mappings from `primitive-census.json`.
- Produces: `bundle_observations(primitives: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str]]`, where each bundle contains stable `bundle_id`, bbox, member primitive IDs, families, detectors, source/page/frame and no semantic field; the second value maps each primitive ID to exactly one bundle ID.

- [ ] **Step 1: Write failing tests** covering co-spatial derived-family fusion, long-line exclusion, nearby-distinct separation, provenance completeness and reversed-input determinism.
- [ ] **Step 2: Run `python -m unittest tests.cew_b01.test_g2a0_observation_bundles -v` and verify RED because the module/API does not yet exist.**
- [ ] **Step 3: Implement the minimal deterministic bundler.** Use union-find only for strong overlap/near-coincidence among compact observations; prevent geometrically dominant line-like observations from joining compact local bundles.
- [ ] **Step 4: Re-run the focused tests and verify PASS.**
- [ ] **Step 5: Run the existing CEW-B01 unit suite `python -m unittest discover -s tests/cew_b01 -p 'test_*.py'` and record all results.**

### Task 2: Rebuild the frozen eight candidates over bundles and compare before/after

**Files:**
- Modify: `experiments/cew_b01/g2_composition_small_spike.py`
- Create: `tests/cew_b01/test_g2_composition_small_spike.py`
- Modify: `docs/experiments/2026-10-29-cew-b01-g2-composition-small-spike.md`

**Interfaces:**
- Consumes: `bundle_observations(...)` from Task 1 plus the frozen manifest and real `primitive-census.json`.
- Produces: result JSON containing raw-observation CORE counts, bundled CORE counts, bundle provenance, candidate comparison metrics and unchanged non-authority flags.

- [ ] **Step 1: Write failing tests** asserting the same eight seed IDs remain bound, every bundled candidate can expand back to original primitive IDs, output is deterministic under primitive-order reversal, and authority flags remain false.
- [ ] **Step 2: Run the focused spike test and verify RED because bundled comparison fields are missing.**
- [ ] **Step 3: Modify the spike to build candidate graphs over bundles while retaining the raw baseline result in the output.**
- [ ] **Step 4: Run focused tests and verify PASS.**
- [ ] **Step 5: Run the script twice on the exact qualified artifact, compare output SHA-256 byte-for-byte, and record the before/after eight-element CORE vectors.**
- [ ] **Step 6: Update the experiment document with the measured result, including any candidate still saturating the cap; do not claim success unless the real-source run demonstrates it.**
- [ ] **Step 7: Re-run the full `tests/cew_b01` unit suite.**

### Task 3: Exact-head verification and PR record

**Files:**
- Modify only PR #166 description if the measured result changes the interpretation.

**Interfaces:**
- Consumes: tested code and exact real-source replay evidence from Tasks 1–2.
- Produces: auditable Draft PR state with no merge/promotion authority.

- [ ] **Step 1: Verify branch diff is limited to the pilot plan, bundling code/tests, spike/test and experiment documentation.**
- [ ] **Step 2: Verify exact head and any available CI/workflow status.**
- [ ] **Step 3: Update PR #166 with measured before/after result and explicit boundary; keep Draft and unmerged.**
