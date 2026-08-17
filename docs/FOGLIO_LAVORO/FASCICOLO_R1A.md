# Fascicolo R1-A — Workspace Professionale Strutturale

Versione: `R1-A-0002` — 2026-08-17 (aggiornato R1-B)

## Scope

Workflow orchestrator per la ricostruzione strutturale N12. Traccia l'ottavo stadio verticale, i 13 fronti professionali, i conteggi evidenze, i residui e le prossime azioni. Non contiene dati strutturali — tutti i dati canonici vivono in `data/canonical/` e `docs/REGISTRO_MASTER.md`.

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
| F10 | Esecuzione / Cantiere | N/A | Fuori scope fase R1 |
| F11 | Post operam | N/A | Fuori scope fase R1 |
| F12 | Fascicolo finale | BLOCKED | Compilazione ultima dopo tutti i fronti |

## Conteggio evidenze per stato (25 voci — da Registro Evidenze RE-0001)

| Stato | Count | Evidenze |
|-------|-------|----------|
| DOC / DOC-* | 10 | EV-T01..T07, EV-S01/S03/S04, EV-L01 |
| DOC-ARTEFATTO | 2 | EV-G06, EV-P01 |
| DOC-famiglia | 2 | EV-S05, EV-S06 |
| VER / VER-* | 2 | EV-G01, EV-P02 |
| RIF | 1 | EV-G02 |
| PREDOC_TOPOLOGICO | 1 | EV-G03 |
| INF_DA_QUOTARE | 1 | EV-G04 |
| INF | 1 | EV-G05 |
| ND | 3 | EV-S02, EV-M01, EV-M02 |
| PLACEHOLDER / PLACEHOLDER_GEOMETRY_ONLY | 3 | EV-F01, EV-F02, EV-F03 |

## Residui / Bloccanti

Vedi `docs/FOGLIO_LAVORO/RESIDUI.md` per il registro completo con stato, dipendenze e prossime azioni.

| ID | Tipo | Front | Descrizione | Stato |
|----|------|-------|-------------|-------|
| R-1A-01 | BLOCCANTE | F3 | Raccordo 57 nodi topologici a coordinate canoniche | BLOCCATO |
| R-1A-02 | BLOCCANTE | F3 | Quote Z definitive | APERTO |
| R-1A-03 | BLOCCANTE | F3 | Connettività globale per impalcato | BLOCCATO |
| R-1A-04 | BLOCCANTE | F3 | Sagome/arretramenti impalcati | APERTO |
| R-1A-05 | BLOCCANTE | F3 | Raccordo geometrico fondazioni | BLOCCATO |
| R-1A-06 | BLOCCANTE | F4 | Sezioni puntuali pilastri per catena e livello | BLOCCATO |
| R-1A-07 | BLOCCANTE | F5 | Materiali calcestruzzo/acciaio | APERTO |
| R-1A-08 | BLOCCANTE | F5 | Livello di conoscenza LC/FC | APERTO |
| R-1A-09 | RISCHIO | F3 | Allineamento T5 ↔ TAV.5 non verificato | APERTO |
| R-1A-10 | RISCHIO | F2 | Topologia 57 nodi: riferimenti a ID > N057 | APERTO |

## Riferimenti R1-B

| Deliverable | Path | Versione |
|-------------|------|----------|
| Matrice Artefatti | docs/FOGLIO_LAVORO/MATRICE_ARTEFATTI.md | MA-0002 |
| Registro Evidenze | docs/FOGLIO_LAVORO/REGISTRO_EVIDENZE.md | RE-0001 |
| Checklist Integrità | docs/FOGLIO_LAVORO/CHECKLIST_INTEGRITA_FONTE.md | CI-0001 |
| Traceability | docs/FOGLIO_LAVORO/TRACEABILITY.md | TR-0001 |
| Residui | docs/FOGLIO_LAVORO/RESIDUI.md | RS-0001 |
| Gate Report R1-A | docs/FOGLIO_LAVORO/GATE_REPORT_R1A.md | GR-0001 |

## Prossima azione globale

R1-A-01: Completare raccordo 57 nodi topologici — recuperare o verificare `ABACO_TOPOLOGICO_TAV5_v11.csv` e costruire dataset canonico verificato contro TAV.5/TAV.7. Questo è lavoro sul modello strutturale canonico e rispetta il gate M0-G; non è attività di interfaccia R1.

## Regole di questo workspace

1. Ogni dato strutturale riporta stato DOC/MIS/RIF/INF/INC/ND.
2. Nessun PLACEHOLDER/ND viene promosso a DOC per analogia o convenienza.
3. Gli exports/ obsoleti non sono fonte canonica; il file Python è la reference.
4. `nodes.csv` non rappresenta la topologia completa a 57 nodi.
5. Telaio 5 resta HYP_A_METRICA non verificato.
6. Le directory `cad/`, `scripts/`, `evidence/`, `model/edilus/` sono pianificate ma inesistenti.
7. **Separazione R1 / M0-G**: il workspace R1 non risolve il modello strutturale; il modello M0-G ha gate propri.
