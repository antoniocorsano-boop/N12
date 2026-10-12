# CEW-CONTRACT-01 — Conformance Matrix

**Spec:** `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`  
**Qualification plan:** `docs/superpowers/plans/2026-10-12-cew-contract-01-qualification.md`  
**Rule:** uno stato diverso da `PASS` resta aperto o bloccato; nessun test viene promosso per deduzione.

| ID | Test | Status | Criterion | Evidence |
|---|---|---|---|---|
| C01-T01 | Rappresentabilità N12 | REVIEW_REQUIRED | I casi N12 richiesti dalla spec sono rappresentabili senza campi N12-specifici. | `CASE_01`–`CASE_10`: tutti i concetti sono rappresentati, ma manca un SolverRun/Result reale e resta incompleto il caso di incertezza di misura. |
| C01-T02 | Provenienza completa | BLOCKED_INPUT | Un Result reale è risalibile fino alla Source originale attraverso tutta la catena CEW. | `CASE_09_END_TO_END_ASSURANCE.md`: Source/Evidence reali esistono, ma Solver Round Trip è PLANNED e nessun Result tecnico reale è autorizzato. |
| C01-T03 | Conflict reale | PASS | Due proposizioni reali incompatibili possono coesistere senza scelta prematura. | `CASE_06_REAL_CONFLICT.md`: conflitto TAV-07A ↔ TAV-06S sul supporto 24. |
| C01-T04 | Aggiornamento non distruttivo | PASS | Nuova evidenza crea nuovo stato senza riscrivere lo stato precedente. | `CASE_07_NON_DESTRUCTIVE_UPDATE.md`: revalidation ledger + pre-snapshot conservato + master corrente. |
| C01-T05 | Identità strutturale | PASS | L'identità fisica resta stabile attraverso revisioni di proprietà; alias non sono ID primari. | `CASE_04_STRUCTURAL_IDENTITY.md`. |
| C01-T06 | Indipendenza dallo strumento | PASS | Il nucleo logico non dipende da CAD, IFC, solver, database o serializzazione specifici. | `CASE_08_SNAPSHOT_SCENARIO.md`: stesso Snapshot → geometry handoff e calculation-model handoff, senza tool identity nel nucleo. |
| C01-T07 | Incertezza | REVIEW_REQUIRED | ND, DOC conflittuale, misura con tolleranza, INF e Assumption di Scenario restano distinguibili. | ND `CASE_02`; DOC/INF `CASE_03`; conflict `CASE_06`; Scenario `CASE_08`; manca ancora un caso N12 con incertezza di misura formalizzata come tolleranza/intervallo. |
| C01-T08 | Relationship incerta | PASS | Una Relationship può avere Evidence, stato epistemico, Conflict e Decision propri. | `CASE_05_RELATIONSHIP_UNCERTAINTY.md`: binding concorrenti C5 V→Z con stato e decisione distinti. |
| C01-T09 | Riproducibilità | BLOCKED_INPUT | ModelGeneration e SolverRun identificano univocamente snapshot/scenario/versioni/input/output. | `CASE_09_END_TO_END_ASSURANCE.md`: handoff riproducibile disponibile, ma SolverRun/Result reale non esiste ancora. |
| C01-T10 | Assurance | PASS | Una trasformazione reale attraversa input → output → Verification → Receipt anche in FAIL/REVIEW_REQUIRED. | `CASE_10_VERIFICATION_RECEIPT.md`: HiRes machine review receipt con source/blob/hash/run/artifact/findings/guards e promozione non autorizzata. |
| C01-T11 | Minima sufficienza | NOT_RUN | Ogni entità V1 è giustificata da almeno un caso reale; il superfluo è rinviato. | — |

## Regola di chiusura

Il gate finale è `PASS` solo se tutte le righe `C01-T01`…`C01-T11` sono `PASS`. Qualunque `FAIL`, `BLOCKED_SOURCE`, `BLOCKED_INPUT`, `REVIEW_REQUIRED` o `NOT_RUN` produce `NOT_QUALIFIED`.
