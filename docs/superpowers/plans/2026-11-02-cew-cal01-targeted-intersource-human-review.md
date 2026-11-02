# CEW-CAL-01 Targeted Inter-Source Human Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Materialize a bounded, deterministic and source-only professional review package for TAV.5 ↔ TAV-02S primary-homology decisions while keeping all registration and engineering authority closed.

**Architecture:** Add one focused module that selects an eight-occurrence TAV.5 review batch using only TAV.5 evidence/geometry, then materializes TAV.5 context crops, a normalized labelled TAV-02S lattice overview, a JSON manifest and static HTML board. Integrate the package into the existing exact-source external-chain workflow without generating homology proposals or correspondence receipts.

**Tech Stack:** Python 3.12.15, stdlib `json/hashlib/math/pathlib/html/argparse`, OpenCV from the existing frozen CAL-01 toolchain, `unittest`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-02-cew-cal01-targeted-intersource-human-review-design.md`

## Global Constraints

- Qualified predecessor exact SHA: `ebac21fc2cc49bff75e0cc7656ee30d219d44f14`.
- TAV.5 source SHA remains `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- TAV.5 governed raster SHA remains `474ed6c3958d8841b95b1ca9cdfb7702ec552204a30a4de6b646ec1e5f391406`.
- TAV-02S source SHA remains `cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f`.
- Current qualified TAV-02S lattice has 21 nodes in `LOCAL_RELATIVE_METRIC`; its origin is not an absolute surveyed/project origin.
- Target geometry must not participate in batch selection.
- No nearest-neighbour matching, automatic homology proposal, similarity/confidence score or target-node ranking.
- Historical comparator, historical affine, historical M0-G and historical CEW support geometry remain forbidden.
- No affine fit, structural identity, canonical geometry, M0-G, canonical write, merge or deploy authority.

## Review Focus

- **Hidden target leakage:** changing TAV-02S node coordinates/order must not change selected TAV.5 occurrence IDs; pin this in Task 1.
- **Frame drift:** TAV.5 crop coordinates must be checked against the governed TAV.5 raster dimensions; pin this in Task 2.
- **Normalization drift:** TAV-02S overview must use the explicit discovery transform and reject unsupported/missing transform metadata; pin this in Task 2.
- **Implicit suggestion in UI:** manifest/HTML must contain no nearest/suggested target or similarity/confidence fields; pin this in Tasks 1–2.
- **Authority escalation:** targeted review assets must not alter governed-correspondence/split state or any authority flag; pin this in Task 3.

---

### Task 1: Deterministic source-only batch selection and review manifest

**Files:**
- Create: `tests/cew_cal01/test_intersource_human_review.py`
- Create: `experiments/cew_cal01/intersource_human_review.py`

**Interfaces:**
- Consumes: `CEW_CAL01_INTERSOURCE_CORRESPONDENCE_CANDIDATES_v1`.
- Produces:
  - `select_targeted_review_batch(candidates: dict, batch_size: int = 8) -> list[str]`
  - `build_targeted_review_manifest(candidates: dict, selected_occurrence_ids: list[str], source_assets: dict[str, dict], target_overview: dict) -> dict`

- [ ] **Step 1: Write failing selection/manifest tests**

Tests must assert:
- exact eight-ID selection for a fixture mirroring the qualified 22 TAV.5 centers/evidence counts;
- candidate input order does not change selection;
- modifying/reordering target lattice-node coordinates does not change selection;
- invalid batch sizes fail closed;
- manifest declares `SOURCE_ONLY_FARTHEST_POINT_COVERAGE_V1`, `target_geometry_used_for_selection=false`, `target_node_ranking_performed=false`, `automatic_homology_proposed=false`;
- manifest has no nearest/suggested/similarity/confidence fields and authority remains closed.

- [ ] **Step 2: Run the focused/full CAL-01 suite and verify RED**

Run: `python -m unittest discover -s tests/cew_cal01 -p 'test_*.py' -v`
Expected: FAIL because `experiments.cew_cal01.intersource_human_review` does not exist.

- [ ] **Step 3: Implement selection and manifest minimally**

Use normalized TAV.5 center coordinates, unique source-evidence count, farthest-point coverage and deterministic tie-breaking exactly as specified. Do not read target-node positions in `select_targeted_review_batch`.

- [ ] **Step 4: Run the full CAL-01 suite and verify GREEN**

Expected: all CAL-01 contract tests PASS.

- [ ] **Step 5: Commit**

Commit message: `feat(cew-cal01): select targeted intersource review batch`.

### Task 2: Exact-source visual assets and static review board

**Files:**
- Modify: `experiments/cew_cal01/intersource_human_review.py`
- Extend: `tests/cew_cal01/test_intersource_human_review.py`

**Interfaces:**
- Produces:
  - `materialize_targeted_review_package(...) -> dict`
  - CLI `python -m experiments.cew_cal01.intersource_human_review ...`
- Output directory contains:
  - `targeted-intersource-human-review.json`
  - `targeted-intersource-human-review.html`
  - `tav5-<occurrence-id>-context.png` for selected rows
  - `tav02-lattice-overview.png`

- [ ] **Step 1: Add failing pure contract tests**

Assert deterministic asset metadata validation, exact source/raster/lattice bindings and HTML text generation without implicit suggestions. Keep OpenCV imports inside runtime materialization so the stdlib contract job remains import-safe.

- [ ] **Step 2: Verify RED**

Run the focused test module; expected failures are missing materialization/board interfaces.

- [ ] **Step 3: Implement materialization minimally**

At runtime import OpenCV, validate TAV.5 raster dimensions, normalize TAV-02S with the explicit discovery transform, create eight clamped source crops, draw neutral candidate crosshairs, draw all 21 target lattice nodes/labels without preference, SHA-256 every generated asset, write manifest and static HTML.

- [ ] **Step 4: Run pure tests GREEN**

Run full CAL-01 contract suite and require PASS.

- [ ] **Step 5: Commit**

Commit message: `feat(cew-cal01): materialize targeted human review assets`.

### Task 3: Exact-source workflow integration

**Files:**
- Modify: `.github/workflows/validate-cew-cal01-external-chain.yml`
- Create: `tests/cew_cal01/test_targeted_intersource_review_workflow.py`

**Interfaces:**
- Consumes: exact candidate JSON, governed TAV.5 raster, frozen TAV-02S raster/discovery.
- Produces: targeted review package under `$RUNNER_TEMP/cew-cal01-external-chain/intersource/targeted-human-review/` and includes it in the existing artifact.

- [ ] **Step 1: Write failing workflow-contract tests**

Require a CLI materialization step after the fail-closed inter-source state and assertions for:
- 22 source candidates, 21 target nodes, batch size 8;
- expected selected IDs on exact source;
- source-only selection flags;
- normalized TAV-02S overview and eight TAV.5 crop assets exist with SHA-256 digests;
- governed correspondences remain 0;
- split remains `INSUFFICIENT_INTERSOURCE_CORRESPONDENCES` and no affine fit occurs;
- all authority remains closed.

- [ ] **Step 2: Run suite and verify RED**

Expected: workflow-contract failures because the materialization step/assertions are absent.

- [ ] **Step 3: Integrate workflow and exact assertions**

Add the new module/test paths to workflow triggers, invoke the CLI with batch size 8, and assert the package without changing the existing governed-correspondence or split inputs.

- [ ] **Step 4: Push exact candidate and require three fresh qualification workflows**

Require on the same SHA:
- CEW-CAL-01 Primary Metric Calibration — PASS;
- CEW-CAL-01 External Dimension Chains — PASS;
- CEW Repository Memory Gate — PASS.

- [ ] **Step 5: Inspect uploaded artifact directly**

Verify the JSON/HTML/assets and their digests, selected IDs, 21-node target overview, zero governed pairs and closed authority.

- [ ] **Step 6: Commit**

Commit message: `ci(cew-cal01): qualify targeted intersource human review`.

### Task 4: Durable governance checkpoint

**Files:**
- Modify: `governance/cew-cal01/CEW_CAL01_EXTERNAL_CHAIN_EXECUTION_LEDGER.md`
- Update PR #187 commentary after qualification.

**Interfaces:**
- Consumes: exact qualified SHA, workflow run IDs, artifact ID/digest and targeted review-package digest.
- Produces: durable checkpoint with the eight selected occurrence IDs and the next human action.

- [ ] **Step 1: Record only fresh qualified evidence**

Ledger must state that the system prepared review evidence only and generated no human decision, no homology proposal and no affine registration.

- [ ] **Step 2: Update PR #187 checkpoint**

Record exact SHA, three PASS runs, artifact/digest, package digest, selected IDs and authority closure; keep PR Draft/open/unmerged.

- [ ] **Step 3: Final verification**

Re-check PR state, exact workflow status and absence of merge/deploy.
