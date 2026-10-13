# CEW-GATE-AUTHORITY-01 — Trusted Qualification Control Plane

**Data:** 13 ottobre 2026  
**Stato:** design approvato in chat; specifica scritta in revisione umana  
**Repository:** `antoniocorsano-boop/N12`  
**Origine:** audit architetturale della PR #147 e dei round successivi di hardening CEW-CONTRACT-01  
**Ambito:** separazione definitiva fra autorità del gate e qualification payload, senza introdurre nuovi dati ingegneristici e senza anticipare CEW-FEM-01.

---

## 1. Decisione architetturale

CEW-GATE-AUTHORITY-01 introduce un **trusted qualification control plane** separato dal contenuto che deve essere qualificato.

La decisione fondamentale è:

> una qualification PR non può modificare, sostituire o reinterpretare il programma che decide se quella stessa PR è qualificata.

Il modello di fiducia diventa:

`Trusted Gate Core G + Trusted Authority A + Candidate H + Operational Authority O → Qualification Receipt R`

con:

- **G — Gate Core:** versione identificata e già qualificata del motore di verifica;
- **A — Frozen Qualification Authority:** profilo trusted che definisce le autorità e gli invarianti applicabili alla qualifica;
- **H — Candidate Head:** exact head della PR da qualificare, trattato esclusivamente come dato non fidato;
- **O — Operational Authority:** commit ingegneristico congelato da cui provengono builder, input e fonti operative immutabili;
- **R — Qualification Receipt:** risultato machine-readable della verifica, legato a G/A/H/O e, quando disponibile, attestato crittograficamente.

Il Candidate H può dichiarare evidenze e manifest, ma non può modificare G o A durante la propria valutazione.

---

## 2. Problema che questa specifica risolve

La stabilizzazione CEW-CONTRACT-01 aveva già congelato invarianti, mutation suite, replay deterministico e finding-triage policy. Tuttavia l'implementazione continuava a verificare la non-bypassabilità del workflow interpretando direttamente YAML/GitHub Actions tramite parser repository-native parziali.

Questo ha prodotto una sequenza di finding semanticamente equivalenti:

- step opzionale;
- chiave YAML quotata;
- condizione a livello job;
- shell alternativa;
- fallback shell;
- `working-directory` diretto o ereditato;
- indentazione YAML valida non standard.

Questi finding non indicano che I02 sia sbagliato. Indicano che è sbagliato tentare di dimostrare I02 enumerando tutte le possibili forme sintattiche di un linguaggio esterno e modificabile dalla stessa PR.

Il problema sistemico è quindi doppio:

1. **semantic surface non finita:** il gate tenta di modellare parzialmente GitHub Actions;
2. **self-validation:** la stessa PR può modificare workflow, parser, validator e test che la giudicano.

CEW-GATE-AUTHORITY-01 elimina entrambe le cause invece di aggiungere un altro round di regressioni.

---

## 3. Obiettivi

La soluzione deve garantire che:

1. la qualification sia valutata da un Gate Core già trusted;
2. il Candidate H non possa eseguire codice nel control plane;
3. G, A, H e O abbiano identità esplicite e verificabili;
4. il Candidate sia letto soltanto come insieme di oggetti Git/dati;
5. il replay ModelGeneration continui a usare esclusivamente O;
6. il risultato R sia riproducibile, machine-readable e attribuibile a G/A/H/O;
7. un difetto futuro del Gate Core produca una nuova versione G+1, non una catena indefinita di patch alla qualification corrente;
8. CEW-CONTRACT-01 resti separato da CEW-FEM-01;
9. il sistema resti utilizzabile con il repository N12 pubblico e con una toolchain a costo zero;
10. le protezioni GitHub disponibili vengano usate come difesa aggiuntiva, non come unica autorità CEW.

---

## 4. Non-obiettivi

CEW-GATE-AUTHORITY-01 non autorizza:

- scelta di solver;
- esecuzione di analisi strutturali N12;
- creazione di `SolverRun` o `Result`;
- introduzione di materiali, carichi, vincoli o parametri geotecnici mancanti;
- modifica della geometria canonica;
- promozione epistemica di dati ND/INF/WATCH;
- migrazione obbligatoria del repository verso una organization;
- creazione immediata di un repository separato per il Gate Core;
- riscrittura retroattiva della storia della PR #147.

---

## 5. Terminologia e autorità

### 5.1 Gate Core — G

G è il programma che applica le regole CEW di qualifica. Deve essere identificato almeno da:

- repository;
- commit SHA completo;
- digest dei file eseguibili rilevanti o manifest di build;
- versione logica del Gate Core;
- set di invarianti che dichiara di implementare;
- qualification receipt propria.

Una qualification non può selezionare arbitrariamente la propria versione G.

### 5.2 Frozen Qualification Authority — A

A contiene i valori trusted contro cui il Candidate viene verificato.

Per il pilot N12 comprende almeno:

- operational commit O;
- canonical snapshot identity;
- builder path + Git blob identity;
- insieme esatto degli input ModelGeneration;
- digest attesi;
- registration source identity;
- supporti congelati;
- output identity/digest/size/timestamp storico;
- authority flags che devono restare false;
- definizione degli invarianti CEW-CONTRACT-01 applicabili;
- riferimenti alle evidenze che devono essere presenti nel Candidate.

A non può essere modificata dalla stessa qualification PR che viene valutata.

### 5.3 Candidate Head — H

H è il commit SHA completo dell'exact PR head.

H è sempre considerato **untrusted input**, anche quando la PR proviene dal proprietario del repository.

### 5.4 Operational Authority — O

Per la qualification N12 corrente:

`O = d806dcca72779b5a186defe557a7a9b739575a90`

O è la sorgente immutabile da cui il Gate Core materializza il builder storico, i sei input autorizzati e la registration source.

### 5.5 Qualification Receipt — R

R è il prodotto della decisione di G. Deve legare in modo esplicito:

- G;
- A;
- H;
- O;
- bundle candidate osservato;
- replay output;
- esiti degli invarianti;
- decisione finale.

---

## 6. Trust model

### 6.1 Trusted

Sono trusted soltanto:

- il workflow del control plane proveniente dalla base trusted;
- Gate Core G già qualificato;
- Frozen Authority A già promossa nel control plane;
- gli oggetti Git del commit O identificati tramite SHA completo;
- l'infrastruttura GitHub/Sigstore usata per esecuzione e attestazione, entro il threat model dichiarato.

### 6.2 Untrusted

Sono sempre untrusted:

- tutto ciò che proviene da H;
- manifest, JSON, CSV e Markdown candidate;
- file workflow presenti in H;
- script Python/shell presenti in H;
- package manifest presenti in H;
- symlink/gitlink/submodule dichiarati da H;
- path, glob, URI o riferimenti dichiarati da H;
- nomi di file e metadata testuali provenienti da H.

### 6.3 Regola centrale

> Il trusted control plane può **leggere** H, ma non può **eseguire** H.

Questa regola vale anche indirettamente: non devono essere eseguiti tool che caricano automaticamente configurazioni, plugin, hook o dipendenze provenienti dal working tree candidate.

---

## 7. Threat model

CEW-GATE-AUTHORITY-01 deve resistere almeno alle seguenti classi di errore o mutazione candidate.

### T01 — Control-plane replacement

H tenta di cambiare il workflow o il Gate Core che lo giudica.

**Difesa:** il workflow e G provengono dalla base trusted/versione G selezionata fuori da H.

### T02 — Candidate code execution

H inserisce Python, shell, Makefile, package script, action locale o configurazione capace di eseguire codice.

**Difesa:** nessun eseguibile H viene importato, invocato o usato come action; H è letto come blob/dati.

### T03 — Path confusion/traversal

H dichiara path assoluti, `..`, path Unicode ambigui, symlink o gitlink per uscire dalla superficie autorizzata.

**Difesa:** allowlist di path normalizzati e verifica del tipo Git object; symlink e gitlink sono rifiutati nelle superfici qualificate salvo futura specifica esplicita.

### T04 — Parser/resource abuse

H fornisce JSON/CSV/Markdown eccessivamente grandi o strutture patologiche.

**Difesa:** limiti di byte, righe, profondità e numero di record; parsing fail-closed.

### T05 — Authority substitution

H tenta di sostituire O, builder, input, fonte registration o snapshot.

**Difesa:** A è trusted e G confronta H/O con A.

### T06 — Receipt confusion/replay

Una receipt valida per un altro G/A/H/O viene riutilizzata.

**Difesa:** R incorpora tutti e quattro gli identificatori, bundle digest e versione dello schema; la verifica richiede match esatto.

### T07 — Gate Core defect

G contiene un bug logico.

**Difesa:** ciclo di vita G → G+1, assurance separata del Gate Core, corpus di regressione e riqualifica solo delle qualification materialmente interessate.

### T08 — GitHub workflow misconfiguration

Il workflow trusted acquisisce permessi eccessivi o introduce condizioni pericolose.

**Difesa:** workflow minimale, pin delle action, `actionlint`, `zizmor`, CodeQL quando applicabile, review indipendente e ruleset/policy repository.

### T09 — Attestation misuse

Il job che attesta viene influenzato da contenuto non trusted o può attestare un risultato non prodotto dal Gate Core.

**Difesa:** separazione dei job; il job di attestazione consuma soltanto la receipt verificata/digestata prodotta dal job read-only e non esegue né rilegge il Candidate.

---

## 8. Architettura logica

La soluzione è composta da sette componenti.

### 8.1 Trusted Trigger Workflow

Responsabilità:

- ricevere l'evento autorizzato;
- determinare H;
- selezionare G e A trusted;
- invocare il Gate Core;
- propagare fail-closed l'exit code;
- passare la receipt al job di attestazione solo in caso di PASS.

Non contiene logica CEW sostanziale.

### 8.2 Candidate Object Reader

Responsabilità:

- acquisire oggetti Git appartenenti esattamente a H;
- esporre soltanto una API di lettura blob;
- verificare path/type/size;
- non creare un ambiente eseguibile del candidate.

Implementazione preferita:

- Git object access/bare repository isolato, oppure API GitHub per blob/trees;
- nessun `checkout` del Candidate come working directory operativa del Gate Core.

La scelta precisa fra bare Git e Git object API è demandata al piano di implementazione; entrambe devono rispettare la stessa interfaccia `CandidateReader`.

### 8.3 Gate Core G

Responsabilità:

- validare schema e semantica del qualification payload;
- applicare gli invarianti;
- orchestrare la materializzazione di O;
- orchestrare replay e confronti;
- produrre R.

G non interpreta il workflow candidate e non contiene un parser GitHub Actions usato come trust boundary.

### 8.4 Frozen Authority A

Responsabilità:

- rendere espliciti i valori trusted;
- definire la superficie candidate ammessa;
- definire gli invarianti applicabili;
- definire le authority boundary CEW-CONTRACT/FEM.

### 8.5 Operational Materializer

Responsabilità:

- materializzare builder/input/source da O;
- verificare Git blob SHA e SHA-256;
- fornire input isolati al replay.

Non legge builder o input equivalenti da H.

### 8.6 Qualification Engine

Responsabilità:

- confrontare Candidate, A e replay;
- verificare provenance, epistemic guards, gate matrix, receipt candidate ed evidenze;
- produrre esiti strutturati per invariante.

### 8.7 Receipt + Attestation Publisher

Responsabilità:

- serializzare R in modo canonico;
- calcolarne SHA-256;
- creare, se la piattaforma/policy è disponibile, un'attestazione GitHub/Sigstore sul subject digest di R o del qualification bundle;
- non decidere autonomamente PASS/FAIL.

---

## 9. Event model GitHub

### 9.1 Preferred mode — `pull_request_target`

Per un repository pubblico, `pull_request_target` ha la proprietà desiderata: il workflow viene preso dal contesto base/trusted invece che dal contenuto H.

Questa modalità è autorizzata soltanto se:

1. esiste una Actions event policy applicabile che consente esplicitamente il workflow/evento desiderato;
2. il workflow non esegue codice proveniente da H;
3. il job di verifica non dispone di secret;
4. i permessi del job di verifica sono minimi;
5. le action terze sono pin a full commit SHA;
6. la configurazione viene verificata prima dell'attivazione.

Vincolo temporale di piattaforma verificato: GitHub ha annunciato l'enforcement della policy predefinita che blocca `pull_request_target` nei repository pubblici dal **2 novembre 2026** in assenza di policy applicabile. La configurazione N12 deve quindi essere verificata esplicitamente in fase di deployment.

### 9.2 Safe fallback — trusted `workflow_dispatch`

Se la policy `pull_request_target` non è configurabile o non è approvata, il Gate Authority deve poter operare tramite `workflow_dispatch` trusted con:

- H passato come SHA completo;
- verifica che H appartenga alla PR candidata prevista;
- attore autorizzato dalla Actions policy;
- stessi vincoli no-exec e stessi permessi minimi.

Il fallback non modifica la semantica della qualification; cambia soltanto il trigger.

### 9.3 Event policy come prerequisito deployment

La presenza/configurazione reale delle Actions Policies del repository non è assunta. Deve essere verificata prima dell'attivazione del control plane.

---

## 10. Permission model

### 10.1 Job `qualify`

Permessi massimi previsti:

- `contents: read`;
- nessun `id-token: write`;
- nessun `attestations: write`;
- nessun `pull-requests: write`;
- nessun secret applicativo.

Il job legge H e O, esegue G e produce una receipt temporanea.

### 10.2 Job `attest`

Eseguito soltanto se `qualify` è PASS.

Permessi minimi previsti:

- `id-token: write`;
- `attestations: write`;
- eventuale `contents: read` solo se strettamente richiesto dall'action di attestazione.

Il job `attest`:

- non checkouta H;
- non interpreta file di H;
- riceve soltanto la receipt/digest prodotto dal job precedente;
- verifica nuovamente il digest della receipt prima dell'attestazione.

---

## 11. Candidate-as-data protocol

Il CandidateReader espone una superficie chiusa.

### 11.1 Path allowlist

A definisce i path candidate autorizzati per la qualification. Qualunque path fuori allowlist è ignorato o, se dichiarato come parte del qualification bundle, causa FAIL.

### 11.2 Object types

Per la superficie qualificata sono accettati soltanto blob regolari.

Sono rifiutati:

- symlink;
- gitlink/submodule;
- path che risolvono fuori dalla root logica;
- path assoluti;
- componenti `..`;
- duplicazioni dopo normalizzazione.

### 11.3 Content constraints

Ogni tipo dati ha limiti dichiarati:

- JSON: dimensione massima + profondità massima + schema chiuso dove necessario;
- CSV: dimensione massima + numero righe + colonne attese;
- Markdown/evidence: dimensione massima e trattamento testuale non eseguibile.

I valori esatti dei limiti saranno definiti nel piano, scegliendo soglie superiori al corpus N12 reale ma finite.

### 11.4 No-exec invariant

È vietato:

- importare moduli Python da H;
- eseguire script H;
- eseguire action locali H;
- eseguire hook Git H;
- installare dipendenze descritte da H;
- valutare template o comandi provenienti da H;
- utilizzare H come working directory di tool che eseguono discovery automatica di plugin/config eseguibile.

---

## 12. Frozen Authority bootstrap

A non deve nascere dentro la qualification PR che dovrà essere giudicata.

La migrazione avviene quindi in due tempi.

### Bootstrap A0

Un piccolo PR dedicato promuove nel trusted control plane:

- l'autorità N12 già verificata;
- i valori derivati da O;
- l'identità dell'output storico;
- i supporti registration congelati;
- gli invarianti CEW-CONTRACT-01;
- la authority boundary CEW-FEM.

A0 non introduce dati nuovi: ricopia in forma machine-checkable fatti già verificati, con confronto indipendente contro O e l'audit trail #147.

### Qualification successiva

Solo dopo il merge umano di A0, una qualification PR può essere giudicata rispetto ad A0.

---

## 13. Qualification Receipt schema

R deve includere almeno:

```text
schema_id
schema_version
qualified_at
gate_core:
  repository
  commit_sha
  version
authority:
  authority_id
  authority_sha256
candidate:
  repository
  pr_number
  head_sha
  qualification_bundle_sha256
operational_authority:
  commit_sha
replay:
  output_identity
  output_sha256
  output_size_bytes
  historical_generated_at
invariants:
  I01..I17 -> PASS|FAIL|NOT_APPLICABLE
failure_codes: []
authority_boundary:
  solver_authorized=false
  calculation_model_ready=false
  synthetic_solver_result=false
  solver_run=false
  result_entity_created=false
cew_fem_01_required=true
qualified=true|false
```

`qualified=true` è valido soltanto se nessun invariant applicabile è FAIL e la authority boundary è intatta.

La serializzazione deve essere deterministica/canonicalizzabile per produrre un digest stabile.

---

## 14. Qualification Attestation

Per repository pubblici, GitHub Artifact Attestations usa Sigstore e registra provenance verificabile; la piattaforma associa l'attestazione a workflow, repository, commit, evento e identità OIDC.

CEW usa questa capacità come **strato aggiuntivo di attestazione**, non come sostituto della receipt.

### Subject

Subject preferito:

- SHA-256 della Qualification Receipt canonica, oppure
- SHA-256 di un qualification bundle deterministico contenente receipt + evidence index.

### Predicate CEW

Il predicate CEW deve contenere almeno:

- `gate_core_sha`;
- `authority_sha256`;
- `candidate_head_sha`;
- `operational_commit_sha`;
- `qualification_bundle_sha256`;
- `replay_output_sha256`;
- `qualified`;
- versione schema CEW Gate Authority.

La verifica futura deve controllare sia la firma/provenance GitHub sia il contenuto CEW del predicate.

---

## 15. Nuova formulazione di I02

La precedente I02 cercava di rendere non bypassabile ogni step del workflow attraverso parsing repository-native della sintassi GitHub Actions.

La nuova formulazione è:

> **I02 — Trusted Gate Invocation.** La decisione di qualification deve essere prodotta esclusivamente da un Gate Core G identificato e trusted, invocato da un control plane non modificabile dal Candidate H. H non può cambiare G/A né introdurre codice eseguito dal control plane. L'exit status e la receipt di G devono propagarsi fail-closed.

I02 si dimostra tramite proprietà architetturali finite:

1. identity di G;
2. identity di H;
3. identity di A;
4. no-exec H;
5. separation dei job/permission;
6. fail-closed propagation;
7. receipt binding G/A/H/O.

Non richiede più di modellare tutte le forme sintattiche equivalenti di GitHub Actions.

---

## 16. Conservazione degli invarianti CEW-CONTRACT-01

Gli invarianti sostanziali restano invariati:

- exact candidate head;
- operational authority identity;
- exact input set;
- byte integrity;
- builder identity;
- canonical snapshot identity;
- durable replay;
- output integrity;
- manifest/verification/receipt coherence;
- registration provenance;
- exact registration examples;
- epistemic guards;
- gate matrix integrity;
- evidence existence;
- authority boundary;
- CEW-FEM separation.

Soltanto l'invariante di non-bypassabilità viene rifondato sul trust boundary invece che sul parsing sintattico del workflow candidate.

---

## 17. Gate Core lifecycle

### 17.1 G0 bootstrap

La prima versione del Gate Core viene introdotta con PR dedicata, separata dalla qualification payload.

### 17.2 Qualification di G

Ogni nuova versione G deve superare:

- unit test;
- property-based test sul parsing dati;
- mutation/adversarial corpus;
- integration test del control plane;
- no-exec test;
- replay test;
- `actionlint` sul workflow;
- `zizmor` sul workflow;
- CodeQL/security checks disponibili;
- review indipendente exact-head.

### 17.3 G → G+1

Un finding futuro nel Gate Core produce una nuova versione G+1.

Non riapre automaticamente tutte le qualification precedenti.

È richiesto impact analysis:

- quale invariant è affetto;
- quali candidate/receipt potrebbero essere state erroneamente qualificate;
- se il difetto è reachable sui dati della specifica qualification;
- se serve requalification.

Solo qualification materialmente interessate vengono riaperte.

---

## 18. Testing strategy

### 18.1 Gate Core unit tests

Test per ogni funzione pura/schema/invariant.

### 18.2 Property-based tests

Applicati ai dati candidate, non alla grammatica GitHub Actions.

Categorie:

- campi mancanti;
- tipi errati;
- liste duplicate;
- permutazioni;
- valori boundary;
- path patologici;
- dati UTF-8/Unicode ambigui;
- strutture annidate;
- dimensioni oltre soglia;
- inconsistenze Manifest/Receipt/Authority.

### 18.3 Adversarial corpus

Corpus stabile per regressioni reali scoperte nelle review #147, riclassificate per invariant invece che per “round”.

Le regressioni puramente legate alla sintassi YAML della qualification workflow non appartengono al Candidate corpus, perché il Candidate non controlla più il workflow trusted.

### 18.4 Integration tests

Devono dimostrare almeno:

- candidate valido → PASS;
- candidate altera G nel proprio branch → nessun effetto sulla decisione;
- candidate altera A nel proprio branch → nessun effetto sulla trusted A;
- candidate aggiunge script malevolo → non eseguito;
- candidate prova symlink/gitlink → FAIL;
- candidate cambia exact head durante una run → receipt legata allo SHA iniziale, nessuna ambiguità;
- replay O → output storico esatto;
- receipt G/A/H/O mismatch → FAIL;
- authority boundary CEW-FEM violata → FAIL.

---

## 19. Workflow assurance tools

Il control plane non deve implementare un parser GitHub Actions alternativo.

Quando cambia il workflow trusted vengono usati strumenti esterni specifici:

- **actionlint** per sintassi/espressioni/semantica statica GitHub Actions;
- **zizmor** per security audit dei workflow;
- **CodeQL** / code scanning disponibile per il repository pubblico;
- pin a SHA completi delle action usate.

Questi strumenti qualificano il control plane, non decidono la semantica CEW del Candidate.

---

## 20. Repository governance

### 20.1 Stato attuale verificato

Al momento della specifica:

- N12 è pubblico;
- `main` non risulta protetto;
- il repository non espone ruleset attivi.

### 20.2 Target minimo

Per `main` deve essere progettato un repository-level ruleset compatibile con repository pubblico GitHub Free che includa, salvo limitazioni di account verificate in fase di implementazione:

- pull request obbligatoria;
- blocco force-push;
- blocco deletion;
- required status check del bootstrap/control-plane dove utile;
- bypass ridotto e documentato.

### 20.3 Required workflows

Non sono prerequisito di CEW-GATE-AUTHORITY-01. GitHub documenta i required workflows nei ruleset a livello organization/enterprise; N12 è attualmente user-owned. La soluzione deve funzionare senza migrazione organizzativa.

---

## 21. Actions policy

Il deployment preferito tramite `pull_request_target` è subordinato a una event policy esplicita.

Prima dell'attivazione deve essere verificato in Settings:

1. se la nuova Actions Policy è disponibile sull'account/repository;
2. quale policy si applicherebbe a `pull_request_target`;
3. che il workflow CEW Gate Authority sia autorizzato;
4. che attori/eventi non necessari restino negati;
5. che la configurazione non allarghi genericamente l'esecuzione di workflow privilegiati.

In assenza di esito positivo si usa il fallback `workflow_dispatch` trusted.

---

## 22. Migrazione dalla PR #147

### Fase M0 — Freeze

La PR #147 viene congelata al suo audit trail finale. Non vengono aggiunti ulteriori round di parser hardening.

### Fase M1 — Gate Authority bootstrap

Nuova PR piccola da `main` contenente esclusivamente:

- presente specifica;
- Gate Core G0;
- Trusted Trigger Workflow;
- A0 Frozen Authority;
- test del control plane;
- configurazione/documentazione di assurance.

Nessuna nuova proprietà ingegneristica N12.

### Fase M2 — Qualifica del Gate Core

G0 viene qualificato tramite il proprio assurance package e review indipendente.

### Fase M3 — Qualification payload pulito

Nuova PR candidate contiene soltanto il qualification payload necessario CEW-CONTRACT-01, non il giudice che lo valuta.

### Fase M4 — Attested Receipt

Il trusted Gate Core produce R per H e la relativa attestation.

### Fase M5 — Retire #147

Dopo che la nuova qualification è chiusa e verificata, #147 può essere chiusa come `superseded`, preservando integralmente discussioni e audit trail.

Nessuna chiusura automatica è autorizzata.

---

## 23. Failure handling

### Gate Core unavailable

Nessuna qualification viene concessa. Stato: `BLOCKED_CONTROL_PLANE`.

### Actions policy blocks trigger

Nessun fallback implicito. Si usa soltanto il trigger trusted alternativo approvato.

### Candidate read failure

FAIL closed con failure code stabile.

### Replay failure

FAIL; nessuna receipt `qualified=true`.

### Attestation service unavailable dopo PASS

La receipt può essere prodotta ma lo stato finale resta `QUALIFIED_NOT_ATTESTED` o equivalente; la promotion finale richiede decisione/policy esplicita. Non si finge un'attestazione avvenuta.

### New Gate Core finding

Si apre Gate Core G+1 e si effettua impact analysis; nessuna riapertura massiva automatica.

---

## 24. Criterio di arresto della qualification

Una qualification CEW-CONTRACT-01 può essere dichiarata chiusa quando, sullo stesso H:

1. G è una versione trusted già qualificata;
2. A è trusted e immutata rispetto alla run;
3. H è l'exact candidate head;
4. O è l'operational commit autorizzato;
5. H non è stato eseguito come codice;
6. il qualification bundle digest è registrato;
7. replay deterministico PASS;
8. tutti gli invarianti applicabili PASS;
9. authority boundary CEW-FEM intatta;
10. R lega esattamente G/A/H/O;
11. il trusted workflow completa con successo;
12. l'attestation è presente se richiesta dalla policy di promotion;
13. non esistono finding aperti che dimostrino una decisione errata di G su quello specifico H.

Dopo questo punto, un finding su G è gestito tramite il lifecycle G → G+1 e impact analysis.

Questo è il meccanismo che rende finita la closure.

---

## 25. Promotion policy

La qualification e la promotion sono due decisioni distinte.

- **Qualification:** G stabilisce che H soddisfa A.
- **Promotion/merge:** resta una decisione umana/governance GitHub.

CEW-GATE-AUTHORITY-01 non autorizza auto-merge.

---

## 26. Evidenze minime del Gate Authority

Il Gate Core bootstrap deve produrre almeno:

- design spec approvata;
- threat model;
- Gate Core source identity;
- A0 identity/digest;
- workflow identity;
- test report;
- actionlint report;
- zizmor report;
- code scanning report disponibile;
- adversarial corpus report;
- integration report;
- sample PASS receipt;
- sample FAIL receipt;
- attestation verification evidence, se attivata;
- human review decision.

---

## 27. Decisioni irrevocabili e reversibili

### Reversibili

- bare Git vs Git object API;
- formato esatto interno del CandidateReader;
- libreria Python per schema/property testing;
- soglie quantitative di size limit, purché finite e documentate;
- naming dei failure code;
- trigger `pull_request_target` vs trusted `workflow_dispatch`.

### Da governare con particolare cautela

- promozione di A0 a trusted authority;
- prima versione G0 qualificata;
- ruleset/policy GitHub applicati a `main`;
- schema/versione delle Qualification Receipt;
- policy che rende obbligatoria l'attestation per promotion.

---

## 28. Precondizioni prima dell'implementazione

Prima di scrivere il piano operativo devono essere considerate approvate/verificate:

1. questa specifica;
2. decisione di mantenere #147 congelata;
3. nessun nuovo round di parser hardening su #147;
4. disponibilità reale o fallback per Actions Policies;
5. repository-level ruleset target compatibile con l'account;
6. possibilità di usare GitHub Artifact Attestations nel repository pubblico;
7. authority A0 derivabile senza introdurre nuovi dati tecnici;
8. nessuna implementazione CEW-FEM inclusa.

---

## 29. Acceptance criteria della prima implementazione

La prima implementazione CEW-GATE-AUTHORITY-01 è accettabile solo se dimostra, con evidenza fresh:

- una PR candidate che modifica il proprio workflow non modifica il workflow trusted effettivamente eseguito;
- una PR candidate che modifica una copia di A non modifica A trusted;
- nessuno script candidate viene eseguito;
- G/A/H/O sono tutti registrati in R;
- una mutazione di ciascuna identità produce FAIL;
- una mutazione di authority boundary produce FAIL;
- O produce lo stesso replay output storico previsto;
- una receipt viene verificata indipendentemente;
- l'event policy/ruleset effettivi sono documentati;
- actionlint/zizmor non producono blocker aperti;
- review indipendente del Gate Core non dimostra false-positive contro il threat model;
- nessun auto-merge è attivo.

---

## 30. Riferimenti piattaforma verificati

Vincoli di piattaforma usati in questa progettazione, verificati sulla documentazione ufficiale GitHub al 13 ottobre 2026:

- `pull_request_target` nei repository pubblici è soggetto a una default policy di blocco; GitHub indica enforcement dal 2 novembre 2026 in assenza di policy applicabile;
- Actions Policies permettono regole per eventi e attori;
- Artifact Attestations usano Sigstore; per repository pubblici la provenance è registrata anche in transparency log pubblico;
- repository-level rulesets sono disponibili sui repository pubblici con GitHub Free;
- i ruleset “Require workflows to pass before merging” sono documentati a livello organization/enterprise e non vengono assunti come disponibili nel repository user-owned N12.

La configurazione specifica dell'account/repository deve essere verificata al deployment e prevale sulle assunzioni di progetto.

---

## 31. Esito atteso

CEW-GATE-AUTHORITY-01 è riuscito quando la qualification non è più un sistema che prova a dimostrare la propria incorrompibilità interpretando sé stesso.

Il risultato atteso è:

> un Candidate H non fidato viene valutato come dato da un Gate Core G già trusted, rispetto a una Authority A già trusted e a una Operational Authority O immutabile; la decisione è registrata in una Receipt R legata a G/A/H/O e, quando previsto, attestata. Un difetto futuro del giudice produce una nuova versione del giudice e una impact analysis, non una sequenza indefinita di patch alla qualification corrente.

Questa architettura costituisce il nuovo punto di riferimento per superare la fase di stabilizzazione CEW-CONTRACT-01 e riprendere la catena canonica CEW senza consumare lavoro in hardening sintattico non finito.