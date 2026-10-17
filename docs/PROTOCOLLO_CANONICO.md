# Protocollo canonico N12

## 1. Scopo

Evitare dispersione, duplicazioni e ricostruzioni non verificabili durante la determinazione del modello strutturale dell'edificio esistente. Il sistema deve operare in modo progressivamente autonomo, mantenendo sempre separati fatto documentale, misura, informazione riferita, inferenza tecnica e dato non disponibile.

## 2. Fonti e stati

Ogni informazione entra nel patrimonio canonico con:

- identificatore stabile;
- oggetto strutturale o dominio interessato;
- valore/fatto;
- unità se applicabile;
- fonte;
- posizione nella fonte;
- stato `DOC/MIS/RIF/INF/INC/ND`;
- versione/data di introduzione;
- eventuale versione di correzione o superamento;
- nota tecnica.

Regola per gli apporti dell'utente:

- una nuova informazione tecnica riferita dall'utente entra come `RIF_USER_QUALIFIED` e viene persistita prima di essere usata come premessa operativa;
- se l'utente sta trascrivendo direttamente un contenuto leggibile di una fonte originale, il dato può diventare `DOC` solo conservando la traccia `HUMAN_QUALIFIED_VISUAL_READ` e il riferimento preciso alla fonte;
- un successivo fatto documentale non cancella il dato riferito precedente: lo conferma, lo supera o lo pone in conflitto mantenendo la storia della decisione.

## 3. Gerarchia e ciclo di lavoro

Gerarchia informativa:

1. fonte originale primaria;
2. estrazione grezza/raster/render registrato;
3. lettura o misura con provenienza;
4. riconciliazione tra fonti;
5. dato canonico;
6. oggetto del modello;
7. verifica nel modello;
8. eventuale revisione del dato canonico con tracciabilità.

Ciclo autonomo obbligatorio per ogni nuovo work item:

`SCAN FONTI -> ESTRAI -> CLASSIFICA EVIDENZA -> CROSS-CHECK TRA DOMINI -> CERCA CONTRADDIZIONI -> REGISTRA RESIDUI -> VALIDA GATE -> PERSISTI -> PROSEGUI`

Il sistema deve cercare nel repository e nelle fonti già disponibili prima di chiedere chiarimenti all'utente. L'utente viene coinvolto quando permane un'ambiguità reale, quando una lettura umana qualificata è più affidabile del parsing automatico o quando due evidenze autorevoli sono incompatibili.

## 4. Divieti

- non completare dati mancanti per simmetria, ricorrenza o analogia senza registrarli come `INF`;
- non trasformare una pratica progettuale ricorrente in prova di un valore specifico;
- non sovrascrivere una correzione senza conservare provenienza e stato precedente;
- non usare uno ZIP storico come stato canonico corrente;
- non confondere carichi storici della relazione con i carichi normativi o con i carichi effettivi dello stato costruito;
- non assegnare automaticamente materiali, LC o FC senza evidenza;
- non dedurre armature dalle sole piante architettoniche;
- non ignorare una geometria architettonica solo perché non compare nello schema di calcolo;
- non fondere elementi omonimi o della stessa lunghezza appartenenti a livelli/sottosistemi differenti senza source binding.

## 5. Modello e fronti

Baseline geometrica/topologica: `M0-G` chiusa e congelata. Riapertura ammessa solo con procedura `M0G-REOPEN` motivata da nuova evidenza documentale primaria e seguita da riesecuzione dei validatori.

Fronti M1:

- `M1-S` sezioni;
- `M1-M` materiali e conoscenza;
- `M1-A` armature;
- `M1-L` carichi e masse;
- `M1-F` fondazioni e raccordo geotecnico;
- `M1-E` handoff EdiLus/FEM e gate `CALCULATION_MODEL_READY`.

I residui non bloccanti vengono conservati e resi risolvibili; non devono arrestare il lavoro sui domini sufficientemente affidabili.

## 6. Reverse engineering strutturale della pratica storica

La pratica originaria va ricostruita come sistema integrato, non come semplice copia dello schema di calcolo. Il tecnico dell'epoca può avere usato rappresentazioni schematiche, famiglie ricorrenti e semplificazioni. Questa ricorrenza è un segnale utile per cercare corrispondenze, omissioni e varianti, ma non costituisce evidenza sufficiente per colmare lacune.

Il controllo deve procedere trasversalmente:

`PIANTA ARCHITETTONICA -> CARPENTERIA -> ARMATURE -> RELAZIONE/CALCOLO -> STATO COSTRUITO/RILIEVO`

Le piante architettoniche sono fonti necessarie per ricostruire almeno:

- sagoma effettiva degli impalcati;
- balconate, terrazzi e sbalzi;
- posizione delle tamponature e loro variazioni;
- superfici interne/esterne e destinazioni d'uso;
- configurazioni che possono generare carichi, masse o eccentricità non rappresentati nello schema strutturale semplificato.

Le carpenterie stabiliscono la configurazione strutturale documentata; le tavole di armatura stabiliscono i dettagli solo dove direttamente leggibili; la relazione/calcolo documenta il modello storico assunto. Ogni differenza significativa tra questi quattro livelli deve produrre un item esplicito `HISTORICAL_MODEL_OMISSION_OR_SIMPLIFICATION`.

## 7. Regola configurazione storica vs stato costruito

Devono coesistere senza sovrascriversi:

1. `HISTORICAL_CALCULATION_MODEL`: ciò che il tecnico ha effettivamente rappresentato e calcolato;
2. `DOCUMENTED_AS_BUILT`: ciò che emerge da carpenterie, architettura, particolari e altri documenti;
3. `CURRENT_SURVEYED_STATE`: ciò che viene confermato da rilievi, saggi, misure e ispezioni;
4. `ANALYTICAL_CHECK_MODEL`: il modello adottato per le verifiche attuali.

Elementi o carichi presenti nello stato costruito ma assenti nel calcolo storico devono essere registrati come delta, non retro-inseriti nel modello storico come se fossero stati considerati all'epoca.

## 8. Persistenza e precedenza dell'evidenza

Ogni informazione utile deve essere salvata nel patrimonio canonico prima di procedere. In caso di contrasto:

- una fonte originale primaria direttamente leggibile prevale sulla ricostruzione riferita per il fatto specifico documentato;
- il dato riferito precedente resta tracciato con stato `CONFIRMED`, `SUPERSEDED_BY_DOC` o `CONFLICT_WITH_DOC`;
- una misura sullo stato reale non riscrive la storia documentale: crea il confronto `DOC vs MIS`;
- l'inferenza tecnica resta `INF` finché non è sostenuta da una fonte o misura indipendente;
- se nessuna evidenza chiude il punto, il valore resta `ND/INC` e il residuo rimane aperto.

Il sistema non deve perdere una precisazione tecnica dell'utente solo perché non è ancora verificata documentalmente.

## 9. Stato corrente

`M0-G`: CLOSED / frozen baseline.  
`M1-A`: IN_PROGRESS — `HOLD_SPECIAL_FEATURE_AUDIT` per completare elementi speciali, torrino scale, cornicioni, impluvi/gronde/colmi, balconate/sbalzi e relativi binding di armatura.  
`M1-L`: deve ricevere in parallelo ogni differenza confermata tra configurazione reale e carichi/modello storico, mantenendo un ledger delta dedicato.

Registri trasversali correnti:

- `data/canonical/M1A_SPECIAL_FEATURE_REINFORCEMENT_GAP_REGISTER_v1.csv`;
- `data/canonical/M1_SPECIAL_CONFIGURATION_LOADS_REGISTER_v1.csv`;
- `docs/M1A_SPECIAL_FEATURES_COMPLETENESS_REVIEW_v1.md`.
