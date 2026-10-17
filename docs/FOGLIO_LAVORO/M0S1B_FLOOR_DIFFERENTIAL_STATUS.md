# M0-S1B: Floor Differential Analysis — Status

**Gate:** M0-S1B  
**Date:** 2026-08-16  
**Status:** BLOCKED (data extraction required)

---

## Data Gap

The user confirmed: **G1-G4 are NOT identical — beam differences exist between floors.**

However, the per-level beam data is only available in the scanned carpenteria PDFs (TAV-02S through TAV-05S), which are image-only documents.

### Available data sources

| Source | Per-level? | Coverage |
|---|---|---|
| `telaio_5.csv` | YES (DOC) | Telaio 5 only (C1-C8) — G1-G4 identical |
| `opensees_m0_geometry.py` | YES | Telaio 5 only — G1-G4 identical |
| TAV5 DXF | NO | Single planimetric view |
| v25 CSVs (13 files) | NO | No level column |
| `SCHEDA_ASSOCIAZIONE_STRUTTURALE_v11.csv` | NO | 38 beams `DA_ASSEGNARE` |
| **TAV-02S through TAV-05S** | **YES** | **Scanned images — not yet read** |

### The 30+ beams with differences

Telaio 5 accounts for 8 beams (C1-C8). The remaining 30+ beams across the floor plan have no per-level data. These are the beams that differ between G1-G4.

## Automatic extraction result: BLOCKED

OCR (Tesseract 300 DPI, ita+eng) on all 4 carpenteria PDFs extracted **only cartiglio text** — zero beam labels, zero section dimensions, zero structural annotations.

**Root cause:** The original drawings are scanned at low resolution/contrast. The structural content (beam labels, section dimensions, column positions) is purely graphical — no text layer, no OCR-readable annotations.

**Implication:** The system cannot automatically extract per-level beam data from these PDFs with current tools.

## What CAN be done

1. **Manual entry**: Technician provides the key differences (which beams change between floors)
2. **Higher-quality scan**: If better scans exist somewhere
3. **AI image analysis**: Use a vision-capable model (not available in current environment)
4. **Vectorization**: Convert scanned drawings to DXF (specialized tool, not available)

## Recommendation

Since the user has already visually confirmed that G1-G4 have different beams, the most efficient path is:

**Ask the user to provide ONLY the specific differences** — not a full comparison, but a targeted list of which beams change and what the new sections are. This is the minimal human input needed to complete the Floor Difference Matrix.

Example of what we need:
```
B17: G1=25×70, G4=30×45 (SECTION_CHANGE)
B23: G1=20×45, G3=removed (BEAM_REMOVED)
```

## Conceptual model (from DECISIONI/M0S_PIANO_TIPO_MODEL_v1.md)

```
TypicalFloorGroup
  ├── FloorVariant
  │     └── ElementOverride
```

Precedence: `ELEMENT_OVERRIDE > FLOOR_VARIANT > TYPICAL_FLOOR_RULE`

## Next steps

1. Attempt OCR on specific beam regions of TAV-02S through TAV-05S
2. If OCR fails on beam sections, escalate to user with specific questions
3. Build Floor Difference Matrix
4. Derive FloorSignatures and propose TYPE_A/TYPE_B
