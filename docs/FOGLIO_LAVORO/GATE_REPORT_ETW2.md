# ETW-2 GATE REPORT — Floor Differential Reconstruction

**Gate:** ETW-2  
**Status:** IN PROGRESS — G3↔G4 DIFFERENTIAL SCAN ACTIVE  
**Parent gate:** ETW-1 = PASS  
**Branch:** `feat/structural-professional-workspace-r1`

## Objective

Resolve the former M0-S1B floor-difference block by applying the validated ETW-1 high-resolution document pipeline to:

- G1 → TAV-02S
- G2 → TAV-03S
- G3 → TAV-04S
- G4 → TAV-05S

No typical-floor equivalence is assumed.

## Task 1 — Four DocumentMaps

Repository-native execution completed successfully.

GitHub Actions run `32269573791` (`ETW2 Floor Differential`) completed with all steps PASS. Artifact `9371761458` contains:
- TAV-02S: 2 regions / 28 tiles;
- TAV-03S: 2 regions / 28 tiles;
- TAV-04S: 2 regions / 35 tiles;
- TAV-05S: 2 regions / 28 tiles;
- `floor_registration.json`;
- `execution_summary.json`.

The pipeline was subsequently optimized so Task 1–2 generate metadata only; high-resolution raster rendering is deferred to Task 3 evidence regions. The optimized workflow also completed successfully.

**Status: PASS.**

## Task 2 — Cross-floor registration

Page-normalized coordinates alone were rejected as insufficient because TAV-04S and TAV-05S differ in sheet width and plan placement.

Controlled raster registration:
- method: SIFT + ratio test + RANSAC homography;
- source: G3 / TAV-04S;
- target: G4 / TAV-05S;
- fit resolution: 100 DPI;
- evidence resolution: 300 DPI;
- good matches: 832;
- inliers: 394;
- inlier ratio: 0.4736;
- inlier RMSE: 1.50 px at 100 DPI.

Registration remains `INF_CONTROLLED_REGISTRATION`: it is a comparison aid, never structural evidence by itself.

A raster-difference candidate queue was added in commit `7a262b09e0ff503f2dfab9200dfb3d776d8110b9`. GitHub Actions run `32271392783` completed successfully and produced `difference_candidates.json` with 60 review candidates. Every candidate is `REVIEW_REQUIRED` and `promotion_allowed=false`.

**Status: PASS as comparison registration / no identity promotion.**

## Task 3 — G4 ↔ G3 evidence sweep

Target pair:

`G4 / TAV-05S ↔ G3 / TAV-04S`

### Confirmed differential findings

Recorded in `ETW2_FLOOR_DIFFERENCE_MATRIX_v1.csv`.

1. `ETW2-DIFF-001` — `BEAM_02`: G3 **140 cm** → G4 **120 cm** — `SECTION_CHANGE`.
2. `ETW2-DIFF-002` — `BEAM_03`: G3 **140 cm** → G4 **120 cm** — `SECTION_CHANGE`.
3. `ETW2-DIFF-003` — candidate `CAND-536`: third homologous wide beam, G3 **140 cm** → G4 **120 cm** — `SECTION_CHANGE`.
4. `ETW2-DIFF-004` — candidate `CAND-420`: upper perimeter configuration differs — G3 has an orthogonal beam return plus projecting polygonal perimeter; G4 has a straight 25×70 perimeter beam and no corresponding projection — `GEOMETRY_CHANGE`.
5. `ETW2-DIFF-005` — candidate `CAND-556`: right-side mid-level outward beam/perimeter extension with visible 150 dimension in G3, absent in G4 — `GEOMETRY_CHANGE`.
6. `ETW2-DIFF-006` — candidate `CAND-781`: distinct lower right-side outward beam extension plus polygonal perimeter in G3, absent in G4 — `GEOMETRY_CHANGE`.

All source readings are `DOC_RASTER`; cross-level correspondence is `VER_PARZIALE`; affected persistent structural IDs remain `CANDIDATE` until bound to the canonical model.

### Candidate-review control

`ETW2_G3_G4_CANDIDATE_REVIEW_v1.csv` records both positive and negative reviews.

Reviewed false positives include:
- `CAND-551`: same 25×70 edge-beam configuration on both sheets → `MATCH_FALSE_POSITIVE`;
- `CAND-738`: same central member geometry and 50×20 annotation → `MATCH_FALSE_POSITIVE`.

This confirms that the raster difference is functioning as a locator rather than an automatic classifier.

**Status: PASS for multiple end-to-end G3↔G4 differences; full-sheet sweep still open.**

## Task 4 — Floor Difference Matrix

Matrix now contains 6 confirmed G3↔G4 difference rows:
- 3 `SECTION_CHANGE`;
- 3 `GEOMETRY_CHANGE`.

The candidate-review log is maintained separately so rejected raster differences remain traceable.

**Status: OPEN / PARTIAL.**

## Current residuals

| ID | Scope | Status | Blocking |
|---|---|---|---|
| ETW2-R01 | Four DocumentMaps | RESOLVED | — |
| ETW2-R02 | G3↔G4 raster registration | RESOLVED for comparison | — |
| ETW2-R03 | First G4/G3 difference | RESOLVED | — |
| ETW2-R04 | Complete Floor Difference Matrix G1–G4 | OPEN | floor signatures / TypicalFloorGroup |
| ETW2-R05..R10 | Bind confirmed G3↔G4 difference candidates to persistent structural IDs | OPEN | identity-level promotion only |
| ETW2-R11 | Complete review of remaining G3↔G4 raster candidates | OPEN | full G3↔G4 differential coverage |

## Gate status

**ETW-2 remains IN PROGRESS because the full G1–G4 Floor Difference Matrix is not complete.**

The former M0-S1B tooling block is removed. The current workflow now separates:

`raster candidate → human/visual review → DOC_RASTER property reading → VER_PARZIALE cross-floor correspondence → later persistent-ID binding`.

This prevents both OCR loss and automatic promotion from image similarity.
