# N12 — Tavole strutturali master

Versione: `TAV-MASTER-0001` — 2026-08-16
Stato: `IN REDAZIONE CONTROLLATA`

## Regola generale

Il presente indice traduce il patrimonio canonico N12 nel fascicolo grafico. Nessun valore ND/INC viene completato per analogia. Ogni tavola usa gli ID canonici, i fili fissi dei pilastri e la classificazione DOC/MIS/RIF/INF/ND.

## TAV-00 — Copertina e indice

Titolo: **RECUPERO E VALORIZZAZIONE DELL'EDIFICIO ESISTENTE IN C.A.**
Sottotitolo: **Dalla conoscenza della struttura alla sicurezza, dalla cura dell'esistente al futuro.**
Parole chiave: Conoscenza · Sicurezza · Durabilità · Recupero · Valorizzazione.

## TAV-S01 — Impalcato di fondazione / attacco a terra

Contenuti minimi:
- orientamento e riferimento planimetrico globale;
- fili fissi canonici dei pilastri;
- impronte e nodi documentabili;
- fondazioni soltanto dove supportate da fonte;
- campitura ND per geometrie/sezioni non documentate;
- rimandi TAV-Fxx.

Stato tecnico: `PRE-EMISSIONE`; non attribuire tipologie di fondazione non documentate.

## TAV-S02 — Carpenteria piano terra

Contenuti minimi:
- perimetro strutturale e corpi articolati secondo topologia M0-G;
- pilastri sui rispettivi fili fissi;
- travi e campate documentate;
- vano scala e discontinuità geometriche;
- ID canonici;
- quote planimetriche documentate;
- Nord e riferimenti ai telai originali.

## TAV-S03 — Carpenteria piano primo

Stessa grammatica di S02. Evidenziare continuità/discontinuità verticale rispetto al piano terra e mantenere separata l'informazione inferita da quella documentale.

## TAV-S04 — Carpenteria piano secondo

Stessa grammatica di S02-S03. Verificare la corrispondenza puntuale degli elementi verticali prima dell'emissione.

## TAV-S05 — Carpenteria piano terzo / ultimo impalcato tipo

Rappresentare esclusivamente la configurazione supportata dal modello canonico e dalle tavole originali. Le variazioni locali devono essere marcate con provenienza.

## TAV-S06 — Copertura

Contenuti:
- sagoma e struttura di copertura documentabile;
- elementi verticali emergenti/torrino scala se presenti nel dato canonico;
- fili fissi di continuità;
- quote e sezioni solo documentate;
- rinvii alle viste tridimensionali.

## TAV-M01 — Modello geometrico globale M0-G

Tavola di controllo principale:
- pianta globale di riferimento;
- sistema di coordinate;
- fili fissi dei pilastri;
- nodi canonici;
- corrispondenza fra livelli;
- orientamento;
- legenda degli stati DOC/MIS/RIF/INF/ND.

Questa tavola costituisce il ponte tra rilievo/documentazione e inserimento in EdiLus-EE.

## TAV-M02 — Modello tridimensionale e livelli

Viste richieste:
- assonometria globale;
- vista strutturale senza solai/opacità ridotta per leggere i telai;
- esploso verticale dei livelli;
- evidenza del vano scala e delle irregolarità geometriche;
- legenda degli elementi ancora non congelati.

## TAV-M03 — Telai longitudinali

Ricostruzione dei telai longitudinali documentati con:
- numerazione nodi originale e ID canonico affiancati;
- campate;
- interpiani;
- sezioni note;
- carichi originali solo come dato documentale, senza assumerli automaticamente come carichi di verifica.

## TAV-M04 — Telai trasversali

Stessa struttura della TAV-M03 per i telai trasversali, compreso il Telaio 5 e le relative corrispondenze con la pianta.

## TAV-M05 — Corrispondenza modello ↔ EdiLus-EE

Tabella grafica di interoperabilità:
- ID N12;
- livello;
- filo fisso;
- nodo iniziale/finale;
- tipo elemento;
- sezione e stato della sezione;
- provenienza;
- identificativo EdiLus quando assegnato.

## TAV-R01 — Quadro sezioni pilastri

Non è un abaco ricostruito per analogia. Deve distinguere:
- sezioni documentate;
- sezioni riferite;
- sezioni inferite;
- sezioni ND/INC.

Il torrino scala 30×40 e le famiglie del corpo principale devono mantenere esattamente lo stato di evidenza registrato nel Registro Master.

## TAV-R02 — Quadro sezioni travi

Raccogliere le sezioni desumibili dalle tavole originali ad alta risoluzione e dai telai, con riferimento puntuale alla fonte.

## TAV-F01 — Fondazioni

Da emettere tecnicamente solo dopo il congelamento della tipologia, geometria e quote documentate. Fino ad allora è ammessa una tavola di stato conoscitivo con ND espliciti.

## Regole grafiche comuni

1. Cartiglio unico secondo `docs/PIANO_EDITORIALE_TAVOLE_CARTIGLIO_COPERTINA.md`.
2. Nord obbligatorio nelle piante.
3. Fili fissi visibili e gerarchicamente distinti dalla sagoma degli elementi.
4. ID canonici prevalenti; sigle originali conservate come riferimento secondario.
5. DOC/MIS/RIF/INF/ND distinguibili graficamente e in legenda.
6. Nessuna quota, sezione o materiale inventato per chiudere graficamente una tavola.
7. Ogni dettaglio deve avere codice stabile `DET-xx`; ogni sezione `SEZ-x`.
8. Ogni PDF emesso deve riportare revisione, data, nome file canonico e fonte.

## Gate di emissione

Per ciascuna tavola: `GEOMETRIA → ID/FILI FISSI → QUOTE → FONTI → RIFERIMENTI INCROCIATI → CARTIGLIO → CONTROLLO REGISTRO MASTER → PDF`.

Una tavola che contiene ND/INC può essere emessa come **STATO CONOSCITIVO**, ma non come tavola costruttiva definitiva.