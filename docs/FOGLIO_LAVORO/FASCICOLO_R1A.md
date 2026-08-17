# Fascicolo R1-A — Workspace Professionale Strutturale

Versione: `R1-A-0001` — 2026-08-17

## Scope

Professional workspace shell for the N12 structural reconstruction. This document is the **workflow orchestrator**: it tracks the eight-stage vertical, the 13 professional fronts, evidence counts, residuals, and next actions. It does NOT contain structural data — all canonical data lives in `data/canonical/` and `docs/REGISTRO_MASTER.md`.

## Workflow Pipeline

```
Progetto → Fonti → Stato di fatto → Modello → Diagnosi → Interventi → Verifica → Post operam → Fascicolo
   F0         F1          F2              F3-F5        F6          F7-F9        F8          F11           F12
```

## Fronti

| Front | Nome | Stato | Prossima azione |
|-------|------|-------|-----------------|
| F0 | Progetto / Committenza | PARTIAL | Formalizzare committenza nel protocollo |
| F1 | Fonti / Quadro Conoscitivo | ADVANCING | Verificare integrità archivio v25 e completezza catalogo |
| F2 | Stato di fatto strutturale | ADVANCING | Completare raccordo 57 nodi topologici e quote Z |
| F3 | Modello globale M0-G | IN CORSO | Normalizzare coordinate e costruire rete globale |
| F4 | Sezioni e armature M0-S/A | NOT STARTED | Completare M0-G prima di assegnare sezioni puntuali |
| F5 | Materiali, conoscenza, carichi M0-M/L | NOT STARTED | Raccogliere dati materiali e definire LC/FC |
| F6 | Diagnosi | BLOCKED | In attesa di M0-G + M0-S completi |
| F7 | Interventi | BLOCKED | In attesa di diagnosi |
| F8 | Verifica normativa M0-V | BLOCKED | In attesa di M0-L e modello validato |
| F9 | Progettazione interventi M1 | BLOCKED | In attesa di M0-V e diagnosi |
| F10 | Esecuzione / Cantiere | N/A | Fuori scope fase R1-A |
| F11 | Post operam | N/A | Fuori scope fase R1-A |
| F12 | Fascicolo finale | BLOCKED | Compilazione ultima dopo tutti i fronti |

## Conteggio evidenze per stato (da Registro Master)

| Stato | Record | Note |
|-------|--------|------|
| DOC / DOC-* | 16 | Tavole, telai, sezioni, fondazioni, modello globale |
| VER / VER-* | 3 | Catene pilastri, altezza interpiano, topologia 27×5 |
| RIF | 1 | Altezza interpiano |
| INF | 2 | Topologia 57 nodi (PREDOC/INF_DA_QUOTARE) |
| ND | 3 | Sezione T1 G2, materiali, conoscenza |
| IN_CORSO | 3 | Allineamento T5, raccordo 57 nodi, coordinate globali |
| PLACEHOLDER | 2 | Sezioni FEM provvisorie (non verificabili) |

## Residui / Bloccanti

| ID | Tipo | Front | Descrizione | Stato |
|----|------|-------|-------------|-------|
| R-1A-01 | BLOCCANTE | F3 | Raccordo 57 nodi topologici a coordinate canoniche | IN ALLINEAMENTO |
| R-1A-02 | BLOCCANTE | F3 | Quote Z definitive (incerte/ND) | ND |
| R-1A-03 | BLOCCANTE | F3 | Connettività globale per livello | IN CORSO |
| R-1A-04 | BLOCCANTE | F3 | Sagome/arretramenti impalcati | ND |
| R-1A-05 | BLOCCANTE | F3 | Raccordo geometrico fondazioni | PARZIALE |
| R-1A-06 | BLOCCANTE | F4 | Sezioni puntuali pilastri 40×50/40×40/30×40 per catena | ND |
| R-1A-07 | BLOCCANTE | F5 | Materiali calcestruzzo/acciaio | ND |
| R-1A-08 | BLOCCANTE | F5 | Livello di conoscenza LC/FC | ND |
| R-1A-09 | RISCHIO | F3 | Allineamento T5 ↔ TAV.5 non verificato | HYP_A_METRICA |
| R-1A-10 | RISCHIO | F2 | Topologia 57 nodi: riferimenti a ID > N057 | INF_DA_QUOTARE |

## Artefatti professionali

Vedi `docs/FOGLIO_LAVORO/MATRICE_ARTEFATTI.md` per la matrice completa.

## Registro Evidenze

Vedi `docs/FOGLIO_LAVORO/REGISTRO_EVIDENZE.md` per il registro contrattuale delle evidenze.

## Prossima azione globale

R1-A-01: Completare raccordo 57 nodi topologici — recuperare o verificare `ABACO_TOPOLOGICO_TAV5_v11.csv` e costruire dataset canonico `nodes.csv` + `vertical_columns.csv` verificato contro TAV.5/TAV.7.

## Regole di questo workspace

1. Ogni dato strutturale riporta stato DOC/MIS/RIF/INF/INC/ND.
2. Nessun PLACEHOLDER/ND viene promosso a DOC per analogia o convenienza.
3. Gli exports/ obsoleti non sono fonte canonica; il file Python è la reference.
4. `nodes.csv` non rappresenta la topologia completa a 57 nodi.
5. Telaio 5 resta HYP_A_METRICA non verificato.
6. Le directory `cad/`, `scripts/`, `evidence/`, `model/edilus/` sono pianificate ma inesistenti.
