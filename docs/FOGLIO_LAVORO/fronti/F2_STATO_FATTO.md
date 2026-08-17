# F2 — Stato di fatto strutturale

Stato: `ADVANCING`

## Scope

Ricostruzione completa dello stato di fatto: geometria,拓撲, sezioni, armature, materiali, carichi storici, fondazioni. Ogni dato con stato di evidenza.

## Evidenze disponibili

| Fonte | Stato | Contenuto |
|-------|-------|-----------|
| data/canonical/nodes.csv | VER_GEOMETRIC | 27 catene verticali pilastri con coordinate X/Y |
| data/canonical/telaio_5.csv | DOC | Geometria documentale Telaio 5: 5 livelli, campate, sezioni |
| data/canonical/tav5_topology_nodes_57.csv | PREDOC_TOPOLOGICO | 57 nodi topologici TAV.5 con coordinate X/Y |
| data/canonical/tav5_topology_connections_v07.csv | INF_DA_QUOTARE | 141 connessioni candidate TAV.5 |
| data/canonical/column_fixed_lines.csv | VER | Fili fissi pilastri |
| data/canonical/storey_height_status.csv | RIF | Altezza interpiano 3.20 m estradosso-estradosso |
| data/canonical/pillar_section_assignment_status.csv | ND | Assegnazione sezioni pilastri: non completata |
| data/canonical/tavole_originali_manifest.csv | DOC | Registro tavole originali |
| data/canonical/m0g_topology_status.csv | VER/INF | Stato topologie: 27 catene VER, 57 nodi PREDOC, 141 conn INF |
| docs/REGISTRO_MASTER.md (COL-001..004) | DOC-ARTEFATTO | Abaco verticale 27×5, famiglie 40×50/40×40/30×40 |
| docs/REGISTRO_MASTER.md (BEAM-001..007) | DOC | Telai 1 e 5: percorsi, campate, G5 |
| docs/REGISTRO_MASTER.md (FND-001) | DOC-ARTEFATTO | Fondazioni: 7 catene / 26 segmenti |
| docs/DECISIONI/M0G_FILI_FISSI_v1.md | DOC | Riferimento geometrico 27 catene come VER_GEOMETRIC |
| docs/DECISIONI/M0G_RACCORDO_TELAIO5_57_NODI_v1.md | IN ALLINEAMENTO | Raccordo T5 ↔ 57 nodi non congelato |
| docs/DECISIONI/M0G_RECUPERO_ABACO_57_NODI_v1.md | RECUPERATO | Abaco 57 nodi recuperato nel repo |

## Completato

- 27 catene verticali pilastri: coordinate X/Y, fili fissi, assegnazione 27×5.
- Telaio 1: percorso I-L-M-N-O-P-Q-R, 7 campate, G5=C2-C6 (DOC).
- Telaio 5: percorso S-S'-T-U-V-Z-A'-B'-C', 8 campate, G5=C2-C7 (DOC).
- Sezioni documentate telai: 20×45, 25×70, 30×45, 30×65, 120×20, 140×20 cm (DOC).
- Fondazioni: 7 catene / 26 segmenti ricostruiti (DOC-ARTEFATTO).
- Altezza interpiano: 3.20 m estradosso-estradosso (RIF, corretta).
- Abaco 57 nodi topologici recuperato nel repo.
- 141 connessioni candidate TAV.5 registrate.

## Mancante

- Normalizzazione completa coordinate nodali globali.
- Connettività strutturale per impalcato.
- Raccordo几何 dei 27 pilastri alle coordinate planimetriche e ai cinque livelli.
- Sagome/arretramenti di tutti gli impalcati.
- Quote Z definitive.
- Raccordo geometrico delle fondazioni.
- Controllo indipendente mediante firme metriche dei Telai 1 e 5.
- Altri telai oltre T1 e T5 non ancora discretizzati.
- Sezioni puntuali pilastri per catena e livello.

## Residui

| ID | Tipo | Front | Descrizione | Stato |
|----|------|-------|-------------|-------|
| R-1A-01 | BLOCCANTE | F3 | Raccordo 57 nodi topologici | IN ALLINEAMENTO |
| R-1A-02 | BLOCCANTE | F3 | Quote Z definitive | ND |
| R-1A-03 | BLOCCANTE | F3 | Connettività globale per livello | IN CORSO |
| R-1A-04 | BLOCCANTE | F3 | Sagome/arretramenti impalcati | ND |
| R-1A-05 | BLOCCANTE | F3 | Raccordo geometrico fondazioni | PARZIALE |
| R-1A-09 | RISCHIO | F3 | Allineamento T5 ↔ TAV.5 | HYP_A_METRICA |

## Prossima azione

Raccordo 57 nodi topologici alle coordinate canoniche: verificare ABACO_TOPOLOGICO_TAV5_v11.csv e costruire dataset `nodes.csv` + `vertical_columns.csv` verificato contro TAV.5/TAV.7.
