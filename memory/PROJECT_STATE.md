# N12 — Canonical Project State

Last checkpoint: 2026-08-19
Branch: `work/m0g-source-recovery`
Purpose: authoritative human/agent restart snapshot.

## Mandatory bootstrap
Read in order: `AGENTS.md` → this file → `memory/VERIFICATION_AUDIT_2026-08-19.md` → `memory/SOURCE_REGISTRY.csv` → `memory/ARTIFACT_INDEX.csv` → `memory/OPEN_RESIDUALS.csv` → regeneration/recovery registers.

Evidence grammar: `DOC / MIS / RIF / INF / ND`. Residuals are explicit and non-blocking. Never promote inference silently.

## Source recovery
Immutable project PDFs are recoverable through `scripts/render_hires_sources.py` + GitHub Actions (`git show commit:path` → native raster → tiles → artifact).

Key recovered sources:
- G3 TAV-04S `tavola4-2.pdf`: raster 5732x8780, run `32223583877`, artifact `9354759992`.
- G4 TAV-05S `tavola 5.pdf`: raster 4680x8353, run `32225800144`, artifact `9355479921`.
- TAV-04 architectural: raster 4680x8298, run `32224976349`, artifact `9355209425`.

TAV-05S↔TAV-04ARCH co-registration is verified in `data/canonical/tav04arch_tav05s_registration_v1.csv`: 46/66 inliers, scale 1.01033, rotation 0.67624°, RMSE 3.76 px, p95 6.37 px. It is a sheet MIS transform, not M0-G.

## Fixed-line semantic rule
Canonical G-16 working rule:
- ANGLE: fixed line at exterior corner;
- FACADE: fixed line at midpoint of exterior edge;
- INTERNAL: fixed line only from documentary evidence;
- section changes modify footprint about the fixed line; do not recenter automatically;
- old `tav05_fixed_lines_numeric_v7.csv` values remain raw measured graphic references, not automatically construction fixed lines.

## G4 baseline
34 supports including distinct `P22P=22'`. Wide supports: P18=30x110 long X, P23=30x110 long X, P30=30x110 long Y. TAV-05S topology v6 remains current planar baseline.

## Telaio 5
Historical path `S–S'–T–U–V–Z–A'–B'–C'` maps to `P17–P18–P19–P20–P21–P22–P22P–P23–P24`.
Projected stations: `0.00 / 4.70 / 8.75 / 9.95 / 15.75 / 18.65 / 19.85 / 23.90 / 28.60 m`; total 28.60 m hard gate. These are projected frame stations, not Euclidean plan-member lengths.

## G3↔G4 identity and sections — VERIFIED
All 34 support identities are matched same-number/same-plan-position across G3/G4. Do not reopen the census without conflicting documentary evidence.

Canonical files:
- `data/canonical/g3_support_sections_tav04s_v1.csv`
- `data/canonical/g3_g4_support_crosswalk_v1.csv`
- `data/canonical/g3_g4_telaio5_vertical_binding_gate_v1.csv`

### Critical HiRes correction
**P20 at G3 is 30x50, not 50x50.** TAV-04S HiRes directly shows labels 30 and 50. G4 P20=40x40. Therefore P20 is `SECTION_RESHAPE` (30x50→40x40), not a pure reduction. All older `P20 50x50` statements are SUPERSEDED.

Current section-change set:
- P10 30x50→30x45 reduction
- P13 30x50→30x45 reduction
- P15 30x50→30x45 reduction
- P20 30x50→40x40 reshape
- P22 30x50→30x45 reduction
- P26 30x50→30x45 reduction
- P29 30x50→30x45 reduction
Other 27 sections unchanged.

Other evidence corrections: P18=30x110 is DOC/HIGH; P21=30x45 remains DOC+MIS/HIGH.

## Architectural roles for section-change supports
P10 FACADE exterior V_NEG; P13 INTERNAL; P15 FACADE exterior V_POS; P20 INTERNAL; P22 INTERNAL; P26 INTERNAL; P29 FACADE exterior U_NEG. All HIGH after registered-plan/local HiRes checks.

Facade changes closed under G-16:
- P10: retain exterior V_NEG; 5 cm reduction on interior V_POS.
- P15: retain exterior V_POS; 5 cm reduction on interior V_NEG.
- P29: retain exterior U_NEG; 5 cm reduction on interior U_POS.
Canonical: `g3_g4_facade_risega_offsets_v1.csv`.

## Internal fixed-line audit — CURRENT FRONT
Canonical:
- `data/canonical/g3_g4_internal_graphic_reference_audit_v1.csv`
- `data/canonical/g3_g4_internal_fixed_line_gate_v1.csv`

Results:
- P13: local crosshair only → graphic MIS reference; construction fixed line NOT_QUALIFIED.
- P20: continuous thin vertical line through P19→P20 at both G3 and G4 → **U alignment qualified; V unresolved**.
- P22: continuous thin vertical line through P22→P22P at both levels → **U alignment qualified; V unresolved**.
- P26: local crosshair only → graphic MIS reference; construction fixed line NOT_QUALIFIED.

Do not generalize `support_fixed_lines_v2.csv` (pre-reaudit semantics, only P18/P23/P30) to these cases.

## Next structural action
1. qualify transverse V fixed-line coordinate for P20 and P22 from independent structural evidence;
2. search independent fixed-line evidence for P13 and P26; if absent, preserve explicit residual instead of inventing centroid/face retention;
3. derive physical face offsets and revalidate beam attachments;
4. release verified G3–G4 vertical geometry to ETABS/EdiLus only after those gates.

## 3D / building notes
Never blindly copy floors: TypicalFloorGroup → FloorVariant → ElementOverride → LocalTopologyOverride. G5 roof is distinct inclined geometry. First three storey intervals are RIF 3.20 m.

Foundation/material facts already consolidated: same foundation elevation; main foundation H=90 + slab 20 = 110 cm; slab 16+4; prestressed joists 3 strands @50 cm; concrete density RIF 2400 kg/m³.

## Memory warning
Memory gate remains `PASS_WITH_WARNING` only because the exact original Telaio 5 user JPEG is not pixel-archived in Git; its SHA/dimensions, semantic trace and recovery pointers are persistent.
