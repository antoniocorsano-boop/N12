# M0-G-R1: LOCAL VERTICAL TOPOLOGY CORRECTION — Terrace Pillars

**Gate:** M0-G-R1  
**Date:** 2026-08-16  
**Status:** IN PROGRESS  
**Trigger:** New RIF evidence from technician

---

## Evidence

> 4 pilastri (L05 lot group: N002, N005, N041, N039) si fermano al primo livello di impalcato, a quota relativa +3.20 m dal piano zero; l'impalcato sovrastante costituisce una terrazza.

**Status:** RIF (referenced from technician visual inspection + image)

## Identification

L05 lot group = 4 pillars in north-east zone:
- N002: x=36501, y=12234 (chain X09-Y05)
- N005: x=36511, y=7840 (chain X09-Y02)
- N041: **NOT IN CANONICAL DATA** (data gap)
- N039: x=36501, y=17276 (chain X09-Y09) — NOTE: position suggests north-east but y=17276 is actually north of N002

## Correction Delta

### Before (GR6 baseline at commit c5360c3)

| Metric | Count |
|---|---|
| StructuralNode3D | 130 |
| Column segments | 104 |
| Horizontal members | 80 |

### Elements to REMOVE

| Type | IDs | Count |
|---|---|---|
| Nodes G2-G5 | N3D-0127..0130 (N002), N3D-0017..0020 (N005), N3D-0102..0105 (N039) | 12 |
| Column segments | VM-0101..0104 (N002), VM-0013..0016 (N005), VM-0081..0084 (N039) | 12 |
| Horizontal members | HM-0018,0034,0050,0066 (N001-N002), HM-0025,0041,0057,0073 (N031-N039) | 8 |

### Elements to MODIFY

| Type | IDs | Change |
|---|---|---|
| G1 terminal nodes | N3D-0126 (N002), N3D-0016 (N005), N3D-0101 (N039) | structuralRole=TERM, continuesAbove=false, terminationLevel=G1 |

### After

| Metric | Count | Delta |
|---|---|---|
| StructuralNode3D | 118 | -12 |
| Column segments | 92 | -12 |
| Horizontal members | 72 | -8 |

## Data Gaps

| Gap | Description | Priority |
|---|---|---|
| N041 missing | Chain N041 not in canonical data. Needs identification/inclusion. | HIGH |
| N005 orphan | After correction, N005/G1 has zero connections (no beams, no columns). Verify if intentional. | MEDIUM |
| Terrace beams | Beams at G1 supporting the terrace floor are NOT removed (they remain at G1). Need verification. | MEDIUM |

## Consequence for FEM

Removing these 12 nodes and 12 segments prevents the FEM from generating non-existent pillars above the terrace. The OpenSees script must be updated to skip these chains at G2+.

## Removal Order (to avoid topology violations)

1. Remove 8 horizontal members
2. Remove 12 column segments  
3. Remove 12 nodes
4. Modify 3 G1 terminal nodes
