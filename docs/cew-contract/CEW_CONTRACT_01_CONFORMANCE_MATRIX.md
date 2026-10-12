# CEW-CONTRACT-01 — Conformance Matrix

**Spec:** `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`  
**Qualification plan:** `docs/superpowers/plans/2026-10-12-cew-contract-01-qualification.md`  
**Rule:** uno stato diverso da `PASS` resta aperto o bloccato; nessun test viene promosso per deduzione.

| ID | Test | Status | Criterion | Evidence |
|---|---|---|---|---|
| C01-T01 | Rappresentabilità N12 | NOT_RUN | I casi N12 richiesti dalla spec sono rappresentabili senza campi N12-specifici. | — |
| C01-T02 | Provenienza completa | NOT_RUN | Un Result reale è risalibile fino alla Source originale attraverso tutta la catena CEW. | — |
| C01-T03 | Conflict reale | NOT_RUN | Due proposizioni reali incompatibili possono coesistere senza scelta prematura. | — |
| C01-T04 | Aggiornamento non distruttivo | NOT_RUN | Nuova evidenza crea nuovo stato senza riscrivere snapshot/run/risultati precedenti. | — |
| C01-T05 | Identità strutturale | NOT_RUN | L'identità fisica resta stabile attraverso revisioni di proprietà; alias non sono ID primari. | — |
| C01-T06 | Indipendenza dallo strumento | NOT_RUN | Il nucleo logico non dipende da CAD, IFC, solver, database o serializzazione specifici. | — |
| C01-T07 | Incertezza | NOT_RUN | ND, DOC conflittuale, misura con tolleranza, INF e Assumption di Scenario restano distinguibili. | — |
| C01-T08 | Relationship incerta | NOT_RUN | Una Relationship può avere Evidence, stato epistemico, Conflict e Decision propri. | — |
| C01-T09 | Riproducibilità | NOT_RUN | ModelGeneration e SolverRun identificano univocamente snapshot/scenario/versioni/input/output. | — |
| C01-T10 | Assurance | NOT_RUN | Una trasformazione reale attraversa input → output → Verification → Receipt anche in FAIL/REVIEW_REQUIRED. | — |
| C01-T11 | Minima sufficienza | NOT_RUN | Ogni entità V1 è giustificata da almeno un caso reale; il superfluo è rinviato. | — |

## Regola di chiusura

Il gate finale è `PASS` solo se tutte le righe `C01-T01`…`C01-T11` sono `PASS`. Qualunque `FAIL`, `BLOCKED_SOURCE`, `BLOCKED_INPUT`, `REVIEW_REQUIRED` o `NOT_RUN` produce `NOT_QUALIFIED`.
