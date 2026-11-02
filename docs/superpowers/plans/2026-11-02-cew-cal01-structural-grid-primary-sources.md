# CEW-CAL-01 Structural Grid Primary Sources Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Discover source-bound external structural-grid dimension candidates from TAV-01S and TAV-02S while keeping metric/canonical authority closed.

**Architecture:** Add a frozen multi-source registry and exact-source renderer, then a structural-grid perimeter discovery stage that reuses the existing CAL-01 graphic grammar without using TAV.5-specific source authority. Run the new stage in a separate CI job and publish a separate governed artifact so TAV.5 evidence remains independently reproducible.

**Tech Stack:** Python 3.12.15, pypdfium2, OpenCV, Tesseract 5.x, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-02-cew-cal01-structural-grid-primary-sources-design.md`

## Global Constraints

- Frozen source commit: `78c20a52db4f391ce0d13b9705b9f04737e218c9`.
- TAV-01S SHA-256: `abd6061c305f2e7222f04659f519d7ee73ed0759b815ac994ff66215f060fec8`.
- TAV-02S SHA-256: `cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f`.
- Render page 0 at 300 dpi from each original PDF.
- Machine-discovered candidates always require human validation and are not fit-eligible.
- `primary_anchor_count = 0` throughout this plan.
- No M0-G, historical affine, S-* annotation, architectural room dimension or canonical write may influence discovery.
- Zero candidates is a valid closed result.

## Review Focus

- Source file exists but digest differs: fail before raster/discovery.
- Portrait/landscape sheet orientation differs: normalize only for envelope detection and preserve source coordinates.
- Title block is larger/darker than the structural plan: structural envelope selection must reject it.
- Numeric OCR occurs without a two-reference dimension grammar: reject it, do not repair/infer.
- Same numeric value occurs on both sheets: cross-sheet summary must not infer semantic equivalence.

---

### Task 1: Frozen structural-grid source registry and exact-source raster

**Files:**
- Create: `experiments/cew_cal01/structural_grid_sources.py`
- Create: `tests/cew_cal01/test_structural_grid_sources.py`

**Interfaces:**
- Produces: `STRUCTURAL_GRID_SOURCES`, `validate_source_registry()`, `render_structural_grid_sources(source_repo: Path, output_dir: Path) -> dict`.
- Output manifest contains source id/path/SHA-256, raster path/dimensions/pixel digest, authority closed.

- [ ] **Step 1: Write failing tests** for exact two-source ordering, exact paths/hashes, duplicate rejection, digest drift rejection, and manifest authority closure.
- [ ] **Step 2: Run contract suite** and verify only the new structural-grid source tests fail because the module/functions do not exist.
- [ ] **Step 3: Implement minimal registry + renderer** using pypdfium2 page 0 at 300 dpi and SHA-256 verification before render.
- [ ] **Step 4: Run full CEW-CAL-01 contract suite** and require green.
- [ ] **Step 5: Commit** `feat(cal01): add frozen structural grid primary sources`.

### Task 2: Structural-grid perimeter dimension discovery

**Files:**
- Create: `experiments/cew_cal01/structural_grid_dimension.py`
- Create: `tests/cew_cal01/test_structural_grid_dimension.py`

**Interfaces:**
- Consumes: manifest from Task 1 and existing CAL-01 envelope/band/OCR/geometry helpers.
- Produces: `discover_structural_grid_dimensions(image_path: Path, source_record: dict, output_dir: Path) -> dict` and `build_cross_sheet_summary(discoveries: list[dict]) -> dict`.

- [ ] **Step 1: Write failing tests** proving: four perimeter bands, only two-reference geometry becomes a candidate, candidates remain non-fit-eligible, zero-candidate result is valid, cross-sheet equal values do not auto-match, and output digest is deterministic.
- [ ] **Step 2: Run contract suite** and verify causal RED from missing implementation.
- [ ] **Step 3: Implement minimal discovery** by reusing existing plan-envelope, perimeter-band, OCR preprocessing/orientation and local dimension-geometry functions; preserve source bboxes and source IDs.
- [ ] **Step 4: Add deterministic review overlay generation** with candidate/rejected locations but no semantic promotion.
- [ ] **Step 5: Run full CEW-CAL-01 contract suite** and require green.
- [ ] **Step 6: Commit** `feat(cal01): discover structural grid dimension chains`.

### Task 3: Exact-source CI qualification for TAV-01S and TAV-02S

**Files:**
- Modify: `.github/workflows/validate-cew-cal01.yml`
- Modify: `tests/cew_cal01/test_structural_grid_sources.py`
- Modify: `tests/cew_cal01/test_structural_grid_dimension.py`

**Interfaces:**
- Consumes: Task 1 renderer and Task 2 discovery.
- Produces: artifact `cew-cal01-structural-grid-primary-sources` containing both rasters, discoveries, overlays and cross-sheet summary.

- [ ] **Step 1: Add failing workflow contract tests** requiring the separate exact-source job, frozen commit fetch, both source IDs, final closed-authority assertions and artifact upload.
- [ ] **Step 2: Run contract suite** and verify only workflow contract assertions fail.
- [ ] **Step 3: Add CI job** after `cal01-contracts`: install frozen toolchain, fetch source commit, render/validate both sheets, discover perimeter candidates, build cross-sheet summary, assert source digests and `primary_anchor_count == 0`, upload artifact.
- [ ] **Step 4: Run full contract suite** and require green.
- [ ] **Step 5: Let GitHub Actions execute exact-source qualification** and inspect artifact counts/digests/overlays.
- [ ] **Step 6: Record governed result** under `governance/cew-cal01/` only after exact-source job result is known.
- [ ] **Step 7: Commit** `ci(cal01): qualify structural grid primary sources`.

### Task 4: Human-review handoff

**Files:**
- Create only after Task 3 artifact exists: `governance/cew-cal01/CEW_CAL01_STRUCTURAL_GRID_PRIMARY_SOURCE_RESULT_v1.json`

**Interfaces:**
- Consumes: exact-source artifact metadata and per-source candidate lists.
- Produces: governed checkpoint for one-component-at-a-time human review.

- [ ] **Step 1: Record exact candidate SHA, run IDs, artifact ID/digest, source digests, per-source counts and deterministic discovery digests.**
- [ ] **Step 2: Explicitly record `primary_anchor_count = 0` and `human_review_required = true`.**
- [ ] **Step 3: Prepare first review image from TAV-01S candidate with generous context directly from exact source raster.**
- [ ] **Step 4: Verify PR remains Draft/open/not merged and no deploy occurred.**
