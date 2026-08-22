# N12 — Agent Entry Point

Questo file è il punto di ingresso obbligatorio per qualunque agente, script o sessione che operi sul repository N12.

## 0. Bootstrap e ciclo automatico

Prima di qualunque attività eseguire:

`python scripts/agent_bootstrap.py`

poi:

`python scripts/n12_orchestrator.py status`

Il primo comando restituisce gate, artefatti autorizzati/condizionati/bloccati. Il secondo seleziona il **prossimo work item eleggibile** dalla coda persistente `automation/N12_WORK_QUEUE_v1.json`.

Non scegliere il prossimo task dalla cronologia della chat. Se il report restituisce `READY_FOR_AGENT`, eseguire soltanto la lettura specialistica richiesta dal work item selezionato. Se restituisce `RESIDUAL_REVIEW`, riaprire soltanto il claim/residuo indicato.

Contratto del ciclo:

- `automation/N12_AUTOMATION_CONTRACT_v1.json`
- `automation/N12_WORK_QUEUE_v1.json`
- `docs/N12_AUTOMATED_ANALYSIS_CYCLE_v1.md`
- runner: `scripts/n12_orchestrator.py`

## 1. Ordine di lettura obbligatorio

Prima di produrre, modificare o promuovere dati leggere nell'ordine:

1. `knowledge/KNOWLEDGE_MANIFEST.json`
2. `knowledge/CURRENT_STATE.json`
3. `knowledge/ARTIFACT_REGISTRY.csv` e le patch di registry indicate dal manifest
4. `automation/N12_AUTOMATION_CONTRACT_v1.json`
5. `automation/N12_WORK_QUEUE_v1.json`
6. `docs/PROTOCOLLO_CANONICO.md`
7. la skill indicata dal manifest per il dominio corrente
8. i registri/evidenze richiamati dal work item corrente

Non ricostruire lo stato dalla cronologia della chat, dalla data dei file o dal nome della versione.

## 2. Regola di autorità

Un artefatto è utilizzabile come premessa canonica soltanto se è registrato nel registry effettivo (base + patch indicate dal manifest) con `authority` compatibile con il task e stato non bloccante.

Se un file non è registrato, il suo stato predefinito è `UNREGISTERED_NON_AUTHORITATIVE`.

Gerarchia generale:

`SOURCE_PRIMARY -> OBSERVATION -> CLAIM_VALIDATED -> CANONICAL -> DERIVED_MODEL`

Gli stati `HISTORICAL_ONLY`, `SUSPENDED`, `SUPERSEDED`, `CONFLICT`, `REOPENED`, `TOMBSTONE` non possono alimentare nuovi dati canonici salvo rivalidazione esplicita.

## 3. Evidenza e provenienza

Mantenere separati:

- `DOC`: dato documentale;
- `MIS`: misurato;
- `RIF`: riferito;
- `INF`: inferito;
- `INC`: incerto;
- `ND`: non disponibile.

Ogni dato derivato deve poter risalire a uno o più `source/evidence/claim` identificabili. Nessuna inferenza diventa `DOC` per analogia, simmetria, ripetizione fra piani o convenienza di modellazione.

## 4. Stato geometrico corrente

La geometria del piano terra è stata rigenerata attraverso i gate G1-G9 ed è corrente in:

`data/canonical/PT_MASTER_CURRENT.csv`

Il precedente stato storico è preservato nello snapshot indicato dal manifest. Non riaprire G1-G9 salvo evidenza primaria diretta in conflitto con uno specifico claim.

Il dominio corrente è la **geometria verticale e la carpenteria per singolo impalcato**. Sono già stabiliti:

- sistema XY comune dei piani con provenienza esplicita;
- livelli Z relativi G1-G5;
- 38 linee di sostegno a G1;
- 34 identità originarie fino a G4;
- 25 identità presenti in copertura;
- `a-b-c-d` terminano dopo G1;
- `1,8,9,16,17,24,31,32,33` non sono presenti sulla carpenteria di copertura.

Regola corrente: **leggere sezioni e travi indipendentemente su TAV-03S, TAV-04S, TAV-05S e TAV-06S**. È vietato copiare verso l'alto sezioni o topologia del PT.

## 5. Regola sostegno/nodo

`1 sostegno fisico != necessariamente 1 nodo analitico`.

I pilastri-setti e i sostegni estesi restano geometrie fisiche. Se travi differenti incidono lo stesso sostegno in punti differenti, creare nodi analitici distinti collegati allo stesso `support_id` e alle rispettive `face_id`.

## 6. Ciclo e gate

Il ciclo standard è:

`bootstrap -> source ready -> specialist reading -> metric/topology checks -> crosscheck -> promotion gate -> state advance -> next item`

Regole di avanzamento:

- `PASS_ADVANCE`: avanzare;
- `PASS_WITH_WATCH_ADVANCE`: avanzare mantenendo il WATCH;
- `READY_FOR_AGENT`: eseguire il task specialistico selezionato;
- `RESIDUAL_REVIEW`: isolare il residuo, non bloccare attività indipendenti;
- `CONFLICT_STOP`: riaprire il claim minimo;
- `FAIL_STOP`: nessuna promozione.

L'automazione deterministica non può sostituire la lettura semantica delle tavole. In assenza di un executor agentico autorizzato deve fermarsi a `READY_FOR_AGENT`.

## 7. Regola di continuità

Ogni sessione/ciclo deve terminare aggiornando, quando necessario:

- artefatto specialistico prodotto;
- ledger/audit di provenienza;
- registry o patch se nasce/cambia ruolo un artefatto;
- `automation/N12_WORK_QUEUE_v1.json` se cambia lo stato del work item o si libera una dipendenza;
- `knowledge/CURRENT_STATE.json` se cambia gate, residuo prioritario o prossimo passo;
- `knowledge/KNOWLEDGE_MANIFEST.json` solo quando cambia l'architettura della conoscenza o il set di entrypoint.

Non promuovere un dato soltanto per continuità con il piano precedente.

## 8. Validazione obbligatoria

Prima di dichiarare completato un avanzamento eseguire:

`python scripts/validate_knowledge_system.py`

`python scripts/n12_orchestrator.py validate`

Per i domini carpenteria/raster eseguire inoltre, quando pertinenti:

`python skills/pt-carpentry-reader/runner.py validate`

`python skills/pt-raster-grid-reconstructor/runner.py status`

Un controllo automatico `PASS` valida struttura, registri e contratti macchina; non sostituisce i gate semantici/visuali esplicitamente richiesti.

## 9. Principio anti-ripartenza

Prima di rifare un'attività:

1. interrogare manifest, stato, registry e coda;
2. cercare l'artefatto o claim già esistente;
3. verificare se è `CURRENT`, `SUSPENDED`, `HISTORICAL_ONLY`, `SUPERSEDED`, `RESIDUAL` o `CONFLICT`;
4. riutilizzare ciò che è rivalidato;
5. riaprire soltanto il claim coinvolto nel conflitto, non l'intero lavoro.

L'assenza di memoria nella sessione non equivale ad assenza di informazione nel repository.
