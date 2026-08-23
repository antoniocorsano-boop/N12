# M1-A — Review di completezza armature speciali

Data: 2026-08-23  
Ramo: `work/m0-global-model`  
Stato: `IN_PROGRESS — SPECIAL_FEATURE_AUDIT_ADVANCED`

## Scopo

Impedire la chiusura prematura di M1-A sulle sole travi ordinarie. Il controllo integra carpenterie, armature, piante architettoniche, sezioni e modello storico per: scala/torrino, cornicioni, balconate, terrazzi, impluvio, gronde, colmi e sbalzi di copertura.

## 1. TAV-034A — coppie sovrapposte e tratto 20-21

Il chiarimento qualificato dell'utente è acquisito: le coppie di numeri sovrapposte rappresentano due sequenze di sostegni cui si applica lo stesso schema di armatura.

Il cross-check con TAV-03S/TAV-04S mostra che 17-18, 18-19, 19-20 e la sequenza 24-23-22'-22-21 appartengono al reticolo ordinario. Il proseguimento 20-21 non compare invece nei ledger delle travi ordinarie e ricade nella zona del vano scala; la carpenteria documenta in tale zona una rampa/struttura scala larga 1.40 m.

Decisione corrente: il fatto di armatura 20-21 non viene cancellato e non genera una falsa trave piana M0-G. È trasferito a `M1A_STAIR_TOWER_SUBSYSTEM_CURRENT_v1.csv` come `SPECIAL_STAIR_SUBSYSTEM_MEMBER_CANDIDATE`, sezione/schedule 50x20 con staffe phi8/15 da TAV-034A, percorso 3D e ruolo da ricostruire.

M0-G resta congelato.

## 2. Balconate e terrazzi — geometria documentale vs armatura

Le piante architettoniche sono state renderizzate dal ramo immutabile e introdotte nel ciclo di controllo.

- TAV-01: pianta interrato; nessun sistema di balconate sporgenti documentato.
- TAV-02: piano terra; tre grandi zone esterne/terrazzo alle estremità delle tre ali.
- TAV-03: piano tipo; balconate sagomate direttamente documentate attorno ai tre appartamenti X, Y e K.
- TAV-04: piano attico; tre grandi terrazzi, uno per ciascuna ala attorno al nucleo scala.

La presenza e la sagoma diventano `DOC_ARCH_PRIMARY`. TAV-034A e TAV-05A sono tavole di armatura delle travi; nel controllo completo corrente non è stato individuato un particolare autonomo dell'armatura della soletta/balconata sagomata.

Decisione: armatura soletta/balconata = `ND_CURRENT`. Non viene ricostruita dalle travi adiacenti. Geometria e carichi restano comunque obbligatori nel modello; eventuali armature potranno provenire da un particolare successivamente recuperato o da MIS (pacometro/saggi).

Registri:

- `M1A_ARCHITECTURAL_SPECIAL_FEATURES_CURRENT_v1.csv`
- `M1A_BALCONY_CORNICE_REINFORCEMENT_SOURCE_AUDIT_v1.csv`
- `M1L_ARCHITECTURAL_ENVELOPE_LOAD_ZONES_v1.csv`

## 3. Torrino scale e sottosistema scala

Il torrino non è più una nota accessoria: è un sottosistema esplicito.

Fonti correnti:

- TAV-04: nucleo scala in pianta;
- TAV-03S/TAV-04S: geometria del vano/rampa ai livelli G2/G3;
- TAV-06E: sviluppo verticale del sistema scala e configurazione superiore;
- Registro Master/TAV-07A: famiglia pilastri torrino 30x40 cm `DOC-famiglia`.

La famiglia 30x40 non viene assegnata automaticamente a tutti i pilastri 30x40 dell'edificio. Il binding member-level resta aperto e deve seguire continuità planimetrica/verticale documentata.

Il candidato 20-21 TAV-034A è conservato dentro questo sottosistema fino alla ricostruzione di percorso, quota Z e funzione (trave di pianerottolo, bordo/rampa o altro elemento scala).

Registro corrente: `M1A_STAIR_TOWER_SUBSYSTEM_CURRENT_v1.csv`.

## 4. Copertura — colmi

I tre elementi `LINEA DI COLMO` sono stati riletti direttamente su TAV-06S.

Esito: le frecce indicano linee tratteggiate di piega/falda, graficamente distinte dalle aste ordinarie del reticolo. TAV-06A non mostra un elemento separato esplicitamente identificato come trave di colmo.

Decisione corrente:

`RIDGE_AXIS = ROOF_GEOMETRIC_FOLD_LINE`  
`SEPARATE_FRAME_MEMBER = NO_BY_CURRENT_SOURCE`

I colmi restano necessari per la geometria 3D della copertura e le quote delle falde, ma non generano tre nuove travi né tre nuovi oggetti di armatura.

Registro: `M1A_G5_RIDGE_GRONDA_INTERPRETATION_CURRENT_v1.csv`.

## 5. Copertura — gronde, cornicione e sbalzi delle travi inclinate

Sono ora distinti tre oggetti diversi.

### 5.1 Otto estremità a sbalzo delle travi inclinate

TAV-06A documenta quattro sequenze:

- 23-15-7;
- 22-14-6;
- 3-11-20;
- 2-10-18.

Ogni sequenza prosegue oltre entrambi gli appoggi estremi: risultano quindi **8 estremità a sbalzo documentate**. Sezione 30x50 e staffe phi6/20 sono documentali per la famiglia.

La lunghezza 1.50 m fornita dall'utente resta `RIF_USER_QUALIFIED` fino a una quota primaria diretta. Anche il legame fra ciascuna estremità e le tre aree di terrazzo/tamponatura resta da cross-registrare.

Registro: `M1A_G5_EAVE_CANTILEVER_ENDS_CURRENT_v1.csv`.

### 5.2 Gronda come linea/bordo di copertura

I tre `GRONDA_EDGE_SET` restano oggetti geometrici di bordo. Non viene assunto un unico asse longitudinale di trave se la fonte non lo documenta.

### 5.3 Particolare diretto di cornicione/gronda

TAV-06S contiene almeno un particolare a L del bordo esterno con:

- proiezione 120 cm;
- spessore indicato 15 cm;
- 6phi10 longitudinali;
- staffe phi6 lunghe.

Questo è il primo dettaglio diretto di armatura di un elemento perimetrale G5. Deve essere mappato lungo il perimetro e non va confuso con gli otto sbalzi delle travi inclinate.

## 6. Impluvio B017 = 12-19

Geometria/ruolo: `IMPLUVIO`, sezione 30x50 `SUPPORTED`.

La TAV-06A contiene un ulteriore schema inclinato 30x50 con staffe phi6/15 (`T6A-G03`), ma mostra due stazioni di appoggio e un'estremità libera a sbalzo e non possiede etichette di estremità leggibili. Non è un direct topology match con il membro canonico B017=12-19.

Decisione: non attribuire T6A-G03 a B017. Armatura B017 = `ND_CURRENT` fino a nuova evidenza diretta o MIS.

## 7. Trave obliqua B036 = 19-26

B036 è chiusa nel nucleo documentale:

- sezione 30x50;
- staffe phi6/15;
- due barre diritte 2phi16 L=725 cm;
- secondo sistema 2phi16 L=725 cm;
- due sistemi 2phi16 sagomati.

Le diagonali non quotate restano watch e non vengono completate per simmetria.

Registro: `M1A_G5_SPECIAL_REINFORCEMENT_CURRENT_v1.csv`.

## 8. Carichi e differenza modello storico -> configurazione documentata

È stato aperto il ledger `M1L_ARCHITECTURAL_ENVELOPE_LOAD_ZONES_v1.csv`.

Sono già separati:

- interrato;
- terrazzi/zone esterne del piano terra;
- balconate sagomate dei piani tipo;
- tre terrazzi dell'attico;
- torrino/nucleo scala;
- estremità a sbalzo delle travi di copertura.

Non sono ancora assegnati valori numerici di carico. Prima si congela geometria e classificazione strutturale; poi M1-L distinguerà carichi storicamente considerati, carichi documentati nello stato costruito e delta omessi/semplificati.

La segnalazione dell'utente sull'omissione storica dei carichi delle balconate e della configurazione superiore resta `RIF_USER_QUALIFIED` finché il confronto con le pagine di carico originali non la conferma o la contraddice.

## 9. Stato del gate

`M1-A = IN_PROGRESS — SPECIAL_FEATURE_AUDIT_ADVANCED`

Punti già chiusi o trasformati in stato esplicito:

- semantica coppie TAV-034A: risolta;
- 20-21: trasferito al sottosistema scala, non più blocco del reticolo ordinario;
- balconate/terrazzi: presenza geometrica DOC;
- armatura soletta/balconata: ND corrente dopo audit delle tavole travi;
- colmi: risolti come linee geometriche di falda, nessuna trave separata corrente;
- B036: nucleo armatura DOC;
- B017: armatura ND corrente, nessuna falsa attribuzione;
- 8 estremità di gronda delle travi inclinate: DOC come presenza/host/famiglia di armatura;
- un particolare gronda/cornicione G5: DOC 120x15, 6phi10 + staffe phi6 lunghe;
- torrino/scala: sottosistema canonico attivo.

Residui prioritari prima del gate M1-A:

1. binding geometrico 3D del sottosistema scala/torrino e del candidato 20-21;
2. mappatura del particolare 120x15 lungo i bordi G5;
3. cross-registration degli 8 sbalzi di copertura con le tre aree di terrazzo e verifica documentale della quota 1.50 m;
4. classificazione G4 dei perimetri/cornicioni e ordinario binding TAV-05A;
5. ricerca finale di particolari balconate; in assenza, mantenimento definitivo ND documentale;
6. completamento del member-level reinforcement mapping ordinario dopo la chiusura dei sottosistemi speciali.

## Regola di continuità

M0-G resta frozen. Una riapertura avviene soltanto se una fonte primaria dimostra una vera asta del frame ordinario mancante. Scale, piastre, balconi, cornicioni, linee di falda e masse/carichi entrano nei rispettivi sottosistemi senza deformare artificialmente il reticolo frame.
