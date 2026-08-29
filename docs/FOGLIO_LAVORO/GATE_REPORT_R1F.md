# Gate Report R1-F

Versione: `GR-0002` — 2026-08-17

## Scope

Implementazione R1-F: Intelligent Evidence Resolution per il workspace R1.

## Obiettivi

1. Knowledge Graph strutturale (nodi + edges)
2. Document Knowledge Layer (fonti indicizzate per proprietà)
3. Property Resolver (ciclo di vita UNKNOWN → VALIDATED)
4. Validation Queue (interfaccia interattiva per umano)

## Risultati

### Knowledge Graph
- **34 nodi**: 1 building + 5 levels + 27 chains + 1 frame
- **437 edges**: contains, same_chain, same_frame, same_level
- **Fonte**: CSV canonici (nodes.csv, column_fixed_lines.csv, telaio_5.csv)

### Document Knowledge Layer
- **11 fonti** indicizzate per proprietà e tipo elemento
- **Indici**: propertyIndex, elementTypeIndex
- **Fonti CSV**: 9 (canonical)
- **Fonti FOGLIO_LAVORO**: 2 (Registro Evidenze + Residui)

### Property Resolver
- **540 proprietà** totali (27 chains × 5 levels × 4 proprietà)
- **214 validate** (posizione da nodes.csv + sezioni T5)
- **42 candidati** (sezioni non-T5 via analogia stessa-telaio)
- **284 unknown** (materiali + armature — nessuna fonte)
- **Ciclo di vita**: UNKNOWN → CANDIDATES → VALIDATED/REJECTED

### Validation Queue
- **326 elementi** in coda per revisione umana
- **Interfaccia**: filtro per stato, espandi/collassa, accetta/rifiuta
- **Badge**: contatore non-risolte nel tab "Validazione"

## Controlli eseguiti

| Check | Risultato |
|-------|-----------|
| tsc --noEmit | ✓ |
| vite build | ✓ |
| snapshot:check | ✓ |
| generatedAt deterministico (YYYY-MM-DD) | ✓ |
| Nessuna promozione epistemica | ✓ |
| Separazione R1/M0-G mantenuta | ✓ |

## Statistiche PR #9

- **40+ commit** (M0-G + R1-A + R1-B + R1-C + R1-D + R1-E + R1-F)
- **28 evidenze** (canonical count)
- **53 artefatti** (canonical count)
- **16 residui** (canonical count)
- **27 catene** × 5 livelli = **135 entità**

## Note

- **Separazione di competenza**: R1-F risolve proprietà dove esistono fonti analogiche (sezioni T5 → sezioni T5-like). Non risolve materiali/armature (ND) dove non ci sono fonti documentali.
- **Human-in-the-loop**: La Validation Queue richiede intervento umano per:
  - Accettare/rifiutare candidati analogici
  - Definire materiali e armature da indagini future
  - Validare conflitti multi-fonte

## Verdetto

**R1-F: PASS.** Il workspace R1 ora include:
- Visualization (Panoramica, Stato di fatto, Modello)
- Navigation (7 tab con badge)
- Validation (queue interattiva per risoluzione proprietà)
- Export (diagnostico JSON per futuri consumatori)

**Prossimo gate**: R1-G (report finale + documentazione utente)
