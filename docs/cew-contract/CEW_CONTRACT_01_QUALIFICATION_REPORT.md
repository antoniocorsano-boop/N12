# CEW-CONTRACT-01 — Qualification Report

**Date:** 13 ottobre 2026  
**Base spec:** `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`  
**Closure spec:** `docs/superpowers/specs/2026-10-13-cew-contract-01-closure-design.md`  
**Closure plan:** `docs/superpowers/plans/2026-10-13-cew-contract-01-closure.md`  
**Operational source authority:** `d806dcca72779b5a186defe557a7a9b739575a90`  
**Gate:** QUALIFIED

## 1. Esito

La closure approvata rimuove la dipendenza circolare fra contratto logico CEW e adapter FEM senza simulare un risultato strutturale.

La matrice di conformità corrente contiene esattamente 11 test `C01-T01`…`C01-T11`, tutti in stato `PASS`.

Distribuzione:

- `PASS`: 11;
- `FAIL`: 0;
- `BLOCKED_SOURCE`: 0;
- `BLOCKED_INPUT`: 0;
- `REVIEW_REQUIRED`: 0;
- `NOT_RUN`: 0.

`CEW-CONTRACT-01 = QUALIFIED` significa che il contratto logico è dimostrato sul caso reale N12 fino alle proiezioni derivate, Verification e Receipt. Non significa che N12 sia pronto per il calcolo strutturale.

## 2. Chiusura del residuo di provenienza — C01-T02

`evidence/cew-contract-01/CASE_13_CORE_END_TO_END_ASSURANCE.md` dimostra il percorso reale:

`TAV-01S Source → derived Evidence anchors → observations/claims → P05 topology candidate → P06 source-local adjudication → P07 promoted primary geometry → FPEP release → M1F_FOUNDATION_MODEL_CURRENT_v1.csv → frozen CanonicalSnapshot → ModelGeneration → derived Projection → Verification → Receipt`.

Il tratto P05→P07 è esplicito e verificabile:

- P05 contiene 15 candidati e non crea membri;
- P06 risolve i 15 claim topologici mediante rilettura/incidence sweep senza uso della topologia legacy come target;
- P07 conserva per ciascuno il riferimento P05 e P06 e promuove solo continuità `CROSS_VALIDATED`;
- P07 registra 0 conflitti topologici bloccanti, 0 coordinate cartesiane create e 0 membri analitici creati;
- due conflitti metrici e un residuo OCR restano non promossi.

Il release gate FPEP autorizza il successivo modello fondazioni con 38 supporti e 55 incidenze primarie, mantenendo `ND` per coordinate/parametri non sostenuti.

## 3. ModelGeneration reale — C01-T09 / C01-T10

Il caso `N12-CEW-MG-001` è formalizzato da:

- `evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_v1.json`;
- `evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_RECEIPT_v1.json`.

La generazione usa lo snapshot congelato:

`N12-FROZEN-INPUTSET@d806dcca72779b5a186defe557a7a9b739575a90`.

Il manifest conserva:

- builder/versione e blob;
- profilo di generazione;
- scenario nullo esplicito;
- parametri/policy;
- sei input canonici con SHA-256;
- output con SHA-256;
- artifact id/archive digest;
- timestamp;
- Verification deterministica associata;
- Receipt associato;
- warning `FOUNDATION_NUMERIC_Z = ND`.

La Verification reale è legata al workflow run `32955421352`, conclusione `success`. Il Receipt prova la trasformazione ma dichiara esplicitamente:

- `engineering_result=false`;
- `solver_run=false`;
- `result_entity_created=false`.

Questa separazione è parte della qualifica, non un'eccezione.

## 4. Incertezza di registrazione reale — C01-T07

`evidence/cew-contract-01/fixtures/N12_REGISTRATION_UNCERTAINTY_v1.json` formalizza osservazioni reali provenienti da `data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv`.

Il caso distingue:

- coordinate osservate e previste in pixel;
- residui `du`, `dv` e scalare;
- stato diagnostico (`PASS_DIAGNOSTIC` / `WATCH`);
- classe di evidenza;
- eventuale bound derivato separato;
- guardia interpretativa.

Il residuo di registrazione non viene rinominato tolleranza, errore standard, incertezza standard o accuratezza certificata. Nessun valore metrologico viene inventato.

## 5. Minima sufficienza — C01-T01 / C01-T11

`evidence/cew-contract-01/CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv` distingue tipi necessari e tassonomia estendibile.

`CORE_REQUIRED` con casi reali:

- `Node`;
- `Column`;
- `Beam`;
- `FoundationElement`.

`Wall` resta `SUPPORTED_EXTENSION`: il gate non fabbrica un'entità muro strutturale N12 solo per soddisfare lo schema. Anche gli altri tipi non necessari restano estensioni finché un caso reale non ne richiede l'identità autonoma.

## 6. Test già qualificati e invariati

Restano PASS senza reinterpretazione sostanziale:

- `C01-T03` — Conflict reale;
- `C01-T04` — aggiornamento non distruttivo;
- `C01-T05` — identità strutturale;
- `C01-T06` — indipendenza dallo strumento;
- `C01-T08` — Relationship incerta.

Le relative evidenze N12 rimangono quelle già registrate nei casi di conformità dedicati.

## 7. Confine di autorità

La qualifica mantiene obbligatoriamente:

- `solver_authorized=false`;
- `calculation_model_ready=false`;
- `synthetic_solver_result=false`;
- nessun nuovo valore di materiali, carichi, geotecnica o fondazioni;
- nessuna promozione di un artefatto derivato a Source primaria;
- nessuna connettività creata per prossimità geometrica;
- nessuna scelta implicita di OpenSees, Code_Aster, EdiLus o altro solver.

N12 resta pertanto **non autorizzato a una verifica strutturale corrente** finché i gate tecnici dedicati non lo consentono.

## 8. Debito trasferito a CEW-FEM-01

Il debito solver-specifico è intenzionalmente separato e resta aperto:

`CEW-FEM-01: ModelGeneration → SolverRun → Result → Verification → Receipt`.

Questa catena sarà obbligatoria per qualificare un adapter FEM e un round trip solver, ma non è più un prerequisito circolare per qualificare il contratto logico CEW.

## 9. Decisione

**CEW-CONTRACT-01: QUALIFIED**, subordinatamente al validator fail-closed sull'exact head che contiene questa matrice e questo report.

La decisione non autorizza merge automatico, scelta solver o calcolo N12. Qualunque successiva mutazione degli artefatti di closure richiede una nuova qualifica exact-head.
