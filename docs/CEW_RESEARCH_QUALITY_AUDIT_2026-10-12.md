# CEW — Audit di qualità delle deduzioni
## 12 ottobre 2026

**Stato:** revisione critica della `CEW_RESEARCH_BASELINE_2026-10-12.md`.

**Regola di prevalenza:** quando questo documento assegna a una proposizione uno stato più prudente rispetto alla baseline, **prevale questo audit**. In particolare, la sezione “Decisioni da considerare consolidate” della baseline non va interpretata come approvazione definitiva delle scelte tecnologiche.

## 1. Metodo

Le proposizioni sono state separate in quattro classi:

- **FATTO VERIFICATO** — supportato direttamente da fonte primaria, normativa, documentazione ufficiale o risultato sperimentale pubblicato;
- **DEDUZIONE SUPPORTATA** — conseguenza progettuale ragionevole sostenuta da più evidenze, ma non dimostrata in modo univoco;
- **CANDIDATO DA QUALIFICARE** — tecnologia/architettura plausibile che richiede prova CEW/N12 prima dell’adozione;
- **IPOTESI / RICERCA FUTURA** — idea promettente che non deve condizionare la V1 finché non è dimostrato il valore.

Criteri applicati:

1. preferenza per fonti primarie e ufficiali;
2. distinzione esplicita tra capacità dichiarata di un software e idoneità al caso CEW;
3. distinzione tra esistenza/vigenza di una norma e applicabilità cogente al singolo procedimento;
4. nessuna promozione da “candidato” ad “adottato” senza prova su casi reali N12;
5. una deduzione architetturale non viene presentata come fatto scientifico.

---

## 2. Esito sintetico

La **direzione concettuale generale di CEW è ben supportata**, soprattutto per provenienza, incertezza, tracciabilità, separazione tra fonti e modelli derivati e necessità di gestire interoperabilità imperfetta.

Sono invece **troppo forti** alcune etichette della baseline, in particolare `ADOTTARE`, `candidato principale` e `decisioni consolidate` riferite a singoli strumenti. Queste scelte devono essere riclassificate come preferenze da qualificare sperimentalmente.

Non risultano motivi per scartare l’architettura CEW; risultano però motivi per rendere più rigoroso il suo **registro delle decisioni**.

---

## 3. Verifica delle deduzioni principali

| # | Proposizione | Stato dopo audit | Motivazione |
|---|---|---|---|
| 1 | CEW deve conservare fonti, provenienza, assunzioni, incertezze e decisioni | **DEDUZIONE SUPPORTATA — alta confidenza** | La letteratura sugli edifici esistenti/Scan-to-Graph identifica esplicitamente fonti, incertezze e decisioni di modellazione come informazioni da preservare; EN 1998-3:2025 richiede documentazione e archiviazione delle procedure di ispezione e raccolta dati. |
| 2 | CEW non deve coincidere con un singolo CAD/BIM/FEM | **DEDUZIONE SUPPORTATA — alta confidenza** | L’interoperabilità tra modelli architettonici e strutturali presenta ancora inconsistenze; IFC ha un dominio strutturale utile ma con limiti espliciti. La conclusione architetturale è ragionevole, non una prescrizione normativa. |
| 3 | Serve un Canonical Structural Model indipendente dagli applicativi | **DEDUZIONE SUPPORTATA — alta confidenza, da prototipare** | È coerente con la necessità di più schemi/domain model e con la tracciabilità, ma resta una scelta di architettura CEW: va validata con CEW-CONTRACT-01 e almeno due adattatori reali. |
| 4 | IFC deve essere una proiezione governata e non l’unica fonte di verità | **DEDUZIONE SUPPORTATA — alta confidenza** | IFC 4.3 Structural Analysis Domain non copre, tra l’altro, topologia FEM, risultati dettagliati di mesh/stress-strain e analisi dinamica. Ciò supporta l’uso come formato interoperabile, non dimostra da solo che un’altra architettura sia impossibile. |
| 5 | W3C PROV è adatto come riferimento concettuale per provenance | **FATTO VERIFICATO sulla capacità; CANDIDATO sul mapping CEW** | PROV-O definisce Entity, Activity e Agent e relazioni di provenienza. Il mapping preciso CEW deve essere progettato e testato. |
| 6 | PostgreSQL + PostGIS deve essere il database canonico | **CANDIDATO PREFERITO, non ancora adottato** | PostGIS fornisce tipi geometrici, operazioni spaziali e indici. Non è stata eseguita una comparazione CEW con alternative né un benchmark del modello dati. |
| 7 | PyMuPDF/pdfplumber sono adatti all’estrazione documentale | **FATTO VERIFICATO sulle capacità; CANDIDATI da qualificare su N12** | PyMuPDF espone i drawing commands vettoriali; pdfplumber espone caratteri, linee, rettangoli, curve, coordinate e tabelle. Accuratezza e copertura vanno misurate sui documenti N12. |
| 8 | OCRmyPDF/Tesseract sono adatti ai PDF scansiti | **FATTO VERIFICATO sulle capacità; CANDIDATI da qualificare** | OCRmyPDF aggiunge un text layer ricercabile ai PDF. La qualità OCR sui documenti storici e tecnici N12 va misurata. |
| 9 | ezdxf deve essere il parser DXF primario | **CANDIDATO PREFERITO** | Le capacità dichiarate sono solide: lettura/modifica/scrittura DXF R12–R2018, recupero/audit e conservazione di dati di terze parti. Va verificata la fedeltà sui DXF N12 e sui casi limite rilevanti. |
| 10 | CADCraft è utile come secondo CAD/evidence adapter agentico | **CANDIDATO AD ALTO INTERESSE, ma immaturo** | Il progetto dichiara CLI/MCP e ampia copertura 2D, ma è in sviluppo rapido. Un test reale AutoCAD↔CADCraft pubblicato l’11/10/2026 segnala 6 errori AUDIT nel DWG ri-salvato; la roadmap stessa indica parità complessiva ≈29% e 3D 0%. Nessun uso canonico senza qualifica. |
| 11 | Geometry-as-Code con build123d/OpenCascade è parte necessaria dell’architettura | **CANDIDATO DA QUALIFICARE** | build123d è effettivamente B-Rep e parametrico. Non è ancora dimostrato che sia la scelta migliore per modelli CEW completi, persistenza topologica, mapping IFC/FEM e robustezza su edifici reali. |
| 12 | IfcOpenShell + IDS + IfcTester sono la catena openBIM da adottare | **CANDIDATO PREFERITO, forte evidenza tecnica** | IfcOpenShell valida sintassi/schema IFC e produce geometria; IfcTester valida modelli contro IDS; IDS 1.0 è standard buildingSMART dal 1/6/2024. Resta da testare il profilo informativo CEW e il round-trip con gli strumenti target. |
| 13 | Open3D/PDAL/COLMAP sono adeguati al rilievo digitale | **FATTO VERIFICATO sulle capacità; non requisito V1** | Open3D fornisce registrazione ICP/global; PDAL pipeline riproducibili; COLMAP SfM/MVS. La loro necessità immediata dipende dal caso pilota e dai dati disponibili. |
| 14 | OpenSeesPy deve essere il solver primario CEW | **CANDIDATO DA BENCHMARK, non confermato** | OpenSeesPy offre modellazione/analisi strutturale via Python, ma non è stato dimostrato che sia il miglior solver primario per CEW/N12, né che copra da solo tutte le verifiche normative italiane. Serve CEW-FEM-01 con casi benchmark e confronto indipendente. |
| 15 | Code_Aster è adatto a cross-check indipendenti | **CANDIDATO FORTE** | È un solver FEM open source maturo per meccanica, termica e dinamica con migliaia di test di verifica. Va definito quali casi CEW giustificano il costo di una seconda catena. |
| 16 | OpenTURNS può supportare sensibilità/affidabilità | **FATTO VERIFICATO sulle capacità** | Documenta Sobol, FORM, SORM, Monte Carlo e altri metodi di affidabilità/sensibilità. L’integrazione CEW è futura. |
| 17 | Investigation Planner basato sul Value of Information | **IPOTESI / RICERCA FUTURA** | Concettualmente coerente, ma non verificata come componente utile o necessaria della V1. Non deve guidare il modello dati oltre il minimo necessario a non precluderla. |
| 18 | Gli agenti non devono promuovere autonomamente dati ambigui a canonici | **REQUISITO DI GOVERNANCE CEW** | È una scelta di controllo del rischio, coerente con il protocollo N12; non viene presentata come verità scientifica esterna. |
| 19 | Ogni trasformazione importante deve essere auditabile | **REQUISITO DI ASSURANCE CEW** | Fortemente coerente con provenienza e riproducibilità. La forma esatta del receipt resta da specificare. |
| 20 | pgvector può supportare ricerca semantica ma non la verità canonica | **FATTO VERIFICATO sulla capacità; scelta di governance supportata** | pgvector fornisce ricerca vettoriale esatta/approssimata in PostgreSQL. I risultati semantici non devono sostituire dati strutturati/evidenze. |

---

## 4. Normativa: verifica e cautela

Sono state verificate le seguenti fonti:

- **DM 17 gennaio 2018 — NTC 2018**: pubblicato in G.U. Serie Generale n. 42 del 20/02/2018, S.O. n. 8;
- **Circolare 21 gennaio 2019 n. 7 C.S.LL.PP.**: istruzioni per l’applicazione delle NTC 2018;
- **UNI EN 1990-2:2026**: in vigore dal 02/04/2026, “Valutazione delle strutture esistenti”;
- **UNI EN 1998-3:2025**: in vigore, valutazione e adeguamento sismico di edifici e ponti; il sommario specifica inoltre che procedure di ispezione/checklist/raccolta dati sono documentate e archiviate;
- **UNI EN 13791:2019**: valutazione della resistenza a compressione in sito del calcestruzzo e correlazione tra prove indirette e carote;
- **UNI EN 12504-2:2021**: determinazione dell’indice sclerometrico.

**Correzione di metodo:** la baseline usa correttamente queste norme come possibili profili/riferimenti, ma **non si deve dedurre la loro applicabilità cogente al singolo caso dalla sola data di vigenza**. Applicabilità, coordinamento con il quadro nazionale, eventuali periodi/transizioni e scopo della verifica devono essere determinati per il procedimento concreto.

---

## 5. Evidenze scientifiche che sostengono l’architettura, senza “provarla” integralmente

### Interoperabilità BIM ↔ analisi strutturale

Sibenik & Kovacic (2020) documentano che il trasferimento seamless tra domini presenta ancora inconsistenze significative e propongono interpretazione esplicita, schemi domain-specific e certificazione del data exchange. Questo **sostiene** l’idea di adattatori e contratti CEW; non prova che il Canonical Structural Model proposto sia l’unica soluzione.

DOI: `10.1016/j.jobe.2020.101589`

### Esistente, fonti, incertezze e decisioni

Werbrouck et al. (2020), “Scan-to-graph”, identificano esplicitamente come problemi dell’esistente l’incertezza, il collegamento alle fonti e la documentazione delle decisioni/assunzioni di modellazione. Questo è uno dei supporti più diretti al Knowledge/Evidence model CEW.

DOI: `10.1016/j.autcon.2020.103286`

### Accuratezza Scan-to-BIM

Esfahani et al. (2021) mostrano sperimentalmente che accuratezza e precisione del modello as-built dipendono dal processo di modellazione e dal livello di automazione/formazione. Questo supporta la necessità di conservare qualità/incertezza e di non trattare un modello ricostruito come verità non qualificata.

DOI: `10.1016/j.autcon.2021.103686`

### Occlusioni e dati mancanti

Abreu et al. (2023), review su Scan-to-BIM/Scan-vs-BIM, identificano i dati mancanti dovuti a occlusioni come limite centrale e sottolineano il ruolo della pianificazione della scansione e della fusione di sensori.

### BIM–FE multi-livello

Alsharif et al. (2025) dimostrano su ponti in c.a. un framework BIM–FE bidirezionale con modellazione di danno e retrofit. È un’evidenza utile sulla fattibilità di integrazione tra rappresentazioni e analisi, ma il dominio ponte non va generalizzato automaticamente agli edifici CEW.

DOI: `10.1016/j.advengsoft.2024.103860`

---

## 6. Fonti primarie/ufficiali usate nell’audit

- IFC 4.3 Structural Analysis Domain: https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/ifcstructuralanalysisdomain/content.html
- IDS buildingSMART: https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/
- IfcOpenShell validation: https://docs.ifcopenshell.org/ifcopenshell-python/validation.html
- IfcTester: https://docs.ifcopenshell.org/ifctester.html
- W3C PROV-O: https://www.w3.org/TR/prov-o/
- ezdxf: https://ezdxf.readthedocs.io/en/stable/introduction.html
- PyMuPDF `Page.get_drawings()`: https://pymupdf.readthedocs.io/en/latest/page.html
- pdfplumber: https://github.com/jsvine/pdfplumber
- OCRmyPDF: https://ocrmypdf.readthedocs.io/en/latest/
- build123d: https://build123d.readthedocs.io/en/latest/introduction.html
- Open3D ICP: https://www.open3d.org/docs/latest/tutorial/pipelines/icp_registration.html
- PDAL pipelines: https://pdal.io/en/stable/pipeline.html
- COLMAP: https://colmap.github.io/tutorial.html
- Code_Aster: https://code-aster.org/en
- OpenTURNS reliability/sensitivity: https://openturns.github.io/openturns/latest/theory/reliability_sensitivity/reliability_sensitivity.html
- PostGIS: https://postgis.net/docs/postgis-en.html
- pgvector: https://github.com/pgvector/pgvector
- CADCraft roadmap: https://github.com/storytold/cadcraft/blob/main/ROADMAP.md
- CADCraft release v0.5.0: https://github.com/storytold/cadcraft/releases
- CADCraft real-world DWG round-trip issue #604: https://github.com/storytold/cadcraft/issues/604
- NTC 2018 G.U.: https://www.gazzettaufficiale.it/eli/id/2018/02/20/18A00716/sg
- Circolare 2019 n. 7: https://www.gazzettaufficiale.it/eli/id/2019/02/11/19A00855/sg
- UNI EN 1990-2:2026: https://store.uni.com/uni-en-1990-2-2026
- UNI EN 1998-3:2025: https://store.uni.com/uni-en-1998-3-2025
- UNI EN 13791:2019: https://store.uni.com/uni-en-13791-2019
- UNI EN 12504-2:2021: https://store.uni.com/uni-en-12504-2-2021

---

## 7. Registro decisionale corretto

### A. Requisiti CEW che possono restare stabili

- separazione tra fonte originale, evidenza, interpretazione e proprietà canonica;
- provenienza e versionamento espliciti;
- stato epistemico/qualità del dato come parte del modello;
- non sovrascrivere la storia delle correzioni;
- mapping tracciabile tra oggetti canonici e modelli derivati;
- nessuna promozione autonoma di dati ambigui da parte degli agenti;
- auditabilità delle trasformazioni importanti;
- profilo normativo esplicito e versionato per ogni verifica.

### B. Architettura di lavoro da mantenere, ma da provare

- Canonical Structural Model indipendente dagli applicativi;
- adattatori separati CAD / IFC / FEM;
- database relazionale-spaziale come base del patrimonio canonico;
- Geometry-as-Code come possibile proiezione geometrica riproducibile.

### C. Tecnologie da NON dichiarare adottate prima dei gate

- PostgreSQL/PostGIS;
- PyMuPDF/pdfplumber/OCRmyPDF;
- ezdxf;
- CADCraft;
- build123d/OpenCascade;
- IfcOpenShell/IfcTester;
- OpenSeesPy;
- Code_Aster;
- Open3D/PDAL/COLMAP;
- OpenTURNS.

Sono **candidati** con livelli diversi di maturità, non dipendenze consolidate.

### D. Elementi da tenere fuori dal percorso critico V1

- Investigation Planner basato su Value of Information;
- Kratos come ulteriore solver;
- fotogrammetria/nuvole di punti se il caso pilota non ne richiede immediatamente l’uso;
- ricerca semantica vettoriale come requisito core.

---

## 8. Gate di prova necessari prima di qualunque consolidamento tecnologico

1. **CEW-CONTRACT-01** — schema minimo del Canonical Structural Model con almeno un edificio, livelli, nodi, elementi, sezioni, proprietà, evidenze e versioni; serializzazione deterministica e migrazione di versione.
2. **CEW-EVIDENCE-01** — benchmark su PDF nativo, scansione e tabella N12, con ground truth umano e metriche di estrazione.
3. **CEW-CAD-01** — TAV.5/TAV.6/TAV.7: inventario deterministico ezdxf, apertura/render CADCraft, differenze, round-trip solo su copie, nessuna perdita ammessa nei dati CEW rilevanti.
4. **CEW-GEO-01** — generazione di una porzione M0-G con identificatori stabili; verifica di coordinate, sezioni, orientamento, livelli e rigenerazione deterministica.
5. **CEW-IFC-01** — export IFC, schema validation, IDS, confronto oggetto-per-oggetto e reimport controllato.
6. **CEW-FEM-01** — benchmark strutturale piccolo con risultato analitico o di riferimento; poi porzione N12; confronto con almeno un secondo solver/strumento affidabile.
7. **CEW-ASSURE-01** — dimostrare la catena completa `Result → SolverRun → Scenario → ModelGeneration → CanonicalProperty → Evidence → Source` senza riferimenti mancanti.

Nessun gate deve diventare PASS sulla sola base della documentazione del fornitore/progetto.

---

## 9. Decisione dell’audit

**PASS CON CORREZIONI sulla direzione concettuale.**

La baseline è utile come mappa di ricerca, ma **non è ancora una specifica architetturale approvata né una selezione tecnologica definitiva**.

Prima di integrare la PR in `main` occorre almeno:

- trattare la sezione “Decisioni consolidate” come registro graduato di confidenza;
- evitare `ADOTTARE` per tecnologie non provate su CEW/N12;
- mantenere OpenSeesPy, CADCraft, build123d e gli altri strumenti nello stato `CANDIDATO/QUALIFICARE`;
- eseguire i gate sopra, a partire da `CEW-CONTRACT-01` e `CEW-EVIDENCE-01`.

**Nessun merge automatico.**