# CEW-CONTRACT-01 — Qualification Report

**Date:** 13 ottobre 2026  
**Base spec:** `docs/superpowers/specs/2026-10-12-cew-contract-01-design.md`  
**Closure spec:** `docs/superpowers/specs/2026-10-13-cew-contract-01-closure-design.md`  
**Stabilization spec:** `docs/superpowers/specs/2026-10-13-cew-contract-01-gate-stabilization-design.md`  
**Stabilization plan:** `docs/superpowers/plans/2026-10-13-cew-contract-01-gate-stabilization.md`  
**Operational source authority:** `d806dcca72779b5a186defe557a7a9b739575a90`  
**Gate state:** `QUALIFIED` only when the repository-native gate is `success` on the exact head being evaluated.

## 1. Esito e criterio di qualifica

CEW-CONTRACT-01 è stato trasformato da un gate progressivamente rafforzato dopo singoli finding in un gate con superficie di assurance dichiarata e finita.

La matrice di conformità conserva esattamente 11 test `C01-T01`…`C01-T11`, tutti `PASS`. La stabilizzazione aggiunge una seconda dimensione di assurance: gli invarianti I01–I17 e una mutation suite avversariale che verifica che alterazioni intenzionali non possano lasciare verde la qualifica.

`CEW-CONTRACT-01 = QUALIFIED` significa che il contratto logico è dimostrato sul caso reale N12 fino a ModelGeneration, Projection, Verification e Receipt, con autorità e provenienza fail-closed. Non significa che N12 sia pronto per il calcolo strutturale.

## 2. Frozen Authority Profile

L'autorità della qualifica è resa machine-checkable da:

`evidence/cew-contract-01/stabilization/N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json`.

Il profilo congela, senza creare nuovi dati tecnici:

- commit operativo `d806dcca72779b5a186defe557a7a9b739575a90`;
- `canonical_snapshot_id = N12-FROZEN-INPUTSET@d806dcca72779b5a186defe557a7a9b739575a90`;
- builder `scripts/cew_structural_model_builder.py` e Git blob SHA `4459fd0f519d8bb9425fa1490cc720a2edb0bd0a`;
- insieme esatto dei sei input ModelGeneration e relativi SHA-256;
- fonte della registration uncertainty e Git blob SHA;
- supporti esatti `1` e `19`;
- profilo di generazione;
- identità, SHA-256 e dimensione dell'output atteso;
- timestamp storico di generazione;
- authority flags che devono restare `false`;
- riferimenti di evidenza `C01-T01`…`C01-T11`.

Il validator non sceglie fra valori dichiarati in conflitto: ogni divergenza fra authority, manifest, receipt, fixture o replay fallisce chiuso.

## 3. ModelGeneration durevole e replay deterministico — C01-T09 / C01-T10

Il caso reale `N12-CEW-MG-001` continua a essere formalizzato da:

- `evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_v1.json`;
- `evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_RECEIPT_v1.json`.

La stabilizzazione elimina però la dipendenza permanente dall'artifact GitHub Actions storico. Il workflow corrente materializza direttamente dal commit operativo congelato:

- il builder autorizzato;
- i sei input canonici esatti;
- la fonte della registration uncertainty.

`scripts/cew_contract_01_replay.py`:

1. ricalcola il Git blob SHA del builder reale;
2. ricalcola gli SHA-256 dei sei input reali;
3. esegue il builder storico con gli stessi path relativi;
4. controlla soltanto il metadato volatile `generated_at`, usando il timestamp storico già congelato;
5. serializza con la stessa regola del builder originario;
6. confronta identità, dimensione e SHA-256 dell'output.

Sul run exact-head `38359875885`, SHA `13dc6df9a6aabf747491efb79adb5c9d60edad31`, il replay reale ha prodotto:

- `passed=true`;
- `generated_at=2026-08-26T09:54:00.472520+00:00`;
- `identity=N12_CEW_CANONICAL_STRUCTURAL_MODEL_v0.json`;
- `sha256=4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2`;
- `size_bytes=1068121`.

Questa è la prova durevole di riproducibilità: la qualifica corrente non necessita che l'artifact Actions storico continui a esistere.

## 4. Evidenza storica di transizione

Il run originario `32955421352` e l'artifact `9601773275` sono stati verificati mentre erano ancora interrogabili e registrati in:

`evidence/cew-contract-01/stabilization/N12_CEW_MODEL_GENERATION_HISTORICAL_RECEIPT_v1.json`.

La receipt conserva workflow, head SHA, status/conclusion, artifact digest e output digest/size e dichiara `runtime_dependency=false`.

Il run/artifact storico ha quindi valore di evidenza della generazione originaria, ma non è più prerequisito runtime del gate permanente. La scadenza o indisponibilità futura dell'artifact non rende non riproducibile CEW-CONTRACT-01.

## 5. Provenienza core — C01-T02

`evidence/cew-contract-01/CASE_13_CORE_END_TO_END_ASSURANCE.md` conserva il percorso reale:

`TAV-01S Source → derived Evidence anchors → observations/claims → P05 topology candidate → P06 source-local adjudication → P07 promoted primary geometry → FPEP release → M1F_FOUNDATION_MODEL_CURRENT_v1.csv → frozen CanonicalSnapshot → ModelGeneration → derived Projection → Verification → Receipt`.

Il tratto P05→P07 resta esplicito e verificabile: P05 contiene 15 candidati e non crea membri; P06 risolve i claim topologici; P07 promuove solo continuità cross-validata; coordinate o parametri non sostenuti restano `ND`.

La stabilizzazione non modifica questa catena né introduce nuove proprietà ingegneristiche.

## 6. Registration uncertainty reale — C01-T07

`evidence/cew-contract-01/fixtures/N12_REGISTRATION_UNCERTAINTY_v1.json` è riconciliata con `data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv` del commit operativo congelato.

Il gate richiede esattamente entrambi i casi qualificati:

- supporto `1` — `PASS_DIAGNOSTIC`, `DOC_METRIC_OR_AXIS`;
- supporto `19` — `WATCH`, `MIS_AFFINE_WATCH`.

Il source Git blob SHA viene ricalcolato. Coordinate osservate/previste, residui, stato diagnostico e classe di evidenza vengono confrontati con le righe reali della fonte.

Il residuo di registrazione non viene promosso a tolleranza, errore standard, incertezza standard o accuratezza certificata; le guardie epistemiche restano esplicitamente `false`.

## 7. Invarianti I01–I17 e mutation testing

La Stabilization Spec congela diciassette famiglie di invarianti relative a:

- exact-head identity e non-bypassabilità del workflow;
- autorità del commit operativo;
- insieme e integrità byte degli input;
- identità byte del builder;
- snapshot canonico;
- replay durevole e integrità dell'output;
- coerenza Manifest / Verification / Receipt;
- provenienza e casi esatti della registration uncertainty;
- guardie epistemiche;
- matrice/evidenze;
- authority boundary;
- separazione CEW-FEM-01.

La suite `tests/test_cew_contract_01_stabilization_mutations.py` esercita mutazioni avversariali isolate. Sul run `38359875885` risultano `15/15 OK`, fra cui:

- perdita dell'exact PR head;
- action non pin a SHA;
- conditional/failure bypass;
- reintroduzione di una dipendenza Actions effimera;
- commit operativo alterato;
- builder blob alterato;
- input set alterato;
- digest replay alterato;
- `solver_run=true`;
- supporto 1 o 19 mancante;
- supporto inatteso;
- historical receipt resa runtime dependency;
- gate ID duplicato;
- evidence mancante.

La mutation suite serve a prevenire la regressione verso il precedente ciclo `finding → patch → nuovo finding`.

## 8. Gate repository-native stabilizzato

`.github/workflows/validate-cew-contract-01-closure.yml` ora:

- qualifica il vero PR head;
- usa `actions/checkout` e `actions/setup-python` pin a SHA completi;
- usa `persist-credentials: false`;
- richiede solo `contents: read`;
- materializza builder, sei input e registration source dal commit `d806...`;
- esegue il replay deterministico;
- esegue authority tests, replay tests, closure tests, review regressions, final-review regressions, stabilization invariants e mutation suite;
- verifica il contratto CI stesso;
- esegue infine il validator di closure in modo incondizionato.

Il workflow non contiene più download dell'artifact storico, lookup runtime del vecchio run, `CEW_MODEL_OUTPUT_ROOT`, `actions: read` o `GITHUB_TOKEN` dedicato alla vecchia dipendenza.

Sul run `38359875885` tutti gli step del job risultano `success`, incluso il validator finale.

## 9. Esito del validator sul gate stabilizzato

Sul medesimo run `38359875885`, il validator finale ha restituito:

- `errors=[]`;
- `qualified=true`;
- `gate.count=11`;
- `gate.pass_count=11`;
- `gate.distribution.PASS=11`;
- `gate.evidence_valid=true`;
- `gate.exact_test_ids=true`;
- `calculation_model_ready_mutated=false`;
- `synthetic_solver_result=false`;
- `fem_debt_declared=true`.

Nello stesso exact head Vercel e CodeRabbit risultavano `success`.

## 10. Confine di autorità

La qualifica mantiene obbligatoriamente:

- `solver_authorized=false`;
- `calculation_model_ready=false`;
- `synthetic_solver_result=false`;
- `solver_run=false` nella receipt ModelGeneration;
- `result_entity_created=false` nella receipt ModelGeneration;
- nessun nuovo valore di materiali, carichi, geotecnica o fondazioni;
- nessuna promozione di un artefatto derivato a Source primaria;
- nessuna scelta implicita di OpenSees, Code_Aster, EdiLus o altro solver.

N12 resta non autorizzato a una verifica strutturale corrente finché i gate tecnici dedicati non lo consentono.

## 11. Debito separato CEW-FEM-01

`CEW_FEM_01_REQUIRED=true`

Resta obbligatoriamente fuori da CEW-CONTRACT-01:

`CEW-FEM-01: ModelGeneration → SolverRun → Result → Verification → Receipt`.

La stabilizzazione non anticipa né simula questa catena.

## 12. Finding triage e criterio di arresto

Dopo la stabilizzazione, un nuovo finding riapre CEW-CONTRACT-01 solo se dimostra che:

- almeno un invariante I01–I17 può essere violato lasciando verde il gate;
- un controllo obbligatorio è bypassabile;
- il replay può usare autorità diversa senza fallire;
- permane una dipendenza effimera necessaria al gate;
- vengono introdotti/promossi dati tecnici non autorizzati;
- viene violato il confine con CEW-FEM-01.

Una nuova garanzia fuori da I01–I17, un refactoring non necessario, un miglioramento prestazionale o una richiesta solver-specifica non diventa automaticamente blocker della closure: richiede decisione umana o nuova specifica.

## 13. Regola exact-head e decisione

Il run `38359875885` qualifica l'implementazione di stabilizzazione allo SHA `13dc6df9a6aabf747491efb79adb5c9d60edad31`.

Questo report è a sua volta una modifica di repository. Pertanto **non eredita automaticamente** la qualifica del precedente SHA: l'exact head che contiene questo report deve completare nuovamente con `success` lo stesso gate repository-native prima della decisione finale e della fresh review indipendente.

Nessun merge automatico, scelta solver o calcolo N12 è autorizzato da questo report.
