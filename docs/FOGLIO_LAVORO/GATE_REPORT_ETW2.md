# ETW-2 GATE REPORT — Floor Differential Reconstruction

**Gate:** ETW-2  
**Status:** IN PROGRESS — G3↔G4 DIFFERENTIAL SCAN 50% REVIEWED  
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

### Review progress

- raster candidates generated: **60**;
- candidates explicitly reviewed: **30 / 60**;
- confirmed structural differences currently in matrix: **15**;
- ambiguous readings remain unpromoted;
- duplicates and false positives are logged explicitly.

### Confirmed differential families

Recorded in `ETW2_FLOOR_DIFFERENCE_MATRIX_v1.csv`.

**Section/dimension changes — 8 rows**
- repeated wide-beam change **140 cm in G3 → 120 cm in G4** at several homologous locations;
- repeated registered vertical-element dimension change **50 → 45**, with the orthogonal readable dimension remaining **30**, at three distinct locations.

**Geometry/topology changes — 7 rows**
- upper, right-side and lower-right beam/slab-perimeter projections or orthogonal returns present in G3 and absent or differently configured in G4;
- local 25-deep / 70-wide edge-beam return geometry differs at one registered location.

All source readings are `DOC_RASTER`; cross-level correspondence is `VER_PARZIALE`; affected persistent structural IDs remain `CANDIDATE` until bound to the canonical model.

### Candidate-review control

`ETW2_G3_G4_CANDIDATE_REVIEW_v1.csv` now records **30 reviewed candidates**, including:
- confirmed `SECTION_CHANGE` / `GEOMETRY_CHANGE` findings;
- `MATCH_FALSE_POSITIVE` cases caused by scan contrast, folds, text or subpixel registration;
- `DUPLICATE_OF_CONFIRMED` cases where multiple raster components belong to one structural finding;
- `UNRESOLVED_READING` / `UNRESOLVED_ANNOTATION` cases that remain blocked rather than being guessed.

This confirms that the raster difference is functioning as a locator rather than an automatic classifier.

**Status: PASS for repeated end-to-end G3↔G4 differences; half-sheet candidate review completed.**

## Task 4 — Floor Difference Matrix

Matrix now contains **15 confirmed G3↔G4 difference rows**:
- **8 `SECTION_CHANGE` / dimension-change rows**;
- **7 `GEOMETRY_CHANGE` rows**.

The candidate-review log is maintained separately so rejected and ambiguous raster differences remain traceable.

**Status: OPEN / PARTIAL.**

## Current residuals

| ID | Scope | Status | Blocking |
|---|---|---|---|
| ETW2-R01 | Four DocumentMaps | RESOLVED | — |
| ETW2-R02 | G3↔G4 raster registration | RESOLVED for comparison | — |
| ETW2-R03 | First G4/G3 difference | RESOLVED | — |
| ETW2-R04 | Complete Floor Difference Matrix G1–G4 | OPEN | floor signatures / TypicalFloorGroup |
| ETW2-R05..R19 | Bind confirmed G3↔G4 difference candidates to persistent structural IDs | OPEN | identity-level promotion only |
| ETW2-R20 | Review remaining 30 G3↔G4 raster candidates | OPEN | full G3↔G4 differential coverage |

## Gate status

**ETW-2 remains IN PROGRESS because the full G1–G4 Floor Difference Matrix is not complete.**

The former M0-S1B tooling block is removed. The current workflow separates:

`raster candidate → visual review → DOC_RASTER property reading → VER_PARZIALE cross-floor correspondence → later persistent-ID binding`.

This prevents both OCR loss and automatic promotion from image similarity.
