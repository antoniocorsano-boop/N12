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

Important correction: these dimensions are projected/station dimensions along the historical reference, not necessarily Euclidean lengths of the polyline segments in plan. Previous direct Euclidean residual comparisons are superseded as a validation method.

Persistent evidence aid:
- `evidence/derived/telaio5_plan_trace_v1.svg`
- original current JPEG metadata: 1152×1536 px; SHA256 `6961c6f0d16f51a98488726cce770687f3baf162cfd0581e342014883d38c041`.

Key files:
- `data/canonical/telaio5_support_mapping_verified_v1.csv`
- `data/canonical/telaio5_station_support_binding_v1.csv`
- `data/canonical/telaio5_projection_dimension_policy_v1.csv`
- `data/canonical/telaio5_projection_stations_v1.csv`

## G3↔G4 rebinding

G3 source is NOT missing. Canonical source is TAV-04S `tavola4-2.pdf`, historical blob `7807c32f52e8d6fcefad8abe7eac79ad9dd65efa` at immutable commit `d521f11...`.

Current crosswalk scaffold:
`data/canonical/g3_g4_support_crosswalk_v1.csv`

Historical 27 vertical chains exist and are `VER_5_LEVELS` but `PREDOC_GEOMETRICO`; they are recovery aids only and must not be auto-mapped to current P01–P33/P22P.

### Telaio 5 vertical binding now closed as scaffold

The historic multipiano frame proves that G3 and G4 share the same nine named alignments `S-S'-T-U-V-Z-A'-B'-C'`. Combined with the verified G4 mapping, the vertical alignment scaffold is now fixed as:
`P17-P18-P19-P20-P21-P22-P22P-P23-P24` across G3↔G4.

Canonical files:
- `data/canonical/g3_g4_telaio5_vertical_binding_v1.csv`
- `data/canonical/g3_g4_telaio5_vertical_binding_gate_v1.csv`

Evidence level: `RIF+DOC / HIGH` for vertical identity of the alignment only. This does NOT propagate G4 section, centroid, footprint or role into G3.

Still pending from TAV-04S visual reading:
1. G3 section for each of the nine supports;
2. orientation and footprint around the fixed line;
3. risega/section-change classification;
4. beam attachments to physical faces;
5. final G3 fixed-line coordinates where the source gives a stronger construction reference.

Current environment limitation: GitHub connector exposes the immutable PDF identity/blob but rejects binary content; current runtime network cannot resolve GitHub raw URLs; File Library search did not locate an indexed `tavola4-2.pdf` copy. This is an environment-access block, not a missing project source.

Next structural action:
- continue source recovery for a visual TAV-04S rendering without asking the user to reproduce work;
- in parallel extend frame-specific G3↔G4 vertical bindings only where historic frame identity independently proves continuity;
- never propagate sections/footprints without DOC source reading.

## Architectural perimeter residual

Candidate pairing for G4 perimeter cross-check: TAV-04 architectural drawing, inferred from documentary ordering. This pairing is `INF/HIGH`, not DOC until visually verified.

Do not promote P17–P24 roles ANGLE/FACADE/INTERNAL without the perimeter check. This residual does not block G3↔G4 structural rebinding.

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

Any agent continuing from here must reconstruct state from repository memory before asking the user to reproduce a source or before rebuilding an artifact already indexed. Search repository + immutable history + File Library recovery pointers before declaring an elaborato missing.
