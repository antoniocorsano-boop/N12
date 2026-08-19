# N12 — Canonical Project State

Last checkpoint: 2026-08-19
Branch: `work/m0g-source-recovery`
Purpose: authoritative human/agent restart snapshot.

## Mandatory bootstrap
Read in order: `AGENTS.md` → this file → `memory/VERIFICATION_AUDIT_2026-08-19.md` → `memory/SOURCE_REGISTRY.csv` → `memory/ARTIFACT_INDEX.csv` → `memory/OPEN_RESIDUALS.csv` → regeneration/recovery registers.

Evidence grammar: `DOC / MIS / RIF / INF / ND`. Residuals are explicit and non-blocking. Never promote inference silently.

## Source recovery — G1 through G4 available
Immutable project PDFs are recoverable through `scripts/render_hires_sources.py` + GitHub Actions (`git show commit:path` → native raster → tiles → artifact).

Recovered structural sources:
- G1 TAV-02S `tavola2-2.pdf`: raster 4680x8609, run `32237614682`, artifact `9359545209`.
- G2 TAV-03S `tavola3-2.pdf`: raster 4680x8327, run `32237614682`, artifact `9359545209`.
- G3 TAV-04S `tavola4-2.pdf`: raster 5732x8780, run `32223583877`, artifact `9354759992`.
- G4 TAV-05S `tavola 5.pdf`: raster 4680x8353, run `32225800144`, artifact `9355479921`.
- TAV-04 architectural: raster 4680x8298, run `32224976349`, artifact `9355209425`.

G1/G2 render hashes and immutable provenance are frozen in `data/canonical/tav02s_tav03s_hires_render_manifest_v1.csv`.

TAV-05S↔TAV-04ARCH co-registration is verified in `data/canonical/tav04arch_tav05s_registration_v1.csv`: 46/66 inliers, scale 1.01033, rotation 0.67624°, RMSE 3.76 px, p95 6.37 px. It is a sheet MIS transform, not M0-G.

## Fixed-line semantic rule
Canonical G-16 working rule:
- ANGLE: fixed line at exterior corner;
- FACADE: fixed line at midpoint of exterior edge;
- INTERNAL: fixed line only from documentary evidence;
- section changes modify footprint about the fixed line; do not recenter automatically;
- old `tav05_fixed_lines_numeric_v7.csv` values remain raw measured graphic references, not automatically construction fixed lines.

## G4 planar baseline
34 supports including distinct `P22P=22'`. Wide supports: P18=30x110 long X, P23=30x110 long X, P30=30x110 long Y. TAV-05S topology v6 remains current planar baseline.

## Telaio 5
Historical path `S–S'–T–U–V–Z–A'–B'–C'` maps to `P17–P18–P19–P20–P21–P22–P22P–P23–P24`.
Projected stations: `0.00 / 4.70 / 8.75 / 9.95 / 15.75 / 18.65 / 19.85 / 23.90 / 28.60 m`; total 28.60 m hard gate. These are projected frame stations, not Euclidean plan-member lengths.

## G1–G4 section layer — VERIFIED 34/34
The structural support numbering remains readable across G1, G2, G3 and G4. Section censuses are complete and frozen as documentary data:
- `data/canonical/g1_support_sections_tav02s_v1.csv`
- `data/canonical/g2_support_sections_tav03s_v1.csv`
- `data/canonical/g3_support_sections_tav04s_v1.csv`
- G4 support sections from TAV-05S baseline
- consolidated `data/canonical/g1_g4_support_section_history_v1.csv`
- gate `data/canonical/g1_g4_support_section_history_gate_v1.csv`

All 34 vertical section sequences are complete, including distinct P22P. This section layer does **not** imply fixed-line/centroid continuity.

Notable sequences:
- P01–P09: `40x50 → 40x45 → 40x40 → 40x40`.
- P10/P13/P15/P22/P26/P29: `40x50 → 35x50 → 30x50 → 30x45`.
- P18/P23/P30: `30x110` unchanged at G1/G2/G3/G4.
- P19: `40x40 → 40x45 → 40x40 → 40x40`; documentary non-monotonic sequence, never regularize.
- P20: `40x50 → 40x45 → 30x50 → 40x40`; documentary non-monotonic sequence, never regularize.

### Critical P20 correction
**P20 at G3 is 30x50, not 50x50.** TAV-04S HiRes directly shows labels 30 and 50. G4 P20=40x40. Therefore G3→G4 P20 is `SECTION_RESHAPE`, not a pure reduction. All older `P20 50x50` statements are SUPERSEDED.

Other evidence corrections: P18=30x110 is DOC/HIGH; P21 G3=30x45 remains DOC+MIS/HIGH.

## Architectural roles for G3→G4 changed supports
- P10 FACADE exterior V_NEG
- P13 INTERNAL
- P15 FACADE exterior V_POS
- P20 INTERNAL
- P22 INTERNAL
- P26 INTERNAL
- P29 FACADE exterior U_NEG

Facade changes are geometrically closed under G-16:
- P10: exterior V_NEG retained; 5 cm inward reduction.
- P15: exterior V_POS retained; 5 cm inward reduction.
- P29: exterior U_NEG retained; 5 cm inward reduction.
Canonical: `data/canonical/g3_g4_facade_risega_offsets_v1.csv`.

## Internal fixed-line audit — CURRENT RESIDUAL LAYER
Canonical files:
- `data/canonical/g3_g4_internal_graphic_reference_audit_v1.csv`
- `data/canonical/g3_g4_internal_u_fixedline_geometry_v1.csv`
- `data/canonical/g3_g4_internal_fixedline_gate_v2.csv`

Current qualified results:
- P13: U/V NOT_QUALIFIED. G1–G4 section history is DOC, but the visible cross remains only a local graphic reference.
- P20: **U PASS, V HOLD**. Continuous structural alignment through P19→P20 qualifies U on G3/G4. Relative U footprint: G3 `30/0 cm` → G4 `20/20 cm`; no single U face retained.
- P22: **U PASS, V HOLD**. Continuous P22→P22P alignment qualifies U. Relative U footprint: G3 `30/20 cm` → G4 `30/15 cm`; U_NEG retained, U_POS retreats 5 cm.
- P26: U/V NOT_QUALIFIED. G1/G2 review still does not provide an independent construction fixed line; local cross only.

Do not promote horizontal beam/slab edges to transverse V fixed lines. Do not generalize old `support_fixed_lines_v2.csv` semantics to internal supports.

## Legacy vertical chains
Historical `column_fixed_lines.csv` contains 27 `VER_5_LEVELS` chains but is explicitly `PREDOC_GEOMETRICO`. It is a recovery/cross-check aid only and cannot override HiRes documentary semantics or fill P13/P26 by analogy.

## Next structural actions
1. keep P13/P26 and P20/P22-V as explicit residuals unless stronger independent fixed-line evidence appears;
2. proceed non-blocking with lower-floor semantic geometry/rebinding now that G1/G2 section censuses are complete;
3. revalidate physical beam attachments wherever section footprint changes relative to a qualified fixed line;
4. release vertical ETABS/EdiLus geometry component-wise only where insertion/offset evidence is qualified; do not wait for unrelated residuals;
5. continue toward G5/roof and foundation/source-specific geometry as separate FloorVariants rather than blind copies.

## 3D / building notes
Never blindly copy floors: TypicalFloorGroup → FloorVariant → ElementOverride → LocalTopologyOverride. G5 roof is distinct inclined geometry. First three storey intervals are RIF 3.20 m.

Foundation/material facts already consolidated: same foundation elevation; main foundation H=90 + slab 20 = 110 cm; slab 16+4; prestressed joists 3 strands @50 cm; concrete density RIF 2400 kg/m³.

## Memory warning
Memory gate remains `PASS_WITH_WARNING` only because the exact original Telaio 5 user JPEG is not pixel-archived in Git; its SHA/dimensions, semantic trace and recovery pointers are persistent.
