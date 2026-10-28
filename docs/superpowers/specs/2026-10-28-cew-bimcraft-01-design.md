# CEW-BIMCRAFT-01 — BIMCraft Benchmark Design

**Data:** 28 ottobre 2026  
**Repository:** `antoniocorsano-boop/N12`  
**Canonical task:** `CEW-B01 — External Tool Qualification / N12 Vertical Slice`  
**Stato:** `PROPOSAL / BENCHMARK / NONCANONICAL / NOT ADOPTED`  
**Base CEW-B01:** `9df814471906a1e4ef618dc71563e78813f03075`

## 1. Decisione di architettura da conservare

BIMCraft viene valutato come possibile **motore BIM parametrico e agentico sostituibile** nella toolchain CEW, non come fonte di verità e non come software di calcolo strutturale.

Il ruolo candidato è:

`CEW Evidence / Canonical Knowledge -> thin adapter -> BIMCraft -> inspection / views / IFC -> downstream professional tools`

L'autorità resta CEW su:

- fonti originali;
- Evidence e provenienza;
- identità degli oggetti;
- stato epistemico `DOC / MIS / RIF / INF / INC / ND`;
- decisioni umane;
- geometria e modello canonici;
- assurance e ricevute.

Un file `.bimcraft`, una vista renderizzata o un IFC generato da BIMCraft sono **proiezioni rigenerabili**, mai autorità primaria.

## 2. Coerenza con il Master CEW

Il Master impone `BUILD LAST — REUSE FIRST`, adapter sottili verso strumenti esterni e la procedura:

`proposal -> benchmark N12 -> evidence -> human decision -> Master change`

Di conseguenza questa tranche **non modifica `CEW_MASTER_PLAN.md` e non promuove BIMCraft ad ADOPT**. Produce esclusivamente evidenza sufficiente per una successiva decisione umana.

`WIP = 1` resta rispettato: CEW-BIMCRAFT-01 è un benchmark subordinato al macro-task corrente CEW-B01, non un nuovo macro-task.

## 3. Upstream congelato per il benchmark

Repository upstream: `IPedrax/BIMCraft`  
Release: `v0.9.0`  
Tag object: `8b690b6c98a1b365c3524b126f6a3015371b5479`  
Exact commit: `c7ba8e2db8d7cc9fbf0847f23c8a56c8e02193f5`  
Release pubblicata: `2026-10-27T20:17:00Z`

Primo artefatto Linux x86_64 candidato:

- `bimcraft-0.9.0-linux-x86_64.AppImage`
- SHA-256: `69aef919a17f7916d3d3b5ab278cb16e27875669bf6b11c0815387d769b57c6f`

Il progetto v0.9.0 usa project-file format 6. La compatibilità dei file di progetto fra versioni non viene assunta: il benchmark deve essere rigenerabile da input CEW e versione upstream congelata.

## 4. Ipotesi da verificare, non assunte

L'analisi preliminare indica che BIMCraft espone un modello a comandi, CLI/MCP, interrogazione del modello, elementi strutturali e scambio IFC. Il benchmark deve dimostrare sul binario congelato, senza affidarsi alla sola documentazione, almeno:

1. avvio deterministico in ambiente CI compatibile;
2. identità/versione esatta del binario;
3. disponibilità effettiva dei comandi necessari;
4. creazione e successiva interrogazione di un piccolo insieme strutturale;
5. associazione di proprietà CEW agli oggetti quando supportata;
6. salvataggio come artefatto non canonico;
7. esportazione IFC realmente leggibile;
8. corrispondenza tra fixture CEW, modello BIMCraft e IFC;
9. comportamento fail-closed quando una capacità necessaria manca o cambia.

## 5. Ruolo candidato nel workflow

BIMCraft può essere promosso solo come uno o più dei seguenti ruoli:

- `BIM_PROJECTION_ENGINE`;
- `AGENTIC_MODEL_INSPECTION_ENGINE`;
- `HUMAN_VISUAL_REVIEW_ENVIRONMENT`;
- `IFC_PROJECTION_ENGINE`.

Non può essere promosso da questo benchmark come:

- fonte documentale;
- Knowledge Engine CEW;
- Canonical Structural Model;
- motore FEM;
- verificatore NTC;
- ricostruttore autonomo di armature;
- sostituto di EdiLus-EE;
- autorità professionale.

## 6. Strategia a due stadi

### Stage A — controlled noncanonical structural fixture

Prima si qualifica l'integrazione usando una fixture sintetica e dichiaratamente non N12, con valori espliciti e senza significato professionale. Scopo: provare il contratto tecnico senza contaminare il patrimonio conoscitivo N12.

La fixture minima deve includere, solo se supportati dal binario congelato:

- almeno un livello;
- un pilastro strutturale;
- una trave;
- un solaio strutturale;
- una fondazione disponibile nel catalogo comandi;
- proprietà CEW di prova.

### Stage B — N12-bound fixture

L'uso di oggetti N12 è consentito soltanto quando esistono input source-bound e human-reviewed compatibili con l'autorità CEW-B01.

L'attuale Step 5 di CEW-B01 è `PENDING_HUMAN`: pertanto CEW-BIMCRAFT-01 **non può inventare, importare dalla memoria della conversazione o promuovere** coordinate/identità strutturali N12 per anticipare quel gate.

Un eventuale patrimonio storico, compreso Telaio 5, può essere usato prima di quel gate soltanto come `BENCHMARK_ONLY / NONCANONICAL / NO_AUTHORITY`, con separazione fisica e semantica dagli output canonici.

## 7. Contratto di provenienza

Quando il tool lo consente, l'adapter deve propagare almeno i seguenti metadati:

- `CEW_OBJECT_ID`;
- `CEW_EVIDENCE_ID`;
- `CEW_SOURCE_SHA256`;
- `CEW_EPISTEMIC_STATE`;
- `CEW_REVISION`;
- `CEW_AUTHORITY`.

Per Stage A i valori devono dichiarare esplicitamente `BENCHMARK_ONLY` e non simulare identità N12.

Se BIMCraft o IFC non possono conservare un campo, la perdita deve essere registrata nel receipt; è vietato considerarlo implicitamente preservato.

## 8. Adapter boundary

Il codice CEW ammesso è sottile e deterministico:

`BenchmarkObject -> BIMCraftCommandPlan`

`BIMCraftObservation -> BenchmarkObservation`

`IFCObservation -> BenchmarkObservation`

L'adapter non deve:

- inferire proprietà tecniche mancanti;
- scegliere sezioni non presenti nell'input;
- correggere automaticamente geometrie;
- promuovere stati epistemici;
- utilizzare coordinate manuali non registrate;
- accedere a chiavi di firma o authority CEW;
- scrivere in `data/canonical`.

## 9. Assurance receipt

Ogni esecuzione reale deve produrre un receipt machine-readable contenente almeno:

- schema/versione del benchmark;
- exact CEW candidate SHA;
- exact BIMCraft tag e commit;
- nome e SHA-256 dell'artefatto eseguito;
- digest della fixture input;
- capability observation;
- command-plan digest;
- model/output digest quando disponibile;
- IFC digest quando disponibile;
- conteggi e identità degli oggetti osservati;
- proprietà attese/osservate;
- differenze;
- risultato `PASS / REWORK / BLOCKED`;
- `canonical_write_authorized=false`;
- `structural_identity_authorized=false`;
- `fem_authorized=false`;
- `master_change_authorized=false`.

## 10. Gate di qualificazione

### G0 — Upstream identity

PASS solo se versione, asset e SHA-256 coincidono con il lock governato.

### G1 — Capability contract

PASS solo se il binario espone realmente le capacità minime che il benchmark dichiara di usare. Nessun fallback silenzioso.

### G2 — Deterministic projection

La stessa fixture e lo stesso tool devono generare un command plan identico. Se l'output nativo contiene metadati non deterministici, questi devono essere separati dall'identità semantica verificata, non ignorati genericamente.

### G3 — Read-back

Gli oggetti creati devono essere interrogabili e riconciliabili con la fixture per categoria, livello, geometria/sezione disponibile e proprietà supportate.

### G4 — IFC boundary

Quando l'export è disponibile, l'IFC deve essere parsabile con IfcOpenShell e deve permettere una riconciliazione esplicita almeno per classi, conteggi, identificatori e proprietà CEW supportate.

### G5 — N12 authority boundary

PASS solo se nessun dato N12 viene creato/promosso al di fuori dei gate CEW correnti. Finché CEW-B01 Step 5 non riceve decisioni umane, Stage B resta bloccato o usa esclusivamente fixture storiche marcate non canoniche.

## 11. Esito ammesso

Il benchmark termina con una sola raccomandazione:

- `ADOPT_CANDIDATE` — evidenza sufficiente per chiedere una decisione umana di modifica del Master;
- `BENCHMARK_CONTINUE` — promettente ma evidenza incompleta;
- `DEFER` — utile ma non adatto alla fase corrente;
- `REJECT` — non soddisfa i requisiti CEW rilevanti.

Nessuna di queste classi modifica automaticamente il Master.

## 12. Relazione con OpenCADStudio

Il lavoro OpenCADStudio esistente resta separato. CEW-BIMCRAFT-01:

- non modifica PR #153/#155/#158/#161;
- non riusa authority o approval receipt OpenCADStudio;
- non avvia nuovi pilot live OpenCADStudio;
- confronta eventualmente i risultati solo dopo aver prodotto evidenza autonoma.

Questo evita conflitti tra due benchmark CAD/BIM e preserva l'isolamento delle rispettive catene di assurance.

## 13. Criterio di successo architetturale

BIMCraft è interessante per CEW solo se possiamo dimostrare la relazione:

`CEW governed input == BIMCraft observed model == IFC observed projection`

entro tolleranze e campi esplicitamente dichiarati, con provenienza verificabile e senza trasformare BIMCraft nel deposito della verità progettuale.

L'eventuale test `IFC -> EdiLus-EE` è un gate professionale successivo e separato: non viene confuso con la qualificazione del motore BIM/IFC.