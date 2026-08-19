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
3. `memory/SOURCE_REGISTRY.csv`
4. `memory/ARTIFACT_INDEX.csv`
5. `memory/OPEN_RESIDUALS.csv`
6. `memory/REGENERATION_RECIPES.csv`
7. `memory/FILE_LIBRARY_RECOVERY.csv`
8. `memory/MEMORY_GATE_STATUS.csv`

Persistence contract:
- immutable originals → Git commit:path + blob SHA;
- canonical text/data → repository path + version/commit;
- derived raster/QA → deterministic regeneration recipe;
- chat/user evidence → repository trace/metadata + recovery pointer until the exact binary is Git-archived;
- `AT_RISK`, uncontracted `RUNTIME_ONLY`, and `CHAT_ONLY` are forbidden by `scripts/check_repository_memory.py`.

Current memory gate: `PASS_WITH_WARNING` only because the original Telaio 5 user JPEG is not pixel-archived in Git. Its structural content is persisted in `evidence/derived/telaio5_plan_trace_v1.svg`, together with dimensions/SHA256 and File Library recovery pointers. This source remains `RIF` and the SVG is not a DOC substitute.

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

TAV-04S can now be recovered without relying on chat/runtime download support:
`git show immutable_commit:path` is executed inside GitHub Actions by `scripts/render_hires_sources.py`, which extracts the native raster and overlapping HiRes tiles. The workflow artifact is then downloadable through the GitHub connector.

Targeted single-source workflow:
- workflow: `.github/workflows/render-hires.yml`
- renderer: `scripts/render_hires_sources.py --source TAV-04S`
- successful run: `32223583877`
- artifact: `9354759992` / `n12-hires-tav04s`
- TAV-04S PDF SHA256: `2b878bcefde54ff2b42bafa2a4fdc8a8420bd71514a7e6966a864f009ade685e`
- native raster SHA256: `46c39e6db16a51b7805db3a2e29b08f47e5809be0ad7d17d7eff5d3533c95b1c`
- native raster: `5732 x 8780 px`
- manifest: `data/canonical/tav04s_hires_render_manifest_v1.csv`

Therefore TAV-04S is not an access residual anymore. The same targeted workflow is the preferred recovery mechanism for future immutable binary source PDFs.

## Current G4 baseline

TAV-05S topology is the current best consolidated planar baseline.

Support census: 34 supports including distinct `P22P` = 22'.
Current support registry: `data/canonical/tav05_fixed_lines_numeric_v7.csv`.
Important caveat: the numeric points in that registry were produced before the latest semantic reaudit of construction fixed lines. They remain usable as measured graphic references, NOT automatically as final construction fixed lines.

Wide supports:
- P18 = 30x110, long side X
- P23 = 30x110, long side X
- P30 = 30x110, long side Y

P22P is distinct from P22.

## Fixed-line semantic rule — RIF canonical working rule

- corner column: fixed line normally at the exterior corner;
- facade column: fixed line normally at the midpoint of the exterior edge;
- internal column: fixed-line position only from documentary evidence;
- vertical fixed line remains aligned between storeys unless explicit documentary evidence says otherwise;
- section reductions/riseghe change the footprint about the fixed line, not the fixed-line coordinate.

Do not overwrite measured graphic references until role/perimeter is verified on source drawings.

## Telaio 5 — closed identity / 1D binding

Historical path:
`S → S' → T → U → V → Z → A' → B' → C'`

Verified G4 support binding:
`P17 → P18 → P19 → P20 → P21 → P22 → P22P → P23 → P24`

Documental 1D stations:
`0.00 / 4.70 / 8.75 / 9.95 / 15.75 / 18.65 / 19.85 / 23.90 / 28.60 m`

Hard gate: total projected extent = `28.60 m`.

These dimensions are projected/station dimensions along the historical reference, not necessarily Euclidean lengths of the polyline segments in plan. Previous direct Euclidean residual comparisons are superseded as a validation method.

Persistent evidence aid:
- `evidence/derived/telaio5_plan_trace_v1.svg`
- original current JPEG metadata: 1152×1536 px; SHA256 `6961c6f0d16f51a98488726cce770687f3baf162cfd0581e342014883d38c041`.

## G3↔G4 rebinding — support identity and sections complete

TAV-04S has been visually recovered and read at native resolution. All 34 G4 supports have a same-number, same-plan-position support on G3, including distinct `P22P = 22'`.

Canonical complete crosswalk:
- `data/canonical/g3_g4_support_crosswalk_v1.csv`
- `data/canonical/g3_support_sections_tav04s_v1.csv`

G3 support sections read from TAV-04S are complete for P01–P33 + P22P.

Section changes G3 → G4 occur only at:
- P10: `30x50 → 30x45`
- P13: `30x50 → 30x45`
- P15: `30x50 → 30x45`
- P20: `50x50 → 40x40`
- P22: `30x50 → 30x45`
- P26: `30x50 → 30x45`
- P29: `30x50 → 30x45`

All other support sections remain unchanged between G3 and G4.

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

For P18 and P21 one dimension is confirmed by direct label and the second by direct graphic measurement of the footprint against the labelled dimension; evidence is `DOC+MIS`, not silently promoted to pure DOC.

### Remaining G3↔G4 work

The former source/section block is closed. Remaining work is geometric around the fixed line:
1. determine orientation of each rectangular/wide footprint on G3 and compare with G4;
2. for P10/P13/P15/P20/P22/P26/P29 classify risega as unilateral/bilateral/other and identify retained face(s);
3. determine `dN/dS/dE/dW` from the fixed line at both levels;
4. update physical beam attachment offsets where footprint changes;
5. only after those checks create verified G3–G4 vertical column segments for ETABS/EdiLus.

Historical 27 vertical chains remain `PREDOC_GEOMETRICO` recovery aids only; they are no longer needed to establish G3/G4 support identity or section, but may still help cross-check fixed-line continuity.

## Architectural perimeter residual

Candidate pairing for G4 perimeter cross-check: TAV-04 architectural drawing, inferred from documentary ordering. This pairing is `INF/HIGH`, not DOC until visually verified.

Do not promote roles ANGLE/FACADE/INTERNAL without the perimeter check. This residual does not block structural G3↔G4 risega analysis where the fixed line is directly visible/documented.

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

## Continuity requirement

Any agent continuing from here must reconstruct state from repository memory before asking the user to reproduce a source or before rebuilding an artifact already indexed. Search repository + immutable history + File Library recovery pointers + targeted GitHub Actions source renderer before declaring an elaborato missing or inaccessible.
