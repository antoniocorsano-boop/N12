# Registro Master N12

Versione repository: `RM-0008`

| ID | Ambito | Dato canonico / stato | Evidenza | Stato |
|---|---|---|---|---|
| SRC-001 | tavole originali | acquisite e catalogate 18 tavole PDF originali ad alta risoluzione | `docs/CATALOGO_TAVOLE_ORIGINALI.md` + `data/canonical/tavole_originali_manifest.csv` | DOC |
| SRC-002 | carpenterie | TAV-01S/02S/03S/04S/05S e TAV-06S copertura diventano fonte primaria per maglia, pilastri, travi e fili fissi | tavole originali | DOC-PRIMARIA |
| SRC-003 | armature | TAV-01A/02A/034A/05A/06A/07A disponibili per sezioni, armature e particolari | tavole originali | DOC |
| SRC-004 | controllo geometrico | tavole architettoniche, prospetto e sezioni disponibili per controllo incrociato | TAV-01/02/03/04/05E/06E | DOC |
| SRC-005 | raccordo livelli→carpenterie | `m0s1a_level_sheet_crosswalk.csv` documenta: fondazioni=TAV-01S/`tavola1-2.pdf`; piano terra/1° impalcato=G1=TAV-02S/`tavola2-2.pdf`; G2=TAV-03S; G3=TAV-04S; G4=TAV-05S; G5=TAV-06S | `data/canonical/m0s1a_level_sheet_crosswalk.csv` @ d521f11 | DOC |
| GEO-001 | TAV.5 | carpenteria vettorializzata storicamente in DXF 1:1 | pacchetto DXF strutturale v25 | DOC-ARTEFATTO |
| GEO-002 | TAV.6 | travi vettorializzate storicamente in DXF | pacchetto DXF strutturale v25 | DOC-ARTEFATTO |
| GEO-003 | TAV.7 | pilastri vettorializzati storicamente in DXF | pacchetto DXF strutturale v25 | DOC-ARTEFATTO |
| GEO-004 | topologia TAV.5 | abaco storico con almeno 57 nodi e coordinate X,Y | ABACO_TOPOLOGICO_TAV5_v11.csv | DOC-ARTEFATTO |
| GEO-005 | topologia | 57 nodi / 38 connessioni / 10 componenti = sottoinsieme topologico storico, non assunto come universo geometrico completo | registri storici + presenza di riferimenti a ID superiori | DOC/INF-controllata |
| GEO-006 | modello globale | ricostruzione geometrica primaria deve ora partire dalle carpenterie originali, verificando gli artefatti DXF/CSV contro di esse | SRC-001/SRC-002 | IN_CORSO |
| GEO-007 | TAV.5 nodi fisici recuperati | recuperato nel repository il file canonico a 57 nodi topologici | `data/canonical/tav5_topology_nodes_57.csv` | PREDOC_TOPOLOGICO_RECUPERATO |
| GEO-008 | TAV.5 connessioni candidate | recuperato registro connessioni TAV.5 v07 con 141 connessioni candidate; alcune richiamano nodi oltre N057 | `data/canonical/tav5_topology_connections_v07.csv` | INF_DA_QUOTARE |
| GEO-009 | baseline DXF estesa | baseline `d521f11` documenta inventario testuale TAV5 con nodi candidati almeno N001-N099 e commit di supporto che dichiara 118 nodi complessivi; inventario derivato, non dato strutturale canonico | `docs/FOGLIO_LAVORO/M0S_DXF_TEXT_MEANINGFUL_TAV5.csv` @ d521f11 | DERIVED_DOCUMENT_INVENTORY |
| COL-001 | pilastri | abaco verticale 27×5 | MATRICE_PILASTRI_27x5_v22.csv | DOC-ARTEFATTO |
| COL-002 | pilastri corpo principale | famiglie 40×50 e 40×40 cm | relazione di calcolo | DOC-famiglia |
| COL-003 | torrino scala | pilastri 30×40 cm | relazione di calcolo | DOC-famiglia |
| COL-004 | fili fissi/orientamento | da determinare e congelare livello per livello sulle carpenterie originali, con controllo di continuità verticale | TAV-01S..06S | IN_CORSO |
| COL-005 | pilastri PT | introdotto registro canonico separato per coordinate geometriche di riferimento, centro baricentrico, sezione, orientamento e provenienza; vietato assumere il filo fisso come centro senza verifica dell'offset | `data/canonical/pt_pillars_coordinate_status_v1.csv` + `docs/PT_PILLARS_CANONICAL_PROTOCOL_v1.md` | IN_RICONCILIAZIONE |
| COL-006 | pilastri terrazzo a-b-c-d | presenti nelle carpenterie originarie ma non considerati nei calcoli originari; appartengono allo stato costruito e vanno modellati separatamente dal modello storico | `data/canonical/pt_pillars_coordinate_status_v1.csv` + conferma utente 2026-08-20 | DOC/RIF-CONFERMATO |
| COL-007 | coordinate PT | rilevata non coincidenza di alcune associazioni `node_id → coordinate/fixed_line` tra dataset canonici correnti; nessuna coordinata viene promossa a centro pilastro prima della riconciliazione sulla tavola originaria | `nodes.csv`; `column_fixed_lines.csv`; `tav5_topology_nodes_57.csv` | RESIDUO_ATTIVO |
| COL-008 | terrazzo / candidati DXF | baseline ETW-1 associa alla regione terrazzo i nodi N002, N005, N039 e N041; N041 resta esplicitamente candidato. Creato crosswalk separato senza forzare `a-b-c-d ↔ N...` | `data/canonical/pt_terrace_pillar_candidate_crosswalk_v1.csv`; ETW-1 | INF_CONTROLLATA |
| COL-009 | trasformazione coordinate DXF→canonico | sui quattro candidati terrazzo la differenza tra coordinate testuali DXF baseline e riferimenti canonici è circa (-120 mm, -120 mm), coerente per tutti e quattro; trasformazione valida come raccordo geometrico candidato, non come centro pilastro | `data/canonical/pt_terrace_pillar_candidate_crosswalk_v1.csv` | VER_GEOMETRIC_CANDIDATE |
| COL-010 | armature/sezioni TAV7 | inventario derivato TAV7 conferma sezione 40×40 documentata in più dettagli ma vieta l'associazione automatica ai 27 pilastri; associazione puntuale resta da leggere sulla fonte | `M0S_DXF_TEXT_MEANINGFUL_TAV7.csv` @ d521f11 | DOC_PARZIALE/VER |
| COL-011 | fonte primaria pilastri PT | per la disposizione planimetrica dei pilastri che sostengono il piano terra/1° impalcato usare TAV-02S `tavola2-2.pdf`; TAV-01S resta carpenteria fondazioni. L'overlay grafico PT deve essere eseguito su TAV-02S, con verifica incrociata su TAV-01S per gli appoggi/fondazioni | `m0s1a_level_sheet_crosswalk.csv` @ d521f11 | DOC |
| BEAM-001 | Telaio 1 | percorso I-L-M-N-O-P-Q-R; 7 campate | relazione di calcolo / consolidato v12 | DOC |
| BEAM-002 | Telaio 1 | campate 4.70 / 5.10 / 3.25 / 2.40 / 2.90 / 5.30 / 4.70 m | relazione di calcolo / v12 | DOC |
| BEAM-003 | Telaio 1 G5 | C2-C6 | relazione di calcolo / v12 | DOC |
| BEAM-004 | Telaio 5 | percorso S-S'-T-U-V-Z-A'-B'-C' | relazione di calcolo / v17 | DOC |
| BEAM-005 | Telaio 5 | campate 4.70 / 4.05 / 1.20 / 5.80 / 2.90 / 1.20 / 4.05 / 4.70 m | relazione di calcolo / v17 | DOC |
| BEAM-006 | Telaio 5 G5 | C2-C7 = 19.20 m | relazione di calcolo / v17 | DOC |
| BEAM-007 | Telaio 5 ↔ TAV.5 | il telaio esiste e va allineato per sovrapposizione di sistemi; matrice candidati creata, nessuna promozione a VER senza overlay | `docs/DECISIONI/M0G_ALLINEAMENTO_TELAIO5_TAV5_v1.md` + `data/canonical/telaio5_tav5_candidate_matrix_v1.csv` | IN_ALLINEAMENTO |
| SEC-001 | travi | sezioni note: 20×45, 25×70, 30×45, 30×65, 120×20, 140×20 cm | relazione / consolidati | DOC |
| SEC-002 | Telaio 1 G2 | sezione non congelata | stato M0 v18 | ND |
| LOAD-001 | Telaio 5 | carichi lineari storici G1-G3 disponibili | RC-P13 / v16 | DOC-STORICO |
| FND-001 | fondazioni | 7 catene / 26 segmenti ricostruiti | consolidato fondazioni | DOC-ARTEFATTO |
| M0G-001 | modello globale | coordinate/reticolo da ricostruire prioritariamente dalle tavole originali, usando DXF e abachi come confronto | gate corrente | IN_CORSO |
| M0G-002 | livelli | quote Z definitive | non congelate | ND |
| M0G-003 | raccordo Telaio 5 ↔ 57 nodi | dataset fisico dei 57 nodi recuperato; raccordo ora in allineamento mediante firma metrica, topologia e carpenterie originali | `docs/DECISIONI/M0G_RECUPERO_ABACO_57_NODI_v1.md` + `data/canonical/tav5_topology_nodes_57.csv` | IN_ALLINEAMENTO |
| M0G-004 | altezza interpiano | altezza di piano estradosso-estradosso corretta a 3.20 m | `data/canonical/storey_height_status.csv` + `docs/DECISIONI/M0G_CORREZIONE_ALTEZZA_INTERPIANO_320_v1.md` | RIF_UTENTE_CORRETTO |
| MAT-001 | materiali | calcestruzzo/acciaio | da documentare/indagare | ND |
| MAT-002 | conoscenza | LC/FC | da definire sul quadro conoscitivo | ND |

## Regola di aggiornamento

Ogni nuova acquisizione deve aggiornare questo registro oppure un dataset canonico collegato prima di essere utilizzata come premessa per il modello.
