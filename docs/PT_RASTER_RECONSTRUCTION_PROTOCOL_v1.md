# PT_RASTER_RECONSTRUCTION_PROTOCOL_v1

## Stato
CURRENT_METHOD — sostituisce come metodo operativo le ricostruzioni geometriche precedenti basate su coordinate derivate non registrate direttamente sul raster.

## Principio di autorità
1. Autorità geometrica primaria: raster nativo TAV-02S.
2. Le quote scritte sulla tavola sono vincoli metrici.
3. Le coordinate del precedente PT_MASTER_CURRENT.csv sono solo storico finché non riconciliate con registrazione pixel riproducibile.
4. Nessun simbolo viene reinterpretato fuori dalla simbologia della tavola: pilastri, pilastri-setti, travi e richiami di sezione restano entità distinte.
5. I pilastri-setti sono geometrie estese. Le travi convergenti generano nodi analitici distinti sulle reali intersezioni asse-trave/faccia del sostegno quando tali intersezioni sono differenti.

## Procedura consolidata
### Fase R0 — conservazione sorgente
- Conservare TAV-02S nativa immutata.
- Registrare dimensione raster, checksum e tiling.
- Nessun deskew/dewarp distruttivo sulla sorgente.

### Fase R1 — registrazione pixel
- Per ogni sostegno identificabile registrare centro simbolico e, quando leggibili, vertici/facce: u_px, v_px.
- Per elementi estesi registrare almeno i quattro vertici o le due facce principali necessarie alle attestazioni.
- Ogni punto deve riportare tile, livello di zoom/sorgente, evidenza e stato DOC/MIS/ND.

### Fase R2 — rete di vincoli metrici
- Trascrivere soltanto quote direttamente leggibili e associazioni topologiche certe.
- Costruire una rete di vincoli tra punti omologhi, non un reticolo teorico imposto.
- Le quote sono usate per stimare e controllare la trasformazione, non per spostare arbitrariamente i simboli.

### Fase R3 — rettifica geometrica controllata
- Testare nell'ordine: Helmert / affine (Polinomiale 1) se sufficienti; trasformazioni locali solo se i residui mostrano deformazione di scansione non modellabile globalmente.
- Per scansione piana evitare trasformazione proiettiva salvo evidenza di prospettiva.
- Polinomi 2/3 e TPS sono ammessi solo con GCP sufficienti e controllo dei residui; non vanno usati per forzare il raster ad aderire a un reticolo ideale.
- Conservare sempre tabella GCP, residui e RMS.

### Fase R4 — vettorializzazione semantica
- Digitalizzazione manuale/assistita sopra raster rettificato con snapping e vincoli metrici.
- Layer separati: SUPPORTI, SUPPORTI_ESTESI, ASSI_TRAVI, FACCE_TRAVI, QUOTE, SIMBOLI_SEZIONE, TESTI_ID, RESIDUI.
- I rettangoli 70x25, 120x20, 65x30 ecc. restano SIMBOLI_SEZIONE_TRAVE salvo prova contraria.
- OpenCV/Hough/LineSegmentDetector può proporre segmenti; nessun segmento viene promosso senza verifica visuale e semantica.

### Fase R5 — nodalizzazione strutturale
- Nodo geometrico != automaticamente centro pilastro.
- Pilastro ordinario: nodo analitico secondo intersezione reale degli assi/facce documentate.
- Pilastro-setto: mantenere poligono/facce; creare nodi distinti alle intersezioni reali delle travi convergenti se non coincidenti.
- Collegare ogni nodo analitico a support_id e face_id.

### Fase R6 — controllo qualità
- Residuo metrico per ogni quota vincolante.
- Controllo chiusura maglie.
- Controllo parallelismo/ortogonalità solo dove documentato dalla tavola.
- Overlay finale sul raster originale e sul raster rettificato.
- Nessuna promozione Master se manca il registro pixel o se l'overlay non è riproducibile.

## Strumenti liberi previsti
- QGIS Georeferencer: GCP, affine/polinomiale/TPS, report residui/RMS.
- QGIS Advanced Digitizing + Snapping: digitalizzazione vincolata e topologica.
- OpenCV: estrazione assistita di linee, intersezioni e raffinamento sub-pixel; mai classificazione strutturale autonoma.
- GDAL: esecuzione/riproduzione delle trasformazioni raster e gestione GCP.

## Artefatti obbligatori prima di un nuovo Master
- PT_PIXEL_SUPPORT_REGISTRY_v1.csv
- PT_GCP_METRIC_NETWORK_v1.csv
- PT_RASTER_RECTIFICATION_REPORT_v1.csv
- PT_VECTOR_SUPPORTS_v1.*
- PT_VECTOR_BEAMS_v1.*
- PT_ANALYTICAL_NODES_v1.csv
- PT_OVERLAY_QA_v1.csv

## Gate
PT_MASTER_GEOMETRY_GATE = CLOSED soltanto se:
- registro pixel completo per tutti i sostegni usati nel modello;
- residui metrici accettabili e documentati;
- simboli/sezioni non scambiati per elementi strutturali;
- supporti estesi conservati come geometrie estese;
- nodi analitici derivati dalle intersezioni reali trave-faccia;
- overlay riproducibile sul raster nativo.
