# Verification Audit — 2026-08-19

Scope: G3↔G4 support rebinding, TAV-04S HiRes readings, Telaio 5 vertical binding, architectural/structural co-registration, repository-memory consistency.

## Verdict

**PASS WITH OPEN FIXED-LINE / RISEGA RESIDUALS**

No contradiction remains in support identity, section mapping, source recovery or architectural↔structural sheet pairing after correction of one evidence-classification error on P18.

## Checks performed

### 1. TAV-04S source integrity — PASS
- immutable source: `d521f11a6989664a54409ab0df064903d8986564:archive/documentazione_originaria/tavola4-2.pdf`
- historical Git blob: `7807c32f52e8d6fcefad8abe7eac79ad9dd65efa`
- targeted render run: `32223583877`
- artifact: `9354759992` (`n12-hires-tav04s`)
- PDF SHA256: `2b878bcefde54ff2b42bafa2a4fdc8a8420bd71514a7e6966a864f009ade685e`
- raster SHA256: `46c39e6db16a51b7805db3a2e29b08f47e5809be0ad7d17d7eff5d3533c95b1c`
- native raster: `5732x8780`

### 2. TAV-05S source integrity — PASS
- immutable source: `d521f11a6989664a54409ab0df064903d8986564:archive/documentazione_originaria/tavola 5.pdf`
- historical Git blob: `ec32cd621877e9037cb26ebc083164140a8e3e68`
- targeted render run: `32225800144`
- artifact: `9355479921` (`n12-hires-tav05s`)
- PDF SHA256: `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`
- raster SHA256: `5cd429cfa6692e644efb875e0aef7130f669b5d024d496ea278574e0b4c8849d`
- native raster: `4680x8353`

### 3. G3 support census — PASS
`data/canonical/g3_support_sections_tav04s_v1.csv` contains all 34 supports: P01–P33 plus distinct P22P=22'. No duplicate support identity and no missing support.

### 4. G3→G4 support identity — PASS
All 34 G4 supports have a same-number/same-plan-position G3 support in `data/canonical/g3_g4_support_crosswalk_v1.csv`.

Telaio 5 subset remains:
`S=P17, S'=P18, T=P19, U=P20, V=P21, Z=P22, A'=P22P, B'=P23, C'=P24`.

### 5. G3→G4 section changes — PASS
Exactly seven section reductions are present:
- P10: 30x50 → 30x45
- P13: 30x50 → 30x45
- P15: 30x50 → 30x45
- P20: 50x50 → 40x40
- P22: 30x50 → 30x45
- P26: 30x50 → 30x45
- P29: 30x50 → 30x45

The remaining 27 support sections are unchanged.

### 6. Evidence classification correction — CORRECTED
P18 was previously marked `DOC+MIS` because the 110 cm side had been treated as measured. HiRes inspection shows both dimensions `30` and `110` directly written at support 18. Therefore P18=30x110 is **DOC/HIGH**.

P21 remains correctly `DOC+MIS/HIGH`: short side 30 is directly written; long side 45 is obtained by direct footprint measurement against the labelled dimension.

### 7. Telaio 5 G3↔G4 gate — PASS/PARTIAL
Identity and G3 sections are PASS. Pending only:
- P20 and P22 risega face retention;
- fixed-line-to-face distances;
- physical beam attachment changes;
- final ETABS/EdiLus offsets.

### 8. TAV-04 architectural source integrity — PASS
- source: `archive/documentazione_originaria/tavola 4.pdf`
- targeted render run: `32224976349`
- artifact: `9355209425` (`n12-hires-tav04arch`)
- PDF SHA256: `87972049435ea9bac6df76b62da67de097a1299f55dadbcb0dcf65526a3f0948`
- raster SHA256: `2580d649761a09689a478a522eb691bde6714441af0ed59bb23e51da6248f9e5`
- native raster: `4680x8298`

### 9. TAV-05S ↔ TAV-04ARCH co-registration — PASS
Independent ORB geometric-feature matching plus RANSAC gives a high-quality similarity-affine registration from TAV-05S native pixels to TAV-04ARCH native pixels:
- 66 accepted feature matches;
- 46 RANSAC inliers;
- inlier ratio 0.69697;
- scale 1.01033;
- rotation 0.67624°;
- RMSE 3.76 px;
- median residual 3.33 px;
- 95th percentile 6.37 px.

Canonical transform: `data/canonical/tav04arch_tav05s_registration_v1.csv`.

This closes the old inferential pairing problem. The transform is a **sheet co-registration MIS**, not an M0-G metric transformation.

### 10. Memory audit — PASS AFTER CORRECTIONS
Corrected stale states:
- TAV-04S no longer inaccessible;
- TAV-05S now also has a reproducible native HiRes render manifest;
- Telaio 5 gate no longer says G3 sections are pending;
- architectural source/pairing residual is closed;
- artifact index records current HiRes and G3↔G4 artifacts;
- P18 evidence is corrected to pure DOC.

## Still open by design
These are not errors:
1. semantic classification of each support as `ANGLE/FACADE/INTERNAL` using the now-registered architectural perimeter;
2. final G4 construction fixed-line positions after role/perimeter audit;
3. risega classification for P10/P13/P15/P20/P22/P26/P29;
4. `dN/dS/dE/dW` at G3 and G4;
5. beam attachment offsets caused by footprint changes;
6. original user JPEG of Telaio 5 remains a source pointer rather than pixel-archived Git evidence; its semantic trace is persistent.

## Canonical conclusion
The G3↔G4 **identity and section layer is verified** and the TAV-04ARCH↔TAV-05S **sheet pairing/co-registration is verified**. Do not reopen either unless new documentary evidence conflicts. The next valid task is support-role → fixed-line → risega/attachment geometry.
