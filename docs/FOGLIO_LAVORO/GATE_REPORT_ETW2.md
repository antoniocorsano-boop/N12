# ETW-2 GATE REPORT — Floor Differential Reconstruction

**Gate:** ETW-2  
**Status:** IN PROGRESS — FIRST DIFFERENCE VERIFIED  
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

GitHub Actions run `32269573791` (`ETW2 Floor Differential`) completed with all steps PASS:
- execution PASS;
- output validation PASS;
- metadata artifact upload PASS.

Execution artifact `9371761458` contains:
- TAV-02S: 2 regions / 28 tiles;
- TAV-03S: 2 regions / 28 tiles;
- TAV-04S: 2 regions / 35 tiles;
- TAV-05S: 2 regions / 28 tiles;
- `floor_registration.json`;
- `execution_summary.json`.

The pipeline was subsequently optimized so Task 1–2 generate metadata only; high-resolution raster rendering is deferred to Task 3 evidence regions. The optimized workflow (`ETW2 Floor Differential` run #18) also completed successfully.

**Status: PASS.**

## Task 2 — Cross-floor registration

Base registration preserves native coordinates and uses G4 only as coordinate reference. `typical_floor_assumption = false` and identity from proximity is forbidden.

The initial same-normalized-page crop probe showed that page-normalized coordinates alone are not sufficient because TAV-04S and TAV-05S differ in sheet width and plan placement. This prevented false differential claims.

A controlled raster registration was therefore added:

- method: SIFT + ratio test + RANSAC homography;
- source: G3 / TAV-04S;
- target: G4 / TAV-05S;
- fit resolution: 100 DPI;
- evidence resolution: 300 DPI;
- good feature matches: 832;
- inliers: 394;
- inlier ratio: 0.4736;
- inlier RMSE: 1.50 px at 100 DPI.

GitHub Actions run `32270566299` completed registration, validation and artifact upload successfully. Artifact `9371990867` contains the registered G3 image, G4 target image, absolute difference, thresholded difference and `registration_result.json`.

Registration status remains `INF_CONTROLLED_REGISTRATION`: it is a geometric comparison aid, not structural evidence by itself.

**Status: PASS as comparison registration / no identity promotion.**

## Task 3 — First G4 ↔ G3 evidence sweep

ETW-1 terrace evidence windows were reused rather than inventing new regions.

Target pair:

`G4 / TAV-05S ↔ G3 / TAV-04S`

### First verified differences

Recorded in `ETW2_FLOOR_DIFFERENCE_MATRIX_v1.csv`.

1. `ETW2-DIFF-001` — region `BEAM_02`
   - G3 / TAV-04S: beam width annotation = **140 cm** (`DOC_RASTER`)
   - G4 / TAV-05S: beam width annotation = **120 cm** (`DOC_RASTER`)
   - comparison = `SECTION_CHANGE`
   - cross-level correspondence = `VER_PARZIALE`
   - persistent structural entity ID = still `CANDIDATE`

2. `ETW2-DIFF-002` — region `BEAM_03`
   - G3 / TAV-04S: inclined beam width annotation = **140 cm** (`DOC_RASTER`)
   - G4 / TAV-05S: inclined beam width annotation = **120 cm** (`DOC_RASTER`)
   - comparison = `SECTION_CHANGE`
   - cross-level correspondence = `VER_PARZIALE`
   - persistent structural entity ID = still `CANDIDATE`

The numeric values are source-document readings. The cross-floor binding remains deliberately below full structural identity until the beams are bound to persistent model IDs.

**Status: PASS for first end-to-end floor difference.**

## Task 4 — Floor Difference Matrix

Matrix initialized with the first two verified comparison rows.

**Status: OPEN / PARTIAL.**

## Current residuals

| ID | Scope | Status | Blocking |
|---|---|---|---|
| ETW2-R01 | Four DocumentMaps | RESOLVED | — |
| ETW2-R02 | G3↔G4 raster registration | RESOLVED for comparison | — |
| ETW2-R03 | First G4/G3 difference | RESOLVED | — |
| ETW2-R04 | Complete Floor Difference Matrix G1–G4 | OPEN | floor signatures / TypicalFloorGroup |
| ETW2-R05 | Bind BEAM_02 candidate to persistent structural ID | OPEN | identity-level promotion only |
| ETW2-R06 | Bind BEAM_03 candidate to persistent structural ID | OPEN | identity-level promotion only |

## Gate status

**ETW-2 remains IN PROGRESS because the full G1–G4 Floor Difference Matrix is not complete.**

However, the former M0-S1B tooling block is now demonstrably removed: the system has produced the first end-to-end verified inter-floor section changes directly from the original scanned carpenterie without OCR transcription and without automatic promotion of structural identity.
