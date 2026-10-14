# CEW Gate Authority Task 9 — Trusted Qualification Workflow Design

**Data:** 14 ottobre 2026  
**Stato:** specifica scritta in revisione umana; implementazione non autorizzata da questo documento  
**Repository:** `antoniocorsano-boop/N12`  
**Baseline `main`:** `692630b3961bff770273e170181c5e025deafdc4`  
**Spec madre:** `docs/superpowers/specs/2026-10-13-cew-gate-authority-01-design.md`  
**Ambito:** Task 9 soltanto — trusted qualification workflow sui trust anchor G0/A0 già promossi.

---

## 1. Decisione

Task 9 rende G0/A0 realmente invocabili da un control plane trusted senza modificare G0/A0 e senza anticipare attestation, promotion automation, repository governance o CEW-FEM-01.

Flusso normativo:

`workflow_dispatch su main (B) → PR metadata check → bare fetch exact H → verifica promotion record/G0/A0 → fetch O → G0 qualification → R + envelope → artifact same-run immutabile → verify-handoff → decision fail-closed`

Le decisioni di trigger, ref, identity, fetch, toolchain, handoff, permission e failure semantics sono congelate in questa specifica. Il piano successivo non deve riaprirle.

---

## 2. Baseline trusted congelata

### G0

- version: `G0`
- exact reviewed commit: `1f32a24f456e7db18c994096e4c8f5067222a592`
- source-bundle SHA-256: `b56a98461373f59bc54ad3bd88d3047cff45a7f840b862248a99cd33ed3fe766`
- manifest Git blob SHA: `318a38199e5d7643e654442b9d92cbf41c94dd7f`

### A0

- authority ID: `N12_CEW_CONTRACT_01_A0`
- Git blob SHA: `d6f71146b5b833650f1943021d956e1a2d742563`
- SHA-256: `88ab731c986cef0af474bf567a9bb19a12a43dcdbef2de6cb211107b17f92dbb`

### O

- exact operational commit: `d806dcca72779b5a186defe557a7a9b739575a90`

### Promotion record

B deve contenere `governance/cew-gate-authority/G0_PROMOTION_RECORD_v1.json` e il workflow deve verificarne almeno:

- `schema_id = CEW_GATE_AUTHORITY_PROMOTION_RECORD`;
- `schema_version = 1`;
- `decision = PROMOTED`;
- repository `antoniocorsano-boop/N12`;
- G0 exact commit/source bundle/manifest blob uguali ai valori sopra;
- A0 ID/blob/SHA-256 uguali ai valori sopra;
- O uguale al valore sopra;
- tutte le cinque authority-boundary flag `false`;
- `cew_fem_01_required = true`.

Il manifest G0 resta byte-identico alla versione recensita e continua a dichiarare `promotion_state=CANDIDATE`: la promozione è esterna e provata dal promotion record.

---

## 3. Hard scope

Task 9 NON include:

- modifiche a G0 o A0;
- G1 o A1;
- modifiche allo schema Qualification Receipt;
- Artifact Attestation/Sigstore;
- `pull_request_target`;
- required checks/ruleset;
- status/check publisher su H;
- auto-merge o merge automatico della qualification PR;
- CEW-FEM-01;
- solver, `SolverRun` o `Result`;
- modifica/chiusura/supersession della PR #147.

Se l'implementazione richiede una modifica decisionale a G0/A0 o a I01..I17, Task 9 si ferma: è un trigger G1/A1, non un finding da correggere localmente.

---

## 4. Trigger e Control Plane Base B

### Evento unico

Il workflow production usa esclusivamente `workflow_dispatch`.

Non contiene `push`, `pull_request`, `pull_request_target`, `workflow_run`, `repository_dispatch` o schedule.

### Ref canonico

Una run è CEW-canonica soltanto se:

- `github.repository == antoniocorsano-boop/N12`;
- `github.ref == refs/heads/main`;
- `github.ref_type == branch`;
- B = exact `github.sha` della run.

GitHub consente di dispatchare un workflow su branch/tag diversi dal default branch. Perciò qualunque ref diverso da `refs/heads/main` deve fallire **prima** di leggere H con `NON_CANONICAL_CONTROL_PLANE_REF`.

R registra sempre B. Una futura modifica al workflow, al B-layer adapter o ai pin delle Actions richiede nuova review/recertificazione del control plane; non modifica implicitamente G0/A0.

---

## 5. Input contract

Il workflow espone esattamente due input obbligatori:

- `pr_number`, `type: number`, valore intero positivo;
- `candidate_sha`, `type: string`, SHA Git completo lowercase di 40 caratteri esadecimali.

G, A, O, repository base, digest, path, artifact identity e permission set NON sono input utente.

Input assente, frazionario, abbreviato, uppercase o non esadecimale fallisce prima del candidate fetch con `INVALID_DISPATCH_INPUT`.

---

## 6. PR metadata contract

Il job `qualify` legge i metadata PR tramite GitHub API con `GITHUB_TOKEN` read-only.

Prima del fetch H devono essere veri insieme:

- PR esistente;
- `state == open`;
- PR number uguale all'input;
- base repository `antoniocorsano-boop/N12`;
- base branch `main`;
- `head.sha == candidate_sha`;
- `head.repo.full_name` presente.

Il JSON API è salvato come file dati e passato al G0 CLI via `--pr-metadata`; nessun campo Candidate/PR viene interpolato direttamente in shell command text.

Le fork PR pubbliche sono ammesse come dati non fidati; l'acquisizione Git avviene comunque dal ref sintetico del base repository.

---

## 7. Candidate H: acquisizione senza checkout

H viene fetchato da:

`refs/pull/<pr_number>/head`

in un repository Git bare nuovo sotto `RUNNER_TEMP`.

Vincoli:

- nessun `actions/checkout` su H;
- nessun working tree Candidate;
- hook locali disabilitati esplicitamente;
- nessun submodule/LFS/package manager;
- nessun import/esecuzione di script/action/config H;
- nessuna credenziale persistente;
- H mai usato come working directory di tool trusted.

Sequenza race-safe:

1. API PR metadata dichiara H = requested SHA;
2. fetch del ref sintetico PR;
3. `FETCH_HEAD` deve essere esattamente H;
4. CandidateReader opera soltanto sull'oggetto H acquisito.

Force-push tra 1 e 3 → `CANDIDATE_FETCHED_SHA_MISMATCH` e FAIL closed.

Force-push dopo 3 non cambia la run: R resta legata allo H originale e non vale per un nuovo head.

---

## 8. Materializzazione trusted G0/A0/O

### B checkout

È ammesso un checkout del solo B trusted, exact `github.sha`, con:

- `persist-credentials: false`;
- `fetch-depth: 1`;
- `submodules: false`;
- `lfs: false`;
- action pin full SHA definito in §12.

### G0

G0 viene fetchato per exact commit `1f32a24f...` e materializzato in directory trusted separata.

Prima dell'invocazione sono obbligatori:

- HEAD G0 esatto;
- manifest blob `318a3819...`;
- `source_bundle_sha256 == b56a9846...`;
- A0 blob `d6f71146...`;
- A0 bytes SHA-256 `88ab731c...`;
- promotion record B coerente con G0/A0/O.

Nessuna copia G/A proveniente da H può essere usata.

### O

Il repository trusted fetch-a exact O `d806dcca...`; la materializzazione builder/input/source resta esclusivamente responsabilità di G0/A0.

---

## 9. Topologia workflow

### Job `qualify`

Fa soltanto:

- ref/input preflight;
- PR metadata contract;
- bare fetch H;
- promotion-record + G0/A0 identity verification;
- fetch O;
- invocazione G0 CLI;
- cattura dell'exit code;
- generazione envelope;
- upload artifact.

Il comando G0 non deve far fallire il job prima che una eventuale `qualified=false` receipt sia preservata. L'exit code G0 viene acquisito come dato e propagato dal job finale.

### Job `verify-handoff`

- non legge H;
- non fetch-a H;
- non riesegue G0;
- scarica obbligatoriamente l'artifact tramite `artifact-id` prodotto da `qualify`;
- usa `digest-mismatch: error`;
- verifica envelope, run identity, trusted identities e digest file/canonico.

Il nome artifact non è usato come autorità o selettore principale.

### Job `decision`

Job minimale con `if: always()`.

Semantica esatta:

- preflight/infrastructure failure → FAIL;
- G0 exit `0` + `verify-handoff` PASS → workflow PASS;
- G0 exit `1` + `verify-handoff` PASS → workflow FAIL, stato `NOT_QUALIFIED`;
- G0 exit `2` → workflow FAIL, stato `CONTROL_PLANE_OR_INVOCATION_ERROR`;
- receipt attesa ma handoff non verificato → FAIL;
- qualunque stato non riconosciuto → FAIL.

Non esistono percorsi implicitamente verdi.

---

## 10. Receipt handoff contract

### Artifact

Quando G0 emette R, l'artifact contiene esattamente:

- `qualification-receipt.json`;
- `handoff-envelope.json`.

Nessun file Candidate viene incluso.

Nome artifact:

`cew-qualification-<run_id>-<run_attempt>-<candidate_sha>`

`overwrite: false`; `if-no-files-found: error`.

Il consumer usa esclusivamente l'`artifact-id` restituito dall'upload.

### Due digest Receipt

Il CLI G0 salva `canonical_receipt_bytes(R) + newline`.

Si registrano quindi due digest distinti:

- `receipt_canonical_sha256`: JSON canonico senza newline;
- `receipt_transport_sha256`: byte esatti del file, newline inclusa.

È vietato usare un generico `receipt_sha256` che renda ambiguo quale rappresentazione è stata hashata.

### Handoff envelope v1

Campi minimi obbligatori:

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

Il consumer richiede match esatto con current `run_id`, current `run_attempt`, B e le trusted constants.

L'`artifact-digest` SHA-256 esposto da upload-artifact è registrato come evidenza di trasporto aggiuntiva/job output. Non sostituisce i due digest CEW sopra.

---

## 11. Permission model

### `qualify`

- `contents: read`
- `pull-requests: read`

### `verify-handoff`

- `actions: read`

### `decision`

- nessun permesso aggiuntivo.

Vietati in Task 9:

- `contents: write`;
- `pull-requests: write`;
- `checks: write`;
- `statuses: write`;
- `id-token: write`;
- `attestations: write`;
- repository/app secrets.

È ammesso soltanto il `GITHUB_TOKEN` automatico con i read scope sopra.

---

## 12. Toolchain production congelata

Runner:

- `ubuntu-24.04`

Python:

- `3.12.15`

Actions ufficiali, release corrente verificata e full SHA obbligatorio nel workflow committed:

- `actions/checkout` release `v7.0.1` → `3d3c42e5aac5ba805825da76410c181273ba90b1` — Node 24;
- `actions/setup-python` release `v7.0.0` → `5fda3b95a4ea91299a34e894583c3862153e4b97` — Node 24;
- `actions/upload-artifact` release `v7.0.2` → `cf430e030ddbb5b0abf93d22962f4752f3646cd9` — Node 24, artifact ID + artifact digest;
- `actions/download-artifact` release `v8.0.2` → `9000827ccba6bdab643e8b6fd33ac0654aef8333` — Node 24, `artifact-ids`, `digest-mismatch: error`.

Nessun tag viene usato nel YAML committed: i tag sopra sono solo riferimenti documentali alla release da cui è stato risolto il full SHA.

Qualunque cambio di uno di questi pin dopo l'approvazione della spec costituisce toolchain revision e richiede review esplicita; il piano non deve scegliere versioni diverse autonomamente.

Task 9 non introduce workflow dependency lockfile: sarebbe una modifica di governance/toolchain separata non necessaria alla qualification minima.

---

## 13. B-layer boundary

Task 9 può aggiungere un adapter trusted piccolo e testabile, separato dal Gate Core, che implementa soltanto:

- ref/input contract;
- PR metadata contract;
- promotion record / G0/A0 identity verification;
- handoff envelope build/verify;
- digest canonico/trasporto.

Questo codice appartiene a B e non entra nel G0 source-bundle manifest.

Non può implementare I01..I17 o reinterpretare il Candidate payload. Se emerge una funzione decisionale CEW, è G1 e Task 9 si ferma.

---

## 14. Failure taxonomy control-plane

Codici minimi:

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

Questi codici descrivono B/control plane e non sostituiscono i failure code CEW interni a R.

---

## 15. Regression matrix obbligatoria

Prima del GREEN devono esistere test RED nominati/assertivi almeno per:

1. dispatch branch diverso da `main`;
2. dispatch tag;
3. PR number non intero/positivo;
4. SHA abbreviato/uppercase/non esadecimale;
5. PR inesistente;
6. PR chiusa;
7. base diversa da `main`;
8. requested H diverso dal current PR head;
9. force-push tra metadata read e fetch;
10. fetched ref diverso da H;
11. fork PR valida letta solo come data;
12. Candidate con workflow/script/action/package malevoli mai eseguiti;
13. Candidate con copie modificate G/A senza effetto;
14. promotion record mancante/contraddittorio;
15. G0 commit errato;
16. G0 manifest blob errato;
17. source-bundle digest errato;
18. A0 blob SHA errato;
19. A0 SHA-256 errato;
20. O non acquisibile;
21. PASS receipt → artifact → handoff PASS;
22. FAIL receipt preservata → handoff PASS → workflow finale FAIL;
23. G0 exit 2/no receipt → workflow finale FAIL;
24. receipt trasporto modificata di un byte;
25. newline receipt modificata;
26. canonical digest corretto ma transport digest errato;
27. envelope con `run_id` errato;
28. envelope con `run_attempt` precedente;
29. envelope B/G/A/H/O incoerente;
30. artifact ID mancante/errato;
31. handoff job che tenta di leggere H;
32. introduzione di qualunque write permission;
33. action non pin a full SHA;
34. action pin non corrispondente alle quattro identità congelate in §12.

Nessuno di questi casi può essere sostituito da un test generico che non renda evidente la specifica proprietà protetta.

---

## 16. Verification ladder

Sul medesimo exact final head Task 9, prima della review indipendente:

1. unit test B-layer;
2. PR/ref/input integration tests;
3. no-exec Candidate regressions esistenti;
4. G0/A0/promotion identity tests;
5. artifact/handoff tests;
6. full `tests/cew_gate_authority` suite esistente;
7. static contract tests della nuova workflow;
8. `python -m compileall`;
9. actionlint;
10. zizmor;
11. CodeQL applicabile;
12. permission/toolchain pin contract tests;
13. fresh independent review sull'exact head.

Una modifica dopo la review invalida la review per quell'exact head.

---

## 17. Activation sequence

1. implementazione su branch dedicato Task 9;
2. TDD RED → GREEN;
3. exact-head certification completa;
4. fresh independent review;
5. decisione umana esplicita di merge/activation;
6. merge commit verso `main` preservando la storia;
7. verifica post-merge che il workflow esista sul default branch;
8. prima run pilot `workflow_dispatch` su `main` contro una PR qualification separata;
9. verifica R + artifact + handoff + final decision;
10. solo allora stato `OPERATIONAL_QUALIFICATION_AVAILABLE`.

La run pilot non ha potere di merge/promotion.

---

## 18. Stop rules anti-churn

Task 9 si ferma invece di accumulare patch se emerge che serve:

- cambiare I01..I17;
- cambiare schema R;
- cambiare G0 o A0;
- introdurre un dato ingegneristico;
- eseguire H;
- introdurre write permission;
- usare attestation per la qualification base;
- usare `pull_request_target` per la qualification base;
- usare un parser GitHub Actions custom come trust boundary.

Questi sono nuovi task/G1/A1, non remediation locali Task 9.

---

## 19. Acceptance criteria

Task 9 è chiudibile soltanto se:

- G0/A0 promossi restano immutati;
- trigger unico `workflow_dispatch`;
- non-main fallisce prima del candidate fetch;
- H è acquisito senza checkout/esecuzione;
- API metadata e fetched PR ref convergono allo stesso exact H;
- promotion record/G0/A0 sono verificati prima di G0;
- replay usa O soltanto;
- PASS e FAIL receipt sono preservate quando emesse;
- handoff usa artifact ID e verifica current run/attempt + entrambi i digest;
- artifact è univoco, no overwrite;
- workflow finale è verde soltanto per G0 PASS + handoff PASS;
- non esistono write scope, secrets, OIDC o attestation scope;
- i quattro pin §12 sono esatti;
- actionlint/zizmor/CodeQL non hanno blocker;
- fresh independent review exact-head è pulita;
- nessun auto-merge;
- #147 resta intoccata;
- CEW-FEM resta non autorizzato.

---

## 20. Fatti GitHub verificati al 14 ottobre 2026

La specifica assume soltanto questi fatti verificati su documentazione/repository ufficiali GitHub:

- `workflow_dispatch` richiede il workflow sul default branch ma può essere eseguito su branch/tag selezionati; `GITHUB_SHA` segue il `GITHUB_REF` scelto;
- GitHub raccomanda pin Action a full commit SHA;
- workflow artifact è il meccanismo previsto per passare dati tra job della stessa run;
- upload-artifact moderno espone artifact ID e SHA-256 digest e crea artifact immutabili;
- download-artifact corrente supporta selezione per artifact ID e `digest-mismatch: error`;
- le quattro Actions congelate in §12 dichiarano runtime Node 24.

Riferimenti:

- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts
- https://github.com/actions/checkout
- https://github.com/actions/setup-python
- https://github.com/actions/upload-artifact
- https://github.com/actions/download-artifact

---

## 21. Esito della specifica

Il confine Task 9 è ora deterministico:

`B(main dispatch) → validated PR metadata → exact bare H → promoted G0/A0 → O → G0 R → immutable artifact by ID → verified handoff → fail-closed decision`

Il piano operativo successivo deve tradurre questo contratto in file, test RED→GREEN, comandi e criteri di verifica; non deve prendere nuove decisioni architetturali.