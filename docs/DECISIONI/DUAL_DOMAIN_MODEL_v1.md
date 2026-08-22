# DECISIONE — Dual Domain Model: AS_BUILT vs HISTORICAL_CALC

**Date:** 2026-08-16  
**Status:** APPROVED  
**Authority:** User (structural engineer)

---

## Foundational Distinction (RIF)

> Non dobbiamo usare il modello storico di calcolo come inventario completo dell'edificio reale.

Two independent domains:

### AS_BUILT_STRUCTURAL_DOMAIN
Ciò che appartiene all'organismo strutturale ricostruito dalle evidenze.
Includes: graphic documentation, physical inspection, technician knowledge, any evidence of existence.

### HISTORICAL_CALCULATION_DOMAIN
Ciò che è effettivamente rappresentato nei calcoli originari disponibili.
May be incomplete, may exclude real structural elements.

## Element Property

Every element can independently declare:

```
historicalCalculationCoverage = INCLUDED | EXCLUDED | NOT_FOUND | UNRESOLVED
```

This does NOT alter:
- `physicalExistence`
- `documentaryStatus`
- `verticalExtent`
- `epistemicStatus`

## Terrace Region (Updated)

```
TerraceRegion
  elevationRelative       = +3.20 m        [RIF]
  structuralRole          = TERRACE        [RIF]
  historicalCalcCoverage  = EXCLUDED       [RIF]

  supporting pillars:
    N002                   [identified]
    N005                   [identified]
    N039                   [identified]
    fourth position/N041   [identity gap]

  pillars vertical extent:
    piano zero → G1        [RIF]

  terrace slab:
    physical existence     = RIF
    historical calculations = EXCLUDED [RIF]
    geometry               = da documentare
    thickness/type         = da recuperare
    reinforcement          = da recuperare
```

## Diagnostic Value

> «Questo elemento è presente nell'edificio/documentazione grafica ma non è rappresentato nei calcoli storici disponibili.»

This is NOT a gap to hide. It is a **diagnostic finding** that must:
1. Emerge nel fascicolo professionale
2. Guidare la costruzione del nuovo FEM
3. Diventare il primo caso concreto della differenza tra modello reale e modello storico

## Consequence for FEM

When building the analysis model:
1. **Modello dello stato di fatto reale** (from all evidence)
2. **Confronto con modello/calcoli storici** (historical calculation domain)
3. **Differenze** (diagnostic findings)
4. **Nuovo modello FEM giustificato dalle evidenze**

## Search Strategy Consequence

**N041 must NOT be searched primarily in calculations.**

Correct path:
```
carpenteria originale → regione terrazza → pilastri + solaio → geometria/sigle/quote
→ confronto con piani superiori → CSM
```

Separately:
```
elemento terrazza → ricerca nei calcoli → assenza → historicalCalculationCoverage = EXCLUDED
```
