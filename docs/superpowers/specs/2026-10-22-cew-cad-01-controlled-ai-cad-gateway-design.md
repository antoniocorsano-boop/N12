# CEW-CAD-01 — Controlled AI CAD Gateway

**Data:** 22 ottobre 2026  
**Stato:** design approvato in chat; specifica scritta in revisione umana; **NOT AUTHORIZED FOR IMPLEMENTATION**  
**Repository:** `antoniocorsano-boop/N12`  
**Base canonica di redazione:** `main@adbad6214df5acaf6dc8250a6cd2692d25733c6b`  
**Caso pilota:** Condominio N.12  
**Ambito:** accesso agentico controllato a un motore CAD esterno, con OpenCADStudio come candidato di benchmark iniziale, per ispezione, proposta, modifica limitata, verifica e salvataggio verificato di copie di lavoro, senza trasferire all'IA autorità epistemica o professionale.

---

## 1. Decisione architetturale

CEW-CAD-01 introduce un **Controlled AI CAD Gateway** fra qualunque agente IA e il motore CAD esterno.

La decisione fondamentale è:

> nessun modello o client agentico accede direttamente alla superficie mutativa generica del motore CAD nel workflow CEW canonico.

Il modello di interazione diventa:

`Human Authority → AI Client → CEW CAD Gateway → CAD Adapter → CAD Engine → Working Copy`

con un percorso distinto per l'autorità CEW:

`Source/Evidence/Claim/Decision/CanonicalProperty → CEW CAD Gateway policy → CAD projection`

Il Gateway è contemporaneamente:

- **server MCP verso l'agente**;
- **adapter/policy enforcement point verso il CAD**;
- **generatore di Changeset e Receipt**;
- **confine fail-closed** fra proposta agentica ed esecuzione CAD.

CEW non implementa un nuovo motore CAD o kernel geometrico, in coerenza con `BUILD LAST — REUSE FIRST` del Master Plan.

---

## 2. Compatibilità con il Master Plan CEW

CEW-CAD-01 non sostituisce né modifica la catena canonica:

**Fonti → Evidenze → Conoscenza canonica → Modello geometrico parametrico → Controllo automatico → Sufficienza conoscitiva → Modello strutturale → Verifiche → Fascicolo tecnico**

Il Gateway è un adapter operativo della fase geometrica/CAD. Non diventa fonte della verità.

Restano vincolanti gli stati epistemici canonici:

- `DOC` — documentale;
- `MIS` — misurato;
- `RIF` — riferito;
- `INF` — inferito;
- `INC` — incerto;
- `ND` — non disponibile.

Regola invariabile:

> la necessità di completare una geometria CAD non autorizza a inventare un valore mancante né a promuovere implicitamente `INF`, `INC` o `ND` a `DOC`/`MIS`.

Il Gateway può produrre **osservazioni candidate** e risultati geometrici verificabili; non può promuoverli autonomamente a proprietà canoniche CEW.

---

## 3. Relazione con lo stato corrente del progetto

Alla base di questa specifica il Master Plan canonico mantiene **WIP=1** e `CEW-B01` come unico macro-task attivo.

Pertanto CEW-CAD-01 è:

- una specifica architetturale parcheggiata;
- non attiva un nuovo fronte operativo;
- non modifica `CEW_CURRENT_STATE.json`;
- non modifica la baseline conoscitiva N12;
- non autorizza CEW-FEM, SolverRun o Result;
- non autorizza modifiche al modello strutturale canonico;
- non autorizza merge, deploy o uso mutativo su elaborati N12 reali.

L'implementazione potrà iniziare solo con una successiva decisione umana di fase che mantenga o aggiorni esplicitamente il vincolo WIP.

---

## 4. Stato di OpenCADStudio nel CEW

**OpenCADStudio è, in CEW-CAD-01, un `BENCHMARK CANDIDATE`, non un componente già adottato della toolchain canonica CEW.**

Questa specifica non modifica le decisioni del `CEW_MASTER_PLAN.md` sugli strumenti esterni. L'eventuale promozione di OpenCADStudio a componente `ADOPT` richiederà una decisione umana separata dopo il pilot.

La separazione `Gateway → CAD Adapter → CAD Engine` è intenzionale: se OpenCADStudio non supera il benchmark, CEW-CAD-01 deve poter conservare invarianti, Changeset, Approval e Receipt sostituendo soltanto l'adapter.

### 4.1 Capacità OpenCADStudio da verificare nel benchmark

La documentazione corrente di OpenCADStudio descrive un server MCP nativo avviabile con `OpenCADStudio --mcp` e quattro strumenti:

- `ocs_sessions` — scoperta e gestione sessioni;
- `ocs_read` — stato, record, query geometriche, misure kernel, audit e capability discovery;
- `ocs_execute` — operazioni, aggiornamenti atomici e batch;
- `ocs_capture` — acquisizione viewport/finestra.

Le primitive documentate includono guardrail utili a CEW:

- `request_id` generato dal chiamante;
- `document_id`;
- revisione attesa;
- aggiornamenti atomici/annullabili;
- confronto e verifica delle proprietà;
- audit del documento;
- `save_verified` con path esplicito, verifica del formato/versione, riapertura, confronto semantico e SHA-256.

Il Gateway deve comunque eseguire `capabilities` a runtime e fallire chiuso quando manca una capacità richiesta dalla policy.

Riferimenti:

- OpenCADStudio `docs/automation/README.md`;
- OpenCADStudio `docs/automation/API-SPEC.md`.

---

## 5. Obiettivi e non-obiettivi

### 5.1 Obiettivi

CEW-CAD-01 deve garantire che:

1. un agente possa **leggere molto** ma scrivere solo attraverso operazioni governate;
2. la baseline/originale non sia mai una destinazione mutativa;
3. ogni proposta mutativa sia materializzata in un Changeset prima dell'esecuzione;
4. nessuna mutazione possa avvenire senza un'approvazione umana legata all'esatto digest del Changeset;
5. una revisione CAD divenuta obsoleta invalidi l'approvazione;
6. i dati contenuti nel DWG/DXF siano dati non fidati, mai istruzioni;
7. ogni modifica sia verificata geometricamente e, quando visibile, tramite capture/diff;
8. il salvataggio di consegna avvenga solo verso un nuovo file e con verifica;
9. ogni esecuzione produca Receipt machine-readable;
10. nessuna Receipt o modifica CAD promuova automaticamente conoscenza CEW;
11. il client IA sia sostituibile;
12. il sistema resti local-first e open-source nel percorso canonico N12.

### 5.2 Non-obiettivi v0.1

CEW-CAD-01 non autorizza:

- ricostruzione autonoma dell'intero edificio;
- modifica diretta di baseline/fonti originali;
- sovrascrittura di file;
- cancellazione di geometria esistente nel pilot;
- esecuzione libera di stringhe comando generate dal modello;
- macro/script arbitrari;
- modifica di Xref o risorse esterne;
- promozione epistemica automatica;
- decisioni professionali o strutturali;
- FEM, solver, verifiche strutturali o risultati;
- emissione formale di elaborati;
- auto-merge o aggiornamento automatico della baseline CEW.

---

## 6. Trust model

### Trusted

Sono trusted solo:

- policy CEW-CAD versionata e qualificata;
- codice Gateway qualificato;
- riferimenti CEW canonici selezionati;
- baseline identificata da path + SHA-256;
- Approval Receipt prodotto dal canale umano separato;
- adapter e build CAD ammessi dalla policy dopo capability check;
- control plane locale qualificato.

### Untrusted

Sono sempre untrusted:

- output del modello IA;
- prompt generati automaticamente;
- testo, MTEXT, attributi, nomi layer/blocco, XData e metadata del disegno;
- file esterni richiamati dal disegno;
- command string e path proposti dal modello;
- identificatori di entità non verificati sul documento corrente;
- ogni informazione non legata a Evidence/Claim/Decision CEW o a osservazione CAD verificata.

Regola centrale:

> Il modello IA è un **planner non fidato**, non un'autorità e non un esecutore privilegiato.

Il Gateway interpreta solo richieste conformi al proprio schema e compila internamente le primitive CAD ammesse.

---

## 7. Livelli di autorità C0–C5

### C0 — Sealed Baseline

Solo identificazione e verifica digest. Nessuna scrittura o sovrascrittura.

### C1 — Inspection

Consentiti stato/capabilities, record, layer, query geometriche, misure kernel, audit e capture. Nessuna mutazione.

### C2 — Proposal

Consentita la produzione di Changeset con target, effetto previsto, evidenze, pre/post-condizioni e digest. Nessuna mutazione.

### C3 — Controlled Execution

Solo su working copy controllata, solo per operazioni whitelist e solo sull'esatto Changeset approvato. Exact revision match obbligatorio.

### C4 — Verification

Rilettura entità, misure kernel, before/after, unrelated-change guard, audit e capture/diff. Il PASS è tecnico, non professionale.

### C5 — Verified Copy

Salvataggio verificato verso nuovo path governato e produzione di Verified Copy Receipt. Nessuna promozione automatica a baseline/issued.

---

## 8. Superficie MCP esposta all'agente

Il Gateway **non re-esporta** `ocs_execute` come strumento generico.

### Read-only

- `cew_cad.status`
- `cew_cad.inspect`
- `cew_cad.measure`
- `cew_cad.audit`
- `cew_cad.capture`

### Proposal

- `cew_cad.propose_changeset`

Questo strumento valida intent/target, risolve entity identity, collega Evidence/Claim/Decision, dichiara unresolved data e produce Changeset + digest. Non esegue nulla.

### Mutating

- `cew_cad.apply_approved_changeset`
- `cew_cad.verify_changeset`
- `cew_cad.save_verified_copy`

`apply_approved_changeset` accetta solo un Changeset già approvato tramite canale umano separato. Nessuno strumento MCP esposto all'agente crea l'Approval Receipt.

---

## 9. Approval e Changeset

### 9.1 Approval Receipt

L'approvazione deve essere fuori dalla superficie invocabile dal modello.

Campi minimi:

```json
{
  "schema": "cew.cad.approval.v1",
  "approval_id": "CEW-CAD-APP-000001",
  "changeset_id": "CEW-CAD-CS-000001",
  "changeset_sha256": "...",
  "document_sha256": "...",
  "document_id": 1,
  "base_revision": 128,
  "decision": "APPROVED",
  "approved_by": "human",
  "approved_at": "..."
}
```

Qualsiasi variazione del Changeset o della revisione invalida l'approvazione.

Le approvazioni native del client IA, quando disponibili, possono aggiungere un secondo livello di consenso ma non sostituiscono l'Approval Receipt CEW.

### 9.2 Changeset canonico

Campi minimi:

```json
{
  "schema": "cew.cad.changeset.v1",
  "changeset_id": "CEW-CAD-CS-000001",
  "intent": "...",
  "document": {
    "working_path": "...",
    "source_sha256": "...",
    "document_id": 1,
    "base_revision": 128,
    "cad_build": "...",
    "capabilities_sha256": "..."
  },
  "cew_context": {
    "evidence_refs": [],
    "claim_refs": [],
    "decision_refs": [],
    "epistemic_states": []
  },
  "operations": [],
  "preconditions": [],
  "postconditions": [],
  "expected_changed_entities": [],
  "forbidden_side_effects": [],
  "unresolved": [],
  "changeset_sha256": "..."
}
```

Regole:

- `base_revision` obbligatoria per ogni mutazione;
- digest sull'intero Changeset canonicalizzato;
- riferimenti CEW risolvibili;
- `ND` non può produrre coordinate/dimensioni implicite;
- `INF`/`INC` restano esplicitamente tali;
- target non univoco → non eseguibile;
- `unresolved` influente → non eseguibile;
- path e raw command non provengono direttamente dall'output del modello.

---

## 10. Whitelist mutativa v0.1

Il pilot deve essere deliberatamente limitato.

Consentito solo su un **DWG di laboratorio/copied working file**:

- creare geometria semplice in un layer `CEW-LAB`;
- modificare proprietà non identitarie esplicitamente ammesse;
- eseguire `undo` della propria transazione;
- salvare una nuova copia verificata.

Vietato nel pilot:

- cancellare entità preesistenti;
- modificare handle/ownership/table identity;
- `EXPLODE` o trasformazioni distruttive equivalenti;
- modificare Xref;
- importare file esterni;
- eseguire macro/script;
- eseguire raw `run` fornito dal modello;
- salvare con overwrite;
- operare su file `baseline` o `issued`.

Se il CAD richiede una command line per un'operazione ammessa, il Gateway deve costruirla da un template interno tipizzato e validato.

---

## 11. Protocollo operativo e fail-closed

### PRE

1. classificare il path;
2. verificare che il target sia `working`;
3. verificare SHA-256 sorgente;
4. acquisire session/document identity, revision e capabilities;
5. verificare assenza di comando interattivo sospeso;
6. audit iniziale;
7. capture baseline se rilevante;
8. Changeset;
9. Approval Receipt umano.

### APPLY

1. rileggere stato;
2. exact match identity/revision;
3. verificare digest Changeset/Approval;
4. eseguire solo primitive whitelist;
5. usare `request_id` stabile per retry identico;
6. stop alla prima failure;
7. nessun adattamento automatico del piano dopo errore mutativo.

### POST

1. rileggere entità attese;
2. verificare post-condizioni con kernel;
3. verificare changed-entity set e cambi non previsti;
4. capture/diff;
5. audit target-aware;
6. Technical Verification Receipt;
7. solo dopo PASS, save verificato su nuovo path;
8. SHA-256 output;
9. promozione CEW solo tramite decisione umana separata.

### Fail-closed minimo

Rifiutare quando:

- manca una capability richiesta;
- adapter/build CAD non soddisfa la policy;
- path non appartiene al working root;
- file è `baseline`/`issued`;
- SHA, document id o revision non coincidono;
- Changeset è cambiato dopo approval;
- Approval Receipt manca/non valida;
- target entity manca o non è univoca;
- operazione non è in whitelist;
- il modello fornisce raw command/path libero;
- precondizione CEW non è risolta;
- viene richiesto di trasformare `ND/INC/INF` in fatto senza Decision CEW;
- CAD è in stato interattivo/modale non previsto;
- risultano entità cambiate fuori dal perimetro;
- audit segnala perdita CEW-rilevante;
- save verificato fallisce;
- output richiede overwrite.

Nessun fallback permissivo.

---

## 12. Threat model minimo

- **T01 Prompt injection nel disegno:** contenuti CAD sono sempre dati, mai istruzioni.
- **T02 Raw command injection:** nessun execute/run generico esposto; template interni.
- **T03 Stale-state mutation:** revision mismatch → nuova proposta/approvazione.
- **T04 Path escape/overwrite:** path confinement server-side + no-overwrite.
- **T05 Epistemic laundering:** stati CEW propagati; nessuna promozione implicita.
- **T06 Unrelated mutation:** before/after + expected-changed-entities guard.
- **T07 Retry duplication:** request id stabile + receipt idempotente.
- **T08 Tool-surface expansion:** nuove capability CAD non diventano automaticamente autorizzate.
- **T09 Client substitution:** sicurezza nel Gateway, non nel prompt del client.
- **T10 Supply-chain drift:** identity/version/capability digest registrati e qualificati.

---

## 13. Workspace controllato

Struttura logica raccomandata:

```text
CivilExisting/
├── 00_sources/      # originali immutabili
├── 01_baseline/     # baseline sigillate
├── 02_working/      # sole copie mutabili
├── 03_evidence/     # evidenze e capture
├── 04_changesets/   # proposal + approval
├── 05_audits/       # audit e verification receipts
├── 06_verified/     # output verificati
└── 07_issued/       # sola promozione umana/formale
```

La struttura fisica del repository può differire; sono normativi classificazione e diritti.

Le root sono configurazione trusted del Gateway, non input del modello.

---

## 14. Client IA e portabilità

### OpenCode — pilot locale preferito

OpenCode supporta server MCP locali. Per CEW il client deve collegarsi al **Gateway**, non direttamente a OpenCADStudio.

`OpenCode → CEW CAD Gateway → OCS Adapter → OpenCADStudio --mcp`

Uso previsto: qualification locale, sviluppo/debug e prima prova senza dipendere da un servizio remoto.

### OpenAI API / Responses API

La Responses API supporta server MCP e collegamento a server locali/private tramite Secure MCP Tunnel, con approval configurabile.

`OpenAI Responses API → Secure MCP Tunnel → CEW CAD Gateway → CAD Adapter → CAD Engine`

Per v0.1, quando disponibile, ogni strumento mutativo deve richiedere anche approval lato client; resta comunque obbligatoria l'Approval Receipt CEW separata.

### ChatGPT

ChatGPT è un'interfaccia futura opzionale solo quando il prodotto/account in uso offre il percorso MCP necessario. La disponibilità della UI ChatGPT non è un requisito architetturale.

### Altri client

Sono ammessi se usano solo il Gateway, non hanno collegamento diretto mutativo al CAD qualificato, non possono creare Approval Receipt e non possono modificare la policy trusted.

---

## 15. Receipt model

### Inspection Receipt

- adapter/CAD build e capability digest;
- session/document identity;
- revision;
- document/source hash;
- audit summary;
- timestamp.

### Change Receipt

- Changeset digest;
- Approval id/digest;
- CAD request ids;
- revision prima/dopo;
- entità dichiarate cambiate;
- warning/errori;
- execution status.

### Technical Verification Receipt

- post-condition results;
- kernel measurements;
- unrelated-change result;
- capture/diff refs;
- audit result;
- `PASS | FAIL` tecnico.

### Verified Copy Receipt

- input technical receipt;
- output governed path;
- target format/version;
- verified-save result;
- output SHA-256;
- semantic verification result;
- stato `CANDIDATE_FOR_HUMAN_REVIEW`.

Nessuna receipt promuove autonomamente un modello a stato ingegneristico approvato.

---

## 16. Pilot di qualificazione

Il primo pilot non usa un elaborato N12 reale come target mutativo.

Sequenza:

1. copia DWG di laboratorio;
2. connessione al CAD candidato;
3. inspection + audit senza mutazione;
4. identificazione di 3–5 entità note;
5. misure kernel;
6. Changeset che crea geometria semplice su `CEW-LAB`;
7. prova che senza Approval la mutazione è negata;
8. approval umano dell'esatto digest;
9. applicazione;
10. verifica geometria, changed-entity set, capture e audit;
11. nuova copia verificata;
12. verifica hash dell'originale invariato;
13. produzione completa delle Receipt.

Negative test obbligatori:

- stale revision;
- Changeset alterato dopo approval;
- overwrite;
- path escape;
- raw command injection;
- target inesistente;
- falsa istruzione contenuta nel CAD;
- `ND` usato come valore geometrico;
- unrelated entity mutation;
- retry identico dopo timeout simulato.

---

## 17. Criteri di accettazione

Il pilot è **QUALIFIED** solo se tutti i seguenti criteri sono PASS:

1. originale invariato per SHA-256;
2. inspection/audit/capture senza mutazioni;
3. client privo di execute generico;
4. nessuna mutazione senza Approval esterna;
5. stale revision rifiutata prima della mutazione;
6. Changeset mutato invalida Approval;
7. operazione fuori whitelist rifiutata prima del CAD;
8. `ND/INC/INF` non diventano implicitamente fatti;
9. nessuna entità non prevista modificata;
10. post-condizioni geometriche verificate dal kernel CAD;
11. capture/diff disponibile per modifiche visibili;
12. audit target-aware senza perdita CEW-rilevante;
13. salvataggio verificato PASS con SHA-256;
14. istruzioni nel CAD non alterano policy/sequenza;
15. retry identico non duplica effetto;
16. catena Inspection → Changeset → Approval → Change → Verification → Verified Copy ricostruibile;
17. adapter OpenCADStudio sostituibile senza cambiare le invarianti CEW-CAD.

Un solo FAIL mantiene lo stato **NOT QUALIFIED**.

---

## 18. Decisioni demandate al futuro piano

Solo dopo approvazione umana della specifica e successiva autorizzazione di fase, il piano dovrà scegliere:

- linguaggio/SDK del Gateway;
- libreria MCP server/client;
- struttura `CADAdapter` e primo `OpenCADStudioAdapter`;
- meccanismo locale di Approval Receipt;
- canonical JSON serialization e digest rules;
- storage delle Receipt;
- MCP vs `--serve` per test headless di OpenCADStudio;
- sandbox/path confinement concreto su Windows;
- fixture DWG e strategia di test;
- CI senza GUI quando non necessaria.

Nessuna decisione implementativa può indebolire le invarianti della presente specifica.

---

## 19. Stop rule

Dopo la pubblicazione di questa specifica:

- **non implementare** CEW-CAD-01;
- **non modificare** `CEW_CURRENT_STATE.json`;
- **non aprire** un nuovo fronte operativo mentre CEW-B01 resta attivo;
- non collegare un agente a un DWG N12 reale con permessi mutativi;
- non configurare ChatGPT/OpenCode/Codex con accesso diretto a `ocs_execute` come scorciatoia;
- non promuovere OpenCADStudio da `BENCHMARK CANDIDATE` a `ADOPT` senza decisione separata.

Il prossimo atto ammesso è la **revisione umana della specifica**. Solo dopo approvazione scritta si potrà redigere un implementation plan; l'esecuzione resterà subordinata a una decisione esplicita sul WIP CEW.

---

## 20. Riferimenti

### CEW / N12

- `CEW_MASTER_PLAN.md`
- `CEW_CURRENT_STATE.json`
- `docs/superpowers/specs/2026-10-13-cew-gate-authority-01-design.md`
- CEW-CONTRACT-01 e relative qualification/assurance receipts

### OpenCADStudio

- <https://github.com/HakanSeven12/OpenCADStudio/blob/main/docs/automation/README.md>
- <https://github.com/HakanSeven12/OpenCADStudio/blob/main/docs/automation/API-SPEC.md>

### MCP clients

- OpenCode MCP: <https://opencode.ai/docs/mcp-servers/>
- OpenAI MCP / Responses API: <https://developers.openai.com/api/docs/guides/tools-connectors-mcp>

---

## 21. Sintesi normativa

CEW-CAD-01 separa quattro responsabilità:

- **IA:** analizza e propone;
- **Gateway:** applica policy, valida e compila operazioni consentite;
- **CAD engine:** esegue e misura la geometria reale;
- **professionista/CEW:** approva, interpreta e promuove conoscenza o elaborati.

Regola finale:

> **No evidence → no fact. No approved changeset → no mutation. No verification → no verified copy. No human decision → no canonical promotion.**
