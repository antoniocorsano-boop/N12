# eTwin — SP-2 Controlled Admission Closeout v1

**Data:** 2026-08-28  
**Stato documentale:** `CLOSEOUT_CANDIDATE`  
**Promotion effect:** `NONE`  
**Engineering authority effect:** `NONE`

## 1. Scope chiuso

La riconciliazione temporanea della specifica ha completato:

- `SP0-G = PASS_WITH_FINDINGS` — genealogia e authority mapping;
- `SP1-G = PASS_WITH_OPEN_ITEMS` — conformance/delta classification;
- `SP2` — ammissione controllata dei soli delta non invasivi D1 e D4.

Non viene creato un lifecycle SP successivo. Dopo il gate finale same-SHA il lavoro torna al programma eTwin corrente.

## 2. D1 ammesso — requirement flexibility

`ETWIN-SPEC-001` è registrata come decisione `ACCEPTED` nel `PRODUCT_DECISION_REGISTER_v1.json`.

Classi ammesse:

- `INVARIANT`;
- `SPECIFIED`;
- `OPEN`;
- `EXPERIMENTAL`;
- `DOMAIN_OWNED`.

La classificazione è subordinata a L0-L7 e non modifica la precedenza delle authority.

## 3. D4 ammesso — acceptance hardening

`docs/ACCEPTANCE/ETWIN_PLATFORM_RED_TEAM_MATRIX_v1.md` rende espliciti i casi di isolation/authority/freshness/same-revision che devono essere provati dove applicabili.

La matrice non sostituisce:

- HVA;
- Production smoke;
- product promotion;
- professional engineering authority.

Il riuso di conoscenza analitica non trasferisce automaticamente receipt promotion-grade a un'altra revisione.

## 4. D2/D3 non ammessi come schema

Restano intenzionalmente `OPEN` o `EXPERIMENTAL`:

- `Person / Role / Capability / Authority / Scope` come modello dati di collaborazione;
- `ProjectRoleAssignment` e `ActiveRoleContext` persistenti;
- primitivo operativo professionale (`WorkItem`, `TechnicalActivity` o equivalente);
- tassonomia completa `CrossDisciplineRelation`;
- ScopeContext extra-granularity;
- global SourceVersion dedup threat model;
- agent freshness states;
- organizzazione user-facing degli agenti;
- handoff/delivery semantics;
- persistenza/deployment platform-wide non ancora richiesta da una capability.

Questi temi non vengono risolti per anticipazione. Ogni item viene aperto soltanto dal journey/slice che ne dimostra la necessità.

## 5. Boundary dopo SP-2

Devono restare veri:

```text
current_slice = ETW-A0
current_execution_mode = PREP_ONLY
promotion_authorized = false
promotion_blocker = CEW_PROMOTED_BASELINE
cew_promoted_baseline_sha = null
A0 revalidation required = true
ETW-A1 = WAITING
engineering_authority_unchanged = true
parallel_platform_lifecycle_created = false
```

La branch discovery `docs/etwin-system-spec-v1` resta L7 input e non current L1.

## 6. Gate di chiusura

SP-2 è `COMPLETE — NON_PROMOTIVE` solo quando l'HEAD che contiene questo closeout ottiene `success` dal workflow:

`Validate eTwin Spec Reconciliation`

Il workflow deve sullo stesso SHA:

1. compilare i validator Python;
2. ottenere `PRODUCT_GOVERNANCE_CONSISTENCY_PASS`;
3. ottenere PASS dalla validazione contratti dell'orchestratore;
4. provare A0 `PREP_ONLY` e non promotiva;
5. provare `CEW_PROMOTED_BASELINE` assente;
6. provare A1 `WAITING`;
7. provare ETWIN-SPEC-001 `ACCEPTED`;
8. provare assenza di lifecycle platform parallelo.

Un run su SHA precedente è evidence storica ma non chiude questo closeout.

## 7. Stato dopo gate verde

Dopo il same-SHA PASS:

`SP-0 / SP-1 / SP-2 = RECONCILIATION COMPLETE`

Il prossimo lavoro **non** è una nuova fase di specifica. La sequenza ammessa torna a:

```text
CEW B1 Human Acceptance v2 / promotion completion
        ↓
CEW_PROMOTED_BASELINE
        ↓
ETW-A0 revalidation under v2 governance
        ↓
APPROVE_PLATFORM_BOUNDARY
        ↓
ETW-A1 → A2 → A3 → A4 → A5 → A6 → Z0
```

Nessun delta di questa riconciliazione autorizza l'anticipo di A1.