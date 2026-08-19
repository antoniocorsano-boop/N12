# N12 — Canonical Project State

Last checkpoint: 2026-08-19
Branch: `work/m0g-source-recovery`
Purpose: single human- and agent-readable snapshot of the active structural reconstruction state.

## Current objective

Complete the existing-RC building dossier and produce a traceable global model suitable for ACCA EdiLus-EE, followed by open-source FEM validation.

## Mandatory evidence grammar

`DOC` documentale · `MIS` misurato · `RIF` riferito/confermato · `INF` inferito · `ND` non disponibile.

Residuals are explicit and non-blocking. Never silently promote inference to DOC.

## Repository memory — mandatory bootstrap

Operational continuity MUST NOT depend on the current chat or on `/mnt/data`.

Before any structural work, read in this order:
1. `AGENTS.md`
2. `memory/PROJECT_STATE.md`
3. `memory/VERIFICATION_AUDIT_2026-08-19.md`
4. `memory/SOURCE_REGISTRY.csv`
5. `memory/ARTIFACT_INDEX.csv`
6. `memory/OPEN_RESIDUALS.csv`
7. `memory/REGENERATION_RECIPES.csv`
8. `memory/FILE_LIBRARY_RECOVERY.csv`
9. `memory/MEMORY_GATE_STATUS.csv`

Persistence contract:
- immutable originals → Git commit:path + blob SHA;
- canonical text/data → repository path + version/commit;
- derived raster/QA → deterministic regeneration recipe;
- chat/user evidence → repository trace/metadata + recovery pointer until the exact binary is Git-archived;
- `AT_RISK`, uncontracted `RUNTIME_ONLY`, and `CHAT_ONLY` are forbidden by `scripts/check_repository_memory.py`.

Current memory gate remains `PASS_WITH_WARNING` only because the original Telaio 5 user JPEG is not pixel-archived in Git. Its structural content is persisted in `evidence/derived/telaio5_plan_trace_v1.svg`, together with dimensions/SHA256 and recovery pointers. This source remains `RIF` and the SVG is not a DOC substitute.

## Source hierarchy

1. Original high-resolution structural drawings.
2. Reinforcement/detail drawings.
3. Architectural/elevation drawings for cross-checking.
4. Calculation report and historical frame drawings.
5. Derived/historical DXF/CSV as recovery aids only.

## Level/source crosswalk

- Foundation → TAV-01S `tavola1-2.pdf`
- G1 / I impalcato → TAV-02S `tavola2-2.pdf`
- G2 / II impalcato → TAV-03S `tavola3-2.pdf`
- G3 / III impalcato → TAV-04S `tavola4-2.pdf`
- G4 / IV impalcato → TAV-05S `tavola 5.pdf`
- G5 / roof → TAV-06S `tavola 6-1.pdf`

Historical immutable source commit: `d521f11a6989664a54409ab0df064903d8986564`.

## HiRes source recovery — operationally resolved

Immutable PDFs can be recovered without relying on chat/runtime binary support. `git show immutable_commit:path` runs inside GitHub Actions through `scripts/render_hires_sources.py`; the action extracts the native raster and overlapping tiles and returns a downloadable artifact.

TAV-04S / G3:
- successful run: `32223583877`
- artifact: `9354759992` / `n12-hires-tav04s`
- PDF SHA256: `2b878bcefde54ff2b42bafa2a4fdc8a8420bd71514a7e6966a864f009ade685e`
- native raster SHA256: `46c39e6db16a51b7805db3a2e29b08f47e5809be0ad7d17d7eff5d3533c95b1c`
- native raster: `5732 x 8780 px`

TAV-04 architectural:
- successful run: `32224976349`
- artifact: `9355209425` / `n12-hires-tav04arch`
- PDF SHA256: `87972049435ea9bac6df76b62da67de097a1299f55dadbcb0dcf65526a3f0948`
- native raster SHA256: `2580d649761a09689a478a522eb691bde6714441af0ed59bb23e51da6248f9e5`
- native raster: `4680 x 8298 px`

Source access is therefore not a current residual.

## Current G4 baseline

TAV-05S topology is the current best consolidated planar baseline.

Support census: 34 supports including distinct `P22P` = 22'.
Current support registry: `data/canonical/tav05_fixed_lines_numeric_v7.csv`.
Important caveat: its numeric points were produced before the latest semantic reaudit of construction fixed lines. They remain measured graphic references, NOT automatically final construction fixed lines.

Wide supports:
- P18 = 30x110, long side X
- P23 = 30x110, long side X
- P30 = 30x110, long side Y

P22P is distinct from P22.

## Fixed-line semantic rule — RIF canonical working rule

- corner column: fixed line normally at exterior corner;
- facade column: fixed line normally at midpoint of exterior edge;
- internal column: fixed-line position only from documentary evidence;
- vertical fixed line remains aligned between storeys unless explicit documentary evidence says otherwise;
- section reductions/riseghe change the footprint about the fixed line, not the fixed-line coordinate.

Do not overwrite measured graphic references until role/perimeter is verified on source drawings.

## Telaio 5 — closed identity / 1D binding

Historical path:
`S → S' → T → U → V → Z → A' → B' → C'`

Verified G4 support binding:
`P17 → P18 → P19 → P20 → P21 → P22 → P22P → P23 → P24`

Documental projected stations:
`0.00 / 4.70 / 8.75 / 9.95 / 15.75 / 18.65 / 19.85 / 23.90 / 28.60 m`

Hard gate: total projected extent = `28.60 m`.

These are projected/station dimensions along the historical reference, not necessarily Euclidean lengths of the plan polyline. Previous direct Euclidean residual comparisons are superseded as a validation method.

Persistent evidence aid:
- `evidence/derived/telaio5_plan_trace_v1.svg`
- original current JPEG metadata: 1152×1536 px; SHA256 `6961c6f0d16f51a98488726cce770687f3baf162cfd0581e342014883d38c041`.

## G3↔G4 rebinding — support identity and sections verified

TAV-04S has been recovered and read at native resolution. All 34 G4 supports have a same-number, same-plan-position support on G3, including distinct `P22P = 22'`.

Canonical files:
- `data/canonical/g3_g4_support_crosswalk_v1.csv`
- `data/canonical/g3_support_sections_tav04s_v1.csv`
- `data/canonical/g3_g4_telaio5_vertical_binding_gate_v1.csv`

Section changes G3 → G4 occur only at:
- P10: `30x50 → 30x45`
- P13: `30x50 → 30x45`
- P15: `30x50 → 30x45`
- P20: `50x50 → 40x40`
- P22: `30x50 → 30x45`
- P26: `30x50 → 30x45`
- P29: `30x50 → 30x45`

All other 27 support sections remain unchanged.

Telaio 5 subset:
- P17 40x40 → 40x40
- P18 30x110 → 30x110
- P19 40x40 → 40x40
- P20 50x50 → 40x40
- P21 30x45 → 30x45
- P22 30x50 → 30x45
- P22P 40x40 → 40x40
- P23 30x110 → 30x110
- P24 40x40 → 40x40

Evidence correction from audit:
- P18 = `30x110` is **DOC/HIGH** because both 30 and 110 are directly readable on TAV-04S HiRes.
- P21 = `30x45` remains **DOC+MIS/HIGH**: 30 is directly written; 45 is obtained by direct footprint measurement.

### Remaining G3↔G4 work

Identity and section layers are closed. Remaining work is geometric around the fixed line:
1. determine orientation of each rectangular/wide footprint on G3 and compare with G4;
2. for P10/P13/P15/P20/P22/P26/P29 classify risega as unilateral/bilateral/other and identify retained face(s);
3. determine `dN/dS/dE/dW` from the fixed line at both levels;
4. update physical beam attachment offsets where footprint changes;
5. only after those checks create verified G3–G4 vertical column geometry for ETABS/EdiLus.

Historical 27 vertical chains remain `PREDOC_GEOMETRICO` recovery aids only.

## Architectural perimeter state

TAV-04 architectural is now recovered and visually inspected. Its overall building geometry is compatible with the structural G4 layout, so the former source-access/visual-inspection residual is superseded.

What remains open is **exact co-registration**, not source availability. Until TAV-04ARCH is geometrically registered to TAV-05S, do not promote individual supports to `ANGLE/FACADE/INTERNAL` and do not apply the exterior-corner/exterior-edge fixed-line rule to final coordinates.

Current residual: `RES-G4-ARCH-001` in `memory/OPEN_RESIDUALS.csv`.

## 3D rules

Never blindly copy a floor.
Use: TypicalFloorGroup → FloorVariant → ElementOverride → LocalTopologyOverride.
Roof G5 is a distinct inclined-geometry domain.

Known storey heights RIF:
- first three intervals: 3.20 m each.
Do not invent later heights.

## Foundation/material notes already consolidated

- reversed-beam/grid foundation; same foundation elevation;
- main foundation section corrected: H 90 cm + 20 cm slab = 110 cm total;
- ground-floor grid filled with inert material, then concrete and screeds;
- slabs 16+4 cm; prestressed joists, 3 strands, 50 cm spacing;
- concrete density RIF 2400 kg/m3.

## Latest audit

Canonical verification report: `memory/VERIFICATION_AUDIT_2026-08-19.md`.
Verdict: **PASS WITH OPEN GEOMETRIC RESIDUALS**.

Any agent continuing from here must reconstruct state from repository memory before asking the user to reproduce a source or before rebuilding an artifact already indexed. Search repository + immutable history + File Library recovery pointers + targeted GitHub Actions source renderer before declaring an elaborato missing or inaccessible.
