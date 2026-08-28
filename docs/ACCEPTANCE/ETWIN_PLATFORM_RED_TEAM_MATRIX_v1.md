# eTwin Platform Red-Team Matrix v1

**Data:** 2026-08-28  
**Stato:** `REQUIRED_WHERE_APPLICABLE_ON_RECONCILIATION_BRANCH`  
**Authority effect:** `NONE`  
**Governing contracts:** `ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2`, `ETW_AGENTIC_DEVELOPMENT_ORCHESTRATION_v2`, shared Security/Authority/Human governance

## 1. Scopo

Questa matrice rende falsificabili i boundary eTwin senza creare nuove primitive di dominio. È un artefatto di acceptance/assurance: non produce engineering truth, non promuove slice e non sostituisce HVA.

Ogni caso si applica soltanto quando la capability candidata espone il boundary corrispondente. `NOT_APPLICABLE` deve avere motivazione esplicita.

## 2. Receipt minimo per ogni prova

Ogni esecuzione registra:

- `case_id`;
- candidate/revision SHA;
- ambiente/runtime;
- Project/Discipline/Scope iniziale;
- precondizioni;
- input/azione;
- comportamento fail-closed atteso;
- comportamento osservato;
- evidence refs/log refs;
- risultato `PASS | FAIL | NOT_APPLICABLE`;
- blocker/residual;
- authority effect, sempre esplicito.

Un PASS tecnico non soddisfa automaticamente HVA o gate professionali.

## 3. Matrice

| ID | Boundary | Stimolo avversariale | Expected safe behavior | Blocking failure | Slice minima |
|---|---|---|---|---|---|
| RT-01 | Project isolation | entra N12, popola cache, passa a TEST_PROJECT e ritorna | nessun dato N12 osservabile/riusato in TEST_PROJECT; ritorno ricostruisce scope corretto | qualsiasi cross-project leakage o inference | A0/A2/Z0 |
| RT-02 | Discipline isolation | switching rapido Structures ↔ Architecture/not-yet-released | scope esatto o fail closed; zero entity/property Architecture sintetica | cross-discipline leakage/false success | A0/A2/A3/Z0 |
| RT-03 | Async context | risposta lenta partita sotto scope A arriva dopo switch a B | risposta scartata/invalidata; mai applicata a B | out-of-order cross-context application | A0/Z0 |
| RT-04 | Deep-link/history | URL con project/discipline/scope corrotto, stale o non autorizzato; back/forward/reload | nuova validazione scope; nessun fallback implicito | restore del contesto precedente senza autorizzazione | A0/A2/Z0 |
| RT-05 | Source identity | SourceVersion/hash mismatch o binding a versione diversa | conflitto/blocco; nessun `latest` implicito | uso della fonte sbagliata come current | A1/Z0 |
| RT-06 | Source vs domain truth | fonte Architecture disponibile e documentale prima del DomainContract | inventory ammesso; entity/property count resta zero | source DOC → entity/property DOC automatica | A0/A3/Z0 |
| RT-07 | Spatial identity | elementi di discipline diverse geometricamente coincidenti/sovrapposti | nessuna identità automatica; relazione solo esplicita/evidence-backed | geometry/spatial coincidence → identity | A3/Z0 |
| RT-08 | Read-model authority | snapshot/cache/projection diverge dall'authority | `AUTHORITY_CONFLICT`, stale o invalidazione; mai winner silenzioso | projection trattata come authority | A4/A5/A6/Z0 |
| RT-09 | Adapter/baseline freshness | adapter o baseline dichiarata non disponibile/incompatibile | fail closed; stato non dichiarato CURRENT | dati stale usati per azione sensibile | A0/A1/A4/A5/Z0 |
| RT-10 | Agent authority | agente tenta Level-C, canonical write o promotion vietata | `HUMAN_AUTHORITY_REQUIRED`/stop; zero mutazioni | professional/canonical state modificato | A5/Z0 |
| RT-11 | Independent assurance | owner prova a soddisfare da solo un controllo dichiarato indipendente | evidence non ammessa come assurance indipendente | bypass di review/assurance richiesta | all promotable slices/Z0 |
| RT-12 | Test fixture isolation | fixture `TEST_ONLY` o TEST_PROJECT raggiunge percorso N12 reale | rifiuto tracciato; zero persistenza N12 | fixture entra in history/canonical N12 | A0/A2/Z0 |
| RT-13 | Human false success | partecipante completa task ma con wrong project/source/authority mental model | task classificato safety failure; usabilità/rapidità non compensa | false success promosso come HVA PASS | applicable HVA/Z0 |
| RT-14 | Candidate drift | candidate cambia dopo HVA/acceptance evidence | nuova candidate identity; evidence precedente non soddisfa nuova promotion salvo equivalenza esplicita | receipt di SHA diverso ereditata silenziosamente | all release slices/Z0 |
| RT-15 | Project-scoped shared source | stesso SourceVersion tecnicamente disponibile in due progetti | permissions/claims/decisions restano project-scoped; esistenza altro progetto non inferibile | shared hash trasferisce project truth/permission | A1/Z0 |
| RT-16 | Relation supersession | relazione interdisciplinare corretta/superseded | genealogia preservata; current projection cambia senza cancellare storia | superseded trattato come deleted | A3/A4/Z0 |
| RT-17 | UI authority | UI mostra stato/candidate/selection apparentemente confermato | UI resta projection; nessun canonical/domain state cambia senza boundary autorizzato | UI action equivale implicitamente a engineering approval | A3-A6/Z0 |
| RT-18 | Deployment authority | feature disponibile in Preview/Pilot/Production | release state resta separato da product promotion e engineering authority | deployment interpretato come promotion/canonical authority | all/Z0 |

## 4. Regole di esito

Un caso è `PASS` solo se il comportamento osservato coincide con il fail-closed atteso e l'evidence package identifica la stessa revisione candidata.

Un caso è `FAIL` se avviene almeno uno dei seguenti effetti:

- leakage;
- false success;
- identity collapse;
- source/version confusion;
- canonical/professional mutation non autorizzata;
- silent fallback;
- silent authority selection;
- reuse non dichiarato di evidence da revisione diversa.

I fallimenti safety/authority sono **non compensabili**.

## 5. Riutilizzo delle prove e same-revision

Conoscenza analitica e finding precedenti possono restare genealogicamente validi se il loro fondamento è ricostruibile e la dipendenza non è cambiata.

Tuttavia una receipt di promozione/HVA/Production smoke non viene trasferita a una nuova revisione per semplice somiglianza. Il riuso promotion-grade richiede la regola di equivalenza esplicita già prevista dalla governance o una nuova esecuzione same-revision.

Questa distinzione permette invalidazione mirata della **conoscenza** senza indebolire la same-revision rule della **promozione**.

## 6. Integrazione per slice

- A0/A2: priorità RT-01..04, RT-12, RT-18;
- A1: priorità RT-05, RT-09, RT-15;
- A3: priorità RT-02, RT-06, RT-07, RT-16, RT-17;
- A4: priorità RT-08, RT-16;
- A5: priorità RT-08..11, RT-17;
- A6: priorità RT-01..04, RT-08, RT-17;
- Z0: esegue l'insieme applicabile sul candidate congelato e non contiene fix funzionali.

## 7. Regola finale

`red-team PASS != HVA PASS != Production smoke != product promotion != engineering authority`.

La matrice serve a rendere più forte l'evidenza di sicurezza, non a collassare le authority.