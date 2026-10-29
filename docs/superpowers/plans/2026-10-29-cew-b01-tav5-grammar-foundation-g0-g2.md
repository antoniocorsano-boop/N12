# CEW-B01 TAV.5 Grammar Foundation G0–G2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first grammar-first foundation for TAV.5: governed document zoning, a neutral graphic census, and a recurring-motif catalog/visual atlas without assigning structural identity.

**Architecture:** Preserve the exact B01 SourceVersion/Step-3 raster as authority, derive explicit zone masks, run neutral source-bound primitive extraction only inside `STRUCTURAL_WORKAREA`, then cluster recurring motifs using the existing #137 descriptor/clustering vocabulary. Human meaning remains downstream; G0–G2 produce inspectable evidence and explicit UNKNOWN residuals only.

**Tech Stack:** Python 3.12, existing `cew_b01` source/raster contracts, OpenCV 5.0.0.93 already locked by B01, NumPy, existing GitHub Actions exact-source pattern, bounded reuse/adaptation from PR #137.

**Spec:** `docs/superpowers/specs/2026-10-29-cew-b01-tav5-grammar-first-design.md`

## Global Constraints

- SourceVersion and governed Step-3 raster remain immutable evidentiary authority.
- Every derived geometry must map to the source page coordinate frame.
- G0–G2 assign no structural identity, canonical geometry, family membership, BIM/FEM/NTC authority or canonical write.
- `RECTANGLE_DOES_NOT_IMPLY_COLUMN`; topology/relations are downstream of G0–G2.
- Historical object numbers, counts and hand-entered object coordinates are forbidden as production detection inputs.
- Title-block exclusion is a document-function mask, not deletion of source evidence.
- Reuse #137 neutral primitive/clustering concepts; do not create a second generic clustering or prototype-memory subsystem.
- Existing V2 and closed-frame/internal-mark detectors remain regression evidence only and are not modified by this plan.
- G1 must not run on regions classified outside `STRUCTURAL_WORKAREA`.
- Recurring unclassified graphics remain explicit `UNKNOWN`; absence of a label is never interpreted as non-structural.

## Review Focus

1. A title block touching/overlapping the structural drawing boundary must not silently erase structural ink; zone overlaps fail closed and require review.
2. Multiple structural workareas on one sheet must be representable without collapsing to one rectangle.
3. Broken/scanned linework must remain neutral primitives/UNKNOWN rather than being dropped because it is not a perfect closed shape.
4. Text and dimension graphics inside the workarea must be inventoried but must not create structural semantics.
5. A recurring motif that does not match an existing descriptor family must appear in the atlas as `UNKNOWN`, not disappear from coverage.

---

## Repository Memory / Reuse Assessment

Reuse decisions are fixed by `docs/repo-memory/CEW_B01_RECONCILIATION_MATRIX_v1.md`:

- exact source/provenance chain → **REUSE** current B01 Steps 1–3;
- neutral primitive/descriptor/clustering foundation → **ADAPT/PORT bounded** from PR #137 `320755e66a7263f1842f73dc14fb9a0ea8ccd7f8`;
- engineering interpretation rules → **REFERENCE/PORT later**, not executed in G0–G2;
- OA-3 similarity/prototype learning → **REUSE later**, not required to discover the initial neutral motif inventory;
- V2 + closed-frame/internal-mark proposal channels → **DEFER TO G8**.

No new generic similarity, semantic grammar or family-learning engine is authorized by this plan.

---

### Task 1: Add grammar-foundation source-bound schema

**Files:**
- Create: `cew_b01/grammar_schema.py`
- Create: `tests/cew_b01/test_grammar_schema.py`

**Interfaces:**
- Consumes: existing `SourceIdentity`, page index and `RASTER_PIXEL` coordinate conventions from `cew_b01/evidence_schema.py`.
- Produces:
  - `DocumentRegionKind`
  - `DocumentRegionMask`
  - `PrimitiveFamily`
  - `GraphicPrimitiveObservation`
  - `MotifClassificationState`
  - `RecurringMotif`
  - deterministic `to_mapping()` payloads and stable IDs/digests.

- [ ] **Step 1: Write failing schema tests**

Tests must assert:
- `DocumentRegionKind` includes `STRUCTURAL_WORKAREA`, `TITLE_BLOCK`, `LOCATION_DIAGRAM`, `APPROVAL_STAMP_SIGNATURE`, `NOTE_OR_LEGEND_REGION`, `MARGIN_VOID`, `SCAN_ARTIFACT`, `UNKNOWN_DOCUMENT_REGION`;
- zero/negative/out-of-frame rectangles are rejected;
- every record requires source SHA, page index and typed coordinate frame;
- `GraphicPrimitiveObservation.semantic_meaning is None` and `structural_identity_authorized is False`;
- `RecurringMotif` defaults to `UNCLASSIFIED` and cannot claim canonical authority;
- stable IDs repeat for identical payloads and change when source geometry changes.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.cew_b01.test_grammar_schema -v`  
Expected: FAIL because `cew_b01.grammar_schema` does not exist.

- [ ] **Step 3: Implement the minimal immutable schema**

Use frozen dataclasses/enums and canonical JSON hashing consistent with current B01 evidence records. Do not add semantic object types.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `python -m unittest tests.cew_b01.test_grammar_schema -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat(b01): add source-bound grammar foundation schema"`

---

### Task 2: G0 document-zone proposal and fail-closed mask application

**Files:**
- Create: `cew_b01/document_zoning.py`
- Create: `tests/cew_b01/test_document_zoning.py`
- Create: `governance/cew-b01/TAV5_DOCUMENT_ZONE_POLICY_v1.json`

**Interfaces:**
- Consumes: `Task3RasterBinding`, exact Step-3 PNG, `DocumentRegionMask`.
- Produces:
  - `propose_document_zones(binding: Task3RasterBinding, raster_path: Path) -> tuple[DocumentRegionMask, ...]`
  - `validate_zone_partition(binding: Task3RasterBinding, zones: Sequence[DocumentRegionMask]) -> None`
  - `apply_structural_workarea_mask(image: np.ndarray, zones: Sequence[DocumentRegionMask]) -> np.ndarray`
- Policy declares proposal-only zoning, human confirmation requirement for exclusion zones on the pilot, and no structural authority.

- [ ] **Step 1: Write failing zoning tests**

Tests cover:
- deterministic proposals from the same raster;
- title-block/notes masks cannot authorize structural identity;
- overlapping exclusion and `STRUCTURAL_WORKAREA` geometry raises `ZONE_PARTITION_REVIEW_REQUIRED` unless overlap is explicitly represented/resolved;
- two disjoint structural workareas remain two regions;
- applying the mask zeroes only confirmed exclusion pixels and preserves exact image size/frame;
- unconfirmed `TITLE_BLOCK` proposal cannot be used to suppress pixels in production G1 input.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.cew_b01.test_document_zoning -v`  
Expected: FAIL because zoning module/policy are absent.

- [ ] **Step 3: Implement deterministic document-function proposals**

Implement a bounded G0 proposer using source-local image statistics and orthogonal/grid/text-density features only. It may propose `TITLE_BLOCK`/other document regions, but exact TAV.5 suppression remains blocked until a human-confirmed zone receipt exists. No object detector output may be used as a zoning oracle.

- [ ] **Step 4: Verify synthetic zoning GREEN**

Run: `python -m unittest tests.cew_b01.test_document_zoning -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

`git commit -m "feat(b01): add governed document zoning foundation"`

---

### Task 3: Exact-TAV.5 G0 review artifact and confirmation boundary

**Files:**
- Create: `cew_b01/zone_review_package.py`
- Create: `tests/cew_b01/test_zone_review_package.py`
- Create: `.github/workflows/validate-cew-b01-grammar-g0.yml`

**Interfaces:**
- Consumes: exact B01 source contract, Step-3 raster, G0 proposed zones.
- Produces workflow artifact containing:
  - full source overview with zone overlays;
  - proposed-zone JSON;
  - per-zone crops;
  - source/raster SHA and transform metadata;
  - `review_state=PENDING_HUMAN_ZONE_REVIEW` unless a governed confirmation receipt is supplied.

- [ ] **Step 1: Write failing review-package tests**

Assert the package cannot claim `G0_PASS` without a confirmation receipt and cannot omit source/raster identities.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python -m unittest tests.cew_b01.test_zone_review_package -v`.

- [ ] **Step 3: Implement the minimal package generator and workflow**

Follow the existing Step-4/Step-5 exact-source checkout/materialization pattern. Do not commit generated raster evidence to the repository.

- [ ] **Step 4: Run exact-TAV.5 workflow**

Expected: engineering generation PASS, review state `PENDING_HUMAN_ZONE_REVIEW` until the proposed `TITLE_BLOCK` and `STRUCTURAL_WORKAREA` are explicitly confirmed.

- [ ] **Step 5: Record the human zone decision**

Persist a small governed receipt bound to exact source SHA, page, zone geometry digest and reviewer decision. The receipt grants document-region classification only.

- [ ] **Step 6: Re-run exact-TAV.5 workflow**

Expected: `G0_DOCUMENT_ZONING_PASS`; artifact proves structural workarea masking while retaining the full source overview.

- [ ] **Step 7: Commit**

`git commit -m "feat(b01): qualify TAV5 document zoning"`

---

### Task 4: G1 neutral raster primitive census

**Files:**
- Create: `cew_b01/primitive_census.py`
- Create: `tests/cew_b01/test_primitive_census.py`
- Create: `.github/workflows/validate-cew-b01-grammar-g1.yml`

**Interfaces:**
- Consumes: confirmed `STRUCTURAL_WORKAREA` mask + exact Step-3 raster.
- Produces:
  - `extract_neutral_primitives(binding, raster_path, zones) -> tuple[GraphicPrimitiveObservation, ...]`
  - primitive families from the spec only;
  - census JSON with counts by family and explicit unknowns;
  - coverage raster/overlay showing which structural-workarea ink is accounted for.

- [ ] **Step 1: Write failing primitive-census tests**

Synthetic fixtures must cover line segments, parallel pairs, intersections/T-junctions, closed/open rectilinear forms, L/T/cross motifs, text-like connected groups, hatch/fill, complex groups and unknowns. Assert that no output carries structural meaning.

- [ ] **Step 2: Add review-focus tests**

Pin behavior for broken rectangles, scan gaps, text/dimension marks and out-of-workarea graphics. Out-of-workarea content must never enter the G1 census.

- [ ] **Step 3: Run tests and verify RED**

Run: `python -m unittest tests.cew_b01.test_primitive_census -v`.

- [ ] **Step 4: Implement bounded raster primitive extraction**

Reuse the #137 primitive-family vocabulary and feature-signature semantics where compatible. Add TAV.5 raster-specific observation types only when the existing neutral vocabulary cannot represent them. Do not port semantic labels.

- [ ] **Step 5: Run unit tests and exact-source G1 workflow**

Expected: deterministic replay; source-bound primitive records; explicit `UNKNOWN_GRAPHIC_GROUP` residuals; no title-block primitives in G1.

- [ ] **Step 6: Commit**

`git commit -m "feat(b01): inventory neutral TAV5 graphic primitives"`

---

### Task 5: G2 recurring motif catalog using reused neutral descriptors

**Files:**
- Create: `cew_b01/motif_catalog.py`
- Create: `tests/cew_b01/test_motif_catalog.py`
- Create: `.github/workflows/validate-cew-b01-grammar-g2.yml`

**Interfaces:**
- Consumes: G1 `GraphicPrimitiveObservation` records.
- Produces:
  - `build_recurring_motif_catalog(primitives) -> tuple[RecurringMotif, ...]`
  - deterministic neutral cluster IDs;
  - member primitive IDs/source locators;
  - occurrence counts;
  - representative-member selection;
  - explicit `UNCLASSIFIED`/`UNKNOWN_EXCEPTION` state without automatic semantics.

- [ ] **Step 1: Write failing clustering/catalog tests**

Use translated/scaled neutral motifs and unrelated graphics. Assert recurring compatible motifs group deterministically; unrelated motifs remain separate; cluster membership never creates structural meaning.

- [ ] **Step 2: Add UNKNOWN preservation test**

A recurring feature signature not covered by a named family must still create a visible recurring catalog entry with `UNCLASSIFIED`/UNKNOWN state.

- [ ] **Step 3: Run tests and verify RED**

Run: `python -m unittest tests.cew_b01.test_motif_catalog -v`.

- [ ] **Step 4: Implement the smallest adapter over #137 clustering semantics**

Do not implement prototype memory, semantic classification or a new similarity engine. G2 grouping is neutral recurrence discovery only.

- [ ] **Step 5: Run tests and exact-source G2 workflow**

Expected: deterministic catalog and replay digest; all members remain source-bound and nonsemantic.

- [ ] **Step 6: Commit**

`git commit -m "feat(b01): catalog recurring TAV5 graphic motifs"`

---

### Task 6: Build the TAV.5 motif visual atlas and G0–G2 coverage gate

**Files:**
- Create: `cew_b01/grammar_review_package.py`
- Create: `tests/cew_b01/test_grammar_review_package.py`
- Create: `.github/workflows/validate-cew-b01-grammar-foundation.yml`

**Interfaces:**
- Consumes: confirmed zone map, G1 census, G2 catalog, exact Step-3 raster.
- Produces review artifact:
  - full-page zone overview;
  - structural-workarea coverage overlay;
  - one section per motif cluster with representative crops and occurrence count;
  - explicit UNKNOWN/unaccounted summary;
  - source/raster/census/catalog digests;
  - `G0_G2_ENGINEERING_PASS` only when deterministic contracts pass;
  - `PENDING_HUMAN_MOTIF_REVIEW` until a human reviews whether the catalog is sufficiently representative.

- [ ] **Step 1: Write failing package tests**

Assert title-block content is absent from motif examples, UNKNOWN clusters are always rendered, and unaccounted structural-workarea ink cannot be silently omitted from the summary.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python -m unittest tests.cew_b01.test_grammar_review_package -v`.

- [ ] **Step 3: Implement package and foundation workflow**

Reuse existing B01 review-package layout helpers where practical; keep the new artifact focused on grammar coverage rather than object recall.

- [ ] **Step 4: Run all G0–G2 tests plus existing B01 regression suite**

Run the grammar-foundation workflow on the exact candidate head. Existing V2/Step-4/Step-5 gates must remain green; no specialist detector output is allowed to affect G0–G2 results.

- [ ] **Step 5: Human motif-catalog review**

Review the atlas by family/group. Decisions are limited to `FUNCTIONALLY_CLASSIFIED`, `NON_STRUCTURAL`, `ARTIFACT`, `UNKNOWN_EXCEPTION` or remain `UNCLASSIFIED`; structural identity is still unauthorized.

- [ ] **Step 6: Freeze G0–G2 checkpoint**

Record exact head, zone-map digest, primitive-census digest, motif-catalog digest and review receipt. Do not start G3 until this checkpoint is accepted.

- [ ] **Step 7: Commit**

`git commit -m "feat(b01): add TAV5 grammar foundation review gate"`

---

## Completion Boundary

G0–G2 are complete only when:

- exact TAV.5 zone map is human-confirmed and source-bound;
- structural extraction demonstrably excludes the title block without altering SourceVersion;
- neutral primitive census is deterministic and explicit about UNKNOWN/unaccounted ink;
- recurring motif catalog is deterministic and preserves source locators;
- visual atlas exposes every recurring motif family and UNKNOWN residual;
- existing CEW-B01 regression gates remain green;
- no object-specific detector tuning was used to make G0–G2 pass;
- no structural/canonical authority has been granted.

After this checkpoint, design G3/G4 from the observed motif inventory rather than from assumptions made before the census.
