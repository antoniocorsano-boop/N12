# CEW-CONTRACT-01 — Qualification Report

**Date:** 12 ottobre 2026  
**Spec:** `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`  
**Plan:** `docs/superpowers/plans/2026-10-12-cew-contract-01-qualification.md`  
**Gate:** NOT_QUALIFIED

## 1. Esito

La qualifica non raggiunge il criterio di uscita 11/11 `PASS`.

Stato finale della matrice:

- `PASS`: 5 — C01-T03, T04, T05, T06, T08;
- `BLOCKED_INPUT`: 3 — C01-T02, T09, T10;
- `REVIEW_REQUIRED`: 3 — C01-T01, T07, T11;
- `FAIL`: 0;
- `BLOCKED_SOURCE`: 0;
- `NOT_RUN`: 0.

`NOT_QUALIFIED` è quindi l'esito obbligatorio del gate, non una valutazione discrezionale.

## 2. Cosa è stato dimostrato su N12

### Provenienza ed epistemologia

La branch operativa N12 contiene registri reali di Source, Evidence e Observation con source identity, SHA-256, locator immutabili, regioni localizzate e letture parziali/unreadable preservate. Il contratto non deve inventare questi concetti: essi corrispondono già a necessità reali del progetto.

### Conflict reale

Il conflitto TAV-07A ↔ TAV-06S sul supporto 24 dimostra che due fatti documentali incompatibili devono poter coesistere, essere governati da una Decision e restare riapribili con nuova evidenza. `C01-T03 = PASS`.

### Aggiornamento non distruttivo

Il revalidation ledger conserva old value, nuova Observation, risultato, new value e decision note; il pre-snapshot resta separato dal master corrente. `C01-T04 = PASS`.

### Identità strutturale

Alias storici e viste (`T5`, `G5`, campate, ID documentali) possono restare separati dall'identità persistente dell'elemento fisico. `C01-T05 = PASS`.

### Indipendenza tecnologica

Snapshot, Scenario, Conflict, Decision, Source/Evidence e identity sono rappresentabili senza rendere PostgreSQL, JSON Schema, IFC, CAD, EdiLus, OpenSees o altri strumenti parte del nucleo logico. `C01-T06 = PASS`.

### Relationship incerta

Il raccordo Telaio 5 ↔ TAV.5 conserva candidate bindings concorrenti, stati inferenziali e una decisione di non-promozione/rifiuto parziale. `C01-T08 = PASS`.

### Verification / Receipt

La HiRes machine review receipt dimostra una trasformazione reale con Source/blob/hash, parametri, run/artifact, findings e guardrail espliciti. Dimostra il sottocontratto Verification/Receipt, ma non sostituisce un SolverRun/Result strutturale.

## 3. Blocker reali

### B1 — nessun SolverRun/Result autorizzato

`CEW_PROJECT_STATE_CURRENT_v1.json` mantiene `R5 Solver Round Trip` in stato `PLANNED`. `M1E_CALCULATION_MODEL_HANDOFF_v1.json` dichiara `calculation_model_ready=false` e mantiene sei domini bloccanti.

Conseguenza: è vietato completare artificialmente la catena `ModelGeneration → SolverRun → Result`. La guardia del caso è `NO_SYNTHETIC_ENGINEERING_RESULT`.

Blocca:

- C01-T02 — provenienza completa fino a Result;
- C01-T09 — riproducibilità completa della run;
- C01-T10 — assurance end-to-end secondo il piano approvato.

### B2 — incertezza di misura non ancora formalizzata come tolleranza/intervallo

N12 contiene stati `MIS` e confronti/delta, ma questa qualifica non ha individuato un record che formalizzi in modo sufficiente una misura come valore + tolleranza/intervallo/metodo di stima secondo il requisito CEW-CONTRACT-01.

Conseguenza: C01-T07 resta `REVIEW_REQUIRED`; nessuna tolleranza viene ricavata a posteriori dai delta.

### B3 — minima sufficienza non completamente provata

L'audit individua:

- `SolverRun` e `Result` senza caso reale autorizzato;
- `Wall` elencato tra i tipi minimi V1 ma non esercitato da un caso N12;
- `ModelGeneration` sostenuto dagli handoff reali ma non ancora formalizzato come evento CEW con tutti gli attributi della spec.

Conseguenza: C01-T11 resta `REVIEW_REQUIRED`.

## 4. Correzione importante emersa durante l'esecuzione

La prima passata aveva ispezionato soltanto la branch documentale della PR e aveva classificato varie prove come `BLOCKED_SOURCE`. Il workflow N12 corrente richiama però esplicitamente `work/m0-global-model`, dove sono presenti i registri operativi Source/Evidence/Observation, conflitti, ledgers e snapshot.

L'audit è stato quindi riaperto e corretto. I blocker di fonte non supportati sono stati rimossi invece di essere trascinati nel risultato finale.

Questo è un esito positivo del metodo fail-closed: anche un blocker viene considerato una deduzione da verificare.

## 5. Significato del NOT_QUALIFIED

`NOT_QUALIFIED` **non** significa che l'architettura CEW-CONTRACT-01 sia stata confutata.

Significa più precisamente:

- cinque proprietà centrali del contratto hanno già casi N12 reali sufficienti;
- il patrimonio operativo N12 è molto più vicino al modello epistemico CEW di quanto mostrasse il solo ramo documentale;
- il gate completo richiede però prove che oggi il progetto stesso dichiara non ancora autorizzate, in particolare il Solver Round Trip;
- la spec resta **design approvato ma non qualificato**; il suo stato non viene modificato.

## 6. Prossimo passo minimo

Non è giustificato scegliere ora PostgreSQL, JSON Schema, IFC o il solver primario per “sbloccare” il gate.

Il passo minimo è separare tre closure item:

1. **Analysis slice reale:** quando i blocker necessari saranno chiusi o coperti da regole di assessment autorizzate, produrre un primo `SolverRun → Result` riproducibile e usarlo per C01-T02/T09/T10.
2. **Measurement uncertainty case:** registrare un caso reale con valore misurato, unità, tolleranza/intervallo e metodo di stima; poi rieseguire C01-T07.
3. **V1 minimality decision:** decidere esplicitamente se `Wall` resta subtype core oppure diventa estensione; formalizzare inoltre `ModelGeneration` sul primo evento derivativo reale. Poi rieseguire C01-T11/T01.

Solo dopo la chiusura dei test residui il gate può essere ricalcolato. Nessun PASS viene anticipato.
