# Checkpoint — 2026-08-19 — Vertical axes / G4 Z recovery

## Canonical progress

The four critical internal supports P13, P20, P22 and P26 no longer block the analytical vertical model.

### Vertical analytical axes
Canonical release: `data/canonical/g1_g4_vertical_axis_release_v1.csv`.

- P13 M0-G axis: X=16.0458 m, Y=-6.4666 m
- P20 M0-G axis: X=12.3443 m, Y=-1.0045 m
- P22 M0-G axis: X=10.4191 m, Y=-9.3752 m
- P26 M0-G axis: X=8.1467 m, Y=-6.2825 m

Axis identity is carried vertically G1→G4 according to G-15 and the repeated internal reference symbol documented on TAV-02S/TAV-03S/TAV-04S/TAV-05S. Pixel coordinates are NOT transferred between scans by global affine transforms.

### Documentary section histories
- P13: 40x50 → 35x50 → 30x50 → 30x45
- P20: 40x50 → 40x45 → 30x50 → 40x40
- P22: 40x50 → 35x50 → 30x50 → 30x45
- P26: 40x50 → 35x50 → 30x50 → 30x45

P20 G3=30x50 is the corrected canonical reading. P20 G3→G4 is SECTION_RESHAPE, not a simple reduction.

### Vertical model seed
Canonical files:
- `data/canonical/g1_g4_internal_vertical_model_seed_v1.csv`
- `data/canonical/g1_g4_internal_vertical_segments_v1.csv`

Known Z:
- G1 / L1 = 3.20 m
- G2 / L2 = 6.40 m
- G3 / L3 = 9.60 m
- G4 / L4 = ND

Therefore, for each of P13/P20/P22/P26:
- G1→G2 segment = READY, 3.20 m
- G2→G3 segment = READY, 3.20 m
- G3→G4 segment = HOLD_Z_ND

### Footprint / attachment residuals
These no longer block the analytical axis.
- P20 G3-G4 U component is qualified: 30/0 cm → 20/20 cm. C036/P20-P11 U_POS face consequence +20 cm is ready; C035/C043 remain V-dependent.
- P22 G3-G4 U component is qualified: 30/20 cm → 30/15 cm. U_NEG retained; C039/P22-P14 retracts 5 cm; C014/C015 remain V-dependent.
- P13/P26 local face offsets remain explicit non-blocking residuals.

### Internal fixed-line protocol
Use `docs/PROTOCOLLO_FILI_FISSI_INTERNI.md`.
Semantic fixed-line identity, local pixel coordinate, M0-G coordinate and section-face offsets are distinct data layers.

## Current active recovery
The next blocking datum for these four vertical segments is the relative Z of G4/L4.

HiRes renderer has been extended to:
- TAV-05E = `archive/documentazione_originaria/tavola5-2.pdf`
- TAV-06E = `archive/documentazione_originaria/tavola6-2.pdf`

Workflow target: `n12-hires-elevations`.
Current purpose: read documentary vertical dimensions/elevations and close L4 without extrapolating the known 3.20 m intervals.

## Hard prohibitions
- Do not set L4=12.80 m by automatic 3.20 m repetition.
- Do not use global sheet registration to transfer internal fixed-line pixel coordinates.
- Do not recenter section footprints on the analytical joint unless documented/measured.
- Do not let unresolved physical face offsets block already verified analytical axes.
