# Procedura — rivalidazione iterativa dei dataset canonici rispetto ai crop

Stato: CANONICAL WORKING PROCEDURE v1
Ambito: TAV-02S / carpenteria PT, estendibile ad altre tavole.

## Principio

I dataset canonici esistenti non sono considerati verità iniziale. Sono ipotesi versionate da sottoporre a verifica continua contro le evidenze primarie ad alta risoluzione.

La lettura del disegno segue una gerarchia obbligatoria:

`MISURE SCRITTE -> LETTERE/NUMERI/ID -> TESTI/SIGLE -> SIMBOLI -> GEOMETRIA GRAFICA -> INFERENZA`.

Le misure numeriche e gli identificativi alfanumerici direttamente leggibili sul disegno hanno priorità rispetto alle coordinate storiche, alla misura in pixel e alla geometria apparente.

Il ciclo obbligatorio è:

`crop -> lettura misure e ID -> osservazione diretta -> confronto con dataset corrente -> compatibilità/conflitto -> candidato aggiornato -> verifica sul crop sovrapposto o su fonte indipendente -> promozione / riapertura / tombstone`.

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

1. quota o misura numerica direttamente leggibile nel PDF/crop originale;
2. lettera, numero, ID, sigla o testo direttamente leggibile;
3. simbolo grafico inequivoco associato a quota/ID;
4. continuità grafica verificata su crop sovrapposti;
5. raccordo con altra tavola originale;
6. dataset storico;
7. misura ricavata dalla scala raster;
8. inferenza.

Il raster/PDF originale è il supporto primario; al suo interno, **testo e quote esplicite prevalgono sulla geometria apparente**.

Se una quota scritta o un ID leggibile contraddice una geometria storica, la geometria viene riaperta. Se la quota o l'ID sono ambigui o illeggibili, non vengono completati per analogia.

## Unità di rivalidazione

Ogni record deve essere ridotto a una proposizione verificabile, ad esempio:

- `dimension chain segment equals 4.05 m`
- `symbol label is 19`
- `pillar label is a/b/c/d`
- `node 19 belongs to row Y=...`
- `pillar 23 section text is 30x110`
- `beam exists between node i and node j`
- `symbol is a pillar and not a callout`

Non si rivalidano file interi in blocco.

## Ciclo iterativo

Per ogni proposizione:

1. Individuare il/i crop che coprono la zona.
2. Leggere e trascrivere prima tutte le misure numeriche visibili.
3. Leggere e trascrivere poi lettere, numeri, ID, sigle e testi visibili.
4. Registrare posizione raster e grado di leggibilità di ciascuna lettura.
5. Classificare i simboli grafici collegati a tali letture.
6. Solo dopo identificare il record storico e la sua provenienza.
7. Confrontare osservazione e record.
8. Classificare l'esito: `MATCH`, `PARTIAL_MATCH`, `CONFLICT`, `NOT_VISIBLE`.
9. Se `MATCH`, cercare una seconda evidenza indipendente quando il record influenza la topologia o le coordinate.
10. Se `CONFLICT`, non correggere in-place senza traccia: creare nuova versione candidata e marcare il precedente `REOPENED` o `SUPERSEDED`.
11. Aggiornare il registro delle decisioni.
12. Solo dopo cross-validation, promuovere il record a `CURRENT`.

## Requisiti di promozione

Coordinate nodali / fili:
- almeno una quota diretta o raccordo quotato;
- associazione corretta della quota ai riferimenti estremi;
- coerenza con lettere/numeri/ID leggibili;
- coerenza con allineamenti visibili;
- nessun conflitto con crop adiacenti.

Pilastri:
- simbolo identificato direttamente;
- ID leggibile o raccordato senza ambiguità;
- sezione/orientamento separati dalla sola posizione del filo.

Travi:
- continuità grafica diretta;
- esclusione di quota, bordo solaio, filo, armatura;
- controllo su crop sovrapposto quando attraversa un confine;
- nessuna contraddizione con quote o identificativi leggibili.

## Regola sulle misure raster

La misura in pixel non sostituisce mai una quota scritta leggibile.

Può essere usata solo per:
- localizzare un elemento non quotato;
- controllare coerenza relativa;
- stimare un rapporto geometrico da mantenere come `INF`;
- individuare un conflitto che richiede nuova lettura.

Una misura raster non può promuovere da sola un dato a `DOC`.

## Anti-propagazione

Un record `SUPPORTED` ma non `CROSS_VALIDATED` non può essere usato per generare nuove coordinate o nuove aste canoniche.

Un record `CONFLICT`, `REOPENED`, `SUPERSEDED` o `TOMBSTONE` non può essere usato come sorgente di inferenza.

## Registro delle rivalidazioni

Usare `data/canonical/CANONICAL_REVALIDATION_LEDGER_v1.csv`.

Campi minimi:

`claim_id,dataset_path,record_key,claim_type,old_value,crop_ids,observation_ids,result,new_value,validation_state,decision_note`.

## Strategia di revisione PT

Ordine obbligatorio:

1. misure/quote numeriche;
2. lettere, numeri e identificativi;
3. fili/riferimenti associati alle quote;
4. identità/posizione dei pilastri;
5. settore sinistro e record già coinvolti in conflitti;
6. travi effettive;
7. campi solaio;
8. terrazzo a-d;
9. sezioni e orientamenti.

La revisione procede crop-per-crop, ma il registro è claim-based: lo stesso claim può essere aggiornato da più crop.

## Gate finale

Il dataset PT può essere dichiarato nuovamente canonico solo quando:

- tutte le quote e gli ID strutturalmente rilevanti leggibili sono registrati;
- ogni record strutturalmente rilevante è almeno `SUPPORTED`;
- ogni record usato per derivare altri dati è `CROSS_VALIDATED`;
- nessun `CONFLICT` aperto viene nascosto;
- tutte le versioni superate restano tracciabili;
- il Master è rigenerato dai soli record `CURRENT`.
