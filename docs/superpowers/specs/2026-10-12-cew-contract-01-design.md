# CEW-CONTRACT-01 — Contratto logico minimo del Civil Existing Workflow

**Data:** 12 ottobre 2026  
**Stato:** design approvato in chat; specifica scritta in attesa di revisione umana finale  
**Caso pilota:** N12  
**Ambito:** contratto logico indipendente dalla tecnologia per conoscenza, struttura, versionamento, scenari, modelli derivati e assurance.

## 1. Scopo

CEW-CONTRACT-01 definisce il nucleo concettuale di CEW prima di scegliere database, formati di serializzazione, IFC, CAD, solver o altri componenti specialistici.

Il contratto deve stabilire:

- quali entità esistono;
- come sono collegate;
- quali invarianti non possono essere violate;
- come si rappresentano provenienza, incertezza, conflitti e decisioni;
- come si versiona il patrimonio canonico;
- come si generano scenari e modelli derivati;
- come si rende riproducibile e auditabile una trasformazione tecnica.

Il contratto deve essere generalizzabile oltre N12. N12 è il banco di prova, non il modello concettuale.

## 2. Non-obiettivi V1

CEW-CONTRACT-01 non definisce:

- schema PostgreSQL/PostGIS;
- JSON Schema o altro formato di serializzazione;
- mapping RDF/W3C PROV fisico;
- schema IFC o mapping IfcOpenShell;
- adapter OpenSees, EdiLus, Code_Aster o altri solver;
- adapter CAD/DXF/DWG;
- dettaglio B-Rep o kernel geometrico;
- mesh o elementi finiti;
- formule normative;
- motore di verifica normativa;
- distribuzioni probabilistiche obbligatorie;
- Investigation Planner o Value of Information.

Questi aspetti possono essere affrontati solo dopo la qualifica del contratto logico.

## 3. Principi invarianti

1. Nessuna proprietà canonica senza provenienza.
2. Nessun dato inferito può diventare documentale senza nuova evidenza.
3. Ogni proprietà canonica appartiene a un oggetto strutturale identificabile.
4. Le revisioni non cancellano lo stato precedente: producono nuove versioni.
5. Uno Scenario non modifica il patrimonio canonico: applica override espliciti e reversibili.
6. Ogni ModelGeneration nasce da uno Snapshot canonico esplicito.
7. Ogni Result deve poter risalire alla catena di provenienza che lo ha prodotto.
8. La stessa Evidence può sostenere più interpretazioni, anche conflittuali.
9. Observation, Claim e Decision restano concetti distinti.
10. CAD, IFC, modelli analitici e solver sono proiezioni o trasformazioni, non fonti di verità canonica.
11. Un Receipt prova il processo eseguito, non sostituisce il giudizio tecnico.
12. CEW non risolve l’incertezza cancellandola: la tratta tramite evidenza, decisione, scenario o accettazione esplicita.

## 4. Famiglie concettuali

Il contratto V1 è suddiviso in cinque famiglie:

### 4.1 Source / Evidence

Rappresentano la fonte originale e le porzioni localizzate della fonte utilizzate nel processo conoscitivo.

### 4.2 Knowledge

Rappresentano osservazioni, interpretazioni, ipotesi, conflitti, decisioni e proprietà canoniche.

### 4.3 Structural Object

Rappresentano l’opera fisica e le relazioni strutturali persistenti.

### 4.4 Model State

Rappresentano snapshot, scenari, generazioni del modello, proiezioni, run e risultati.

### 4.5 Assurance

Rappresentano controlli, revisioni e ricevute di processo.

## 5. Modello epistemico minimo

### 5.1 Source

Fonte originale immutabile o trattata come tale: PDF, tavola, DXF/DWG, fotografia, rilievo, certificato di prova, relazione, CSV o altra fonte tecnica.

Attributi logici minimi:

- identificatore stabile;
- tipo;
- origine;
- hash quando applicabile;
- data di acquisizione;
- versione/edizione quando disponibile.

### 5.2 Evidence

Porzione localizzata di una Source che supporta una conoscenza: pagina, riquadro, riga tabellare, entità CAD, regione di immagine, misura o campione.

Invariante: una Evidence appartiene a una sola Source.

### 5.3 Observation

Ciò che viene letto, misurato o rilevato dall’Evidence senza assumerlo ancora come verità canonica.

Esempio: «nel riquadro compare 40×50 cm».

### 5.4 Claim

Interpretazione proposta a partire da una o più Observation/Evidence.

Esempio: «la sezione del pilastro C14 è 40×50 cm».

Più Claim possono riguardare la stessa proprietà e possono essere incompatibili.

### 5.5 Conflict

Oggetto di primo livello che rappresenta incompatibilità tra Claim, Observation o proprietà candidate.

Stati minimi:

- `OPEN`;
- `UNDER_REVIEW`;
- `RESOLVED`;
- `ACCEPTED_UNCERTAINTY`.

Un Conflict conserva almeno:

- oggetti coinvolti;
- proprietà contestata;
- proposizioni incompatibili;
- evidenze di supporto;
- stato;
- impatto potenziale;
- Decision finale, se presente.

### 5.6 Assumption

Ipotesi esplicita necessaria per uno Scenario o una trasformazione quando la conoscenza è insufficiente.

Una Assumption non è una CanonicalProperty e non modifica il canonico.

Deve poter dichiarare:

- oggetto/proprietà interessata;
- motivazione;
- valore o alternativa assunta;
- campo di applicazione;
- Scenario;
- evidenze disponibili;
- stato epistemico;
- intervallo o alternative quando disponibili.

### 5.7 Decision

Atto identificabile con cui una Claim o un Conflict viene valutato.

Esiti minimi:

- `ACCEPT`;
- `REJECT`;
- `SUPERSEDE`;
- `DEFER`;
- `KEEP_UNCERTAIN`;
- `REQUIRE_INVESTIGATION`;
- `ALLOW_SCENARIO_ONLY`;
- `MERGE_OBJECTS`;
- `SPLIT_OBJECT`.

Una Decision può concludere che l’incertezza deve restare aperta.

### 5.8 CanonicalProperty

Proprietà ammessa nello stato conoscitivo corrente, sempre riferita a uno StructuralObject e sempre derivata da una Decision.

Catena minima obbligatoria:

`Evidence → Observation → Claim → Decision → CanonicalProperty`

Sono vietate scorciatoie quali:

`Source → CanonicalProperty`

oppure:

`AI extraction → CanonicalProperty`.

## 6. Stato epistemico e qualità

Stati minimi:

- `DOC` — documentale;
- `MIS` — misurato;
- `RIF` — riferito;
- `INF` — inferito;
- `INC` — incerto;
- `ND` — non disponibile.

Lo stato epistemico descrive **come** una proprietà è conosciuta, non la sua affidabilità complessiva.

Regole:

- `DOC` richiede evidenza documentale;
- `MIS` richiede misura o prova riferibile;
- `RIF` richiede fonte dichiarativa/riferita;
- `INF` conserva la regola o il ragionamento inferenziale;
- `INC` esplicita la natura dell’incertezza;
- `ND` non significa zero e non autorizza default impliciti.

Stato epistemico e confidenza sono separati. Non esiste in V1 un confidence score numerico obbligatorio privo di metodo di calibrazione.

## 7. Tipi di incertezza

Il contratto distingue almeno:

1. **incertezza epistemica** — conoscenza insufficiente;
2. **incertezza di misura** — precisione finita di misura/prova;
3. **variabilità fisica** — dispersione reale della proprietà.

Rappresentazione minima:

- tipo;
- valore nominale, se esiste;
- intervallo, se noto;
- unità;
- origine;
- metodo di stima;
- oggetto/proprietà cui si riferisce.

Le distribuzioni probabilistiche sono rinviate.

## 8. StructuralObject

StructuralObject identifica persistentemente un elemento fisico o concettuale dell’opera.

Tipi minimi V1:

- `Building`;
- `StructuralUnit`;
- `Level`;
- `Node`;
- `Column`;
- `Beam`;
- `Wall`;
- `Slab`;
- `FoundationElement`;
- `Section`;
- `Material`;
- `Reinforcement`;
- `LoadObject`.

Non appartengono al nucleo V1:

- fibre FEM;
- elementi finiti;
- mesh;
- hinge plastici;
- leggi costitutive solver-specifiche;
- combinazioni normative;
- entità IFC-specifiche.

### 8.1 Identità stabile

L’identità dello StructuralObject sopravvive alle revisioni delle sue proprietà purché continui a rappresentare lo stesso elemento fisico dell’opera.

Alias come “P14”, “Telaio 5” o “G3” non sono identità primarie.

Merge e split richiedono Decision esplicita e tracciata.

### 8.2 Oggetto separato dalla geometria

Un Column, Beam o altro StructuralObject non coincide con il suo solido 3D, entità CAD, oggetto IFC o elemento FEM.

Geometrie e rappresentazioni sono proprietà o proiezioni dello stesso oggetto persistente.

### 8.3 Section e Material condivisibili

Section e Material sono oggetti riutilizzabili referenziati da più elementi tramite Relationship.

## 9. Relationship

Relazioni semantiche minime:

- `part_of`;
- `belongs_to_level`;
- `connects_to`;
- `supported_by`;
- `supports`;
- `spans_between`;
- `uses_section`;
- `uses_material`;
- `reinforced_by`;
- `derived_from`;
- `supersedes`.

Una Relationship può avere provenienza, stato epistemico, Claim, Conflict, Decision e versione propri.

Topologia e geometria restano concetti separati: CEW può conoscere che due elementi sono connessi anche se la geometria non è ancora determinata con precisione.

## 10. Cardinalità fondamentali

- una Source può contenere molte Evidence;
- una Evidence appartiene a una sola Source;
- una Evidence può sostenere più Observation;
- una Observation può generare più Claim;
- un Claim può essere supportato da più Evidence/Observation;
- un Claim può riferirsi a uno o più StructuralObject;
- una Decision può valutare uno o più Claim correlati;
- una CanonicalProperty appartiene a un solo StructuralObject;
- uno StructuralObject può avere molte CanonicalProperty;
- una CanonicalProperty può succedere a una versione precedente senza cancellarla;
- un Conflict collega almeno due proposizioni incompatibili;
- uno Scenario può applicare più override;
- una ModelGeneration riferisce un CanonicalSnapshot e al massimo uno Scenario esplicito;
- un SolverRun deriva da una ModelGeneration;
- un Result deriva da un SolverRun;
- una Verification valuta uno o più Result o artefatti derivati.

## 11. CanonicalSnapshot

CanonicalSnapshot è una fotografia coerente e immutabile del patrimonio canonico.

Contiene almeno:

- StructuralObject attivi;
- versioni delle CanonicalProperty;
- versioni delle Relationship;
- Decision applicate;
- Conflict ancora aperti;
- stato epistemico rilevante;
- versione logica/timestamp.

Uno Snapshot referenziato da una ModelGeneration non viene modificato retroattivamente.

## 12. Scenario

Scenario applica variazioni esplicite rispetto a un CanonicalSnapshot senza modificarlo.

Formalmente:

`Scenario = CanonicalSnapshot base + override dichiarati`

Gli override devono essere:

- espliciti;
- localizzati;
- motivati;
- reversibili;
- versionati;
- riconducibili a una Assumption o Decision.

## 13. ModelGeneration

ModelGeneration registra l’atto con cui CEW produce un modello derivato da uno stato conoscitivo preciso.

Deve dichiarare almeno:

- `canonical_snapshot_id`;
- eventuale `scenario_id`;
- profilo di generazione;
- adattatore;
- versione adattatore;
- parametri;
- artefatti prodotti;
- hash output quando applicabile;
- warning/degradazioni;
- timestamp.

## 14. Projection

Projection è una rappresentazione derivata: CAD, IFC, B-Rep, modello analitico, input solver, vista o altro artefatto specialistico.

Una Projection non può introdurre nuova conoscenza canonica con backfill implicito. Qualsiasi nuova informazione deve rientrare nel ciclo epistemico.

## 15. SolverRun

SolverRun registra una esecuzione riproducibile riferita a una ModelGeneration.

Deve dichiarare almeno:

- ModelGeneration;
- solver e versione;
- input/hash;
- parametri;
- ambiente rilevante;
- output grezzo;
- stato;
- warning/errori.

È vietato il concetto di analisi sul “modello corrente” mutabile: ogni run parte da uno Snapshot esplicito.

## 16. Result

Result non è un numero isolato. Deve poter essere riferito a:

- SolverRun;
- StructuralObject o gruppo di oggetti;
- tipo di risultato;
- unità;
- caso/combinazione;
- eventuale step/modo;
- qualità o validità del risultato.

Il mapping deve permettere il percorso bidirezionale:

`CEW Object → solver entity → Result → CEW Object`.

## 17. Verification

Verification è un controllo tecnico o logico indipendente dal Receipt.

Tipi minimi:

- deterministica;
- geometrica;
- semantica;
- normativa;
- cross-tool;
- human review;
- regression.

Esiti minimi:

- `PASS`;
- `FAIL`;
- `WARNING`;
- `REVIEW_REQUIRED`;
- `NOT_APPLICABLE`.

Ogni Verification dichiara:

- oggetto verificato;
- criterio;
- versione;
- tolleranza quando applicabile;
- metodo/strumento;
- esito.

## 18. Receipt

Receipt è la registrazione auditabile di una trasformazione eseguita.

Contenuto minimo:

- identificatore;
- tipo di trasformazione;
- input/versioni/hash;
- strumento/adattatore e versione;
- parametri;
- ambiente rilevante;
- timestamp;
- output/hash;
- Verification eseguite;
- esito;
- warning/errori;
- autore/agente/processo;
- Decision associata quando richiesta.

Trasformazioni che devono poter produrre Receipt:

- estrazione documentale;
- promozione canonica;
- generazione geometrica;
- export CAD;
- export IFC;
- generazione modello analitico;
- esecuzione solver;
- import risultati;
- verifica automatica;
- migrazione/versionamento dati.

Un Receipt può esistere anche per trasformazioni fallite o che richiedono revisione.

## 19. Invalidazione e successione

Nuove evidenze o verifiche non cancellano artefatti precedenti.

Oggetti, risultati o Receipt possono essere marcati come:

- `superseded`;
- `invalidated`;
- `impacted`;
- `needs_review`.

La storia resta consultabile.

## 20. Catena di provenienza end-to-end

Per ogni risultato tecnico significativo deve essere possibile ricostruire:

`Result`
→ `SolverRun`
→ `ModelGeneration`
→ `Scenario` quando presente
→ `CanonicalSnapshot`
→ `CanonicalProperty`
→ `Decision`
→ `Claim`
→ `Observation`
→ `Evidence`
→ `Source`.

Invariante:

> Nessun Result è valido in CEW se non è possibile identificare in modo univoco Snapshot canonico, Scenario se presente, ModelGeneration e SolverRun che lo hanno prodotto.

## 21. Regola di aggiornamento non distruttivo

Quando una nuova evidenza contraddice una proprietà canonica:

1. si crea una nuova Observation/Claim;
2. si apre o aggiorna un Conflict;
3. si emette una nuova Decision;
4. si crea una nuova CanonicalProperty se necessario;
5. si crea un nuovo CanonicalSnapshot;
6. ModelGeneration, SolverRun e Result precedenti restano associati al vecchio Snapshot.

## 22. N12 come caso pilota

Il contratto deve poter rappresentare N12 senza campi specifici del progetto.

Devono essere rappresentabili almeno:

- edificio e livelli;
- telai, travi, pilastri e fondazioni;
- nodi e relazioni topologiche;
- sezioni condivise;
- proprietà `DOC`, `MIS`, `INF`, `INC`, `ND`;
- più fonti per lo stesso oggetto;
- conflitti tra fonti;
- dati mancanti;
- versioni successive della stessa proprietà;
- Scenario alternativi;
- una ModelGeneration congelata;
- SolverRun, Result, Verification e Receipt.

Termini come `T5`, `G3`, `TAV.5` sono alias, viste o provenienze, non concetti fondamentali del contratto.

## 23. Test di conformità CEW-CONTRACT-01

Il gate deve includere almeno i seguenti test.

### 23.1 Rappresentabilità N12

Tutti i casi reali sopra devono essere rappresentabili senza eccezioni o campi N12-specifici.

### 23.2 Provenienza completa

Un Result reale deve essere percorribile all’indietro fino alla Source originale.

### 23.3 Conflict reale

Due fonti incompatibili devono coesistere senza scelta prematura, con Conflict e Scenario alternativi.

### 23.4 Aggiornamento non distruttivo

Una nuova evidenza deve produrre nuovo stato canonico senza riscrivere Snapshot, run o risultati precedenti.

### 23.5 Identità strutturale

Variazioni di geometria, sezione, materiale o orientamento non cambiano l’identità dell’elemento fisico. Merge/split richiedono Decision esplicita.

### 23.6 Indipendenza dallo strumento

Lo stesso Snapshot deve poter produrre almeno due proiezioni concettualmente diverse senza introdurre nel nucleo concetti specifici di CAD, IFC, OpenSees, EdiLus o altro software.

### 23.7 Incertezza

Devono essere distinguibili:

- dato assente;
- dato documentato ma conflittuale;
- misura con tolleranza;
- inferenza;
- assunzione valida solo nello Scenario.

### 23.8 Relationship incerta

Una connessione strutturale incerta deve poter avere Evidence, stato epistemico, Conflict e Decision propri.

### 23.9 Riproducibilità

Data una ModelGeneration devono essere determinabili Snapshot, Scenario, adapter, versione, parametri e output. Data una SolverRun devono essere determinabili input, solver/versione, parametri, output e verifiche.

### 23.10 Assurance

Almeno una trasformazione deve attraversare input → output → Verification → Receipt, includendo anche un caso `FAIL` o `REVIEW_REQUIRED`.

### 23.11 Minima sufficienza

Ogni entità V1 deve essere necessaria ad almeno un caso reale del gate. Entità prive di giustificazione vengono rinviate.

## 24. Criterio di uscita del gate

CEW-CONTRACT-01 passa solo se:

- tutti i casi di conformità sono rappresentabili;
- non esistono dipendenze tecnologiche nel nucleo logico;
- non esistono scorciatoie che saltano provenienza o Decision;
- non esistono campi specifici N12 nel contratto generale;
- ogni entità ha uno scopo dimostrabile;
- almeno un caso end-to-end reale N12 attraversa l’intera catena.

Il risultato atteso del gate è:

> Il contratto rappresenta correttamente conoscenza, struttura, versioni, conflitti, scenari, modelli e assurance su un caso reale, senza dipendere da uno specifico software.

## 25. Decisioni congelate da questa specifica

Sono congelate come design CEW-CONTRACT-01:

1. contratto logico indipendente dalla tecnologia;
2. catena `Source → Evidence → Observation → Claim → Decision → CanonicalProperty`;
3. identità persistente di StructuralObject separata dalle rappresentazioni;
4. proprietà e relazioni versionabili e potenzialmente incerte;
5. aggiornamento non distruttivo del patrimonio canonico;
6. Scenario come override esplicito senza mutazione del canonico;
7. ModelGeneration sempre riferita a Snapshot esplicito;
8. provenienza completa dei Result;
9. distinzione tra Verification e Receipt;
10. Receipt come prova di processo, non come certificazione automatica della correttezza ingegneristica;
11. N12 come banco di prova e non come modello concettuale;
12. nessuna tecnologia specialistica adottata dal contratto.

## 26. Decisioni esplicitamente rinviate

Restano fuori da CEW-CONTRACT-01 e richiedono gate dedicati:

- database fisico;
- serializzazione;
- mapping W3C PROV;
- mapping IFC;
- CAD adapter;
- Geometry-as-Code;
- solver primario;
- adapter EdiLus/OpenSees/Code_Aster;
- motore normativo;
- distribuzioni probabilistiche;
- Investigation Planner;
- scelta di tecnologie come PostgreSQL/PostGIS, ezdxf, CADCraft, build123d, IfcOpenShell, OpenSeesPy o equivalenti.

## 27. Dipendenze successive previste

Dopo l’approvazione scritta della presente specifica, i gate successivi previsti sono:

1. `CEW-CONTRACT-01` — implementazione/qualifica del contratto;
2. `CEW-EVIDENCE-01` — acquisizione documentale e DXF;
3. `CEW-CAD-01` — confronto/qualifica CAD;
4. `CEW-GEO-01` — proiezione geometrica;
5. `CEW-IFC-01` — proiezione openBIM;
6. `CEW-FEM-01` — modello analitico e solver;
7. `CEW-ASSURE-01` — prova end-to-end della catena di assurance.

Questa sequenza non costituisce ancora piano di implementazione: definisce solo le dipendenze architetturali.