# Matrice Artefatti Professionali N12

Versione: `MA-0002` — 2026-08-17 (R1-B)

## Scope

Inventario completo degli artefatti professionali con due dimensioni distinte:
- **Stato epistemico** dell'evidenza: `DOC / MIS / RIF / INF / INC / ND / VER / PLACEHOLDER / ...`
- **Provenienza Git/documentale**: da quale linea di sviluppo proviene l'artefatto (`main / M0-G / R1-A / R1-B`)

Le due dimensioni non vanno fuse. Un artefatto può essere su `main` con stato `ND`, o su `R1-A` con stato `DOC`.

## Artefatti

### Protocollo e gestione

| ID | Artefatto | Path | Stato | Provenienza | Fronte | Evidenza | Note |
|----|-----------|------|-------|-------------|--------|----------|------|
| AP-00 | Protocollo canonico | docs/PROTOCOLLO_CANONICO.md | ATTIVO | main | F0 | — | Versione corrente |
| AP-01 | Registro Master | docs/REGISTRO_MASTER.md | RM-0005 | main→M0-G | F1/F2 | — | Registro delle evidenze |
| AP-02 | Stato di ripresa | docs/STATO_RIPRESA.md | 2026-08-16 | M0-G | F0/F2 | — | Snapshot contesto |
| AP-03 | AGENTS.md | AGENTS.md | v1 | R1-A | — | — | Guardia operativa OpenCode |
| AP-04 | Fascicolo R1-A | docs/FOGLIO_LAVORO/FASCICOLO_R1A.md | R1-A-0002 | R1-B | — | — | Workspace orchestrator (v2) |
| AP-05 | Registro Evidenze | docs/FOGLIO_LAVORO/REGISTRO_EVIDENZE.md | RE-0001 | R1-A | — | — | Contratto evidenze |
| AP-06 | Matrice Artefatti | docs/FOGLIO_LAVORO/MATRICE_ARTEFATTI.md | MA-0002 | R1-B | — | — | Questo file (v2) |
| AP-07 | Checklist Integrità | docs/FOGLIO_LAVORO/CHECKLIST_INTEGRITA_FONTE.md | CI-0001 | R1-B | F1 | — | Conformità fonti |
| AP-08 | Traceability | docs/FOGLIO_LAVORO/TRACEABILITY.md | TR-0001 | R1-B | — | — | Tracciabilità many-to-many |
| AP-09 | Residui | docs/FOGLIO_LAVORO/RESIDUI.md | RS-0001 | R1-B | — | — | Tracking residui |
| AP-10 | Gate Report R1-A | docs/FOGLIO_LAVORO/GATE_REPORT_R1A.md | GR-0001 | R1-B | — | — | Provenienza 45 file |

### Fonti originali

| ID | Artefatto | Path | Stato | Provenienza | Fronte | Evidenza | Note |
|----|-----------|------|-------|-------------|--------|----------|------|
| AF-00 | Catalogo tavole originali | docs/CATALOGO_TAVOLE_ORIGINALI.md | DOC | M0-G | F1 | — | 18 tavole PDF |
| AF-01 | Manifest tavole | data/canonical/tavole_originali_manifest.csv | DOC | M0-G | F1 | — | Registro digitale |
| AF-02 | Inventario artefatti storici | archive/ARTEFATTI_STORICI.md | DOC | main→M0-G | F1 | — | DXF v25 |

### Dati canonici

| ID | Artefatto | Path | Stato | Provenienza | Fronte | Evidenza | Note |
|----|-----------|------|-------|-------------|--------|----------|------|
| AD-00 | Nodi 27 catene | data/canonical/nodes.csv | VER_GEOMETRIC | M0-G | F2/F3 | EV-G01, EV-P02 | Coordinate X/Y in mm |
| AD-01 | Fili fissi pilastri | data/canonical/column_fixed_lines.csv | VER | M0-G | F2 | EV-P02 | Asse geometriche |
| AD-02 | Altezza interpiano | data/canonical/storey_height_status.csv | RIF | M0-G | F2/F3 | EV-G02 | 3.20 m estradosso-estradosso |
| AD-03 | Telaio 5 geometria | data/canonical/telaio_5.csv | DOC | main→M0-G | F2/F3 | EV-T07 | 5 livelli, campate, sezioni |
| AD-04 | T5 candidati | data/canonical/telaio5_tav5_candidate_matrix_v1.csv | INF | M0-G | F3 | EV-G05 | HYP_A_METRICA |
| AD-05 | Topologia 57 nodi | data/canonical/tav5_topology_nodes_57.csv | PREDOC_TOPOLOGICO | M0-G | F2/F3 | EV-G03 | 57 nodi TAV.5, sottoinsieme storico |
| AD-06 | 141 connessioni | data/canonical/tav5_topology_connections_v07.csv | INF_DA_QUOTARE | M0-G | F2/F3 | EV-G04 | Candidate, non verificate |
| AD-07 | Assegnazione pilastri | data/canonical/pillar_section_assignment_status.csv | ND | M0-G | F4 | EV-P03 | Non completata |
| AD-08 | Sezioni FEM placeholder | data/canonical/fem_section_placeholders.csv | PLACEHOLDER_GEOMETRY_ONLY | M0-G | F3 | EV-F02 | Solo smoke-test |
| AD-09 | Stato topologia M0G | data/canonical/m0g_topology_status.csv | VER/INF | M0-G | F3 | EV-G01,G03,G04 | Stato avanzamento |
| AD-10 | Raccordo T5 57 nodi | data/canonical/telaio5_raccordo_57_nodi_status.csv | IN_ALLINEAMENTO | M0-G | F3 | EV-G05 | Non congelato |
| AD-11 | Telaio 5 (originale) | data/canonical/telaio_5.csv | DOC | main | F2/F3 | EV-T07 | Originale su main, aggiornato da M0-G |

### Decisioni

| ID | Artefatto | Path | Stato | Provenienza | Fronte | Evidenza | Note |
|----|-----------|------|-------|-------------|--------|----------|------|
| AZ-00 | Allineamento T5 ↔ TAV.5 | docs/DECISIONI/M0G_ALLINEAMENTO_TELAIO5_TAV5_v1.md | IN ALLINEAMENTO | M0-G | F3 | EV-G05 | Non verificato |
| AZ-01 | Correzione altezza | docs/DECISIONI/M0G_CORREZIONE_ALTEZZA_INTERPIANO_320_v1.md | CHIUSO | M0-G | F2/F3 | EV-G02 | 3.20 m congelato |
| AZ-02 | Fili fissi | docs/DECISIONI/M0G_FILI_FISSI_v1.md | DOC | M0-G | F2 | EV-P02 | Riferimento geometrico |
| AZ-03 | Raccordo T5 57 nodi | docs/DECISIONI/M0G_RACCORDO_TELAIO5_57_NODI_v1.md | BLOCCATO_PARZIALE | M0-G | F3 | EV-G05 | R-v17-01 |
| AZ-04 | Recupero abaco 57 nodi | docs/DECISIONI/M0G_RECUPERO_ABACO_57_NODI_v1.md | RECUPERATO | M0-G | F2/F3 | EV-G03 | Abaco nel repo |
| AZ-05 | Pilastri TAV.7 gate | docs/DECISIONI/M0S_PILASTRI_TAV7_GATE_v1.md | IN CORSO | M0-G | F4 | EV-P03 | Gate assegnazione |

### Modelli FEM

| ID | Artefatto | Path | Stato | Provenienza | Fronte | Evidenza | Note |
|----|-----------|------|-------|-------------|--------|----------|------|
| AM-00 | Geometria OpenSeesPy | model/open_source_fem/opensees_m0_geometry.py | M0-OS-0002 | M0-G | F3 | EV-F01 | Generator, non eseguibile localmente |
| AM-01 | Requirements FEM | model/open_source_fem/requirements.txt | OK | M0-G | F3 | — | openseespy>=3.5.1 |
| AM-02 | README FEM | model/open_source_fem/README.md | DOC | M0-G | F3 | — | Documentazione M0-OS-0002 |
| AM-03 | STATUS M0-G | model/M0-G/STATUS.md | IN CORSO | M0-G | F3 | — | Stato e criteri chiusura |
| AM-04 | Exports README | model/open_source_fem/exports/README.md | PLACEHOLDER | M0-G | F3 | — | Cartella output (stale) |

### Tavole strutturali

| ID | Artefatto | Path | Stato | Provenienza | Fronte | Evidenza | Note |
|----|-----------|------|-------|-------------|--------|----------|------|
| AT-00 | Tavole strutturali master | docs/TAVOLE/TAVOLE_STRUTTURALI_MASTER_v1.md | TAV-MASTER-0001 | M0-G | F1 | — | In redazione |
| AT-01 | Cartiglio unico | docs/TAVOLE/CARTIGLIO_UNICO_v1.md | DOC | M0-G | F12 | — | Template grafico |
| AT-02 | Piano editoriale | docs/PIANO_EDITORIALE_TAVOLE_CARTIGLIO_COPERTINA.md | DOC | M0-G | F12 | — | Copertina/cartiglio |

### Fronti (docs/FOGLIO_LAVORO/fronti/)

| ID | Artefatto | Path | Stato | Provenienza | Fronte | Evidenza |
|----|-----------|------|-------|-------------|--------|----------|
| FF-00 | F0 Progetto | docs/FOGLIO_LAVORO/fronti/F0_PROGETTO.md | PARTIAL | R1-A | F0 | EV-G01,G02 |
| FF-01 | F1 Fonti | docs/FOGLIO_LAVORO/fronti/F1_FONDI.md | ADVANCING | R1-A | F1 | AF-00,AF-01,AF-02 |
| FF-02 | F2 Stato di fatto | docs/FOGLIO_LAVORO/fronti/F2_STATO_FATTO.md | ADVANCING | R1-A | F2 | EV-G*,EV-T*,EV-S*,EV-P* |
| FF-03 | F3 Modello globale | docs/FOGLIO_LAVORO/fronti/F3_MODELLO_GLOBALE.md | IN CORSO | R1-A | F3 | EV-G*,EV-F* |
| FF-04 | F4 Sezioni/armature | docs/FOGLIO_LAVORO/fronti/F4_SEZIONI_ARMATURE.md | NOT STARTED | R1-A | F4 | EV-S*,EV-P03 |
| FF-05 | F5 Materiali/carichi | docs/FOGLIO_LAVORO/fronti/F5_MATERIALI_CARICHI.md | NOT STARTED | R1-A | F5 | EV-M*,EV-L* |
| FF-06 | F6 Diagnosi | docs/FOGLIO_LAVORO/fronti/F6_DIAGNOSI.md | BLOCKED | R1-A | F6 | — |
| FF-07 | F7 Interventi | docs/FOGLIO_LAVORO/fronti/F7_INTERVENTI.md | BLOCKED | R1-A | F7 | — |
| FF-08 | F8 Verifica | docs/FOGLIO_LAVORO/fronti/F8_VERIFICA.md | BLOCKED | R1-A | F8 | — |
| FF-09 | F9 Progettazione | docs/FOGLIO_LAVORO/fronti/F9_PROGETTAZIONE.md | BLOCKED | R1-A | F9 | — |
| FF-10 | F10 Esecuzione | docs/FOGLIO_LAVORO/fronti/F10_ESECUZIONE.md | N/A | R1-A | F10 | — |
| FF-11 | F11 Post operam | docs/FOGLIO_LAVORO/fronti/F11_POST_OPERAM.md | N/A | R1-A | F11 | — |
| FF-12 | F12 Fascicolo | docs/FOGLIO_LAVORO/fronti/F12_FASCICOLO.md | BLOCKED | R1-A | F12 | — |

## Legenda provenienza

| Provenienza | Significato |
|-------------|-------------|
| `main` | File esistente su `main` prima di qualsiasi sviluppo |
| `main→M0-G` | File su `main`, modificato/aggiornato dal branch M0-G |
| `M0-G` | File creato durante lo sviluppo M0-G (work/m0-global-model) |
| `R1-A` | File creato nella fase R1-A (workspace professionale) |
| `R1-B` | File creato/aggiornato nella fase R1-B (evidence integration) |
