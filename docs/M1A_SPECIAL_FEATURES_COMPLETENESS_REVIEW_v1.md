# M1-A — Review di completezza armature speciali

Data: 2026-08-23  
Ramo: `work/m0-global-model`  
Stato: `HOLD_SPECIAL_FEATURE_AUDIT_BEFORE_M1A_GATE`

## Scopo

Verifica preventiva richiesta prima di proseguire la trascrizione ordinaria delle armature. Ambiti controllati: semantica delle coppie di numeri sovrapposte in TAV-034A, cornicioni/perimetri ai livelli in cui compaiono in carpenteria, impluvi/gronde/colmi di copertura e relativa armatura, balconate/sbalzi con sagoma cementata o sagomata, terrazzo/addizioni.

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

Sono censiti tre `GRONDA_EDGE_SET` con identità DOC. Il centrolinea metrico e la quota Z restano volutamente ND perché una singola asse di trave non è attualmente documentato.

Armatura: `NON CHIUSA`. Occorre ricercare il dettaglio diretto su TAV-06A e distinguere la trave/cordolo di gronda dall'eventuale bordo della soletta o dal cornicione.

### Trave obliqua 19-26

`G5-B036 = 19-26`, 30x50, è invece una vera trave ordinaria obliqua documentata e già conteggiata una sola volta. La sua armatura TAV-06A deve ancora essere portata nel registro M1-A a livello barra-per-barra.

## 4. Balconate e sbalzi con sagoma cementata/sagomata

Esito: `PRESENZA DA INVENTARIARE; ARMATURA NON DOCUMENTATA CANONICAMENTE`.

Il patrimonio corrente contiene geometria dedicata del terrazzo e almeno un membro locale sporgente di 1.50 m (`ETW-FLT-E03`), per il quale lo stesso registro dichiara sezione e dettaglio di ancoraggio ND. I pilastri aggiunti a-d sono documentati in carpenteria come 30x30 e devono rimanere distinti dal modello di calcolo storico.

Non risulta, nell'indice delle fonti immutabili, una tavola autonoma dedicata alle armature delle balconate/solette a sbalzo. Le tavole di armatura disponibili sono principalmente armature travi per livello e armature di copertura. Pertanto non possiamo affermare che l'armatura della sagoma cementata sia disponibile finché non viene eseguito un controllo mirato dentro TAV-02A, TAV-034A, TAV-05A e negli eventuali particolari presenti nelle carpenterie.

Regola: se la ricerca non produce un dettaglio diretto, l'armatura delle balconate resta `ND`; non viene copiata da travi vicine né ricostruita per analogia. Eventuali dati successivi da pacometro/saggi saranno `MIS`, separati dal progetto originario.

## 5. Valutazione complessiva

Il lavoro sulle armature delle travi ordinarie è avanzato e tracciato, ma M1-A non è ancora completo come modello dell'intero organismo strutturale. Il gap non riguarda più soprattutto le normali campate del telaio: riguarda gli elementi speciali e di bordo.

Stato di gate consigliato:

`M1-A = IN_PROGRESS — HOLD_SPECIAL_FEATURE_AUDIT`

Il gate M1-A potrà chiudere soltanto dopo:

1. applicazione del chiarimento sulle sequenze sovrapposte TAV-034A e cross-check del tratto candidato 20-21;
2. inventario cornicioni G4 e G5 con classificazione strutturale/non strutturale;
3. binding armature TAV-05A ai cornicioni/travi G4 dove documentate;
4. binding TAV-06A a B017 impluvio, B036 e a ogni vero membro di colmo/gronda/cornicione identificato;
5. inventario balconate/sbalzi per livello e ricerca sistematica delle armature;
6. marcatura esplicita `ND` per qualsiasi armatura speciale non reperita, senza completamenti per analogia.

Registro operativo associato: `data/canonical/M1A_SPECIAL_FEATURE_REINFORCEMENT_GAP_REGISTER_v1.csv`.

## Regola di continuità

Questa review non riapre M0-G. Una riapertura geometrica è consentita solo se la carpenteria primaria dimostra un elemento strutturale mancante. Cornicioni o balconi modellabili come piastra/sbalzo di soletta possono essere introdotti nel successivo handoff al solver senza modificare il reticolo frame, purché la loro geometria e provenienza siano registrate separatamente.
