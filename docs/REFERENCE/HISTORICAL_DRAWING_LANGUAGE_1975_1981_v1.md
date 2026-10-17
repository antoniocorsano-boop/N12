# Linguaggio grafico storico per carpenterie in c.a. — 1975–1981

## Scopo
Questo documento definisce il criterio di lettura storico-documentale da usare per la TAV-02S del progetto N12. Non sostituisce la tavola originale e non autorizza inferenze automatiche: serve a distinguere i segni grafici prima di convertirli in entità strutturali.

## Quadro storico verificato
- La Legge 5 novembre 1971 n. 1086 disciplina le opere in conglomerato cementizio armato normale e precompresso e richiede un progetto esecutivo redatto da tecnico abilitato.
- La Circolare LL.PP. 14 febbraio 1974 n. 11951 chiarisce che i disegni di progetto depositati devono definire le strutture dell'opera e che i particolari esecutivi possono essere presentati successivamente, purché prima della loro esecuzione.
- La manualistica era un riferimento professionale sostanziale per la progettazione e il dettaglio del c.a. nel periodo. Sono documentati come testi di uso comune o coevi: Luigi Santarella, *Prontuario del cemento armato* (edizioni diffuse negli anni '60-'80; edizione Hoepli 1977 attestata e XXXI edizione 1981); *Manuale del costruttore civile e del geometra*, Cremonese, 1975.
- La UNI 3972 sui tratteggi dei materiali entra in vigore nel 1981: pertanto non si deve retrodatare automaticamente alla tavola del 1978 una convenzione UNI successiva se la simbologia interna della tavola indica diversamente.

## Principio di interpretazione
La TAV-02S va letta secondo la seguente gerarchia:
1. segno grafico effettivo sulla tavola;
2. quote e catene dimensionali associate;
3. continuità del segno nella stessa carpenteria;
4. corrispondenza con sezioni, particolari, abachi e armature coeve del progetto;
5. confronto con manualistica e convenzioni del periodo;
6. solo in ultima istanza, inferenza geometrico-strutturale controllata.

Una convenzione moderna non può promuovere da sola un elemento a DOC.

## Classi semantiche da usare sulla TAV-02S
### FILO_FISSO / RIFERIMENTO
Linea geometrica di tracciamento o faccia di riferimento. Non equivale automaticamente all'asse o al baricentro del pilastro. Le quote possono misurare distanze tra fili e non tra centri.

### PILASTRO
Deve essere riconosciuto dalla combinazione di impronta/sezione, sigla o numero, eventuale quotatura della sezione e coerenza con abachi o particolari. Il solo incrocio di linee non è sufficiente.

### TRAVE
Deve risultare da un contorno, asse/linea strutturale chiaramente riconoscibile, sezione associata, continuità tra appoggi o altra evidenza grafica specifica. Una semplice linea di quota o di riferimento non può diventare trave.

### TRAVE_EMERGENTE
Classe da assegnare solo quando la tavola o le tavole collegate permettono di distinguere una trave con altezza maggiore dello spessore dell'impalcato.

### TRAVE_A_SPESSORE
Classe da assegnare solo quando larghezza/sezione e relazione col solaio sono documentabili. Non dedurre dal solo spessore apparente della linea.

### SOLAIO / DIREZIONE_PORTANTE
Campi di solaio, nervature, travetti o segni di orditura vanno separati dalle travi. La direzione del solaio è una proprietà del campo, non una connessione nodo-nodo.

### BORDO_IMPALCATO / SBALZO
Linea di contorno dell'impalcato o dello sbalzo. Non equivale automaticamente a trave di bordo.

### QUOTA
Linea di misura, linea di riferimento, freccia/tacca, testo numerico. Mai convertire in elemento strutturale.

### SEZIONE_RICHIAMO / TESTO / SIMBOLO
Richiami, sigle, numerazione, riferimenti a dettagli e sezioni. Servono alla semantica, non alla topologia diretta.

### INCERTO
Qualsiasi segno non riconosciuto con almeno due discriminatori indipendenti resta INCERTO e non entra nel grafo strutturale.

## Regola specifica per N12
Nel reticolo PT, le coordinate derivanti dalle catene di quota devono essere trattate come coordinate dei riferimenti geometrici della tavola finché non è dimostrato che la quota è riferita al centro del pilastro. La promozione a centro di sezione richiede verifica di sezione, orientamento, filo fisso ed eventuale offset.

## Stato epistemico
- DOC: lettura diretta e inequivoca dalla fonte originale.
- MIS: misura eseguita sul raster/PDF con tolleranza dichiarata.
- RIF: informazione riferita da tecnico/utente o fonte indiretta.
- INF: deduzione controllata e reversibile.
- ND: non disponibile/non determinato.

## Divieti operativi
- Non usare colore o spessore di linea del raster come prova unica della funzione strutturale.
- Non convertire automaticamente segmenti tra due nodi in travi.
- Non assumere che asse, filo fisso e baricentro coincidano.
- Non usare file storici marcati SUPERSEDED per promuovere entità.
- Non usare simbologie UNI successive al 1978 come prova documentale retroattiva.

## Fonti esterne verificate
- Legge 5 novembre 1971 n. 1086.
- Circolare Ministero LL.PP. 14 febbraio 1974 n. 11951.
- Luigi Santarella, *Prontuario del cemento armato*, Hoepli: edizione 1977 attestata; edizione 1981 attestata.
- *Manuale del costruttore civile e del geometra*, Cremonese, 1975.
- UNI 3972:1981, tratteggi per la rappresentazione dei materiali nelle sezioni.

## Applicazione immediata
Prima di continuare `PT_CARPENTRY_TOPOLOGY_FROM_QUOTES_v1.csv`, ogni tratto candidato deve essere classificato sulla TAV-02S con almeno: `semantic_class`, `graphic_evidence`, `dimension_evidence`, `cross_sheet_evidence`, `status`. Solo `semantic_class=TRAVE*` con `status=DOC` può generare un'asta strutturale canonica.
