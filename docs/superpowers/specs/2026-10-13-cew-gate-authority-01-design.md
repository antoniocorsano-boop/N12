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

`Trusted Control Plane B + Gate Core G + Frozen Authority A + Candidate H + Operational Authority O → Qualification Receipt R`

con:

- **B — Control Plane Base:** commit trusted della base/default branch da cui proviene il workflow che invoca G;
- **G — Gate Core:** versione identificata e già qualificata del motore di verifica;
- **A — Frozen Qualification Authority:** profilo trusted che definisce autorità e invarianti applicabili;
- **H — Candidate Head:** exact head della PR da qualificare, trattato esclusivamente come dato non fidato;
- **O — Operational Authority:** commit ingegneristico congelato da cui provengono builder, input e fonti operative immutabili;
- **R — Qualification Receipt:** risultato machine-readable della verifica, legato a B/G/A/H/O e, quando previsto, attestato crittograficamente.

Il Candidate H può dichiarare evidenze e manifest, ma non può modificare B, G o A durante la propria valutazione.

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
3. B, G, A, H e O abbiano identità esplicite e verificabili;
4. il Candidate sia letto soltanto come insieme di oggetti Git/dati;
5. il replay ModelGeneration continui a usare esclusivamente O;
6. il risultato R sia riproducibile, machine-readable e attribuibile a B/G/A/H/O;
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
- riscrittura retroattiva della storia della PR #147;
- auto-merge.

---

## 5. Terminologia e autorità

### 5.1 Control Plane Base — B

B è il commit trusted della base/default branch che fornisce il workflow e seleziona G e A.

B viene registrato in R perché una run `pull_request_target` opera nel contesto della base e non del Candidate.

### 5.2 Gate Core — G

G è il programma che applica le regole CEW di qualification. Deve essere identificato almeno da:

- repository;
- commit SHA completo;
- digest dei file eseguibili rilevanti o manifest di build;
- versione logica;
- set di invarianti implementati;
- qualification receipt propria.

Una qualification non può selezionare arbitrariamente la propria versione G.

### 5.3 Frozen Qualification Authority — A

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

### 5.4 Candidate Head — H

H è identificato almeno da:

- base repository;
- PR number;
- head repository;
- exact head commit SHA completo.

H è sempre considerato **untrusted input**, anche quando la PR proviene dal proprietario del repository.

### 5.5 Operational Authority — O

Per la qualification N12 corrente:

`O = d806dcca72779b5a186defe557a7a9b739575a90`

O è la sorgente immutabile da cui il Gate Core materializza il builder storico, i sei input autorizzati e la registration source.

### 5.6 Qualification Receipt — R

R è il prodotto della decisione di G. Deve legare in modo esplicito:

- B;
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

- il workflow proveniente da B;
- Gate Core G già qualificato;
- Frozen Authority A già promossa nel control plane;
- gli oggetti Git del commit O identificati tramite SHA completo;
- l'infrastruttura GitHub/Sigstore usata per esecuzione e attestazione, entro il threat model dichiarato.

### 6.2 Untrusted

Sono sempre untrusted:

- tutto ciò che proviene da H;
- manifest, JSON, CSV e Markdown candidate;
- workflow presenti in H;
- script Python/shell presenti in H;
- package manifest presenti in H;
- symlink/gitlink/submodule dichiarati da H;
- path, glob, URI o riferimenti dichiarati da H;
- nomi file e metadata testuali provenienti da H.

### 6.3 Regola centrale

> Il trusted control plane può **leggere** H, ma non può **eseguire** H.

La regola vale anche indirettamente: non devono essere eseguiti tool che caricano automaticamente configurazioni, plugin, hook o dipendenze provenienti dal Candidate.

---

## 7. Threat model

### T01 — Control-plane replacement

H tenta di cambiare workflow, G o A.

**Difesa:** B/G/A provengono dal lato trusted e le loro identità sono registrate in R.

### T02 — Candidate code execution

H inserisce Python, shell, Makefile, package script, action locale o configurazione capace di eseguire codice.

**Difesa:** nessun eseguibile H viene importato, invocato o usato come action; H è letto come blob/dati.

### T03 — Path confusion/traversal

H dichiara path assoluti, `..`, path Unicode ambigui, symlink o gitlink.

**Difesa:** allowlist di path normalizzati + verifica del tipo Git object; symlink/gitlink sono rifiutati nella superficie qualificata salvo futura specifica esplicita.

### T04 — Parser/resource abuse

H fornisce JSON/CSV/Markdown eccessivamente grandi o strutture patologiche.

**Difesa:** limiti finiti di byte, righe, profondità e record; parsing fail-closed.

### T05 — Authority substitution

H tenta di sostituire O, builder, input, fonte registration o snapshot.

**Difesa:** A è trusted e G confronta H/O con A.

### T06 — Receipt confusion/replay

Una receipt valida per un altro B/G/A/H/O viene riutilizzata.

**Difesa:** R incorpora tutti gli identificatori, bundle digest e versione schema; la verifica richiede match esatto.

### T07 — Gate Core defect

G contiene un bug logico.

**Difesa:** ciclo G → G+1, assurance separata, corpus regressione e riqualification soltanto se l'impact analysis dimostra reachability sulla qualification interessata.

### T08 — GitHub workflow misconfiguration

Il workflow trusted acquisisce permessi eccessivi o condizioni pericolose.

**Difesa:** workflow minimale, pin action, `actionlint`, `zizmor`, CodeQL quando applicabile, review indipendente e governance repository.

### T09 — Attestation misuse

Il job di attestazione viene influenzato da H o attesta un risultato non prodotto da G.

**Difesa:** separazione dei job; il job attest consuma soltanto R/digest già verificati e non esegue né rilegge H.

### T10 — Supply-chain substitution

Una dipendenza del control plane cambia senza essere qualificata.

**Difesa:** dipendenze e action pin a versione immutabile/digest quando tecnicamente possibile; lock/manifest e review esplicita di ogni variazione della toolchain trusted.

---

## 8. Architettura logica

### 8.1 Trusted Trigger Workflow

Responsabilità:

- ricevere l'evento autorizzato;
- fissare B e H;
- selezionare G e A trusted;
- invocare G;
- propagare fail-closed l'exit code;
- consegnare R al successivo strato soltanto in caso di PASS.

Non contiene logica CEW sostanziale.

### 8.2 Candidate Object Reader

Responsabilità:

- acquisire oggetti Git appartenenti esattamente a H;
- esporre soltanto una API di lettura blob;
- verificare path/type/size;
- non creare un ambiente eseguibile del Candidate.

Implementazione preferita:

- Git object access/bare repository isolato, oppure API GitHub per blob/trees;
- nessun checkout di H usato come working directory operativa di G.

La scelta bare Git vs Git object API è reversibile e demandata al piano; entrambe devono rispettare la stessa interfaccia `CandidateReader`.

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
- definire gli invarianti;
- definire la authority boundary CEW-CONTRACT/FEM.

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
- creare, se richiesto dalla policy, un'attestazione GitHub/Sigstore;
- non decidere autonomamente PASS/FAIL.

### 8.8 Optional Promotion Publisher

Se la governance di merge richiederà un check/status esplicitamente associato a H, esso deve essere pubblicato **solo dopo** la verifica di R da un job separato e minimale.

Il Promotion Publisher è difesa operativa GitHub, non trust anchor CEW. La qualification resta definita da R.

---

## 9. Event model GitHub

### 9.1 Preferred mode — `pull_request_target`

Per un repository pubblico, `pull_request_target` usa il workflow dal contesto base/trusted e quindi fornisce la separazione desiderata.

Questa modalità è autorizzata soltanto se:

1. esiste una Actions event policy applicabile che consente esplicitamente l'evento/workflow desiderato;
2. il workflow non esegue codice proveniente da H;
3. il job di verifica non dispone di secret;
4. i permessi sono minimi;
5. le action sono pin a full commit SHA;
6. la configurazione viene verificata prima dell'attivazione.

Vincolo temporale verificato: GitHub indica enforcement della default policy che blocca `pull_request_target` nei repository pubblici dal **2 novembre 2026** in assenza di policy applicabile.

### 9.2 SHA semantics

Con `pull_request_target`, `GITHUB_SHA` è il commit della base/default branch, non H.

Conseguenza normativa:

> il successo del check della run `pull_request_target` **non costituisce da solo prova dell'identità o della qualification di H**.

B viene derivato dal contesto trusted; H viene letto esplicitamente dal payload PR e verificato/registrato in R.

La qualification CEW è quindi legata a H dalla Receipt, non dal valore implicito di `GITHUB_SHA` della run.

### 9.3 Required-status-check semantics

GitHub consente a workflow `pull_request_target` di produrre check valutabili nelle PR, ma i required checks devono essere soddisfatti rispetto al commit che GitHub considera corrente per la merge policy.

CEW-GATE-AUTHORITY-01 **non assume** che il check nativo della run sia sufficiente a provare H.

Se si desidera automatizzare la promotion tramite required status check, l'implementazione deve scegliere una delle due strade:

1. dimostrare con uno spike repository reale che il check configurato soddisfa correttamente la policy sulla latest H; oppure
2. usare un Promotion Publisher separato che pubblica il risultato verificato esplicitamente per H.

In entrambi i casi R resta la prova CEW canonica.

### 9.4 Safe fallback — trusted `workflow_dispatch`

Se `pull_request_target` non è configurabile o approvato, il Gate Authority può operare tramite `workflow_dispatch` trusted con:

- H passato come SHA completo;
- verifica che H appartenga alla PR prevista;
- attore autorizzato dalla Actions policy;
- stessi vincoli no-exec e permessi minimi.

GitHub documenta che i check generati da `workflow_dispatch` non devono essere assunti come required checks di una PR. Il fallback preserva quindi la **qualification**, non necessariamente la stessa automazione di **promotion**.

### 9.5 Event policy come prerequisito deployment

La presenza/configurazione reale delle Actions Policies non è assunta. Deve essere verificata prima dell'attivazione.

---

## 10. Permission model

### 10.1 Job `qualify`

Permessi massimi previsti:

- `contents: read`;
- nessun `id-token: write`;
- nessun `attestations: write`;
- nessun `pull-requests: write`;
- nessun secret applicativo.

### 10.2 Handoff `qualify → attest`

Il trasporto di R tra job è un dettaglio implementativo ma deve rispettare:

- same-run scope;
- digest R calcolato nel job `qualify`;
- verifica del digest nel consumer;
- nessuna dipendenza da retention storica;
- nessun artifact effimero usato come autorità permanente.

### 10.3 Job `attest`

Eseguito soltanto se `qualify` è PASS.

Permessi minimi previsti:

- `id-token: write`;
- `attestations: write`;
- `contents: read` solo se richiesto dall'action usata.

Il job:

- non checkouta H;
- non interpreta H;
- verifica il digest di R prima dell'attestazione.

### 10.4 Job `promote` opzionale

Se necessario per la merge policy, riceve soltanto R verificata + H e dispone esclusivamente del permesso minimo necessario a pubblicare il check/status previsto.

Non riesegue la qualification.

---

## 11. Candidate-as-data protocol

### 11.1 Path allowlist

A definisce i path candidate autorizzati. Qualunque path fuori allowlist è ignorato o, se dichiarato parte del qualification bundle, causa FAIL.

### 11.2 Object types

Per la superficie qualificata sono accettati soltanto blob regolari.

Sono rifiutati:

- symlink;
- gitlink/submodule;
- path assoluti;
- componenti `..`;
- duplicazioni dopo normalizzazione;
- oggetti di tipo non previsto.

### 11.3 Content constraints

Ogni tipo dati ha limiti dichiarati:

- JSON: dimensione massima + profondità massima + schema chiuso dove necessario;
- CSV: dimensione massima + numero righe + colonne attese;
- Markdown/evidence: dimensione massima e trattamento testuale non eseguibile.

Le soglie quantitative saranno fissate nel piano sopra il corpus N12 reale ma resteranno finite.

### 11.4 No-exec invariant

È vietato:

- importare moduli Python da H;
- eseguire script H;
- eseguire action locali H;
- eseguire hook Git H;
- installare dipendenze descritte da H;
- valutare template o comandi provenienti da H;
- usare H come working directory di tool che fanno discovery automatica di plugin/config eseguibile.

---

## 12. Frozen Authority bootstrap

A non deve nascere dentro la qualification PR che dovrà essere giudicata.

### Bootstrap A0

Un piccolo PR dedicato promuove nel trusted control plane:

- autorità N12 già verificata;
- valori derivati da O;
- identità output storico;
- supporti registration congelati;
- invarianti CEW-CONTRACT-01;
- authority boundary CEW-FEM.

A0 non introduce dati nuovi: rende machine-checkable fatti già verificati contro O e audit trail #147.

### Qualification successiva

Solo dopo il merge umano di A0, una qualification PR può essere giudicata rispetto ad A0.

---

## 13. Qualification Receipt schema

R deve includere almeno:

```text
schema_id
schema_version
qualified_at
control_plane:
  base_commit_sha
gate_core:
  repository
  commit_sha
  version
authority:
  authority_id
  authority_sha256
candidate:
  base_repository
  pr_number
  head_repository
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

Per repository pubblici, GitHub Artifact Attestations usa Sigstore e registra provenance verificabile. CEW usa questa capacità come **strato aggiuntivo**, non come sostituto della receipt.

### Subject

Subject preferito:

- SHA-256 della Qualification Receipt canonica; oppure
- SHA-256 di un qualification bundle deterministico contenente receipt + evidence index.

### Predicate CEW

Deve contenere almeno:

- `control_plane_base_sha`;
- `gate_core_sha`;
- `authority_sha256`;
- `candidate_head_sha`;
- `operational_commit_sha`;
- `qualification_bundle_sha256`;
- `replay_output_sha256`;
- `qualified`;
- versione schema CEW Gate Authority.

La verifica futura controlla sia firma/provenance GitHub sia contenuto CEW.

---

## 15. Nuova formulazione di I02

> **I02 — Trusted Gate Invocation.** La decisione di qualification deve essere prodotta esclusivamente da un Gate Core G identificato e trusted, invocato da un control plane B non modificabile dal Candidate H. H non può cambiare G/A né introdurre codice eseguito dal control plane. L'exit status e la receipt di G devono propagarsi fail-closed.

I02 si dimostra tramite proprietà finite:

1. identity di B/G/A;
2. identity di H;
3. no-exec H;
4. separation dei job/permission;
5. fail-closed propagation;
6. receipt binding B/G/A/H/O.

Non richiede di modellare tutte le forme sintattiche equivalenti di GitHub Actions.

---

## 16. Conservazione degli invarianti CEW-CONTRACT-01

Restano invariati:

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

Soltanto la non-bypassabilità viene rifondata sul trust boundary invece che sul parsing sintattico del workflow candidate.

---

## 17. Gate Core lifecycle

### 17.1 G0 bootstrap non self-validating

G0 non può dichiarare autonomamente di essere trusted.

La prima promozione G0 richiede almeno:

- presente design approvato;
- review umana indipendente del diff;
- actionlint/zizmor/code scanning disponibili;
- test unit/property/adversarial/integration;
- prova no-exec Candidate;
- replay N12 riproducibile;
- verifica manuale della configurazione GitHub rilevante;
- decisione umana esplicita di promozione G0.

Soltanto dopo tale decisione G0 diventa trust anchor per qualification successive.

### 17.2 Qualification delle versioni successive

Ogni G+1 deve superare il Gate Core assurance package della versione precedente quando applicabile, più review indipendente.

### 17.3 G → G+1

Un finding futuro nel Gate Core produce G+1.

Non riapre automaticamente le qualification precedenti. È richiesta impact analysis:

- invariant affetto;
- classi di input raggiungibili;
- receipt/candidate potenzialmente interessate;
- prova di reachability sul caso specifico;
- decisione di requalification solo se materialmente necessaria.

---

## 18. Testing strategy

### 18.1 Unit tests

Test per ogni funzione pura/schema/invariant.

### 18.2 Property-based tests

Applicati ai dati candidate, non alla grammatica GitHub Actions.

Categorie:

- campi mancanti;
- tipi errati;
- duplicati;
- permutazioni;
- valori boundary;
- path patologici;
- Unicode ambiguo;
- strutture annidate;
- dimensioni oltre soglia;
- inconsistenze Manifest/Receipt/Authority.

### 18.3 Adversarial corpus

Corpus stabile per regressioni reali #147, riclassificate per invariant invece che per “round”.

Le regressioni puramente legate alla sintassi YAML della qualification workflow non appartengono al Candidate corpus perché H non controlla più il workflow trusted.

### 18.4 Integration tests

Devono dimostrare almeno:

- candidate valido → PASS;
- candidate modifica il proprio workflow → nessun effetto sul control plane;
- candidate modifica una copia di A → nessun effetto su A trusted;
- candidate aggiunge script malevolo → non eseguito;
- symlink/gitlink → FAIL;
- candidate force-push durante una run → R resta legata allo H iniziale;
- replay O → output storico esatto;
- mismatch B/G/A/H/O → FAIL;
- handoff R alterato → FAIL;
- authority boundary CEW-FEM violata → FAIL.

---

## 19. Workflow assurance tools

Il control plane non implementa un parser GitHub Actions alternativo.

Quando cambia il workflow trusted vengono usati:

- **actionlint**;
- **zizmor**;
- **CodeQL/code scanning** disponibile;
- pin a SHA completi delle action;
- dipendenze trusted pin/locked.

Questi strumenti qualificano il control plane; non decidono la semantica CEW del Candidate.

---

## 20. Repository governance

### 20.1 Stato attuale verificato

Al momento della specifica:

- N12 è pubblico;
- `main` non risulta protetto;
- non risultano ruleset attivi.

### 20.2 Target minimo

Per `main` deve essere progettato un repository-level ruleset compatibile con repository pubblico GitHub Free che includa, salvo verifica account:

- pull request obbligatoria;
- blocco force-push;
- blocco deletion;
- required status check dove utile;
- bypass ridotto/documentato.

### 20.3 Required workflows

Non sono prerequisito. GitHub documenta i required workflows nei ruleset organization/enterprise; N12 è user-owned. La soluzione deve funzionare senza migrazione organizzativa.

---

## 21. Actions policy

Il deployment preferito tramite `pull_request_target` è subordinato a event policy esplicita.

Prima dell'attivazione deve essere verificato in Settings:

1. disponibilità Actions Policy;
2. policy applicabile a `pull_request_target`;
3. autorizzazione del workflow CEW Gate Authority;
4. attori/eventi non necessari negati;
5. assenza di liberalizzazione generica dei workflow privilegiati.

In assenza di esito positivo si usa `workflow_dispatch` trusted.

---

## 22. Migrazione dalla PR #147

### M0 — Freeze

#147 viene congelata al suo audit trail finale. Non vengono aggiunti ulteriori round di parser hardening.

### M1 — Gate Authority bootstrap

Nuova PR piccola da `main` contenente esclusivamente:

- presente specifica;
- Gate Core G0;
- Trusted Trigger Workflow;
- A0 Frozen Authority;
- test del control plane;
- documentazione assurance.

Nessuna nuova proprietà ingegneristica N12.

### M2 — Promozione umana di G0/A0

G0/A0 vengono promossi soltanto dopo il bootstrap non self-validating definito in §17.1.

### M3 — Qualification payload pulito

Nuova PR contiene soltanto il qualification payload CEW-CONTRACT-01, non il giudice.

### M4 — Receipt/Attestation

Il trusted Gate Core produce R per H e, se richiesto, relativa attestation.

### M5 — Retire #147

Dopo la nuova qualification chiusa e verificata, #147 può essere chiusa come `superseded`, preservando integralmente audit trail e discussioni.

Nessuna chiusura automatica è autorizzata.

---

## 23. Failure handling

### Gate Core unavailable

Nessuna qualification. Stato `BLOCKED_CONTROL_PLANE`.

### Actions policy blocks trigger

Nessun fallback implicito: soltanto trigger trusted alternativo approvato.

### Candidate read failure

FAIL closed con failure code stabile.

### Replay failure

FAIL; nessuna receipt `qualified=true`.

### Attestation service unavailable dopo PASS

R può essere prodotta ma lo stato resta `QUALIFIED_NOT_ATTESTED` o equivalente; se la promotion policy richiede attestazione, la promotion resta bloccata.

### New Gate Core finding

Si apre G+1 e si effettua impact analysis; nessuna riapertura massiva automatica.

---

## 24. Criterio di arresto della qualification

Una qualification CEW-CONTRACT-01 può essere dichiarata chiusa quando, sullo stesso H:

1. B è identificato;
2. G è trusted già qualificato;
3. A è trusted e immutata rispetto alla run;
4. H è l'exact candidate head con head repository/PR identificati;
5. O è l'operational commit autorizzato;
6. H non è stato eseguito come codice;
7. qualification bundle digest registrato;
8. replay deterministico PASS;
9. tutti gli invarianti applicabili PASS;
10. authority boundary CEW-FEM intatta;
11. R lega esattamente B/G/A/H/O;
12. trusted workflow completa con successo;
13. attestation presente se richiesta dalla promotion policy;
14. nessun finding aperto dimostra una decisione errata di G su quello specifico H.

Dopo questo punto, un finding su G è gestito tramite lifecycle G → G+1 e impact analysis.

---

## 25. Qualification vs Promotion

Le due decisioni sono separate.

- **Qualification:** G stabilisce che H soddisfa A e produce R.
- **Promotion/merge:** governance umana/GitHub decide se H può essere integrato.

Il fatto che `pull_request_target` operi con `GITHUB_SHA` della base rende ancora più importante non confondere check GitHub e qualification identity.

La promotion può usare required checks/status publisher/attestation, ma la prova CEW canonica rimane R.

Nessun auto-merge è autorizzato.

---

## 26. Evidenze minime del Gate Authority

Il bootstrap deve produrre almeno:

- design spec approvata;
- threat model;
- Gate Core source identity;
- B/G/A0 identity/digest;
- workflow identity;
- test report;
- actionlint report;
- zizmor report;
- code scanning report disponibile;
- adversarial corpus report;
- integration report;
- sample PASS receipt;
- sample FAIL receipt;
- prova handoff-integrity;
- attestation verification evidence, se attivata;
- human review decision;
- human promotion decision G0/A0.

---

## 27. Decisioni reversibili e da governare

### Reversibili

- bare Git vs Git object API;
- formato interno CandidateReader;
- libreria property testing;
- soglie size limit finite;
- naming failure code;
- `pull_request_target` vs trusted `workflow_dispatch`;
- meccanismo same-run di handoff R;
- uso o meno del Promotion Publisher.

### Da governare con particolare cautela

- promozione A0;
- promozione G0;
- ruleset/policy applicati a `main`;
- schema/versione delle Qualification Receipt;
- policy che rende obbligatoria l'attestation per promotion.

---

## 28. Precondizioni prima dell'implementazione

Prima del piano operativo devono essere approvate/verificate:

1. questa specifica;
2. decisione di mantenere #147 congelata;
3. nessun nuovo round di parser hardening su #147;
4. disponibilità reale o fallback Actions Policies;
5. repository-level ruleset target compatibile con account;
6. disponibilità Artifact Attestations nel repository pubblico;
7. A0 derivabile senza nuovi dati tecnici;
8. nessuna implementazione CEW-FEM;
9. bootstrap G0 esplicitamente non self-validating.

---

## 29. Acceptance criteria della prima implementazione

La prima implementazione è accettabile solo se dimostra con evidenza fresh:

- PR candidate modifica il proprio workflow → nessun effetto su B/G;
- PR candidate modifica copia A → nessun effetto su A trusted;
- nessuno script Candidate eseguito;
- B/G/A/H/O tutti registrati in R;
- una mutazione di ciascuna identity produce FAIL;
- authority boundary mutation produce FAIL;
- O riproduce output storico;
- R viene verificata indipendentemente;
- alterazione del handoff R viene rifiutata;
- event policy/ruleset effettivi documentati;
- actionlint/zizmor senza blocker aperti;
- review indipendente G0 senza false-positive contro threat model;
- decisione umana di promozione G0/A0;
- nessun auto-merge attivo.

---

## 30. Riferimenti piattaforma verificati

Vincoli usati nella progettazione, verificati sulla documentazione ufficiale GitHub al 13 ottobre 2026:

- `pull_request_target` nei repository pubblici è soggetto a default policy di blocco; GitHub indica enforcement dal 2 novembre 2026 in assenza di policy applicabile;
- `pull_request_target` usa come `GITHUB_SHA` l'ultimo commit della base/default branch, non H;
- Actions Policies consentono regole per eventi e attori;
- Artifact Attestations usa Sigstore; nei repository pubblici la provenance è registrata anche in transparency log pubblico;
- repository-level rulesets sono disponibili nei repository pubblici con GitHub Free;
- i ruleset “Require workflows to pass before merging” sono documentati a livello organization/enterprise e non vengono assunti disponibili nel repository user-owned N12;
- required status checks devono riferirsi al commit considerato corrente dalla merge policy;
- check da `workflow_dispatch` non devono essere assunti come required checks della PR.

La configurazione specifica dell'account/repository deve essere verificata al deployment e prevale sulle assunzioni di progetto.

---

## 31. Esito atteso

CEW-GATE-AUTHORITY-01 è riuscito quando la qualification non è più un sistema che prova a dimostrare la propria incorrompibilità interpretando sé stesso.

Il risultato atteso è:

> un Candidate H non fidato viene valutato come dato da un Gate Core G già trusted, invocato da B, rispetto a una Authority A già trusted e a una Operational Authority O immutabile; la decisione è registrata in una Receipt R legata a B/G/A/H/O e, quando previsto, attestata. Un difetto futuro del giudice produce una nuova versione del giudice e una impact analysis, non una sequenza indefinita di patch alla qualification corrente.

Questa architettura costituisce il nuovo punto di riferimento per superare la fase di stabilizzazione CEW-CONTRACT-01 e riprendere la catena canonica CEW senza consumare lavoro in hardening sintattico non finito.