# eTwin — Registro genealogico e riconciliazione SP-0 v1

**Data osservazione:** 2026-08-28  
**Stato:** `SP0-G — PASS_WITH_FINDINGS`  
**Effetto di autorità:** `NONE`  
**Promozione autorizzata:** `false`  
**Ramo di lavoro:** `docs/etwin-spec-reconciliation-sp0-v1`  
**Baseline osservata:** `79b6ddb28205f4151d23f330218724fc96d4cc20`

## 1. Scopo

Questo registro ricostruisce la genealogia reale di eTwin nel repository `antoniocorsano-boop/N12` e impedisce che piani, prototipi, vecchi strumenti N12 o nuove specifiche nate su rami storici vengano scambiati per authority corrente.

SP-0 non cambia il programma eTwin, CEW o l'authority ingegneristica N12. Classifica ciò che esiste e stabilisce da quale linea deve proseguire la riconciliazione.

## 2. Catena di authority corrente

La precedenza osservata è:

1. `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json` — manifest machine-readable canonico;
2. `docs/GOVERNANCE/AI_NATIVE_PRODUCT_AGENCY_OPERATING_MODEL_v1.md` — governo di prodotto;
3. `docs/GOVERNANCE/DOCUMENTATION_AUTHORITY_MODEL_v1.md` — gerarchia documentale L0–L7;
4. `docs/GOVERNANCE/CEW_ETWIN_PRODUCT_FAMILY_CAPABILITY_MAP_v1.md` — confine eTwin / CEW / N12;
5. `docs/PROGRAM/ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2.md` — contratto L1 corrente per la futura promozione eTwin;
6. `docs/PROGRAM/ETW_AGENTIC_DEVELOPMENT_ORCHESTRATION_v2.md` — orchestrazione corrente per la futura promozione;
7. `automation/ETW_PROGRAM_MANIFEST_v1.json`, `automation/ETW_PROGRAM_STATUS_v1.json`, `automation/ETW_DEVELOPMENT_QUEUE_v1.json`, `automation/ETW_HUMAN_GATE_STATE_v1.json` — stato/esecuzione L3/L4;
8. `knowledge/CURRENT_STATE.json` + artefatti ingegneristici governati — authority ingegneristica N12.

**Regola:** eTwin possiede il contesto multi-progetto/multi-disciplina; CEW possiede il prodotto specialistico Structures / Existing Structures; N12 conserva i propri fatti e decisioni ingegneristiche.

## 3. Topologia Git osservata

### 3.1 Linea di programma corrente

- ramo: `work/etw-platform-extension-program-v1`;
- HEAD osservato: `79b6ddb28205f4151d23f330218724fc96d4cc20`;
- PR #103: programma eTwin/orchestratore, ancora aperta;
- PR #104: `ETW-A0` preparata, `PREPARED_BLOCKED_PROMOTION`, head `36b101ed32cb61263609c84f17b740c2446be9c1`;
- PR #105: governance AI-native/Human Acceptance v2, integrata nella linea di programma;
- PR #109: runtime Render Candidate/HVA, integrata nella linea di programma;
- PR #110: CEW B1.8 Human-Centred Acceptance v2 su runtime stabile, aperta sopra la stessa linea.

### 3.2 Default branch

`main` è osservato a `8d2b32a0f7913227b0aa757f27c1ebb7b05180c5` e contiene il trigger repository-wide per i candidati CEW. Non coincide con la linea stacked completa del programma eTwin.

### 3.3 Linea strutturale storica

Il ramo `feat/structural-professional-workspace-r1` è osservato a `dd5b48e64cb63eb5556d8bcc033b63cdc2bb302e` ed è la genealogia da cui provengono molti strumenti ETW/N12 storici.

La branch di discovery `docs/etwin-system-spec-v1`, creata da quella linea e arrivata a `51cd3d265f142665c4f83da972529e37751cf9a0`, è quindi **fuori dalla corrente catena L0/L1**. La comparazione con `main` mostra divergenza; non deve essere integrata come contratto di piattaforma per semplice recenza.

## 4. Classificazione degli artefatti

| Famiglia | Esempi | Classificazione SP-0 | Regola |
|---|---|---|---|
| Governo corrente | `PRODUCT_GOVERNANCE_MANIFEST`, modelli L0, capability map | `CURRENT_AUTHORITY` | prevale secondo il Documentation Authority Model |
| Programma eTwin v2 | `ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2`, orchestrazione v2 | `CURRENT_L1/L3` | unica base per futura promozione |
| Preparazione A0 v1 | programma/orchestrazione v1, receipt A0, PR #104 | `HISTORICAL_PREPARATION_EVIDENCE` | preservare; revalidare, non riscrivere |
| N12 engineering | `knowledge/CURRENT_STATE.json`, canonici governati, decisioni tecniche | `DOMAIN_OWNED` | eTwin può riferire, non ridefinire |
| ETW document engine storico | `.asw/plans/etw1-*`, `.asw/plans/etw2-*`, `model/etwin/*` | `HISTORICAL_DOMAIN_TOOL` | riuso possibile solo dietro contract CEW/eTwin corrente |
| Workflow ETW storici | `.github/workflows/etw*` della linea strutturale | `DOMAIN_AUTOMATION` | output non promotivo per piattaforma |
| Artefatti N12 ETW | `docs/FOGLIO_LAVORO/ETW_*`, `etwin_crops/*` | `DOMAIN_EVIDENCE_OR_DERIVED` | mantengono provenienza N12; non diventano schema universale |
| Dashboard strutturale | `docs/FOGLIO_LAVORO/dashboard/*` | `READ_MODEL_ONLY / EXPERIMENTAL` | mai authority; semantica da auditare prima del riuso |
| Specifica discovery 2026-08-28 | branch `docs/etwin-system-spec-v1`, `docs/ETWIN/*` | `L7_DISCOVERY_INPUT` | estrarre delta utili; non sostituire L1 corrente |

## 5. Finding SP-0

### F-SP0-01 — Contratto di piattaforma duplicabile

La specifica discovery definiva nuovamente identità e programma eTwin pur esistendo già `ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2`. Se promossa direttamente avrebbe creato due L1 concorrenti.

**Risoluzione:** la discovery resta L7; i soli requisiti nuovi vengono confrontati e, se validi, ammessi tramite decisione/versionamento nel contratto corrente.

### F-SP0-02 — Duplicazione storica di semantica CEW

`model/etwin/document_engine.py` definisce localmente `EvidenceStatus`, `Claim`, `StructuralEntity`, `DocumentEntityCandidate`, `PropertyResolution` e `VerificationResult`. Il modello corrente assegna invece source/evidence/claim, entità strutturali, stato epistemico e modello canonico a CEW/N12.

**Risoluzione:** classificare il modulo come strumento storico N12/document intelligence. Vietata la generalizzazione automatica a modello dati eTwin.

### F-SP0-03 — Read-model con semantica potenzialmente autoritativa

La dashboard storica è tecnicamente derivata e le azioni della coda di validazione non scrivono il dataset canonico. Tuttavia il contratto TypeScript contiene stati/formule come `VALIDATED` e commenti che possono essere letti come passaggio verso il canonico.

**Risoluzione:** `READ_MODEL_ONLY / EXPERIMENTAL`; SP-1 deve verificare ogni semantica prima di qualsiasi riuso nella piattaforma.

### F-SP0-04 — Tooling documentale riusabile ma domain-bound

Probe, registrazioni geometriche, rendering e crop hanno valore tecnico e in diversi casi esplicitano `no identity promotion`. Sono candidati al riuso, ma solo come servizi/tool sotto l'authority CEW o una futura disciplina ammessa.

### F-SP0-05 — Fingerprint storico non risolvibile

Il riferimento `40e126c01e4ba5966255976a93c329256374626b` dichiarato nel dossier non è risolvibile come commit del repository osservato.

**Risoluzione:** `UNRESOLVED_HISTORICAL_REFERENCE`; nessuna decisione corrente può dipendere da quel fingerprint.

### F-SP0-06 — `main` non rappresenta da solo l'intero programma stacked

Il default branch e la linea eTwin/CEW stacked hanno funzioni diverse. La baseline di riconciliazione deve essere l'HEAD esplicito del programma corrente, non il semplice default branch.

## 6. Decisione di genealogia

Da questo punto:

```text
CURRENT AUTHORITY
PRODUCT_GOVERNANCE_MANIFEST
        ↓
eTwin v2 / CEW current contracts
        ↓
current state + queues + receipts

DISCOVERY / HISTORY
old ETW document engine
old dashboard/read models
old structural workflow artifacts
docs/etwin-system-spec-v1
        ↓
SP-1 conformance/delta review
        ↓
explicit decision + controlled admission only
```

Non viene creato un secondo ciclo SP-0→SP-8 parallelo ad A0→Z0. Le attività SP-0/SP-1 sono un **lavoro di riconciliazione temporaneo** che rientra nel programma eTwin canonico.

## 7. Gate SP0-G

| Criterio | Esito |
|---|---|
| Authority corrente identificata | PASS |
| N12 engineering authority separata | PASS |
| Linea eTwin corrente identificata | PASS |
| Artefatti storici classificati | PASS |
| Specifica discovery classificata | PASS |
| Fingerprint non riproducibili dichiarati | PASS |
| Conflitti silenziosi residui | NONE — i conflitti potenziali sono espliciti |
| Promozione eTwin autorizzata | NO |

**Esito:** `SP0-G — PASS_WITH_FINDINGS`.

**Next admissible work:** `SP-1 — conformance/delta reconciliation` sulla linea `work/etw-platform-extension-program-v1`, senza alterare A0, CEW B1 o N12 engineering authority.