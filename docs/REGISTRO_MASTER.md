# Registro Master N12

Versione repository: `RM-0016`

| ID | Ambito | Dato canonico / stato | Evidenza | Stato |
|---|---|---|---|---|
| SRC-001 | tavole originali | acquisite e catalogate 18 tavole PDF originali ad alta risoluzione | `docs/CATALOGO_TAVOLE_ORIGINALI.md` + `data/canonical/tavole_originali_manifest.csv` | DOC |
| SRC-002 | carpenterie | TAV-01S/02S/03S/04S/05S e TAV-06S copertura diventano fonte primaria per maglia, pilastri, travi e fili fissi | tavole originali | DOC-PRIMARIA |
| SRC-003 | armature | TAV-01A/02A/034A/05A/06A/07A disponibili per sezioni, armature e particolari del progetto originario; non sono attese le armature della successiva aggiunta del terrazzo al primo livello | tavole originali + conferma utente 2026-08-19 | DOC_ORIGINALE / LIMITE_NOTO |
| SRC-004 | controllo geometrico | tavole architettoniche, prospetto e sezioni disponibili per controllo incrociato | TAV-01/02/03/04/05E/06E | DOC |
| SRC-005 | foto ultimo piano/torrino | foto di campo dell'ultimo livello e torrino scala acquisita; hash SHA-256 c84764fcda31e2f203797dacf19ea87b1ed8496f529b8a4e29967153a198d6c5, 1152×1536 px | `ETW_UPPER_FLOOR_PHOTO_EVIDENCE_v1.md` | PHOTO_RIF_PRIMARY |
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
| COL-005 | sottotetto / piano ridotto | al livello superiore risultano assenti/terminati tre pilastri per ciascuna ala | conferma utente + TAV-06S/TAV-07A reconciliation | RIF + DOC_COUNT |
| COL-006 | TAV-06S / copertura | nella carpenteria di copertura sono rappresentati i pilastri che proseguono effettivamente fino alla copertura; presenza/assenza a posizione G4 risolta diventa evidenza di continuità/terminazione verticale | conferma utente 2026-08-19 + `ETW_G4_G5_ROOF_TRANSITION_v1.csv` | RIF_REGOLA_LETTURA / BINDING_IN_CORSO |
| COL-007 | torrino scala / copertura | TAV-06S può contenere pilastri locali/addizionali del torrino scala non appartenenti alle 27 catene ordinarie; vanno separati dalla popolazione di prosecuzione del telaio principale | conferma utente 2026-08-19 + foto ultimo piano/torrino | RIF / IDENTITA_ND |
| COL-008 | terminazioni superiori | nove terminazioni complessive chiuse e raggruppate 3+3+3 in tre rami topologici convenzionali: WING-A P31/P32/P33; WING-B P01/P09/P17; WING-C P08/P16/P21. I nomi delle ali sono convenzionali, non documentali | `ETW_UPPER_TERMINATIONS_BY_WING_v1.csv` | VER_PARZIALE_TOPOLOGICAL_GROUPING |
| BEAM-001 | Telaio 1 | percorso I-L-M-N-O-P-Q-R; 7 campate | relazione di calcolo / consolidato v12 | DOC |
| BEAM-002 | Telaio 1 | campate 4.70 / 5.10 / 3.25 / 2.40 / 2.90 / 5.30 / 4.70 m | relazione di calcolo / v12 | DOC |
| BEAM-003 | Telaio 1 G5 | C2-C6 | relazione di calcolo / v12 | DOC |
| BEAM-004 | Telaio 5 | percorso S-S'-T-U-V-Z-A'-B'-C' | relazione di calcolo / v17 | DOC |
| BEAM-005 | Telaio 5 | campate 4.70 / 4.05 / 1.20 / 5.80 / 2.90 / 1.20 / 4.05 / 4.70 m | relazione di calcolo / v17 | DOC |
| BEAM-006 | Telaio 5 G5 | C2-C7 = 19.20 m | relazione di calcolo / v17 | DOC |
| BEAM-007 | Telaio 5 ↔ TAV.5 | il telaio esiste e va allineato per sovrapposizione di sistemi; matrice candidati creata, nessuna promozione a VER senza overlay | `docs/DECISIONI/M0G_ALLINEAMENTO_TELAIO5_TAV5_v1.md` + `data/canonical/telaio5_tav5_candidate_matrix_v1.csv` | IN_ALLINEAMENTO |
| BEAM-008 | copertura | TAV-06S mostra tre distinte diciture `LINEA DI COLMO`, una per ciascun ramo di copertura; numero dei colmi chiuso documentalmente, estremi/supporti ancora da legare | `ETW_ROOF_RIDGE_EAVES_REGISTER_v1.csv` + TAV-06S HiRes | DOC_GEOMETRY / ENDPOINT_BINDING_PENDENTE |
| BEAM-009 | copertura | bordi di gronda/falda leggibili geometricamente sulla TAV-06S; la loro promozione a singole travi di gronda richiede binding degli estremi e dei supporti | `ETW_ROOF_RIDGE_EAVES_REGISTER_v1.csv` + TAV-06S HiRes | DOC_GEOMETRY + RIF_MEMBER / BINDING_PENDENTE |
| BEAM-010 | torrino scala | copertura del torrino resta sottosistema distinto dalla copertura principale a tre colmi | foto campo + `ETW_ROOF_RIDGE_EAVES_REGISTER_v1.csv` | PHOTO_RIF_PRIMARY / BINDING_PENDENTE |
| BEAM-011 | mansarde / terrazzo superiore | TAV-06E documenta lo sbalzo originario dell'ultimo impalcato oltre la linea degli appoggi; la foto mostra il bordo attuale e l'utente riferisce il successivo allungamento delle travi per aumentare la superficie utile delle mansarde | `ETW_UPPER_ATTIC_TERRACE_EXTENSION_v1.md` + `ETW_UPPER_CANTILEVER_RECONCILIATION_v1.csv` + foto campo | DOC_GEOMETRY_ORIGINALE + RIF_PROLUNGAMENTO / MEMBER_ID_PENDENTE |
| BEAM-012 | mansarde / genealogia elementi | creati candidati di genealogia senza falsi ID documentali: WING-A support line P28/P29/P30, WING-B P02/P10/P18; WING-C resta transizione composita. G4 beam IDs sono solo evidenza di asse/localizzazione e non vengono rinominati come travi a sbalzo superiori | `ETW_UPPER_CANTILEVER_BEAM_GENEALOGY_CANDIDATES_v1.csv` + `ETW_UPPER_CANTILEVER_WELL_FORMEDNESS_RULE_v1.md` | VER_PARZIALE / EXACT_UPPER_MEMBER_ID_ND |
| SEC-001 | travi | sezioni note: 20×45, 25×70, 30×45, 30×65, 120×20, 140×20 cm | relazione / consolidati | DOC |
| SEC-002 | Telaio 1 G2 | sezione non congelata | stato M0 v18 | ND |
| LOAD-001 | Telaio 5 | carichi lineari storici G1-G3 disponibili | RC-P13 / v16 | DOC-STORICO |
| FND-001 | fondazioni | 7 catene / 26 segmenti ricostruiti | consolidato fondazioni | DOC-ARTEFATTO |
| M0G-001 | modello globale | coordinate/reticolo da ricostruire prioritariamente dalle tavole originali, usando DXF e abachi come confronto | gate corrente | IN_CORSO |
| M0G-002 | livelli | quote Z definitive | non congelate | ND |
| M0G-003 | raccordo Telaio 5 ↔ 57 nodi | dataset fisico dei 57 nodi recuperato; raccordo ora in allineamento mediante firma metrica, topologia e carpenterie originali | `docs/DECISIONI/M0G_RECUPERO_ABACO_57_NODI_v1.md` + `data/canonical/tav5_topology_nodes_57.csv` | IN_ALLINEAMENTO |
| M0G-004 | altezza interpiano | altezza di piano estradosso-estradosso corretta a 3.20 m | `data/canonical/storey_height_status.csv` + `docs/DECISIONI/M0G_CORREZIONE_ALTEZZA_INTERPIANO_320_v1.md` | RIF_UTENTE_CORRETTO |
| TOPO-001 | primo livello | unico terrazzo in questo ambito: aggiunta strutturale successiva al telaio originario, realizzata al primo livello con pilastri e travi aggiunti innestati ai corrispondenti nodi del telaio preesistente; riferiti monconi/elementi di ancoraggio al nodo; tali armature non sono presenti nelle tavole originarie | `ETW_TOPOLOGY_VARIANTS_REGISTER_v1.csv` + conferma utente 2026-08-19 | RIF / AGGIUNTA_SUCCESSIVA / BINDING_NODI_PENDENTE |
| TOPO-002 | sottotetto | piano superiore/sottotetto a pianta ridotta con tre appartamenti dotati di terrazzo; foto campo conferma per la vista acquisita volume superiore arretrato, terrazzo/setback e torrino emergente | `ETW_TOPOLOGY_VARIANTS_REGISTER_v1.csv` + `ETW_UPPER_FLOOR_PHOTO_EVIDENCE_v1.md` | RIF + PHOTO_RIF_PRIMARY / BINDING_PENDENTE |
| TOPO-003 | copertura | tre ali / tre colmi documentati sulla TAV-06S; foto conferma almeno per la vista acquisita copertura principale a falde e copertura distinta del torrino | `ETW_ROOF_RIDGE_EAVES_REGISTER_v1.csv` + `ETW_UPPER_FLOOR_PHOTO_EVIDENCE_v1.md` | DOC_GEOMETRY + PHOTO_RIF_PRIMARY / ENDPOINT_BINDING_PENDENTE |
| TOPO-004 | G1↔G2 | registrazione controllata TAV-02S/G1 → TAV-03S/G2 completata: 1046 match, 510 inlier, rapporto 0.4876, RMSE 1.05 px @100 DPI; 186 candidati differenziali | GitHub Actions run `32277543302` + `ETW_FIRST_LEVEL_TERRACE_G12_CANDIDATES_v1.csv` | INF_CONTROLLATA / REVIEW_IN_CORSO |
| TOPO-005 | terrazzo legacy ETW-1 | il precedente `terrace_probe.py` su TAV-05S/G4 è SUPERATO per l'identificazione del terrazzo del primo livello; resta solo provenienza ETW-1/TAV-05S. Il conflitto coordinate N039 è residuo aperto | `ETW_LEGACY_TERRACE_BINDING_AUDIT_v1.md` | SUPERATO_PER_TERRAZZO_PRIMO_LIVELLO |
| TOPO-006 | terrazzo primo livello / armature | la ricerca delle armature dell'aggiunta nelle tavole originarie è chiusa come non applicabile: intervento successivo; dettagli di barre/diametri/lunghezze di ancoraggio restano ND salvo diversa documentazione o rilievo | conferma utente 2026-08-19 | RIF_CRONOLOGIA / ND_DETTAGLIO |
| TOPO-007 | G4↔G5 / transizione copertura | confronto controllato TAV-05S/G4 → TAV-06S/G5 completato per registrazione e directional probe; support-presence reconciliation chiude 25 continuità e 9 terminazioni | `ETW_G4_G5_ROOF_TRANSITION_v1.csv` + `ETW_TAV06S_ROOF_SUPPORT_INVENTORY_v1.csv` + workflow run `32286265838` | VER_PARZIALE |
| TOPO-008 | mansarde / ampliamento successivo | bordo attuale delle mansarde non coincide necessariamente con il telaio originario: distinguere linea pilastri/nodi originari, sbalzo originario documentato e prolungamento successivo che ha ampliato la superficie utile | `ETW_UPPER_ATTIC_TERRACE_EXTENSION_v1.md` + `ETW_UPPER_CANTILEVER_WELL_FORMEDNESS_RULE_v1.md` | DOC_GEOMETRY + RIF_CRONOLOGIA / GENEALOGIA_PARZIALE |
| MAT-001 | materiali | calcestruzzo/acciaio | da documentare/indagare | ND |
| MAT-002 | conoscenza | LC/FC | da definire sul quadro conoscitivo | ND |

## Regola di aggiornamento

Ogni nuova acquisizione deve aggiornare questo registro oppure un dataset canonico collegato prima di essere utilizzata come premessa per il modello.
