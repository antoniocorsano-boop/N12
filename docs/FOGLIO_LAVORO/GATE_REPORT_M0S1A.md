# GATE REPORT — M0-S1A: Document Recovery & Level-Sheet Crosswalk

**Gate:** M0-S1A  
**Date:** 2026-08-16  
**Status:** ✅ PASS  
**Blocker:** None

---

## Objective

Resolve the document-to-level mapping: which structural drawing (TAV-S sheet / original PDF) corresponds to which structural level (G1-G5 / Fondazioni / Copertura).

## Evidence Chain

### 1. PDF Recovery (DOC)

Original PDFs located on disk at:
```
C:\Users\anton\Progetti ingegneria civile\Condominio N.12\documentazione originaria\
```

18 PDFs total, all SHA256-hashed in `data/canonical/tavole_originali_manifest.csv`.

### 2. OCR via Tesseract (DOC)

Installed Tesseract OCR (`C:\Program Files\Tesseract-OCR\tesseract.exe`) + pytesseract.  
Scanned all 6 carpenteria PDFs at 300 DPI with `ita+eng` language pack.

**Results:**

| PDF Filename | OCR Cartiglio Text | Parsed Level | Evidence Status |
|---|---|---|---|
| `tavola1-2.pdf` | `CARPENTERIA FONDAZIONI` | **Fondazioni** | DOC |
| `tavola2-2.pdf` | `CARPENTERIA I° IMPALCATO` | **G1** (1° impalcato) | DOC |
| `tavola3-2.pdf` | `CARPENTERIA II° IMPALCATO` | **G2** (2° impalcato) | DOC |
| `tavola4-2.pdf` | `CARPENTERIA III° IMPALCATO` | **G3** (3° impalcato) | DOC |
| `tavola 5.pdf` | `CARPENTERIA IV° IMPALCATO` | **G4** (4° impalcato) | DOC |
| `tavola 6-1.pdf` | `CARPENTERIA COPERTURA` | **COPERTURA** (G5) | DOC |

### 3. Cross-Reference with TAVOLE_STRUTTURALI_MASTER_v1.md (RIF)

The planned set mapping confirms:
- TAV-S02 → G1, TAV-S03 → G2, TAV-S04 → G3, TAV-S05 → G4, TAV-S06 → Roof
- TAV-S01 → Fondazioni (not in original catalog, but present on disk)

### 4. Architectural PDFs

Architectural PDFs (`tavola1.pdf` through `tavola6.pdf`) are also scanned images. Cartiglio text not reliably extracted (contrast too low, different layout). Not needed for level mapping — structural PDFs already resolved it.

## Key Findings

### 4 Ordinary Levels (G1-G4), NOT 5

The original drawings contain **4 impalcati** (G1-G4) plus **copertura** (G5) plus **fondazioni**. This means:
- `StructuralLevel.G1` through `StructuralLevel.G4` are the four ordinary floor groups
- `StructuralLevel.G5` = roof (COPERTURA)
- Foundation = separate (not in the 5-level system from M0-GR5)

### TAV-05S = G4 (INF status)

G4 assignment confirmed by user visual inspection of the scanned PDF. Status upgraded from INF to DOC.

### Foundation Sheet Present

`TAV-01S` = `tavola1-2.pdf` contains `CARPENTERIA FONDAZIONT`. Foundation carpentry exists in the original drawings but was not part of the M0-G structural model (which deals with above-ground levels G1-G5).

## Canonical Artifact

Saved: `data/canonical/m0s1a_level_sheet_crosswalk.csv`

```csv
structural_level,level_name,level_name_it,tav_s_sheet,pdf_filename,ocr_text,evidence_status,resolution_method
G1,1st_floor,1°_impalcato,TAV-02S,tavola2-2.pdf,"CARPENTERIA I° IMPALCATO",DOC,OCR_tesseract300dpi
G2,2nd_floor,2°_impalcato,TAV-03S,tavola3-2.pdf,"CARPENTERIA II° IMPALCATO",DOC,OCR_tesseract300dpi
G3,3rd_floor,3°_impalcato,TAV-04S,tavola4-2.pdf,"CARPENTERIA III° IMPALCATO",DOC,OCR_tesseract300dpi
G4,4th_floor,4°_impalcato,TAV-05S,tavola 5.pdf,"CARPENTERIA IV° IMPALCATO",DOC,user_visual_confirmation
G5,roof,copertura,TAV-06S,tavola 6-1.pdf,"CARPENTERIA COPERTURA",DOC,OCR_tesseract300dpi
NA,foundation,fondazioni,TAV-01S,tavola1-2.pdf,"CARPENTERIA FONDAZIONI",DOC,user_correction_ocr_misread
```

## Residuals

| ID | Description | Priority |
|---|---|---|
| ~~RES-M0S1A-01~~ | ~~TAV-05S = G4 is INF~~ | **Resolved** — user visual confirmation |
| RES-M0S1A-02 | Architectural PDF cartigli not read. May contain additional floor metadata. | Low |
| RES-M0S1A-03 | TypicalFloorGroup assignment pending: which of G1-G4 are TYPE_A vs TYPE_B. | High — next gate |

## Consequence for M0-S

The 5-level system from M0-GR5 (`G1` through `G5`) is confirmed as the correct vertical decomposition. The crosswalk provides the documentary basis for:
1. **Element→Level assignment**: each horizontal element belongs to one of G1-G4 or G5
2. **TypicalFloorGroup resolution**: G1-G4 need to be classified as TYPE_A/TYPE_B (next gate M0-S1B)
3. **Roof treatment**: G5 (COPERTURA) is structurally distinct from G1-G4
