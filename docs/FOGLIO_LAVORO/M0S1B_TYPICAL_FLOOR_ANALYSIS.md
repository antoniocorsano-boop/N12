# M0-S1B: TypicalFloorGroup Analysis

**Gate:** M0-S1B  
**Date:** 2026-08-16  
**Status:** OPEN (G4 confirmed DOC, typical floor group pending)

---

## Objective

Classify G1-G4 into TypicalFloorGroup (TYPE_A / TYPE_B / ROOF / UNRESOLVED).

## Evidence

### Structural Data: All G1-G4 Identical

| Property | G1 | G2 | G3 | G4 | G5 (roof) |
|---|---|---|---|---|---|
| Storey height | 3.20 m | 3.20 m | 3.20 m | 3.20 m | 3.20 m |
| T5 beam sections | 25×70 + 140×20 | 25×70 + 140×20 | 25×70 + 140×20 | 25×70 + 140×20 | **20×45** |
| T5 span coverage | C1-C8 | C1-C8 | C1-C8 | C1-C8 | **C2-C7** |
| T5 development | 28.60 m | 28.60 m | 28.60 m | 28.60 m | **19.20 m** |
| Horizontal members | 16 (identical) | 16 (identical) | 16 (identical) | 16 (identical) | 16 (identical) |
| Column arrangement | 27 chains | 27 chains | 27 chains | 27 chains | 27 chains |
| Column sections | ND (all) | ND (all) | ND (all) | ND (all) | ND (all) |

### DXF Text Inventories

- **TAV5**: No floor-type keywords. Only node IDs, beam candidates, metric groups.
- **TAV6**: No level-specific text. Only general reinforcement rules.
- **TAV7**: "pilastri I-V ordine" = type-ordering on sheet, NOT floor levels. "Ultimo piano: pilastri d'angolo ridotti a 40×40" = G5 rule only.

### OpenSees Script

`beam_section_for()` treats G1-G4 identically (levels 0-3). No conditional within that range.

### Original PDF Drawings

Each floor has its own carpenteria sheet (TAV-02S through TAV-05S), but:
- OCR extraction shows only cartiglio text (floor label), not structural content
- The actual structural plans within each PDF have not been read (scanned images)
- Differences between floors (if any) would be visible in the drawings but not yet extracted

## Conclusion

**All extracted evidence shows G1-G4 are structurally identical.** No basis to distinguish TYPE_A from TYPE_B.

Two hypotheses:
1. **Single typical floor**: All 4 ordinary floors share one configuration → `TypicalFloorGroup = TYPE_A` for G1-G4
2. **Unresolved differences**: Differences exist in the scanned PDFs but haven't been extracted → `TypicalFloorGroup = UNRESOLVED` until visual inspection

## Recommendation

Given the user's mandate specifies two groups (TYPE_A + TYPE_B), but all extracted structural data shows G1-G4 are identical:

**G1-G4 = UNRESOLVED** pending:
1. Visual inspection of the 4 carpenteria PDFs to check if beam sections/column types differ between drawings
2. Or technician confirmation that all 4 floors share the same configuration (→ single TYPE_A)

**G4 = DOC confirmed** (user visual inspection: "CARPENTERIA IV° IMPALCATO")

## Residual

| ID | Description | Priority |
|---|---|---|
| RES-M0S1B-01 | G1-G4 TypicalFloorGroup: set to UNRESOLVED pending visual PDF inspection | High |
| RES-M0S1B-02 | G5 = ROOF (confirmed by OCR "CARPENTERIA COPERTURA") | Resolved |
