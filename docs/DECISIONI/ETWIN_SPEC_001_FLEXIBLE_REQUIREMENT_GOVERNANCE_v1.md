# ETWIN-SPEC-001 — Governo flessibile dei requisiti eTwin

**Data:** 2026-08-28  
**Stato:** `ACCEPTED`  
**Ammissione:** registrata in `automation/PRODUCT_DECISION_REGISTER_v1.json`  
**Effetto:** convenzione di classificazione dei requisiti eTwin; nessuna promozione di prodotto o engineering authority  
**Ambito:** classificazione e gestione evolutiva dei requisiti eTwin  
**Non modifica:** authority CEW, N12 engineering authority, programma A0→Z0, Human System, promotion semantics

## 1. Problema

Una specifica tecnica può diventare dannosa in due modi opposti:

1. se è troppo rigida, congela decisioni di interfaccia, implementazione o organizzazione prima che l'uso reale le abbia verificate;
2. se è troppo fluida, consente di cambiare implicitamente boundary di autorità, isolamento o provenienza senza una decisione tracciata.

La soluzione non è rendere tutto modificabile. È distinguere **che cosa può evolvere facilmente e che cosa richiede una revisione governata**.

## 2. Decisione

I requisiti eTwin possono essere annotati con una delle seguenti classi, subordinate alla gerarchia documentale L0–L7 già vigente.

| Classe | Significato | Regola di modifica |
|---|---|---|
| `INVARIANT` | boundary di autorità, isolamento, sicurezza, provenienza o non-promozione | modifica solo con decisione materiale, revisione del contratto governante e nuovi gate |
| `SPECIFIED` | scelta corrente necessaria per interoperabilità o coerenza del prodotto | può evolvere in modo compatibile con versione/decisione appropriata |
| `OPEN` | decisione deliberatamente non chiusa | il lavoro dipendente resta bloccato dove la decisione è necessaria |
| `EXPERIMENTAL` | soluzione usata per apprendere senza authority | può essere sostituita; non diventa canonica per uso o anzianità |
| `DOMAIN_OWNED` | semantica appartenente a CEW, N12 o altra disciplina/prodotto specialistico | eTwin la riferisce attraverso il contratto proprietario; non la ridefinisce |

## 3. Precedenza

Questa classificazione **non crea un nuovo livello di authority**.

La precedenza resta:

`PRODUCT_GOVERNANCE_MANIFEST → L0 → L1 → L2 → L3 → admitted current state/receipts`.

Le classi servono a rendere esplicito il grado di stabilità di un requisito dentro il livello che già lo possiede.

Esempi:

- `project_id hard boundary` può essere `INVARIANT` nel contratto eTwin;
- forma della Home può essere `OPEN` o `EXPERIMENTAL`;
- schema operativo di un task può essere `SPECIFIED` dopo HVA;
- `EvidenceRegion` in Structures è `DOMAIN_OWNED` da CEW;
- una visualizzazione 3D è `EXPERIMENTAL` finché non ha una capability/acceptance contract ammessa.

## 4. Regola fondamentale

> **La flessibilità è ammessa dentro i boundary, non sui boundary.**

Sono quindi liberamente iterabili, entro i contratti applicabili:

- disposizione e linguaggio dell'interfaccia;
- implementazione tecnica;
- strategia di cache non autoritativa;
- organizzazione interna di agenti non promotori;
- forma di proiezioni/read-model;
- workflow ergonomico finché non cambia authority.

Non possono essere modificati per convenienza implementativa:

- isolamento Project/Discipline/Scope;
- ownership eTwin/CEW/N12;
- provenienza e identità immutabile delle fonti;
- distinzione candidate/evidence/claim/engineering truth;
- separazione deployment/HVA/promotion;
- authority professionale umana richiesta;
- divieto di promozione automatica da AI/OCR/vector/solver/read-model.

## 5. Stati e transizioni

### `OPEN → SPECIFIED`

Richiede problema e alternative dichiarate, evidenza sufficiente, decisione tracciata quando materialmente rilevante e aggiornamento del contratto proprietario.

### `EXPERIMENTAL → SPECIFIED`

Richiede evidenza che l'esperimento risolve il bisogno dichiarato, conformità agli `INVARIANT`, regression/safety test applicabili, eventuale HVA e ammissione esplicita. L'uso prolungato non vale come promozione.

### `SPECIFIED → nuova forma compatibile`

Può usare una revisione minore se non cambia il significato contrattuale né i boundary.

### modifica di `INVARIANT`

È una decisione architetturale/materiale e richiede almeno decision record, impatto su authority/sicurezza/dati, piano di migrazione, regressioni, revisione L1/L2 pertinente e nuova evidenza di acceptance.

### `DOMAIN_OWNED`

Non ha transizione autonoma in eTwin. Cambia solo quando cambia il contratto della verticale proprietaria e l'adapter/reference contract eTwin viene poi riconciliato.

## 6. Fail-closed

Un requisito `OPEN` non può essere implementato scegliendo silenziosamente una delle opzioni se la scelta produce effetti persistenti o autoritativi.

Un artefatto `EXPERIMENTAL` non può essere assunto come source of truth, creare canonical write, soddisfare un gate di promozione salvo ammissione espressa dal gate, né ridefinire una semantica `DOMAIN_OWNED`.

## 7. Versionamento

La convenzione è:

- `PATCH` — chiarimento senza cambio semantico;
- `MINOR` — estensione compatibile o chiusura governata di un `OPEN`;
- `MAJOR` — cambio di boundary, authority, isolamento o significato persistente.

Il versionamento documentale effettivo resta soggetto al `DOCUMENTATION_AUTHORITY_MODEL_v1` e al manifest corrente.

## 8. Relazione con la specifica discovery

Le classi derivano dal lavoro di discovery persistito sul ramo storico `docs/etwin-system-spec-v1`, ma **questa decisione non ammette quel ramo come contratto L1**.

La matrice SP-1 usa le classi per distinguere requisiti già coperti da eTwin v2, requisiti nuovi realmente utili, aspetti `OPEN`, elementi che duplicano CEW/N12 e prototipi da conservare come `EXPERIMENTAL`.

## 9. Conseguenze dell'ammissione

L'ammissione di ETWIN-SPEC-001:

1. non modifica `ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2` come current L1;
2. non modifica capability ownership eTwin/CEW/N12;
3. non modifica il programma A0→Z0;
4. non rende current authority la branch discovery `docs/etwin-system-spec-v1`;
5. consente alle future specifiche/capability contract eTwin di dichiarare esplicitamente il proprio grado di stabilità;
6. impone fail-closed per `OPEN` ed `EXPERIMENTAL` quando una scelta avrebbe effetto persistente o autoritativo.

**Decisione:** `ACCEPTED — NON_PROMOTIVE`.