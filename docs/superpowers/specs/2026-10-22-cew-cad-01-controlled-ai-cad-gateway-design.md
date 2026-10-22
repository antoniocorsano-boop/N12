# CEW-CAD-01 — Controlled AI CAD Gateway

**Data:** 22 ottobre 2026  
**Stato:** design approvato in chat; specifica scritta in revisione umana; **NOT AUTHORIZED FOR IMPLEMENTATION**  
**Repository:** `antoniocorsano-boop/N12`  
**Base canonica di redazione:** `main@adbad6214df5acaf6dc8250a6cd2692d25733c6b`  
**Caso pilota:** Condominio N.12  
**Ambito:** accesso agentico controllato a OpenCADStudio per ispezione, proposta, modifica limitata, verifica e salvataggio verificato di copie di lavoro, senza trasferire all'IA autorità epistemica o professionale.

---

## 1. Decisione architetturale

CEW-CAD-01 introduce un **Controlled AI CAD Gateway** fra qualunque agente IA e OpenCADStudio.

La decisione fondamentale è:

> nessun modello o client agentico accede direttamente alla superficie mutativa generica di OpenCADStudio nel workflow CEW canonico.

Il modello di interazione diventa:

`Human Authority → AI Client → CEW CAD Gateway → OpenCADStudio → Working Copy`

con un percorso distinto per l'autorità CEW:

`Source/Evidence/Claim/Decision/CanonicalProperty → CEW CAD Gateway policy → CAD projection`

Il Gateway è contemporaneamente:

- **server MCP verso l'agente**;
- **client/adapter verso OpenCADStudio**;
- **policy enforcement point**;
- **generatore di Changeset e Receipt**;
- **confine fail-closed** fra proposta agentica ed esecuzione CAD.

OpenCADStudio resta il motore CAD e il kernel geometrico esterno. CEW non implementa un nuovo motore CAD, in coerenza con `BUILD LAST — REUSE FIRST` del Master Plan.

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
- non attiva `CEW-CAD-01` come nuovo fronte operativo;
- non modifica `CEW_CURRENT_STATE.json`;
- non modifica la baseline conoscitiva N12;
- non autorizza CEW-FEM, SolverRun o Result;
- non autorizza modifiche al modello strutturale canonico;
- non autorizza merge, deploy o uso su elaborati reali.

L'implementazione potrà iniziare solo con una successiva decisione umana di fase che mantenga o aggiorni esplicitamente il vincolo WIP.

---

## 4. Capacità OpenCADStudio assunte

La specifica si appoggia esclusivamente a capacità pubblicamente documentate da OpenCADStudio e deve verificarle a runtime tramite `capabilities` prima dell'uso.

OpenCADStudio espone via MCP quattro strumenti:

- `ocs_sessions` — scoperta e gestione sessioni;
- `ocs_read` — stato, record, query geometriche, misure kernel, audit e capability discovery;
- `ocs_execute` — operazioni, aggiornamenti atomici e batch;
- `ocs_capture` — acquisizione viewport/finestra.

Le mutazioni supportano almeno i seguenti guardrail utili a CEW:

- `request_id` generato dal chiamante;
- `document_id`;
- revisione attesa;
- aggiornamenti atomici/annullabili;
- confronto e verifica delle proprietà;
- audit del documento;
- `save_verified` con path esplicito, verifica del formato/versione, riapertura, confronto semantico e SHA-256.

CEW-CAD-01 non presume che queste capacità restino immutate: il Gateway deve rilevare versione e capability effettive della build connessa e fallire chiuso quando manca una capacità richiesta dalla policy.

Riferimenti tecnici:

- OpenCADStudio `docs/automation/README.md`;
- OpenCADStudio `docs/automation/API-SPEC.md`.

---

## 5. Obiettivi

CEW-CAD-01 deve garantire che:

1. un agente possa **leggere molto** ma scrivere solo attraverso operazioni governate;
2. la baseline/originale non sia mai una destinazione mutativa;
3. ogni proposta mutativa sia materializzata in un Changeset determinato prima dell'esecuzione;
4. nessuna mutazione possa avvenire senza un'approvazione umana legata all'esatto digest del Changeset;
5. una revisione CAD divenuta obsoleta invalidi l'approvazione e richieda nuova lettura/proposta;
6. i dati contenuti nel DWG/DXF siano trattati come **dati non fidati**, mai come istruzioni per l'agente;
7. ogni modifica sia verificata geometricamente e, quando visibile, anche tramite capture;
8. il salvataggio di consegna avvenga soltanto verso un nuovo file e con `save_verified`;
9. ogni esecuzione produca una Receipt machine-readable;
10. nessuna Receipt o modifica CAD promuova automaticamente conoscenza CEW;
11. il client IA sia sostituibile: OpenCode, Codex, OpenAI API, ChatGPT quando tecnicamente disponibile, o altro client MCP;
12. il sistema resti local-first e open-source per il percorso canonico N12.

---

## 6. Non-obiettivi

CEW-CAD-01 v0.1 non autorizza:

- ricostruzione autonoma dell'intero edificio;
- modifica diretta della baseline o delle fonti originali;
- salvataggio con sovrascrittura;
- cancellazione di geometria esistente nel pilot;
- esecuzione libera di stringhe comando generate dal modello;
- script arbitrari provenienti dal modello o dal disegno;
- caricamento automatico di plugin, macro o dipendenze indicate dal DWG;
- modifica di Xref o risorse esterne;
- promozione epistemica automatica;
- decisioni professionali o strutturali;
- modello FEM, solver, verifiche strutturali o risultati;
- emissione formale di elaborati;
- auto-merge o aggiornamento automatico della baseline CEW.

---

## 7. Trust model

### 7.1 Trusted

Sono trusted solo:

- la policy CEW-CAD versionata e qualificata;
- il codice Gateway qualificato;
- i riferimenti CEW canonici esplicitamente selezionati;
- la baseline identificata da path + SHA-256;
- l'Approval Receipt prodotto dal canale umano separato;
- la build OpenCADStudio ammessa dalla policy dopo capability check;
- il codice del control plane locale qualificato.

### 7.2 Untrusted

Sono sempre untrusted:

- output del modello IA;
- prompt generati automaticamente;
- testo, MTEXT, attributi, nomi layer, nomi blocco, XData e metadata del disegno;
- file esterni richiamati dal disegno;
- command string proposta dal modello;
- path proposti dal modello;
- identificatori di entità non verificati sul documento corrente;
- ogni informazione non legata a Evidence/Claim/Decision CEW o a osservazione CAD verificata.

### 7.3 Regola centrale

> Il modello IA è un **planner non fidato**, non un'autorità e non un esecutore privilegiato.

Il Gateway interpreta soltanto richieste conformi al proprio schema e compila internamente le primitive OpenCADStudio ammesse.

---

## 8. Livelli di autorità C0–C5

### C0 — Sealed Baseline

Consentito:

- identificare file, digest, formato, dimensione e provenienza;
- verificare che l'originale resti invariato.

Vietato:

- aprire la baseline come destinazione di scrittura;
- salvare sopra la baseline;
- modificarne metadata o contenuto.

### C1 — Inspection

Consentito:

- `sessions` / `state` / `capabilities`;
- lettura record e layer;
- query geometriche;
- misure kernel;
- audit;
- capture;
- calcolo di osservazioni candidate.

Nessuna mutazione.

### C2 — Proposal

Consentito:

- produrre un Changeset;
- indicare target, effetto previsto, evidenze e controlli post-condizione;
- calcolare il digest del Changeset.

Nessuna mutazione.

### C3 — Controlled Execution

Consentito solo su **working copy disposable o controllata**:

- eseguire operazioni presenti nella whitelist;
- usare esclusivamente l'esatto Changeset approvato;
- applicare optimistic concurrency sulla revisione;
- produrre nuova revisione e Change Receipt.

### C4 — Verification

Consentito:

- rileggere entità mutate;
- misurare post-condizioni;
- confrontare entità prima/dopo;
- verificare assenza di cambi non previsti;
- audit;
- capture/diff;
- classificare PASS/FAIL tecnico del changeset.

Il PASS tecnico non equivale a decisione professionale.

### C5 — Verified Copy

Consentito:

- `save_verified` verso un nuovo path governato;
- registrare hash, formato, versione e receipt;
- produrre una copia candidata a revisione umana.

Vietato:

- promuovere automaticamente la copia a baseline o `issued`;
- sovrascrivere originali o versioni già emesse.

---

## 9. Architettura logica

```text
Human Authority
      |
      | approval / review
      v
+---------------------------+
| AI Client                 |
| OpenCode / Codex / API /  |
| other MCP client          |
+-------------+-------------+
              |
              | CEW-safe MCP tools
              v
+---------------------------+
| CEW CAD Gateway           |
| - schema validation       |
| - policy engine           |
| - epistemic guards        |
| - changeset compiler      |
| - approval verifier       |
| - path confinement        |
| - receipts / audit log    |
+-------------+-------------+
              |
              | OCS MCP adapter
              v
+---------------------------+
| OpenCADStudio             |
| ocs_sessions/read/        |
| execute/capture           |
+-------------+-------------+
              |
              v
       CEW working copy
```

Il Gateway **non re-esporta** `ocs_execute` come strumento generico.

---

## 10. Superficie MCP esposta all'agente

La superficie v0.1 deve essere piccola e semanticamente CEW-specifica.

### 10.1 Strumenti read-only

- `cew_cad.status`
  - build OCS;
  - capability digest;
  - session/document identity;
  - revision;
  - path class (`baseline`, `working`, `verified`, `issued`);
  - source hash quando disponibile.

- `cew_cad.inspect`
  - layer;
  - entità filtrate;
  - proprietà selezionate;
  - record CEW-rilevanti.

- `cew_cad.measure`
  - lunghezze;
  - aree;
  - nearest geometry;
  - containment;
  - intersections;
  - altri risultati del kernel esplicitamente supportati.

- `cew_cad.audit`
  - wrapper read-only dell'audit OCS;
  - target format/version richiesto dalla policy.

- `cew_cad.capture`
  - viewport/window entro limiti definiti;
  - supporto a diff quando disponibile.

### 10.2 Strumento di proposta

- `cew_cad.propose_changeset`
  - valida intent e target;
  - risolve entity identity sul documento corrente;
  - collega Evidence/Claim/Decision refs;
  - rifiuta assunzioni non dichiarate;
  - produce Changeset canonico e digest;
  - **non esegue nulla**.

### 10.3 Strumenti mutativi

- `cew_cad.apply_approved_changeset`
  - accetta solo un Changeset già approvato tramite canale umano separato;
  - verifica digest, documento, revisione, working-root e policy;
  - compila internamente le operazioni OCS consentite;
  - non accetta comandi arbitrari dal modello.

- `cew_cad.verify_changeset`
  - verifica post-condizioni e unrelated-change guard;
  - produce Technical Verification Receipt.

- `cew_cad.save_verified_copy`
  - disponibile solo dopo verification PASS;
  - salva esclusivamente sotto il root `verified` autorizzato;
  - usa `save_verified`;
  - produce Verified Copy Receipt.

Nessuno strumento MCP esposto all'agente crea l'Approval Receipt.

---

## 11. Canale di approvazione umano

L'approvazione deve essere **fuori dalla superficie che il modello può invocare**.

Formato logico minimo:

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

v0.1 può usare una CLI o una piccola UI locale separata. L'implementazione concreta è demandata al piano, ma deve rispettare due invarianti:

1. il modello non può generare una approval valida per se stesso;
2. qualsiasi variazione del Changeset o della revisione invalida l'approvazione.

Le approvazioni native del client IA, quando disponibili, possono aggiungere un secondo livello di consenso, ma non sostituiscono l'Approval Receipt CEW.

---

## 12. Changeset canonico

Formato logico minimo:

```json
{
  "schema": "cew.cad.changeset.v1",
  "changeset_id": "CEW-CAD-CS-000001",
  "created_at": "...",
  "intent": "...",
  "document": {
    "working_path": "...",
    "source_sha256": "...",
    "document_id": 1,
    "base_revision": 128,
    "ocs_build": "...",
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

### 12.1 Regole

- `base_revision` è obbligatoria per qualsiasi mutazione;
- il digest copre l'intero contenuto canonicalizzato del Changeset;
- riferimenti CEW devono essere risolvibili;
- una proprietà `ND` non può produrre una coordinata o dimensione implicita;
- ogni `INF`/`INC` usato deve restare dichiarato come tale;
- un elemento non identificabile univocamente rende il Changeset non eseguibile;
- `unresolved` non vuoto rende il Changeset non eseguibile salvo che ogni voce sia esplicitamente non influente sulle operazioni proposte;
- path e command string non provengono direttamente dall'output del modello.

---

## 13. Whitelist mutativa v0.1

Il primo pilot deve essere deliberatamente limitato.

Consentito su un **DWG di laboratorio/copied working file**:

- creare geometria semplice in un layer dedicato CEW-LAB;
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
- eseguire comandi arbitrari `run` forniti dal modello;
- salvare con overwrite;
- operare su file classificati `baseline` o `issued`.

Quando OpenCADStudio richiede una command line per un'operazione ammessa, il Gateway deve costruirla da un template interno tipizzato e validato, non accettarla come stringa libera dal modello.

---

## 14. Protocollo operativo

### PRE

1. classificare il path del documento;
2. verificare che il target sia `working`;
3. calcolare/verificare SHA-256 della sorgente;
4. ottenere `session_id`, `document_id`, revision e capabilities;
5. verificare che non vi sia un comando interattivo sospeso;
6. eseguire audit iniziale;
7. acquisire capture baseline quando la modifica è visiva;
8. creare Changeset;
9. ottenere Approval Receipt umano.

### APPLY

1. rileggere stato;
2. verificare exact match di document identity e revision;
3. verificare digest Changeset/Approval;
4. eseguire solo primitive whitelist;
5. usare `request_id` deterministico per il retry della stessa richiesta;
6. fermarsi alla prima failure;
7. non adattare automaticamente il piano a un errore mutativo.

### POST

1. rileggere le entità attese;
2. misurare le post-condizioni con il kernel;
3. verificare `expected_changed_entities`;
4. rilevare cambi non previsti;
5. acquisire capture/diff;
6. eseguire audit target-aware;
7. produrre Technical Verification Receipt;
8. solo se PASS, consentire `save_verified` su nuovo path;
9. registrare SHA-256 del file salvato;
10. lasciare la promozione CEW a una decisione umana separata.

---

## 15. Fail-closed conditions

Il Gateway deve rifiutare l'operazione almeno quando:

- manca una capability OCS richiesta;
- build/versione OCS non soddisfa la policy;
- il path non appartiene al working root autorizzato;
- il file appartiene a `baseline` o `issued`;
- SHA-256 sorgente non coincide;
- `document_id` non coincide;
- revision non coincide;
- il Changeset è cambiato dopo l'approvazione;
- manca Approval Receipt valida;
- un target entity non esiste più o non è univoco;
- l'operazione non è in whitelist;
- il modello fornisce una command string libera;
- una precondizione CEW non è risolta;
- viene richiesto di trasformare `ND/INC/INF` in fatto senza Decision CEW;
- il CAD è in `waiting_input`, dialogo modale o altro stato non deterministico non previsto;
- la verifica rileva entità modificate fuori dal perimetro atteso;
- audit segnala perdita CEW-rilevante;
- `save_verified` fallisce o rileva mismatch semantico/versione;
- il percorso di output richiede overwrite.

Nessun fallback permissivo.

---

## 16. Threat model

### T01 — Prompt injection nel disegno

Un testo/attributo/layer contiene istruzioni rivolte all'agente.

**Difesa:** tutto il contenuto CAD è dato non fidato; il Gateway non trasforma contenuti del disegno in istruzioni di sistema o policy.

### T02 — Raw command injection

Il modello propone una stringa OCS/CAD arbitraria.

**Difesa:** nessun raw `ocs_execute` o `run` generico è esposto; template interni tipizzati.

### T03 — Stale-state mutation

Il documento cambia dopo la proposta o approvazione.

**Difesa:** exact revision match prima della mutazione; mismatch → nuova proposta/approvazione.

### T04 — Path escape / overwrite

Il modello tenta di scrivere fuori dal workspace o sopra un originale.

**Difesa:** path confinement server-side + no-overwrite + destinazioni generate dal Gateway.

### T05 — Epistemic laundering

Un dato inferito/incerto diventa geometria presentata come documentata.

**Difesa:** propagazione obbligatoria degli stati epistemici e riferimenti CEW; nessuna promozione implicita.

### T06 — Unrelated mutation

Una singola operazione modifica più entità del previsto.

**Difesa:** before/after manifest e guardia `expected_changed_entities`; mismatch → FAIL.

### T07 — Retry duplication

Timeout/reconnect induce duplicazione della mutazione.

**Difesa:** `request_id` stabile per retry identico e receipt locale idempotente.

### T08 — Tool-surface expansion

Una nuova versione OCS espone nuove capacità che l'agente potrebbe usare.

**Difesa:** il Gateway espone solo la propria superficie CEW; capability discovery non equivale ad autorizzazione.

### T09 — Client substitution

Cambio di modello/client modifica il comportamento operativo.

**Difesa:** policy, schema, approval e receipts risiedono nel Gateway, non nel prompt del client.

### T10 — Supply-chain drift

Gateway, OCS o dipendenze cambiano senza qualification.

**Difesa:** version pin/digest dove praticabile, capability digest, qualification separata e receipt che registra le identità operative.

---

## 17. Workspace controllato

Struttura logica raccomandata:

```text
CivilExisting/
├── 00_sources/      # originali immutabili
├── 01_baseline/     # baseline sigillate
├── 02_working/      # sole copie mutabili
├── 03_evidence/     # evidenze e capture
├── 04_changesets/   # proposal + approval
├── 05_audits/       # audit e verification receipts
├── 06_verified/     # save_verified output
└── 07_issued/       # solo promozione umana/formale
```

La struttura fisica del repository potrà differire; ciò che è normativo è la **classificazione delle zone e i diritti**.

Il Gateway deve conoscere le root per configurazione trusted, non apprenderle dal modello.

---

## 18. Integrazione con i client IA

### 18.1 OpenCode — pilot locale preferito

OpenCode supporta server MCP locali e può avviare un comando locale via `stdio`.

Per CEW il client deve collegarsi al **Gateway**, non direttamente a `OpenCADStudio --mcp`.

Schema:

`OpenCode → CEW CAD Gateway → OpenCADStudio --mcp`

Uso consigliato:

- prima qualification locale;
- sviluppo e debugging del Gateway;
- nessuna dipendenza da servizi remoti.

### 18.2 OpenAI API / Responses API

La Responses API supporta server MCP remoti e server locali/private network tramite Secure MCP Tunnel, con policy di approval configurabile.

Schema possibile:

`OpenAI Responses API → Secure MCP Tunnel → CEW CAD Gateway → OpenCADStudio`

Policy v0.1:

- read-only tools: approvazione client configurabile;
- mutating tools: approval del client **sempre** richiesta quando disponibile;
- Approval Receipt CEW comunque obbligatoria e separata.

Riferimento: OpenAI Developers — `MCP servers` / Responses API.

### 18.3 ChatGPT

ChatGPT può essere un'interfaccia futura **solo quando il prodotto/account in uso offre il percorso MCP necessario**.

La disponibilità del prodotto non è un requisito architetturale di CEW-CAD-01. Nessuna regola di sicurezza deve dipendere dalla UI ChatGPT.

### 18.4 Altri client

Qualunque client MCP può essere adottato purché:

- usi esclusivamente il Gateway;
- non abbia un secondo collegamento diretto a OpenCADStudio nello stesso workflow qualificato;
- non possa creare Approval Receipt;
- non possa modificare la policy trusted.

---

## 19. Receipt model

### 19.1 Inspection Receipt

Contiene almeno:

- OCS build/version;
- capability digest;
- session/document identity;
- revision;
- document/source hash;
- audit summary;
- timestamp.

### 19.2 Change Receipt

Contiene almeno:

- Changeset digest;
- Approval Receipt id/digest;
- OCS request ids;
- revision prima/dopo;
- entità dichiarate cambiate;
- errori/warning;
- execution status.

### 19.3 Technical Verification Receipt

Contiene almeno:

- post-condition results;
- kernel measurements;
- unrelated-change result;
- capture/diff refs;
- audit result;
- decisione `PASS | FAIL` tecnica.

### 19.4 Verified Copy Receipt

Contiene almeno:

- input technical receipt;
- output absolute governed path;
- target format/version;
- `save_verified` result;
- output SHA-256;
- semantic verification result;
- stato `CANDIDATE_FOR_HUMAN_REVIEW`.

Nessuna receipt usa lo stato `APPROVED_ENGINEERING_MODEL` o equivalente senza una decisione CEW separata.

---

## 20. Pilot di qualificazione CEW-CAD-01

Il primo pilot non usa un elaborato N12 reale come target mutativo.

### Scenario

1. creare una copia DWG di laboratorio;
2. connettere OpenCADStudio;
3. eseguire inspection e audit senza cambiare revision;
4. identificare 3–5 entità note;
5. ottenere misure kernel;
6. generare un Changeset che crea una semplice geometria sul layer `CEW-LAB`;
7. verificare che senza Approval Receipt la mutazione sia negata;
8. approvare l'esatto digest tramite canale umano;
9. applicare il Changeset;
10. verificare geometria, changed-entity set, capture e audit;
11. produrre una copia con `save_verified`;
12. verificare hash del file originale invariato;
13. produrre tutte le Receipt.

### Negative tests obbligatori

- revision stale;
- Changeset alterato dopo approval;
- tentativo di overwrite;
- path escape;
- raw command injection;
- entità target inesistente;
- testo CAD contenente una falsa istruzione per l'agente;
- `ND` usato come valore geometrico;
- unrelated entity mutation;
- retry identico dopo timeout simulato.

---

## 21. Criteri di accettazione

CEW-CAD-01 pilot è **QUALIFIED** solo se tutte le condizioni seguenti sono dimostrate:

1. **Baseline integrity:** SHA-256 dell'originale invariato.
2. **Read-only purity:** inspection/audit/capture non producono revisione mutativa.
3. **No direct execute:** il client non vede `ocs_execute` generico.
4. **Approval separation:** nessuna mutazione senza Approval Receipt esterna al modello.
5. **Stale guard:** revision mismatch rifiutato prima della mutazione.
6. **Digest binding:** Changeset mutato invalida l'approval.
7. **Whitelist:** operazione non consentita rifiutata prima di raggiungere OCS.
8. **Epistemic guard:** `ND/INC/INF` non diventano implicitamente fatti.
9. **Scope guard:** nessuna entità non prevista risulta modificata.
10. **Kernel verification:** le post-condizioni geometriche sono verificate da OCS, non stimate dal modello.
11. **Visual evidence:** le modifiche visibili hanno capture/diff utilizzabile.
12. **Target-aware audit:** audit non segnala perdita CEW-rilevante per il formato di output.
13. **Verified save:** `save_verified` PASS e SHA-256 registrato.
14. **Prompt-injection resistance:** istruzioni contenute nel CAD non alterano policy o sequenza.
15. **Idempotent retry:** retry identico non duplica l'effetto.
16. **Complete receipts:** catena Inspection → Changeset → Approval → Change → Verification → Verified Copy ricostruibile.

Un solo FAIL mantiene lo stato **NOT QUALIFIED**.

---

## 22. Decisioni demandate al piano di implementazione

Solo dopo approvazione umana di questa specifica e successiva autorizzazione di fase, il piano dovrà scegliere:

- linguaggio/SDK del Gateway;
- libreria MCP server/client;
- meccanismo locale di Approval Receipt;
- canonical JSON serialization e digest rules;
- storage delle Receipt;
- adapter OCS MCP vs `--serve` per test headless;
- sandbox/path confinement concreto su Windows;
- strategia di test e fixture DWG;
- modalità di integrazione CI senza richiedere GUI quando non necessaria.

Queste sono decisioni implementative; non possono indebolire le invarianti della presente specifica.

---

## 23. Stop rule

Dopo la pubblicazione di questa specifica:

- **non implementare** CEW-CAD-01;
- **non modificare** `CEW_CURRENT_STATE.json`;
- **non aprire** un nuovo fronte operativo mentre CEW-B01 resta attivo;
- non collegare un agente a un DWG N12 reale con permessi mutativi;
- non configurare ChatGPT/OpenCode/Codex con accesso diretto a `ocs_execute` come scorciatoia.

Il prossimo atto ammesso è la **revisione umana della specifica**. Solo dopo l'approvazione scritta si potrà redigere un implementation plan; l'esecuzione resterà comunque subordinata a una decisione esplicita sul WIP CEW.

---

## 24. Riferimenti

### CEW / N12

- `CEW_MASTER_PLAN.md`
- `CEW_CURRENT_STATE.json`
- `docs/superpowers/specs/2026-10-13-cew-gate-authority-01-design.md`
- CEW-CONTRACT-01 e relative qualification/assurance receipts

### OpenCADStudio

- <https://github.com/HakanSeven12/OpenCADStudio/blob/main/docs/automation/README.md>
- <https://github.com/HakanSeven12/OpenCADStudio/blob/main/docs/automation/API-SPEC.md>

### Client / MCP

- OpenCode MCP servers: <https://opencode.ai/docs/mcp-servers/>
- OpenAI MCP servers / Responses API: <https://developers.openai.com/api/docs/guides/tools-connectors-mcp>

---

## 25. Sintesi normativa

CEW-CAD-01 separa in modo esplicito quattro responsabilità:

- **IA:** analizza e propone;
- **Gateway:** applica policy, valida e compila operazioni consentite;
- **OpenCADStudio:** esegue e misura la geometria reale;
- **professionista/CEW:** approva, interpreta e promuove conoscenza o elaborati.

La regola finale è:

> **No evidence → no fact. No approved changeset → no mutation. No verification → no verified copy. No human decision → no canonical promotion.**
