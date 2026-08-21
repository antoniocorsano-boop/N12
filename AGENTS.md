# N12 — Agent Entry Point

Questo file è il punto di ingresso obbligatorio per qualunque agente, script o sessione che operi sul repository N12.

## 1. Ordine di lettura obbligatorio

Prima di produrre, modificare o promuovere dati leggere nell'ordine:

1. `knowledge/KNOWLEDGE_MANIFEST.json`
2. `knowledge/CURRENT_STATE.json`
3. `knowledge/ARTIFACT_REGISTRY.csv`
4. `docs/PROTOCOLLO_CANONICO.md`
5. la skill indicata dal manifest per il dominio corrente
6. i registri/evidenze richiamati dal task corrente

Non ricostruire lo stato dalla cronologia della chat, dalla data dei file o dal nome della versione.

## 2. Regola di autorità

Un artefatto è utilizzabile come premessa canonica soltanto se è registrato in `knowledge/ARTIFACT_REGISTRY.csv` con `authority` compatibile con il task e con stato non bloccante.

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

Ogni dato derivato deve poter risalire a uno o più `source/evidence/claim` identificabili. Nessuna inferenza diventa `DOC` per analogia, simmetria o convenienza di modellazione.

## 4. Stato geometrico PT corrente

La geometria PT precedente in `data/canonical/PT_MASTER_CURRENT.csv` è **SUSPENDED come autorità geometrica** finché non viene completato il gate di registrazione raster definito in:

- `data/canonical/PT_PIXEL_REGISTRATION_GATE_v1.csv`
- `skills/pt-raster-grid-reconstructor/SKILL.md`

Per la TAV-02S il metodo corrente è:

`centri/sagome osservati sul raster -> quote documentali -> rete metrica -> supporti fisici -> travi documentate -> intersezioni trave-faccia -> nodi analitici -> overlay -> nuovo Master`.

È vietato usare coordinate X/Y del vecchio Master come prova della loro stessa correttezza.

## 5. Regola sostegno/nodo

`1 sostegno fisico != necessariamente 1 nodo analitico`.

I pilastri-setti e i sostegni estesi restano geometrie fisiche. Se travi differenti incidono lo stesso sostegno in punti differenti, creare nodi analitici distinti collegati allo stesso `support_id` e alle rispettive `face_id`.

## 6. Regola di continuità

Ogni sessione deve terminare aggiornando, quando necessario:

- artefatto specialistico prodotto;
- ledger/registro di provenienza;
- `knowledge/ARTIFACT_REGISTRY.csv` se nasce o cambia ruolo un artefatto;
- `knowledge/CURRENT_STATE.json` se cambia gate, residuo prioritario o prossimo passo;
- `knowledge/KNOWLEDGE_MANIFEST.json` solo quando cambia l'architettura della conoscenza o il set di entrypoint.

Non aggiornare un Master sospeso per semplice continuità: aggiornare prima claim/evidenze e rispettare il gate del dominio.

## 7. Validazione obbligatoria

Prima di dichiarare completato un avanzamento eseguire:

`python scripts/validate_knowledge_system.py`

Per il PT raster eseguire inoltre:

`python skills/pt-carpentry-reader/runner.py validate`

`python skills/pt-raster-grid-reconstructor/runner.py validate`

Un controllo automatico `PASS` valida struttura, registri e contratti macchina; non sostituisce i gate semantici/visuali esplicitamente richiesti dalle skill.

## 8. Principio anti-ripartenza

Prima di rifare un'attività:

1. interrogare manifest e registry;
2. cercare l'artefatto o claim già esistente;
3. verificare se è `CURRENT`, `SUSPENDED`, `HISTORICAL_ONLY` o `SUPERSEDED`;
4. riutilizzare ciò che è rivalidato;
5. riaprire soltanto il claim coinvolto nel conflitto, non l'intero lavoro.

L'assenza di memoria nella sessione non equivale ad assenza di informazione nel repository.