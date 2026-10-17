# F4 — Sezioni e armature M0-S / M0-A

Stato: `NOT STARTED`

## Scope

Assegnazione sezioni puntuali (pilastri e travi per ogni elemento) e armature a tutti gli elementi del modello globale. Gate M0-S (sezioni) e M0-A (armature).

## Evidenze disponibili

| Fonte | Stato | Contenuto |
|-------|-------|-----------|
| docs/REGISTRO_MASTER.md (SEC-001) | DOC | Sezioni note: 20×45, 25×70, 30×45, 30×65, 120×20, 140×20 cm |
| docs/REGISTRO_MASTER.md (SEC-002) | ND | T1 G2 sezione non congelata |
| data/canonical/pillar_section_assignment_status.csv | ND | Assegnazione sezioni pilastri: non completata |
| data/canonical/fem_section_placeholders.csv | PLACEHOLDER | Sezioni geometriche provvisorie FEM |
| data/canonical/telaio_5.csv | DOC | Sezioni T5: 20×45, 25×70+140×20 per livello |
| docs/REGISTRO_MASTER.md (COL-002..003) | DOC-famiglia | Famiglie pilastri 40×50/40×40 corpo, 30×40 torrino |
| docs/DECISIONI/M0S_PILASTRI_TAV7_GATE_v1.md | IN CORSO | Gate assegnazione pilastri TAV.7 |

## Pre-requisiti (non soddisfatti)

- M0-G completato e validato.
- TAV.7 estratto e verificato per corrispondenza tipo pilastro ↔ catena.
- 27 catene con assegnazione univoca sezione puntuale.

## Mancante

- Assegnazione univoca sezione puntuale per ciascuna delle 135 posizioni pilastro.
- Orientamento (rotazione) di ciascuna sezione pilastro.
- Sezioni travi per tutti gli elementi (non solo T1 e T5).
- Armature longitudinali e traverse per ogni sezione.
- Verifica completezza armature rispetto a minimum normativi.

## Residui

| ID | Tipo | Descrizione |
|----|------|-------------|
| R-1A-06 | BLOCCANTE | Sezioni puntuali pilastri 40×50/40×40/30×40 per catena e livello |

## Prossima azione

Completare M0-G, poi estrarre sagome documentali da TAV.7 e verificare corrispondenza univoca tra tipi di pilastro e 27 catene. Solo casi univoci → DOC; altri → ND/INC.
