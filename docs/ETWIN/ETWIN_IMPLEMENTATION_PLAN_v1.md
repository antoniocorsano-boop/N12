# eTwin Implementation Plan v1

**Versione:** `1.0`  
**Data:** 2026-08-28  
**Dipendenza:** `docs/ETWIN/ETWIN_SYSTEM_SPECIFICATION_v1.md`  
**Stato:** `PLANNED — NO PLATFORM PROMOTION AUTHORIZED`  
**Obiettivo:** trasformare la specifica di piattaforma in verticali verificabili senza duplicare CEW, senza assumere N12 come modello universale e senza cristallizzare prematuramente UI o modello operativo.

---

# 1. Regole del piano

1. Ogni fase produce un artefatto verificabile, non solo codice.
2. Un gate tecnico non sostituisce HVA o decisione umana.
3. Gli `INVARIANT` della System Specification prevalgono sulle scelte di fase.
4. Gli elementi `OPEN` vengono chiusi solo quando una prova reale li rende falsificabili.
5. Una soluzione `EXPERIMENTAL` può essere scartata senza migrazione canonica finché non viene promossa a `SPECIFIED`.
6. N12 è il banco di prova iniziale; nessuna proprietà specifica N12 diventa automaticamente requisito universale.
7. Il lavoro strutturale N12 e i suoi gate continuano nella propria authority; questo piano non li rinomina né li riordina.

---

# 2. Sequenza complessiva

```text
SP-0  Baseline & Genealogy
  |
  v
SP-1  Platform Contract Conformance
  |
  v
SP-2  Persona × Role × Task × Authority × Scope Discovery
  |
  v
SP-3  Operational Work Model
  |
  v
SP-4  A0 Platform Identity & Isolation Vertical
  |
  v
SP-5  A1 Source Binding & Cross-Discipline Foundation
  |
  v
SP-6  Delegation / Agent Governance Vertical
  |
  v
SP-7  HVA + Safety + Independent Review
  |
  v
SP-8  Controlled Platform Baseline
```

Le fasi `SP-*` appartengono al programma di piattaforma e non sostituiscono i gate `M0-*`, CEW o P0–P16.

---

# 3. SP-0 — Baseline & Genealogy

**Scopo:** sapere con certezza da quale repository, contratti e artefatti stiamo partendo.

## Attività

- congelare SHA corrente della branch di lavoro;
- censire `docs/STATO_RIPRESA.md`, `docs/REGISTRO_MASTER.md`, `docs/PROTOCOLLO_CANONICO.md` e decisioni rilevanti;
- censire `.asw/plans/etw*`, `model/etwin/*`, `docs/FOGLIO_LAVORO/ETW_*`, dashboard/read-model;
- classificare ogni artefatto come `DOMAIN_OWNED`, `EXPERIMENTAL`, `READ_MODEL_ONLY`, `HISTORICAL` o `CANDIDATE_PLATFORM`;
- verificare i riferimenti storici non più risolvibili, incluso il fingerprint `40e126c...` dichiarato dal dossier;
- registrare dipendenze verso CEW/P0–P16 solo se materialmente verificabili.

## Deliverable

`docs/ETWIN/ETWIN_GENEALOGY_REGISTER_v1.md`

## Gate `SP0-G`

**PASS** se:

- nessun artefatto storico viene scambiato per authority corrente;
- ogni source of truth rilevante è identificato;
- i fingerprint non riproducibili sono marcati come tali;
- non esiste un authority conflict non dichiarato.

**BLOCK** se una decisione di piattaforma dipende da un contratto non reperibile o non identificato.

---

# 4. SP-1 — Platform Contract Conformance

**Scopo:** confrontare l'implementazione esistente con la nuova specifica senza riscriverla automaticamente.

## Attività

Costruire una matrice per:

- `model/etwin/*`;
- dashboard/read-model;
- workflow ETW;
- registri e JSON sperimentali.

Per ogni componente assegnare:

```text
KEEP
ADAPT
ISOLATE_AS_DOMAIN_TOOL
EXPERIMENT
DEPRECATE
BLOCKED_BY_OPEN_SPEC
```

Controlli minimi:

- duplicazione di Evidence/Claim/Entity/Decision/Gate;
- authority implicita nei read-model;
- project hard-boundary;
- disciplina/scope;
- semantica dei candidate binding;
- source/hash provenance;
- possibili leakage da cache o snapshot;
- uso di `ETW_*` come prefisso storico senza confonderlo con piattaforma.

## Deliverable

`docs/ETWIN/ETWIN_CONFORMANCE_MATRIX_v1.md`

## Gate `SP1-G`

**PASS** se ogni componente esistente ha una classificazione e nessuna incompatibilità critica è lasciata implicitamente attiva.

Nessuna refactor applicativa è richiesta per chiudere SP-1: il gate produce prima una decisione di compatibilità.

---

# 5. SP-2 — Discovery Persona × Role × Task × Authority × Scope

**Scopo:** evitare una piattaforma disegnata intorno ai concetti interni anziché al lavoro professionale.

## Casi minimi

Usare 3–5 attività N12 realmente avvenute e almeno un caso interdisciplinare controllato. Il set iniziale consigliato:

1. riconciliare un telaio/documentazione con geometria già ricostruita;
2. correggere un'interpretazione precedente senza perdere genealogia;
3. delegare una ricerca/riconciliazione a un agente e revisionarne l'output;
4. gestire un conflitto Structures ↔ Architecture o, se Architecture non è rilasciata, simulare il boundary senza creare entity;
5. preparare una consegna usando solo risultati sufficientemente governati.

## Per ogni journey registrare

```text
trigger
persona
active role
project
scope
input
sources/evidence needed
decision rights
actions
agent option
review requirement
failure/recovery
handoff
output
provenance lookup
exit condition
```

Devono essere provati almeno:

- studio individuale con più ruoli;
- team con assegnazioni separate;
- revisione indipendente non aggirabile.

## Deliverable

- `ETWIN_USER_MODEL_v1.md`
- `ETWIN_TASK_CATALOG_v1.md`
- `ETWIN_AUTHORITY_SCOPE_MATRIX_v1.md`
- `ETWIN_CRITICAL_JOURNEYS_v1.md`

## Gate `SP2-G`

**PASS** se i journey mostrano bisogni comuni sufficienti a derivare un modello operativo senza dipendere da peculiarità grafiche N12.

**BLOCK** se il modello richiede di conoscere la struttura interna di CEW per svolgere un compito ordinario o se studio individuale/team richiedono modelli dati incompatibili.

---

# 6. SP-3 — Operational Work Model

**Scopo:** risolvere l'`OPEN` relativo all'unità di lavoro.

## Candidati

Valutare almeno:

- `WorkItem`;
- `TechnicalActivity`;
- combinazione `Task / Issue / Review / Delivery`;
- un modello più semplice se i journey lo consentono.

## Criteri non negoziabili

Il modello scelto deve supportare:

- project/scope;
- active role;
- assignee persona/agente/reviewer;
- authority boundary;
- riferimenti domain-owned;
- blocchi/dipendenze;
- incertezze;
- review;
- handoff/delivery;
- genealogia;
- solo/team senza migrazione.

Non deve duplicare Evidence/Claim/Decision/Gate.

## Deliverable

`docs/ETWIN/ETWIN_WORK_MODEL_v1.md`

Se il gate passa, aggiornare System Specification a `1.1` promuovendo il primitivo scelto da `OPEN` a `SPECIFIED`.

## Gate `SP3-G`

**PASS** solo se il modello è verificato contro tutti i journey SP-2 e non richiede eccezioni authority-breaking.

---

# 7. SP-4 — A0 Platform Identity & Isolation Vertical

**Scopo:** prima verticale runtime realmente di piattaforma.

Non deve essere viewer-first.

## Capacità minime

- `Project`;
- registry discipline;
- `Person`/identity reference;
- `ProjectRoleAssignment`;
- `ActiveRoleContext`;
- `ScopeContext` minimo;
- adapter read-only verso Structures/CEW/N12;
- project/discipline/role switching fail-closed;
- cache/async/deep-link/history con context validation;
- visualizzazione esplicita di progetto, disciplina e ruolo attivo.

## Vincoli

- nessun `ProjectSourceBinding` se non ancora autorizzato dalla verticale successiva;
- nessuna migration dei primitivi CEW;
- nessuna entity Architecture automatica;
- nessuna promotion Level C;
- zero write path verso canonical Structures.

## Test minimi

- N12 ↔ TEST_PROJECT con cache popolata;
- Structures ↔ Architecture non rilasciata;
- async fuori ordine;
- deep-link non autorizzato;
- reload/history;
- wrong active role;
- adapter unavailable/stale.

## Gate `SP4-G / A0`

`PREP_PASS` tecnico non promuove la piattaforma. Servono anche baseline CEW verificata, HVA pertinente e approvazione esplicita del platform boundary secondo la governance corrente.

---

# 8. SP-5 — A1 Source Binding & Cross-Discipline Foundation

**Scopo:** introdurre il primo collegamento di piattaforma verso fonti e relazioni interdisciplinari senza trasformare la piattaforma in domain authority.

## Capacità minime

- `ProjectSourceBinding`;
- `ProjectScopedReference`;
- separation `SourceVersion` / binding;
- `SpatialReference`;
- `DisciplineEntityReference`;
- prima forma sperimentale di `CrossDisciplineRelation`;
- threat model della deduplicazione globale;
- source/hash mismatch handling.

## Acceptance

- stesso file in due progetti: nessun leakage;
- TAV-02 e TAV-02S restano fonti distinte se il registro le distingue;
- fonte Architecture `DOC` + dominio non rilasciato: zero entity automatica;
- geometria coincidente: zero equivalenza automatica;
- relazione interdisciplinare sempre esplicita e revisionabile.

## Gate `SP5-G / A1`

PASS solo con red-team project + discipline isolation e traceability completa.

---

# 9. SP-6 — Delegation / Agent Governance Vertical

**Scopo:** introdurre gli agenti solo dopo aver provato identity, scope e isolation.

## Capacità minime

- AgentDefinition/version;
- mandate;
- permitted/prohibited tools;
- project + role + discipline scope;
- reconciliation state `CURRENT/STALE/UNRECONCILED`;
- execution receipt append-only;
- human disposition;
- independent review requirement;
- zero direct Level C/promotion.

## Decisione ancora aperta

Confrontare:

- agenti per ruolo;
- agenti per capacità;
- composizione dinamica sotto mandato.

La scelta deve essere guidata dai journey, non dalla convenienza del framework agentico.

## Gate `SP6-G`

PASS solo se:

- stale agent sensitive task -> fail closed;
- overreach -> zero mutation;
- agent self-approval -> rifiutato;
- output sempre attribuibile a versione, mandato, fonti e fingerprint.

---

# 10. SP-7 — HVA + Safety + Independent Review

**Scopo:** provare che il sistema corretto tecnicamente sia anche comprensibile e utilizzabile senza false success.

## HVA minima

Misurare:

- task success;
- abandonment;
- false success;
- critical error;
- time-on-task;
- help/backtracking;
- confidence;
- provenance lookup;
- riconoscimento di project/discipline/role;
- comprensione di agent output vs human decision.

## Safety non compensabile

Usare le metriche definite dalla System Specification. Zero compensazione tramite punteggi medi.

## Independent review

Reviewer e autore non coincidono sullo stesso fingerprint quando il gate lo richiede.

## Gate `SP7-G`

`PASS` richiede zero blocker safety e zero evidence gap critici.

---

# 11. SP-8 — Controlled Platform Baseline

**Scopo:** produrre la prima baseline eTwin utilizzabile come fondazione per verticali successive.

## Deliverable

- System Specification aggiornata;
- conformance matrix finale;
- platform runtime contract;
- security/isolation evidence pack;
- HVA receipt;
- independent review receipt;
- open questions residue;
- migration/deprecation map degli esperimenti storici.

## Gate `SP8-G`

Solo qui una versione può essere marcata `CONTROLLED_PLATFORM_BASELINE`.

Questo gate non approva decisioni ingegneristiche e non modifica i gate disciplinari.

---

# 12. Priorità operative immediate

Ordine da eseguire adesso:

1. **SP-0** — creare il registro genealogico e chiarire i contratti realmente presenti;
2. **SP-1** — classificare il codice eTwin esistente rispetto alla nuova specifica;
3. **SP-2** — discovery sui journey reali;
4. solo dopo decidere il modello operativo SP-3;
5. nessun nuovo mockup strutturale o piattaforma generalizzata prima di SP2-G;
6. nessun refactor massivo di `model/etwin` prima della matrice SP-1.

---

# 13. Criterio di aggiornamento del piano

Il piano è deliberatamente evolutivo.

Una fase può essere:

```text
PLANNED
READY
IN_PROGRESS
BLOCKED
PASS
SUPERSEDED
```

Una nuova evidenza può:

- cambiare una fase futura;
- aggiungere un test;
- ridurre o ampliare lo scope;
- sostituire una soluzione `EXPERIMENTAL`.

Non può invece eliminare retroattivamente un gate già necessario per un `INVARIANT` senza modifica formale della System Specification.

> Il piano deve adattarsi all'apprendimento; gli invarianti devono proteggere il sistema dall'adattamento opportunistico.
