# CEW MASTER PLAN
## Civil Existing Workflow — Canonical Roadmap & External Toolchain

**Data di consolidamento:** 14 ottobre 2026  
**Caso pilota:** Condominio N.12  
**Stato:** APPROVED / CANONICAL MASTER v1

---

## 1. Missione

Civil Existing Workflow non deve reinventare strumenti specialistici già disponibili.

CEW deve governare:

- fonti originali;
- evidenze;
- provenienza;
- identità degli oggetti strutturali;
- stati epistemici;
- conflitti;
- decisioni tecniche;
- modello geometrico/strutturale canonico;
- propagazione controllata dei dati;
- generazione delle proiezioni CAD / IFC / FEM;
- verifiche;
- ricevute di assurance;
- fascicolo tecnico.

Catena canonica:

**Fonti → Evidenze → Conoscenza canonica → Modello geometrico parametrico → Controllo automatico → Sufficienza conoscitiva → Modello strutturale → Verifiche → Fascicolo tecnico**

Gli strumenti esterni sono motori sostituibili. CEW resta l'autorità su conoscenza, identità, provenienza e stato dei dati.

---

## 2. Principio BUILD LAST — REUSE FIRST

Prima di sviluppare qualsiasi nuovo componente CEW deve essere verificato se esiste già un componente open-source adeguato.

Si sviluppa internamente solo:

1. ciò che costituisce il patrimonio conoscitivo CEW;
2. gli adapter verso strumenti esterni;
3. i controlli di coerenza e assurance;
4. ciò che non è ragionevolmente disponibile in software open-source esistente.

Non sviluppare da zero:

- motore CAD;
- kernel geometrico;
- OCR;
- motore PDF;
- BIM authoring tool;
- parser IFC;
- viewer 3D generico;
- motore point-cloud;
- fotogrammetria;
- mesh generator;
- FEM solver;
- database engine.

---

## 3. Stati epistemici

Ogni proprietà strutturale deve mantenere esplicitamente uno stato:

- `DOC` — documentale;
- `MIS` — misurato;
- `RIF` — riferito;
- `INF` — inferito;
- `INC` — incerto;
- `ND` — non disponibile.

Nessun valore `INF`, `INC` o `ND` può diventare implicitamente `DOC`.

La geometria necessaria al CAD o al FEM non autorizza a inventare informazioni mancanti.

---

# 4. Toolchain esterna canonica

## 4.1 Documenti e PDF

### Docling / Docling Parse
**Stato: ADOPT / benchmark N12**

Ruolo:
- normalizzazione documentale;
- parsing di PDF e documenti;
- struttura pagina;
- layout;
- tabelle;
- coordinate;
- serializzazione strutturata.

Non è la fonte di verità: produce Evidence candidate collegate al documento originale.

### pypdfium2
**Stato: ADOPT**

Ruolo:
- rendering PDF;
- accesso pagina;
- ispezione;
- rasterizzazione deterministica;
- supporto alle coordinate.

### pdfplumber
**Stato: ADOPT**

Ruolo:
- testo;
- linee;
- rettangoli;
- geometria PDF;
- tabelle;
- coordinate.

### PyMuPDF
**Stato: NON CANONICAL / optional only**

Tecnologicamente valido, ma non deve diventare dipendenza obbligatoria CEW; preferire componenti permissivi per il percorso canonico.

---

## 4.2 OCR e image processing

### OCRmyPDF + Tesseract
**Stato: ADOPT come baseline OCR**

Ruolo:
- OCR riproducibile;
- generazione di rappresentazioni searchable;
- integrazione documentale.

L'OCR non sostituisce mai il documento originale.

### PaddleOCR
**Stato: BENCHMARK**

Secondo motore candidato quando Tesseract non è sufficiente, specialmente per layout tecnici complessi.

### OpenCV
**Stato: ADOPT**

Ruolo:
- preprocessing immagini;
- deskew;
- filtri;
- segmentazione;
- geometria raster;
- confronto visivo;
- supporto al riconoscimento.

---

## 4.3 DXF / CAD Evidence

### ezdxf
**Stato: ADOPT — parser DXF primario**

Ruolo:
- lettura/scrittura DXF;
- inventario delle entità;
- layer;
- blocchi;
- testi;
- quote;
- coordinate;
- handle;
- trasformazioni deterministiche;
- controlli automatici.

CEW usa ezdxf come **CAD Evidence Parser**.

### CADCraft
**Stato: BENCHMARK N12 — NON CORE**

Ruolo candidato:
- apertura DXF/DWG;
- rendering;
- interazione umana;
- command line;
- JSON;
- MCP;
- interrogazione agentica del disegno;
- seconda lettura indipendente.

CADCraft non può diventare fonte canonica né dipendenza fondamentale prima di superare un benchmark N12.

Benchmark N12: **TAV.5 / TAV.6 / TAV.7**.

Verificare:
- numero/tipo entità;
- coordinate;
- scala;
- layer;
- blocchi;
- testi;
- quote;
- retini;
- estensioni;
- stabilità;
- rendering;
- round-trip senza perdita CEW-rilevante.

---

## 4.4 Geometria parametrica / CAD-as-Code

### build123d
**Stato: ADOPT come adapter geometrico primario**

Ruolo:

`CEW Canonical Geometry → build123d → B-Rep`

### OpenCascade / OCP
**Stato: FOUNDATION**

Kernel geometrico sottostante. CEW non implementa un kernel geometrico.

### FreeCAD
**Stato: OPTIONAL HUMAN TOOL**

Può essere utilizzato per ispezione, verifica visiva e interoperabilità. Non è la fonte canonica CEW e non deve governare i dati.

---

## 4.5 IFC / openBIM

### IfcOpenShell
**Stato: ADOPT**

Ruolo:
- generazione IFC;
- lettura;
- manipolazione;
- interrogazione;
- geometria IFC.

Catena:

`CEW → IFC Adapter → IfcOpenShell → IFC`

### IDS + IfcTester
**Stato: ADOPT**

Ruolo:
- specifiche machine-readable;
- validazione degli IFC;
- ricevute di conformità.

### Bonsai
**Stato: OPTIONAL HUMAN ENVIRONMENT**

Ambiente specialistico umano per ispezione/authoring IFC. Non deve essere dipendenza del core CEW.

---

## 4.6 Grafo strutturale

### NetworkX
**Stato: ADOPT**

Ruolo:
- nodi;
- travi;
- pilastri;
- fondazioni;
- collegamenti;
- continuità;
- componenti sconnesse;
- elementi orfani;
- topologia strutturale.

Il grafo NetworkX è una proiezione del Canonical Structural Model, non la fonte primaria.

---

## 4.7 Persistenza e dati

### Fase pilota N12

Preferire inizialmente formati semplici, versionabili e verificabili:
- JSON;
- CSV;
- Parquet.

### DuckDB / Parquet
**Stato: ADOPT quando utile per analisi locali**

Nessun server necessario.

### PostgreSQL + PostGIS
**Stato: DEFER UNTIL NEEDED**

Da introdurre soltanto quando esisterà una reale necessità di accesso multiutente, query spaziali server-side, gestione persistente di grandi patrimoni o servizio CEW condiviso.

### pgvector
**Stato: OPTIONAL SUPPORT**

Mai fonte di verità; solo supporto per retrieval/ricerca semantica.

---

## 4.8 Nuvole di punti e rilievo

### Open3D
**Stato: DEFER / ADOPT WHEN DATA EXISTS**

### PDAL
**Stato: DEFER / ADOPT WHEN DATA EXISTS**

### COLMAP
**Stato: DEFER / ADOPT WHEN PHOTOGRAMMETRY IS NEEDED**

Questi strumenti non devono diventare un nuovo fronte finché N12 non presenta realmente queste fonti.

---

## 4.9 Viewer

Non sviluppare un viewer generale CEW.

Possibili strumenti esterni:
- OpenSeadragon — documenti e immagini ad alta risoluzione;
- Three.js — visualizzazioni web 3D;
- Bonsai — IFC;
- viewer build123d/OCP — geometria parametrica;
- CADCraft — DXF/DWG.

**Stato: DEFER fino al vertical slice.**

Prima utilizzare i viewer già disponibili nei tool scelti.

---

## 4.10 Analisi strutturale

### OpenSeesPy
**Stato: SELECTED PRIMARY FEM CANDIDATE — FROZEN UNTIL CEW-FEM-01**

Target principale per il futuro adapter FEM. Non autorizzato oggi.

### Code_Aster
**Stato: SELECTED INDEPENDENT SECONDARY SOLVER**

Ruolo futuro: verifica indipendente e FEM avanzato. Non autorizzato oggi.

### Gmsh
**Stato: FUTURE MESH COMPONENT**

### concreteproperties
**Stato: FUTURE SECTION ANALYSIS SUPPORT**

### Kratos Multiphysics
**Stato: PARKED**

### PyNite
**Stato: PARKED**

Non aprire un terzo fronte solver.

---

## 4.11 Incertezza e affidabilità

### OpenTURNS
**Stato: DEFER UNTIL UNCERTAINTY PHASE**

Candidato per Monte Carlo, Sobol, FORM/SORM, reliability, sensitivity e Value of Information.

---

# 5. Cosa CEW deve costruire

CEW costruisce esclusivamente:

### Evidence Engine
`Source → EvidenceRegion → Observation`

### Knowledge Engine
`Observation → Claim → Conflict → Decision → CanonicalProperty`

### Object Identity
Ogni elemento mantiene una identità stabile: `StructuralObject ID`.

### Canonical Model
Rappresentazione solver-independent del fabbricato.

### Provenance
Ogni proprietà deve conoscere fonte, evidenza, metodo, stato epistemico, versione, autore/agente, validatore e decisione.

### Adapter
Adapter sottili verso CAD, IFC, FEM, viewer e database.

### Assurance Engine
Ogni trasformazione produce digest input, versione tool, parametri, digest output, oggetti coinvolti, validator, risultato e receipt.

CEW non duplica le funzioni del software esterno.

---

# 6. Roadmap canonica

## FASE A — Knowledge Baseline N12

Obiettivo: congelare ciò che sappiamo realmente dell'edificio.

Output: **N12 KNOWLEDGE BASELINE v1**

Registro:

`Fonte → Evidenza → Oggetto → Proprietà → Valore → Stato epistemico → Conflitto → Residuo → Utilizzabilità`

Exit criterion: nessun dato strutturale importante deve dipendere dalla memoria della conversazione.

## FASE B — External Tool Qualification + Source→Evidence

Primo vertical slice.

Pipeline:

`PDF/DXF → tool esterno → Evidence CEW`

Tool da qualificare subito:
1. Docling/docling-parse;
2. pypdfium2;
3. pdfplumber;
4. OCRmyPDF/Tesseract;
5. OpenCV;
6. ezdxf;
7. CADCraft come benchmark separato.

Exit criterion: evidenze geometriche riproducibili dal documento originale senza coordinate manuali non provenienziate.

## FASE C — Canonical Geometry

Pipeline:

`Evidence → Canonical Object → build123d/OpenCascade`

Output: modello geometrico parametrico N12.

Exit criterion: un insieme reale e non banale di pilastri/travi/fondazioni viene rigenerato deterministicamente dal patrimonio CEW.

## FASE D — Automatic Control + IFC

Tool:
- NetworkX;
- IfcOpenShell;
- IDS;
- IfcTester.

Controlli:
- nodi orfani;
- elementi scollegati;
- duplicati;
- continuità verticale;
- intersezioni;
- livelli;
- sezioni;
- relazioni;
- corrispondenza CEW↔IFC.

Output: modello geometrico controllato + proiezione IFC validata.

## FASE E — Sufficienza conoscitiva

Domanda: **sappiamo abbastanza per costruire un modello strutturale affidabile?**

Verificare materiali, armature, carichi, masse, fondazioni, geotecnica, dettagli costruttivi, degrado e incertezze.

Output:
- livello di conoscenza;
- lista gap;
- Investigation Plan.

CEW-FEM resta bloccato se il gate non passa.

## FASE F — CEW-FEM-01

Solo dopo autorizzazione esplicita.

Pipeline:

`Canonical Structural Model → OpenSees adapter → SolverRun → Result → Verification → Receipt`

Controllo indipendente: Code_Aster nei casi selezionati.

## FASE G — Assessment e Fascicolo

Output finale:
- stato dell'esistente;
- evidenze;
- livelli di conoscenza;
- modelli;
- scenari;
- verifiche;
- criticità;
- indagini;
- interventi;
- ricevute;
- fascicolo tecnico riproducibile.

---

# 7. CURRENT TASK

## CEW-B01 — External Tool Qualification / N12 Vertical Slice

Questo è l'unico macro-task autorizzato dopo il consolidamento del Master.

Obiettivo:

far attraversare a dati reali N12 questa catena:

`Fonte reale → Evidence → StructuralObject → geometria parametrica`

senza software proprietario e senza ricostruzioni manuali nascoste.

Tool del primo slice:
- Docling/docling-parse;
- pypdfium2;
- pdfplumber;
- OCRmyPDF/Tesseract se necessario;
- OpenCV;
- ezdxf;
- build123d/OpenCascade.

CADCraft viene testato separatamente come strumento CAD/agentico e non può bloccare il vertical slice.

---

# 8. Fronti congelati

Fino alla chiusura di CEW-B01:

- nessun nuovo Gate Authority;
- nessuna nuova infrastruttura governance salvo bug bloccante;
- nessun CEW-FEM;
- nessun SolverRun;
- nessun Result;
- nessun nuovo solver;
- nessun CAD engine interno;
- nessun OCR interno;
- nessun viewer generale interno;
- nessun framework agentico nuovo;
- nessun database server obbligatorio;
- nessuna point-cloud pipeline senza una fonte reale che la richieda;
- nessuna nuova grande astrazione architetturale.

PR #147 resta congelata/read-only e non viene modificata, chiusa o superseded da questo Master.

---

# 9. Regola WIP = 1

CEW ha un solo macro-task operativo corrente.

Ogni task deve dichiarare:
- `phase`;
- `canonical_task`;
- `input`;
- `expected_output`;
- `external_tools`;
- `internal_components`;
- `exit_criteria`;
- `out_of_scope`.

Un nuovo macro-task può partire soltanto dopo la chiusura del precedente oppure dopo una decisione umana esplicita di modifica del Master.

---

# 10. Anti-drift gate

Ogni futura PR CEW deve poter rispondere:

**Quale riga del Master Plan realizza?**

Se non esiste risposta: `SCOPE_DRIFT`.

Nuove tecnologie non entrano automaticamente nel Master.

Procedura:

`proposal → benchmark N12 → evidence → decisione umana → modifica Master`

Il gate automatico che implementerà questa regola è un task futuro separato; non viene introdotto da questo consolidamento documentale.

---

# 11. Autorità dei documenti

Gerarchia:

1. `CEW_MASTER_PLAN.md` — direzione del progetto;
2. `CEW_CURRENT_STATE.json` — unico lavoro autorizzato;
3. baseline/evidence N12;
4. specifiche della fase corrente;
5. piani di implementazione;
6. PR e commit;
7. conversazione — supporto operativo, non autorità.

Se una conversazione contraddice il Master, prevale il Master finché non viene modificato esplicitamente.

Riferimento storico di ricerca: `docs/CEW_RESEARCH_BASELINE_2026-10-12.md` sulla PR #147. Il Master consolida la direzione senza modificare o supersedere quella PR.

---

# 12. Definizione sintetica del prodotto

CEW non è un CAD.

CEW non è un BIM.

CEW non è un FEM.

CEW è il **sistema governato che trasforma evidenze eterogenee su una costruzione esistente in conoscenza strutturale tracciabile e quindi in modelli CAD/IFC/FEM riproducibili, mantenendo sempre identità, provenienza, incertezza e responsabilità tecnica**.
