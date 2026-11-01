# CEW-CAL-01 Internal Dimension-Chain Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Discover source-bound planimetric dimension-chain candidates inside the qualified TAV.5 structural-plan envelope after the external-perimeter search returned zero candidates.

**Architecture:** A new `internal_dimension.py` stage consumes the exact raster plus the qualified perimeter result, restricts OCR to the source-frame structural envelope, clusters alternate numeric readings by location, and reuses the existing semantic line/tick/closed-frame grammar. Only `LINEAR_DIMENSION` locations become human-review candidates; all engineering authority stays closed.

**Tech Stack:** Python 3.12, OpenCV, NumPy, Tesseract 5.x, unittest, existing CEW-CAL-01 semantic-role modules.

**Spec:** `docs/superpowers/specs/2026-11-01-cew-cal01-internal-dimension-chain-design.md`

## Global Constraints

- Exact source SHA-256: `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Internal discovery requires qualified perimeter status `PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED` and `candidate_count == 0`.
- Historical M0-G, historical affine, historical `S-*`, and TAV02 inputs remain forbidden.
- OCR alone never creates a metric relation.
- Only semantic role `LINEAR_DIMENSION` becomes an internal candidate.
- Human `PRIMARY_VISUAL_VALIDATED` review remains mandatory.
- `primary_anchor_count` remains `0`.
- No merge or deploy is part of this plan.

## Review Focus

- A perimeter payload with candidates must fail closed/defer internal search rather than duplicate the hierarchy.
- OCR readings disagreeing at the same location must remain inspectable and must not be digit-repaired.
- A geometrically busy beam/column section must remain `SECTION_MEASURE` or `UNRESOLVED`, not become a planimetric candidate.
- Vertical and horizontal dimension text must preserve source orientation through OCR rotation/backprojection.
- Zero confirmed internal dimensions must be a valid closed result, not a reason to relax the grammar.

---

### Task 1: Internal search contract and hierarchy gate

**Files:**
- Create: `tests/cew_cal01/test_internal_dimension.py`
- Create: `experiments/cew_cal01/internal_dimension.py`

**Interfaces:**
- Produces: `select_internal_search_roi(perimeter_payload) -> list[int]`, `classify_internal_role_result(cluster, role_result) -> dict`.

- [ ] **Step 1: Write failing tests** proving the internal ROI is the perimeter stage's source-frame structural envelope, perimeter candidates defer the internal stage, only `LINEAR_DIMENSION` becomes `INTERNAL_LINEAR_DIMENSION_CANDIDATE`, and authority remains non-promoting.
- [ ] **Step 2: Run** `python -m unittest tests.cew_cal01.test_internal_dimension -v`; expected RED because the module/functions do not exist.
- [ ] **Step 3: Implement the minimal hierarchy/role functions.**
- [ ] **Step 4: Run focused and full CAL-01 contracts**; expected PASS.
- [ ] **Step 5: Commit** `feat(cal01): gate internal dimension search`.

### Task 2: Exact-source internal OCR and semantic replay

**Files:**
- Modify: `experiments/cew_cal01/internal_dimension.py`
- Modify: `tests/cew_cal01/test_internal_dimension.py`

**Interfaces:**
- Consumes: qualified exact raster, base discovery JSON, perimeter result JSON, existing `cluster_numeric_observations_by_location`, `select_ocr_consensus`, `collect_local_line_evidence`, `detect_nearby_closed_frame`, and `classify_numeric_graphic_role`.
- Produces: `build_internal_dimension_discovery(image_path, base_discovery_path, perimeter_discovery_path, output_dir) -> dict`.

- [ ] **Step 1: Add failing tests** for location clustering with conflicting readings, semantic rejection of section/unresolved roles, deterministic candidate output, and zero-authority invariants.
- [ ] **Step 2: Implement bounded OCR** on the source structural envelope using native 300 dpi, PSM 11, the three preprocessing modes, four rotations, numeric whitelist, and no line suppression.
- [ ] **Step 3: For each location cluster**, compute bounded OCR consensus, collect local line/tick evidence, detect closed-frame context, and apply the existing semantic role gate.
- [ ] **Step 4: Emit deterministic JSON and overlay** with source endpoints for confirmed linear dimensions, but no anchor promotion.
- [ ] **Step 5: Run focused and full CAL-01 tests**; expected PASS.
- [ ] **Step 6: Commit** `feat(cal01): discover internal dimension chains`.

### Task 3: Workflow qualification

**Files:**
- Modify: `.github/workflows/validate-cew-cal01.yml`
- Modify: `tests/cew_cal01/test_internal_dimension.py`

**Interfaces:**
- Consumes: Task 2 CLI/module and perimeter output.
- Produces: `internal/internal-dimension-discovery.json` and `internal/internal-dimension-search-overlay.png` in the governed CAL-01 artifact.

- [ ] **Step 1: Add RED workflow contract assertions** for the internal CLI invocation, exact source digest, perimeter hierarchy gate, zero `primary_anchor_count`, forbidden historical inputs, and closed authority.
- [ ] **Step 2: Integrate internal discovery immediately after perimeter discovery.**
- [ ] **Step 3: Update governed evidence assertions** without asserting that any candidate must exist.
- [ ] **Step 4: Run CI on the exact candidate and inspect the archived artifact.**
- [ ] **Step 5: Commit** `ci(cal01): qualify internal dimension discovery`.

### Task 4: Evidence assessment and human review

**Files:**
- Create or modify governed evidence under `governance/cew-cal01/` only after reading the exact artifact.

**Interfaces:**
- Consumes: qualified Task 3 artifact.
- Produces: factual candidate inventory and, when candidates exist, one-at-a-time exact-source human-review crops.

- [ ] **Step 1: Verify artifact source SHA, search ROI, role counts, candidate count, endpoints, and closed authority.**
- [ ] **Step 2: If candidates exist, order them deterministically and present only the first candidate for human review; if zero, record the closed result.**
- [ ] **Step 3: Do not promote any candidate without explicit human `PRIMARY_VISUAL_VALIDATED` evidence.**
