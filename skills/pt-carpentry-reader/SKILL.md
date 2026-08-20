# Skill: PT Carpenteria Reader

## Scopo

Ricostruire e replicare carpenterie storiche in c.a. da tavole raster/PDF ad alta risoluzione, distinguendo correttamente simbologia, fili, pilastri, travi, solai, quote e residui. La skill è progettata per elaborati anni 1975-1982 e per il caso N12/TAV-02S, ma il metodo è riusabile.

## Principio fondamentale

I dataset canonici esistenti NON sono assunti come verità iniziale. Sono ipotesi versionate da rivalidare contro le evidenze primarie.

Sequenza obbligatoria:

`crop originale -> osservazione diretta -> confronto con claim corrente -> match/conflitto -> seconda evidenza -> promozione / riapertura / tombstone`

Per la geometria strutturale la lettura semantica resta:

`quota -> filo/riferimento -> simbolo pilastro -> contorno/asse trave -> campo solaio -> connessione strutturale`

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

Procedura di riferimento:

- `docs/PROCEDURES/CANONICAL_DATASET_ITERATIVE_REVALIDATION_v1.md`
- `docs/PROCEDURES/PT_CARPENTRY_REPLICATION_FROM_HIRES_v1.md`

## Precedenza delle evidenze

1. PDF/raster originale ad alta risoluzione.
2. Crop con coordinate raster note.
3. Quota leggibile direttamente.
4. Continuità grafica osservata su crop sovrapposti.
5. Raccordo con altra tavola originale.
6. Dataset storico.
7. Inferenza.

Qualsiasi record marcato `SUPERSEDED`, `CONFLICT`, `REOPENED`, `REVOKED` o `TOMBSTONE` non può promuovere nuovi dati canonici.

## Claim-based revalidation

Ogni informazione va ridotta a una proposizione verificabile, per esempio:

- `node 19 belongs to row Y=...`
- `pillar 23 section is 30x110`
- `beam exists between node i and node j`
- `dimension segment equals 4.05 m`
- `symbol is a pillar`

Per ogni claim:

1. leggere il record storico e la provenienza;
2. individuare il/i crop pertinenti;
3. osservare il crop senza usare il record come guida interpretativa;
4. registrare l'osservazione;
5. classificare `MATCH`, `PARTIAL_MATCH`, `CONFLICT`, `NOT_VISIBLE`;
6. cercare una seconda evidenza indipendente per coordinate/topologia;
7. aggiornare `CANONICAL_REVALIDATION_LEDGER_v1.csv`;
8. promuovere a `CURRENT` solo dopo cross-validation e assenza di conflitti aperti.

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
- `TEXT_OR_CALLOUT`
- `REBAR_SYMBOL`
- `UNCERTAIN`

## Gate di promozione a BEAM_DOC

Una connessione può essere promossa solo se:

- gli estremi o raccordi sono identificabili;
- il segno strutturale è continuo;
- non è quota, filo, bordo solaio, armatura o richiamo;
- se attraversa il confine di un crop, è confermata nel crop sovrapposto;
- non esiste un audit canonico che abbia riaperto quella relazione;
- la provenienza viene registrata;
- gli endpoint usati sono almeno `CROSS_VALIDATED` se la trave dipende dalle loro coordinate.

In caso contrario usare `TO_VERIFY_BEAM`, `UNCERTAIN` o `CONFLICT`.

## Procedura per ciascun crop

1. Leggere `tile_id`, `u0,v0,u1,v1` da `hires_index.json`.
2. Classificare i segni grafici senza assumere corretti i nodi storici.
3. Trascrivere le quote esattamente come leggibili.
4. Generare osservazioni semantiche.
5. Solo dopo, confrontare le osservazioni con i claim dei dataset correnti.
6. Registrare match e conflitti nel ledger.
7. Verificare i claim nel crop sovrapposto o in altra fonte indipendente.
8. Applicare i gate di promozione.
9. Aggiornare osservazioni, travi documentate e residui.
10. Aggiornare lo stato del crop.
11. Rigenerare i dataset canonici solo dai claim `CURRENT`.

## Ordine standard N12

`R01C01 -> R01C02 -> R01C03 -> R02C01 -> R02C02 -> R02C03 -> R03C01 -> R03C02 -> R03C03 -> R04C01 -> R04C02 -> R04C03`

C02 e C03 della stessa riga sono fortemente sovrapposti: trattarli come controllo incrociato e non duplicare entità.

## Regole per i fili e i centri

Le coordinate ottenute dalle quote sono riferimenti geometrici finché il crop non dimostra il significato del riferimento. Non assumere automaticamente che siano baricentri dei pilastri. La trasformazione filo/asse -> centro richiede sezione, orientamento ed eventuale offset documentato.

## Gestione residui

Ogni residuo deve contenere:

- crop e posizione raster;
- elementi coinvolti;
- problema preciso;
- alternative compatibili;
- evidenza mancante;
- azione richiesta.

I residui non bloccano la scansione globale.

## Criterio di completamento

La skill considera chiusa la replica PT quando esistono:

- 12 crop revisionati;
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
