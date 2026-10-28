# CEW-B01 Drawing Grammar V3 Implementation Plan

> **STATUS: SUPERSEDED BY RECONCILIATION — DO NOT CONTINUE THIS PLAN AS WRITTEN.**
>
> On 2026-10-28 repository reconciliation found that Tasks 1–2 assign generic similarity, family discovery and prototype responsibilities already implemented in qualified noncanonical CEW lines (#116, #137, #143). Continuing this plan would violate `BUILD LAST — REUSE FIRST`.
>
> Canonical reconciliation inputs for the active B01 task:
>
> - `docs/repo-memory/CEW_REPO_MEMORY_v1.md`
> - `docs/repo-memory/CEW_B01_RECONCILIATION_MATRIX_v1.md`
> - `docs/repo-memory/CEW_LESSONS_LEARNED_v1.md`
> - `governance/repo-memory/CEW_CAPABILITY_REGISTRY_v1.json`
> - `governance/repo-memory/CEW_B01_REUSE_DECISION_v1.json`
>
> The residual implementation boundary is now:
>
> 1. B01 exact-source adapter into existing primitive/prototype/similarity contracts;
> 2. B01-specific high-recall proposal feature/channel only where existing discovery is insufficient;
> 3. deterministic candidate union/dedup/provenance mapping;
> 4. exact TAV.5 qualification + human review evidence.
>
> The historical content below is retained only as provenance for how the duplicate responsibility was discovered. It is not an executable implementation plan.

---

## Historical plan — retained for provenance only

**Original goal:** Replace the narrow Step 4 four-cell-only detector with a high-recall, source-bound candidate system that learns local technical-drawing motif families and supports deterministic `find_similar` without assigning structural identity.

**Original architecture:** Keep the qualified V2 compound-cell channel, add a technical-drawing grammar module that derives neutral frame motifs, context fingerprints, prototype/family candidates and similarity matches, then union those candidates in Step 4 with deterministic deduplication. Human review remains the precision/promotion gate; real TAV.5 qualification must regenerate the review surface and expose channel/family evidence.

**Why superseded:** generic family discovery, project-local learning and `find_similar` are repository capabilities and must be reused/adapted rather than recreated inside `cew_b01`.

### Historical Task 1: Drawing grammar primitives and fingerprints

The closed-frame/internal-mark extraction work may be retained only as an experimental B01-specific proposal/feature channel. Generic similarity ownership is superseded.

### Historical Task 2: Prototype/family discovery and find-similar

**Do not implement as a new B01 subsystem.** Reconcile against #116 and #137.

### Historical Task 3: Integrate grammar into Step 4 V3 candidate union

The candidate-union responsibility remains valid, but it must consume reconciled/reused capabilities rather than a second local similarity/learning stack.

### Historical Task 4: Real-source qualification and review evidence

This responsibility remains valid. Exact-source qualification must be rerun after bounded reuse/adaptation and must preserve the human review/promotion boundary.

## Current completion boundary

No implementation continuation is authorized from this historical plan alone. A revised reuse-first implementation plan must be produced from the reconciliation matrix before new product code is added.
