# Traceability N12

Versione: `TR-0001` — 2026-08-17 (R1-B)

## Scope

Modello di tracciabilità many-to-many tra voci del fascicolo, evidenze, fonti, stati epistemici e residui. Ogni relazione è **deterministica**: da una voce del fascicolo si risale senza ambiguità a evidenza → fonte → stato → residuo.

## Modello relazionale

```
VOCE FASCICOLO ←→ EVIDENZA ←→ FONTE
                       ↓
                   STATO EPISTEMICO
                       ↓
                   AMBITO
                       ↓
                   RESIDUO/I (zero, uno o più)
```

Una fonte può sostenere **più evidenze**. Una voce del fascicolo può dipendere da **più evidenze**. Non si duplicano EV-xxx per ottenere una matrice semplice.

## 1. Voce Fascicolo → Evidenze

| Voce Fascicolo | Fronte | Evidenze | Note |
|----------------|--------|----------|------|
| Coordinate 27 catene | F2/F3 | EV-G01, EV-P02 | Dati geometrici verificati |
| Altezza interpiano 3.20 m | F2/F3 | EV-G02 | Riferimento congelato |
| Topologia 57 nodi TAV.5 | F2/F3 | EV-G03 | Sottoinsieme storico, non universo |
| 141 connessioni candidate | F2/F3 | EV-G04 | Non verificate come travi |
| Allineamento T5 ↔ TAV.5 | F3 | EV-G05 | Ipotesi, non verificata |
| Fondazioni 7 catene/26 segmenti | F2 | EV-G06 | Ricostruzione parziale |
| T1 percorso e campate | F2 | EV-T01, EV-T02, EV-T03 | DOC dalla relazione |
| T5 percorso e campate | F2 | EV-T04, EV-T05, EV-T06, EV-T07 | DOC dalla relazione |
| Sezioni travi note | F4 | EV-S01, EV-S03, EV-S04 | DOC |
| Sezioni pilastri famiglie | F4 | EV-S05, EV-S06 | DOC-famiglia, non assegnate |
| Sezione T1 G2 | F4 | EV-S02 | ND |
| Materiali calcestruzzo/acciaio | F5 | EV-M01 | ND |
| Conoscenza LC/FC | F5 | EV-M02 | ND |
| Carichi storici T5 | F5 | EV-L01 | DOC-STORICO |
| Abaco 27×5 pilastri | F2/F3 | EV-P01 | DOC-ARTEFATTO |
| Fili fissi pilastri | F2 | EV-P02 | VER |
| Sezioni puntuali pilastri | F4 | EV-P03 | ND |
| Modello FEM M0-OS-0002 | F3 | EV-F01, EV-F02, EV-F03 | PLACEHOLDER |

## 2. Evidenza → Fonti

| Evidenza | Fonti (file canonici) | Note |
|----------|----------------------|------|
| EV-G01 | data/canonical/nodes.csv | Coordinate 27 catene |
| EV-G02 | data/canonical/storey_height_status.csv | Altezza 3.20 m |
| EV-G03 | data/canonical/tav5_topology_nodes_57.csv | 57 nodi topologici |
| EV-G04 | data/canonical/tav5_topology_connections_v07.csv | 141 connessioni |
| EV-G05 | data/canonical/telaio5_tav5_candidate_matrix_v1.csv, data/canonical/telaio5_raccordo_57_nodi_status.csv | Matrice candidati + raccordo |
| EV-G06 | archive/ARTEFATTI_STORICI.md (referenza a consolidato fondazioni) | Fonte indiretta |
| EV-T01 | docs/REGISTRO_MASTER.md (BEAM-001) | Relazione di calcolo |
| EV-T02 | docs/REGISTRO_MASTER.md (BEAM-002) | Relazione di calcolo |
| EV-T03 | docs/REGISTRO_MASTER.md (BEAM-003) | Relazione di calcolo |
| EV-T04 | docs/REGISTRO_MASTER.md (BEAM-004) | Relazione di calcolo |
| EV-T05 | docs/REGISTRO_MASTER.md (BEAM-005) | Relazione di calcolo |
| EV-T06 | docs/REGISTRO_MASTER.md (BEAM-006) | Relazione di calcolo |
| EV-T07 | data/canonical/telaio_5.csv | Geometria documentale T5 |
| EV-S01 | docs/REGISTRO_MASTER.md (SEC-001) | Sezioni note |
| EV-S02 | docs/REGISTRO_MASTER.md (SEC-002) | Sezione ND |
| EV-S03 | data/canonical/telaio_5.csv (G5=20×45) | Sezione documentata |
| EV-S04 | data/canonical/telaio_5.csv (G1-G4=25×70+140×20) | Sezione documentata |
| EV-S05 | docs/REGISTRO_MASTER.md (COL-002) | Famiglia doc |
| EV-S06 | docs/REGISTRO_MASTER.md (COL-003) | Famiglia doc |
| EV-M01 | — (nessuna fonte disponibile) | ND |
| EV-M02 | — (nessuna fonte disponibile) | ND |
| EV-L01 | docs/REGISTRO_MASTER.md (LOAD-001) | Dati storici |
| EV-P01 | data/canonical/m0g_topology_status.csv (referenza a MATRICE_PILASTRI_27x5_v22.csv) | Fonte indiretta |
| EV-P02 | docs/DECISIONI/M0G_FILI_FISSI_v1.md | Decisione documentata |
| EV-P03 | — (nessuna fonte disponibile) | ND, da TAV.7 |
| EV-F01 | model/open_source_fem/opensees_m0_geometry.py | Script generatore |
| EV-F02 | data/canonical/fem_section_placeholders.csv | Sezioni provvisorie |
| EV-F03 | model/open_source_fem/opensees_m0_geometry.py | Vincoli prova |

## 3. Evidenza → Stato epistemico → Ambito → Residui

| Evidenza | Stato | Ambito | Residui aperti |
|----------|-------|--------|----------------|
| EV-G01 | VER_GEOMETRIC | Coordinate 27 catene | — |
| EV-G02 | RIF | Altezza interpiano | — |
| EV-G03 | PREDOC_TOPOLOGICO | Topologia 57 nodi TAV.5 | R-1A-01 (raccordo a coordinate canoniche) |
| EV-G04 | INF_DA_QUOTARE | 141 connessioni candidate | R-1A-01 |
| EV-G05 | INF | Allineamento T5 ↔ TAV.5 | R-1A-09 (non verificato) |
| EV-G06 | DOC-ARTEFATTO | Fondazioni | R-1A-05 (raccordo geometrico) |
| EV-T01 | DOC | T1 percorso | — |
| EV-T02 | DOC | T1 campate | — |
| EV-T03 | DOC | T1 G5 | — |
| EV-T04 | DOC | T5 percorso | — |
| EV-T05 | DOC | T5 campate | — |
| EV-T06 | DOC | T5 G5 | — |
| EV-T07 | DOC | T5 livelli e sezioni | — |
| EV-S01 | DOC | Sezioni travi | — |
| EV-S02 | ND | T1 G2 | R-1A-06 (sezione da definire) |
| EV-S03 | DOC | T5 G5 sezione | — |
| EV-S04 | DOC | T5 G1-G4 sezioni | — |
| EV-S05 | DOC-famiglia | Pilastri corpo 40×50/40×40 | R-1A-06 (assegnazione) |
| EV-S06 | DOC-famiglia | Torrino 30×40 | R-1A-06 (assegnazione) |
| EV-M01 | ND | Materiali | R-1A-07 |
| EV-M02 | ND | Conoscenza LC/FC | R-1A-08 |
| EV-L01 | DOC-STORICO | Carichi storici T5 | — |
| EV-P01 | DOC-ARTEFATTO | Abaco 27×5 | R-1A-06 (assegnazione sezioni) |
| EV-P02 | VER | Fili fissi | — |
| EV-P03 | ND | Sezioni puntuali pilastri | R-1A-06 |
| EV-F01 | PLACEHOLDER | Modello FEM geometrico | — (non di verifica) |
| EV-F02 | PLACEHOLDER_GEOMETRY_ONLY | Sezioni FEM | — (non di verifica) |
| EV-F03 | PLACEHOLDER | Vincoli FEM | — (non di verifica) |

## 4. Percorso inverso: Fonte → Evidenze → Artefatti

| Fonte | Evidenze sostenute | Artefatti che la utilizzano |
|-------|-------------------|---------------------------|
| data/canonical/nodes.csv | EV-G01 | AD-00, FF-02, FF-03 |
| data/canonical/storey_height_status.csv | EV-G02 | AD-02, FF-02, FF-03 |
| data/canonical/tav5_topology_nodes_57.csv | EV-G03 | AD-05, FF-02, FF-03 |
| data/canonical/tav5_topology_connections_v07.csv | EV-G04 | AD-06, FF-02, FF-03 |
| data/canonical/telaio5_tav5_candidate_matrix_v1.csv | EV-G05 | AD-04, FF-03 |
| data/canonical/telaio5_raccordo_57_nodi_status.csv | EV-G05 | AD-10, FF-03 |
| data/canonical/telaio_5.csv | EV-T07, EV-S03, EV-S04 | AD-03/AD-11, FF-02, FF-03, FF-04 |
| data/canonical/fem_section_placeholders.csv | EV-F02 | AD-08, FF-03 |
| data/canonical/m0g_topology_status.csv | EV-G01, EV-G03, EV-G04 | AD-09, FF-03 |
| docs/REGISTRO_MASTER.md | EV-T01..T06, EV-S01/S02/S05/S06, EV-L01, EV-P01 | AP-01, FF-01, FF-02 |
| docs/DECISIONI/M0G_FILI_FISSI_v1.md | EV-P02 | AZ-02, FF-02 |
| model/open_source_fem/opensees_m0_geometry.py | EV-F01, EV-F03 | AM-00, FF-03 |
| archive/ARTEFATTI_STORICI.md | EV-G06 | AF-02, FF-01 |
