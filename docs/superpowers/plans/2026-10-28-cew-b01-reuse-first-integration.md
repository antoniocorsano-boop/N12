# CEW-B01 Reuse-First Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the repository-memory loop and complete CEW-B01 Step 4 as a reuse-first, source-bound candidate system that reuses existing CEW capabilities instead of reimplementing generic learning/similarity subsystems.

**Architecture:** Repository Memory becomes an active governance gate through a machine validator that checks capability-registry and reuse-decision consistency and requires new CEW plans to declare consulted capability IDs. CEW-B01 then narrows its local responsibility to exact-source proposal extraction, adaptation into reused CEW similarity contracts, deterministic candidate union/deduplication, and exact TAV.5 qualification. Historical CEW capability code is ported only as the smallest coherent unit with explicit provenance.

**Tech Stack:** Python 3.12.15, JSON, unittest, OpenCV 5.0.0.93, GitHub Actions exact-SHA workflows.

**Spec:** `docs/repo-memory/CEW_B01_RECONCILIATION_MATRIX_v1.md`, `docs/repo-memory/CEW_REPO_MEMORY_v1.md`, `docs/superpowers/specs/2026-10-28-cew-b01-drawing-grammar-induction-design.md`

## Repository Memory / Reuse Assessment

Consulted capabilities:
- `CEW-CAP-MASTER-BUILD-LAST-REUSE-FIRST` -> REUSE governance.
- `CEW-CAP-ENG-DRAWING-GRAMMAR-V1` -> PORT bounded interpretation rules/provenance only.
- `CEW-CAP-OA3-DETERMINISTIC-SIMILARITY-V1` -> PORT/ADAPT deterministic similarity contract.
- `CEW-CAP-VISUAL-PROTOTYPE-LEARNING-V1` -> REUSE contract concepts; no new B01 learning ontology.
- `CEW-CAP-ZERO-PRIOR-GRAPHIC-DISCOVERY-V1` -> ADAPT source-bound primitive concepts.
- `CEW-CAP-B01-V2-COMPOUND-CELL-DETECTOR` -> REUSE as high-precision candidate channel.
- `CEW-CAP-B01-CLOSED-FRAME-INTERNAL-MARK-SPIKE` -> ADAPT only as B01 proposal/feature channel.
- `CEW-CAP-B01-CANDIDATE-UNION-QUALIFICATION` -> BUILD/ADAPT as the active task-local responsibility.

New work is justified only for the B01 adapter, B01-local proposal channel, union/dedup/provenance, repository-memory validation, and exact-source qualification.

## Global Constraints

- Immutable TAV.5 / governed Step-3 raster remain evidentiary authority.
- No hard-coded support numbers, historical count oracle, manual source coordinates or semantic labels in production candidate generation.
- Similarity/prototype/family membership never creates structural identity or canonical write authority.
- `19` and `22` remain human-observed regression witnesses only; literal identifiers and coordinates are forbidden production inputs.
- Historical PRs are not merged wholesale; only bounded coherent capability slices may be ported/adapted.
- The existing `cew_b01/drawing_grammar.py` may retain source-local extraction/features but must not remain owner of generic family memory or generic `find_similar` semantics.
- Human review remains the precision and promotion gate.

## Review Focus

- Registry/reuse-decision drift: fail closed if a decision references an unknown capability or invalid reuse disposition.
- Plan bypass: a new CEW implementation plan without Repository Memory / Reuse Assessment must fail the memory gate.
- Provenance loss in adapter: source/version/page/candidate identity must survive transformation into similarity inputs.
- Duplicate similarity ownership: B01 must not silently continue a second generic similarity engine after OA-3 reuse is introduced.
- Real-source recall: exact TAV.5 review evidence must expose the previously omitted recurring numbered-symbol class without identifier/coordinate oracle data.

---

### Task 1: Activate Repository Memory Gate

**Files:**
- Create: `automation/validate_cew_repo_memory.py`
- Create: `tests/test_cew_repo_memory.py`
- Create: `.github/workflows/validate-cew-repo-memory.yml`
- Modify: `docs/repo-memory/CEW_REPO_MEMORY_v1.md`

**Interfaces:**
- Consumes: `governance/repo-memory/CEW_CAPABILITY_REGISTRY_v1.json`, `governance/repo-memory/*_REUSE_DECISION_v1.json`, CEW implementation plans.
- Produces: deterministic PASS/FAIL validation and actionable diagnostics.

- [ ] Write RED tests for unknown capability IDs, invalid reuse dispositions, and a CEW plan missing `## Repository Memory / Reuse Assessment`.
- [ ] Verify RED because validator is absent.
- [ ] Implement `validate_repository_memory(root: Path) -> list[str]` and CLI exit behavior; valid current memory returns no errors.
- [ ] Add exact-SHA workflow running validator and tests.
- [ ] Run gate and require GREEN.

### Task 2: Port OA-3 Deterministic Similarity as a Reused Capability

**Files:**
- Create: `cew_reuse/__init__.py`
- Create: `cew_reuse/oa3_similarity_v1.py`
- Create: `tests/cew_b01/test_reuse_similarity_adapter.py`
- Create: `cew_b01/reuse_adapter.py`

**Interfaces:**
- Ported source provenance: PR #116 / `a7020bef3934156c917f5bfe975d888c6ba9e684` / `scripts/cew_oa3_deterministic_similarity.py`.
- Produces: `find_similar(scene, prototype, weights=None)` with OA-3 authority invariants unchanged.
- Produces: `motif_to_oa3_object(motif, *, source_binding, candidate_id) -> dict` and `build_oa3_scene(...) -> dict`.

- [ ] Write RED tests proving B01 motif/source binding maps into OA-3 signals without losing source version/page/evidence identity and that translated/context-compatible candidates outrank incompatible context.
- [ ] Verify RED because reuse module/adapter are absent.
- [ ] Port the smallest coherent OA-3 similarity unit with provenance header and unchanged authority behavior.
- [ ] Implement B01 adapter only; do not add a new similarity formula.
- [ ] Run focused tests and OA-3 authority assertions; require GREEN.

### Task 3: Narrow B01 Drawing Channel Ownership

**Files:**
- Modify: `cew_b01/drawing_grammar.py`
- Modify: `tests/cew_b01/test_drawing_grammar_families.py`
- Modify: `tests/cew_b01/test_evidence_extraction.py`

**Interfaces:**
- Keep: source-local `DrawingGrammarConfig`, `DrawingMotif`, `extract_drawing_motifs` and measurable motif features used by Step 4.
- Remove/supersede generic ownership: `LocalSymbolFamilyCandidate`, generic `find_similar`, generic family discovery as production responsibilities.
- Similarity consumption moves through `cew_b01.reuse_adapter` + `cew_reuse.oa3_similarity_v1`.

- [ ] Write RED contract test asserting production B01 similarity path uses reused OA-3 module and no longer exposes local generic family discovery as the authoritative path.
- [ ] Verify RED on current branch.
- [ ] Refactor minimally: retain extraction/features, route similarity tests through adapter/OA-3, remove or clearly deprecate overlapping generic APIs.
- [ ] Run drawing-channel and reuse tests; require GREEN.

### Task 4: Reconcile Candidate Union and Provenance

**Files:**
- Modify: `cew_b01/evidence_extraction.py`
- Modify: `tests/cew_b01/test_evidence_extraction_v3.py`

**Interfaces:**
- `extract_g4_evidence_candidates(...)` remains the public Step-4 entry point.
- Union inputs: qualified V2 compound channel + B01 closed-frame/internal-mark proposal channel.
- Output method: `OPENCV_DRAWING_GRAMMAR_CANDIDATE_UNION_V3` while preserving per-channel reason/provenance evidence where contract allows.

- [ ] Preserve the already-green V3 synthetic recovery/dedup tests as regression contracts.
- [ ] Add RED test that union output contains no generic family/semantic assignment and retains exact source binding.
- [ ] Implement only the missing provenance/reason mapping required by the contract.
- [ ] Run Step-4 contract suite and require GREEN.

### Task 5: Exact TAV.5 Qualification and Human Review Regeneration

**Files:**
- Modify: `.github/workflows/validate-cew-b01-step4.yml` only where diagnostics are needed.
- Modify: `cew_b01/review_package.py` / tests only if required to surface channel/reuse explanations.
- Update: repository-memory decision/lesson record with final qualification outcome.

**Interfaces:**
- Exact-source run must emit candidate count, proposal-channel diagnostics, source digest, method IDs and review artifact.
- Review package remains `PENDING_HUMAN`.

- [ ] Run full exact-SHA Step 4 qualification on TAV.5 and replay deterministically.
- [ ] Regenerate Step-5 overview/contact sheets.
- [ ] Inspect review artifact for the omission class identified by the human; compatible visible symbols left unproposed => REWORK.
- [ ] If omissions remain, diagnose candidate extraction/context features rather than tuning generic similarity thresholds.
- [ ] Require all CEW-B01 relevant gates GREEN on the final exact SHA before Ready-for-review consideration.

## Completion boundary

This plan completes only when Repository Memory is enforced by CI, B01 no longer owns a duplicate generic similarity/family subsystem, the candidate union is source-bound and deterministic, and a fresh exact-source TAV.5 review package is available for human validation. No Step 6, structural identity, BIM/FEM, canonical write, merge or main promotion is authorized by this plan.
