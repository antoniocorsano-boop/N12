# CEW Gate Authority Task 9 — Trusted Qualification Workflow Design

**Data:** 14 ottobre 2026  
**Stato:** specifica scritta in revisione umana; implementazione non autorizzata da questo documento  
**Repository:** `antoniocorsano-boop/N12`  
**Baseline `main`:** `692630b3961bff770273e170181c5e025deafdc4`  
**Spec madre:** `docs/superpowers/specs/2026-10-13-cew-gate-authority-01-design.md`  
**Ambito:** Task 9 soltanto — trusted qualification workflow basato sui trust anchor G0/A0 già promossi.

---

## 1. Obiettivo

Task 9 deve trasformare G0/A0 da trust anchor bootstrap promossi a **control plane di qualification realmente invocabile**, senza modificare G0/A0 e senza anticipare attestation, promotion automation, CEW-FEM-01 o repository governance.

Il risultato deve essere un workflow trusted che:

1. parte soltanto tramite `workflow_dispatch` sul ref trusted `main`;
2. riceve esclusivamente `pr_number` e `candidate_sha` come input umano;
3. verifica che `candidate_sha` sia l'exact head corrente della PR indicata al momento del preflight;
4. acquisisce H come oggetti Git in un bare repository, senza checkout e senza esecuzione di codice Candidate;
5. materializza e verifica G0/A0 dalle identità promosse;
6. usa esclusivamente O per il replay storico;
7. produce la Qualification Receipt R tramite G0;
8. trasferisce R a un secondo job tramite artifact same-run immutabile;
9. verifica indipendentemente l'integrità dell'handoff;
10. propaga alla conclusione del workflow la decisione PASS/FAIL di G0 in modo fail-closed.

Task 9 deve ridurre la superficie futura di review: tutte le decisioni di trigger, ref, identity, fetch, handoff, permessi e failure semantics vengono congelate qui prima del codice.

---

## 2. Baseline trusted congelata

Task 9 NON modifica le identità promosse.

### G0

- Gate Core version: `G0`
- exact reviewed commit: `1f32a24f456e7db18c994096e4c8f5067222a592`
- source-bundle SHA-256: `b56a98461373f59bc54ad3bd88d3047cff45a7f840b862248a99cd33ed3fe766`
- G0 manifest Git blob SHA: `318a38199e5d7643e654442b9d92cbf41c94dd7f`

### A0

- authority ID: `N12_CEW_CONTRACT_01_A0`
- Git blob SHA: `d6f71146b5b833650f1943021d956e1a2d742563`
- SHA-256: `88ab731c986cef0af474bf567a9bb19a12a43dcdbef2de6cb211107b17f92dbb`

### O

- Operational Authority commit: `d806dcca72779b5a186defe557a7a9b739575a90`

### Promotion evidence

Il workflow deve verificare nel Control Plane Base B la presenza di:

`governance/cew-gate-authority/G0_PROMOTION_RECORD_v1.json`

con almeno questi valori esatti:

- `decision = PROMOTED`
- repository `antoniocorsano-boop/N12`
- G0 exact reviewed commit come sopra;
- G0 source-bundle SHA-256 come sopra;
- G0 manifest blob SHA come sopra;
- A0 authority ID, blob SHA e SHA-256 come sopra;
- O come sopra;
- tutte le authority-boundary flag `false`;
- `cew_fem_01_required = true`.

La promozione è esterna al manifest G0: il workflow non deve modificare `promotion_state=CANDIDATE` né reinterpretarlo come difetto.

---

## 3. Non-obiettivi

Task 9 non include:

- modifica di G0 o A0;
- nuova versione G1;
- modifica dello schema Qualification Receipt;
- Artifact Attestation / Sigstore;
- `id-token: write`;
- `attestations: write`;
- pubblicazione di commit status/check su H;
- required checks o ruleset repository;
- `pull_request_target`;
- auto-merge;
- merge automatico della qualification PR;
- CEW-FEM-01;
- solver selection/run/result;
- chiusura o supersession di PR #147.

Qualunque necessità reale di cambiare il comportamento di G0/A0 durante Task 9 è un **G1 trigger** e deve fermare Task 9 invece di patchare silenziosamente il trust anchor promosso.

---

## 4. Trigger canonico e Control Plane Base B

### 4.1 Evento unico

Il workflow production Task 9 usa esclusivamente:

`workflow_dispatch`

Non vengono configurati nello stesso file `push`, `pull_request`, `pull_request_target`, `workflow_run`, `repository_dispatch` o trigger schedulati.

### 4.2 Ref canonico

Una run è CEW-canonica soltanto se:

- `github.repository == antoniocorsano-boop/N12`;
- `github.ref == refs/heads/main`;
- il ref è una branch, non un tag;
- B è registrato come exact `github.sha` della run.

GitHub permette di lanciare un `workflow_dispatch` selezionando un branch/tag diverso dal default branch. Per questo la presenza di `workflow_dispatch` non è, da sola, prova di trusted invocation.

Qualunque run su ref diverso da `refs/heads/main` deve terminare prima di leggere H con classificazione `NON_CANONICAL_CONTROL_PLANE_REF`.

### 4.3 Evoluzione di B

B può cambiare quando `main` avanza. R registra sempre l'exact B usato dalla run.

Task 9 non considera automaticamente trusted una futura modifica al workflow o ai componenti B-layer. Ogni modifica a:

- workflow production;
- preflight/dispatch contract;
- handoff verifier;
- toolchain action pin;

richiede review e ricertificazione del control plane prima di essere usata come nuova baseline operativa.

G0/A0 restano invece selezionati tramite le identità promosse, indipendentemente dall'avanzamento di B.

---

## 5. Input contract

Il workflow espone soltanto due input obbligatori:

- `pr_number`: intero positivo in rappresentazione decimale canonica;
- `candidate_sha`: SHA Git completo lowercase di 40 caratteri esadecimali.

Non sono input utente:

- G;
- A;
- O;
- repository base;
- path A0;
- digest A0;
- gate-core version;
- workflow mode;
- artifact name;
- permission set.

Questi valori sono trusted constants del control plane.

Input mancanti, non canonici o fuori formato devono fallire prima di qualsiasi candidate fetch.

---

## 6. PR metadata contract

Il job `qualify` acquisisce i metadata PR tramite GitHub API usando il `GITHUB_TOKEN` soltanto con permessi read-only.

Prima del fetch Candidate devono essere veri contemporaneamente:

- PR esistente;
- `state == open`;
- base repository `antoniocorsano-boop/N12`;
- base branch `main`;
- PR number uguale all'input;
- `head.sha == candidate_sha`;
- `head.repo.full_name` presente e non vuoto.

Il payload API viene salvato come file dati e passato al G0 CLI come `--pr-metadata`; non viene interpolato in comandi shell.

Il preflight non assume che H appartenga allo stesso repository: le fork PR pubbliche sono ammesse come dati non fidati, purché il ref PR sintetico del base repository risolva esattamente a H.

---

## 7. Candidate acquisition — no checkout

### 7.1 Fonte Git

H viene acquisito dal base repository tramite:

`refs/pull/<pr_number>/head`

in un repository Git **bare** dedicato sotto `RUNNER_TEMP`.

Non viene usato `actions/checkout` per H.

### 7.2 Regole del bare repo

Il repository Candidate locale deve:

- essere creato ex novo;
- avere hook disabilitati esplicitamente;
- non avere working tree;
- non eseguire submodule/LFS/package manager;
- non usare credenziali persistenti;
- non avere come directory operativa il workspace B/G.

Dopo il fetch, il commit ottenuto viene confrontato byte-for-byte come stringa SHA con `candidate_sha`.

### 7.3 Race / force-push semantics

Sequenza normativa:

1. API PR metadata dichiara H = requested SHA;
2. fetch del ref sintetico PR;
3. `FETCH_HEAD` deve essere esattamente H;
4. da quel punto la run usa soltanto l'oggetto H già acquisito.

Se un force-push avviene tra 1 e 3 e il ref sintetico punta a H2, la run fallisce chiusa.

Se il branch cambia dopo 3, la run può completare per H originale: R resterà legata a H e non potrà essere usata per promuovere un H successivo senza una nuova qualification.

---

## 8. Trusted materialization di G0/A0/O

### 8.1 Checkout B

È ammesso un checkout del solo B trusted, exact `github.sha`, con:

- `persist-credentials: false`;
- profondità minima sufficiente;
- action ufficiale pin a full commit SHA.

### 8.2 Materializzazione G0

G0 viene fetchato esplicitamente per exact commit `1f32a24f...` e materializzato in una directory trusted separata.

Prima dell'invocazione devono essere verificati:

- `HEAD == 1f32a24f...`;
- manifest blob SHA `318a3819...`;
- `source_bundle_sha256 == b56a9846...` nel manifest;
- A0 blob SHA `d6f71146...` dentro G0;
- SHA-256 bytes A0 `88ab731c...`;
- promotion record in B coerente con queste identità.

Non si usa una copia di G/A proveniente da H.

### 8.3 Materializzazione O

Nel repository trusted viene fetchato exact O `d806dcca...`.

La successiva materializzazione di builder/input/source resta demandata esclusivamente al Gate Core G0 e alle identity già congelate in A0.

---

## 9. Workflow topology

Il workflow ha tre job logici.

### 9.1 `qualify`

Responsabilità:

- validare B/ref/input;
- leggere PR metadata;
- acquisire H bare;
- verificare trust anchor G0/A0/promotion record;
- fetch O;
- invocare il G0 CLI;
- catturare l'exit code senza perdere un'eventuale FAIL receipt;
- costruire l'handoff envelope;
- caricare l'artifact same-run una sola volta.

Il job `qualify` non trasforma `qualified=false` in un errore infrastrutturale prima di aver preservato e trasportato la receipt.

### 9.2 `verify-handoff`

Responsabilità:

- non leggere né acquisire H;
- non rieseguire G0;
- scaricare esclusivamente l'artifact prodotto da `qualify`, preferibilmente tramite `artifact-id` restituito dall'upload;
- verificare envelope, run identity e digest;
- verificare che la receipt trasportata sia esattamente quella prodotta dal job precedente.

### 9.3 `decision`

Job minimale finale con `if: always()`.

Regole:

- infrastructure/preflight failure → FAIL;
- G0 exit `0` + handoff PASS → workflow PASS;
- G0 exit `1` + handoff PASS → workflow FAIL come `NOT_QUALIFIED`;
- G0 exit `2` → workflow FAIL come `CONTROL_PLANE_OR_INVOCATION_ERROR`;
- receipt attesa ma handoff non verificato → FAIL;
- stato ambiguo → FAIL.

Il workflow non ha percorsi implicitamente verdi.

---

## 10. Receipt handoff contract

### 10.1 File artifact

Quando G0 emette R, l'artifact contiene esattamente:

- `qualification-receipt.json`;
- `handoff-envelope.json`.

Nessun file Candidate viene incluso nell'artifact di handoff.

### 10.2 Naming

Il nome dell'artifact deve essere univoco almeno per:

- `github.run_id`;
- `github.run_attempt`;
- H.

`overwrite` resta disabilitato.

Il consumer usa l'`artifact-id` prodotto dall'upload quando supportato dall'action ufficiale selezionata; il nome non è l'unico selettore di identità.

### 10.3 Due digest distinti

Il CLI G0 salva `canonical_receipt_bytes(R) + newline` nel file.

Per evitare ambiguità vengono registrati due digest diversi:

1. `receipt_canonical_sha256`: SHA-256 della serializzazione canonica JSON senza newline;
2. `receipt_transport_sha256`: SHA-256 dei byte esatti del file `qualification-receipt.json`, inclusa la newline finale prodotta dal CLI.

I due digest non devono essere confusi né rinominati genericamente `receipt_sha256`.

### 10.4 Handoff envelope v1

Campi minimi:

- `schema_id = CEW_GATE_AUTHORITY_HANDOFF_ENVELOPE`
- `schema_version = 1`
- `run_id`
- `run_attempt`
- `control_plane_base_sha`
- `gate_core_commit_sha`
- `gate_core_source_bundle_sha256`
- `authority_id`
- `authority_sha256`
- `candidate_pr_number`
- `candidate_head_repository`
- `candidate_head_sha`
- `operational_commit_sha`
- `qualification_exit_code`
- `receipt_canonical_sha256`
- `receipt_transport_sha256`

Il consumer richiede match esatto con il contesto same-run e con le trusted constants.

### 10.5 Artifact-service digest

Se l'action di upload espone `artifact-digest`, esso viene registrato come evidenza di trasporto aggiuntiva e come job output.

Non sostituisce né il digest canonico CEW né il digest dei byte della receipt.

---

## 11. Permission model

Permessi massimi Task 9:

### Job `qualify`

- `contents: read`
- `pull-requests: read` soltanto per acquisire metadata PR in modo autenticato

### Job `verify-handoff`

- nessun write scope;
- eventuale `actions: read` soltanto se richiesto dall'action ufficiale per lo scenario same-run selezionato.

### Job `decision`

- nessun permesso aggiuntivo.

Sono vietati in Task 9:

- `contents: write`;
- `pull-requests: write`;
- `checks: write`;
- `statuses: write`;
- `id-token: write`;
- `attestations: write`;
- repository/app secrets.

Il `GITHUB_TOKEN` automatico è ammesso esclusivamente con i read scope dichiarati.

---

## 12. Toolchain policy

Tutte le GitHub Actions usate nel workflow production devono essere:

- ufficiali o già esplicitamente approvate;
- compatibili con Node 24 al momento dell'implementazione;
- risolte fresh alla versione stabile scelta;
- verificate come provenienti dal repository ufficiale;
- pin a **full commit SHA**, mai a tag nel workflow committed.

Il piano operativo dovrà registrare per ogni action:

- repository;
- release/tag informativo;
- full commit SHA usato;
- runtime Node;
- motivo d'uso.

Non vengono introdotti workflow dependency lockfile in Task 9: sono una variazione di governance/toolchain separata e non necessaria per ottenere il control plane minimale.

Il workflow deve essere validato con actionlint, zizmor e CodeQL/scan applicabile prima dell'attivazione.

---

## 13. B-layer code boundary

Task 9 può aggiungere un piccolo adapter trusted separato dal Gate Core, con responsabilità limitate a:

- validazione ref/input;
- validazione PR metadata;
- verifica promotion record / trust-anchor identities;
- costruzione e verifica handoff envelope;
- calcolo digest trasporto/canonico.

Questo codice appartiene a B, non a G0, e non deve essere inserito nel G0 source-bundle manifest.

Non può implementare invarianti CEW I01..I17 né reinterpretare il Candidate payload.

Se una funzione necessaria modifica la decisione CEW sostanziale, appartiene a G1 e non a Task 9.

---

## 14. Failure taxonomy Task 9

Failure code/control-plane state minimi:

- `NON_CANONICAL_CONTROL_PLANE_REF`
- `INVALID_DISPATCH_INPUT`
- `PR_METADATA_UNAVAILABLE`
- `PR_NOT_OPEN`
- `PR_BASE_MISMATCH`
- `PR_HEAD_MISMATCH`
- `CANDIDATE_REF_FETCH_FAILED`
- `CANDIDATE_FETCHED_SHA_MISMATCH`
- `PROMOTION_RECORD_INVALID`
- `G0_IDENTITY_MISMATCH`
- `A0_IDENTITY_MISMATCH`
- `OPERATIONAL_AUTHORITY_FETCH_FAILED`
- `GATE_CORE_INVOCATION_ERROR`
- `RECEIPT_NOT_EMITTED`
- `HANDOFF_ENVELOPE_INVALID`
- `HANDOFF_RUN_ID_MISMATCH`
- `HANDOFF_RECEIPT_DIGEST_MISMATCH`
- `ARTIFACT_HANDOFF_FAILED`
- `NOT_QUALIFIED`

Questi codici descrivono il control plane. Non devono duplicare o sostituire i failure code CEW prodotti dentro R da G0.

---

## 15. Threat / regression matrix obbligatoria prima del GREEN

Il piano deve introdurre test RED espliciti almeno per:

1. dispatch su branch diverso da `main`;
2. dispatch su tag;
3. `pr_number` non canonico;
4. SHA abbreviato/non lowercase/non esadecimale;
5. PR inesistente;
6. PR chiusa;
7. PR con base diversa da `main`;
8. requested H diverso dal current PR head;
9. force-push tra metadata read e fetch PR ref;
10. fetched PR ref diverso da H;
11. fork PR valida acquisita solo come Git data;
12. Candidate con workflow/script/action/package malevoli non eseguiti;
13. Candidate che modifica copie di G/A senza effetto sul trusted G/A;
14. promotion record mancante o contraddittorio;
15. G0 commit errato;
16. G0 manifest blob errato;
17. G0 source-bundle digest errato;
18. A0 blob SHA errato;
19. A0 SHA-256 errato;
20. O non acquisibile;
21. G0 PASS receipt → artifact → verify-handoff PASS;
22. G0 FAIL receipt → artifact preservato → verify-handoff PASS → workflow finale FAIL;
23. G0 invocation error senza receipt → workflow finale FAIL;
24. receipt modificata di un byte nel trasporto;
25. newline receipt rimossa/aggiunta senza aggiornare transport digest;
26. canonical digest corretto ma transport digest errato;
27. envelope con `run_id` di altra run;
28. envelope con `run_attempt` di un rerun precedente;
29. envelope H/B/G/A/O non coerente;
30. artifact selector ambiguo/nome riusato;
31. handoff job che tenta di leggere H;
32. permesso write introdotto nel workflow;
33. action non pin a full SHA;
34. action pin proveniente da repository/fork non autorizzato.

Il GREEN non è accettabile con test genericamente equivalenti: questi casi devono essere tracciabili per nome/assertion nel corpus Task 9.

---

## 16. Verification ladder

Prima di chiedere una review indipendente sul branch Task 9 devono essere verdi sullo stesso exact head:

1. unit test B-layer;
2. integration test dispatch/PR contract;
3. no-exec Candidate regression suite esistente;
4. G0/A0 identity verification tests;
5. artifact/handoff tests;
6. full `tests/cew_gate_authority` suite esistente senza regressioni;
7. Task 9 workflow simulation/static contract tests;
8. Python compileall;
9. actionlint sulla nuova workflow;
10. zizmor sulla nuova workflow;
11. CodeQL applicabile;
12. test che prova assenza di write permission/secret/attestation scopes;
13. fresh independent review sull'exact final head.

Qualunque modifica dopo la review invalida la review per l'exact head.

---

## 17. Activation sequence

Task 9 non deve diventare production-active nello stesso istante in cui viene scritto.

Sequenza:

1. implementazione su branch dedicato;
2. RED → GREEN locale/CI;
3. exact-head certification;
4. fresh independent review;
5. human visual/non-visual review non richiesta: la decisione è tecnica/governance;
6. decisione umana esplicita di merge/activation;
7. merge commit verso `main`, preservando la storia della PR;
8. verifica post-merge che il workflow sia presente sul default branch;
9. prima run pilot `workflow_dispatch` su `main` contro una PR qualification separata;
10. verifica R + handoff + decision semantics;
11. solo dopo Task 9 può essere dichiarato `OPERATIONAL_QUALIFICATION_AVAILABLE`.

La prima run pilot non deve avere potere di merge/promotion.

---

## 18. Stop rules anti-churn

Durante Task 9 si interrompe l'implementazione invece di aggiungere patch locali se emerge uno dei seguenti casi:

- serve cambiare I01..I17;
- serve cambiare schema R;
- serve cambiare A0;
- serve cambiare G0 runtime;
- serve introdurre un nuovo dato ingegneristico;
- serve eseguire H;
- serve un write permission GitHub;
- serve attestation per far funzionare la qualification base;
- serve `pull_request_target` per far funzionare la qualification base;
- serve un parser GitHub Actions custom come trust boundary.

Questi casi richiedono rispettivamente G1, A1 o un nuovo task di governance, non un altro round di hardening ad hoc dentro Task 9.

---

## 19. Acceptance criteria Task 9

Task 9 è completabile soltanto se, su un exact head unico e recensito:

- #148/G0/A0 restano immutati come trust anchor;
- production workflow usa solo `workflow_dispatch`;
- run non-main fallisce prima di candidate fetch;
- H è acquisito senza checkout/esecuzione;
- PR metadata e fetched ref convergono allo stesso exact H;
- G0/A0/promotion record identities sono verificate prima dell'invocazione;
- replay usa O soltanto;
- PASS e FAIL receipt sono entrambe preservate quando G0 le emette;
- handoff verifica run identity e i due digest della receipt;
- artifact è univoco e non overwrite;
- workflow finale è verde soltanto per G0 PASS + handoff PASS;
- nessun write scope, secret, OIDC o attestation scope è presente;
- action pin sono full SHA e verificati;
- actionlint/zizmor/CodeQL non hanno blocker;
- independent review dell'exact head è pulita;
- nessun auto-merge è abilitato;
- #147 resta intoccata;
- CEW-FEM resta non autorizzato.

---

## 20. Riferimenti piattaforma verificati al 14 ottobre 2026

La specifica usa questi fatti GitHub, verificati sulla documentazione ufficiale corrente:

- `workflow_dispatch` richiede che il workflow esista sul default branch, ma può essere eseguito su un branch/tag selezionato; `GITHUB_SHA` è l'ultimo commit del `GITHUB_REF` scelto;
- GitHub raccomanda il pin delle Actions a full-length commit SHA; il repository può anche applicare una policy che lo richiede;
- gli artifact servono al passaggio di dati tra job della stessa run;
- le generazioni moderne di `upload-artifact` creano artifact immutabili, con artifact ID e digest SHA-256 esposti dall'action;
- le versioni correnti delle principali Actions ufficiali stanno migrando/sono migrate a Node 24, quindi Task 9 deve risolvere fresh pin compatibili invece di riusare automaticamente i pin Node 20 del bootstrap.

Riferimenti ufficiali:

- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts
- https://github.com/actions/upload-artifact

---

## 21. Decisione architetturale finale

Task 9 adotta il seguente modello:

`workflow_dispatch on main (B) → PR metadata check → bare fetch exact H → promoted G0/A0 verification → O fetch → G0 qualification → R + envelope → immutable same-run artifact → independent handoff verification → final fail-closed decision`

Questo è il confine operativo da implementare.

Il piano non deve riaprire le decisioni qui congelate; deve soltanto tradurle in file, test RED→GREEN, comandi di verifica e criteri di review.
