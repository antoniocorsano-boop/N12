# Registro Master N12

Versione repository: `RM-0004`

| ID | Ambito | Dato canonico / stato | Evidenza | Stato |
|---|---|---|---|---|
| SRC-001 | tavole originali | acquisite e catalogate 18 tavole PDF originali ad alta risoluzione | `docs/CATALOGO_TAVOLE_ORIGINALI.md` + `data/canonical/tavole_originali_manifest.csv` | DOC |
| SRC-002 | carpenterie | TAV-01S/02S/03S/04S/05S e TAV-06S copertura diventano fonte primaria per maglia, pilastri, travi e fili fissi | tavole originali | DOC-PRIMARIA |
| SRC-003 | armature | TAV-01A/02A/034A/05A/06A/07A disponibili per sezioni, armature e particolari | tavole originali | DOC |
| SRC-004 | controllo geometrico | tavole architettoniche, prospetto e sezioni disponibili per controllo incrociato | TAV-01/02/03/04/05E/06E | DOC |
| GEO-001 | TAV.5 | carpenteria vettorializzata storicamente in DXF 1:1 | pacchetto DXF strutturale v25 | DOC-ARTEFATTO |
| GEO-002 | TAV.6 | travi vettorializzate storicamente in DXF | pacchetto DXF strutturale v25 | DOC-ARTEFATTO |
| GEO-003 | TAV.7 | pilastri vettorializzati storicamente in DXF | pacchetto DXF strutturale v25 | DOC-ARTEFATTO |
| GEO-004 | topologia TAV.5 | abaco storico con almeno 57 nodi e coordinate X,Y | ABACO_TOPOLOGICO_TAV5_v11.csv | DOC-ARTEFATTO |
| GEO-005 | topologia | 57 nodi / 38 connessioni / 10 componenti = sottoinsieme topologico storico, non assunto come universo geometrico completo | registri storici + presenza di riferimenti a ID superiori | DOC/INF-controllata |
| GEO-006 | modello globale | ricostruzione geometrica primaria deve ora partire dalle carpenterie originali, verificando gli artefatti DXF/CSV contro di esse | SRC-001/SRC-002 | IN_CORSO |
| GEO-007 | TAV.5 nodi fisici recuperati | recuperato nel repository il file canonico a 57 nodi topologici | `data/canonical/tav5_topology_nodes_57.csv` | PREDOC_TOPOLOGICO_RECUPERATO |
| GEO-008 | TAV.5 connessioni candidate | recuperato registro connessioni TAV.5 v07 con 141 connessioni candidate; alcune richiamano nodi oltre N057 | `data/canonical/tav5_topology_connections_v07.csv` | INF_DA_QUOTARE |
| COL-001 | pilastri | abaco verticale 27×5 | MATRICE_PILASTRI_27x5_v22.csv | DOC-ARTEFATTO |
| COL-002 | pilastri corpo principale | famiglie 40×50 e 40×40 cm | relazione di calcolo | DOC-famiglia |
| COL-003 | torrino scala | pilastri 30×40 cm | relazione di calcolo | DOC-famiglia |
| COL-004 | fili fissi/orientamento | da determinare e congelare livello per livello sulle carpenterie originali, con controllo di continuità verticale | TAV-01S..06S | IN_CORSO |
| BEAM-001 | Telaio 1 | percorso I-L-M-N-O-P-Q-R; 7 campate | relazione di calcolo / consolidato v12 | DOC |
| BEAM-002 | Telaio 1 | campate 4.70 / 5.10 / 3.25 / 2.40 / 2.90 / 5.30 / 4.70 m | relazione di calcolo / v12 | DOC |
| BEAM-003 | Telaio 1 G5 | C2-C6 | relazione di calcolo / v12 | DOC |
| BEAM-004 | Telaio 5 | percorso S-S'-T-U-V-Z-A'-B'-C' | relazione di calcolo / v17 | DOC |
| BEAM-005 | Telaio 5 | campate 4.70 / 4.05 / 1.20 / 5.80 / 2.90 / 1.20 / 4.05 / 4.70 m | relazione di calcolo / v17 | DOC |
| BEAM-006 | Telaio 5 G5 | C2-C7 = 19.20 m | relazione di calcolo / v17 | DOC |
| SEC-001 | travi | sezioni note: 20×45, 25×70, 30×45, 30×65, 120×20, 140×20 cm | relazione / consolidati | DOC |
| SEC-002 | Telaio 1 G2 | sezione non congelata | stato M0 v18 | ND |
| LOAD-001 | Telaio 5 | carichi lineari storici G1-G3 disponibili | RC-P13 / v16 | DOC-STORICO |
| FND-001 | fondazioni | 7 catene / 26 segmenti ricostruiti | consolidato fondazioni | DOC-ARTEFATTO |
| M0G-001 | modello globale | coordinate/reticolo da ricostruire prioritariamente dalle tavole originali, usando DXF e abachi come confronto | gate corrente | IN_CORSO |
| M0G-002 | livelli | quote Z definitive | non congelate | ND |
| M0G-003 | raccordo Telaio 5 ↔ 57 nodi | dataset fisico dei 57 nodi recuperato; raccordo ancora da dimostrare mediante firma metrica, topologia e carpenterie originali | `docs/DECISIONI/M0G_RECUPERO_ABACO_57_NODI_v1.md` + `data/canonical/tav5_topology_nodes_57.csv` | SBLOCCATO_DATI_RECUPERATI |
| MAT-001 | materiali | calcestruzzo/acciaio | da documentare/indagare | ND |
| MAT-002 | conoscenza | LC/FC | da definire sul quadro conoscitivo | ND |

## Regola di aggiornamento

Ogni nuova acquisizione deve aggiornare questo registro oppure un dataset canonico collegato prima di essere utilizzata come premessa per il modello.
