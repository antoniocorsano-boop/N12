# DECISIONE — M0-S1B: Modello Concettuale Piano Tipo

**Gate:** M0-S1B  
**Date:** 2026-08-16  
**Status:** APPROVED  
**Authority:** User (structural engineer)

---

## Finding (RIF)

> G1–G4 non sono identici: esistono differenze nelle travi tra gli impalcati.

**Evidence status:** RIF (referenced from technician visual inspection)  
**Source:** User visual comparison of TAV-02S through TAV-05S via Streamlit viewer

## Conceptual Model Update

### Old model (INCORRECT)

```
TypicalFloorGroup → tutti gli elementi identici
```

### New model (CANONICAL)

```
TypicalFloorGroup
  ├── FloorVariant
  │     └── ElementOverride
```

**Hierarchy:** `TYPICAL_FLOOR_RULE → FLOOR_VARIANT → ELEMENT_OVERRIDE`

**Precedence:** `ELEMENT_OVERRIDE > FLOOR_VARIANT > TYPICAL_FLOOR_RULE`

### Implications

1. Two levels can share the same TypicalFloorGroup even if some beams differ
2. Don't duplicate full floor definitions — represent common properties + overrides
3. If G1 and G2 share 35 beams and differ on 3: represent `TYPE_A` with common properties + `G2 FloorVariant` with 3 overrides
4. Differences are documented, not deduced

## Floor Difference Matrix Schema

| Element | G1 | G2 | G3 | G4 | Difference |
|---|---|---|---|---|---|
| Bxxx | section | section | section | section | SAME/SECTION_CHANGE/GEOMETRY_CHANGE/BEAM_ADDED/BEAM_REMOVED/TYPE_CHANGE/LABEL_CHANGE/UNRESOLVED |

## FloorSignature

```
FloorSignature = topology + beam layout + beam types + column layout + documentary references
```

Compare G1–G4 → determine:
- Common core
- Systematic differences
- Local exceptions

Only then propose: `TYPE_A`, `TYPE_B`, `FloorVariant`, `ElementOverride`.

**Proposal remains `CANDIDATE` until supported documentally.**

## Operational Rule

**Never ask the user to compare drawings manually.** The system must:
1. Detect differences automatically
2. Retrieve relevant documents
3. Present findings with evidence
4. Only ask the user when it cannot resolve a conflict

## Consequence

M0-S1B requires automatic beam extraction from the 4 carpenteria PDFs (TAV-02S through TAV-05S). Since these are scanned images, the system must:
1. Use DXF vector data (TAV5) as primary source
2. Cross-reference with v25 archive files
3. Use OCR selectively on specific regions of interest
4. Present a Floor Difference Matrix to the user for validation
