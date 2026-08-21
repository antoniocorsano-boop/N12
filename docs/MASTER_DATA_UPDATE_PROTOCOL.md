# Protocollo permanente di aggiornamento dei dati canonici

## Stato

SUPERSEDE la precedente regola “Master unico sempre autoritativo”.

Il sistema corrente è governato da:

`AGENTS.md -> knowledge/KNOWLEDGE_MANIFEST.json -> knowledge/CURRENT_STATE.json -> knowledge/ARTIFACT_REGISTRY.csv -> gate/skill di dominio`.

## Regola vincolante

Ogni nuova informazione utile deve essere registrata nello stesso ciclo di lavoro con:

- artefatto/evidenza;
- provenienza;
- stato `DOC/MIS/RIF/INF/INC/ND` quando applicabile;
- stato di validazione;
- eventuale claim nel ledger;
- ruolo/autorità dell'artefatto nel registry;
- eventuale aggiornamento dello stato di ripresa.

## Master di dominio

Un Master è una **vista canonica derivata e gated**, non automaticamente la fonte superiore a tutte le evidenze.

Un Master può essere:

- `CURRENT` — ammesso dal gate del dominio;
- `SUSPENDED` — conservato ma non utilizzabile come autorità per la proprietà sospesa;
- `HISTORICAL_ONLY` — solo provenienza/storia;
- `SUPERSEDED` — sostituito da una versione meglio supportata.

È vietato usare un valore contenuto in un Master sospeso per confermare lo stesso valore.

## Separazione delle proprietà

Coordinate, identità, sezioni, orientamenti, armature, travi, fondazioni, materiali e carichi hanno provenienza e gate separabili.

La sospensione della geometria XY di un elemento non annulla automaticamente una sezione documentata indipendentemente. Analogamente, una sezione non documentata non invalida automaticamente la posizione raster osservata.

## Procedura obbligatoria

1. leggere `AGENTS.md` e lo stato corrente;
2. individuare nel registry gli artefatti autorizzati per il task;
3. acquisire/analizzare l'evidenza primaria;
4. aggiornare osservazioni e claim senza sovrascrivere la storia;
5. applicare il gate specifico della skill;
6. aggiornare un Master solo se il gate autorizza la promozione;
7. aggiornare `knowledge/ARTIFACT_REGISTRY.csv` se cambia ruolo/stato di un artefatto;
8. aggiornare `knowledge/CURRENT_STATE.json` se cambia il punto di ripresa;
9. eseguire `python scripts/validate_knowledge_system.py`.

## Stato PT corrente

`data/canonical/PT_MASTER_CURRENT.csv` è attualmente `SUSPENDED` come autorità delle coordinate geometriche PT.

L'output autorizzato del gate corrente è `data/canonical/PT_PIXEL_SUPPORT_REGISTRY_v1.csv`, ottenuto direttamente dal raster TAV-02S senza usare le vecchie coordinate X/Y come input.

## Principio di continuità

La memoria tecnica persistente non è un singolo CSV ma il sistema coordinato di fonti, osservazioni, claim, registri canonici, manifest, stato e skill.

Un agente deve riaprire il minimo insieme di claim coinvolti in un conflitto, non ricostruire un intero dominio già documentato.