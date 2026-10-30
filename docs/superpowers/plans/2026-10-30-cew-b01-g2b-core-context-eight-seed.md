# CEW-B01 G2B CORE/CONTEXT Eight-Seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine only the CORE/CONTEXT boundary for the same eight frozen TAV.5 candidates, moving geometrically dominant or merely-near neighbours out of the local symbol nucleus without deleting any G2A0 bundle or provenance.

**Architecture:** Keep G2A0 output immutable as the input surface. G2B is a pure, neutral reclassification layer over each candidate: the seed remains CORE; compact bundles with direct topological contact may remain CORE; `NEAR`-only neighbours and geometrically dominant line/closed/complex bundles move to CONTEXT with explicit reason codes. No semantic or structural meaning is introduced.

**Tech Stack:** Python 3.12, stdlib, existing CEW-B01 experiment JSON and GitHub Actions unit gates.

**Spec:** `docs/experiments/2026-10-29-cew-b01-g2-composition-small-spike.md`

## Global Constraints

- Use exactly the same eight frozen seed primitive IDs and the same qualified TAV.5 source.
- G2A0 bundles and their constituent `primitive_id` provenance are immutable input evidence.
- Moving a bundle from CORE to CONTEXT must preserve its bundle ID and every member primitive ID.
- No bundle may be dropped; `CORE ∪ CONTEXT` after G2B must equal the incoming G2A0 candidate membership.
- No semantic labels, structural identity, canonical writes, G3 authorization or merge authorization.
- Thresholds are experimental pilot rules, not production or structural criteria.

## Review Focus

- `NEAR` without overlap/touch/containment must not be promoted to nucleus membership merely because it is close.
- Long attached linework crossing or leaving the seed region must remain CONTEXT even when touching/overlapping the seed.
- A larger closed or complex neighbour that geometrically dominates the seed must remain CONTEXT.
- Compact overlapping local derived-event bundles must remain CORE.
- Reclassification must be deterministic and provenance-preserving.

---

### Task 1: G2B neutral boundary classifier

**Files:**
- Create: `experiments/cew_b01/g2b_core_context_refinement.py`
- Create: `tests/cew_b01/test_g2b_core_context_refinement.py`
- Create: `.github/workflows/validate-cew-b01-g2b-pilot.yml`

**Interfaces:**
- Consumes: one G2A0 candidate from `g2_composition_bundled_compare.py`.
- Produces: `refine_candidate(candidate: dict[str, Any]) -> dict[str, Any]` with `g2b_core_bundle_ids`, `g2b_context_bundle_ids`, expanded primitive IDs, deterministic `boundary_decisions`, and all authority flags false.

- [ ] **Step 1: Write failing tests** for NEAR-only demotion, dominant line demotion, dominant closed/complex demotion, compact overlapping derived-event retention, membership conservation and determinism.
- [ ] **Step 2: Run the dedicated G2B gate and verify RED because the new module does not exist.**
- [ ] **Step 3: Implement the minimal neutral classifier.** Pilot rules: seed always CORE; `NEAR`-only non-seed bundles move to CONTEXT; line-only bundles whose major span exceeds `2.0 ×` seed major span move to CONTEXT; non-seed `RECTILINEAR_CLOSED_SHAPE`/`COMPLEX_GRAPHIC_GROUP` bundles move to CONTEXT when area exceeds `1.8 ×` seed area or major span exceeds `1.6 ×` seed major span; otherwise retain the incoming G2A0 CORE classification.
- [ ] **Step 4: Verify GREEN on the dedicated gate and repository memory gate.**

### Task 2: Exact eight-seed replay and human-review atlas

**Files:**
- Create: `governance/cew-b01/G2B_EIGHT_SEED_RESULT_v1.json`
- Modify: `docs/experiments/2026-10-29-cew-b01-g2-composition-small-spike.md`

**Interfaces:**
- Consumes: exact G2A0 eight-seed result and `refine_candidate(...)`.
- Produces: deterministic eight-candidate before/after counts, moved-bundle reason receipts, membership-conservation evidence and a human-review micro-atlas.

- [ ] **Step 1: Replay the same eight candidates twice and require byte-identical output.**
- [ ] **Step 2: Verify every candidate preserves `incoming CORE ∪ CONTEXT == G2B CORE ∪ CONTEXT` and every moved bundle appears in CONTEXT with a reason code.**
- [ ] **Step 3: Generate the eight-case micro-atlas showing G2A0 CORE versus G2B nucleus and moved CONTEXT.**
- [ ] **Step 4: Record only neutral findings; human decisions remain limited to `SAME_CONFIGURATION / DIFFERENT_CONFIGURATION / ARTIFACT / NON_SIGNIFICANT / UNCERTAIN`.**
- [ ] **Step 5: Keep PR #166 Draft and non-promoting; do not authorize G3 or merge.**
