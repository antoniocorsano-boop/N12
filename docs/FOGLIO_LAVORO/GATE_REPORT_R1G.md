# Gate Report R1-G — Intelligent Resolution Validation & R1 Freeze

Versione: `GR-0003` — 2026-08-17

## Scope

Validazione semantica di R1-F e freeze della verticale R1.

## G1 — Audit 162 proprietà VALIDATED

### Risultato: PASS

**Pre-fix**: 214 proprietà marcate VALIDATED, di cui 52 con valore `ND` (bug: `lev.section` truthy anche con value `ND`).

**Post-fix**: 162 proprietà VALIDATED, 0 con valore ND/null.

| Categoria | Count | Fonte | Stato |
|-----------|-------|-------|-------|
| Position (27 chains × 5 levels) | 135 | nodes.csv | VER_GEOMETRIC |
| Section (solo T5 con valore reale) | 27 | telaio_5.csv | DOC |

**Catena di tracciabilità** per ogni proprietà:
```
entity.property → value → EV-ID → source → evidence status → resolution rule
```

- 162/162 catene complete
- 0 catene incomplete

**Bug corretto**: Le sezioni con `ND` value venivano classificate come VALIDATED. Fix: `hasRealSection = lev.section && lev.section.value && lev.section.value !== "ND"`.

**Key collision fix**: Le chiavi ora includono chain ID (`position_G1_X07-Y05` invece di `position_G1`). 540 proprietà uniche, 0 duplicati.

## G2 — Audit 81 candidati analogici

### Risultato: PASS

| Metrica | Valore |
|---------|--------|
| Totale candidati | 81 |
| Struttura valida | 81/81 |
| Auto-promozioni | 0 |
| Confidence media | 0.4 (mid) |

**Catena per ogni candidato**:
```
target entity → property → proposed value → source entities → relation/analogy → supporting evidence → confidence → reason
```

**Origini analogiche**:
- X09-Y09: 25 candidati
- X07-Y05: 20 candidati
- X05-Y11: 18 candidati
- X06-Y05: 18 candidati

**Significatività strutturale**: Tutte le analogie sono da catene dello stesso telaio (T5), stesso livello. L'analogia è strutturalmente significativa (stessa famiglia documentale).

**Vincolo rispettato**: Nessun candidato diventa automaticamente canonico.

## G3 — Classificazione 297 UNKNOWN

### Risultato: PASS

| Classificazione | Count | Proprietà |
|-----------------|-------|-----------|
| DOCUMENT_SEARCHABLE | 135 | material (certificati, relazioni di prova) |
| REQUIRES_NEW_EVIDENCE | 135 | reinforcement (calcoli, indagini) |
| DOCUMENT_SEARCHABLE | 27 | section senza analogia (tavole originali) |

**297/297 con searchHint** per orientare la ricerca.

**Distinzione fondamentale**: UNKNOWN non significa "dato assente". Significa "non ancora risolto". La classificazione guida l'azione successiva.

## G4 — Validation Queue semantics

### Risultato: PASS

**Prima**: "Accetta" modificava silenziosamente lo stato locale.

**Dopo**: Ogni azione produce un `ValidationDecision` tracciabile:
```typescript
{
  propertyId, candidateId, candidateValue,
  reviewerDecision: "ACCEPT" | "REJECT" | "DEFER",
  evidenceRefs, previousState, resultingState,
  timestamp, reviewerNote?
}
```

**Decision log**: Visualizzato nella UI, registra ogni decisione con full traceability.

**Vincolo**: La decisione non modifica il dataset canonico. Produce solo una registrazione.

## G5 — Benchmark resolver su M0-G

### Risultato: COMPLEMENTARY (non BLOCKED)

| Requisito M0-G | Copertura R1-F | Gap |
|----------------|----------------|-----|
| Coordinate X/Y (27 catene) | 135/135 VALIDATED | 0 |
| Quote Z (interpiano) | In storey_height_status.csv | Non in resolver |
| 57 nodi topologici | 0/57 | 30 nodi non modellati |
| 141 connessioni candidate | 0/141 | Non in resolver |
| T5↔T5.5 alignment | Parziale | Non verificato |

**Conclusione**: Il resolver R1-F copre 27 chains × 5 levels. M0-G richiede la topologia completa a 57 nodi con connettività. Il resolver complementa M0-G, non lo sostituisce.

## G6 — Knowledge Graph audit

### Risultato: PASS

| Metrica | Valore |
|---------|--------|
| Nodi | 34 |
| Archi | 437 |
| Archi validi | 437/437 |
| Nodi orfani | 0 |
| Archi duplicati | 0 |

**Tipi di nodo**: building (1), level (5), column (27), frame (1)

**Tipi di arco**:
- contains: 167 (building→level, level→column, building→column)
- same_level: 135 (column→level membership)
- same_chain: 108 (vertical continuity within chain)
- same_frame: 27 (column→frame assignment)

**Ogni arco ha**: source, target, type, weight, documented.

## G7 — Document Layer

### Risultato: PASS

| Fonte | Proprietà fornite |
|-------|-------------------|
| nodes.csv | position, axisX, axisY, chainId |
| column_fixed_lines.csv | section, continuity, fixedLine |
| telaio_5.csv | section, spans, development, frame |
| storey_height_status.csv | height |
| pillar_section_assignment_status.csv | section_assignment |
| tav5_topology_nodes_57.csv | topology |
| tav5_topology_connections_v07.csv | connectivity |
| telaio5_tav5_candidate_matrix_v1.csv | alignment |
| fem_section_placeholders.csv | section_fem |

**Property index**: 16 proprietà mappate a fonti.
**Element type index**: 7 tipi elemento mappati a fonti.

## G8 — Metrica UX

### Risultato: PASS

**Prima**: "39% risolto" (ambiguo)

**Dopo**:
- **162/540** validate
- **81/540** candidati
- **297/540** da ricercare

Ciascuna categoria ha significato tecnico profondamente diverso.

## G9 — Freeze checks

| Check | Risultato |
|-------|-----------|
| snapshot:generate | ✓ |
| snapshot:check | ✓ |
| tsc --noEmit | ✓ |
| vite build | ✓ |
| No ND-as-VALIDATED | ✓ |
| Unique keys | ✓ |
| Traceability chains complete | ✓ |
| No auto-promotions | ✓ |
| Decision log traceable | ✓ |
| Knowledge graph valid | ✓ |
| Document layer complete | ✓ |

## Verdetto R1

**R1-A → R1-G: PASS.**

La verticale R1 è completa come capability:

```
R1-A: Workspace professionale + 16 file
R1-B: Matrice artefatti + checklist integrità
R1-C: Dashboard scaffolded (Vite+React+TS)
R1-C2: Snapshot deterministico + drift detection
R1-D: Stato di fatto interattivo (27 catene)
R1-E: Modello strutturale canonic (27 entità, 326 proprietà mancanti)
R1-F: Intelligent evidence resolution (540 proprietà, 162 validate, 81 candidati, 297 da ricercare)
R1-G: Validation & freeze (audit completo, bug fix, tracciabilità)
```

**Catena dimostrata**:
```
documento → evidenza → elemento → proprietà → candidato → decisione umana → modello canonico
```

**Senza promozioni automatiche e senza perdita della provenienza.**

**Prossimo lavoro**: Usare R1 per risolvere M0-G — non più infrastruttura, ma decisioni tecniche reali.
