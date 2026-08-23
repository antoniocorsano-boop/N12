# M1-A — Review di completezza armature speciali

Data: 2026-08-23  
Ramo: `work/m0-global-model`  
Stato: `HOLD_SPECIAL_FEATURE_AUDIT_BEFORE_M1A_GATE`

## Scopo

Verifica preventiva richiesta prima di proseguire la trascrizione ordinaria delle armature. Ambiti controllati: semantica delle coppie di numeri sovrapposte in TAV-034A, cornicioni/perimetri ai livelli in cui compaiono in carpenteria, impluvi/gronde/colmi di copertura e relativa armatura, balconate/sbalzi con sagoma cementata o sagomata, terrazzo/addizioni, torrino scale, sbalzi di gronda verso i terrazzi dell'ultimo livello e loro conseguenze sulla configurazione reale e sui carichi.

## 1. Coppie di numeri sovrapposte in TAV-034A

Chiarimento qualificato dell'utente: le coppie di numeri sovrapposte rappresentano due sequenze di sostegni alle quali si applica lo stesso schema di armatura. La precedente classificazione come ambiguità di etichetta è quindi superata.

Decisione: lo schema centrale va trattato come `PAIRED_SEQUENCE_SCHEDULE`, analogamente agli altri schemi doppi della tavola. Prima della proiezione sui member ID si deve comunque verificare ogni coppia consecutiva contro TAV-03S/TAV-04S e contro `STOREY_BEAMS_G2_v1.csv` / `STOREY_BEAMS_G3_v1.csv`. In particolare la sequenza superiore letta come 17-18-19-20-21 introduce un controllo mirato sul tratto 20-21: il chiarimento semantico non costituisce da solo evidenza sufficiente per una modifica topologica.

## 2. Cornicioni/perimetri G4 e G5

Esito: `NON ANCORA COPERTI IN MODO SUFFICIENTE`.

Le fonti primarie corrette sono disponibili: TAV-05S/TAV-05A per G4 e TAV-06S/TAV-06A per G5. Tuttavia il modello canonico corrente è centrato sulle travi ordinarie supporto-supporto e non possiede ancora un inventario esplicito `CORNICIONE/PERIMETER_CANTILEVER`. TAV-05A risulta ancora da associare ai membri; TAV-06A è soltanto parzialmente associata.

Prima del gate M1-A ogni elemento perimetrale deve essere classificato in una delle seguenti categorie, senza fusione automatica:

- trave perimetrale ordinaria tra sostegni;
- cornicione/sbalzo strutturale oltre l'ultimo sostegno;
- bordo o fascia di soletta/sbalzo da modellare come elemento di piastra;
- profilo in calcestruzzo con funzione prevalentemente non strutturale, da trattare come massa/carico e non come trave.

Solo dopo questa classificazione l'armatura TAV-05A/TAV-06A può essere attribuita correttamente.

## 3. Copertura: impluvio, colmi e gronde

### Impluvio

`G5-B017 = 12-19` è già identificato come `IMPLUVIO`, sezione 30x50 `SUPPORTED`. Geometria e ruolo sono quindi acquisiti, ma l'armatura longitudinale/staffe specifica dell'impluvio non è ancora legata canonicamente. Non è corretto assumere automaticamente l'armatura della famiglia delle travi rettangolari adiacenti.

### Colmi

Sono censite tre `RIDGE_AXIS`, con identità documentale. Le coordinate XY sono MIS e la quota Z globale resta ND. Il registro speciale mantiene correttamente `TO_VERIFY_MEMBER`: non è stato creato automaticamente un elemento trave per ciascun colmo.

Armatura: `NON CHIUSA`. Per ogni colmo TAV-06S/TAV-06A deve stabilire prima se la linea corrisponde a una vera trave/cordolo strutturale, a una linea geometrica della copertura o ad altro dettaglio. Solo nel primo caso si crea il relativo oggetto di armatura.

### Gronde

Sono censiti tre `GRONDA_EDGE_SET` con identità DOC. Il centrolinea metrico e la quota Z restano volutamente ND perché un singolo asse di trave non è attualmente documentato.

Armatura: `NON CHIUSA`. Occorre ricercare il dettaglio diretto su TAV-06A e distinguere la trave/cordolo di gronda dall'eventuale bordo della soletta o dal cornicione.

### Trave obliqua 19-26

`G5-B036 = 19-26`, 30x50, è invece una vera trave ordinaria obliqua documentata e già conteggiata una sola volta. La sua armatura TAV-06A deve ancora essere portata nel registro M1-A a livello barra-per-barra.

## 4. Balconate e sbalzi con sagoma cementata/sagomata

Esito: `PRESENZA DA INVENTARIARE; ARMATURA NON DOCUMENTATA CANONICAMENTE`.

Il patrimonio corrente contiene geometria dedicata del terrazzo e almeno un membro locale sporgente di 1.50 m (`ETW-FLT-E03`), per il quale lo stesso registro dichiara sezione e dettaglio di ancoraggio ND. I pilastri aggiunti a-d sono documentati in carpenteria come 30x30 e devono rimanere distinti dal modello di calcolo storico.

Non risulta, nell'indice delle fonti immutabili, una tavola autonoma dedicata alle armature delle balconate/solette a sbalzo. Le tavole di armatura disponibili sono principalmente armature travi per livello e armature di copertura. Pertanto non possiamo affermare che l'armatura della sagoma cementata sia disponibile finché non viene eseguito un controllo mirato dentro TAV-02A, TAV-034A, TAV-05A e negli eventuali particolari presenti nelle carpenterie.

Chiarimento qualificato dell'utente del 2026-08-23: le balconate sagomate di piano sono rilevabili dalle piante architettoniche e non risultavano considerate negli effetti del calcolo storico. Questo chiarimento viene trattato come `RIF_USER_QUALIFIED` fino al confronto diretto con piante architettoniche e relazione/calcoli. La geometria architettonica deve essere decodificata esplicitamente e confrontata con la carpenteria, non ignorata come informazione non strutturale.

Regola: se la ricerca non produce un dettaglio diretto, l'armatura delle balconate resta `ND`; non viene copiata da travi vicine né ricostruita per analogia. Eventuali dati successivi da pacometro/saggi saranno `MIS`, separati dal progetto originario.

## 5. Torrino scale

Esito: `PRESENTE NEL PATRIMONIO, NON ANCORA AUDITATO COME SOTTOSISTEMA SPECIALE`.

Il Registro Master contiene già la famiglia documentale dei pilastri del torrino scala, sezione 30x40 cm. Questo dato resta `DOC-famiglia`: non autorizza da solo l'assegnazione puntuale a tutti i membri del torrino.

Il torrino deve essere trattato come sottosistema strutturale distinto e verificato almeno per:

- pilastri e continuità verticale;
- travi/cordoli o bordi del vano scala;
- collegamento con G4, G5 e copertura;
- eventuale soletta/copertura propria;
- armature da TAV-07A e da eventuali dettagli di travi;
- masse e carichi propri/non strutturali;
- discontinuità o eccentricità introdotte rispetto al corpo principale.

Fonti target: TAV-05S, TAV-06S, TAV-06E, TAV-07A e piante architettoniche. Ogni associazione member-level va documentata separatamente.

## 6. Sbalzi di 1.50 m delle travi di gronda verso i terrazzi dell'ultimo livello

Chiarimento qualificato dell'utente del 2026-08-23: all'ultimo livello sono presenti sbalzi di 1.50 m delle travi di gronda verso i terrazzi; tali sbalzi hanno consentito di spostare verso l'esterno la tamponatura, aumentando la superficie utile dei tre appartamenti dell'ultimo livello, ciascuno dotato di terrazzo.

Stato attuale: `RIF_USER_QUALIFIED — DOCUMENTARY_CROSSCHECK_REQUIRED`.

Questa informazione non va confusa con `ETW-FLT-E03`, altro elemento locale sporgente di 1.50 m già registrato in ambito G1. Il nuovo fatto riguarda G5/ultimo livello e deve avere oggetti propri.

Controlli obbligatori:

1. localizzare i tre sbalzi su TAV-06S e sulle piante architettoniche;
2. stabilire se si tratta di vere travi di gronda a mensola, bordi strutturali di soletta o altra configurazione;
3. leggere sezione e armatura su TAV-06A senza ereditarle per analogia;
4. ricostruire la linea reale della tamponatura rispetto alla linea strutturale;
5. determinare la superficie aggiuntiva e la porzione a terrazzo per ciascuno dei tre appartamenti;
6. trasferire le conseguenze a M1-L: permanenti strutturali/non strutturali, tamponature, finiture, carichi d'uso e masse sismiche, mantenendo distinta la configurazione storicamente calcolata dallo stato costruito/documentato.

## 7. Reverse engineering della pratica storica e lettura incrociata delle fonti

Principio operativo introdotto: la pratica originaria può utilizzare rappresentazioni schematiche, ripetitive e semplificate. Questa caratteristica è una chiave di ricerca, non un'evidenza sufficiente per completare dati mancanti.

Il sistema deve quindi leggere congiuntamente:

`architettura -> carpenteria -> armature -> relazione/calcoli -> stato costruito/rilievo`

Le piante architettoniche hanno valore diretto per individuare sagome di balconi, terrazzi, posizione delle tamponature, distribuzione degli ambienti e superfici effettivamente utilizzate. Non costituiscono però prova automatica delle armature.

Ogni divergenza tra configurazione architettonica/carpenteria e schema di calcolo deve generare un residuo esplicito di tipo `HISTORICAL_MODEL_OMISSION_OR_SIMPLIFICATION`, da verificare prima di definire carichi e modello dello stato di fatto.

## 8. Valutazione complessiva

Il lavoro sulle armature delle travi ordinarie è avanzato e tracciato, ma M1-A non è ancora completo come modello dell'intero organismo strutturale. Il gap non riguarda più soprattutto le normali campate del telaio: riguarda gli elementi speciali, di bordo e i sottosistemi che lo schema di calcolo storico può avere semplificato o omesso.

Stato di gate:

`M1-A = IN_PROGRESS — HOLD_SPECIAL_FEATURE_AUDIT`

Il gate M1-A potrà chiudere soltanto dopo:

1. applicazione del chiarimento sulle sequenze sovrapposte TAV-034A e cross-check del tratto candidato 20-21;
2. inventario cornicioni G4 e G5 con classificazione strutturale/non strutturale;
3. binding armature TAV-05A ai cornicioni/travi G4 dove documentate;
4. binding TAV-06A a B017 impluvio, B036 e a ogni vero membro di colmo/gronda/cornicione identificato;
5. inventario balconate/sbalzi per livello mediante carpenterie e piante architettoniche e ricerca sistematica delle armature;
6. audit completo del torrino scale come sottosistema;
7. verifica documentale e modellazione dei tre sbalzi di gronda da 1.50 m verso i terrazzi dell'ultimo livello;
8. apertura dei corrispondenti item M1-L per carichi/massi non presenti nel modello storico, se la verifica conferma l'omissione;
9. marcatura esplicita `ND` per qualsiasi armatura speciale non reperita, senza completamenti per analogia.

Registro operativo associato: `data/canonical/M1A_SPECIAL_FEATURE_REINFORCEMENT_GAP_REGISTER_v1.csv`.

## Regola di continuità

Questa review non riapre M0-G. Una riapertura geometrica è consentita solo se una fonte primaria dimostra un elemento strutturale mancante nel baseline frame congelato. Elementi di piastra, balconi, cornicioni o masse non strutturali possono essere introdotti nel successivo modello analitico senza modificare il reticolo frame, purché geometria, provenienza e relazione con il baseline M0-G siano registrate separatamente.
