# Skill: PT Raster Grid Reconstructor

## Scopo

Ricostruire la geometria strutturale di una carpenteria storica raster/PDF partendo dai **centri osservati dei sostegni** e dalle **quote documentali**, senza assumere corrette le coordinate dei Master precedenti e senza adattare arbitrariamente il reticolo alla deformazione della scansione.

La skill è progettata per N12 / TAV-02S ma il metodo è riusabile per elaborati strutturali storici in c.a.

## Principio fondamentale

La geometria viene separata in tre livelli che non devono essere confusi:

1. **RASTER_OBSERVED** — ciò che appare sulla scansione: centro simbolico, contorno, orientamento, travi apparenti, identificativo, coordinate pixel `(u,v)`;
2. **DOCUMENTED_METRIC** — ciò che la tavola dichiara: quote, catene di quote, allineamenti, sezioni, offset, simbologia;
3. **ANALYTICAL_GEOMETRY** — geometria strutturale ricostruita: centri metrici, supporti estesi, facce, assi trave e nodi analitici.

Il raster stabilisce **identità e topologia osservata**. Le quote stabiliscono **la metrica**. Le sezioni stabiliscono **le facce fisiche**. Le intersezioni trave-faccia stabiliscono **i nodi analitici**.

## Regola di autorità

Ordine obbligatorio delle evidenze:

`QUOTA SCRITTA -> ID/SIGLA -> SIMBOLOGIA -> RELAZIONE TOPOLOGICA -> CENTRO PIXEL -> GEOMETRIA APPARENTE -> INFERENZA`

Le coordinate metriche di `PT_MASTER_CURRENT.csv` e dei Master precedenti sono **HISTORICAL_ONLY** finché non vengono ricostruite con questa procedura.

È vietato usare un vecchio valore X/Y come punto iniziale per confermare lo stesso valore.

## Fonti primarie

- raster/PDF nativo TAV-02S;
- `analysis/source_renders/TAV02S/manifest.txt`;
- crop persistenti TAV-02S;
- quote e identificativi leggibili direttamente sulla tavola;
- `skills/pt-carpentry-reader/SKILL.md` per le regole semantiche di lettura.

## Separazione sostegno / nodo

Un **sostegno fisico** non coincide automaticamente con un **nodo analitico**.

### Pilastro ordinario

Registrare:

- `support_id`;
- centro raster `(u,v)`;
- centro metrico `(x,y)` dopo soluzione della rete;
- sezione e orientamento;
- contorno/facce.

Il nodo analitico viene creato soltanto quando è definita l'intersezione strutturale effettiva con la trave.

### Pilastro-setto / sostegno esteso

Esempi N12: P23, P30 e qualsiasi elemento con sviluppo tale da ricevere travi in punti differenti.

Regola obbligatoria:

> `1 supporto fisico != necessariamente 1 nodo analitico`.

Se due travi intercettano facce o punti distinti dello stesso sostegno, devono essere creati **nodi analitici distinti**, entrambi collegati allo stesso `support_id` ma a `face_id` differenti.

Non collassare mai preventivamente un pilastro-setto al proprio baricentro.

## Fase G0 — congelamento del pregresso

Prima di iniziare:

- marcare i Master geometrici precedenti come `HISTORICAL_ONLY` o `SUSPENDED`;
- non cancellarli;
- non usarli come input geometrico;
- recuperarne successivamente solo quote, ID, sezioni o claim che siano rivalidati direttamente.

## Fase G1 — acquisizione indipendente dei centri raster

Per ogni sostegno leggibile, registrare **senza consultare le vecchie coordinate metriche**:

- `support_id`;
- `tile_id`;
- `u_center_px`;
- `v_center_px`;
- metodo di individuazione del centro;
- tipo di simbolo;
- sezione leggibile;
- orientamento;
- stato evidenza;
- nota di ambiguità.

Per sostegni estesi registrare anche, se leggibili:

- quattro vertici raster oppure;
- facce principali;
- asse maggiore/minore.

Output obbligatorio:

`data/canonical/PT_PIXEL_SUPPORT_REGISTRY_v1.csv`

## Fase G2 — rete documentale delle quote

Costruire una rete di vincoli esclusivamente da quote e allineamenti rivalidati.

Ogni record contiene:

- `constraint_id`;
- `support_i`;
- `support_j`;
- tipo (`DISTANCE_X`, `DISTANCE_Y`, `DISTANCE`, `ALIGN_X`, `ALIGN_Y`, `OFFSET`, `ORTHOGONAL`, altro);
- valore documentale;
- unità;
- fonte/crop;
- stato evidenza.

Una quota grafica non viene tradotta automaticamente in distanza centro-centro: verificare sempre a quali riferimenti puntano le linee di estensione.

Output obbligatorio:

`data/canonical/PT_GCP_METRIC_NETWORK_v1.csv`

## Fase G3 — soluzione della rete metrica

La rete viene risolta come problema di aggiustamento geometrico.

Procedura:

1. scegliere un'origine convenzionale su un sostegno affidabile;
2. fissare l'orientamento globale usando un asse documentato;
3. propagare solo vincoli esatti non conflittuali;
4. quando la rete è sovradeterminata, risolvere con minimi quadrati / least-squares;
5. calcolare residuo per ogni vincolo;
6. non modificare quote documentali per farle coincidere con il raster;
7. non usare la distanza pixel come sostituto di una quota scritta;
8. usare il raster per diagnosticare deformazioni locali e associazioni errate.

Output obbligatori:

- `data/canonical/PT_METRIC_SUPPORT_CENTERS_v1.csv`
- `data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv`

## Fase G4 — diagnosi della scansione

Dopo aver ottenuto i centri metrici, stimare una trasformazione raster->metrica usando i punti omologhi `(u,v) <-> (x,y)`.

Testare nell'ordine:

1. similitudine/Helmert;
2. affine;
3. trasformazione locale solo se i residui dimostrano deformazione non modellabile globalmente.

La trasformazione serve per:

- overlay;
- misurazione degli errori di scansione;
- supporto alla vettorializzazione.

Non serve per spostare la rete quotata verso il raster.

Registrare:

- modello;
- parametri;
- residui per punto;
- RMS globale;
- outlier;
- eventuali zone deformate.

Output:

`data/canonical/PT_RASTER_TO_METRIC_DIAGNOSTIC_v1.csv`

## Fase G5 — costruzione delle sezioni fisiche

Per ogni sostegno con sezione nota:

- costruire il rettangolo/poligono metrico attorno al centro ricostruito;
- rispettare l'orientamento documentato;
- mantenere ND i lati non leggibili;
- non sostituire un sostegno esteso con un punto.

Output:

`data/canonical/PT_VECTOR_SUPPORTS_v1.csv` oppure formato vettoriale equivalente con tabella attributi canonica.

## Fase G6 — vettorializzazione delle travi

Le travi vengono riconosciute semanticamente sul raster e poi ricostruite metricamente.

Regole:

- rispettare la simbologia originale;
- distinguere contorno trave, asse, quota, bordo solaio e richiamo di sezione;
- rettangoli `70x25`, `120x20`, `65x30`, ecc. sono `BEAM_SECTION_CALLOUT` salvo prova contraria;
- una trave non viene creata perché due pilastri sono allineati;
- una relazione diventa `BEAM_DOC` solo dopo verifica grafica diretta secondo `pt-carpentry-reader`;
- OpenCV/Hough/LSD può proporre segmenti ma non può promuoverli semanticamente.

Output:

`data/canonical/PT_VECTOR_BEAMS_v1.csv`

## Fase G7 — nodalizzazione analitica

Per ogni trave documentata:

1. determinare il suo asse geometrico;
2. intersecare l'asse con il contorno/faccia del sostegno reale;
3. creare il nodo analitico nel punto fisico di attestazione;
4. assegnare:
   - `analytical_node_id`;
   - `support_id`;
   - `face_id`;
   - `beam_id`;
   - coordinate `(x,y)`;
   - provenienza;
   - stato.

Se più travi incidono lo stesso sostegno nello stesso punto entro tolleranza documentata, possono condividere il nodo.

Se incidono in punti diversi, **devono mantenere nodi distinti**.

Output:

`data/canonical/PT_ANALYTICAL_NODES_v1.csv`

## Fase G8 — controllo delle maglie

Controllare:

- chiusura geometrica delle maglie;
- coerenza delle lunghezze con le quote;
- corretta appartenenza delle travi;
- assenza di falsi nodi derivati da simboli;
- preservazione di pilastri-setti e supporti speciali;
- perimetro strutturale derivato da elementi documentati, non da convex hull o allineamenti ipotetici.

## Fase G9 — overlay finale

Produrre due overlay distinti:

1. **overlay osservativo** sul raster nativo: centri raster e contorni osservati;
2. **overlay metrico**: geometria ricostruita proiettata sul raster tramite trasformazione diagnostica.

Gli scarti devono restare visibili. Non deformare l'overlay per nascondere errori locali.

Output:

`data/canonical/PT_OVERLAY_QA_v1.csv`

## Tolleranze

Non fissare tolleranze universali arbitrarie.

Per ogni fase registrare:

- tolleranza pixel di lettura;
- tolleranza metrica derivata dalla qualità del documento;
- residuo effettivo;
- giustificazione.

Una tolleranza non può convertire un conflitto semantico in una corrispondenza.

## Stati

Usare almeno:

- `OBSERVED`
- `DOC`
- `MIS`
- `SUPPORTED`
- `CROSS_VALIDATED`
- `CONFLICT`
- `ND`
- `RESIDUAL`
- `CURRENT`
- `HISTORICAL_ONLY`
- `SUSPENDED`

## Gate di promozione del Master

`PT_MASTER_GEOMETRY_GATE = PASS` soltanto quando:

- tutti i sostegni utilizzati nel modello hanno registrazione raster indipendente;
- la rete metrica è risolta e i residui sono disponibili;
- ogni centro metrico ha provenienza;
- sezioni e orientamenti sono separati dalle coordinate;
- i supporti estesi sono conservati come geometrie fisiche;
- i nodi analitici derivano da intersezioni trave-faccia reali;
- il perimetro deriva dalla carpenteria documentata;
- l'overlay è riproducibile;
- nessun valore geometrico dipende esclusivamente da un Master storico non rivalidato.

Se manca uno di questi requisiti, il Master resta `SUSPENDED`.

## Artefatti minimi obbligatori

1. `PT_PIXEL_SUPPORT_REGISTRY_v1.csv`
2. `PT_GCP_METRIC_NETWORK_v1.csv`
3. `PT_METRIC_SUPPORT_CENTERS_v1.csv`
4. `PT_METRIC_NETWORK_RESIDUALS_v1.csv`
5. `PT_RASTER_TO_METRIC_DIAGNOSTIC_v1.csv`
6. `PT_VECTOR_SUPPORTS_v1.csv`
7. `PT_VECTOR_BEAMS_v1.csv`
8. `PT_ANALYTICAL_NODES_v1.csv`
9. `PT_OVERLAY_QA_v1.csv`

## Comando operativo

Usare:

`python skills/pt-raster-grid-reconstructor/runner.py status`

per verificare quali artefatti mancano e quale fase è autorizzata.

Usare:

`python skills/pt-raster-grid-reconstructor/runner.py validate`

per verificare che nessun Master sia promosso senza registro pixel, rete metrica, residui e nodi analitici.

## Divieti tassativi

- non generare una griglia regolare per analogia;
- non inventare il perimetro;
- non usare il vecchio Master come verità geometrica;
- non far coincidere forzatamente raster e reticolo;
- non convertire un simbolo di sezione in un pilastro;
- non collassare pilastri-setti in nodi puntuali;
- non creare una trave dal solo allineamento fra sostegni;
- non promuovere un dato non riproducibile;
- non nascondere gli scarti della scansione;
- non completare quote o sezioni illeggibili per simmetria o analogia.

## Criterio di completamento

La ricostruzione geometrica PT è completa quando un terzo operatore può, usando soltanto raster nativo, registri pixel, rete delle quote e questa skill, rigenerare la stessa geometria entro le tolleranze documentate senza consultare il Master storico.