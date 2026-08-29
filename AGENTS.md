# AGENTS.md — N12 repository memory bootstrap

Questo file e' il punto di ingresso OBBLIGATORIO per qualunque agente, sessione o strumento che lavori sul repository N12.

## Regola zero

La chat NON e' memoria canonica. Git e' la fonte di verita' dello stato consolidato.

Prima di analizzare, modificare o ricostruire qualsiasi elaborato, leggere nell'ordine:

1. `memory/PROJECT_STATE.md`
2. `memory/ARTIFACT_INDEX.csv`
3. `memory/SOURCE_REGISTRY.csv`
4. `memory/OPEN_RESIDUALS.csv`
5. i dataset richiamati da `PROJECT_STATE.md`
6. `docs/GRAMMATICA_DISEGNO_STRUTTURALE_CA.md` quando si lavora sulle tavole strutturali

E' vietato chiedere all'utente di ricaricare o ricreare un elaborato prima di aver controllato questi registri e la storia Git indicata nei relativi `source_ref`.

## Protocollo di continuita'

Ogni nuova informazione utile deve essere registrata PRIMA di passare al passo successivo.

Ogni artefatto o dato deve avere almeno:
- `artifact_id` o identificatore stabile;
- percorso corrente o riferimento Git immutabile;
- tipo: SOURCE / DERIVED / CANONICAL / QA / MODEL / REPORT;
- stato evidenza: DOC / MIS / RIF / INF / ND;
- stato ciclo: ACTIVE / CANONICAL / SUPERSEDED / RESIDUAL / ARCHIVED;
- `source_ref` o lista delle fonti;
- versione e commit quando disponibile;
- istruzioni di rigenerazione se il file binario non e' presente nel ramo corrente.

## Politica sugli elaborati binari

Un PDF, raster, DXF, immagine QA o altro elaborato binario NON deve esistere soltanto nella chat o nel runtime temporaneo.

Per ogni binario devono essere garantite almeno una delle seguenti condizioni:
1. file versionato direttamente nel repository; oppure
2. riferimento Git immutabile `commit:path + blob_sha` a una copia gia' versionata; oppure
3. ricetta deterministica di rigenerazione da una fonte versionata, registrata nell'indice artefatti.

Se nessuna delle tre condizioni e' soddisfatta, l'elaborato e' classificato `AT_RISK` e va messo in sicurezza prima di proseguire.

## Separazione fonte / derivato

Le fonti originali non vengono sostituite dagli elaborati derivati. Ogni derivato deve dichiarare esplicitamente la fonte e il metodo di produzione.

Gli stati DOC, MIS, RIF, INF, ND non vanno promossi per analogia. Un residuo non deve bloccare l'avanzamento globale: va registrato in `memory/OPEN_RESIDUALS.csv` con una prossima azione risolvibile.

## Checkpoint di fine sessione

Prima di chiudere una sessione che ha prodotto lavoro sostanziale:
- aggiornare `memory/PROJECT_STATE.md`;
- registrare nuovi/sostituiti elaborati in `memory/ARTIFACT_INDEX.csv`;
- aggiornare i residui;
- riportare commit e percorsi nel checkpoint;
- non lasciare come unico deposito file in `/mnt/data`, allegati chat o descrizioni testuali.

## Regola di recupero

Quando un file sembra mancante:
1. cercare in `ARTIFACT_INDEX.csv`;
2. seguire `repo_path`, `historical_ref` o `source_ref`;
3. cercare nella storia Git/branch/commit specificati;
4. rigenerare solo se il registro lo prevede;
5. chiedere all'utente una nuova copia soltanto dopo il fallimento documentato dei passaggi precedenti.
