# CEW-B01 V3 Reuse-First Implementation Plan

**Status:** ACTIVE — supersedes the historical drawing-grammar V3 implementation plan.

**Goal:** Close the Step 4 recall omission on exact TAV.5 evidence without creating a second CEW similarity, family-discovery, prototype-memory or engineering-grammar subsystem.

**Governance inputs:**
- `docs/repo-memory/CEW_B01_RECONCILIATION_MATRIX_v1.md`
- `governance/repo-memory/CEW_B01_REUSE_DECISION_v1.json`
- `governance/repo-memory/CEW_CAPABILITY_REGISTRY_v1.json`

## Repository Memory / Reuse Assessment

**Repository-memory retrofit (2026-10-28):** this section was added after activation of the CEW repository-memory gate; it does not rewrite the plan's original decisions.

Consulted capabilities and dispositions:
- `CEW-CAP-ENG-DRAWING-GRAMMAR-V1` → PORT bounded rules/provenance.
- `CEW-CAP-OA3-DETERMINISTIC-SIMILARITY-V1` → ADAPT/PORT deterministic similarity; do not reimplement locally.
- `CEW-CAP-VISUAL-PROTOTYPE-LEARNING-V1` → REUSE human-teaching/prototype-memory contract.
- `CEW-CAP-ZERO-PRIOR-GRAPHIC-DISCOVERY-V1` → ADAPT structured graphic descriptor/discovery contract.
- `CEW-CAP-B01-V2-COMPOUND-CELL-DETECTOR` → REUSE unchanged as one candidate channel.
- `CEW-CAP-B01-CLOSED-FRAME-INTERNAL-MARK-SPIKE` → ADAPT as B01 proposal feature channel only.
- `CEW-CAP-B01-CANDIDATE-UNION-QUALIFICATION` → BUILD/ADAPT because exact-source B01 union/qualification is task-local.

**Reusable sources:**
- OA-3 deterministic similarity: PR #116, `a7020bef3934156c917f5bfe975d888c6ba9e684`, `scripts/cew_oa3_deterministic_similarity.py`.
- Zero-prior structured graphic descriptor / visual-learning contracts: PR #137, `320755e66a7263f1842f73dc14fb9a0ea8ccd7f8`, `scripts/cew_new_project_preacquisition.py` and `scripts/cew_visual_learning.py`.
- Engineering drawing interpretation contract: PR #143, `098f98d2724c0a16b9293adc366a585f356bc9fc`, `automation/N12_ENGINEERING_DRAWING_GRAMMAR_CONTRACT_v1.json`.

## Authority boundary

All work remains proposal/evidence only. `structural_identity_authorized=false`, `canonical_write_authorized=false`, no Step 6 promotion, BIM/FEM/NTC authority, or automatic family membership. Human teaching/review remains required before any project-local meaning is attached.

## Task A — Replace duplicate local similarity/family ownership with a bounded adapter

**Create:**
- `cew_b01/reuse_adapter.py`
- `cew_b01/reused_oa3_similarity.py`
- `tests/cew_b01/test_reuse_adapter.py`

**Change:**
- `cew_b01/drawing_grammar.py`
- `tests/cew_b01/test_evidence_extraction.py`
- `.github/workflows/validate-cew-b01-drawing-grammar.yml`

**Contract:**
1. `DrawingMotif` remains a B01-local observation/feature record only.
2. Adapter derives stable nonauthoritative `source_version_id`, whole-page `page_id`, and whole-page `evidence_region_id` from the exact B01 `SourceIdentity`, while retaining the original source mapping.
3. Adapter maps each motif to the PR #137 structured descriptor vocabulary (`RECTILINEAR_CLOSED_SHAPE`, aspect/area/complexity/stroke buckets) and to the PR #116 OA-3 signal vocabulary.
4. OA-3 scorer is a bounded provenance-preserving port of the exact PR #116 algorithm; no B01-specific weight tuning.
5. A prototype can be constructed only through an explicitly named human-taught adapter call requiring a human decision identifier; the Step 4 detector never creates prototypes automatically.
6. Remove B01-local generic `find_similar`, local-family discovery, medoid/family IDs and generic similarity weighting.

**TDD:**
- RED: adapter imports absent; exact source identity must survive mapping; translated compatible motifs rank above context-incompatible motif; absent human decision blocks prototype construction; all OA-3 authority flags remain false.
- GREEN: minimal adapter + bounded OA-3 port; no local generic learning subsystem remains.

## Task B — Keep and narrow the B01-specific high-recall proposal channel

**Keep:** closed-frame + internal-mark extraction and measurable frame/interior/context features.

**Do not own:** generic clustering, family memory, semantic interpretation, prototype lifecycle or generic similarity.

The existing filename `drawing_grammar.py` may remain temporarily to avoid interface churn; its module contract must explicitly state `B01_PROPOSAL_FEATURE_CHANNEL_ONLY`. Rename only after dependent tests/review surfaces are reconciled.

## Task C — Candidate union/dedup and provenance diagnostics

**Keep:** `OPENCV_DRAWING_GRAMMAR_CANDIDATE_UNION_V3` as a B01-local union of V2 compound-cell proposals plus the bounded closed-frame/internal-mark proposal channel.

**Extend qualification evidence with:**
- candidate count and deterministic replay digests;
- channel capability IDs and exact source refs;
- method provenance for PR #116/#137/#143;
- explicit `semantic_identity_assigned=false`, `structural_identity_authorized=false`, `canonical_write_authorized=false`.

No historical object count, object-number whitelist, or manual coordinates may enter production detection.

## Task D — Exact TAV.5 qualification and human review evidence

1. Run focused adapter/unit gate on exact head.
2. Run full Step 4 exact-raster qualification twice.
3. Run Step 5 review-package workflow on the same exact head.
4. Inspect the regenerated whole-sheet overview/contact sheets for the omission class previously witnessed by 19/22. These numbers are review witnesses only, never detection inputs.
5. If compatible recurring symbols remain visibly unboxed, outcome is `REWORK` even when CI is green.
6. If recall is visibly adequate, keep all candidates `UNREVIEWED_GEOMETRIC_REGION` until explicit human decisions.

## Completion boundary

The implementation is technically complete only when the final exact SHA has:
- focused reuse/adapter gate PASS;
- complete Step 4 qualification PASS with deterministic replay;
- Step 5 package generation PASS;
- no duplicate local similarity/family subsystem;
- review evidence sufficient for a human recall judgment.

No merge or promotion is authorized by this plan.
