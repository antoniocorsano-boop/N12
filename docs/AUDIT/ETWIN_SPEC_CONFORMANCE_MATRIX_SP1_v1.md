# eTwin — Matrice di conformità e delta SP-1 v1

**Data:** 2026-08-28  
**Stato:** `SP1-G — PASS_WITH_OPEN_ITEMS`  
**Baseline corrente confrontata:** `79b6ddb28205f4151d23f330218724fc96d4cc20`  
**Discovery confrontata:** `docs/etwin-system-spec-v1@51cd3d265f142665c4f83da972529e37751cf9a0`  
**Contratto L1 corrente:** `docs/PROGRAM/ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2.md`  
**Effetto di authority:** `NONE`

## 1. Metodo

La specifica discovery non viene confrontata come candidata a sostituire il contratto corrente. Ogni suo blocco viene classificato secondo l'azione minima necessaria:

- `ALREADY_COVERED`;
- `REFINE_CURRENT_CONTRACT`;
- `NEW_OPEN_REQUIREMENT`;
- `KEEP_EXPERIMENTAL`;
- `DOMAIN_OWNED_REFERENCE`;
- `HISTORICAL_ONLY`;
- `REJECT_DUPLICATION`.

La classe di flessibilità (`INVARIANT`, `SPECIFIED`, `OPEN`, `EXPERIMENTAL`, `DOMAIN_OWNED`) è proposta come annotazione e non crea un nuovo livello di authority.

## 2. Matrice

| # | Tema discovery | Copertura corrente | Azione SP-1 | Classe | Owner | Impatto / quando serve |
|---:|---|---|---|---|---|---|
| 0 | classificazione flessibile dei requisiti | non formalizzata come tassonomia | `REFINE_CURRENT_CONTRACT` | `SPECIFIED` | Product Governance | ammettere solo la convenzione ETWIN-SPEC-001; nessun nuovo L1 |
| 1 | eTwin multi-project/multi-discipline, non CEW/N12/viewer-first | esplicito in eTwin v2 + capability map | `ALREADY_COVERED` | `INVARIANT` | eTwin L1 | nessun cambio |
| 2 | eTwin coordina, verticale governa il dominio | esplicito | `ALREADY_COVERED` | `INVARIANT` | Product Family Governance | nessun cambio |
| 3A | `Person != Role != Capability != Authority != Scope` | principi di authority presenti, ma non modello platform Person/Role | `NEW_OPEN_REQUIREMENT` | `OPEN` | eTwin future collaboration | non blocca A0/A1; richiede journey reali prima di persistenza |
| 3B | `ProjectRoleAssignment` / `ActiveRoleContext` | non ammessi nel L1 corrente | `NEW_OPEN_REQUIREMENT` | `OPEN` | eTwin future collaboration | introdurre solo con capability di collaborazione/delega |
| 3C | indipendenza sostanziale della review | independent assurance + participant/reviewer separation già governati | `ALREADY_COVERED` | `INVARIANT` | Shared Governance | nessun nuovo stato platform necessario ora |
| 4 | `project_id` hard boundary, zero leakage, fail closed | A0/v2/orchestration coprono route/query/cache/async/deep-link/history | `ALREADY_COVERED` | `INVARIANT` | eTwin A0 | regressione obbligatoria, nessun redesign |
| 5A | Discipline/DomainContract e `NOT_YET_RELEASED` | eTwin v2 + ArchitectureDisciplineContract | `ALREADY_COVERED` | `SPECIFIED` | eTwin + discipline owner | nessun cambio |
| 5B | granularità extra di ScopeContext (`spatial/entity/source/baseline`) | non richiesta dalla release corrente | `NEW_OPEN_REQUIREMENT` | `OPEN` | eTwin | aggiungere solo quando un journey ne dimostra necessità |
| 5C | stato `UNCLASSIFIED` | non presente nel modello corrente | `KEEP_EXPERIMENTAL` | `EXPERIMENTAL` | eTwin | non introdurre come pseudo-disciplina; serve caso reale |
| 6A | SourceVersion immutabile e uso project-scoped | esplicito in eTwin v2 | `ALREADY_COVERED` | `INVARIANT` | CEW source semantics + eTwin scope | A1 |
| 6B | `ProjectSourceBinding` exact Source/SourceVersion, no latest | esplicito in A1 | `ALREADY_COVERED` | `SPECIFIED` | eTwin A1 | nessun cambio |
| 6C | deduplicazione tecnica globale + threat model | non definita | `NEW_OPEN_REQUIREMENT` | `OPEN` | Security + storage architecture | blocca solo un'implementazione che deduplica cross-project |
| 6D | source DOC != entity/property/relation DOC | esplicito | `ALREADY_COVERED` | `INVARIANT` | CEW/domain | nessun cambio |
| 7 | `ProjectScopedReference` e divieto di copia semantica | esplicito nella v2/capability map | `ALREADY_COVERED` | `INVARIANT` | eTwin | nessun cambio |
| 8A | `SpatialReference` / discipline identity / `CrossDisciplineRelation` | esplicito in A3 | `ALREADY_COVERED` | `INVARIANT` | eTwin A3 + discipline owners | nessun cambio |
| 8B | tassonomia/stati completi delle relazioni interdisciplinari | volutamente non definiti | `NEW_OPEN_REQUIREMENT` | `OPEN` | eTwin A3 + Architecture contract | deve emergere dal primo caso Architecture reale |
| 9 | assertion concorrenti, genealogia, supersession | eTwin v2 A4 + documentation governance | `ALREADY_COVERED` | `INVARIANT` | discipline owner / eTwin projection | forma esatta resta `DOMAIN_OWNED` |
| 10A | least-authority, mandato, agent owner/support, no Level-C | agent operating contract + orchestration v2 | `ALREADY_COVERED` | `INVARIANT` | Shared Agent Governance | nessun cambio |
| 10B | schema `AgentExecution` con source versions, assumptions, uncertainties, receipt | copertura parziale tramite admitted inputs/results/receipts | `REFINE_CURRENT_CONTRACT` | `OPEN` fino a prova | Agent Governance | valutare schema execution-level solo per task authority-sensitive |
| 10C | `CURRENT / STALE / UNRECONCILED` per agent freshness | baseline/same-revision esistono, tassonomia runtime agent non esiste | `NEW_OPEN_REQUIREMENT` | `OPEN` | Agent Governance + Security | introdurre solo se freshness non è già garantita da immutable candidate/tool contract |
| 10D | organizzazione agenti per ruolo/capacità/composizione | delivery agents correnti hanno owner/support; user-facing agents non definiti | `KEEP_EXPERIMENTAL` | `EXPERIMENTAL` | future agent capability | non confondere delivery workforce con agenti del prodotto |
| 11 | human authority, independent review, append-only receipts | coperto da governance/Human System/orchestration | `ALREADY_COVERED` | `INVARIANT` | Shared Governance + domain human authority | nessun cambio |
| 12A | separazione runtime/availability/governance states | operating model separa delivery/human/release/promotion/professional; eTwin usa ACTIVE/NOT_YET_RELEASED/TEST_ONLY | `ALREADY_COVERED` | `INVARIANT` | Product Governance | evitare nuovo mega-status |
| 12B | `LOADING / ERROR / UNAVAILABLE` come runtime states | dettaglio UI/runtime non L1 | `KEEP_EXPERIMENTAL` | `EXPERIMENTAL` | capability UI | definire localmente se necessario |
| 12C | `INDEPENDENT_REVIEW_REQUIRED` come stato persistente | concetto coperto, stato universale non necessario | `KEEP_EXPERIMENTAL` | `EXPERIMENTAL` | owning workflow | non creare enum globale senza producer/exit contract |
| 13 | snapshot/read-model/cache non authority, rebuildability | esplicito in eTwin v2 + authority audit | `ALREADY_COVERED` | `INVARIANT` | eTwin/CEW | storico dashboard resta read-only |
| 14 | async context token, out-of-order, deep-link/history/reload fail closed | esplicito A0 e support Security Isolation | `ALREADY_COVERED` | `INVARIANT` | eTwin A0 | test di regressione |
| 15A | task-oriented, professional language, progressive disclosure, not agent/viewer-first | Shared Human System + product agency model | `ALREADY_COVERED` | `INVARIANT` | Human System | tradurre in HVA per capability, non in layout fisso |
| 15B | keyboard/focus/no-colour-only | accessibilità/Human System; A6 esplicita viewer semantics | `REFINE_CURRENT_CONTRACT` | `SPECIFIED` | Human System / A6 | tenere come criterio acceptance trasversale, non come nuova IA |
| 15C | Home/menu/workspace non congelati | coerente con capability/journey-first | `ALREADY_COVERED` | `OPEN` | Product + Human System | decidere per journey, non ora |
| 16 | primitivo operativo professionale (`WorkItem`/`TechnicalActivity`) per lavoro/delega/review/handoff | non presente; il Work hierarchy corrente descrive sviluppo prodotto, non lavoro professionale utente | `NEW_OPEN_REQUIREMENT` | `OPEN` | eTwin future work coordination | futura capability; non espandere A0/A1 per introdurlo |
| 17 | contratto autonomo per nuove discipline, no automatic release | esplicito in A3/ArchitectureDisciplineContract | `ALREADY_COVERED` | `INVARIANT` | eTwin + discipline owner | nessun cambio |
| 18A | technical green != HVA; safety non compensabile | esplicito nella governance v2 | `ALREADY_COVERED` | `INVARIANT` | Shared Human/Release Governance | nessun cambio |
| 18B | matrice red-team concreta a 13 casi | categorie/stop conditions esistono, ma non la matrice prescrittiva completa | `REFINE_CURRENT_CONTRACT` | `SPECIFIED` | QA + Security + Z0 | candidabile come acceptance matrix, senza cambiare L1 ownership |
| 19 | conformance rules contro leakage, false equivalence, auto-promotion | sostanzialmente coperte da invariants + stop conditions | `ALREADY_COVERED` | `INVARIANT` | Governance | nessun cambio |
| 20.1 | modello operativo professionale | gap reale, vedi #16 | `NEW_OPEN_REQUIREMENT` | `OPEN` | future work coordination | non bloccante release corrente |
| 20.2 | information architecture/Home | volutamente journey-driven | `ALREADY_COVERED` | `OPEN` | Human System | non cristallizzare |
| 20.3 | relation taxonomy | gap A3, vedi #8B | `NEW_OPEN_REQUIREMENT` | `OPEN` | A3 | blocca solo la porzione dipendente di A3 |
| 20.4 | ScopeContext oltre minimo | gap condizionale, vedi #5B | `NEW_OPEN_REQUIREMENT` | `OPEN` | eTwin | needs-driven |
| 20.5 | global SourceVersion dedup threat model | gap condizionale, vedi #6C | `NEW_OPEN_REQUIREMENT` | `OPEN` | Security/storage | solo se dedup cross-project |
| 20.6 | agent organization | non serve per delivery agents correnti | `KEEP_EXPERIMENTAL` | `EXPERIMENTAL` | future product agents | nessun blocco A0-Z0 |
| 20.7 | tecnologia persistenza/deployment eTwin | provider non è authority; runtime corrente CEW non determina tutta eTwin | `NEW_OPEN_REQUIREMENT` | `OPEN` | Operations | decidere per capability/risk, non L1 semantico |
| 20.8 | handoff/consegne | non capability della release A0-A6 | `NEW_OPEN_REQUIREMENT` | `OPEN` | future work coordination | backlog futuro |
| 20.9 | confine reference/read-model | principi già chiusi; dettagli implementativi localizzati | `ALREADY_COVERED` | `INVARIANT` | eTwin/CEW | nessuna nuova authority |
| 20.10 | prima verticale Architecture | già A3 | `ALREADY_COVERED` | `SPECIFIED` | eTwin A3 + Architecture | nessun cambio |
| 21 | genealogia ETW storico come experimental input | ora formalizzata da SP-0 | `ALREADY_COVERED` | `DOMAIN_OWNED/EXPERIMENTAL` | Audit/Governance | nessun cambio L1 |
| 22A | fingerprint di review | same-revision e receipt identity già richiesti | `ALREADY_COVERED` | `INVARIANT` | Release Governance | nessun cambio |
| 22B | invalidazione mirata della conoscenza non impattata | compatible con history preservation, ma non può sostituire same-revision promotion evidence | `REFINE_CURRENT_CONTRACT` | `SPECIFIED` | Documentation/Release Governance | utile come regola di riuso analitico; promotion resta same-revision salvo equivalenza esplicita |
| 23 | `Persona × Role × Task × Authority × Scope` prima di canonizzare il modello di lavoro | capability/journey/human research esistono, matrice specifica no | `REFINE_CURRENT_CONTRACT` | `OPEN` | Human System + future work coordination | criterio discovery per #3/#16; non amplia A0 già definita |
| 24 | vecchi `STATO_RIPRESA/REGISTRO_MASTER/PROTOCOLLO` come fonti platform | manifest corrente assegna N12 authority a `knowledge/CURRENT_STATE.json` + canonici governati | `REJECT_DUPLICATION` per platform authority; `DOMAIN_OWNED_REFERENCE` come storia/engineering | `DOMAIN_OWNED` | N12 | usare la current authority dichiarata dal manifest |

## 3. Delta candidati all'ammissione controllata

SP-1 identifica **quattro famiglie** che aggiungono valore senza creare un nuovo programma:

### D1 — Flessibilità governata dei requisiti

Già persistita come proposta `ETWIN-SPEC-001`. È una convenzione di annotazione subordinata a L0–L7.

**Azione SP-2:** valutare registrazione nel Product Decision Register e un riferimento nel Documentation Authority Model o nel programma eTwin, senza duplicare L1.

### D2 — Discovery per future capability di lavoro/collaborazione

Comprende `Person/Role/Capability/Authority/Scope`, `ProjectRoleAssignment`, `ActiveRoleContext`, primitivo operativo professionale, delega/collaborazione/handoff.

**Azione SP-2:** non implementare ora. Registrare come future capability discovery, con gate `Persona × Role × Task × Authority × Scope`; non blocca A0→Z0 corrente.

### D3 — Delta condizionali di sicurezza/semantica

Comprende:

- relation taxonomy A3;
- ScopeContext extra-granularity;
- global dedup threat model;
- agent freshness semantics.

**Azione SP-2:** legare ogni delta all'esatto slice/caso che lo rende necessario. Nessun enum/schema preventivo globale.

### D4 — Acceptance hardening

Comprende matrice red-team prescrittiva e regola di invalidazione mirata della conoscenza, mantenendo intatta la same-revision rule per promotion.

**Azione SP-2:** tradurre in acceptance/audit contracts e validator dove applicabile, preferibilmente Z0/shared QA invece di gonfiare il L1.

## 4. Artefatti storici: decisione di riuso

### `model/etwin/*`

- rendering/document mapping/registration possono essere riusati come **tool CEW/domain** se conformi ai source/evidence contract correnti;
- `Claim`, `StructuralEntity`, `EvidenceStatus`, `PropertyResolution` locali non vengono promossi a primitive eTwin.

### dashboard/read-model

- riuso possibile per pattern di visualizzazione e diagnostica;
- `VALIDATED`, `canonical`, KnowledgeGraph e altri nomi non trasferiscono authority;
- qualsiasi nuova UI deve leggere proiezioni governate e mantenere `READ_MODEL_ONLY`.

### vecchi workflow ETW

- possono restare strumenti N12/analisi;
- un PASS di tali workflow non soddisfa gate di promozione eTwin v2 se non esplicitamente ammesso dal gate corrente.

## 5. Gate SP1-G

| Criterio | Esito |
|---|---|
| Tutti i blocchi materiali della discovery classificati | PASS |
| Nessuna authority CEW/N12 ricreata come eTwin-owned | PASS |
| Delta `OPEN` con owner e condizione d'uso | PASS |
| Esperimenti non-promotivi | PASS |
| Unico L1 eTwin corrente preservato | PASS |
| A0/A1 sequence invariata | PASS |
| Delta ammessi automaticamente | NONE |

**Esito:** `SP1-G — PASS_WITH_OPEN_ITEMS`.

Gli open item sono intenzionali e localizzati. Non bloccano il programma corrente salvo il slice che in futuro dipende direttamente da essi.

**Next admissible work:** SP-2 deve ammettere solo D1 e le parti non invasive di D4; D2/D3 restano backlog/open finché un journey o slice corrente non li rende necessari.