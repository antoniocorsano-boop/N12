# N12 — Source Sufficiency Audit for CEW-CONTRACT-01

**Purpose:** verificare quali voci del patrimonio N12 possono già fungere da Source/Evidence localizzabile per la qualifica del contratto, senza inventare locator o promuovere dati secondari a fonte originale.

## Esito sintetico

Il repository contiene `docs/REGISTRO_MASTER.md`, `docs/PROTOCOLLO_CANONICO.md`, `archive/ARTEFATTI_STORICI.md` e `data/canonical/telaio_5.csv`. L'inventario storico dichiara l'esistenza di DXF/CSV e altri artefatti originali, ma tali file originali non sono presenti nell'albero corrente del repository. Di conseguenza, molte voci sono verificabili come **registrate/canoniche di secondo livello**, ma non ancora come Evidence localizzata sulla fonte originale.

## Audit minimo richiesto

| Registro ID | Fonte dichiarata | File reperibile nel repository corrente | Locator interno verificabile | Stato epistemico | Esito / limite |
|---|---|---:|---:|---|---|
| GEO-004 | `ABACO_TOPOLOGICO_TAV5_v11.csv` nel pacchetto DXF strutturale v25 | No; è solo inventariato in `archive/ARTEFATTI_STORICI.md` | No | `DOC-ARTEFATTO` | `UNRESOLVED_LOCATOR`: il file originale non è nel repository corrente. |
| GEO-005 | registri storici + riferimenti a ID superiori a N057 | No, non come artefatti sorgente direttamente ispezionabili | No | `DOC/INF-controllata` | `UNRESOLVED_LOCATOR`: si conserva la distinzione tra fatto documentale e inferenza controllata, ma manca il locator sorgente. |
| BEAM-006 | relazione di calcolo / v17; dato anche in `data/canonical/telaio_5.csv` | **Parziale**: il CSV canonico è presente; la relazione di calcolo originale non è presente | Sì sul dataset canonico (`T5,G5`), no sulla fonte originale | `DOC` | Il CSV è supporto canonico secondario; per la catena Source→Evidence originale resta `UNRESOLVED_LOCATOR`. |
| SEC-002 | stato M0 v18 | No artefatto sorgente separato reperibile | No | `ND` | `UNRESOLVED_LOCATOR`; il valore deve restare assente, senza default. |
| M0G-002 | livelli / quote Z definitive non congelate | Nessuna fonte che congeli il valore | Non applicabile | `ND` | Mancanza conoscitiva reale: nessuna Evidence da inventare. |
| MAT-001 | calcestruzzo/acciaio da documentare/indagare | Nessuna fonte materiale/prova presente | Non applicabile | `ND` | Mancanza conoscitiva reale: nessun materiale canonico può essere assunto. |

## Fonti di secondo livello effettivamente disponibili

1. `docs/REGISTRO_MASTER.md` — registra ID, dato/stato, evidenza dichiarata e stato epistemico.
2. `docs/PROTOCOLLO_CANONICO.md` — definisce gerarchia fonte→estrazione→riconciliazione→dato canonico e divieti di promozione implicita.
3. `archive/ARTEFATTI_STORICI.md` — inventaria il pacchetto DXF strutturale v25 e conferma che gli artefatti originali devono restare immutabili.
4. `data/canonical/telaio_5.csv` — dataset canonico corrente con il record `T5,G5,1-7,C2-C7,19.20,20x45,DOC,relazione_calcolo_v17`.

## Conseguenze per il gate

- La rappresentabilità concettuale può essere esercitata su fixture N12, ma resta `REVIEW_REQUIRED` finché tutti i casi obbligatori non sono materializzati.
- La provenienza end-to-end fino alla **Source originale** è `BLOCKED_SOURCE` per i casi che dipendono da artefatti storici non presenti.
- Un Conflict reale, una Relationship incerta e una revisione storica non possono essere dichiarati solo sulla base di assenza o inferenza: se non emergono fonti contraddittorie/localizzabili, restano `BLOCKED_SOURCE`.
- I casi `ND` possono essere qualificati negativamente: il contratto deve saper conservare l'assenza senza completarla.

## Regola fail-closed

`UNRESOLVED_LOCATOR` significa che la voce è nota attraverso il Registro Master/inventario, ma non è ancora possibile costruire una Evidence localizzata sulla fonte originale. Nessun locator viene sintetizzato.
