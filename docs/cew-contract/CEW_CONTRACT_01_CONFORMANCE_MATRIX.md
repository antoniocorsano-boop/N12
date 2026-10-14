# CEW-CONTRACT-01 — Conformance Matrix

**Base spec:** `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`  
**Closure spec (prevale sui punti modificati):** `docs/superpowers/specs/2026-10-13-cew-contract-01-closure-design.md`  
**Closure plan:** `docs/superpowers/plans/2026-10-13-cew-contract-01-closure.md`  
**Machine matrix:** `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.csv`  
**Rule:** uno stato diverso da `PASS` resta aperto o bloccato; nessun test viene promosso per deduzione.

| ID | Test | Status | Criterion | Evidence |
|---|---|---|---|---|
| C01-T01 | Rappresentabilità N12 | PASS | I concetti core necessari sono rappresentabili senza campi N12-specifici; i tipi non necessari restano estensioni. | `CASE_01`–`CASE_13` + `CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv`: `Node`, `Column`, `Beam`, `FoundationElement` sono `CORE_REQUIRED`; `Wall` resta `SUPPORTED_EXTENSION`. |
| C01-T02 | Provenienza completa core | PASS | Una Projection reale con Verification/Receipt è risalibile fino alla Source attraverso la catena CEW core. | `CASE_13_CORE_END_TO_END_ASSURANCE.md`: TAV-01S/Evidence → P05 → P06 → P07 → FPEP release → fondazioni canoniche → ModelGeneration → Verification → Receipt. `SolverRun/Result` resta `CEW-FEM-01`. |
| C01-T03 | Conflict reale | PASS | Due proposizioni reali incompatibili possono coesistere senza scelta prematura. | `CASE_06_REAL_CONFLICT.md`: conflitto TAV-07A ↔ TAV-06S sul supporto 24. |
| C01-T04 | Aggiornamento non distruttivo | PASS | Nuova evidenza crea nuovo stato senza riscrivere lo stato precedente. | `CASE_07_NON_DESTRUCTIVE_UPDATE.md`: revalidation ledger + pre-snapshot conservato + master corrente. |
| C01-T05 | Identità strutturale | PASS | L'identità fisica resta stabile attraverso revisioni di proprietà; alias non sono ID primari. | `CASE_04_STRUCTURAL_IDENTITY.md`. |
| C01-T06 | Indipendenza dallo strumento | PASS | Il nucleo logico non dipende da CAD, IFC, solver, database o serializzazione specifici. | `CASE_08_SNAPSHOT_SCENARIO.md` + `CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv` + ModelGeneration solver-independent. |
| C01-T07 | Incertezza | PASS | Un caso reale N12 distingue valore osservato, residuo di registrazione, eventuale bound derivato e limiti del metodo. | `fixtures/N12_REGISTRATION_UNCERTAINTY_v1.json`: casi reali `PASS_DIAGNOSTIC` e `WATCH`; il residuo in pixel non è promosso a tolleranza/accuratezza/incertezza metrologica certificata. |
| C01-T08 | Relationship incerta | PASS | Una Relationship può avere Evidence, stato epistemico, Conflict e Decision propri. | `CASE_05_RELATIONSHIP_UNCERTAINTY.md`: binding concorrenti C5 V→Z con stato e decisione distinti. |
| C01-T09 | Riproducibilità | PASS | ModelGeneration identifica snapshot, scenario, builder/versione, parametri, input/output e hash. | `CASE_12_MODEL_GENERATION.md` + `model-generation/N12_CEW_MODEL_GENERATION_v1.json` + relativo Receipt: snapshot congelato su `d806dcca…`, sei input SHA-256, output e artifact digest. |
| C01-T10 | Assurance | PASS | Una trasformazione reale attraversa input → output → Verification → Receipt preservando warning/residui. | `CASE_13` + manifest/receipt ModelGeneration: workflow reale PASS; `FOUNDATION_NUMERIC_Z` resta `ND`; `engineering_result=false`, `solver_run=false`. |
| C01-T11 | Minima sufficienza | PASS | Ogni tipo `CORE_REQUIRED` ha un caso reale; il superfluo non viene fabbricato. | `CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv`: solo `Node`, `Column`, `Beam`, `FoundationElement` sono core; `Wall` e gli altri tipi non necessari restano estensioni supportate. |

## Regola di chiusura

Il gate finale è `PASS` solo se tutte le righe `C01-T01`…`C01-T11` sono `PASS` anche nella matrice CSV letta dal validator. Qualunque `FAIL`, `BLOCKED_SOURCE`, `BLOCKED_INPUT`, `REVIEW_REQUIRED` o `NOT_RUN` produce `NOT_QUALIFIED`.

La presente matrice non autorizza un calcolo strutturale N12. Restano invariati:

- `solver_authorized=false`;
- `calculation_model_ready=false`;
- nessun `Result` fittizio;
- debito separato `CEW-FEM-01: ModelGeneration → SolverRun → Result → Verification → Receipt`.
