# CEW-CONTRACT-01 — Piano di chiusura dei tre residui

**Data:** 13 ottobre 2026  
**Modalità approvata:** Native + TDD RED → GREEN  
**PR:** #147  
**Branch di lavoro:** `docs/cew-research-baseline-2026-10-12`  
**Branch N12 di evidenza operativa (read-only per questa attività):** `work/m0-global-model`  
**Baseline operativa verificata:** `d806dcca72779b5a186defe557a7a9b739575a90`  
**Spec di autorità:** `docs/superpowers/specs/2026-10-13-cew-contract-01-closure-design.md`

## Obiettivo

Portare `CEW-CONTRACT-01` da `NOT_QUALIFIED` a `QUALIFIED` **solo se** tutti gli 11 test C01 risultano `PASS` sull'exact head, chiudendo i tre residui approvati senza:

- introdurre un SolverRun/Result sintetico;
- scegliere un solver in CEW-CONTRACT-01;
- modificare `calculation_model_ready=false` del progetto N12;
- inventare tolleranze o accuratezze metrologiche;
- fabbricare un'entità `Wall` per soddisfare lo schema;
- mutare dati tecnici del ramo operativo N12.

L'attività modifica esclusivamente la branch della PR #147. `work/m0-global-model` è sorgente di evidenza, non target di scrittura.

## Fonti operative congelate

Usare i seguenti artefatti del ref `d806dcca72779b5a186defe557a7a9b739575a90`:

- `data/canonical/M1E_CALCULATION_MODEL_HANDOFF_v1.json`;
- `data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv`;
- `scripts/cew_structural_model_builder.py`;
- `.github/workflows/validate-cew-structural-model-builder.yml`;
- gli input del builder indicati dal workflow:
  - `data/canonical/M0G_GEOMETRY_HANDOFF_v1.json`;
  - `data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv`;
  - `data/canonical/M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv`;
  - `data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv`;
  - `data/canonical/M1F_FOUNDATION_MODEL_CURRENT_v1.csv`;
  - `data/canonical/M1E_FOUNDATION_XY_SOLVER_PROJECTION_RULE_v1.json`.

Non usare il nome della branch come identificatore sufficiente: ogni fixture/manifest deve citare il commit operativo esatto.

---

## Task 1 — Validator fail-closed della closure

### File

**Creare**
- `scripts/validate_cew_contract_01_closure.py`
- `tests/test_cew_contract_01_closure.py`

**Leggere senza modificare**
- `docs/superpowers/specs/2026-10-13-cew-contract-01-closure-design.md`
- `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`
- `docs/cew-contract/CEW_CONTRACT_01_MINIMALITY_AUDIT.md`

### RED

Scrivere test che falliscono finché non esistono e non sono validi:

1. fixture `REGISTRATION_UNCERTAINTY` con provenance e residuo reale;
2. manifest `ModelGeneration` con Snapshot/Scenario/builder/versione/parametri/input/output/hash/Verification/Receipt;
3. tassonomia di minimalità con `Wall=SUPPORTED_EXTENSION` e nessun `CORE_REQUIRED` privo di caso;
4. gate C01 con esattamente 11 righe e tutti gli status ammessi;
5. guardia `NO_SYNTHETIC_SOLVER_RESULT`;
6. guardia `N12_CALCULATION_MODEL_READY_MUST_REMAIN_FALSE`;
7. debito esplicito verso `CEW-FEM-01` per `ModelGeneration → SolverRun → Result → Verification → Receipt`.

Comando RED:

```bash
python -m unittest tests/test_cew_contract_01_closure.py -v
```

Esito atteso iniziale: FAIL per fixture/manifest/tassonomia mancanti.

### GREEN minimo

Implementare il validator come controllo deterministico di documenti/JSON/CSV della PR. Il validator **non** deve leggere “PASS” da testo libero: deve derivare il gate dai campi macchina/righe strutturate.

Comandi:

```bash
python -m py_compile scripts/validate_cew_contract_01_closure.py
python -m unittest tests/test_cew_contract_01_closure.py -v
```

Non dichiarare GREEN complessivo finché i Task 2–5 non hanno prodotto gli artefatti richiesti.

---

## Task 2 — Caso reale `REGISTRATION_UNCERTAINTY`

### File

**Creare**
- `evidence/cew-contract-01/fixtures/N12_REGISTRATION_UNCERTAINTY_v1.json`
- `evidence/cew-contract-01/CASE_11_REGISTRATION_UNCERTAINTY.md`

### Fonte

`work/m0-global-model@d806dcca72779b5a186defe557a7a9b739575a90:data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv`

Usare almeno:

- un caso `PASS_DIAGNOSTIC`;
- un caso `WATCH`;

copiando esattamente coordinate osservate/previste, `du_px`, `dv_px`, `residual_px`, stato e classe di evidenza.

### RED

I test devono rifiutare fixture che:

- chiamano `residual_px` tolleranza, accuracy, standard error o standard uncertainty;
- mancano del commit/ref della fonte;
- cambiano i valori reali;
- promuovono il residuo a `DOC`/`MIS` come nuova misura autonoma;
- introducono un `±x` non derivato da una regola esplicita.

### GREEN

La fixture deve contenere per ogni esempio:

- `uncertainty_type: REGISTRATION_UNCERTAINTY`;
- structural/property reference;
- observed/predicted coordinates;
- vector residual e scalar residual;
- unità `px`;
- source path + source commit;
- evidence class originale;
- diagnostic status originale;
- interpretive guard;
- `derived_bound: null` salvo regola esplicita.

Criterio: C01-T07 può diventare PASS senza inventare una tolleranza.

---

## Task 3 — Formalizzare una `ModelGeneration` N12 reale

### File

**Creare**
- `evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_v1.json`
- `evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_RECEIPT_v1.json`
- `evidence/cew-contract-01/CASE_12_MODEL_GENERATION.md`

### Fonte

Builder reale:

`work/m0-global-model@d806dcca72779b5a186defe557a7a9b739575a90:scripts/cew_structural_model_builder.py`

Workflow reale:

`.github/workflows/validate-cew-structural-model-builder.yml`

Il workflow genera `/tmp/N12_CEW_CANONICAL_STRUCTURAL_MODEL_v0.json` e verifica inventario/topologia prima dell'upload come artifact `N12-CEW-canonical-structural-model-v0`.

### RED

Il validator deve fallire se il manifest non dichiara:

- `model_generation_id`;
- `canonical_snapshot_id` o frozen-state reference univoco;
- `scenario_id` esplicitamente `null` oppure valido;
- `generation_profile`;
- builder path + source commit + builder blob/version identifier;
- parametri/command profile;
- tutti gli input con path e digest disponibile;
- output identity + digest/provenance;
- warning/residuals;
- timestamp/provenance timestamp rule;
- Verification;
- Receipt;
- `solver_authorized: false`;
- `calculation_model_ready: false`.

### GREEN

Formalizzare come ModelGeneration il processo **già esistente**, senza cambiare il builder operativo.

Se l'artefatto CI storico è disponibile, registrare il suo digest reale. Se non è disponibile in modo riproducibile dalla sessione, il manifest deve usare un output identity governato + workflow recipe e restare `REVIEW_REQUIRED`; in tal caso C01-T09 non può essere promosso. Non sostituire il digest mancante con un valore inventato.

Per chiudere T09/T10 è preferibile materializzare/riprodurre l'output dal medesimo commit e calcolarne SHA-256; la receipt deve distinguere chiaramente **qualification receipt** da risultato ingegneristico.

---

## Task 4 — Tassonomia di minima sufficienza

### File

**Creare**
- `evidence/cew-contract-01/CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv`

**Aggiornare**
- `docs/cew-contract/CEW_CONTRACT_01_MINIMALITY_AUDIT.md`

### RED

Il test deve fallire quando:

- un subtype `CORE_REQUIRED` non ha `case_ref` reale;
- `Wall` è `CORE_REQUIRED` senza caso N12;
- un subtype `SUPPORTED_EXTENSION` viene contato come obbligatorio per il gate;
- la tassonomia contiene classificazioni diverse da `CORE_REQUIRED`, `SUPPORTED_EXTENSION`, `DEFERRED`.

### GREEN

Classificare solo in base alle prove già presenti. Regola conservativa:

- segnare `CORE_REQUIRED` soltanto quando esiste un caso N12 citabile;
- `Wall = SUPPORTED_EXTENSION`;
- non declassare concetti realmente usati solo per rendere il gate più facile;
- mantenere `SolverRun` e `Result` come concetti CEW/FEM, non come subtype strutturali e non come requisito operativo C01.

Criterio: C01-T11 PASS soltanto se ogni `CORE_REQUIRED` ha giustificazione verificabile.

---

## Task 5 — Nuova assurance core e riallineamento matrice

### File

**Creare**
- `evidence/cew-contract-01/CASE_13_CORE_END_TO_END_ASSURANCE.md`

**Aggiornare**
- `docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.md`
- `docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md`

**Non riscrivere come se non fossero mai esistiti**
- `CASE_09_END_TO_END_ASSURANCE.md`
- `CASE_10_VERIFICATION_RECEIPT.md`

I casi precedenti restano evidenza storica della qualifica iniziale; il nuovo caso dichiara esplicitamente che li supersede **solo per il criterio operativo C01 modificato dalla closure spec**.

### Catena da provare

`Projection/derived graph → Verification → Receipt → ModelGeneration → Snapshot → canonical knowledge → Source/Evidence`

La catena solver resta debito separato:

`ModelGeneration → SolverRun → Result → Verification → Receipt` = `CEW-FEM-01`.

### Gate aggiornati

Promuovere solo con prove reali:

- C01-T01: rappresentabilità core senza Wall fittizio;
- C01-T02: provenance core fino a Source;
- C01-T07: registration uncertainty reale;
- C01-T09: ModelGeneration riproducibile;
- C01-T10: Verification + Receipt reali senza SolverRun sintetico;
- C01-T11: minimalità verificata.

T03/T04/T05/T06/T08 restano PASS solo se i relativi casi precedenti sono ancora presenti e non contraddetti.

---

## Task 6 — Gate finale exact-head e fail-closed

### File

**Aggiornare solo dopo GREEN**
- `docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md`
- eventuale descrizione PR #147.

### Verifiche obbligatorie

```bash
python -m py_compile scripts/validate_cew_contract_01_closure.py
python -m unittest tests/test_cew_contract_01_closure.py -v
python scripts/validate_cew_contract_01_closure.py
```

Il validator deve emettere in modo strutturato:

- conteggio test = 11;
- distribuzione status;
- `qualified = true` **solo** con 11 `PASS`;
- `synthetic_solver_result = false`;
- `calculation_model_ready_mutated = false`;
- `fem_debt_declared = true`.

### Verifica exact-head

1. rilevare SHA corrente della PR;
2. rifare i controlli sul contenuto dell'exact head;
3. verificare che la PR resti Draft/open/non-merged;
4. richiedere review indipendente se disponibile;
5. non dichiarare `QUALIFIED` se un controllo è `REVIEW_REQUIRED`, `BLOCKED_*`, `FAIL` o se una receipt/digest richiesta non è verificabile.

### Criterio di completamento

Solo 11/11 PASS autorizza:

`CEW-CONTRACT-01 = QUALIFIED`

con nota obbligatoria:

`CEW-FEM-01 remains required to qualify ModelGeneration → SolverRun → Result → Verification → Receipt.`

Nessun merge automatico.
