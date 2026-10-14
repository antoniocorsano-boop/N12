# CEW-CONTRACT-01 — Disegno di chiusura dei tre residui

**Data:** 13 ottobre 2026  
**Stato:** design approvato in chat; specifica scritta in revisione umana  
**PR:** #147  
**Caso pilota:** N12  
**Ambito:** chiusura dei tre residui che impediscono la qualifica di CEW-CONTRACT-01 senza anticipare CEW-FEM-01 né inventare dati tecnici.

## 1. Scopo

Questa specifica integra e corregge in modo mirato `2026-10-12-cew-contract-01-design.md` per chiudere tre residui emersi dalla qualifica iniziale:

1. dipendenza circolare `CEW-CONTRACT-01 ↔ SolverRun/Result`;
2. assenza di un caso N12 formalizzato di incertezza associata a una registrazione/misura reale;
3. minima sufficienza non dimostrata per `Wall` e `ModelGeneration`.

La chiusura deve preservare gli invarianti già approvati:

- nessun dato tecnico inventato;
- nessuna inferenza promossa a dato documentale;
- nessun solver scelto implicitamente dal contratto logico;
- nessuna esecuzione strutturale dello stato corrente finché il progetto N12 non la autorizza;
- nessuna entità V1 obbligatoria senza un caso reale che ne dimostri la necessità;
- nessuna perdita di provenienza, stato epistemico o storia delle decisioni.

## 2. Autorità, precedenza e riferimenti N12

Questa specifica prevale sulla specifica del 12 ottobre 2026 solo per i punti esplicitamente modificati qui.

Restano invariati tutti gli altri principi e contratti di CEW-CONTRACT-01.

In caso di conflitto, vale l'ordine:

1. presente specifica di chiusura;
2. `2026-10-12-cew-contract-01-design.md`;
3. piano/artefatti di qualifica derivati;
4. implementazioni e report.

Per i tre residui sono autorizzati come casi di prova, senza attribuire loro autorità superiore a quella già registrata nel repository:

- `data/canonical/M1E_CALCULATION_MODEL_HANDOFF_v1.json` — autorità sul fatto che il modello di calcolo corrente non è autorizzato (`calculation_model_ready=false`) e sui relativi blocker;
- `data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv` — osservazioni reali degli scarti di registrazione geometrica in pixel;
- `scripts/cew_structural_model_builder.py` e l'output governato che esso produce — caso reale di generazione di un grafo strutturale solver-independent.

Questi riferimenti non autorizzano nuove proprietà tecniche, nuovi valori di progetto o esecuzioni solver.

## 3. Residuo 1 — separazione CEW-CONTRACT-01 / CEW-FEM-01

### 3.1 Problema

La specifica iniziale richiedeva, per il PASS di CEW-CONTRACT-01, un caso end-to-end reale comprendente `SolverRun → Result`.

Contemporaneamente rinviava la scelta e qualifica del solver a `CEW-FEM-01`.

Sul caso N12, inoltre, il handoff corrente dichiara `calculation_model_ready=false` e vieta una verifica strutturale dello stato corrente quando i domini tecnici necessari non sono supportati o ammessi da una regola di scenario esplicita.

Questa combinazione crea una dipendenza circolare: il contratto logico non può qualificarsi senza un solver, ma il solver non dovrebbe essere adottato prima che il contratto logico sia qualificato.

### 3.2 Decisione architetturale

`SolverRun` e `Result` restano concetti CEW validi, ma **non costituiscono più requisito di uscita operativo di CEW-CONTRACT-01**.

Il confine diventa:

### CEW-CONTRACT-01

`Source → Evidence → Observation → Claim → Decision → CanonicalProperty → CanonicalSnapshot → Scenario → ModelGeneration → Projection → Verification → Receipt`

### CEW-FEM-01

`ModelGeneration → SolverRun → Result → Verification → Receipt`

`CEW-FEM-01` deve riusare Snapshot, Scenario, ModelGeneration, identità CEW e provenienza definiti dal contratto logico; non può ridefinirli in forma solver-specifica.

### 3.3 Conseguenze

- Nessun solver viene scelto o incorporato nel core CEW-CONTRACT-01.
- Non viene creato un `Result` fittizio per rendere verde il gate.
- Non viene eseguito un calcolo N12 non autorizzato.
- La futura prova `SolverRun → Result → CEW Object` resta obbligatoria, ma viene spostata nel gate che ha l'autorità per qualificare un adapter FEM.
- La provenienza end-to-end del core viene dimostrata fino alla `Projection` derivata e alla relativa `Verification/Receipt`.

### 3.4 Modifica ai test di conformità

Il precedente test di provenienza completa viene scisso in due livelli:

**C01 core:**

`Projection/Verification/Receipt → ModelGeneration → Scenario → CanonicalSnapshot → CanonicalProperty → Decision → Claim → Observation → Evidence → Source`

**FEM extension:**

`Result → SolverRun → ModelGeneration → ... → Source`

Un `Result` reale non è più necessario per dichiarare qualificato CEW-CONTRACT-01, ma resta necessario per dichiarare qualificato CEW-FEM-01.

## 4. Residuo 2 — incertezza di registrazione reale N12

### 4.1 Fonte del caso pilota

Il caso N12 usa `data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv`, che conserva per supporti reali del piano terra:

- coordinate osservate in pixel;
- coordinate previste dalla trasformazione;
- scarti `du_px`, `dv_px`;
- modulo del residuo `residual_px`;
- stato diagnostico `PASS_DIAGNOSTIC` o `WATCH`;
- classe di evidenza.

Questi dati sono osservazioni reali del processo di registrazione. **Non sono una tolleranza normativa, un errore standard, una deviazione standard, una precisione certificata dello strumento o una misura di accuratezza metrologica.**

### 4.2 Rappresentazione CEW richiesta

Il caso deve essere formalizzato come `REGISTRATION_UNCERTAINTY` o struttura logica equivalente collegata alla proprietà geometrica registrata.

Campi minimi:

- `uncertainty_type = REGISTRATION_UNCERTAINTY`;
- oggetto/proprietà cui si riferisce;
- valore nominale osservato;
- unità;
- origine/source/evidence;
- metodo di registrazione;
- residuo osservato vettoriale (`du`, `dv`), se disponibile;
- residuo osservato scalare, se disponibile;
- eventuale intervallo/bound **solo se derivato esplicitamente da una regola dichiarata**;
- stato epistemico della coordinata/proprietà di base;
- stato diagnostico;
- note sui limiti di interpretazione.

### 4.3 Regola anti-invenzione

`residual_px` non deve essere rinominato “tolleranza”, “errore standard”, “incertezza standard” o “accuratezza”.

Se viene costruito un **bound diagnostico derivato**, la trasformazione deve dichiarare:

- formula;
- input;
- unità;
- natura `DERIVED_DIAGNOSTIC`;
- assenza di valore metrologico certificato;
- impossibilità di promuoverlo a `DOC` o `MIS` come nuova misura autonoma.

Il PASS del contratto **non richiede** di fabbricare un intervallo `±x` quando la fonte non lo dichiara. È sufficiente che il modello distingua correttamente valore osservato, residuo reale, eventuale bound derivato e limiti del metodo.

### 4.4 Criterio di PASS

Il test C01-T07 passa se almeno un caso N12 reale presenta:

1. proprietà registrata/misurata reale;
2. provenienza completa;
3. metodo dichiarato;
4. scarto/residuo osservato;
5. eventuale bound derivato separato dalla misura di base;
6. nessuna promozione epistemica impropria;
7. classificazione esplicita che impedisce di scambiare il residuo di registrazione per incertezza metrologica certificata.

La precedente formulazione “misura con tolleranza” viene quindi precisata in “misura/registrazione con incertezza o discrepanza caratterizzata secondo il metodo disponibile”.

## 5. Residuo 3A — `Wall` e minima sufficienza

### 5.1 Problema

La specifica iniziale elencava `Wall` tra i tipi minimi V1, ma la qualifica N12 non dimostra che un'entità `Wall` autonoma sia necessaria al contratto core.

Forzare un pilastro-setto, un supporto esteso o altro oggetto N12 dentro `Wall` soltanto per soddisfare una cardinalità di schema violerebbe il criterio di minima sufficienza.

### 5.2 Decisione

I tipi strutturali vengono distinti in:

**Core V1 obbligatorio:** tipi dimostrati da casi reali del gate.

**Tassonomia estendibile:** tipi legittimi ma non obbligatori per il PASS del core.

`Wall` passa nella tassonomia estendibile finché un caso reale non ne richiede l'identità strutturale autonoma.

Questa decisione non vieta `Wall`; vieta soltanto di renderlo obbligatorio senza necessità dimostrata.

### 5.3 Regola generale di minima sufficienza

Un subtype del modello strutturale può essere:

- `CORE_REQUIRED` — richiesto da almeno un caso reale del gate;
- `SUPPORTED_EXTENSION` — supportato dal contratto ma non richiesto dal gate corrente;
- `DEFERRED` — non ancora definito/qualificato.

Il validator deve fallire se un tipo viene marcato `CORE_REQUIRED` senza una giustificazione/caso di conformità associato.

## 6. Residuo 3B — formalizzazione di ModelGeneration

### 6.1 Caso reale disponibile

N12 dispone di `scripts/cew_structural_model_builder.py`, che genera un grafo strutturale solver-independent da artefatti canonici promossi, senza estrarre geometria dalle tavole e senza creare connettività per prossimità geometrica.

Il builder incorpora già:

- riferimenti agli input canonici;
- hash degli input;
- identificatore di generazione;
- inventario;
- sistema di coordinate;
- stato del modello;
- residui espliciti;
- usi autorizzati e non autorizzati.

### 6.2 Decisione

Questo processo costituisce il caso pilota N12 per `ModelGeneration`, purché la qualifica aggiunga e verifichi in modo esplicito almeno:

- `canonical_snapshot_id` o riferimento univoco equivalente allo stato congelato;
- `scenario_id` nullo o esplicito;
- profilo di generazione;
- adapter/builder e versione;
- parametri;
- input + hash;
- output + hash;
- warning/residui;
- timestamp;
- `Verification` associata;
- `Receipt` associato.

Se uno di questi campi non esiste ancora nel pacchetto prodotto, va aggiunto nella fase di implementazione prima di dichiarare PASS.

### 6.3 Divieto

La formalizzazione di `ModelGeneration` non autorizza di per sé un `SolverRun`.

Un modello derivato può essere valido come proiezione/grafo CEW pur restando non autorizzato al calcolo strutturale corrente.

## 7. Gate aggiornato CEW-CONTRACT-01

Il gate continua ad avere 11 test, ma i test interessati vengono reinterpretati come segue:

- `C01-T01` — rappresentabilità N12: PASS solo se tutti i concetti core necessari sono rappresentabili senza campi N12-specifici; `Wall` non è richiesto se resta `SUPPORTED_EXTENSION`.
- `C01-T02` — provenienza completa core: chiusura end-to-end da Projection/Receipt fino a Source; la parte SolverRun/Result è rinviata a CEW-FEM-01.
- `C01-T07` — incertezza: usa un caso reale N12 di registrazione/misura con residuo e metodo; eventuali bound restano derivati e non metrologici salvo fonte esplicita.
- `C01-T09` — riproducibilità: usa la ModelGeneration N12 formalizzata con Snapshot/Scenario/adapter/versione/parametri/input/output/hash.
- `C01-T10` — assurance: almeno una trasformazione reale attraversa input → output → Verification → Receipt e include uno stato non banalmente PASS quando applicabile.
- `C01-T11` — minima sufficienza: ogni entità/tipo `CORE_REQUIRED` ha almeno un caso reale; ciò che non è necessario viene riclassificato senza essere fittiziamente istanziato.

Gli altri test restano invariati.

## 8. Criterio di uscita aggiornato

CEW-CONTRACT-01 può diventare `QUALIFIED` solo se:

1. tutti gli 11 test del gate risultano `PASS` sull'exact head;
2. nessun PASS dipende da un `SolverRun` o `Result` fittizio;
3. la ModelGeneration è reale, riproducibile e receipt-gated;
4. il caso di incertezza usa dati N12 reali e distingue osservazione/residuo da eventuale bound derivato;
5. `Wall` o altri tipi non necessari non vengono fabbricati per soddisfare il test;
6. non vengono introdotti concetti specifici di OpenSees, EdiLus, Code_Aster, IFC o CAD nel nucleo logico;
7. nessuna modifica rende `calculation_model_ready=true` nel progetto N12;
8. il report finale registra esplicitamente il debito trasferito a CEW-FEM-01:
   `ModelGeneration → SolverRun → Result → Verification → Receipt`.

Risultato atteso:

> CEW-CONTRACT-01 dimostra sul caso reale N12 un contratto logico completo e riproducibile fino alle proiezioni derivate e alla loro assurance, senza anticipare né simulare un calcolo strutturale. La catena solver/result resta un gate obbligatorio e separato di CEW-FEM-01.

## 9. Fuori ambito di questa chiusura

Non devono essere introdotti in questa attività:

- scelta del solver primario;
- implementazione OpenSeesPy/Code_Aster/EdiLus;
- calcolo strutturale N12;
- modifica dei valori di materiali, LC, FC, carichi, geotecnica o fondazioni;
- nuovo modello normativo;
- IFC/CAD adapter;
- nuove evidenze tecniche non già presenti nelle fonti autorizzate;
- promozione dei residui geometrici a precisione metrologica certificata.

## 10. Artefatti previsti dall'implementazione

L'implementazione successiva dovrà aggiornare, nel minimo perimetro necessario:

- documentazione del gate CEW-CONTRACT-01;
- matrice/test di qualifica;
- fixture/caso N12 per `REGISTRATION_UNCERTAINTY`;
- manifest/receipt della ModelGeneration;
- validator della minima sufficienza;
- report finale di qualifica;
- eventuale PR body per riflettere il nuovo esito.

Le modifiche a codice o script devono seguire TDD RED → GREEN e non possono dichiarare `QUALIFIED` prima dell'esecuzione completa del gate sull'exact head.

## 11. Review focus

La review finale deve controllare specificamente:

1. che lo spostamento di SolverRun/Result a CEW-FEM-01 non riduca la tracciabilità del core;
2. che il caso di incertezza non confonda residuo di registrazione con tolleranza o incertezza metrologica certificata;
3. che `Wall` non venga rimosso dalla tassonomia generale, ma soltanto dall'obbligo di istanziazione del core gate;
4. che ModelGeneration punti a uno stato canonico immutabile e identificabile;
5. che nessuna modifica autorizzi implicitamente un calcolo N12 oggi vietato;
6. che il passaggio finale da NOT_QUALIFIED a QUALIFIED sia prodotto esclusivamente dai test e dalle evidenze del nuovo exact head.
