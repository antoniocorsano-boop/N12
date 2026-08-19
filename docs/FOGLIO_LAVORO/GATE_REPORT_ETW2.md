# ETW-2 GATE REPORT — Floor Differential Reconstruction

**Gate:** ETW-2  
**Status:** IN PROGRESS — G3↔G4 DIFFERENTIAL SCAN COMPLETE  
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

GitHub Actions run `32269573791` completed with execution, validation and metadata artifact upload PASS. Artifact `9371761458` contains the four DocumentMaps and floor registration metadata. The metadata-only optimized workflow also passed.

**Status: PASS.**

## Task 2 — G3↔G4 controlled registration

Page-normalized coordinates alone were rejected as insufficient. Controlled registration uses SIFT + ratio test + RANSAC homography, source G3/TAV-04S → target G4/TAV-05S, fit 100 DPI and evidence 300 DPI.

Observed quality:
- good matches: 832;
- inliers: 394;
- inlier ratio: 0.4736;
- inlier RMSE: 1.50 px at 100 DPI.

Registration remains `INF_CONTROLLED_REGISTRATION`; it is a comparison aid only.

A difference-candidate queue produced **60 REVIEW_REQUIRED candidates**, with automatic promotion forbidden.

**Status: PASS for comparison registration / no identity promotion.**

## Task 3 — G4 ↔ G3 evidence sweep

Target pair: `G4 / TAV-05S ↔ G3 / TAV-04S`.

### Review completion

- raster candidates generated: **60**;
- candidates explicitly reviewed: **60 / 60**;
- confirmed distinct structural differences in `ETW2_FLOOR_DIFFERENCE_MATRIX_v1.csv`: **15**;
- ambiguous readings remain unpromoted;
- duplicate raster components are not double-counted;
- folds, text, scan contrast and subpixel-registration responses are explicitly logged as false positives.

### Confirmed differential families

**Section/dimension changes — 8 rows**
- repeated wide-beam change **140 cm in G3 → 120 cm in G4** at homologous registered locations;
- repeated registered vertical-element dimension change **50 → 45**, with orthogonal readable dimension **30** unchanged, at three distinct locations.

**Geometry/topology changes — 7 rows**
- upper, right-side and lower-right beam/slab-perimeter projections or orthogonal returns present in G3 and absent or differently configured in G4;
- local 25-deep / 70-wide edge-beam return geometry differs at registered locations.

All source property readings are `DOC_RASTER`. Cross-level correspondence is `VER_PARZIALE`. Persistent structural IDs remain `CANDIDATE` until later entity binding.

### Candidate-review control

`ETW2_G3_G4_CANDIDATE_REVIEW_v1.csv` now records all 60 dispositions, including:
- confirmed `SECTION_CHANGE` / `GEOMETRY_CHANGE`;
- `MATCH_FALSE_POSITIVE`;
- `DUPLICATE_OF_CONFIRMED`;
- `UNRESOLVED_READING` / `UNRESOLVED_ANNOTATION`.

**Status: PASS — full G3↔G4 raster candidate sweep complete.**

## Task 4 — Floor Difference Matrix

Current matrix contains **15 confirmed G3↔G4 difference rows**:
- **8 section/dimension changes**;
- **7 geometry/topology changes**.

G3↔G4 candidate review is complete. The next comparison pair is **G3↔G2**.

**Status: OPEN / PARTIAL for G1–G4.**

## Current residuals

| ID | Scope | Status | Blocking |
|---|---|---|---|
| ETW2-R01 | Four DocumentMaps | RESOLVED | — |
| ETW2-R02 | G3↔G4 raster registration | RESOLVED for comparison | — |
| ETW2-R03 | First G4/G3 difference | RESOLVED | — |
| ETW2-R04 | Complete Floor Difference Matrix G1–G4 | OPEN | floor signatures / TypicalFloorGroup |
| ETW2-R05..R19 | Bind confirmed G3↔G4 candidates to persistent structural IDs | OPEN | identity-level promotion only |
| ETW2-R20 | Review 60 G3↔G4 raster candidates | RESOLVED | — |
| ETW2-R21 | Execute controlled G2↔G3 registration and evidence sweep | OPEN | next pair differential coverage |

## Gate status

**ETW-2 remains IN PROGRESS because G2↔G3 and G1↔G2 are not yet complete.**

The G3↔G4 differential stage is complete at raster-candidate level. The validated workflow is now:

`DocumentMap → controlled registration → raster candidate → visual review → DOC_RASTER property reading → VER_PARZIALE correspondence → persistent-ID binding later`.
