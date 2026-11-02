# CEW-CAL-01 Primary Anchor Connectivity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic TAV-02S local metric reference lattice from already-qualified human relations, then discover and qualify primary TAV-02S↔TAV.5 correspondences that can support TAV.5 local-metric anchor candidates without historical affine or M0-G input.

**Architecture:** The slice is deliberately two-stage. Stage A derives a relative metric lattice from TOP:R1 and RIGHT:R1 only, preserving exact relation provenance and no absolute-origin authority. Stage B discovers homologous primary points between TAV-02S and the governed TAV.5 raster, freezes a fit/holdout correspondence split, and only then permits local-metric TAV.5 anchor candidates. Any insufficiency stops fail-closed.

**Tech Stack:** Python 3.12, existing CEW-CAL-01 JSON contracts, qualified external-chain artifact, qualified TAV.5 structural candidate bridge, deterministic JSON artifacts, `unittest`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-02-cew-cal01-primary-anchor-connectivity-design.md`

## Global Constraints

- Baseline exact SHA before this plan: `ae00f9f565c683c75cf7249c9c0bf8a59838f4b2`.
- TAV-02S metric-network input must remain bound to source SHA `cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f` and its qualified network digest.
- TAV.5 source authority is the existing governed TAV.5 source/raster binding only.
- TAV-01S is out of scope except as an untouched regression input.
- Historical M0-G, historical affine coefficients, historical CEW `S-*` geometry and historical support identities are forbidden before primary registration freeze.
- No pending human-review interval may contribute a metric value.
- Local reference origin is a convention only: `absolute_origin_authorized=false`.
- No canonical geometry, structural identity, M0-G, canonical write, merge or deploy authority is introduced.

## Review Focus

- **False absolute authority:** a `[0,0]` local origin must never be represented as surveyed/project coordinates; Task 1 tests frame semantics and authority closure.
- **Circular inter-source registration:** historical affine/M0-G inputs must be rejected even if they improve correspondence residuals; Task 3 tests forbidden provenance.
- **Ambiguous homology:** automatic nearest-neighbour geometry cannot silently become a governed correspondence; Task 2 keeps proposals distinct from governed pairs.
- **Residual-biased holdout:** correspondence holdout must be frozen before fit and independent of residuals; Task 4 tests split invariance.
- **Mixed raster frames:** TAV.5 original raster and TAV-02S normalized raster coordinates must never be compared without explicit frame metadata; Tasks 1–3 test source/frame binding.

---

### Task 1: Materialize the TAV-02S local metric reference lattice

**Files:**
- Create: `experiments/cew_cal01/reference_lattice.py`
- Create: `tests/cew_cal01/test_reference_lattice.py`
- Modify: `.github/workflows/validate-cew-cal01-external-chain.yml`

**Interfaces:**
- Consumes: `metric-relation-network.json` for TAV-02S.
- Produces: `build_reference_lattice(network: dict) -> dict` with schema `CEW_CAL01_TAV02_REFERENCE_LATTICE_v1`.

- [ ] **Step 1: Write failing tests** requiring exactly seven ordered x references from TOP:R1, three ordered y references from RIGHT:R1, 21 Cartesian lattice nodes, cumulative local metric coordinates `[0, 4.70, 9.80, 13.95, 18.10, 23.40, 28.10]` on x and `[0, 2.10, 5.55]` on y, exact relation provenance, `coordinate_frame=LOCAL_RELATIVE_METRIC`, and all authority closed.
- [ ] **Step 2: Run the focused test** and verify RED because `reference_lattice` does not exist.
- [ ] **Step 3: Implement `build_reference_lattice`** using only validated TOP:R1 and RIGHT:R1 relation geometry/value fields; reject source/network drift, pending values, non-contiguous interval indices and conflicting shared endpoints.
- [ ] **Step 4: Add tests** proving LEFT/BOTTOM pending values are ignored, input order does not change the digest, and a missing TOP or RIGHT validated segment fails closed.
- [ ] **Step 5: Integrate exact-source materialization** into the existing external-chain workflow and assert the expected TAV-02S lattice counts while leaving TAV-01S unchanged.
- [ ] **Step 6: Run the full CAL-01 suite** and require PASS.
- [ ] **Step 7: Commit** `feat(cew-cal01): materialize TAV02 reference lattice`.

### Task 2: Build primary inter-source correspondence proposals

**Files:**
- Create: `experiments/cew_cal01/intersource_correspondence.py`
- Create: `tests/cew_cal01/test_intersource_correspondence.py`
- Output in workflow artifact: `tav5-tav02-correspondence-candidates.json`

**Interfaces:**
- Consumes: TAV-02S lattice, governed TAV.5 raster metadata, qualified 22-occurrence structural candidate bridge.
- Produces: `discover_correspondence_candidates(...) -> dict` containing proposals only, never governed correspondences.

- [ ] **Step 1: Write RED tests** that candidate centers are derived deterministically from TAV.5 `pixel_geometry`, exact raster SHA/frame is preserved, and no historical support ID or M0-G coordinate appears in proposals.
- [ ] **Step 2: Implement the minimal proposal builder** using source-bound TAV.5 candidate centers and TAV-02S lattice node descriptors; do not assign pairings solely by nearest distance.
- [ ] **Step 3: Add candidate classification** `UNMATCHED | AMBIGUOUS | HOMOLOGY_PROPOSAL` with explicit evidence refs and no fit eligibility.
- [ ] **Step 4: Verify that ambiguous or unsupported proposals remain non-governed** and cannot enter anchor inventory.
- [ ] **Step 5: Run focused and full suites** and require PASS.
- [ ] **Step 6: Commit** `feat(cew-cal01): propose primary intersource homologies`.

### Task 3: Govern exact TAV-02S↔TAV.5 correspondences

**Files:**
- Create: `experiments/cew_cal01/intersource_governance.py`
- Create: `tests/cew_cal01/test_intersource_governance.py`
- Create when evidence exists: `governance/cew-cal01/CEW_CAL01_INTERSOURCE_CORRESPONDENCE_RECEIPT_v1.json`

**Interfaces:**
- Consumes: correspondence proposals plus exact primary evidence or explicit human-professional correspondence decisions.
- Produces: governed point pairs with exact source/target bindings.

- [ ] **Step 1: Write RED tests** rejecting historical affine/M0-G provenance, duplicate conflicting partners, source/raster drift and unconfirmed automatic proposals.
- [ ] **Step 2: Implement validation contract** for governed correspondence rows: exact TAV.5 point, exact TAV-02S lattice node, evidence refs, validation state and closed authority.
- [ ] **Step 3: Reconcile any already-available source-native equivalences**; if fewer than four governed pairs exist, materialize `INSUFFICIENT_INTERSOURCE_CORRESPONDENCES` rather than fabricating pairs.
- [ ] **Step 4: If human confirmation is required, produce a deterministic review packet** with source/target context views but no suggested identity; do not create human receipts automatically.
- [ ] **Step 5: Run focused and full suites** and require PASS.
- [ ] **Step 6: Commit** `feat(cew-cal01): govern primary intersource correspondences`.

### Task 4: Freeze fit/holdout registration evidence and qualify readiness

**Files:**
- Create: `experiments/cew_cal01/intersource_split.py`
- Create: `tests/cew_cal01/test_intersource_split.py`
- Output: `tav5-tav02-registration-split.json`

**Interfaces:**
- Consumes: governed correspondences.
- Produces: deterministic registration/holdout IDs or fail-closed insufficiency state.

- [ ] **Step 1: Write RED tests** for >=4 total governed pairs, >=3 non-collinear fit pairs, >=1 holdout, non-overlap, spatial non-degeneracy and invariance to residual fields.
- [ ] **Step 2: Implement deterministic split** from frozen IDs/positions only.
- [ ] **Step 3: If current evidence is insufficient, return `INSUFFICIENT_INTERSOURCE_CORRESPONDENCES` with exact missing condition and stop before affine fitting.
- [ ] **Step 4: Run focused and full suites** and require PASS.
- [ ] **Step 5: Commit** `feat(cew-cal01): freeze primary intersource registration split`.

### Task 5: Integrate the anchor-connectivity gate and qualify exact source

**Files:**
- Modify: `.github/workflows/validate-cew-cal01.yml`
- Modify: `.github/workflows/validate-cew-cal01-external-chain.yml`
- Modify: `governance/cew-cal01/CEW_CAL01_EXTERNAL_CHAIN_EXECUTION_LEDGER.md`
- Modify: PR #187 body/commentary.

**Interfaces:**
- Consumes: Tasks 1–4 outputs.
- Produces: exact-SHA qualification evidence and one governed next action.

- [ ] **Step 1: Write/update workflow-contract tests** requiring exact checkout, no historical comparator before freeze, deterministic lattice digest, correspondence state and authority closure.
- [ ] **Step 2: Run workflows on one exact candidate SHA** and require Repository Memory Gate, External Dimension Chains and Primary Metric Calibration PASS on the same SHA.
- [ ] **Step 3: Inspect uploaded artifacts directly** and verify lattice counts/digest, correspondence count/state, split/readiness state and closed authority.
- [ ] **Step 4: Record one next action:** `BUILD_INTERSOURCE_AFFINE_REGISTRATION` only if the governed split is sufficient; otherwise `TARGETED_INTERSOURCE_HUMAN_REVIEW` or `INSUFFICIENT_INTERSOURCE_CORRESPONDENCES`.
- [ ] **Step 5: Record qualification in ledger and PR without merge/deploy.**
- [ ] **Step 6: Commit documentation-only checkpoint separately from the qualified implementation SHA.**
