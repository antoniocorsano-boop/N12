# Verification Audit — 2026-08-19

Scope: source recovery G1–G4, complete support-section census, G3↔G4 support rebinding, Telaio 5 vertical binding, architectural/structural co-registration, fixed-line semantic audit and repository-memory consistency.

## Verdict

**PASS WITH OPEN 2D INTERNAL FIXED-LINE / ATTACHMENT RESIDUALS**

The support identity and **section layer are now verified from G1 through G4 for all 34 supports**. Remaining uncertainty is geometrical insertion/fixed-line/physical-face placement, not section identity.

## Source integrity — PASS
- TAV-02S / G1 immutable source: `d521f11...:archive/documentazione_originaria/tavola2-2.pdf`; native raster 4680x8609; run `32237614682`; artifact `9359545209`.
- TAV-03S / G2 immutable source: `d521f11...:archive/documentazione_originaria/tavola3-2.pdf`; native raster 4680x8327; run `32237614682`; artifact `9359545209`.
- TAV-04S / G3: raster 5732x8780; run `32223583877`; artifact `9354759992`.
- TAV-05S / G4: raster 4680x8353; run `32225800144`; artifact `9355479921`.
- TAV-04 architectural: raster 4680x8298; run `32224976349`; artifact `9355209425`.

G1/G2 hashes/dimensions/provenance are frozen in `data/canonical/tav02s_tav03s_hires_render_manifest_v1.csv`.

## Support identity — PASS
All P01–P33 plus distinct P22P=22' are readable in the structural plans. G3↔G4 same-number/same-plan-position identity remains verified. Telaio 5 mapping remains:
`S=P17, S'=P18, T=P19, U=P20, V=P21, Z=P22, A'=P22P, B'=P23, C'=P24`.

## Complete G1–G4 section layer — PASS
Canonical sources:
- `data/canonical/g1_support_sections_tav02s_v1.csv` — 34/34 DOC/HIGH;
- `data/canonical/g2_support_sections_tav03s_v1.csv` — 34/34 DOC/HIGH;
- `data/canonical/g3_support_sections_tav04s_v1.csv` — 34/34, with P21 long side DOC+MIS;
- G4 TAV-05S support baseline;
- `data/canonical/g1_g4_support_section_history_v1.csv` — complete vertical history;
- `data/canonical/g1_g4_support_section_history_gate_v1.csv` — PASS.

Representative/documentarily important sequences:
- P01–P09: `40x50 → 40x45 → 40x40 → 40x40`.
- P10/P13/P15/P22/P26/P29: `40x50 → 35x50 → 30x50 → 30x45`.
- P18/P23/P30: `30x110 → 30x110 → 30x110 → 30x110`.
- P19: `40x40 → 40x45 → 40x40 → 40x40`; preserve the non-monotonic documentary sequence.
- P20: `40x50 → 40x45 → 30x50 → 40x40`; preserve the non-monotonic documentary sequence.

Section history does **not** determine fixed-line coordinates or insertion points.

## Critical P20 correction — PASS
P20 at G3 is **30x50, not 50x50**. TAV-04S HiRes directly shows 30 and 50. Therefore G3→G4 P20 is `30x50 → 40x40 = SECTION_RESHAPE`. All older P20=50x50 statements are SUPERSEDED.

Other evidence corrections retained:
- P18=30x110 is DOC/HIGH.
- P21 G3=30x45 remains DOC+MIS/HIGH.

## G3→G4 section changes — PASS
Six reductions and one reshape:
- P10: 30x50 → 30x45
- P13: 30x50 → 30x45
- P15: 30x50 → 30x45
- P20: 30x50 → 40x40 — reshape
- P22: 30x50 → 30x45
- P26: 30x50 → 30x45
- P29: 30x50 → 30x45

Other 27 G3→G4 sections are unchanged.

## Architectural co-registration — PASS
`data/canonical/tav04arch_tav05s_registration_v1.csv`: 46/66 RANSAC inliers; scale 1.01033; rotation 0.67624°; RMSE 3.76 px; p95 6.37 px. This is a MIS sheet transform, not an M0-G transform.

## Section-change architectural roles — PASS
- P10 FACADE, exterior V_NEG
- P13 INTERNAL
- P15 FACADE, exterior V_POS
- P20 INTERNAL
- P22 INTERNAL
- P26 INTERNAL
- P29 FACADE, exterior U_NEG

Facade P10/P15/P29 changes are resolved under G-16 as unilateral 5 cm inward reductions retaining the exterior edge.

## Internal fixed-line audit — PARTIAL PASS
Canonical current files:
- `data/canonical/g3_g4_internal_graphic_reference_audit_v1.csv`
- `data/canonical/g3_g4_internal_u_fixedline_geometry_v1.csv`
- `data/canonical/g3_g4_internal_fixedline_gate_v2.csv`

Qualified results:
- P13: U/V HOLD. Local cross only; G1/G2 review does not supply an independent construction fixed-line alignment.
- P20: **U PASS, V HOLD**. Continuous P19→P20 alignment qualifies U. Relative U footprint: G3 `30/0 cm` → G4 `20/20 cm`; no single U face retained.
- P22: **U PASS, V HOLD**. Continuous P22→P22P alignment qualifies U. Relative U footprint: G3 `30/20 cm` → G4 `30/15 cm`; U_NEG retained, U_POS retreats 5 cm.
- P26: U/V HOLD. Local cross only; lower-floor inspection does not independently qualify it.

Extended horizontal lines near P20/P22/P13/P26 are not promoted automatically: where they are beam/slab physical edges they are not fixed-line evidence.

## Legacy 27 vertical chains — RECOVERY AID ONLY
Historical `column_fixed_lines.csv` contains 27 chains marked `VER_5_LEVELS`, but all are `PREDOC_GEOMETRICO`. They may be used for cross-checking only; they cannot fill P13/P26 or the missing P20/P22 V coordinate by analogy.

## Repository-memory audit — PASS AFTER UPDATE
- G1/G2 source access is persistent and regenerable.
- G1/G2 section censuses and G1–G4 history are indexed.
- Internal fixed-line gate v1 is superseded by v2.
- Open residuals now distinguish section-complete geometry from unresolved insertion/fixed-line components.
- No source should be requested again before repository/history/renderer recovery is exhausted.

## Remaining open by design
1. P20 transverse V fixed-line component.
2. P22 transverse V fixed-line component.
3. P13 and P26 construction fixed-line components.
4. physical beam attachment offsets where footprints change.
5. semantic fixed-line/attachment rebinding of lower floors as needed for the global model.
6. exact original Telaio 5 user JPEG remains a source pointer rather than pixel-archived Git evidence.

## Canonical conclusion
**Do not reopen the G1–G4 support-section census.** It is complete. Continue from geometry: preserve P13/P26 and P20/P22-V as explicit residuals unless stronger evidence emerges, while advancing all independent lower-floor and global-model work non-blockingly.
