# Skill: PT Carpenteria Reader

## Scopo

Ricostruire e replicare carpenterie storiche in c.a. da tavole raster/PDF ad alta risoluzione, distinguendo correttamente simbologia, fili, pilastri, travi, solai, quote e residui. La skill è progettata per elaborati anni 1975-1982 e per il caso N12/TAV-02S, ma il metodo è riusabile.

## Principio fondamentale

I dataset canonici esistenti NON sono assunti come verità iniziale. Sono ipotesi versionate da rivalidare contro le evidenze primarie.

La gerarchia interna della lettura del disegno è obbligatoria:

`MISURE SCRITTE -> LETTERE/NUMERI/ID -> TESTI E SIGLE -> SIMBOLI -> GEOMETRIA GRAFICA -> INFERENZA`.

Le misure numeriche scritte sulla tavola e gli identificativi alfanumerici leggibili hanno priorità sulla misura ricavata dalla scala raster, sulla posizione apparente dei segni e sulle ricostruzioni geometriche precedenti.

Se una quota scritta o un ID leggibile contraddice una geometria ricostruita, la geometria viene riaperta. Se il testo è illeggibile o ambiguo, non viene completato per analogia: resta `UNCERTAIN/ND`.

Sequenza obbligatoria di rivalidazione:

`crop originale -> lettura misure e ID -> osservazione semantica -> confronto con claim corrente -> match/conflitto -> seconda evidenza -> promozione / riapertura / tombstone`.

Per la geometria strutturale la lettura resta:

`quota -> filo/riferimento -> simbolo pilastro -> contorno/asse trave -> campo solaio -> connessione strutturale`.

Una relazione tra due nodi diventa `BEAM_DOC` solo dopo verifica grafica diretta e controllo delle sovrapposizioni tra crop.

## Fonti primarie N12

- `archive/documentazione_originaria/tavola2-2.pdf`
- `evidence/hires/TAV-02S/hires_index.json` sul ramo `work/m0g-source-recovery`
- i 12 crop PNG indicizzati nel pacchetto HiRes

## Dataset da rivalidare

I seguenti file sono input storici da verificare, non autorità interpretative:

- `data/canonical/tav02s_dimension_chains_v1.csv`
- `data/canonical/tav02s_pt_global_nodes_current_v3.csv`
- `data/canonical/tav02s_left_sector_coordinate_conflict_audit_v1.csv`
- `data/canonical/tav02s_left_sector_global_grid_v2.csv`
- `data/canonical/PT_CARPENTRY_TOPOLOGY_FROM_QUOTES_v1.csv`
- `data/canonical/PT_MASTER_CURRENT.csv`

Il Master è un output rigenerabile dai soli claim `CURRENT`, non una fonte superiore ai crop.

## Registri operativi

- `data/canonical/tav02s_symbol_semantics_policy_v1.csv`
- `data/canonical/TAV02S_CROP_REVIEW_REGISTER_v1.csv`
- `data/canonical/TAV02S_SYMBOL_OBSERVATIONS_v1.csv`
- `data/canonical/TAV02S_BEAMS_DOC_CURRENT_v1.csv`
- `data/canonical/TAV02S_READING_RESIDUALS_v1.csv`
- `data/canonical/CANONICAL_REVALIDATION_LEDGER_v1.csv`

Procedure di riferimento:

- `docs/PROCEDURES/CANONICAL_DATASET_ITERATIVE_REVALIDATION_v1.md`
- `docs/PROCEDURES/PT_CARPENTRY_REPLICATION_FROM_HIRES_v1.md`

## Precedenza delle evidenze

1. quota/misura numerica direttamente leggibile nel PDF/crop originale;
2. lettera, numero, ID, sigla o testo direttamente leggibile;
3. simbolo grafico inequivoco associato a misura/ID;
4. continuità grafica verificata sul crop e sui crop sovrapposti;
5. raccordo con altra tavola originale;
6. dataset storico;
7. misura ricavata dalla scala raster;
8. inferenza.

Il PDF/raster originale è il supporto primario, ma al suo interno **testo e quote esplicite prevalgono sulla geometria apparente**.

Qualsiasi record marcato `SUPERSEDED`, `CONFLICT`, `REOPENED`, `REVOKED` o `TOMBSTONE` non può promuovere nuovi dati canonici.

## Claim-based revalidation

Ogni informazione va ridotta a una proposizione verificabile, per esempio:

- `dimension segment equals 4.05 m`
- `symbol label is 19`
- `pillar label is a/b/c/d`
- `node 19 belongs to row defined by quoted chain ...`
- `pillar 23 section text is 30x110`
- `beam exists between node i and node j`

Per ogni claim:

1. leggere prima tutte le misure e gli identificativi alfanumerici nel crop, senza consultare il valore storico;
2. registrare tali letture come osservazioni primarie;
3. classificare i simboli collegati a quelle letture;
4. solo dopo leggere il record storico e la sua provenienza;
5. confrontare osservazione e record;
6. classificare `MATCH`, `PARTIAL_MATCH`, `CONFLICT`, `NOT_VISIBLE`;
7. cercare una seconda evidenza indipendente per coordinate/topologia;
8. aggiornare `CANONICAL_REVALIDATION_LEDGER_v1.csv`;
9. promuovere a `CURRENT` solo dopo cross-validation e assenza di conflitti aperti.

Stati di validazione:

- `UNREVIEWED`
- `SUPPORTED`
- `CROSS_VALIDATED`
- `CONFLICT`
- `REOPENED`
- `SUPERSEDED`
- `TOMBSTONE`
- `CURRENT`

Un record solo `SUPPORTED` non può generare nuovi dati derivati.

## Classi semantiche

Usare una delle seguenti classi:

- `DIMENSION_VALUE`
- `ALPHANUMERIC_ID`
- `TEXT_OR_CALLOUT`
- `PILLAR_SYMBOL`
- `BEAM_CONTOUR`
- `BEAM_AXIS_OR_REFERENCE`
- `SLAB_FIELD`
- `SLAB_DIRECTION`
- `DIMENSION_LINE`
- `DIMENSION_EXTENSION`
- `GRID_OR_FIXED_LINE`
- `EDGE_OR_CANTILEVER`
- `STAIR_OR_OPENING`
- `REBAR_SYMBOL`
- `UNCERTAIN`

`DIMENSION_VALUE` e `ALPHANUMERIC_ID` sono classi prioritarie: devono essere registrate prima dell'interpretazione della geometria strutturale.

## Gate di promozione a BEAM_DOC

Una connessione può essere promossa solo se:

- gli estremi o raccordi sono identificabili;
- il segno strutturale è continuo;
- non è quota, filo, bordo solaio, armatura o richiamo;
- se attraversa il confine di un crop, è confermata nel crop sovrapposto;
- non esiste un audit canonico che abbia riaperto quella relazione;
- la provenienza viene registrata;
- gli endpoint usati sono almeno `CROSS_VALIDATED` se la trave dipende dalle loro coordinate;
- non contraddice quote o identificativi alfanumerici leggibili.

In caso contrario usare `TO_VERIFY_BEAM`, `UNCERTAIN` o `CONFLICT`.

## Procedura per ciascun crop

1. Leggere `tile_id`, `u0,v0,u1,v1` da `hires_index.json`.
2. Trascrivere **prima** tutte le quote/misure numeriche leggibili.
3. Trascrivere **poi** lettere, numeri, ID, sigle e testi leggibili.
4. Registrare posizione raster e leggibilità di ciascuna misura/ID.
5. Classificare i simboli grafici senza assumere corretti i nodi storici.
6. Generare osservazioni semantiche.
7. Solo dopo, confrontare le osservazioni con i claim dei dataset correnti.
8. Registrare match e conflitti nel ledger.
9. Verificare i claim nel crop sovrapposto o in altra fonte indipendente.
10. Applicare i gate di promozione.
11. Aggiornare osservazioni, travi documentate e residui.
12. Aggiornare lo stato del crop.
13. Rigenerare i dataset canonici solo dai claim `CURRENT`.

## Ordine standard N12

`R01C01 -> R01C02 -> R01C03 -> R02C01 -> R02C02 -> R02C03 -> R03C01 -> R03C02 -> R03C03 -> R04C01 -> R04C02 -> R04C03`.

C02 e C03 della stessa riga sono fortemente sovrapposti: trattarli come controllo incrociato e non duplicare entità.

## Regole per quote, fili e centri

Una quota scritta è un dato documentale prioritario. La sua associazione ai riferimenti estremi deve però essere letta correttamente dalle linee di quota e di richiamo.

Le coordinate ottenute dalle quote sono riferimenti geometrici finché il crop non dimostra il significato del riferimento. Non assumere automaticamente che siano baricentri dei pilastri. La trasformazione filo/asse -> centro richiede sezione, orientamento ed eventuale offset documentato.

È vietato sostituire una quota scritta con una misura in pixel quando entrambe sono disponibili. La misura raster può servire solo come controllo di coerenza o per localizzare un elemento non quotato.

## Gestione residui

Ogni residuo deve contenere:

- crop e posizione raster;
- misura/ID coinvolto, se presente;
- elementi coinvolti;
- problema preciso;
- alternative compatibili;
- evidenza mancante;
- azione richiesta.

I residui non bloccano la scansione globale.

## Criterio di completamento

La skill considera chiusa la replica PT quando esistono:

- 12 crop revisionati;
- registro completo di misure e ID leggibili;
- registro semantico completo;
- claim geometrici/topologici necessari almeno `CROSS_VALIDATED`;
- travi `BEAM_DOC` con provenienza;
- campi solaio/direzioni quando leggibili;
- residui separati;
- matrice nodi-aste pronta per DXF;
- nessun dato `CURRENT` derivato da record superseded o non rivalidati;
- Master rigenerato dai soli claim `CURRENT`.

## Comando operativo

Usare `python skills/pt-carpentry-reader/runner.py status` per vedere il prossimo crop e lo stato dei gate.

Usare `python skills/pt-carpentry-reader/runner.py validate` per verificare registri, stati ammessi e promozioni `BEAM_DOC`.

La skill orchestra e valida la lettura documentale; il riconoscimento visuale produce osservazioni candidate, ma nessun dato viene promosso senza il ciclo di rivalidazione iterativa.
