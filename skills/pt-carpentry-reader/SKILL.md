# Skill: PT Carpenteria Reader

## Scopo

Ricostruire e replicare carpenterie storiche in c.a. da tavole raster/PDF ad alta risoluzione, distinguendo correttamente simbologia, fili, pilastri, travi, solai, quote e residui. La skill e progettata per elaborati anni 1975-1982 e per il caso N12/TAV-02S, ma il metodo e riusabile.

## Principio fondamentale

Non trasformare automaticamente geometria vicina in struttura.

Sequenza obbligatoria:

`quota -> filo/riferimento -> simbolo pilastro -> contorno/asse trave -> campo solaio -> connessione strutturale`

Una relazione tra due nodi diventa `BEAM_DOC` solo dopo verifica grafica diretta e controllo delle sovrapposizioni tra crop.

## Fonti canoniche N12

- `archive/documentazione_originaria/tavola2-2.pdf`
- `evidence/hires/TAV-02S/hires_index.json` sul ramo `work/m0g-source-recovery`
- `data/canonical/tav02s_dimension_chains_v1.csv`
- `data/canonical/tav02s_pt_global_nodes_current_v3.csv`
- `data/canonical/tav02s_left_sector_coordinate_conflict_audit_v1.csv`
- `data/canonical/tav02s_left_sector_global_grid_v2.csv`
- `data/canonical/PT_CARPENTRY_TOPOLOGY_FROM_QUOTES_v1.csv`
- `data/canonical/tav02s_symbol_semantics_policy_v1.csv`
- `data/canonical/TAV02S_CROP_REVIEW_REGISTER_v1.csv`
- `data/canonical/TAV02S_SYMBOL_OBSERVATIONS_v1.csv`
- `data/canonical/TAV02S_BEAMS_DOC_CURRENT_v1.csv`
- `data/canonical/TAV02S_READING_RESIDUALS_v1.csv`

## Precedenza delle evidenze

1. PDF/raster originale ad alta risoluzione.
2. Quote leggibili direttamente.
3. Continuita grafica osservata su uno o piu crop.
4. Allineamenti gia consolidati da quote.
5. Inferenze controllate, sempre separate da DOC.

Qualsiasi file marcato `SUPERSEDED`, `CONFLICT`, `REVOKED` o equivalente non puo promuovere dati canonici.

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

Una connessione puo essere promossa solo se:

- gli estremi o raccordi sono identificabili;
- il segno strutturale e continuo;
- non e quota, filo, bordo solaio, armatura o richiamo;
- se attraversa il confine di un crop, e confermata nel crop sovrapposto;
- non esiste un audit canonico che abbia riaperto quella relazione;
- la provenienza viene registrata.

In caso contrario usare `TO_VERIFY_BEAM`, `UNCERTAIN` o `CONFLICT`.

## Procedura per ciascun crop

1. Leggere `tile_id`, `u0,v0,u1,v1` da `hires_index.json`.
2. Individuare i fili/nodi canonici che ricadono nel settore.
3. Classificare i segni grafici.
4. Trascrivere le quote esattamente come leggibili.
5. Registrare le possibili connessioni come osservazioni.
6. Verificare le connessioni nel crop sovrapposto quando disponibile.
7. Applicare il gate di promozione.
8. Aggiornare osservazioni, travi documentate e residui.
9. Aggiornare lo stato del crop.
10. Passare al crop successivo senza riaprire i settori gia chiusi salvo conflitto esplicito.

## Ordine standard N12

`R01C01 -> R01C02 -> R01C03 -> R02C01 -> R02C02 -> R02C03 -> R03C01 -> R03C02 -> R03C03 -> R04C01 -> R04C02 -> R04C03`

C02 e C03 della stessa riga sono fortemente sovrapposti: trattarli come controllo incrociato e non duplicare entita.

## Regole per i fili e i centri

Le coordinate ottenute dalle quote sono riferimenti geometrici. Non assumere automaticamente che siano baricentri dei pilastri. La trasformazione filo/asse -> centro richiede sezione, orientamento ed eventuale offset documentato.

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
- travi `BEAM_DOC` con provenienza;
- campi solaio/direzioni quando leggibili;
- residui separati;
- matrice nodi-aste pronta per DXF;
- nessun dato canonico derivato da file superseded.

## Comando operativo

Usare `python skills/pt-carpentry-reader/runner.py status` per vedere il prossimo crop e lo stato dei gate.

Usare `python skills/pt-carpentry-reader/runner.py validate` per verificare registri, stati ammessi e promozioni `BEAM_DOC`.

Questa skill non esegue riconoscimento visuale autonomo: orchestra e valida il processo di lettura documentale. La classificazione visuale resta basata sui crop originali e sulle evidenze registrate.
