# N12 Interpretive Knowledge Readiness v1

## Scopo

Valutare se il patrimonio già accumulato da N12/CEW consente al sistema di interpretare tavole strutturali e documenti tecnici, distinguendo chiaramente tra: evidenza, memoria di progetto, conoscenza procedurale, conoscenza tecnica e conoscenza scientifico-normativa.

## Conclusione sintetica

Il sistema possiede già un patrimonio interpretativo sostanziale, ma oggi è distribuito tra registri, contratti, ricevute, prototipi, casi corretti e workflow. È sufficiente per guidare una lettura tecnica governata e per formulare candidati strutturali spiegabili. Non è ancora sufficiente, da solo, per costituire una base di conoscenza ingegneristica esplicita capace di giustificare automaticamente interpretazioni strutturali complesse o decisioni di progetto.

La maturità attuale è quindi:

`STRONG_EVIDENCE_AND_PROJECT_INTERPRETATION / PARTIAL_ENGINEERING_KNOWLEDGE / SCIENTIFIC_AUTHORITY_NOT_ENCODED`

## Patrimonio già acquisito

### 1. Conoscenza di provenienza e affidabilità — FORTE

N12/CEW conserva SourceVersion, Page, EvidenceRegion, trasformazioni, fingerprint e stati DOC/MIS/RIF/INF/INC/ND. La correzione di una lettura non cancella lo storico e una inferenza non diventa automaticamente dato di progetto.

Questa conoscenza consente al sistema di sapere non soltanto "che cosa è stato letto", ma anche "da dove proviene", "quanto è forte" e "cosa resta da verificare".

### 2. Conoscenza procedurale del lavoro strutturale — FORTE

Sono già codificate catene operative quali:

`documenti -> rilievo -> carpenterie -> armature -> fondazioni -> materiali/indagini -> modello -> carichi -> verifiche -> interventi`

ed il percorso di modello:

`M0-G -> M0-S -> M0-A -> M0-M -> M0-L -> M0-V -> M1 -> M2`.

Il sistema sa quindi quale tipo di informazione è prerequisito di un'altra e quali promozioni sono vietate.

### 3. Conoscenza interpretativa derivata dai casi reali N12 — FORTE MA PROJECT-SPECIFIC

Sono stati acquisiti e corretti casi che rappresentano vera conoscenza interpretativa:

- un rettangolo non è automaticamente un pilastro;
- una sezione di trave rappresentata in mezzeria deve essere interpretata attraverso il contesto della tavola;
- quote poco leggibili possono essere riconciliate mediante occorrenze della stessa famiglia, piani adiacenti e sovrapposizioni documentali;
- una coincidenza metrica non basta per identificare un elemento: è richiesto almeno un secondo discriminante;
- numerazioni interne di uno schema di telaio non devono essere identificate con nodi canonici senza raccordo documentale;
- geometria, carichi, sezione, armatura e identità strutturale restano livelli separati finché la catena di evidenza non li lega.

Questi sono pattern riutilizzabili, non semplici valori numerici.

### 4. Conoscenza geometrico-topologica del progetto — FORTE

Il lavoro storico contiene DXF, topologie, 57 nodi, connessioni, componenti, catene verticali, abachi, telai discretizzati per campata, firme metriche, sezioni e topologia delle fondazioni. CEW dispone inoltre di registrazioni spaziali, GCP strutturali, locator governati e controlli sul frame del viewer.

Questa base permette confronti strutturali molto più forti della semplice similarità visuale.

### 5. Memoria di prototipi e famiglie — PRESENTE

OA/OAR e Document Discovery hanno già introdotto:

- ObjectPrototype / ObjectFamily / ObjectSignature;
- TEACH_THIS_IS -> FIND_SIMILAR -> REVIEW_SIMILAR_GROUP;
- project-local PrototypeMemory;
- esempi POSITIVE / NEGATIVE / AMBIGUOUS;
- counterexample memory;
- replay deterministico delle ricevute;
- separazione tra riferimenti esterni, memoria locale del progetto e futura conoscenza generica.

Il sistema può quindi apprendere progressivamente "come appare questo tipo di oggetto in questo progetto" senza trasformare automaticamente la somiglianza in verità.

### 6. Conoscenza tecnica di dominio — PARZIALE

Esiste nella skill specialistica e nei casi N12: elementi in c.a., carpenterie, pilastri, travi, solai, fondazioni, armature, sezioni, carichi, livelli di conoscenza, materiali e percorso verso EdiLus-EE.

Tuttavia questa conoscenza è ancora prevalentemente testuale/procedurale e distribuita. Non esiste ancora un'ontologia ingegneristica unica che renda interrogabili relazioni come:

`dimension line -> measured span`
`bar callout -> reinforcement set`
`section marker -> section view`
`beam span -> supports -> storey -> section -> reinforcement`
`column continuation -> vertical structural line`
`foundation beam -> supported column/wall -> soil interface`

### 7. Conoscenza scientifica e normativa — PRESENTE COME RIFERIMENTO, NON COME MOTORE

La skill richiama NTC 2018, livelli di conoscenza, materiali e verifiche, ma il sistema non dispone ancora di una base normativa/scientifica versionata e computabile che possa essere usata come autorità automatica.

Le regole normative devono quindi continuare ad essere verificate contro fonti ufficiali vigenti. Il sistema può assistere l'interpretazione, ma non deve dedurre automaticamente conformità, sicurezza o capacità resistente dalla sola lettura documentale.

## Cosa può già interpretare in modo governato

Il sistema può già:

1. distinguere geometria grafica da identità tecnica;
2. associare candidati mediante geometria, dimensioni, orientamento, testo, topologia e contesto;
3. utilizzare firme metriche e relazioni di continuità per discriminare telai/travi/nodi;
4. cercare occorrenze simili e apprendere da esempi umani;
5. confrontare fonti diverse e mantenere inferenze separate dai dati documentali;
6. produrre CandidateObservation / CandidateGeometry / ObjectCandidate spiegabili;
7. indicare quale evidenza manca per promuovere un candidato.

## Cosa non deve ancora fare autonomamente

Non è ancora autorizzato né sufficientemente supportato per:

- attribuire una funzione strutturale solo dalla forma;
- creare identità strutturali da similarità visuale;
- dedurre armature mancanti per analogia senza stato INF;
- trasformare una quota in dimensione reale senza contesto e calibrazione;
- inferire continuità tridimensionale non dimostrata;
- determinare modello resistente, LC/FC, sicurezza o conformità normativa senza dati e controllo professionale;
- usare conoscenza generale del modello linguistico come verità del progetto.

## Gap da colmare: Interpretive Engineering Knowledge Layer

Per trasformare il patrimonio esistente in un vero motore interpretativo occorre aggiungere un livello separato, versionato e interrogabile:

`Evidence -> Graphic Semantics -> Technical Semantics -> Structural Hypothesis -> Engineering Rule Check -> Human Decision`

Il layer deve includere almeno:

- ontologia degli oggetti di disegno strutturale;
- grammatica delle quote, richiami, sezioni, assi, nodi, armature e simboli;
- relazioni topologiche e di continuità;
- pattern storici dei disegni in c.a.;
- regole di coerenza geometrica e strutturale;
- provenance di ogni regola;
- livello di autorità della regola: `PROJECT_LEARNED`, `ENGINEERING_HEURISTIC`, `SCIENTIFIC_REFERENCE`, `NORMATIVE_REFERENCE`;
- gestione di conflitto, eccezione e revisione;
- test su casi positivi, negativi e ambigui N12.

## Relazione con il benchmark PDF

Il benchmark degli estrattori non deve misurare soltanto OCR e geometria. Ogni output dovrà essere valutato anche per la sua capacità di alimentare correttamente questo layer senza saltare livelli di significato.

Esempio:

`"2Ø14 L=970"`

non deve diventare direttamente armatura canonica. La catena corretta è:

`TEXT tokens -> reinforcement-callout candidate -> association to graphic bar/span -> context check -> structural-object binding candidate -> human validation -> canonical reinforcement assertion`.

## Gate proposto

Prima di dichiarare CEW capace di interpretazione tecnica autonoma assistita, richiedere:

`IK-G1 Evidence semantics complete`
`IK-G2 Technical drawing grammar validated`
`IK-G3 Structural relation engine validated`
`IK-G4 Scientific/normative reference provenance validated`
`IK-G5 N12 blind-case human comparison PASS`

Fino a IK-G5 lo stato resta:

`INTERPRETIVE_ASSISTANT_WITH_HUMAN_AUTHORITY`.
