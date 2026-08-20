# Procedura — rivalidazione iterativa dei dataset canonici rispetto ai crop

Stato: CANONICAL WORKING PROCEDURE v1
Ambito: TAV-02S / carpenteria PT, estendibile ad altre tavole.

## Principio

I dataset canonici esistenti non sono considerati verità iniziale. Sono ipotesi versionate da sottoporre a verifica continua contro le evidenze primarie ad alta risoluzione.

Il ciclo obbligatorio è:

`crop -> osservazione diretta -> confronto con dataset corrente -> compatibilità/conflitto -> candidato aggiornato -> verifica sul crop sovrapposto o su fonte indipendente -> promozione / riapertura / tombstone`.

## Stati ammessi per un record canonico

- `UNREVIEWED`: record storico non ancora riesaminato contro crop.
- `SUPPORTED`: compatibile con almeno una evidenza primaria diretta.
- `CROSS_VALIDATED`: compatibile con almeno due evidenze indipendenti o con crop + quota documentale.
- `CONFLICT`: incompatibile con almeno una evidenza primaria.
- `REOPENED`: precedentemente chiuso, ma riaperto dopo conflitto.
- `SUPERSEDED`: sostituito da un record successivo meglio supportato.
- `TOMBSTONE`: mantenuto solo per provenienza, vietato come sorgente di nuove inferenze.
- `CURRENT`: ammesso solo dopo `CROSS_VALIDATED` e assenza di conflitti aperti.

## Regola di priorità

1. PDF/raster originale ad alta risoluzione.
2. Crop con coordinate raster note.
3. Quota direttamente leggibile.
4. Continuità grafica verificata su crop sovrapposti.
5. Raccordo con altra tavola originale.
6. Dataset storico.
7. Inferenza.

Un dataset storico non può prevalere su un crop originale.

## Unità di rivalidazione

Ogni record deve essere ridotto a una proposizione verificabile, ad esempio:

- `node 19 belongs to row Y=...`
- `pillar 23 section is 30x110`
- `beam exists between node i and node j`
- `dimension chain segment equals 4.05 m`
- `symbol is a pillar and not a callout`

Non si rivalidano file interi in blocco.

## Ciclo iterativo

Per ogni proposizione:

1. Identificare il record corrente e la sua provenienza.
2. Individuare il/i crop che coprono la zona.
3. Registrare osservazioni dirette senza usare il dataset come guida interpretativa.
4. Confrontare osservazione e record.
5. Classificare l'esito: `MATCH`, `PARTIAL_MATCH`, `CONFLICT`, `NOT_VISIBLE`.
6. Se `MATCH`, cercare una seconda evidenza indipendente quando il record influenza la topologia o le coordinate.
7. Se `CONFLICT`, non correggere in-place senza traccia: creare nuova versione candidata e marcare il precedente `REOPENED` o `SUPERSEDED`.
8. Aggiornare il registro delle decisioni.
9. Solo dopo cross-validation, promuovere il record a `CURRENT`.

## Requisiti di promozione

Coordinate nodali / fili:
- almeno una quota diretta o raccordo quotato;
- coerenza con allineamenti visibili;
- nessun conflitto con crop adiacenti.

Pilastri:
- simbolo identificato direttamente;
- ID leggibile o raccordato senza ambiguità;
- sezione/orientamento separati dalla sola posizione del filo.

Travi:
- continuità grafica diretta;
- esclusione di quota, bordo solaio, filo, armatura;
- controllo su crop sovrapposto quando attraversa un confine.

## Anti-propagazione

Un record `SUPPORTED` ma non `CROSS_VALIDATED` non può essere usato per generare nuove coordinate o nuove aste canoniche.

Un record `CONFLICT`, `REOPENED`, `SUPERSEDED` o `TOMBSTONE` non può essere usato come sorgente di inferenza.

## Registro delle rivalidazioni

Usare `data/canonical/CANONICAL_REVALIDATION_LEDGER_v1.csv`.

Campi minimi:

`claim_id,dataset_path,record_key,claim_type,old_value,crop_ids,observation_ids,result,new_value,validation_state,decision_note`.

## Strategia di revisione PT

Ordine consigliato:

1. quote e fili principali;
2. identità/posizione dei pilastri;
3. settore sinistro e record già coinvolti in conflitti;
4. travi effettive;
5. campi solaio;
6. terrazzo a-d;
7. sezioni e orientamenti.

La revisione procede crop-per-crop, ma il registro è claim-based: lo stesso claim può essere aggiornato da più crop.

## Gate finale

Il dataset PT può essere dichiarato nuovamente canonico solo quando:

- ogni record strutturalmente rilevante è almeno `SUPPORTED`;
- ogni record usato per derivare altri dati è `CROSS_VALIDATED`;
- nessun `CONFLICT` aperto viene nascosto;
- tutte le versioni superate restano tracciabili;
- il Master è rigenerato dai soli record `CURRENT`.
