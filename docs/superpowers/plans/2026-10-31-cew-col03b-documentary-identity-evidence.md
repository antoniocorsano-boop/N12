# CEW COL-03B Documentary Identity Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, provenance-complete evidence layer for documentary identity across exactly the 22 qualified `COL-OCC-*` occurrences, without promoting any support, structural or canonical identity.

**Architecture:** Add successor package `experiments/cew_col03b`. It consumes the qualified COL-03A ledger as the immutable subject set, derives reproducible local source regions, classifies text/callout/local-topology observations into separate evidence channels, reconciles inventoried historical artifacts as independent candidate evidence, builds non-authoritative hypotheses, and closes only evidence collection. Identity resolution remains a later gate.

**Tech Stack:** Python 3.12.15, standard library JSON/hashlib/pathlib, existing CEW exact-source/PDF/OCR toolchain from COL-02, `unittest`, GitHub Actions. No new runtime dependency unless an already-frozen CEW lockfile provides it.

**Spec:** `docs/superpowers/specs/2026-10-31-cew-col03b-documentary-identity-evidence-design.md`

## Global Constraints

- Exact qualified predecessor is `0d4a43cf02eadd2ab6f4b2641888395586c08a98`.
- Input subject set is exactly 22 records: `COL-OCC-0001` … `COL-OCC-0022`.
- COL-03B must never add, delete, merge or renumber COL-03A occurrences.
- Exact TAV.5 source lineage remains immutable and must be replayed from the existing COL-03A/COL-02 chain.
- Evidence channels remain separate: internal text, intersecting text, nearby text, high-resolution local reading, callout, local topology, cross-document correspondence.
- OCR/raw reading is observation only. Raw and normalized/transcribed values must both be retained.
- Historical TAV.5/TAV.7/topology/27x5 assets are independent reconciliation evidence only; they never define the occurrence set and never become authority by fit.
- The historical 57-node universe must not be assumed complete.
- A hypothesis may be `MULTI_CHANNEL_SUPPORTED` only with at least two genuinely independent discriminants.
- `documentary_identity_evidence_collection_complete = true` may coexist with unresolved identities.
- `support_identity_authorized`, `family_assignment_authorized`, `section_assignment_authorized`, `fixed_line_assignment_authorized`, `structural_identity_authorized`, `canonical_geometry_authorized`, `canonical_write_authorized`, `g2c_promotion_authorized`, `g3_authorized`, `merge_authorized` remain false.
- No merge, deploy, G2C, G3 or EdiLus promotion is authorized by COL-03B.

## File Structure

- Create `experiments/cew_col03b/__init__.py` — package marker.
- Create `experiments/cew_col03b/predecessor.py` — validate/replay qualified COL-03A ledger, closure and authority boundary.
- Create `experiments/cew_col03b/local_evidence.py` — deterministic local regions, text relation classification, callout/local-topology evidence primitives.
- Create `experiments/cew_col03b/historical_correspondence.py` — provenance-checked adapters for inventoried historical artifacts and candidate correspondences.
- Create `experiments/cew_col03b/hypotheses.py` — evidence independence, contradiction handling and non-authoritative hypothesis states.
- Create `experiments/cew_col03b/exact_source.py` — end-to-end exact-source replay, artifact emission and deterministic double-build.
- Create `tests/cew_col03b/test_predecessor.py`.
- Create `tests/cew_col03b/test_local_evidence.py`.
- Create `tests/cew_col03b/test_historical_correspondence.py`.
- Create `tests/cew_col03b/test_hypotheses.py`.
- Create `tests/cew_col03b/test_exact_source_writer.py`.
- Create `.github/workflows/validate-cew-col03b-documentary-identity-evidence.yml`.
- Produce evidence only at runtime under `evidence/cew-col03b/`; do not commit generated evidence unless repository policy already requires it.

## Review Focus

- A dimension string close to two occurrences must remain `AMBIGUOUS_TEXT_BINDING`, never become a support number by nearest-distance alone. Pin in Task 2.
- Two evidence records derived from the same OCR token/region must count as one discriminant, not two. Pin in Task 4.
- A historical `N###` candidate must remain a candidate when coordinate transform/provenance is missing or multiple targets fit. Pin in Task 3.
- A callout is `DIRECT_GRAPHICAL_BINDING` only when connecting geometry is actually represented; otherwise it degrades to nearby/intersecting text. Pin in Task 2.
- COL-03B closure must succeed with explicitly unresolved occurrences but fail on omitted channels, lineage drift, source reconstruction failure or any authority promotion. Pin in Task 5.

---

### Task 1: Freeze the COL-03A predecessor and create evidence-bundle skeletons

**Files:**
- Create: `experiments/cew_col03b/__init__.py`
- Create: `experiments/cew_col03b/predecessor.py`
- Create: `tests/cew_col03b/test_predecessor.py`

**Interfaces:**
- Produce: `validate_col03a_predecessor(*, ledger: dict, reconciliation: dict, closure: dict, expected_sha: str) -> list[dict]`.
- Produce: `build_evidence_bundle_skeleton(occurrence: dict, *, col03a_ledger_digest: str) -> dict`.
- Bundle keys must include all seven evidence-channel arrays, `hypotheses`, collection/resolution/conflict states, `missing_channels`, exact-source/lineage flags and all authority booleans.

- [ ] **Step 1: Write failing tests** asserting exactly 22 contiguous IDs, complete predecessor closure, unchanged two human-equivalence collapses, complete exact-source lineage, and all downstream authority flags false.
- [ ] **Step 2: Run** `python -m unittest discover -s tests/cew_col03b -p 'test_*.py' -v`; expected causal FAIL because `experiments.cew_col03b` does not exist.
- [ ] **Step 3: Implement** predecessor validation and skeleton creation; every channel starts empty and listed in `missing_channels`; `documentary_identity_resolution_state = UNRESOLVED`.
- [ ] **Step 4: Re-run focused tests**; expected PASS.
- [ ] **Step 5: Commit** `feat: freeze COL-03A boundary for COL-03B`.

### Task 2: Deterministic local source evidence and channel classification

**Files:**
- Create: `experiments/cew_col03b/local_evidence.py`
- Create: `tests/cew_col03b/test_local_evidence.py`

**Interfaces:**
- Produce: `derive_local_region(occurrence: dict, *, margin_x: float, margin_y: float) -> dict`.
- Produce: `classify_text_relation(*, occurrence_bbox: dict, text_bbox: dict, local_region: dict) -> str` returning `INTERNAL`, `INTERSECTING`, `NEARBY`, or `OUTSIDE`.
- Produce: `build_text_evidence(...) -> dict` preserving raw text, normalized text, extraction method, geometry, distance/direction and provenance.
- Produce: `build_callout_evidence(...) -> dict` with explicit connector geometry or downgraded relation.
- Produce: `build_local_topology_signature(...) -> dict` containing only documentary/local relations, never canonical node/grid/fixed-line IDs.

- [ ] **Step 1: Write failing geometry/channel tests** for contained, intersecting, bounded-nearby and outside text; competing-neighbor ambiguity; connector-present versus connector-absent callouts; deterministic local region clipping at page boundaries.
- [ ] **Step 2: Run focused tests**; expected FAIL on missing APIs.
- [ ] **Step 3: Implement minimal deterministic geometry primitives** using normalized source coordinates only; no identity assignment.
- [ ] **Step 4: Verify GREEN** with `python -m unittest tests.cew_col03b.test_local_evidence -v`.
- [ ] **Step 5: Commit** `feat: classify COL-03B local documentary evidence`.

### Task 3: Provenance-checked historical correspondence

**Files:**
- Create: `experiments/cew_col03b/historical_correspondence.py`
- Create: `tests/cew_col03b/test_historical_correspondence.py`

**Interfaces:**
- Produce: `validate_historical_artifact_manifest(manifest: dict) -> dict`.
- Produce: `build_cross_document_candidate(*, occurrence_id: str, artifact_ref: dict, candidate_id: str, matching_discriminants: list[str], conflicting_discriminants: list[str], transform_ref: dict | None) -> dict`.
- Candidate status is one of `CANDIDATE`, `SUPPORTED`, `CONTRADICTED`, `NOT_APPLICABLE`.

- [ ] **Step 1: Write failing tests** requiring explicit artifact path/version/digest where available; missing transform/provenance cannot yield `SUPPORTED`; one-to-many/many-to-one match stays ambiguous; `N###` or 27x5 membership never sets support identity.
- [ ] **Step 2: Run focused tests**; expected FAIL.
- [ ] **Step 3: Implement adapters** for the inventoried historical surfaces while keeping their raw identifiers namespaced to the historical artifact.
- [ ] **Step 4: Verify GREEN**.
- [ ] **Step 5: Commit** `feat: add governed historical correspondence evidence`.

### Task 4: Non-authoritative identity hypotheses and independent-discriminant rules

**Files:**
- Create: `experiments/cew_col03b/hypotheses.py`
- Create: `tests/cew_col03b/test_hypotheses.py`

**Interfaces:**
- Produce: `evidence_independence_key(evidence: dict) -> tuple`.
- Produce: `build_identity_hypothesis(*, occurrence_id: str, hypothesis_kind: str, candidate_value: str, supporting: list[dict], contradicting: list[dict]) -> dict`.
- Allowed kinds: `DOCUMENTARY_LABEL_CANDIDATE`, `SUPPORT_NUMBER_CANDIDATE`, `CROSS_DOCUMENT_COUNTERPART_CANDIDATE`.
- States: `UNSUPPORTED`, `SINGLE_CHANNEL`, `MULTI_CHANNEL_SUPPORTED`, `AMBIGUOUS`, `CONTRADICTED`.

- [ ] **Step 1: Write failing independence tests** showing that duplicate OCR derivatives count once, callout + independent TAV.7 correspondence count twice, contradiction overrides multi-channel maturity, and all hypotheses keep `promotion_authorized = false`.
- [ ] **Step 2: Run focused tests**; expected FAIL.
- [ ] **Step 3: Implement deterministic hypothesis classification** without numerical confidence score.
- [ ] **Step 4: Verify GREEN**.
- [ ] **Step 5: Commit** `feat: classify documentary identity hypotheses`.

### Task 5: Evidence collection reconciliation and closure

**Files:**
- Create: `experiments/cew_col03b/exact_source.py`
- Create: `tests/cew_col03b/test_exact_source_writer.py`

**Interfaces:**
- Produce: `finalize_evidence_bundle(bundle: dict) -> dict`.
- Produce: `build_documentary_reconciliation(bundles: list[dict], *, historical_manifest: dict) -> dict`.
- Produce: `build_documentary_closure(*, bundles: list[dict], reconciliation: dict, predecessor_closure: dict, qualified_base_sha: str) -> dict`.
- Produce: `write_col03b_artifacts(output_dir: Path, ...) -> dict[str, str]` returning SHA-256 digests.

- [ ] **Step 1: Write failing closure tests**: every required channel must be populated or explicitly `NO_EVIDENCE`/`NOT_APPLICABLE`; unresolved identity is allowed; omitted channel, lineage drift, source reconstruction failure, historical-provenance failure or any authority=true blocks closure.
- [ ] **Step 2: Run focused tests**; expected FAIL.
- [ ] **Step 3: Implement reconciliation/closure and deterministic JSON writing** for evidence ledger, hypothesis matrix, reconciliation, optional human-review packet and closure artifact.
- [ ] **Step 4: Verify deterministic double-build** produces byte-identical JSON/digests for shuffled input order.
- [ ] **Step 5: Commit** `feat: close COL-03B evidence collection fail closed`.

### Task 6: Exact-source orchestration, workflow and regression qualification

**Files:**
- Modify: `experiments/cew_col03b/exact_source.py`
- Create: `.github/workflows/validate-cew-col03b-documentary-identity-evidence.yml`
- Modify tests only if exact-source orchestration exposes a contract gap; no weakening assertions.

**Interfaces:**
- CLI: `python -m experiments.cew_col03b.exact_source`.
- Workflow jobs: `unit`, `exact-source`.

- [ ] **Step 1: Add workflow before production orchestration is complete** so the first branch run records the causal RED while COL-03A regression remains green.
- [ ] **Step 2: Exact-source job** checks out the candidate exact SHA, proves `0d4a43cf…` ancestry, replays COL-03A, then runs COL-03B.
- [ ] **Step 3: Implement source-local evidence orchestration** using the existing frozen CEW B01/COL-02 toolchain; do not introduce a new unfrozen OCR dependency.
- [ ] **Step 4: Assert terminal qualification**: 22/22 occurrence bundles; complete channel accounting; deterministic digests; no authority promotion; COL-03A regression PASS.
- [ ] **Step 5: Run all unit/regression/exact-source jobs** and retain the exact-SHA workflow evidence.
- [ ] **Step 6: Commit** `ci: qualify COL-03B documentary identity evidence`.

### Task 7: Human documentary review only for unresolved source interpretation

**Files:**
- Create only if required by actual exact-source ambiguity: `governance/cew-col03b/COL03B_DOCUMENTARY_EVIDENCE_HUMAN_REVIEW_v1.json`.
- Modify exact-source assertions only to consume the append-only receipt; do not change prior machine observations.

**Interfaces:**
- Human decisions may transcribe text, decide connector relation, documentary correspondence or ambiguity state only.
- Human decisions may not authorize support identity, family, section, fixed line, vertical chain, canonical node/geometry, G2C or G3.

- [ ] **Step 1: Generate a review packet only if deterministic replay leaves genuine documentary ambiguity.**
- [ ] **Step 2: If no review is needed, record `human_review_required = false` and do not fabricate a receipt.**
- [ ] **Step 3: If review is needed, consume the receipt append-only and rerun exact-source qualification.**
- [ ] **Step 4: Verify final exact SHA has unit + exact-source + repository memory gates PASS.**
- [ ] **Step 5: Keep PR Draft and unmerged; no deploy.**

## Self-Review Result

- Spec coverage: all design sections map to Tasks 1–7; identity promotion intentionally has no implementation task.
- Type consistency: all downstream tasks consume explicit dict/list contracts from earlier tasks; `COL-OCC-*` remains the sole occurrence namespace.
- Review focus: the five highest-risk failure modes are each pinned to a concrete task.
- Proportion: plan specifies interfaces, causal tests and gates without embedding production bodies.
- Integration boundary: successor remains stacked on qualified PR #176 head; merge/deploy remain prohibited.
