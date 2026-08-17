# Matrice Artefatti Professionali N12

Versione: `MA-0001` — 2026-08-17

## Scope

Inventario completo degli artefatti professionali (documenti, dataset, modelli, tavole) con stato, fronte di pertinenza, e relazione con le evidenze.

## Artefatti

### Protocollo e gestione

| ID | Artefatto | Path | Stato | Fronte | Note |
|----|-----------|------|-------|--------|------|
| AP-00 | Protocollo canonico | docs/PROTOCOLLO_CANONICO.md | ATTIVO | F0 | Versione corrente |
| AP-01 | Registro Master | docs/REGISTRO_MASTER.md | RM-0005 | F1/F2 | Registro delle evidenze |
| AP-02 | Stato di ripresa | docs/STATO_RIPRESA.md | 2026-08-16 | F0/F2 | Snapshot contesto |
| AP-03 | AGENTS.md | AGENTS.md | v1 | — | Guardia operativa OpenCode |
| AP-04 | Fascicolo R1-A | docs/FOGLIO_LAVORO/FASCICOLO_R1A.md | R1-A-0001 | — | Workspace orchestrator |
| AP-05 | Registro Evidenze | docs/FOGLIO_LAVORO/REGISTRO_EVIDENZE.md | RE-0001 | — | Contratto evidenze |
| AP-06 | Matrice Artefatti | docs/FOGLIO_LAVORO/MATRICE_ARTEFATTI.md | MA-0001 | — | Questo file |

### Fonti originali

| ID | Artefatto | Path | Stato | Fronte | Note |
|----|-----------|------|-------|--------|------|
| AF-00 | Catalogo tavole originali | docs/CATALOGO_TAVOLE_ORIGINALI.md | DOC | F1 | 18 tavole PDF |
| AF-01 | Manifest tavole | data/canonical/tavole_originali_manifest.csv | DOC | F1 | Registro digitale |
| AF-02 | Inventario artefatti storici | archive/ARTEFATTI_STORICI.md | DOC | F1 | DXF v25 |

### Dati canonici

| ID | Artefatto | Path | Stato | Fronte | Note |
|----|-----------|------|-------|--------|------|
| AD-00 | Nodi 27 catene | data/canonical/nodes.csv | VER_GEOMETRIC | F2/F3 | Coordinate X/Y in mm |
| AD-01 | Fili fissi pilastri | data/canonical/column_fixed_lines.csv | VER | F2 | Asse geometriche |
| AD-02 | Altezza interpiano | data/canonical/storey_height_status.csv | RIF | F2/F3 | 3.20 m estradosso-estradosso |
| AD-03 | Telaio 5 geometria | data/canonical/telaio_5.csv | DOC | F2/F3 | 5 livelli, campate, sezioni |
| AD-04 | T5 candidati | data/canonical/telaio5_tav5_candidate_matrix_v1.csv | INF | F3 | HYP_A_METRICA |
| AD-05 | Topologia 57 nodi | data/canonical/tav5_topology_nodes_57.csv | PREDOC | F2/F3 | 57 nodi TAV.5 |
| AD-06 | 141 connessioni | data/canonical/tav5_topology_connections_v07.csv | INF_DA_QUOTARE | F2/F3 | Candidate, non verificate |
| AD-07 | Assegnazione pilastri | data/canonical/pillar_section_assignment_status.csv | ND | F4 | Non completata |
| AD-08 | Sezioni FEM placeholder | data/canonical/fem_section_placeholders.csv | PLACEHOLDER | F3 | Solo smoke-test |
| AD-09 | Stato topologia M0G | data/canonical/m0g_topology_status.csv | VER/INF | F3 | Stato avanzamento |
| AD-10 | Raccordo T5 57 nodi | data/canonical/telaio5_raccordo_57_nodi_status.csv | IN_ALLINEAMENTO | F3 | Non congelato |

### Decisioni

| ID | Artefatto | Path | Stato | Fronte | Note |
|----|-----------|------|-------|--------|------|
| AZ-00 | Allineamento T5 ↔ TAV.5 | docs/DECISIONI/M0G_ALLINEAMENTO_TELAIO5_TAV5_v1.md | IN ALLINEAMENTO | F3 | Non verificato |
| AZ-01 | Correzione altezza | docs/DECISIONI/M0G_CORREZIONE_ALTEZZA_INTERPIANO_320_v1.md | CHIUSO | F2/F3 | 3.20 m congelato |
| AZ-02 | Fili fissi | docs/DECISIONI/M0G_FILI_FISSI_v1.md | DOC | F2 | Riferimento geometrico |
| AZ-03 | Raccordo T5 57 nodi | docs/DECISIONI/M0G_RACCORDO_TELAIO5_57_NODI_v1.md | BLOCCATO_PARZIALE | F3 | R-v17-01 |
| AZ-04 | Recupero abaco 57 nodi | docs/DECISIONI/M0G_RECUPERO_ABACO_57_NODI_v1.md | RECUPERATO | F2/F3 | Abaco nel repo |
| AZ-05 | Pilastri TAV.7 gate | docs/DECISIONI/M0S_PILASTRI_TAV7_GATE_v1.md | IN CORSO | F4 | Gate assegnazione |

### Modelli FEM

| ID | Artefatto | Path | Stato | Fronte | Note |
|----|-----------|------|-------|--------|------|
| AM-00 | Geometria OpenSeesPy | model/open_source_fem/opensees_m0_geometry.py | M0-OS-0002 | F3 | Generator, non eseguibile localmente |
| AM-01 | Requirements FEM | model/open_source_fem/requirements.txt | OK | F3 | openseespy>=3.5.1 |
| AM-02 | README FEM | model/open_source_fem/README.md | DOC | F3 | Documentazione M0-OS-0002 |
| AM-03 | STATUS M0-G | model/M0-G/STATUS.md | IN CORSO | F3 | Stato e criteri chiusura |

### Tavole strutturali

| ID | Artefatto | Path | Stato | Fronte | Note |
|----|-----------|------|-------|--------|------|
| AT-00 | Tavole strutturali master | docs/TAVOLE/TAVOLE_STRUTTURALI_MASTER_v1.md | TAV-MASTER-0001 | F1 | In redazione |
| AT-01 | Cartiglio unico | docs/TAVOLE/CARTIGLIO_UNICO_v1.md | DOC | F12 | Template grafico |
| AT-02 | Piano editoriale | docs/PIANO_EDITORIALE_TAVOLE_CARTIGLIO_COPERTINA.md | DOC | F12 | Copertina/cartiglio |

### Fronti (docs/FOGLIO_LAVORO/fronti/)

| ID | Artefatto | Path | Stato | Fronte |
|----|-----------|------|-------|--------|
| FF-00 | F0 Progetto | docs/FOGLIO_LAVORO/fronti/F0_PROGETTO.md | PARTIAL | F0 |
| FF-01 | F1 Fonti | docs/FOGLIO_LAVORO/fronti/F1_FONDI.md | ADVANCING | F1 |
| FF-02 | F2 Stato di fatto | docs/FOGLIO_LAVORO/fronti/F2_STATO_FATTO.md | ADVANCING | F2 |
| FF-03 | F3 Modello globale | docs/FOGLIO_LAVORO/fronti/F3_MODELLO_GLOBALE.md | IN CORSO | F3 |
| FF-04 | F4 Sezioni/armature | docs/FOGLIO_LAVORO/fronti/F4_SEZIONI_ARMATURE.md | NOT STARTED | F4 |
| FF-05 | F5 Materiali/carichi | docs/FOGLIO_LAVORO/fronti/F5_MATERIALI_CARICHI.md | NOT STARTED | F5 |
| FF-06 | F6 Diagnosi | docs/FOGLIO_LAVORO/fronti/F6_DIAGNOSI.md | BLOCKED | F6 |
| FF-07 | F7 Interventi | docs/FOGLIO_LAVORO/fronti/F7_INTERVENTI.md | BLOCKED | F7 |
| FF-08 | F8 Verifica | docs/FOGLIO_LAVORO/fronti/F8_VERIFICA.md | BLOCKED | F8 |
| FF-09 | F9 Progettazione | docs/FOGLIO_LAVORO/fronti/F9_PROGETTAZIONE.md | BLOCKED | F9 |
| FF-10 | F10 Esecuzione | docs/FOGLIO_LAVORO/fronti/F10_ESECUZIONE.md | N/A | F10 |
| FF-11 | F11 Post operam | docs/FOGLIO_LAVORO/fronti/F11_POST_OPERAM.md | N/A | F11 |
| FF-12 | F12 Fascicolo | docs/FOGLIO_LAVORO/fronti/F12_FASCICOLO.md | BLOCKED | F12 |
