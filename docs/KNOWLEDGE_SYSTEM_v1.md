# N12 Knowledge System v1

## Scopo

Rendere persistente, interrogabile e verificabile il patrimonio tecnico del progetto N12 affinché agenti e sessioni successive possano riprendere il lavoro senza ricostruire lo stato dalla chat o dalla cronologia dei file.

## Architettura

Il sistema usa cinque livelli distinti.

### K0 — Fonti primarie

PDF/raster originali, fotografie, relazione di calcolo e altre fonti non derivate. Sono immutabili come contenuto e costituiscono il riferimento ultimo dell'evidenza.

### K1 — Osservazioni

Trascrizioni, letture di quote/ID, coordinate pixel, classificazioni semantiche e misure. Una osservazione non è ancora automaticamente un dato canonico.

### K2 — Claim e rivalidazione

Ogni informazione strutturalmente rilevante viene ridotta a un claim verificabile. Il ledger conserva compatibilità, conflitti, versioni superate e cross-validation.

### K3 — Dati canonici di dominio

Dataset utilizzabili dal modello solo dopo i gate specifici del dominio. Un dataset può essere canonico per una proprietà e sospeso per un'altra: ad esempio sezioni dei pilastri e coordinate geometriche sono contratti distinti.

### K4 — Modello derivato

Nodi analitici, aste, modelli M0, EdiLus e verifiche sono derivazioni. Non possono diventare retroattivamente evidenza primaria dei dati che li hanno generati.

## Entry point degli agenti

`AGENTS.md` è la porta d'ingresso obbligatoria.

Ogni agente deve leggere:

1. `knowledge/KNOWLEDGE_MANIFEST.json`;
2. `knowledge/CURRENT_STATE.json`;
3. `knowledge/ARTIFACT_REGISTRY.csv`;
4. protocollo e skill del dominio.

Il manifest dichiara l'architettura. CURRENT_STATE dichiara il punto di ripresa. ARTIFACT_REGISTRY dichiara autorità e stato dei singoli artefatti.

## Default deny

Un file non registrato in `knowledge/ARTIFACT_REGISTRY.csv` è `UNREGISTERED_NON_AUTHORITATIVE`.

Questo impedisce che un agente scelga automaticamente il file con versione più alta, timestamp più recente o nome più convincente.

## Contratto di autorità

Classi:

- `SOURCE_PRIMARY` — fonte primaria;
- `SOURCE_REFERENCE` — fonte di controllo;
- `OBSERVATION` — osservazione non promossa;
- `CLAIM_LEDGER` — registro delle rivalidazioni;
- `CANONICAL` — dato canonico ammesso dal relativo gate;
- `DERIVED` — prodotto derivato;
- `PROCEDURE` — regola operativa;
- `SKILL` — procedura agente/esecutore;
- `HISTORICAL` — solo provenienza/storia.

Stati bloccanti come `SUSPENDED`, `SUPERSEDED`, `CONFLICT`, `REOPENED`, `TOMBSTONE`, `HISTORICAL_ONLY` non possono alimentare dati canonici.

## Separazione dei domini

Non esiste più l'idea che un singolo Master sia sempre l'unica autorità per tutte le proprietà.

Ogni proprietà segue il proprio gate:

- identità/simbologia;
- coordinate raster;
- rete metrica;
- sezioni/orientamenti;
- contorni dei supporti;
- travi documentate;
- nodi analitici;
- armature;
- fondazioni;
- materiali;
- carichi;
- modello.

Una correzione della geometria PT non invalida automaticamente una sezione documentata o un dato di fondazione indipendente.

## Anti-ripartenza

Quando compare un conflitto:

1. identificare il claim o dominio coinvolto;
2. marcare il record precedente come riaperto/sospeso/superato;
3. non cancellare la provenienza;
4. non riaprire domini indipendenti;
5. aggiornare CURRENT_STATE;
6. registrare il nuovo artefatto nel registry;
7. eseguire il validatore.

## PT/TAV-02S — stato corrente

Il precedente `PT_MASTER_CURRENT.csv` è conservato ma non è autorità geometrica. Il gate corrente richiede registrazione indipendente dei centri/sagome sul raster e costruzione metrica dalle quote documentali.

La pipeline è:

`raster observed -> metric constraints -> metric support centers -> scan residuals -> physical supports -> documentary beams -> analytical nodes -> overlay QA -> regenerated master`.

Il principio per i pilastri-setti è:

`1 supporto fisico != necessariamente 1 nodo analitico`.

## Validazione

`python scripts/validate_knowledge_system.py`

controlla:

- presenza dei file centrali;
- validità JSON/CSV;
- unicità di ID e path;
- esistenza dei file registrati;
- coerenza authority/status/may_feed_canonical;
- coerenza tra manifest e CURRENT_STATE;
- presenza e registrazione delle skill attive;
- sospensione effettiva del vecchio Master PT durante il gate raster.

Il workflow `.github/workflows/validate-knowledge-system.yml` esegue automaticamente questi controlli e il validatore semantico della carpenteria.

Il validatore strutturale non sostituisce la revisione visuale: i gate semantici e gli overlay restano obbligatori dove indicato dalle skill.

## Regola di fine sessione

Una sessione che modifica lo stato tecnico non è completa finché il repository non contiene:

- evidenza/artefatto prodotto;
- provenienza/claim aggiornato;
- eventuale aggiornamento registry;
- eventuale aggiornamento CURRENT_STATE;
- validazione eseguita con esito registrabile.
