# Repository Memory Protocol — N12

## Scopo

Garantire che elaborati, decisioni, fonti, derivati, stato di avanzamento e residui siano sempre recuperabili dal repository da parte dell'utente e di qualunque agente, senza dipendere dalla continuita' di una chat.

## Architettura della memoria

### 1. Bootstrap
`AGENTS.md` e' il punto di ingresso obbligatorio.

### 2. Stato operativo
`memory/PROJECT_STATE.md` contiene lo snapshot sintetico corrente: obiettivo, baseline, decisioni canoniche, prossima azione.

### 3. Fonti immutabili
`memory/SOURCE_REGISTRY.csv` contiene le fonti originali con `commit:path`, blob SHA, evidenza e disponibilita'. Una fonte e' considerata reperibile anche se non e' materialmente presente nel ramo corrente, purché esista un riferimento Git immutabile valido.

### 4. Elaborati
`memory/ARTIFACT_INDEX.csv` e' l'indice unico degli elaborati SOURCE / DERIVED / CANONICAL / QA / MODEL / REPORT. Ogni voce dice dove si trova o come rigenerarla.

### 5. Residui
`memory/OPEN_RESIDUALS.csv` separa i problemi aperti dai dati affidabili. I residui non bloccanti non devono interrompere il ciclo globale.

## Stati degli elaborati

- `CANONICAL`: elaborato corrente di riferimento.
- `ACTIVE`: elaborato valido in uso, non necessariamente definitivo.
- `RECOVERY_AID`: materiale storico utile ma non canonico.
- `SUPERSEDED`: sostituito, mantenuto per audit.
- `AT_RISK`: esiste solo in chat/runtime o non ha ancora recupero deterministico.
- `ARCHIVED`: mantenuto esclusivamente per storico.

## Regola binaria

Un file binario e' persistentemente gestito solo se:

1. e' versionato nel repository; oppure
2. e' puntato da un riferimento Git immutabile; oppure
3. puo' essere rigenerato deterministicamente da fonti versionate e la ricetta e' registrata.

`/mnt/data`, allegati chat e immagini generate non sono storage permanente.

## Naming

Gli elaborati persistenti devono avere identificatore stabile e versione, ad esempio:

`TAV05_ETABS_wide_support_offsets_QA_v2.png`

L'indice conserva anche il rapporto di supersessione, se presente.

## Provenienza minima

Ogni derivato deve dichiarare:

- fonte/i;
- operazione di produzione;
- scala/rendering quando pertinente;
- commit dei dataset usati;
- evidence status;
- eventuale confidence;
- stato del ciclo.

## Checkpoint atomico

Un'attivita' non si considera realmente conclusa finche' non sono aggiornati, se applicabili:

1. dato/elaborato prodotto;
2. `ARTIFACT_INDEX.csv`;
3. `PROJECT_STATE.md`;
4. `OPEN_RESIDUALS.csv`;
5. commit Git.

La risposta in chat e' un resoconto del checkpoint, non il checkpoint stesso.

## Recupero di un elaborato

Quando un agente non trova un file:

1. legge `ARTIFACT_INDEX.csv`;
2. controlla `SOURCE_REGISTRY.csv`;
3. segue commit/path/blob SHA;
4. controlla storico e artefatti `RECOVERY_AID`;
5. rigenera se esiste ricetta;
6. soltanto alla fine chiede una nuova copia all'utente.

## Regola strutturale N12

La memoria del repository non sostituisce la gerarchia delle evidenze. Conservare un'informazione non la rende `DOC`. Ogni dato mantiene il proprio stato `DOC / MIS / RIF / INF / ND` e la propria provenienza.

## Obiettivo evolutivo

Portare progressivamente a zero le righe `AT_RISK` dell'indice artefatti. I render e le immagini QA utili alla prosecuzione del lavoro devono essere archiviati oppure resi riproducibili con script/versioni di input registrate.
