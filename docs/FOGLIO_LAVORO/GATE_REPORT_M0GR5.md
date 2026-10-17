# Gate Report M0-GR5 — Vertical Geometry, Storeys & Elevation Resolution

Versione: `GR-M0G-0005` — 2026-08-17

## Scope

Costruzione della geometria verticale canonica con distinzione rigorosa tra livello strutturale, quota relativa, interpiano, quota assoluta e Z analitica futura.

## A. Semantic Gate (GR5.7) — Che cosa rappresenta un PhysicalNode GR4?

**RISPOSTA: Un PhysicalNode GR4 e una posizione planimetrica (X/Y) nella carpenteria. NON e un nodo strutturale tridimensionale.**

### Evidence

1. `nodes.csv` non ha colonna Z — e puramente planimetrico
2. `tav5_topology_nodes_57.csv` ha solo X/Y
3. `CATENE_VERTICALI_PILASTRI_v20.csv` definisce 27 catene verticali che si estendono attraverso TUTTI i livelli
4. `telaio_5.csv` definisce 5 livelli (G1-G5) con nodi diversi per livello
5. Il FEM script (`opensees_m0_geometry.py`) genera Z come `level_index * 3.20m`

### Implicazione ontologica

La topologia 3D dovrà generare:

```
PhysicalPosition (X/Y) × StructuralLevel → StructuralNode3D
```

e NON semplicemente aggiungere Z all'oggetto GR4.

Il modello 3D conterra':
- **Fino a 550 nodi** (110 posizioni × 5 livelli), ma molti livelli non hanno nodi in tutte le posizioni
- **Pilastri** che attraversano tutti i livelli (27 catene documentate)
- **Travi** che collegano nodi allo stesso livello
- **Possibili eccezioni**: pilastri che iniziano/terminano, torrino, variazioni di pianta

## B. Inventario fonti verticali (GR5.1)

### Primary Sources

| Source | Content | Evidence Status | File |
|--------|---------|-----------------|------|
| `storey_height_status.csv` | h = 3.20m estradosso-estradosso | RIF | data/canonical/ |
| `CATENE_VERTICALI_PILASTRI_v20.csv` | 27 vertical pillar chains | VER | v25 archive |
| `telaio_5.csv` | 5 levels (G1-G5) with sections | DOC | data/canonical/ |
| `M0G_CORREZIONE_ALTEZZA_INTERPIANO_320_v1.md` | Decision record for 3.20m | CHIUSO | docs/DECISIONI/ |

### Secondary Sources

| Source | Content | Evidence Status |
|--------|---------|-----------------|
| `opensees_m0_geometry.py` | FEM model derives Z from 3.20m | (inherits RIF) |
| `M0G_RESOLUTION_MATRIX.csv` | 285 Z resolutions (all RIF, derived) | RIF |
| `CATENE_QUOTE_CANDIDATE_TAV5_v10.csv` | Candidate dimensional chains | INF |
| `SCHEDA_QUOTE_TAV5_v09.csv` | Horizontal dimensions (all DA_VALIDARE) | INC |

### Missing Sources

| Expected | Status |
|----------|--------|
| Sections with absolute elevations | NOT FOUND in v25 archive |
| Prospetti (elevations) | NOT FOUND |
| Original drawings with Z quotes | NOT FOUND |
| TAV20_ABACO_VERTICALE_PILASTRI.dxf | EXISTS in v25 but not yet inspected |

## C. Definizione livelli (GR5.2)

### 5 Structural Levels Identified

| levelId | ordinal | documentAliases | structuralRole | evidenceStatus |
|---------|---------|-----------------|----------------|----------------|
| G1 | 1 | G1 (telaio_5.csv) | Ground floor | DOC |
| G2 | 2 | G2 (telaio_5.csv) | First floor | DOC |
| G3 | 3 | G3 (telaio_5.csv) | Second floor | DOC |
| G4 | 4 | G4 (telaio_5.csv) | Third floor | DOC |
| G5 | 5 | G5 (telaio_5.csv) | Fourth floor | DOC |

### Level Evidence Chain

- **5 levels** documented in `telaio_5.csv` (DOC, from relazione_calcolo)
- Levels are identified by name (G1-G5) in the calculation report
- No other level naming conventions found in the archive
- No conflicting level definitions found

## D. Le quattro quantita' (GR5.3)

### A. storeyHeight

| Claim | Value | Source | Evidence Status |
|-------|-------|--------|-----------------|
| h_piano | 3.20m (3200mm) | storey_height_status.csv | RIF |
| h_piano | estradosso-estradosso | storey_height_status.csv | RIF |
| h_piano | Costante per tutti i 5 livelli | M0G_CORREZIONE_ALTEZZA_INTERPIANO_320_v1.md | RIF |

### B. relativeElevation (Z relative)

| Level | Z_relative | Derivation | Evidence Status |
|-------|-----------|------------|-----------------|
| G1 | 0.00m | Datum (implicit) | RIF |
| G2 | +3.20m | G1 + 3.20m | DERIVED_BY_RULE |
| G3 | +6.40m | G2 + 3.20m | DERIVED_BY_RULE |
| G4 | +9.60m | G3 + 3.20m | DERIVED_BY_RULE |
| G5 | +12.80m | G4 + 3.20m | DERIVED_BY_RULE |

### C. absoluteElevation

| Level | Z_absolute | Source | Evidence Status |
|-------|-----------|--------|-----------------|
| G1 | ND | — | ND |
| G2 | ND | — | ND |
| G3 | ND | — | ND |
| G4 | ND | — | ND |
| G5 | ND | — | ND |

**Le quote assolute NON esistono in nessuna fonte.**

### D. analyticalZ

Non ancora creato. Sara' generato quando il modello FEM verra' istanziato.

## E. Il valore 3.20m — analisi (GR5.4)

### Dove compare

1. `storey_height_status.csv` — unica riga, valore 3.20m
2. `M0G_CORREZIONE_ALTEZZA_INTERPIANO_320_v1.md` — decisione congelata
3. `opensees_m0_geometry.py` — `DEFAULT_STOREY_HEIGHT_M = 3.20`
4. `M0G_RESOLUTION_MATRIX.csv` — 285 righe con Z derivate da 3.20m
5. Gate reports — referenze testuali

### A quali livelli si applica

Tutti e 5 (G1-G5). Il dato e costante.

### Eccezioni

Nessuna eccezione trovata.

### Significato

**estradosso-estradosso** (dal soffitto del livello inferiore al soffitto del livello superiore). Non e chiaro se sia:
- pavimento-pavimento
- massetto-massetto
- altro

Questo e un **residuo aperto**: il significato esatto dell'interpiano va verificato sulle fonti originali.

### Promozione a DOC

Non possibile senza verifica su sezioni/prospetti originali. Il dato rimane RIF.

## F. Associazione nodi-livelli (GR5.6)

### 27 Catene Verticali

`CATENE_VERTICALI_PILASTRI_v20.csv` definisce 27 catene verticali (pilastri) che attraversano tutti i livelli. Ogni catena:
- Ha una posizione X/Y fissa
- E identificata da un'intersezione assi (es. X07-Y05)
- Attraversa G1-G5 (ma la continuita' non e ancora verificata)
- Ha stato VER (da verificare su TAV7)

### Mapping XY × Livello

```
27 catene × 5 livelli = 135 punti strutturali potenziali
```

Ma:
- Non tutti i 110 PhysicalNodes di GR4 sono pilastri
- Alcuni nodi sono travi/intersezioni che esistono solo ad un livello
- La geometria varia per livello (telaio_5.csv mostra sezioni diverse)

### Cosa significa

I 110 PhysicalNodes GR4 sono **posizioni planimetriche**. La topologia 3D sara':
- 27 pilastri × 5 livelli = 135 nodi pilastro
- + nodi trave/intersezione per livello
- Totale stimato: 200-400 nodi 3D (da verificare)

## G. Output GR5 (GR5.8)

### Livelli

| Livello | Ordinal | Alias | Ruolo | Z_relative | Z_absolute | Status |
|---------|---------|-------|-------|-----------|-----------|--------|
| G1 | 1 | G1 | Ground | 0.00m | ND | DOC (livello) / RIF (quota) |
| G2 | 2 | G2 | First | +3.20m | ND | DERIVED |
| G3 | 3 | G3 | Second | +6.40m | ND | DERIVED |
| G4 | 4 | G4 | Third | +9.60m | ND | DERIVED |
| G5 | 5 | G5 | Fourth | +12.80m | ND | DERIVED |

### Interpiani

| Da | A | Distanza | Fonte | Status |
|----|---|----------|-------|--------|
| G1 | G2 | 3.20m | storey_height_status.csv | RIF |
| G2 | G3 | 3.20m | DERIVED | DERIVED_BY_RULE |
| G3 | G4 | 3.20m | DERIVED | DERIVED_BY_RULE |
| G4 | G5 | 3.20m | DERIVED | DERIVED_BY_RULE |

### Quote

| Tipo | Status |
|------|--------|
| Relative | RIF (da 3.20m constante) |
| Assolute | ND (nessuna fonte) |
| Analytical | NON ANCORA CREATO |

### Nodi associabili ai livelli

| Tipo | Count | Status |
|------|-------|--------|
| Pilastri (catene verticali) | 27 × 5 = 135 | VER (da verificare su TAV7) |
| Posizioni planimetriche GR4 | 110 | XY noti, Z da istanziare |
| Nodi 3D | ~200-400 (stimati) | NON ANCORA CREATI |

## H. Human Queue

| Item | Description | Priority |
|------|-------------|----------|
| Significato estradosso-estradosso | Verificare se 3.20m e pavimento-pavimento o altro | HIGH |
| TAV20_ABACO_VERTICALE | Ispezionare DXF verticale pilastri per quote assolute | HIGH |
| Continuita' pilastri | Verificare se tutti i 27 pilastri attraversano G1-G5 | MEDIUM |
| Variazioni di pianta | Verificare se la pianta cambia tra livelli | MEDIUM |
| Quote assolute | Cerca su sezioni/prospetti/tavole originali | MEDIUM |

## I. Delta Summary

| Metrica | Prima GR5 | Dopo GR5 |
|---------|-----------|----------|
| Livelli strutturali | ? | **5** (G1-G5, DOC) |
| Interpiani documentati | 0 | **0** |
| Interpiani derivati | 0 | **4** (da 3.20m RIF) |
| Quote relative | ND | **RIF** (0, 3.20, 6.40, 9.60, 12.80m) |
| Quote assolute | ND | **ND** (nessuna fonte) |
| Significato PhysicalNode GR4 | ? | **Posizione planimetrica** |
| Topologia 3D | ? | **PhysicalPosition × Level → Node3D** |
| Nodi 3D potenziali | 0 | **~200-400** (stimati) |

## Controlli eseguiti

| Check | Result |
|-------|--------|
| Fonti verticali inventariate | PASS |
| 5 livelli definiti | PASS |
| 4 quantita' distinte (storeyHeight/relative/absolute/analytical) | PASS |
| 3.20m trattato come claim | PASS |
| Significato PhysicalNode GR4 determinato | PASS |
| Mapping XY × Level registrato | PASS |
| Nessuna promozione automatica | PASS |

## Verdetto

**M0-GR5: PASS.**

Conosciamo i livelli (5), sappiamo quali distanze verticali conosciamo (una: 3.20m RIF), da quali fonti (storey_height_status.csv), quale datum utilizziamo (G1=0 implicito), quali quote sono documentate/derivate (tutte relative, nessuna assoluta), e come la topologia XY dovrà essere istanziata verticalmente (PhysicalPosition × Level → StructuralNode3D).

**Prossimo passo**: GR6 — Assemblaggio e verifica M0-G. Prima geometria globale tridimensionale canonica, confrontata visivamente contro le fonti.
