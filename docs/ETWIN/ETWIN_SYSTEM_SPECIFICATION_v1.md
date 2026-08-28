# eTwin System Specification v1

**Versione:** `1.0-baseline`  
**Stato:** `BASELINE_FOR_DISCOVERY_AND_DESIGN`  
**Data:** 2026-08-28  
**Natura:** contratto di piattaforma governato; non è authority disciplinare  
**Repository:** `antoniocorsano-boop/N12`  
**Baseline repository di questa versione:** `dd5b48e64cb63eb5556d8bcc033b63cdc2bb302e`  
**Ramo di specifica:** `docs/etwin-system-spec-v1`

> Questa specifica definisce i confini e gli invarianti della piattaforma eTwin. Non modifica i dati canonici N12, il Registro Master N12, il Protocollo Canonico N12, i gate M0/M1/M2, né le authority CEW o di altre discipline.

---

## 0. Regola di lettura: specifica governata, non rigida

Ogni requisito appartiene a una delle seguenti classi:

| Classe | Significato | Regola di modifica |
|---|---|---|
| `INVARIANT` | confine di sicurezza, autorità o provenienza non negoziabile nella v1 | richiede revisione architetturale, nuova major se cambia il contratto |
| `SPECIFIED` | scelta corrente necessaria per costruire in modo coerente | può evolvere in modo compatibile con versione minor e decision record |
| `OPEN` | problema deliberatamente non ancora chiuso | va risolto tramite discovery/prova prima dell'implementazione dipendente |
| `EXPERIMENTAL` | soluzione provvisoria ammessa per apprendere | non è authority e può essere sostituita senza migrazione canonica finché non promossa |
| `DOMAIN_OWNED` | concetto o decisione appartenente a CEW/N12 o altra verticale | eTwin può solo riferirlo; non può ridefinirlo |

### 0.1 Principio di flessibilità controllata — `INVARIANT`

La flessibilità è ammessa **dentro i boundary**, non sui boundary. UI, forma del lavoro, tecnologia, schemi interni e strategie degli agenti possono evolvere. Isolamento, authority, provenienza, non-promozione indebita e revisione umana non possono essere aggirati per velocizzare l'evoluzione.

### 0.2 Versionamento — `SPECIFIED`

- `PATCH`: chiarimenti editoriali o requisiti equivalenti senza cambiamento semantico.
- `MINOR`: estensione compatibile di concetti `SPECIFIED`, promozione di un `OPEN`, aggiunta di stati o capacità senza violare invarianti.
- `MAJOR`: modifica di un `INVARIANT`, boundary di authority, isolamento o significato di dati persistenti.

Ogni `MINOR` o `MAJOR` deve avere: motivazione, impatto, artefatti coinvolti, migrazione se necessaria, test di regressione e nuovo fingerprint.

---

# 1. Definizione del prodotto

## 1.1 eTwin — `INVARIANT`

eTwin è una **piattaforma multi-progetto e multidisciplinare evidence-first per il lavoro tecnico professionale**. Coordina progetti, persone, ruoli, scope, attività operative, deleghe, revisioni, handoff e consegne, senza sostituire le authority disciplinari.

## 1.2 Cosa eTwin non è — `INVARIANT`

eTwin non è:

- CEW;
- il modello strutturale N12;
- un nuovo lifecycle parallelo a P0–P16 o ai gate disciplinari;
- un BIM authoring tool universale;
- principalmente un viewer 2D/3D;
- una dashboard generica;
- un knowledge graph presentato come metafora obbligatoria di lavoro;
- un orchestratore agent-first nel quale l'agente sostituisce il professionista;
- una seconda authority epistemica.

## 1.3 N12 — `DOMAIN_OWNED`

N12 è il primo progetto/caso reale di prova. Non definisce da solo il modello dati universale della piattaforma. Le decisioni strutturali N12 restano governate dai documenti e dai gate del dominio strutturale.

---

# 2. Stratificazione delle authority

## 2.1 Regola piattaforma/verticale — `INVARIANT`

**eTwin coordina; la verticale disciplinare conosce e governa il proprio dominio.**

Schema concettuale:

```text
ETWIN PLATFORM
  Studio / Project / Person / Role / Scope
  Work coordination / Delegation / Review / Delivery
        |
        | project-scoped references
        v
DOMAIN AUTHORITIES
  Structures -> CEW
  Architecture -> authority disciplinare dedicata
  Geotechnics -> authority disciplinare dedicata
  MEP -> authority disciplinare dedicata
        |
        v
SOURCE / EVIDENCE CHAINS
```

## 2.2 Ownership minima — `INVARIANT`

| Concetto | Owner |
|---|---|
| `Project` | eTwin |
| `Person` / identity reference | eTwin |
| `Role` / role assignment | eTwin |
| `ActiveRoleContext` | eTwin |
| registro discipline | eTwin |
| `ScopeContext` | eTwin |
| coordinamento del lavoro | eTwin |
| mandato di agente | eTwin |
| coordinamento interdisciplinare | eTwin |
| Evidence disciplinare | domain authority |
| Claim / Assertion disciplinare | domain authority |
| Entity disciplinare | domain authority |
| Decision disciplinare | domain authority |
| Gate disciplinare | domain authority |
| P0–P16 CEW | CEW |
| Level C | authority umana prevista dal dominio |

Nomi differenti non autorizzano duplicazioni semanticamente equivalenti.

---

# 3. Identità, ruoli, capacità e autorità

## 3.1 Separazione fondamentale — `INVARIANT`

```text
Person != Role != Capability != Authority != Scope
```

L'appartenenza, il possesso di una capacità tecnica o l'assegnazione di un ruolo non implicano automaticamente authority decisionale.

## 3.2 `ProjectRoleAssignment` — `SPECIFIED`

Una `Person` può ricevere più assegnazioni di ruolo nello stesso progetto o in progetti diversi.

## 3.3 `ActiveRoleContext` — `INVARIANT`

Ogni azione authority-sensitive deve avvenire in un contesto di ruolo attivo esplicito e registrabile. Il sistema non deve fondere silenziosamente i permessi di ruoli differenti appartenenti alla stessa persona.

## 3.4 Studio individuale e team — `INVARIANT`

Il modello deve supportare senza migrazione concettuale:

- una sola persona che cumula più ruoli;
- team multidisciplinari;
- collaboratori con scope limitato;
- revisori esterni;
- successivo ingresso di nuove persone nel progetto.

Il cumulo dei ruoli non annulla i requisiti di indipendenza. Dove serve un secondo soggetto reale, il sistema deve produrre `INDEPENDENT_REVIEW_REQUIRED` e impedire l'auto-approvazione.

---

# 4. Project isolation

## 4.1 `project_id` hard boundary — `INVARIANT`

`project_id` è un confine di sicurezza e deve propagarsi almeno a:

- routing;
- query;
- storage project-scoped;
- cache;
- ricerca;
- memoria di sessione dell'agente;
- tool call;
- async request/response;
- deep-link;
- history/reload;
- read-model e snapshot;
- receipt;
- export e consegne.

## 4.2 Zero leakage — `INVARIANT`

Un dato ottenuto sotto Project A non è osservabile, utilizzabile o inferibile in Project B senza una relazione/operazione inter-progetto esplicitamente autorizzata e tracciata.

La semplice presenza dello stesso `SourceVersion` in due progetti non rende osservabile l'esistenza dell'altro progetto.

## 4.3 Fail closed — `INVARIANT`

Su scope mancante, mismatch di progetto, deep-link non autorizzato, risposta asincrona fuori contesto o cache non riconciliabile, il sistema deve rifiutare o invalidare il dato; non deve effettuare fallback verso un progetto precedente o predefinito.

---

# 5. Discipline e Scope

## 5.1 Discipline — `SPECIFIED`

La piattaforma mantiene un registro di discipline. Una disciplina non acquisisce authority solo perché registrata: deve avere un proprio `DomainContract` o essere esplicitamente `NOT_YET_RELEASED`.

## 5.2 `ScopeContext` — `SPECIFIED`

Minimo concettuale:

```text
ScopeContext
  project_id             required
  scope_kind             PROJECT_WIDE | DISCIPLINE_SET | UNCLASSIFIED
  discipline_scope[]     0..N
  owner_discipline_id?   optional
```

Sono candidati `OPEN` da validare nei journey:

- `spatial_scope`;
- `entity_scope`;
- `source_scope`;
- `baseline_scope` / temporal scope.

## 5.3 `UNCLASSIFIED` — `INVARIANT`

`UNCLASSIFIED` non significa `COMMON`, `SHARED` o nuova disciplina universale. Indica che la classificazione disciplinare non è ancora risolta o non è applicabile nel contesto definito.

---

# 6. Fonti e identità documentale

## 6.1 `SourceVersion` — `SPECIFIED`

`SourceVersion` identifica contenuto immutabile tramite identità tecnica/hash ed è concettualmente separato dal suo uso nel progetto.

## 6.2 `ProjectSourceBinding` — `SPECIFIED`

Il binding project-scoped può contenere:

- `project_id`;
- discipline/scope;
- alias/nome visibile;
- classificazione;
- permessi;
- provenienza di progetto;
- metadati di progetto.

Il binding non cambia l'hash della `SourceVersion`.

## 6.3 Deduplicazione globale — `OPEN`

L'implementazione può deduplicare contenuti identici a livello tecnico, ma deve dimostrare che tale deduplicazione non permette leakage, enumeration o inferenza tra progetti.

## 6.4 Fonte `DOC` — `INVARIANT`

Il fatto che una fonte sia documentale non promuove automaticamente a `DOC` una entity, proprietà, identità o relazione derivata.

---

# 7. Riferimenti platform-to-domain

## 7.1 `ProjectScopedReference` — `SPECIFIED`

La piattaforma deve poter riferire oggetti delle authority disciplinari senza copiarli. Il riferimento deve includere almeno:

- `project_id`;
- `domain_id` / `discipline_id`;
- `object_type`;
- `object_id` stabile nel dominio;
- versione/fingerprint quando necessario;
- stato di risoluzione.

## 7.2 No semantic duplication — `INVARIANT`

Un oggetto eTwin non deve diventare una copia mutabile di Evidence, Claim, PropertyAssertion, Entity, Decision o Gate del dominio.

Read-model e cache possono materializzare proiezioni, ma la loro authority resta `READ_MODEL_ONLY`.

---

# 8. Interdisciplinarità

## 8.1 Triade semantica — `SPECIFIED`

Separare:

```text
SpatialReference
DisciplineEntityReference
CrossDisciplineRelation
```

## 8.2 Regole di identità — `INVARIANT`

- spazio != entità;
- geometria coincidente != identità;
- vicinanza != equivalenza;
- similarità != stessa entity;
- assenza/ND in una disciplina != assenza nell'altra;
- una relazione interdisciplinare deve essere esplicita, revisionabile e evidence-backed quando ha significato tecnico.

## 8.3 Stati delle relazioni — `OPEN`

La tassonomia esatta delle relazioni (`CONFIRMED`, `CANDIDATE`, `SAME_AREA_DIFFERENT_IDENTITY`, ecc.) sarà definita solo dopo casi reali Structures/Architecture. Non può però contenere equivalenza automatica da geometria.

---

# 9. Assertion-first e genealogia

## 9.1 Assertion concorrenti — `INVARIANT`

Una proiezione operativa corrente non cancella assertion concorrenti, conflitti o genealogia dell'authority disciplinare.

## 9.2 Supersession — `INVARIANT`

```text
SUPERSEDED != DELETED
CORRECTED != ERASED
```

Correzioni e revisioni devono conservare il precedente oggetto quando il dominio lo richiede e devono poter spiegare perché la rappresentazione corrente è cambiata.

## 9.3 Ownership — `DOMAIN_OWNED`

La forma esatta delle assertion e della promotion è definita dall'authority disciplinare. eTwin può rappresentarne la genealogia tramite riferimenti e read-model.

---

# 10. Agenti specialistici

## 10.1 Agente subordinato al mandato — `INVARIANT`

Un agente non possiede authority professionale autonoma. Opera soltanto sotto un mandato esplicito contenente progetto, ruolo, scope, fonti/strumenti consentiti e azioni vietate.

## 10.2 Contratto universale minimo — `SPECIFIED`

Ogni esecuzione authority-sensitive deve essere riconducibile almeno a:

```text
AgentExecution
  agent_id
  agent_version
  project_id
  active_role_context
  discipline_scope
  mandate
  permitted_tools
  prohibited_actions
  domain_contract_ref
  normative_baseline_ref?
  source_versions_used[]
  assumptions[]
  uncertainties[]
  result_ref / result_payload
  execution_receipt
  required_review
  human_disposition?
```

## 10.3 Organizzazione degli agenti — `OPEN`

Non è ancora stabilito che debba esistere esattamente un `RoleSupportAgent` per ogni ruolo. Sono ammesse, da valutare, composizione per capacità, agenti di ruolo o agenti specialistici condivisi, purché il mandato e l'authority boundary restino invariati.

## 10.4 Stato di riconciliazione — `SPECIFIED`

Per attività sensibili l'agente deve esporre uno stato verificabile:

- `CURRENT`;
- `STALE`;
- `UNRECONCILED`.

La semantica di `CURRENT` deve derivare da fingerprint verificabili di agent version, DomainContract, baseline rilevanti e toolset; non può essere una semplice etichetta.

`STALE` o `UNRECONCILED` devono fallire chiusi sulle attività per le quali la freschezza è condizione di autorità.

## 10.5 Divieti — `INVARIANT`

L'agente non può:

- promuovere autonomamente stati epistemici riservati al dominio/umano;
- risolvere un `AUTHORITY_CONFLICT` per convenienza;
- completare Level C;
- approvare il proprio output;
- aggirare un requisito di revisione indipendente;
- mutare direttamente dati canonici senza il percorso di promotion autorizzato.

---

# 11. Revisione umana e indipendente

## 11.1 Human authority — `INVARIANT`

Quando il DomainContract richiede decisione o approvazione umana, l'output automatico è proposta/evidenza di supporto e non decisione.

## 11.2 Independent review — `INVARIANT`

Se una regola richiede indipendenza sostanziale, autore e reviewer non possono coincidere sullo stesso fingerprint anche se la stessa `Person` possiede entrambi i ruoli.

## 11.3 Receipt — `INVARIANT`

I receipt di delega, revisione e promozione devono essere append-only o equivalenti per immutabilità/auditabilità. Una correzione genera nuova genealogia; non riscrive retroattivamente il receipt originale.

---

# 12. Modello degli stati

Le categorie devono restare distinte.

## 12.1 Runtime states — `SPECIFIED`

- `LOADING`
- `ERROR`
- `UNAVAILABLE`

Descrivono capacità runtime, non stato epistemico.

## 12.2 Availability/release states — `SPECIFIED`

- `ACTIVE`
- `NOT_YET_RELEASED`
- `TEST_ONLY`

`TEST_ONLY` non può essere usato come evidenza reale o authority di produzione.

## 12.3 Governance states — `SPECIFIED`

- `STALE`
- `UNRECONCILED`
- `AUTHORITY_CONFLICT`
- `HUMAN_AUTHORITY_REQUIRED`
- `INDEPENDENT_REVIEW_REQUIRED`

Ogni nuovo stato deve dichiarare: producer, significato, blocking effect, exit condition, persistenza e receipt/provenienza richiesta.

## 12.4 Nessun appiattimento UI — `INVARIANT`

Gli stati di governance non possono essere presentati come semplici errori tecnici o ridotti a colore/icone senza testo comprensibile.

---

# 13. Snapshot, read-model e cache

## 13.1 Read-model only — `INVARIANT`

Snapshot, dashboard model, materialized view e cache sono derivati. Non possono diventare authority né elevare lo stato epistemico.

## 13.2 Divergenza — `INVARIANT`

Se read-model/snapshot e authority canonica divergono oltre la tolleranza esplicitamente definita, il sistema deve produrre `AUTHORITY_CONFLICT`, `STALE` o invalidazione; non deve scegliere silenziosamente la versione più comoda.

## 13.3 Rebuildability — `SPECIFIED`

Ogni read-model usato per decisioni operative deve dichiarare origine, fingerprint e processo di ricostruzione.

---

# 14. Runtime e sicurezza asincrona

## 14.1 Context token — `SPECIFIED`

Ogni operazione asincrona significativa deve poter essere ricondotta al contesto che l'ha originata almeno per `project_id`, discipline/scope e active role quando pertinente.

## 14.2 Out-of-order response — `INVARIANT`

Una risposta appartenente a un contesto precedente non può essere applicata al nuovo contesto dopo project/discipline/role switching.

## 14.3 Deep-link/history/reload — `INVARIANT`

Ripristino e navigazione devono validare nuovamente scope e permessi; nessun fallback verso dati precedentemente in cache.

---

# 15. UX invariants

## 15.1 Principi — `INVARIANT`

L'esperienza deve essere:

- task-oriented, non struttura-interna-oriented;
- project/discipline/role aware;
- provenance reachable;
- authority-aware;
- fail-closed per scope sensibili;
- accessibile da tastiera;
- con focus visibile e gerarchia tipografica funzionale;
- senza affidare semantica critica al solo colore;
- basata su progressive disclosure;
- non viewer-first;
- non agent-first.

## 15.2 Information architecture — `OPEN`

Non sono ancora congelati:

- Home;
- menu e tab;
- modalità `Conoscenza / Esplora / Risolvi / Evidenze / Consegna`;
- posizione del viewer;
- posizione dell'assistente;
- forma del workspace.

Queste decisioni devono derivare dai journey reali.

---

# 16. Modello operativo del lavoro

## 16.1 Primitivo operativo — `OPEN`

Non è ancora canonico `TechnicalActivity`, `WorkItem` o altra struttura equivalente.

La decisione deve derivare da casi reali e deve dimostrare di supportare almeno:

- lavoro curato personalmente;
- delega ad agente;
- assegnazione a collaboratore;
- revisione;
- blocchi e dipendenze;
- evidenze e riferimenti disciplinari;
- handoff/consegna;
- studio individuale e team.

## 16.2 Divieto di anticipazione — `INVARIANT`

Un mockup o un'implementazione non può rendere canonico implicitamente un modello di lavoro ancora `OPEN`.

---

# 17. Estensione a nuove discipline

## 17.1 DomainContract — `SPECIFIED`

Una nuova verticale deve dichiarare almeno:

- `domain_id` / discipline;
- owner dell'authority;
- entità/proprietà disciplinari;
- stati epistemici rilevanti;
- promotion boundary;
- Level C o equivalente se presente;
- source/admission rules;
- gate/lifecycle;
- riferimenti platform-to-domain consentiti;
- operazioni read-only e write/promote;
- failure behavior.

## 17.2 No automatic release — `INVARIANT`

La presenza di fonti di una disciplina non rende il dominio rilasciato e non autorizza la creazione automatica di entity/property canoniche.

---

# 18. HVA, test e red-team

## 18.1 Technical green != human validation — `INVARIANT`

Pass di test, build o smoke non equivale a HVA, visual PASS, approvazione professionale o gate umano.

## 18.2 Safety metrics non compensabili — `INVARIANT`

Almeno:

- `cross_project_leakage`;
- `cross_discipline_leakage`;
- `cross_discipline_false_equivalence`;
- `discipline_owner_misidentification`;
- `spatial_relation_misread_as_identity`;
- `wrong_active_role`;
- `agent_authority_overreach`;
- `stale_agent_used_for_authority_sensitive_task`;
- `independent_review_bypass`.

Un fallimento safety non può essere compensato da rapidità, usabilità o estetica.

## 18.3 Red-team minimo — `SPECIFIED`

Ogni release di piattaforma che tocca i relativi boundary deve provare almeno:

1. N12 -> TEST_PROJECT e ritorno con cache popolata: zero leakage;
2. discipline switching rapido: zero leakage;
3. async fuori ordine: zero applicazione cross-context;
4. deep-link corrotto/non autorizzato: fail closed;
5. SourceVersion/hash mismatch: conflitto/blocco;
6. fonte DOC + dominio non rilasciato: zero entity automatica;
7. geometria coincidente: zero equivalenza semantica automatica;
8. adapter stale/unavailable: nessun dato dichiarato CURRENT senza prova;
9. snapshot divergente: conflitto/stale, non authority silenziosa;
10. agente tenta Level C/promotion vietata: `HUMAN_AUTHORITY_REQUIRED`, zero mutazioni;
11. agente stale su task sensibile: blocco;
12. self-review vietata: `INDEPENDENT_REVIEW_REQUIRED`;
13. fixture `TEST_ONLY` verso progetto reale: rifiuto tracciato.

Ogni prova registra precondizioni, input, expected fail-closed, observed, evidence reference, fingerprint e risultato.

---

# 19. Conformance rules

Un'implementazione è **non conforme** se introduce almeno uno dei seguenti casi:

- duplicazione semantica delle authority CEW/domain;
- leakage cross-project o cross-discipline;
- promozione di `ND/INC/INF` per convenienza;
- geometria usata come identità automatica;
- source `DOC` usata come promotion automatica;
- snapshot/read-model trattato come authority;
- Level C o equivalente completato da agente;
- receipt mutabile senza genealogia;
- dato/hash/source inventato;
- fixture `TEST_ONLY` usata come evidenza reale;
- agente sensibile stale/unmandated che continua;
- independent review bypass;
- technical green presentato come HVA.

---

# 20. Decisioni deliberatamente aperte nella v1

Le seguenti questioni non bloccano la baseline della specifica, ma bloccano l'implementazione che dipende da esse:

1. forma canonica del primitivo operativo di lavoro;
2. information architecture e Home;
3. tassonomia definitiva delle `CrossDisciplineRelation`;
4. granularità di `ScopeContext` oltre il minimo;
5. deduplicazione globale delle `SourceVersion` e relativo threat model;
6. modello organizzativo degli agenti (per ruolo, capacità, composizione);
7. tecnologia di persistenza e deployment della piattaforma;
8. semantica completa delle consegne e degli handoff;
9. confine esatto fra reference platform e read-model di dominio;
10. prima verticale Architecture e suo DomainContract.

---

# 21. Genealogia e stato delle implementazioni esistenti

## 21.1 Implementazioni eTwin storiche nel repository — `EXPERIMENTAL`

Gli artefatti esistenti in `.asw/plans/etw*`, `model/etwin/*`, `docs/FOGLIO_LAVORO/ETW_*` e `docs/FOGLIO_LAVORO/dashboard/*` sono input di genealogia e sperimentazione N12. Non diventano automaticamente il modello di piattaforma.

In particolare, eventuali definizioni locali di `Claim`, `StructuralEntity`, verification status o entity binding devono essere confrontate con le authority CEW/domain prima di essere riusate. La compatibilità non si presume dal nome.

## 21.2 Dossier di discovery 2026-08-28 — `EXPERIMENTAL_INPUT`

Il dossier fornito per independent review è input principale di consolidamento ma non è authority. Dichiarava un HEAD `40e126c01e4ba5966255976a93c329256374626b`, che non è risolvibile nel repository N12 corrente al momento della stesura. La presente specifica è quindi fingerprintata sulla baseline reale `dd5b48e64cb63eb5556d8bcc033b63cdc2bb302e`.

---

# 22. Fingerprint e revisione

## 22.1 Fingerprint minimo — `SPECIFIED`

Ogni review formale deve registrare:

- repository;
- branch/ref;
- commit SHA;
- versione della specifica;
- hash/fingerprint dei contratti esterni rilevanti;
- scope della review;
- reviewer;
- esito.

## 22.2 Invalidazione mirata — `SPECIFIED`

Un cambiamento di HEAD non rende automaticamente inutile tutta la conoscenza precedente. Invalida la review **per le parti il cui fingerprint o dipendenze sono cambiate**. Le decisioni e prove non impattate restano genealogicamente valide se la loro base è ancora ricostruibile.

Una modifica a un `INVARIANT` richiede invece revalidation completa dei boundary interessati.

---

# 23. Condizione di passaggio alla progettazione operativa

La piattaforma non deve essere ulteriormente cristallizzata nella UI prima di aver completato un gate di discovery almeno su:

```text
Persona x Role x Task x Authority x Scope
```

provato sia per studio individuale sia per team.

Il gate deve utilizzare casi reali, almeno uno con agente, uno con revisione e uno interdisciplinare. Solo dopo può essere promosso un primitivo operativo (`WorkItem`, `TechnicalActivity` o equivalente) da `OPEN` a `SPECIFIED`.

---

# 24. Fonti autorevoli e informative

## 24.1 Domain-owned nel repository N12

- `docs/STATO_RIPRESA.md`
- `docs/REGISTRO_MASTER.md`
- `docs/PROTOCOLLO_CANONICO.md`
- `docs/DECISIONI/*`
- dataset canonici e gate del dominio strutturale

Questi documenti non sono sostituiti dalla presente specifica.

## 24.2 Genealogia informativa

- `.asw/plans/etw1-document-engine.md`
- `.asw/plans/etw2-floor-differential.md`
- `model/etwin/*`
- `docs/FOGLIO_LAVORO/ETW_*`
- `docs/FOGLIO_LAVORO/dashboard/*`

## 24.3 Regola finale

> Se una scelta futura può cambiare senza violare authority, isolamento, provenienza o responsabilità, deve poter evolvere tramite il processo di versione previsto. Se invece una scelta riduce uno di questi boundary, non è “flessibilità”: è una modifica del contratto e deve essere trattata come tale.
