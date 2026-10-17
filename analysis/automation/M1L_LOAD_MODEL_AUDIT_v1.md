# M1-L load-model audit

## Decision

Work item: `M1L-LOAD-MODEL`.

Decision: `PASS_WITH_WATCH`. The current load model is complete as an evidence-aware, parametric schema, not as a numerical calculation input. It preserves historical reconstruction, documented/as-built state and present assessment rules as distinct views.

No numerical permanent load, variable load, environmental action, mass, eccentricity, unit weight or combination factor has been introduced without source authority.

## Canonical premises

- Frozen geometry and member identities: `data/canonical/M0G_GEOMETRY_HANDOFF_v1.json`.
- Sections: `data/canonical/M1S_SECTION_GATE_v1.csv`.
- Materials evidence and residuals: `data/canonical/M1M_MATERIAL_GATE_v1.csv`.
- Reinforcement evidence gate: `data/canonical/M1A_REINFORCEMENT_GATE_v1.csv`.
- Load paths: `data/canonical/M1L_LOAD_PATH_CLASSIFICATION_CURRENT_v1.csv`.
- Historical/as-built deltas: `data/canonical/M1L_HISTORICAL_VS_ASBUILT_LOAD_DELTA_REGISTER_v1.csv`.
- Existing semantic gate: `data/canonical/M1L_LOADS_GATE_v1.csv`.
- PT interface guard: `data/canonical/M1F_GROUND_FLOOR_INTERFACE_CURRENT_v1.csv`.

This cycle did not require a new raster/PDF reading. It used already registered canonical source interpretations and did not elevate a derived render to primary-source authority.

## Provenance treatment

- `DOC`: frozen structural identities, documented architectural zones, eight G5 eave hosts, a-d as-built presence, and the registered existence of historical Telaio 5 G1-G3 line loads.
- `RIF`: PT qualitative build-up, reported 1.50 m eave length, reported outward infill shift and reported historical omissions.
- `INF`: none promoted.
- `INC`: none converted into a numeric value.
- `ND`: numerical historical line loads, layer thicknesses and unit weights, supported areas, tributary geometry, use categories, current action values, masses and combinations.

## Residuals and model guards

1. Recover the numerical RC-P13/v16 historical line-load schedule before reproducing the historical Telaio 5 load input.
2. Establish floor/roof construction layers, thicknesses, unit weights and structurally supported areas.
3. Classify present use zones and adopt the applicable current assessment actions and combination rules explicitly.
4. Complete PT ground-supported-versus-structural transfer; never load the complete fill package by default.
5. Bind balcony, terrace, stair/torrino, eave and roof-special tributary geometry before assigning loads.
6. Cross-register present and historical infill lines before creating line-load, mass or eccentricity deltas.
7. Assemble seismic mass only from traceable numerical load rows and admitted participation rules.

These residuals block numerical load execution and `CALCULATION_MODEL_READY`, but do not block independent foundation topology, section, reinforcement and interface work.
