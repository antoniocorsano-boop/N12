# Verification Audit — 2026-08-19

Scope: G3↔G4 support rebinding, TAV-04S/TAV-05S HiRes readings, Telaio 5 vertical binding, architectural/structural co-registration, fixed-line semantic audit and repository-memory consistency.

## Verdict

**PASS WITH OPEN 2D INTERNAL FIXED-LINE / ATTACHMENT RESIDUALS**

Support identity remains verified for all 34 supports. The section census is complete after one substantive HiRes correction: **P20 at G3 is 30x50, not 50x50**. The previous audit statement `P20 50x50→40x40` is SUPERSEDED.

## Source integrity — PASS
- TAV-04S immutable source: `d521f11...:archive/documentazione_originaria/tavola4-2.pdf`; raster 5732x8780; run `32223583877`; artifact `9354759992`.
- TAV-05S immutable source: `d521f11...:archive/documentazione_originaria/tavola 5.pdf`; raster 4680x8353; run `32225800144`; artifact `9355479921`.
- TAV-04 architectural: raster 4680x8298; run `32224976349`; artifact `9355209425`.

## G3↔G4 identity — PASS
All P01–P33 plus distinct P22P=22' are matched same-number/same-plan-position across G3 and G4. Telaio 5 mapping remains:
`S=P17, S'=P18, T=P19, U=P20, V=P21, Z=P22, A'=P22P, B'=P23, C'=P24`.

## Section layer — PASS AFTER CORRECTION
Six pure reductions and one reshape occur between G3 and G4:
- P10: 30x50 → 30x45 — SECTION_REDUCTION
- P13: 30x50 → 30x45 — SECTION_REDUCTION
- P15: 30x50 → 30x45 — SECTION_REDUCTION
- **P20: 30x50 → 40x40 — SECTION_RESHAPE**
- P22: 30x50 → 30x45 — SECTION_REDUCTION
- P26: 30x50 → 30x45 — SECTION_REDUCTION
- P29: 30x50 → 30x45 — SECTION_REDUCTION

The other 27 support sections are unchanged.

Evidence corrections retained:
- P18=30x110 is DOC/HIGH: both dimensions are directly readable.
- P21=30x45 remains DOC+MIS/HIGH: 30 is written, 45 measured from footprint.
- P20=30x50 is DOC/HIGH: HiRes crop directly shows bottom label 30 and side label 50.

Canonical corrected files:
- `data/canonical/g3_support_sections_tav04s_v1.csv`
- `data/canonical/g3_g4_support_crosswalk_v1.csv`
- `data/canonical/g3_g4_telaio5_vertical_binding_gate_v1.csv`

## Architectural co-registration — PASS
`data/canonical/tav04arch_tav05s_registration_v1.csv`:
46/66 RANSAC inliers; scale 1.01033; rotation 0.67624°; RMSE 3.76 px; p95 6.37 px. This is a MIS sheet transform, not an M0-G transform.

## Section-change support roles — PASS FOR THE SEVEN CASES
- P10 FACADE, exterior V_NEG
- P13 INTERNAL
- P15 FACADE, exterior V_POS
- P20 INTERNAL
- P22 INTERNAL
- P26 INTERNAL
- P29 FACADE, exterior U_NEG

Facade footprint changes P10/P15/P29 are resolved under G-16 as unilateral 5 cm reductions toward the interior while retaining the exterior edge.

## Internal graphic-reference audit
Canonical files:
- `data/canonical/g3_g4_internal_graphic_reference_audit_v1.csv`
- `data/canonical/g3_g4_internal_fixed_line_gate_v1.csv`

Results:
- P13: local crosshair only → NOT_QUALIFIED as construction fixed line.
- **P20: continuous thin vertical alignment through P19→P20 at G3 and G4 → one fixed-line coordinate qualified (U); transverse coordinate unresolved.**
- **P22: continuous thin vertical alignment through P22→P22P at G3 and G4 → one fixed-line coordinate qualified (U); transverse coordinate unresolved.**
- P26: local crosshair only → NOT_QUALIFIED as construction fixed line.

The old `support_fixed_lines_v2.csv` is a recovery aid with pre-reaudit semantics and is not generalized to these internal supports.

## Remaining open by design
1. qualify the transverse fixed-line coordinate for P20 and P22;
2. find independent documentary fixed-line evidence for P13 and P26, otherwise leave explicit residuals;
3. determine face offsets and beam attachment consequences for P13/P20/P22/P26;
4. extend support-role/fixed-line registry to other supports only where required by the global model;
5. preserve the original Telaio 5 user JPEG warning until its exact binary is archived.

## Canonical conclusion
Do not reopen the 34-support identity census. Use **P20 G3=30x50** as canonical. The next valid work is the unresolved fixed-line coordinate/physical-face attachment layer, with P20 and P22 already partially constrained in 1D.
