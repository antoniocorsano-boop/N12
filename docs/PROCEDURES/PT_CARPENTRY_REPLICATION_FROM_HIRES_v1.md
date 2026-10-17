# Procedura PT — replica della carpenteria TAV-02S da crop ad alta risoluzione

Stato: CANONICAL WORKING PROCEDURE v1
Ambito: piano terra / TAV-02S
Obiettivo: replicare la carpenteria originale mediante lettura controllata di quote, simbologia e continuità grafica. Non produrre una pianta plausibile: riprodurre l'elaborato strutturale documentato.

## 1. Fonti e precedenza

1. Fonte grafica primaria: `archive/documentazione_originaria/tavola2-2.pdf`.
2. Evidenza visuale operativa: pacchetto `evidence/hires/TAV-02S/` sul ramo `work/m0g-source-recovery`.
3. Indice crop: `evidence/hires/TAV-02S/hires_index.json`.
4. Reticolo da quote corrente: `data/canonical/tav02s_pt_global_nodes_current_v3.csv` e successivi file esplicitamente non superseded.
5. Audit conflitti: `data/canonical/tav02s_left_sector_coordinate_conflict_audit_v1.csv`.
6. Griglia sinistra riconciliata: `data/canonical/tav02s_left_sector_global_grid_v2.csv`.
7. Matrice geometrica preliminare: `data/canonical/PT_CARPENTRY_TOPOLOGY_FROM_QUOTES_v1.csv`.
8. Politica semantica: `data/canonical/tav02s_symbol_semantics_policy_v1.csv`.

Un file marcato `SUPERSEDED`, `CONFLICT`, `REVOKED` o equivalente non può alimentare automaticamente lo stato canonico.

## 2. Pacchetto crop già disponibile

Raster nativo TAV-02S: 4680 x 8609 px.
Crop: 12 immagini da 2400 x 2400 px, sovrapposizione 12,5%.

Riga 1: `R01C01`, `R01C02`, `R01C03` — v=0..2400.
Riga 2: `R02C01`, `R02C02`, `R02C03` — v=2100..4500.
Riga 3: `R03C01`, `R03C02`, `R03C03` — v=4200..6600.
Riga 4: `R04C01`, `R04C02`, `R04C03` — v=6209..8609.

Le colonne 2 e 3 hanno forte sovrapposizione intenzionale: non sono settori indipendenti. Servono al controllo di continuità e leggibilità sul bordo destro.

## 3. Principio di lettura

La sequenza obbligatoria è:

`quota -> filo/riferimento -> simbolo pilastro -> contorno/asse trave -> campo solaio -> connessione strutturale`.

È vietata la sequenza `due nodi vicini -> asta`.

Le coordinate ottenute dalle catene di quota sono inizialmente coordinate di riferimenti geometrici. Non sono automaticamente coordinate del baricentro del pilastro. La trasformazione filo/asse -> centro richiede evidenza su sezione, orientamento e scostamento.

## 4. Classi semantiche

Ogni primitiva o gruppo grafico osservato nel crop deve ricevere una delle classi:

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

Non usare lo spessore della linea come unico discriminante.

## 5. Regola di promozione delle aste

Una relazione geometrica può diventare `BEAM_DOC` solo se:

1. i due estremi/raccordi sono identificabili;
2. la continuità grafica della trave è visibile sulla TAV-02S;
3. il segno non è una linea di quota, proiezione, bordo solaio, filo fisso o armatura;
4. l'eventuale passaggio tra crop è confermato nell'area di sovrapposizione;
5. non esiste un audit canonico che abbia riaperto quella relazione.

Se manca uno dei requisiti: `TO_VERIFY_BEAM` o `UNCERTAIN`, mai `BEAM_DOC`.

## 6. Procedura crop-per-crop

Per ogni crop:

A. Registrare `tile_id` e coordinate raster globali `u0,v0,u1,v1`.
B. Individuare esclusivamente i nodi/fili già riconciliati che ricadono nel settore.
C. Classificare i segni grafici secondo §4.
D. Trascrivere le quote leggibili senza reinterpretarle.
E. Registrare ogni possibile connessione come osservazione, non ancora come trave.
F. Verificare la stessa connessione sul crop sovrapposto quando disponibile.
G. Promuovere a `BEAM_DOC` solo dopo il gate §5.
H. Annotare residui con posizione raster e motivo preciso.
I. Aggiornare il registro canonico prima di passare al crop successivo.

## 7. Ordine di scansione

L'ordine standard è spaziale e riproducibile:

`R01C01 -> R01C02 -> R01C03 -> R02C01 -> R02C02 -> R02C03 -> R03C01 -> R03C02 -> R03C03 -> R04C01 -> R04C02 -> R04C03`.

Tuttavia C02/C03 della stessa riga devono essere trattati come coppia sovrapposta; una connessione sul confine non viene contata due volte.

## 8. Registro delle osservazioni

Ogni osservazione deve avere almeno:

`obs_id,tile_id,u_px,v_px,semantic_class,node_i,node_j,quoted_value,graphic_continuity,evidence_status,source,note`

Stati ammessi:

- `DOC_DIRECT`
- `DOC_CROSS_TILE`
- `DOC_ALIGN`
- `INF_STRONG`
- `UNCERTAIN`
- `CONFLICT`
- `SUPERSEDED`

Solo i primi tre possono concorrere alla replica documentale; `INF_STRONG` resta separato.

## 9. Controllo delle quote

Ogni catena deve essere verificata con chiusura numerica. Le catene già consolidate non vengono rilette da zero: si controllano soltanto se il crop introduce un conflitto.

Quote note di controllo comprendono le catene 3,45-3,45-5,50-5,60; 4,70-5,10-4,15-4,15-5,33-4,70; 4,70-3,45-2,10; 6,25-4,95; 6,45-4,65. Le associazioni ai nodi devono provenire dallo stato canonico corrente, non da file superseded.

## 10. Residui

I residui non bloccano la scansione globale. Vanno registrati con:

- posizione raster;
- elementi coinvolti;
- alternative compatibili;
- evidenza mancante;
- azione necessaria per chiuderli.

Nessun residuo può essere risolto per simmetria o analogia con un'altra ala senza prova documentale.

## 11. Output della fase

La fase termina quando esistono:

1. registro semantico dei 12 crop;
2. elenco pilastri/fili documentati;
3. elenco `BEAM_DOC` con provenienza crop;
4. campi solaio e direzioni, quando leggibili;
5. residui separati;
6. matrice nodi-aste pronta per il disegno tecnico;
7. nessuna entità derivata da file superseded.

Solo dopo questo gate si genera la replica grafica/DXF della carpenteria PT.
