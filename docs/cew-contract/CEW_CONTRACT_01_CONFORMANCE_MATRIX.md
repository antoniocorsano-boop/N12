# CEW-CONTRACT-01 — Conformance Matrix

**Spec:** `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`  
**Qualification plan:** `docs/superpowers/plans/2026-10-12-cew-contract-01-qualification.md`  
**Rule:** uno stato diverso da `PASS` resta aperto o bloccato; nessun test viene promosso per deduzione.

| ID | Test | Status | Criterion | Evidence |
|---|---|---|---|---|
| C01-T01 | Rappresentabilità N12 | REVIEW_REQUIRED | I casi N12 richiesti dalla spec sono rappresentabili senza campi N12-specifici. | `CASE_01`–`CASE_07` coprono modello epistemico e identità; restano snapshot/assurance e blocker di fonte. |
| C01-T02 | Provenienza completa | BLOCKED_SOURCE | Un Result reale è risalibile fino alla Source originale attraverso tutta la catena CEW. | `CASE_01_DOCUMENTED_PROPERTY.md`: Source originale della relazione v17 non localizzabile. |
| C01-T03 | Conflict reale | BLOCKED_SOURCE | Due proposizioni reali incompatibili possono coesistere senza scelta prematura. | `CASE_06_REAL_CONFLICT.md`: nessuna coppia di fonti originali contraddittorie localizzabile. |
| C01-T04 | Aggiornamento non distruttivo | BLOCKED_SOURCE | Nuova evidenza crea nuovo stato senza riscrivere snapshot/run/risultati precedenti. | `CASE_07_NON_DESTRUCTIVE_UPDATE.md`: mancano due versioni storiche complete della stessa proprietà. |
| C01-T05 | Identità strutturale | PASS | L'identità fisica resta stabile attraverso revisioni di proprietà; alias non sono ID primari. | `CASE_04_STRUCTURAL_IDENTITY.md`: fixture CEW separa StructuralObject da alias T5/G5/BEAM-006. |
| C01-T06 | Indipendenza dallo strumento | NOT_RUN | Il nucleo logico non dipende da CAD, IFC, solver, database o serializzazione specifici. | — |
| C01-T07 | Incertezza | REVIEW_REQUIRED | ND, DOC conflittuale, misura con tolleranza, INF e Assumption di Scenario restano distinguibili. | `CASE_02` qualifica ND; `CASE_03` qualifica DOC/INF. Mancano conflitto reale, misura con tolleranza e Scenario. |
| C01-T08 | Relationship incerta | BLOCKED_SOURCE | Una Relationship può avere Evidence, stato epistemico, Conflict e Decision propri. | `CASE_05_RELATIONSHIP_UNCERTAINTY.md`: abaco topologico originale non presente/localizzabile. |
| C01-T09 | Riproducibilità | NOT_RUN | ModelGeneration e SolverRun identificano univocamente snapshot/scenario/versioni/input/output. | — |
| C01-T10 | Assurance | NOT_RUN | Una trasformazione reale attraversa input → output → Verification → Receipt anche in FAIL/REVIEW_REQUIRED. | — |
| C01-T11 | Minima sufficienza | NOT_RUN | Ogni entità V1 è giustificata da almeno un caso reale; il superfluo è rinviato. | — |

## Regola di chiusura

Il gate finale è `PASS` solo se tutte le righe `C01-T01`…`C01-T11` sono `PASS`. Qualunque `FAIL`, `BLOCKED_SOURCE`, `BLOCKED_INPUT`, `REVIEW_REQUIRED` o `NOT_RUN` produce `NOT_QUALIFIED`.
