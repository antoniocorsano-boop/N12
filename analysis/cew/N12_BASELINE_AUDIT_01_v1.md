# N12-BASELINE-AUDIT-01 — Baseline conoscitiva canonica v1

**Stato:** PASS — BASELINE_FROZEN / M1E_RESIDUAL_EXECUTION  
**Data:** 2026-10-09  
**Base verificata:** `docs/n12-canonical-execution-plan-v1@fc7424ee43420d80ce20d5e6b3c9c752abc51809`  
**Piano sovraordinato:** `docs/REFERENCE/N12_CANONICAL_EXECUTION_PLAN_v1.md`

## 1. Obiettivo

Eseguire l'audit stretto richiesto dal piano canonico per evitare ricostruzioni inutili e distinguere:

- ciò che è già validato e deve essere **RIUSATO**;
- ciò che esiste ma richiede una verifica circoscritta;
- ciò che è stato superato e non deve essere riattivato;
- ciò che manca realmente e costituisce un blocker per `CALCULATION_MODEL_READY`.

L'audit non crea nuova geometria, non assegna valori mancanti e non modifica autorità ingegneristica.

## 2. Fonti canoniche lette

L'audit è fondato su:

- `knowledge/CONTEXT_PACK_CURRENT.json`;
- `knowledge/KNOWLEDGE_MANIFEST.json`;
- `knowledge/CURRENT_STATE.json`;
- `knowledge/ARTIFACT_REGISTRY.csv`;
- `docs/PROTOCOLLO_CANONICO.md`;
- `data/canonical/M0G_GEOMETRY_HANDOFF_v1.json`;
- `data/canonical/M1S_SECTION_GATE_v1.csv`;
- `data/canonical/M1M_MATERIAL_GATE_v1.csv`;
- `data/canonical/M1A_REINFORCEMENT_GATE_v1.csv`;
- `data/canonical/M1L_LOAD_GATE_v1.csv`;
- `data/canonical/M1F_PRIMARY_GEOMETRY_GATE_v1.csv`;
- `data/canonical/M1F_FPEP_RELEASE_GATE_v1.csv`;
- `data/canonical/M1F_FOUNDATION_GATE_v1.csv`;
- `data/canonical/M1E_CALCULATION_MODEL_HANDOFF_v1.json`;
- `docs/M1A_SPECIAL_FEATURES_COMPLETENESS_REVIEW_v1.md`.

## 3. Esito sintetico

La Baseline v1 dimostra che **N12 non è in una fase di ricostruzione geometrica iniziale**. Il repository contiene già una catena strutturale avanzata e governata.

### 3.1 Da RIUSARE — nessuna ricostruzione globale

#### M0-G — geometria/topologia globale

- stato: `PASS_WITH_WATCH` / frozen;
- 629 nodi analitici;
- 464 rigid-joint links;
- 359 membri strutturali ordinari;
- 232 travi ordinarie;
- 127 segmenti verticali di pilastro;
- 1 componente analitica con 0 nodi orfani;
- riapertura consentita soltanto tramite procedura `M0G-REOPEN` con nuova evidenza primaria.

**Classificazione audit:** `RIUSA`.

#### M1-S — sezioni

- 359/359 membri ordinari con sezione utilizzabile;
- 0 sezioni ND;
- 5 watch di evidenza;
- 1 elemento `SUPPORTED` non promosso a DOC.

**Classificazione audit:** `RIUSA`.

#### M1-F — geometria primaria e modello fondazioni

Il workflow FPEP risulta già rilasciato:

- P00–P07: chain completa;
- P08–P11: cross-check completati;
- 38 supporti primari;
- 55 incidenze/membri fondazione correnti;
- 1 componente con 0 supporti orfani;
- precedente topologia 58 membri esplicitamente declassata a storia/regressione;
- `M1F_FPEP_RELEASE = PASS_WITH_WATCH`;
- `M1F_FOUNDATION_GATE = FOUNDATION_STRUCTURAL_ASSEMBLY_COMPLETE_WITH_EXECUTION_WATCHES`.

**Classificazione audit:** `RIUSA` per identità/topologia; `VERIFICA` solo per i watch numerici/proprietà espliciti.

#### M1-L — modello semantico dei carichi

- schema e load-path canonici presenti;
- distinzione storico / as-built preservata;
- zero valori numerici inventati;
- gate `PASS_WITH_WATCH`.

**Classificazione audit:** `RIUSA` per struttura semantica; `MANCANTE` per valori numerici necessari all'esecuzione.

#### M1-A — armature

- sei fonti primarie immutabili indicizzate;
- gruppi ordinari trascritti e source-bound;
- 165/165 righe pilastro classificate;
- special features mantenute in sottosistemi separati;
- gate `PASS_WITH_WATCH` sufficiente per rilasciare M1-L ma non per tutte le verifiche member-level.

**Classificazione audit:** `RIUSA` per inventario e binding già chiusi; `VERIFICA/MANCANTE` solo sui residui espliciti.

## 4. Artefatti da considerare SUPERATI o solo storici

### 4.1 Vecchie ricostruzioni geometriche

Le ricostruzioni storiche anteriori alla pipeline corrente non devono essere usate come autorità quando il registry le marca `HISTORICAL_ONLY`, `SUPERSEDED` o `SUSPENDED`.

In particolare:

- vecchie griglie/mesh PT storiche: non devono rigenerare M0-G;
- vecchia topologia fondazioni a 58 membri: regressione/storia soltanto dopo FPEP;
- una coincidenza con dataset storici non riapre automaticamente un gate corrente.

**Classificazione audit:** `DEPRECATO` come input canonico; conservazione obbligatoria per provenance/regression.

## 5. Disallineamento dello stato macchina — RISOLTO

L'audit aveva rilevato che `knowledge/CURRENT_STATE.json` conservava campi FPEP storici (`READY_P00 / NOT_YET_PROMOTED`) non coerenti con i gate downstream già chiusi.

Il riallineamento è stato applicato e protetto da regressione:

- `knowledge/CURRENT_STATE.json` è ora sul gate `M1-E/CALCULATION_MODEL_HANDOFF`;
- FPEP è `RELEASED_PASS_WITH_WATCH`;
- il modello fondazioni corrente è `FOUNDATION_STRUCTURAL_ASSEMBLY_COMPLETE_WITH_EXECUTION_WATCHES`;
- la topologia corrente resta 38 supporti / 55 membri;
- `KNOWLEDGE_MANIFEST.json` è riallineato al fronte M1E;
- l'istruzione storica è conservata in `analysis/cew/N12_CURRENT_STATE_ALIGNMENT_REQUIRED_v1.json` come `STATE_DRIFT_RESOLVED` e **non deve essere riapplicata**.

**Classificazione corrente:** `CLOSED — ANTI_RESTART_GUARDED`.

## 6. Veri blocker per CALCULATION_MODEL_READY

La fonte più vicina al gate finale, `M1E_CALCULATION_MODEL_HANDOFF_v1.json`, registra sei domini bloccanti indipendenti.

### B01 — Materiali correnti / livello di conoscenza

Disponibile e riusabile:

- calcestruzzo storico `R'=300 kg/cm²` come evidenza documentale storica;
- acciaio `FeB38k` come evidenza documentale storica.

Mancano realmente:

- resistenza attuale in situ del calcestruzzo;
- LC;
- FC.

**Classificazione:** `MANCANTE — EVIDENZA/DECISIONE PROFESSIONALE`.

### B02 — Carichi, masse e combinazioni numeriche

La struttura semantica è chiusa. Il backlog numerico è ora finito e governato da:

- `data/canonical/M1E_B02_LOAD_RESIDUAL_REGISTER_v1.csv` — 16 righe;
- `data/canonical/M1E_B02_LOAD_GATE_v1.csv` — `RESIDUAL_SCOPE_BOUND_16_OPEN`.

Nessun Gk, Qk, peso unitario, massa, eccentricità o fattore di combinazione viene introdotto dal backlog.

**Classificazione:** `MANCANTE/VERIFICA — BACKLOG FINITO 16 RIGHE`.

### B04 — Quota numerica delle fondazioni

Disponibile:

- piano simbolico comune `ZF_COMMON`;
- riferimento storico 1.00 m sotto piano di campagna come informazione storica.

Manca:

- relazione diretta e verificata fra G1, terreno e datum fondazione numerico.

**Classificazione:** `MANCANTE — RILIEVO/DATUM VERTICALE`.

### B05 — Proprietà di 15 membri di fondazione

Disponibile:

- 39 binding diretti TAV-01A;
- 1 binding `SUPPORTED`;
- 15 incidenze con `ND_DOCUMENTARY_COVERAGE`.

Mancano:

- 15 binding esatti sezione/armatura longitudinale.

**Classificazione:** `MANCANTE — EVIDENZA DOCUMENTALE O INDAGINE`; vietato colmare per analogia.

### B06 — Residui armature sovrastruttura

Il gate M1-A è `PASS_WITH_WATCH`. Il residuo è ora finito e governato da:

- `data/canonical/M1E_B06_SUPERSTRUCTURE_REINFORCEMENT_RESIDUAL_REGISTER_v1.csv` — 21 righe;
- `data/canonical/M1E_B06_SUPERSTRUCTURE_REINFORCEMENT_GATE_v1.csv` — `RESIDUAL_SCOPE_BOUND_21_OPEN`.

Le 21 righe sono separate in 11 attività mirate su fonti già governate e 10 casi che richiedono nuova evidenza oppure esclusione tracciabile dello scope.

**Classificazione:** `VERIFICA/MANCANTE — BACKLOG FINITO 21 RIGHE`.

### B07 — Modello geotecnico corrente

Mancano realmente:

- stratigrafia sito-specifica corrente;
- falda/groundwater screening;
- parametri di resistenza attuali;
- parametri di rigidezza/cedimento attuali.

I dati storici di pressione ammissibile non vengono convertiti automaticamente in parametri moderni.

**Classificazione:** `MANCANTE — DOCUMENTAZIONE/INDAGINE GEOTECNICA CORRENTE`.

## 7. Cosa NON deve essere fatto adesso

- non ricostruire i 629 nodi M0-G;
- non ricostruire le 359 sezioni;
- non riusare la vecchia topologia fondazioni 58 membri come autorità;
- non rieseguire FPEP P00–P11;
- non riapplicare lo `STATE_DRIFT` già risolto;
- non trasformare GeoEngineAI in fonte canonica;
- non lanciare una verifica strutturale corrente con materiali, carichi, Z o geotecnica inventati;
- non colmare i 15 binding fondazione per analogia;
- non riaprire M0-G per chiudere residui di scala, balconi, gronde o altri sottosistemi speciali.

## 8. GeoEngineAI — classificazione nell'audit

GeoEngineAI è classificato `VERIFICA — CANDIDATE_SPECIALIST_ENGINE`.

Capability potenzialmente riusabili:

- trasformazioni CRS tramite `proj4`;
- analisi geometrica/spaziale tramite Turf;
- parsing DXF;
- rendering Three.js;
- DTM/profili topografici;
- moduli geotecnici e bearing-capacity;
- architettura deterministic-engine -> snapshot -> AI interpreter, compatibile concettualmente con il confine CEW fra calcolo deterministico e interpretazione IA.

Vincolo:

- nessun output GeoEngineAI diventa `DOC/MIS/CANONICAL` per il solo fatto di essere prodotto dal motore;
- DTM o stratigrafie inferite/fallback restano `INF/VERIFICA` finché non sono sostenuti da fonte/misura;
- prima del riuso deve essere verificato il contratto input/output e la compatibilità con gli ID/provenance CEW.

## 9. Prossimo passo canonico derivato dall'audit

La **Fase 0 è chiusa**. Non richiede nuova modellazione globale né ulteriori riallineamenti di stato.

Il lavoro corrente è esclusivamente `M1E-CALCULATION-MODEL-HANDOFF` sui sei blocker reali. La priorità operativa è:

1. B06 tramite il registro finito da 21 righe, limitando l'attività interna alle 11 righe `EXISTING_GOVERNED_SOURCE_TARGETED`;
2. B02 tramite il registro finito da 16 righe, senza assegnazioni numeriche non autorizzate;
3. B04, B05, B01 e B07 soltanto secondo i requisiti di evidenza/decisione già registrati;
4. GeoEngineAI solo come acceleratore specialistico subordinato all'autorità CEW.

## 10. Gate di uscita N12-BASELINE-AUDIT-01

Stato corrente: `PASS`.

Completato:

- matrice di classificazione persistita in `analysis/cew/N12_BASELINE_AUDIT_MATRIX_v1.csv`;
- checkpoint `RIUSA` identificati e protetti da anti-restart;
- artefatti `DEPRECATO` esclusi dall'autorità corrente;
- sei blocker M1E identificati come sola lista di blocchi per `CALCULATION_MODEL_READY`;
- `CURRENT_STATE` e `KNOWLEDGE_MANIFEST` riallineati a M1E;
- registri finiti B02 e B06 collegati all'handoff e ai relativi gate;
- istruzione di allineamento storica marcata `STATE_DRIFT_RESOLVED`.

**Residui di Fase 0:** nessuno. Il lavoro successivo non deve riaprire l'audit, ma consumare esclusivamente i backlog M1E correnti.
