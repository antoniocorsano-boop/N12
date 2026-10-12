# CEW — Civil Existing Workflow
## Research Baseline — 12 ottobre 2026

**Stato:** baseline di ricerca e architettura, da usare come riferimento progettuale CEW.

**Ambito:** piattaforma per la conoscenza, ricostruzione, modellazione, analisi e valutazione delle costruzioni esistenti, con N12 come caso pilota ma senza dipendenze concettuali specifiche da N12.

---

## 1. Decisione architetturale principale

CEW non deve diventare un nuovo CAD, un nuovo BIM authoring tool o un nuovo solutore strutturale.

Deve essere una **piattaforma governata per la conoscenza, ricostruzione e valutazione delle costruzioni esistenti**, capace di usare strumenti specialistici sostituibili senza perdere provenienza, incertezza, versioni e responsabilità.

Catena canonica:

`fonti originali → evidenze → conoscenza canonica → modello strutturale canonico → proiezioni specialistiche → analisi → assessment → interventi → fascicolo tecnico`

Principio fondamentale:

- DXF non è la fonte di verità CEW;
- IFC non è la fonte di verità CEW;
- un file CAD/BIM non è la fonte di verità CEW;
- un modello OpenSees/EdiLus/Code_Aster non è la fonte di verità CEW;
- tutte queste rappresentazioni sono derivate dal **Canonical Structural Model**.

---

## 2. Allineamento con il protocollo N12

N12 ha già fissato una regola coerente con CEW:

`fonti originali → evidenze → dati canonici → modello M0 → EdiLus-EE → verifiche → interventi → fascicolo finale`

Ogni dato strutturale deve mantenere uno stato esplicito:

- `DOC` — documentale;
- `MIS` — misurato;
- `RIF` — riferito;
- `INF` — inferito;
- `INC` — incerto;
- `ND` — non disponibile.

Un dato `ND`, `INC` o `INF` non può essere promosso implicitamente a `DOC` per analogia o convenienza di modellazione.

Il gate N12 corrente è `M0-G` — geometria globale dell’intero edificio tridimensionale.

---

## 3. Architettura CEW di riferimento

```text
                     CIVIL EXISTING WORKFLOW

 ┌──────────────────── FONTI IMMUTABILI ─────────────────────┐
 │ PDF | foto | scansioni | DXF/DWG | rilievi | prove | CSV │
 └──────────────────────────┬─────────────────────────────────┘
                            ↓
                    EVIDENCE ENGINE
             estrazione + posizione + hash + fonte
                            ↓
                    KNOWLEDGE ENGINE
       Observation → Claim → Conflict → Decision → Canonical
                            ↓
              CANONICAL STRUCTURAL MODEL
     oggetti + proprietà + relazioni + incertezza + versioni
                            ↓
      ┌─────────────────────┼──────────────────────┐
      ↓                     ↓                      ↓
 Geometry Adapter       IFC Adapter          Analysis Adapter
 B-Rep / CAD          IfcOpenShell/IDS        OpenSeesPy
      ↓                     ↓                      ↓
  visualizzazione      openBIM model          solver runs
      └─────────────────────┼──────────────────────┘
                            ↓
                    ASSURANCE ENGINE
          controlli + confronti + ricevute + audit
                            ↓
                MULTI-MODE ASSESSMENT
          scenari + incertezza + sensibilità + VoI
                            ↓
                INVESTIGATION PLANNER
                            ↓
             INTERVENTI / RETROFIT / AS-BUILT
                            ↓
                   FASCICOLO TECNICO
```

Gli agenti attraversano questi servizi, ma **non sono la fonte di verità**.

---

## 4. Cosa CEW deve costruire direttamente

### Da costruire

- Evidence Engine;
- Knowledge Engine;
- provenienza e tracciabilità;
- stati `DOC/MIS/RIF/INF/INC/ND`;
- gestione dei conflitti tra fonti;
- decisioni umane e promozione canonica;
- Canonical Structural Model indipendente dagli applicativi esterni;
- gestione dell’incertezza e degli scenari;
- versioni e ricevute;
- Assurance Engine;
- mapping tra oggetti canonici e proiezioni CAD/IFC/FEM;
- Investigation Planner;
- fascicolo tecnico riproducibile.

### Da non costruire da zero

- motore CAD;
- lettore/scrittore IFC;
- motore FEM;
- OCR;
- kernel per nuvole di punti;
- fotogrammetria;
- viewer 3D generico.

Il valore distintivo CEW è il **modello epistemico + strutturale + di assurance**, non la reinvenzione dei motori specialistici.

---

## 5. Canonical Structural Model

Il nucleo CEW deve rappresentare almeno:

- edificio;
- corpi strutturali;
- livelli;
- nodi;
- pilastri;
- travi;
- pareti;
- solai;
- fondazioni;
- sezioni;
- armature;
- materiali;
- vincoli;
- carichi e masse;
- proprietà geometriche;
- proprietà meccaniche;
- prove;
- osservazioni;
- incertezze;
- scenari;
- decisioni;
- relazioni tra oggetti.

Ogni proprietà canonica deve poter rispondere a:

- da quale evidenza deriva?
- è documentata, misurata, riferita, inferita, incerta o non disponibile?
- quando è stata introdotta?
- chi/che cosa l’ha proposta?
- chi/che cosa l’ha validata?
- quale versione del modello la usa?
- quali analisi dipendono da essa?

---

## 6. Modello epistemico minimo

CEW deve distinguere formalmente almeno:

- **Evidence** — ciò che la fonte contiene;
- **Observation** — ciò che è stato osservato o misurato;
- **Claim** — interpretazione proposta;
- **Assumption** — ipotesi necessaria ma non dimostrata;
- **Conflict** — incompatibilità tra fonti/interpretazioni;
- **Decision** — scelta tecnica approvata;
- **CanonicalProperty** — dato ammesso nel patrimonio corrente;
- **Scenario** — combinazione esplicita di ipotesi;
- **ModelGeneration** — modello derivato da una versione dei dati;
- **SolverRun** — singola esecuzione riproducibile;
- **Result** — risultato associato a modello e scenario;
- **Verification** — controllo del risultato;
- **Investigation** — rilievo/prova destinato a ridurre un’incertezza;
- **Intervention** — modifica proposta o realizzata;
- **Receipt** — prova informatica del passaggio.

---

## 7. Acquisizione documentale

### PDF vettoriali

Componenti candidati:

- PyMuPDF;
- pdfplumber.

Obiettivo: estrarre non solo testo, ma anche coordinate, vettori, linee, rettangoli, tabelle e riferimenti spaziali.

### PDF scansiti

Componenti candidati:

- OCRmyPDF;
- Tesseract.

Regola CEW: l’OCR non sostituisce mai il documento originale; produce una rappresentazione derivata con provenienza e posizione.

### Output desiderato

Non un semplice testo estratto, ma un oggetto tipo:

```text
Observation OBS-00421
source_sha256 = ...
page = 13
bbox = [x1,y1,x2,y2]
raw_text = "40 x 50"
proposed_interpretation = "40 × 50 cm"
candidate_object = COL-C14
method = vector-text | OCR | table-extraction
state = DOC-candidate
review = pending
```

---

## 8. CAD e DXF/DWG

### ezdxf

Scelta di base per:

- parsing deterministico DXF;
- inventario entità;
- coordinate;
- layer;
- blocchi;
- testi;
- controlli automatici;
- trasformazioni riproducibili.

Ruolo: **CAD Evidence Parser**.

### CADCraft

Ruolo candidato:

- CAD operativo/interattivo;
- rendering;
- interrogazione da agente;
- command line / JSON / MCP;
- seconda lettura indipendente del disegno.

CADCraft non deve essere il modello canonico CEW né il kernel centrale del sistema.

Strategia consigliata:

`ezdxf + CADCraft`, con responsabilità differenti.

Per N12: qualificare TAV.5/TAV.6/TAV.7 su copie controllate.

Gate minimo CAD:

- tipo e numero entità;
- coordinate;
- unità e scala;
- layer;
- blocchi;
- testi;
- quote;
- retini;
- estensioni geometriche;
- handle/identificatori;
- stabilità apertura;
- coerenza rendering/geometria;
- round-trip DXF senza perdita rilevante per CEW.

---

## 9. Geometry-as-Code

CEW deve generare la geometria dal modello canonico, non ricavare la verità dal file CAD.

Candidato principale:

- **build123d / OpenCascade**.

Esempio concettuale:

```text
Column C14
axis = ...
level_from = ...
level_to = ...
section = SEC-07
orientation = ...
evidence = [...]
```

Da questi dati CEW genera il solido B-Rep.

La geometria è quindi una conseguenza della conoscenza canonica.

---

## 10. IFC / openBIM

Componenti candidati:

- IfcOpenShell;
- IDS 1.0;
- IfcTester;
- Bonsai come ambiente specialistico umano, non come dipendenza del core.

Catena proposta:

`CEW Canonical Model → IFC generator → schema validation → IDS validation → visual review → receipt`

IFC è una proiezione interoperabile importante, ma non il nucleo CEW e non il motore FEM.

---

## 11. Nuvole di punti e rilievo

CEW deve essere predisposto fin dall’inizio a ricevere:

- misura manuale;
- stazione totale;
- fotogrammetria;
- nuvole di punti;
- laser scanner.

Componenti candidati:

- Open3D;
- PDAL;
- COLMAP per fotogrammetria.

Principio: fonti geometriche diverse devono poter riferirsi allo **stesso StructuralObject ID**.

La letteratura recente conferma che Scan-to-BIM/Scan-to-Graph e digital twin strutturali sono promettenti ma devono conservare incertezza, provenienza e decisioni di modellazione; occlusioni e dati mancanti restano criticità centrali.

---

## 12. Prove, indagini e conoscenza dei materiali

CEW non deve memorizzare un semplice valore finale come `f_c = ...`.

Deve rappresentare la catena:

`campione → posizione → elemento → metodo → laboratorio → risultato → incertezza → correlazione → popolazione → valore adottato → decisione`

Il piano delle indagini deve poter diventare un oggetto computabile.

Obiettivo futuro: **Investigation Planner** basato su sensibilità e valore dell’informazione, per suggerire quali indagini riducono davvero l’incertezza che influenza il risultato strutturale.

---

## 13. Analisi strutturale

### Motore principale candidato

- **OpenSeesPy**.

Architettura:

`Canonical Model → CEW Analysis Scenario → OpenSees Adapter → exact input → run → immutable raw results → CEW object mapping → checks → receipt`

### Motori indipendenti / di controllo

- Code_Aster — candidato forte per verifiche indipendenti e casi FEM avanzati;
- Gmsh — mesh controllata 2D/3D;
- Kratos Multiphysics — possibile espansione futura, non requisito V1;
- concreteproperties — utile per analisi di sezione, ma non come verificatore normativo finale.

Nessun solutore deve diventare la fonte di verità CEW.

---

## 14. Incertezza e affidabilità

CEW deve trattare l’incertezza come oggetto esplicito.

Esempio:

```text
E = 30000 MPa
```

non è sufficiente.

Devono essere disponibili:

- fonte;
- zona di validità;
- stato epistemico;
- distribuzione/dispersione se nota;
- misura diretta o inferenza;
- versione;
- scenario che la utilizza;
- analisi dipendenti.

Candidato per sensibilità/affidabilità:

- **OpenTURNS**.

Possibili metodi futuri:

- Monte Carlo;
- Sobol;
- FORM/SORM;
- probabilità di superamento;
- Value of Information.

---

## 15. Normativa e profili di valutazione

CEW non deve incorporare “la normativa” come blocco unico immutabile.

Deve avere profili normativi versionati, separando:

1. norma vigente;
2. norma applicabile al caso specifico;
3. regola implementata nel software.

Profili candidati di riferimento:

- `IT-NTC2018`;
- `IT-CIRC2019`;
- `EU-EN1990-2-2026`;
- `EU-EN1998-3-2025`;
- `TEST-EN13791-2019`;
- famiglia `EN12504-*`;
- linee guida nazionali per materiali/interventi, versionate.

Ogni verifica deve dichiarare giurisdizione, data, finalità e profilo normativo usato.

---

## 16. Agenti

Gli agenti CEW devono essere **operatori specializzati sotto contratto**, non decisori autonomi del patrimonio canonico.

Catena minima:

`agente → proposta → validatore deterministico → confronto fonti → eventuale human review → decisione → commit canonico`

Un agente può:

- estrarre dati da documenti;
- proporre mapping;
- interrogare CAD/IFC;
- rilevare conflitti;
- generare modelli derivati;
- lanciare analisi;
- sintetizzare risultati;
- proporre indagini.

Non può promuovere automaticamente una proprietà a canonica quando esiste ambiguità tecnica o normativa.

---

## 17. Assurance Engine

Ogni trasformazione importante deve produrre almeno:

- hash input;
- versione dello strumento;
- parametri;
- hash output;
- identificatori degli oggetti coinvolti;
- validatori eseguiti;
- risultato;
- autore/operatore/agente;
- decisione umana se richiesta;
- timestamp/versione.

Obiettivo: da un risultato strutturale deve essere possibile risalire senza ambiguità a:

`Result → SolverRun → Scenario → ModelGeneration → CanonicalProperty → Decision → Claim/Observation → Evidence → Source`

---

## 18. Pila tecnologica candidata

| Ambito | Candidato | Ruolo | Stato CEW |
|---|---|---|---|
| Database canonico | PostgreSQL + PostGIS | dati, relazioni, geometrie, versioni | ADOTTARE |
| Provenienza | modello compatibile W3C PROV | lineage e responsabilità | ADOTTARE |
| PDF vettoriali | PyMuPDF + pdfplumber | testo/vettori/tabelle/coordinate | ADOTTARE |
| PDF scansiti | OCRmyPDF + Tesseract | OCR derivato | ADOTTARE |
| DXF | ezdxf | parser deterministico | ADOTTARE |
| CAD operativo | CADCraft | ispezione/render/agenti | QUALIFICARE |
| B-Rep parametrico | build123d/OpenCascade | Geometry-as-Code | QUALIFICARE |
| IFC | IfcOpenShell | proiezione openBIM | ADOTTARE |
| Contratti IFC | IDS + IfcTester | validazione automatica | ADOTTARE |
| BIM specialistico | Bonsai | authoring/ispezione umana | QUALIFICARE |
| Nuvole di punti | Open3D + PDAL | registrazione/controllo | QUALIFICARE |
| Fotogrammetria | COLMAP | foto → 3D | FASE SUCCESSIVA |
| Analisi strutturale | OpenSeesPy | solver primario | CONFERMARE |
| FEM indipendente | Code_Aster | cross-check/casi avanzati | QUALIFICARE |
| Mesh | Gmsh | mesh 2D/3D | QUALIFICARE |
| FEM avanzato | Kratos | espansione futura | NON V1 |
| Sezioni c.a. | concreteproperties | analisi di sezione | ADOTTARE CON CAUTELA |
| Affidabilità | OpenTURNS | sensibilità/VoI | FASE SUCCESSIVA |
| Ricerca semantica | pgvector | supporto retrieval | SUPPORTO, NON CANONICO |

---

## 19. Evidenze dalla ricerca scientifica

La letteratura recente converge su alcuni punti utili a CEW:

- integrazione BIM-FEM utile, ma interoperabilità e data loss restano problemi reali;
- per strutture esistenti servono modelli multi-livello e tracciabilità dei danni/dati;
- Scan-to-BIM e digital twin strutturali funzionano meglio quando geometria, semantica e fonti restano collegate;
- l’incertezza del rilievo e le occlusioni non possono essere ignorate;
- “scan-to-graph” è concettualmente vicino a CEW perché conserva fonti, incertezza, decisioni e più rappresentazioni geometriche;
- il BIM può essere una vista/archivio utile, ma non sostituisce un modello conoscitivo più generale.

Riferimenti scientifici rilevanti individuati:

1. Alsharif M., Thermou G., Ninić J., Tizani W. (2025), *Data integration framework for multi-level information modelling and numerical analysis of deteriorated RC bridges*, Advances in Engineering Software.
2. Levine N., Spencer B.F. (2022), *Post-Earthquake Building Evaluation Using UAVs: A BIM-Based Digital Twin Framework*, Sensors.
3. Sibenik G., Kovacic I. (2020), *Assessment of model-based data exchange between architectural design and structural analysis*, Journal of Building Engineering.
4. Spanò A. et al. (2023), *Digital Twinning for 20th Century Concrete Heritage: HBIM Cognitive Model for Torino Esposizioni Halls*, Sensors.
5. Abbate E., Invernizzi S., Spanò A. (2020), *HBIM parametric modelling from clouds to perform structural analyses based on finite elements*, Applied Geomatics.
6. Abreu N. et al. (2023), *Procedural Point Cloud Modelling in Scan-to-BIM and Scan-vs-BIM Applications: A Review*, ISPRS International Journal of Geo-Information.
7. Esfahani M.E. et al. (2021), *Quantitative investigation on the accuracy and precision of Scan-to-BIM under different modelling scenarios*, Automation in Construction.
8. Mirzaei K. et al. (2022), *Automatic generation of structural geometric digital twins from point clouds*, Scientific Reports.
9. Werbrouck J. et al. (2020), *Scan-to-graph: Semantic enrichment of existing building geometry*, Automation in Construction.

---

## 20. Fonti tecniche/normative da mantenere nel dossier CEW

- NTC 2018 e Circolare applicativa 2019;
- UNI EN 1990-2:2026 — valutazione delle strutture esistenti;
- EN 1998-3:2025 — valutazione e adeguamento sismico di edifici e ponti esistenti;
- UNI EN 13791:2019;
- famiglia UNI EN 12504;
- buildingSMART IFC 4.3 Structural Analysis Domain;
- IDS 1.0;
- W3C PROV;
- documentazione ufficiale PostGIS;
- documentazione ufficiale IfcOpenShell/IfcTester;
- documentazione ufficiale OpenSeesPy, Code_Aster, Gmsh, Open3D, PDAL, COLMAP, ezdxf, build123d, OpenTURNS.

Nota: la presenza di una norma più recente non implica automaticamente la sua applicabilità cogente in uno specifico procedimento italiano. CEW deve sempre registrare il profilo normativo effettivamente adottato.

---

## 21. Piano operativo risultante

### CEW-CONTRACT-01 — Canonical Structural Model

Congelare:

- oggetti;
- proprietà;
- relazioni;
- provenienza;
- incertezza;
- versioni;
- scenari;
- decisioni.

### CEW-EVIDENCE-01

Qualificare la catena:

- PDF nativo;
- PDF scansito;
- tabelle;
- DXF;
- immagini;
- riferimenti spaziali.

### CEW-CAD-01

Confrontare sullo stesso DXF N12:

- ezdxf;
- CADCraft;
- inventario entità;
- round-trip;
- rendering;
- discrepanze.

### CEW-GEO-01

Generare una porzione reale di M0-G dal Canonical Structural Model tramite Geometry-as-Code.

### CEW-IFC-01

`CEW → IFC → schema validation → IDS → visual review → receipt`

### CEW-FEM-01

`CEW Canonical Model → OpenSeesPy`, con mapping bidirezionale degli identificatori e ricevuta completa.

### CEW-ASSURE-01

Dimostrare la risalita completa:

`risultato → run → scenario → modello → proprietà → decisione → evidenza → fonte`

### CEW-KNOWLEDGE-01

Introdurre il ciclo:

`prova/indagine → nuova evidenza → aggiornamento conoscitivo → nuova generazione modello`, senza sovrascrivere la generazione precedente.

---

## 22. Decisioni da considerare consolidate

1. CEW è una piattaforma di conoscenza e assurance per costruzioni esistenti, non un singolo applicativo CAD/BIM/FEM.
2. Il Canonical Structural Model è indipendente dai software esterni.
3. N12 resta il banco di prova principale, ma il modello CEW deve essere generalizzabile.
4. Geometry-as-Code è parte dell’architettura di riferimento.
5. IFC è una proiezione governata, non la fonte di verità.
6. OpenSeesPy è il candidato principale per l’adattatore di analisi, ma non l’unico verificatore.
7. CADCraft va qualificato come CAD Evidence Adapter / strumento agentico, non come core.
8. ezdxf resta il candidato deterministico primario per DXF.
9. L’incertezza epistemica è parte del modello, non una nota accessoria.
10. Gli agenti producono proposte e trasformazioni verificabili, non decisioni canoniche autonome.
11. Ogni trasformazione importante deve essere auditabile tramite receipt.
12. Il piano delle indagini deve diventare in prospettiva computabile e guidato dal valore dell’informazione.

---

## 23. Principio finale

CEW deve essere in grado di rispondere, per qualunque risultato tecnico:

> Questo valore deriva da questa proprietà canonica; questa proprietà è stata approvata sulla base di queste evidenze; ciascuna evidenza conserva stato, fonte e incertezza; questa analisi usa questa versione del patrimonio conoscitivo; modificando questa ipotesi si ottiene questo scenario; questa indagine riduce questa incertezza; questa è la decisione tecnica finale.

Questo è il nucleo differenziante di Civil Existing Workflow.
