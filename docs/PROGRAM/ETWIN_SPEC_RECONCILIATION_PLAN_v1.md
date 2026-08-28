# eTwin — Piano di riconciliazione della specifica v1

**Data:** 2026-08-28  
**Stato:** `ACTIVE_RECONCILIATION / NON_PROMOTIVE`  
**Baseline:** `79b6ddb28205f4151d23f330218724fc96d4cc20`  
**Governing L1:** `docs/PROGRAM/ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2.md`  
**Autorità modificata:** nessuna

## 1. Regola del piano

Questo piano non introduce un nuovo lifecycle eTwin. Le etichette `SP-0`, `SP-1`, `SP-2` sono una sequenza temporanea di riconciliazione e terminano prima della ripresa del programma canonico.

```text
SP-0 Genealogy                    COMPLETE — PASS_WITH_FINDINGS
  ↓
SP-1 Conformance & Delta          NEXT
  ↓
SP-2 Controlled Admission
  ↓
RETURN TO CURRENT PROGRAM
CEW_PROMOTED_BASELINE
  ↓
ETW-A0 revalidation
  ↓
A1 → A2 → A3 → A4 → A5 → A6 → Z0
```

Non esistono quindi `SP-3…SP-8` come nuovo programma concorrente.

## 2. SP-0 — Genealogia

**Stato:** `COMPLETE — PASS_WITH_FINDINGS`.

Deliverable:

`docs/AUDIT/ETWIN_GENEALOGY_REGISTER_SP0_v1.md`

Risultato essenziale:

- current authority identificata;
- linea eTwin corrente identificata;
- linea strutturale/ETW storica classificata;
- specifica discovery classificata L7;
- nessuna promotion effettuata;
- nessuna modifica a CEW/N12.

## 3. SP-1 — Conformance & Delta

**Obiettivo:** confrontare il materiale di discovery e gli artefatti eTwin storici con il contratto eTwin v2 corrente, senza trasferirli automaticamente.

### 3.1 Unità di confronto

Per ogni requisito/artefatto assegnare una sola azione:

- `ALREADY_COVERED` — il contratto corrente lo contiene già;
- `REFINE_CURRENT_CONTRACT` — migliora una semantica già ammessa senza cambiare ownership;
- `NEW_OPEN_REQUIREMENT` — tema utile ma non ancora determinabile;
- `KEEP_EXPERIMENTAL` — soluzione da provare, non da promuovere;
- `DOMAIN_OWNED_REFERENCE` — appartiene a CEW/N12/altra disciplina;
- `HISTORICAL_ONLY` — valore genealogico, nessun percorso di ammissione corrente;
- `REJECT_DUPLICATION` — duplica o viola un'authority esistente.

Ogni riga deve anche riportare:

- classe di flessibilità proposta (`INVARIANT/SPECIFIED/OPEN/EXPERIMENTAL/DOMAIN_OWNED`);
- authority owner;
- contratto corrente coinvolto;
- eventuale migrazione;
- gate/evidenza necessaria;
- effetto se non risolta.

### 3.2 Sorgenti obbligatorie

Current authority:

- `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`;
- `docs/GOVERNANCE/CEW_ETWIN_PRODUCT_FAMILY_CAPABILITY_MAP_v1.md`;
- `docs/PROGRAM/ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2.md`;
- `docs/PROGRAM/ETW_AGENTIC_DEVELOPMENT_ORCHESTRATION_v2.md`;
- current ETW status/queue/human gate.

Discovery/history:

- `docs/etwin-system-spec-v1@51cd3d...` e `docs/ETWIN/*` su quel ramo;
- `.asw/plans/etw1-document-engine.md`;
- `.asw/plans/etw2-floor-differential.md`;
- `model/etwin/*`;
- `docs/FOGLIO_LAVORO/ETW_*`;
- dashboard/read-model storico.

### 3.3 Deliverable

`docs/AUDIT/ETWIN_SPEC_CONFORMANCE_MATRIX_SP1_v1.md`

### 3.4 Gate SP1-G

PASS solo se:

- ogni requisito discovery materiale è classificato;
- nessun concetto CEW/N12 viene ricreato come eTwin-owned;
- ogni `OPEN` ha owner e blocker espliciti;
- ogni `EXPERIMENTAL` è non-promotivo;
- non restano due L1 concorrenti;
- l'azione proposta è compatibile con eTwin v2.

## 4. SP-2 — Controlled Admission

**Obiettivo:** ammettere soltanto i delta SP-1 che migliorano davvero il programma corrente.

### 4.1 Regole

- un delta `ALREADY_COVERED` non genera duplicazione documentale;
- un `REFINE_CURRENT_CONTRACT` genera patch/minor coerente e, se materiale, decision record;
- un `NEW_OPEN_REQUIREMENT` viene registrato come work item/open question nel luogo proprietario;
- un `KEEP_EXPERIMENTAL` riceve scope e criteri di falsificazione, non authority;
- un `DOMAIN_OWNED_REFERENCE` usa adapter/reference contract;
- `REJECT_DUPLICATION` e `HISTORICAL_ONLY` restano fuori dal manifest corrente.

### 4.2 Deliverable minimi

A seconda dei delta effettivi:

- decision record;
- eventuale revisione L1/L2;
- eventuale aggiornamento machine-readable L3;
- validator/regression test;
- aggiornamento del `PRODUCT_GOVERNANCE_MANIFEST` solo se cambia un riferimento di authority corrente.

### 4.3 Gate SP2-G

PASS se:

- i delta ammessi sono verificati;
- manifest e validator sono coerenti;
- history resta preservata;
- nessuna promotion CEW/eTwin/N12 è avvenuta per effetto della riconciliazione.

## 5. Rientro nel programma canonico

Dopo SP2-G non esiste un ulteriore piano di specifica. Si rientra nella sequenza corrente già governata:

```text
CEW B1 Human Acceptance v2 / persistence reconciliation
        ↓
CEW_PROMOTED_BASELINE
        ↓
ETW-A0 revalidation under v2 governance
        ↓
APPROVE_PLATFORM_BOUNDARY
        ↓
ETW-A1 → A2 → A3
              ↓
APPROVE_CROSSDISCIPLINE_CONTRACT
              ↓
A4 → A5 → A6 → Z0
                  ↓
APPROVE_PRODUCTION_ACCEPTANCE
```

## 6. Criterio di arresto

La riconciliazione si arresta immediatamente se una proposta:

- sposta l'engineering authority da N12;
- sposta source/evidence/claim/structural semantics fuori da CEW senza decisione di prodotto;
- consente fallback implicito di Project/Discipline/Scope;
- equipara spatial coincidence e identity;
- fa discendere authority da UI, agente, modello, solver, CI o deployment;
- tenta di anticipare A1 prima della revalidation/promozione A0 prevista dal contratto corrente.

In tali casi la riga SP-1 diventa `REJECT_DUPLICATION` o `BLOCKED_DECISION` e non viene implementata.